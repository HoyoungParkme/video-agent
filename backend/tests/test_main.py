"""main — 앱 조립 · 시작(키 확인 → 죽은 작업 되돌리기 → 워커) · 끝 · /health."""

from __future__ import annotations

import asyncio
import logging

import httpx
import pytest
from sqlalchemy import select

from app.core.config import config
from app.core.db import SessionLocal
from app.core.settings import settings
from app.domains.job import pipeline
from app.domains.job.models import AnalysisJobRow, AudioChunkRow, ChunkState, ErrorKind, JobStatus
from app.domains.job.service import JobService
from app.domains.video.service import VideoService
from app.infra.openai import KeyState
from app.main import app, load_video


async def test_health() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://localhost"
    ) as c:
        r = await c.get("/health")
    assert r.json() == {"status": "ok"}


async def test_lifespan_checks_stored_key(db, env_file, verify, monkeypatch, caplog) -> None:
    monkeypatch.setattr(settings, "last_check", settings.last_check)  # 끝나면 되돌린다
    caplog.set_level(logging.INFO, logger="app")
    env_file.write_text("OPENAI_API_KEY=sk-abcdefghijklmnop1234\n")
    async with app.router.lifespan_context(app):
        assert settings.last_check.state == KeyState.ok
    assert verify.calls == ["sk-abcdefghijklmnop1234"]
    assert "키 확인: ok" in caplog.text  # SEQ-13 — 로그 한 줄, 키는 없다
    assert "sk-abcdefghijklmnop1234" not in caplog.text


@pytest.mark.parametrize(
    ("host", "status"),
    [("localhost:8000", 200), ("127.0.0.1", 200), ("api:8000", 200), ("evil.example", 400)],
)
async def test_host_check(host: str, status: int) -> None:
    """DNS 리바인딩 — Host가 localhost · 127.0.0.1 · api가 아니면 400(INFRA 5절)."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://localhost"
    ) as c:
        r = await c.get("/health", headers={"Host": host})
    assert r.status_code == status


async def _status(job_id: int) -> AnalysisJobRow:
    async with SessionLocal() as s:
        return await s.scalar(select(AnalysisJobRow).where(AnalysisJobRow.id == job_id))


async def test_restart_fails_running_and_continues_queued(
    db, make, audio_source, summarizer, env_file, verify, monkeypatch, tmp_path, caplog
) -> None:
    """서버 재시작(SEQ-13) — running이던 작업은 failed, 기다리던 작업은 이어서 돈다.

    fail_orphans가 워커보다 먼저다 — 거꾸로면 죽은 running 행 때문에 워커가 아무것도 못 꺼낸다.
    """
    monkeypatch.setattr(pipeline, "audio_source", audio_source)
    monkeypatch.setattr(pipeline, "summarizer", summarizer)
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "last_check", settings.last_check)
    caplog.set_level(logging.INFO, logger="app")
    dead = await make.job((await make.video()).id, JobStatus.running, stage="summarize")
    waiting = await make.job((await make.video()).id, JobStatus.queued)
    async with app.router.lifespan_context(app):
        for _ in range(250):
            if (await _status(waiting.id)).status == JobStatus.done:
                break
            await asyncio.sleep(0.02)
    dead_row, done_row = await _status(dead.id), await _status(waiting.id)
    assert (dead_row.status, dead_row.error_kind, dead_row.error_reason) == (
        JobStatus.failed,
        ErrorKind.unknown,
        "서버가 다시 시작됨",
    )
    assert done_row.status == JobStatus.done
    assert "멈춘 작업 1개를 실패로 되돌렸다" in caplog.text


async def test_restart_during_transcription_then_retry(
    db, make, key, audio_source, audio_split, stt, summarizer, verify, monkeypatch, tmp_path
) -> None:
    """받아쓰기 도중 서버가 죽었다 — 다시 뜨면 failed(보내던 조각은 waiting), 다시 시도하면
    끝난 조각은 다시 보내지 않고 이어서 끝난다."""
    for name, port in [
        ("audio_source", audio_source),
        ("audio_split", audio_split),
        ("stt", stt),
        ("summarizer", summarizer),
    ]:
        monkeypatch.setattr(pipeline, name, port)
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "last_check", settings.last_check)
    video = await make.video(has_captions=False, caption_language=None, caption_kind=None)
    stages = ["download", "transcribe", "summarize", "chapter", "suggest"]
    job = await make.job(
        video.id, JobStatus.running, stage="transcribe", stages=stages, stt_model="whisper-1"
    )
    tmp = tmp_path / "tmp" / str(video.id)
    tmp.mkdir(parents=True)
    done = [{"start_sec": 0.0, "end_sec": 5.0, "text": "끝난 조각", "language": "ko"}]
    for seq, state in [(1, ChunkState.done), (2, ChunkState.in_flight), (3, ChunkState.waiting)]:
        (tmp / f"{seq}.mp3").write_bytes(b"chunk")
        db.add(
            AudioChunkRow(
                job_id=job.id,
                seq=seq,
                offset_sec=(seq - 1) * 600,
                duration_sec=600,
                path=None if state == ChunkState.done else str(tmp / f"{seq}.mp3"),
                state=state,
                attempts=1 if state != ChunkState.waiting else 0,
                result=done if state == ChunkState.done else None,
            )
        )
    await db.commit()

    async with app.router.lifespan_context(app):  # 다시 뜬다 — 죽은 작업은 failed
        pass
    row = await _status(job.id)
    assert (row.status, row.stage, row.error_reason) == (
        JobStatus.failed,
        "transcribe",
        "서버가 다시 시작됨",
    )
    async with SessionLocal() as s:
        states = list(await s.scalars(select(AudioChunkRow.state).order_by(AudioChunkRow.seq)))
    assert states == [ChunkState.done, ChunkState.waiting, ChunkState.waiting]

    async with SessionLocal() as s:  # 다시 시도 — 워커가 resume으로 이어 간다
        await JobService(s).retry((await VideoService(s, None, None).get(video.id)).video)
    async with app.router.lifespan_context(app):
        for _ in range(250):
            if (await _status(job.id)).status == JobStatus.done:
                break
            await asyncio.sleep(0.02)
    assert (await _status(job.id)).status == JobStatus.done
    assert sorted(stt.calls) == [2, 3]  # 끝난 1번은 다시 보내지 않는다
    assert audio_split.calls == []  # 조각 행이 있어 다시 나누지 않는다


async def test_lifespan_stops_worker(db, env_file, verify, monkeypatch) -> None:
    monkeypatch.setattr(settings, "last_check", settings.last_check)
    before = {t for t in asyncio.all_tasks() if not t.done()}
    async with app.router.lifespan_context(app):
        assert any("worker" in repr(t.get_coro()) for t in asyncio.all_tasks() - before)
    await asyncio.sleep(0)
    assert not [
        t for t in asyncio.all_tasks() - before if not t.done() and "worker" in repr(t.get_coro())
    ]


async def test_load_video(db, make) -> None:
    row = await make.video()
    assert (await load_video(row.id)).id == row.id
    assert await load_video(999) is None  # 그 사이 지워진 영상

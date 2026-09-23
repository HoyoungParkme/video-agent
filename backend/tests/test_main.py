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
from app.domains.job.models import AnalysisJobRow, ErrorKind, JobStatus
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

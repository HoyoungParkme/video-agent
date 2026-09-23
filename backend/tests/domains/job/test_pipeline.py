"""job/pipeline — 오류 종류 · 첫 단계부터 · 대기열 워커(VA-MS-002 pipeline). 포트는 가짜로."""

from __future__ import annotations

import asyncio
import errno
import socket
from datetime import UTC, datetime, timedelta

import httpx
import openai as sdk
import pytest
from sqlalchemy import select

from app.core.config import config
from app.core.db import SessionLocal
from app.core.errors import NotImplementedYet
from app.domains.analysis.models import SegmentRow, SummaryRow, TranscriptRow
from app.domains.job import pipeline
from app.domains.job.models import AnalysisJobRow, ErrorKind, JobStage, JobStatus
from app.domains.job.service import JobService
from app.domains.video.models import VideoRow
from app.domains.video.service import VideoService
from app.infra.errors import FfmpegError, OpenAIOutputError, YtdlpError

T0 = datetime(2026, 9, 23, 3, 0, tzinfo=UTC)
REQ = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")


@pytest.fixture
def ports(monkeypatch, audio_source, summarizer, tmp_path):
    """파이프라인에 가짜 포트를 끼우고 data 폴더를 임시로."""
    monkeypatch.setattr(pipeline, "audio_source", audio_source)
    monkeypatch.setattr(pipeline, "summarizer", summarizer)
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    return audio_source, summarizer


async def _row(job_id: int) -> AnalysisJobRow:
    async with SessionLocal() as s:
        return await s.scalar(select(AnalysisJobRow).where(AnalysisJobRow.id == job_id))


async def _running(make, **kw):
    """자막 있는 YouTube 영상과, 워커가 막 꺼낸 작업."""
    row = await make.video(**kw)
    job = await make.job(row.id, JobStatus.running)
    return VideoService.to_dto(row, None, 0), job


# --- error_kind


def test_error_kind_each() -> None:
    kind = pipeline.error_kind
    assert kind(TimeoutError()) == ErrorKind.network
    assert kind(ConnectionResetError()) == ErrorKind.network
    assert kind(socket.gaierror()) == ErrorKind.network
    assert kind(sdk.APIConnectionError(request=REQ)) == ErrorKind.network  # SDK 예외지만 네트워크
    assert kind(sdk.APITimeoutError(request=REQ)) == ErrorKind.network
    status = sdk.InternalServerError("x", response=httpx.Response(500, request=REQ), body=None)
    assert kind(status) == ErrorKind.openai
    assert kind(OpenAIOutputError("형식")) == ErrorKind.openai
    assert kind(YtdlpError("Video unavailable", "unavailable")) == ErrorKind.youtube
    assert kind(FfmpegError("bad", 1)) == ErrorKind.ffmpeg
    assert kind(OSError(errno.ENOSPC, "No space left on device")) == ErrorKind.disk
    assert kind(ValueError("x")) == ErrorKind.unknown
    assert kind(NotImplementedYet("아직")) == ErrorKind.unknown


# --- 스텁


async def test_stubs(make) -> None:
    video, job = await _running(make)
    with pytest.raises(NotImplementedYet):
        await pipeline.transcribe_stage(job.id, video, "/tmp/a.mp3", "/tmp")
    with pytest.raises(NotImplementedYet):
        await pipeline.resume(job.id, video)


# --- run


async def test_run_captions_to_done(db, make, ports, tmp_path) -> None:
    audio_source, summarizer = ports
    video, job = await _running(make)
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.progress_pct, row.stage) == (JobStatus.done, 100, JobStage.suggest)
    assert set(row.stage_durations_sec) == {"download", "summarize", "chapter", "suggest"}
    assert audio_source.calls == [video.source_id]
    assert [name for name, _ in summarizer.calls] == [
        "summary",
        "chapters",
        "questions",
    ]  # 받아쓰기 0회
    t = await db.scalar(select(TranscriptRow))
    assert (t.source, t.language, t.model) == ("caption_manual", "ko", None)
    assert not (tmp_path / "tmp" / str(video.id)).exists()  # 끝나면 임시 폴더가 없다


async def test_run_auto_captions_source(db, make, ports) -> None:
    audio_source, _ = ports
    lines, _, _ = audio_source.result
    audio_source.result = (lines, "en", "auto")
    video, job = await _running(make)
    await pipeline.run(job.id, video)
    t = await db.scalar(select(TranscriptRow))
    assert (t.source, t.language) == ("caption_auto", "en")


async def test_run_summary_fails(db, make, ports) -> None:
    _, summarizer = ports
    summarizer.fail["summary"] = OpenAIOutputError("모델 출력을 읽지 못했어요(형식)")
    video, job = await _running(make)
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.stage, row.progress_pct) == (JobStatus.failed, JobStage.summarize, 25)
    assert (row.error_kind, row.error_reason, row.error_attempts) == (
        ErrorKind.openai,
        "모델 출력을 읽지 못했어요(형식)",
        1,
    )
    assert await db.scalar(select(SegmentRow).limit(1)) is not None  # 스크립트는 남아 있다
    assert await db.scalar(select(SummaryRow)) is None


async def test_run_download_fails_removes_tmp(db, make, ports, tmp_path) -> None:
    audio_source, _ = ports
    audio_source.error = YtdlpError("ERROR: Private video\nsecond line", "private")
    video, job = await _running(make)
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.stage, row.error_kind) == (
        JobStatus.failed,
        JobStage.download,
        ErrorKind.youtube,
    )
    assert row.error_reason == "ERROR: Private video"  # 첫 줄
    assert not (tmp_path / "tmp" / str(video.id)).exists()


async def test_run_captions_vanished(db, make, ports) -> None:
    audio_source, _ = ports
    audio_source.result = None  # 등록 뒤 자막이 사라졌다
    video, job = await _running(make)
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.error_kind, row.error_reason) == (
        JobStatus.failed,
        ErrorKind.youtube,
        "자막을 찾지 못했습니다",
    )


async def test_run_without_captions_is_stub(db, make, ports) -> None:
    video, job = await _running(make, has_captions=False, caption_language=None, caption_kind=None)
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.stage, row.error_kind) == (
        JobStatus.failed,
        JobStage.download,
        ErrorKind.unknown,
    )


async def test_run_cancelled_writes_nothing(db, make, ports) -> None:
    _, summarizer = ports
    summarizer.delay = 5
    video, job = await _running(make)
    task = asyncio.create_task(pipeline.run(job.id, video))
    while not summarizer.calls:
        await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):  # 예외가 밖으로
        await task
    row = await _row(job.id)
    assert (row.status, row.stage, row.error_kind) == (JobStatus.running, JobStage.summarize, None)


# --- worker


async def load_video(video_id: int):
    """main.py의 load_video와 같은 일 — 짧은 세션으로 VideoService.get."""
    async with SessionLocal() as s:
        return (await VideoService(s, None, None).get(video_id)).video


def _worker(load=load_video) -> asyncio.Task:
    return asyncio.create_task(pipeline.worker(load))


async def _stop(task: asyncio.Task) -> None:
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


async def _wait_status(job_id: int, status: JobStatus, timeout: float = 5) -> None:
    async def loop():
        while (await _row(job_id)).status != status:
            await asyncio.sleep(0.02)

    await asyncio.wait_for(loop(), timeout)


async def test_worker_runs_queue_one_by_one(db, make, ports, monkeypatch) -> None:
    monkeypatch.setattr(config, "WORKER_IDLE_SEC", 0.05)
    running_seen: list[int] = []

    async def fake_run(job_id: int, video) -> None:
        async with SessionLocal() as s:
            n = len(
                list(
                    await s.scalars(
                        select(AnalysisJobRow.id).where(AnalysisJobRow.status == JobStatus.running)
                    )
                )
            )
        running_seen.append(n)
        await asyncio.sleep(0.05)
        if job_id == first.id:
            raise RuntimeError("첫 작업이 예외로 끝난다")
        async with SessionLocal() as s:
            await JobService(s).finish(job_id)

    monkeypatch.setattr(pipeline, "run", fake_run)
    first = await make.job((await make.video()).id, JobStatus.queued, at=T0)
    second = await make.job((await make.video()).id, JobStatus.queued, at=T0 + timedelta(seconds=1))
    worker = _worker()
    try:
        await _wait_status(second.id, JobStatus.done)  # 첫 작업이 예외로 끝나도 둘째가 돈다
    finally:
        await _stop(worker)
    assert running_seen == [1, 1]  # 동시에 running 둘이 없다
    assert JobService.tasks == {}
    failed = await _row(first.id)  # 예외로 끝난 작업은 실패로 접혀 대기열을 막지 않는다
    assert (failed.status, failed.error_kind, failed.error_reason) == (
        JobStatus.failed,
        ErrorKind.unknown,
        "첫 작업이 예외로 끝난다",
    )


async def test_worker_resumes_retried_and_skips_deleted(db, make, ports, monkeypatch) -> None:
    monkeypatch.setattr(config, "WORKER_IDLE_SEC", 0.05)
    calls: list[tuple[str, int]] = []

    async def fake_resume(job_id: int, video) -> None:
        calls.append(("resume", job_id))
        async with SessionLocal() as s:
            await JobService(s).finish(job_id)

    monkeypatch.setattr(pipeline, "resume", fake_resume)
    retried = await make.job((await make.video()).id, JobStatus.queued, stage="summarize")
    gone = await make.job((await make.video()).id, JobStatus.queued, at=T0 - timedelta(days=1))

    loaded: list[int] = []

    async def load(video_id: int):
        loaded.append(video_id)
        if video_id == gone.video_id:  # 그 사이 지워졌다 — 작업 행도 cascade로 없다
            async with SessionLocal() as s:
                await s.delete(await s.get(VideoRow, video_id))
                await s.commit()
            return None
        return await load_video(video_id)

    worker = _worker(load)
    try:
        await _wait_status(retried.id, JobStatus.done)
    finally:
        await _stop(worker)
    assert calls == [("resume", retried.id)]  # stage가 pending이 아니면 resume
    assert loaded[0] == gone.video_id


async def test_worker_cancel_cancels_task(db, make, ports, monkeypatch) -> None:
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def fake_run(job_id: int, video) -> None:
        started.set()
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            cancelled.set()
            raise

    monkeypatch.setattr(pipeline, "run", fake_run)
    job = await make.job((await make.video()).id, JobStatus.queued)
    worker = _worker()
    await asyncio.wait_for(started.wait(), 5)
    await _stop(worker)  # 서버 종료 — 워커 자신의 취소는 다시 던진다
    assert cancelled.is_set()  # 돌던 태스크도 취소된다
    assert (await _row(job.id)).status == JobStatus.running  # 다음 시작 때 fail_orphans가 되돌린다


async def test_worker_survives_deleted_task(db, make, ports, monkeypatch) -> None:
    monkeypatch.setattr(config, "WORKER_IDLE_SEC", 0.05)
    started = asyncio.Event()

    async def fake_run(job_id: int, video) -> None:
        if job_id == first.id:
            started.set()
            await asyncio.sleep(30)
        async with SessionLocal() as s:
            await JobService(s).finish(job_id)

    monkeypatch.setattr(pipeline, "run", fake_run)
    first = await make.job((await make.video()).id, JobStatus.queued, at=T0)
    second = await make.job((await make.video()).id, JobStatus.queued, at=T0 + timedelta(seconds=1))
    worker = _worker()
    try:
        await asyncio.wait_for(started.wait(), 5)
        JobService.tasks[first.video_id].cancel()  # 삭제가 도는 태스크를 취소한 것처럼
        async with SessionLocal() as s:  # 삭제 라우터가 행을 지운 것처럼 — 도는 작업이 없어진다
            await s.delete(await s.get(AnalysisJobRow, first.id))
            await s.commit()
        JobService.wake()
        await _wait_status(second.id, JobStatus.done)  # 워커는 살아 다음 작업을 꺼낸다
    finally:
        await _stop(worker)

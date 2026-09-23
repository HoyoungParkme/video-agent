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

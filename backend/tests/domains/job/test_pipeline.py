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

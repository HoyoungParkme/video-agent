"""job/service — 작업 시작 · 진행 · 대기열(VA-MS-002 JobService). B1 몫 전부와 스텁 둘."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.config import config
from app.core.errors import JobExists, KeyMissing, NotFound, NotImplementedYet
from app.domains.job.models import (
    AnalysisJobRow,
    AudioChunkRow,
    ChunkState,
    ErrorKind,
    JobStage,
    JobStatus,
)
from app.domains.job.schemas import JobError
from app.domains.job.service import JobService
from app.domains.video.models import SourceKind
from app.domains.video.schemas import Video

T0 = datetime(2026, 9, 23, 3, 0, tzinfo=UTC)
STT_STAGES = ["download", "transcribe", "summarize", "chapter", "suggest"]


def _video(row, status: str = "registered") -> Video:
    # 영상 묶음을 부르지 않고 DTO를 바로 — 작업 묶음은 Video를 받기만 한다
    return Video(
        **{c: getattr(row, c) for c in Video.model_fields if hasattr(row, c)},
        status=status,
        analyzed_at=None,
        chat_turn_count=0,
    )


async def _job_row(db, job_id: int) -> AnalysisJobRow:
    # 서비스가 쓴 값을 DB에서 다시 — 다른 객체는 건드리지 않는다
    return await db.scalar(
        select(AnalysisJobRow)
        .where(AnalysisJobRow.id == job_id)
        .execution_options(populate_existing=True)
    )


# --- stages_for


async def test_stages_for_four_sources(make) -> None:
    yt = await make.video()
    yt_no = await make.video(has_captions=False, caption_language=None, caption_kind=None)
    mp4 = await make.video(
        source_kind=SourceKind.local,
        channel=None,
        origin="talk.MP4",
        has_captions=False,
        caption_language=None,
        caption_kind=None,
    )
    mp3 = await make.video(
        source_kind=SourceKind.local,
        channel=None,
        origin="call.m4a",
        has_captions=False,
        caption_language=None,
        caption_kind=None,
    )
    assert JobService.stages_for(_video(yt)) == ["download", "summarize", "chapter", "suggest"]
    assert JobService.stages_for(_video(yt_no)) == STT_STAGES
    assert JobService.stages_for(_video(mp4)) == ["extract", *STT_STAGES[1:]]
    assert JobService.stages_for(_video(mp3)) == STT_STAGES[1:]  # 로컬 음성은 origin의 확장자

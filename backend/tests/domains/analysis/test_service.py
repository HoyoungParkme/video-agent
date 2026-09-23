"""analysis/service — 스크립트 · 요약 · 챕터 · 추천 질문 · 결과(VA-MS-003). B1 몫(구간 · 파트 갈래는 B2)."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.core.errors import NotImplementedYet, ResultNotReady
from app.domains.analysis import crud
from app.domains.analysis.models import (
    ChapterRow,
    InsightRow,
    PartRow,
    SegmentRow,
    SuggestedQuestionRow,
    SummaryRow,
    TranscriptRow,
    TranscriptSource,
)
from app.domains.analysis.schemas import CaptionLine, ChapterDraft, Segment, SummaryDraft
from app.domains.analysis.service import AnalysisService
from app.domains.job.models import JobStatus
from app.domains.job.service import JobService
from app.domains.video.service import VideoService


async def _count(db, model) -> int:
    return await db.scalar(select(func.count()).select_from(model))


async def _video(db, make, status: JobStatus | None = None, **kw):
    row = await make.video(**kw)
    if status is not None:
        await make.job(row.id, status)
    return VideoService.to_dto(row, await JobService(db).latest(row.id), 0)


def _segs(*starts: float) -> list[Segment]:
    return [Segment(seq=i, start_sec=s, end_sec=s + 5, text="x") for i, s in enumerate(starts, 1)]


# --- segments_of · chapters_of · clamp_secs


async def test_segments_of(db, make, summarizer) -> None:
    row = await make.video()
    assert await AnalysisService(db, summarizer).segments_of(row.id) == []  # 예외 아님
    await make.transcript(row.id, ["하나", "둘", "셋"])
    got = await AnalysisService(db, summarizer).segments_of(row.id)
    assert [(s.seq, s.start_sec, s.text) for s in got] == [
        (1, 0, "하나"),
        (2, 10, "둘"),
        (3, 20, "셋"),
    ]

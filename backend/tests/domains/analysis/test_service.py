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


async def test_chapters_of_without_parts(db, make, summarizer) -> None:
    row = await make.video()
    await crud.replace_chapters(db, row.id, [(i * 360.0, f"챕터 {i}", ["a"]) for i in range(8)])
    await db.commit()
    chapters = await AnalysisService(db, summarizer).chapters_of(row.id)
    assert [c.seq for c in chapters] == list(range(1, 9))
    assert all(c.part_seq is None for c in chapters)


def test_clamp_secs() -> None:
    segs = _segs(0, 10, 20, 2990)
    clamp = AnalysisService.clamp_secs
    assert clamp([-3], 3000, segs) == [0]  # 첫 구간 시작
    assert clamp([3010], 3000, segs) == [2990]  # 마지막 구간 시작
    assert clamp([12.5, 700], 3000, segs) == [12.5, 700]  # 범위 안은 그대로
    assert clamp([30, 30, 5], 3000, segs) == [5, 30]  # 중복 없이 오름차순
    assert clamp([-1, 3001], 3000, []) == []  # 구간이 없으면 범위 밖은 뺀다

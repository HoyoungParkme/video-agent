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


# --- save_transcript


async def test_save_transcript_replaces_and_sorts(db, make, summarizer, queries) -> None:
    row = await make.video()
    svc = AnalysisService(db, summarizer)
    lines = [
        CaptionLine(20, 25, "셋째"),
        CaptionLine(0, 5, "첫째"),
        CaptionLine(10, 8, "둘째"),
        CaptionLine(30, 31, "  "),
    ]
    await svc.save_transcript(row.id, TranscriptSource.caption_manual, "ko", None, lines)
    await svc.save_transcript(row.id, TranscriptSource.caption_manual, "ko", None, lines)  # 두 번
    assert await _count(db, TranscriptRow) == 1  # 한 벌
    segs = list(await db.scalars(select(SegmentRow).order_by(SegmentRow.seq)))
    assert [(s.seq, s.text) for s in segs] == [
        (1, "첫째"),
        (2, "둘째"),
        (3, "셋째"),
    ]  # 시각순 · 빈 줄 없음
    assert (segs[1].start_sec, segs[1].end_sec) == (10, 10)  # 끝이 시작보다 앞이면 시작으로
    t = await db.scalar(select(TranscriptRow))
    assert (t.source, t.language, t.model) == ("caption_manual", "ko", None)


async def test_save_transcript_3000_lines_one_insert(db, make, summarizer, queries) -> None:
    row = await make.video()
    lines = [CaptionLine(i, i + 1, f"줄 {i}") for i in range(3000)]
    queries.clear()
    await AnalysisService(db, summarizer).save_transcript(
        row.id, TranscriptSource.stt, "ko", "whisper-1", lines
    )
    inserts = [q for q in queries if q.startswith("INSERT INTO segments")]
    assert len(inserts) == 1  # 3,000줄이 쿼리 하나로
    assert await _count(db, SegmentRow) == 3000


async def test_save_transcript_empty(db, make, summarizer) -> None:
    row = await make.video()
    with pytest.raises(ValueError):
        await AnalysisService(db, summarizer).save_transcript(
            row.id, TranscriptSource.caption_auto, "ko", None, []
        )


# --- generate_summary


async def test_generate_summary_50_minutes(db, make, summarizer, env_file) -> None:
    video = await _video(db, make, duration_sec=3000)
    await make.transcript(video.id, [f"문장 {i}" for i in range(300)])
    summarizer.summary_draft = SummaryDraft(
        one_liner="한 줄",
        insights=[(f"인사이트 {i}", [i * 100.0]) for i in range(1, 11)]  # 열 개 와도
        + [("범위 밖", [99999.0]), ("출처 없음", [])],
    )
    await AnalysisService(db, summarizer).generate_summary(video)
    assert [name for name, _ in summarizer.calls] == ["summary"]  # 포트 호출 1회
    rows = list(await db.scalars(select(InsightRow).order_by(InsightRow.seq)))
    assert len(rows) == 8  # 1시간 이하는 8개까지
    s = await db.scalar(select(SummaryRow))
    assert (s.one_liner, s.model) == ("한 줄", "gpt-5-mini")


async def test_generate_summary_clamps_and_drops(db, make, summarizer, env_file) -> None:
    video = await _video(db, make, duration_sec=3000)
    await make.transcript(video.id, [f"문장 {i}" for i in range(300)])  # 0~2990초
    summarizer.summary_draft = SummaryDraft(
        one_liner="한 줄",
        insights=[("범위 밖", [99999.0, 12.0]), ("출처 없음", []), ("정상", [760.0])],
    )
    await AnalysisService(db, summarizer).generate_summary(video)
    rows = list(await db.scalars(select(InsightRow).order_by(InsightRow.seq)))
    assert [(r.text, r.source_secs) for r in rows] == [
        ("범위 밖", [12.0, 2990.0]),
        ("정상", [760.0]),
    ]


async def test_generate_summary_long_video_allows_ten(db, make, summarizer, env_file) -> None:
    video = await _video(db, make, duration_sec=9000)
    await make.transcript(video.id, ["짧은 문장"] * 50, step=180)
    summarizer.summary_draft = SummaryDraft(
        one_liner="한 줄", insights=[(f"{i}", [i * 60.0]) for i in range(1, 13)]
    )
    await AnalysisService(db, summarizer).generate_summary(video)
    assert await _count(db, InsightRow) == 10


async def test_generate_summary_twice_one_set(db, make, summarizer, env_file) -> None:
    video = await _video(db, make, duration_sec=3000)
    await make.transcript(video.id, ["문장"] * 10)
    svc = AnalysisService(db, summarizer)
    await svc.generate_summary(video)
    await svc.generate_summary(video)
    assert (await _count(db, SummaryRow), await _count(db, InsightRow)) == (1, 6)


async def test_generate_summary_windowed_is_stub(db, make, summarizer, env_file) -> None:
    video = await _video(db, make, duration_sec=9000)
    await make.transcript(video.id, ["가" * 1000] * 90)  # 글자 90,000 → 토큰 45,000 > 40,000
    with pytest.raises(NotImplementedYet):
        await AnalysisService(db, summarizer).generate_summary(video)
    assert summarizer.calls == []

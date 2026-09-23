"""analysis/service — 스크립트 · 요약 · 챕터 · 추천 질문 · 결과(VA-MS-003). B1 몫(구간 · 파트 갈래는 B2)."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.core.errors import ResultNotReady
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
    await crud.replace_chapters(
        db, row.id, [], [(None, i * 360.0, f"챕터 {i}", ["a"]) for i in range(8)]
    )
    await db.commit()
    chapters = await AnalysisService(db, summarizer).chapters_of(row.id)
    assert [c.seq for c in chapters] == list(range(1, 9))
    assert all(c.part_seq is None for c in chapters)


async def test_chapters_of_with_parts(db, make, summarizer) -> None:
    row = await make.video()
    await crud.replace_chapters(
        db,
        row.id,
        [("앞", 0.0), ("뒤", 3600.0)],
        [(1, 0.0, "하나", ["a"]), (1, 1800.0, "둘", ["a"]), (2, 3600.0, "셋", ["a"])],
    )
    await db.commit()
    chapters = await AnalysisService(db, summarizer).chapters_of(row.id)
    assert [c.part_seq for c in chapters] == [1, 1, 2]


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


async def test_generate_summary_by_windows(db, make, summarizer, env_file) -> None:
    video = await _video(db, make, duration_sec=9000)
    # 글자 90,000 → 토큰 45,000 > 40,000. 100초마다 한 줄 — 30분 구간 다섯
    await make.transcript(video.id, ["가" * 1000] * 90, step=100)
    summarizer.summary_draft = SummaryDraft(
        one_liner="구간 요약", insights=[(f"인사이트 {i}", [i * 100.0]) for i in range(1, 4)]
    )
    await AnalysisService(db, summarizer).generate_summary(video)
    calls = summarizer.calls
    assert [name for name, _ in calls] == ["summary"] * 6  # 구간 5 + 최종 1
    assert [len(segs) for _, segs in calls[:5]] == [18] * 5
    final = calls[5][1]  # 가짜 구간 — 구간마다 한 줄 요약 하나 + 인사이트 셋
    assert len(final) == 5 * 4
    assert [s.start_sec for s in final] == sorted(s.start_sec for s in final)  # 시각순
    summaries = [s.start_sec for s in final if s.text == "구간 요약"]
    assert summaries == [0, 1800, 3600, 5400, 7200]  # 한 줄 요약은 구간 시작 시각에


async def test_generate_summary_long_but_within_limit_is_one_call(
    db, make, summarizer, env_file
) -> None:
    video = await _video(db, make, duration_sec=9000)  # 150분이라도 토큰이 상한 안이면 한 번
    await make.transcript(video.id, ["짧은 문장"] * 90, step=100)
    await AnalysisService(db, summarizer).generate_summary(video)
    assert [name for name, _ in summarizer.calls] == ["summary"]


# --- generate_chapters


async def test_generate_chapters_50_minutes(db, make, summarizer, env_file) -> None:
    video = await _video(db, make, duration_sec=3000)
    await make.transcript(video.id, ["x"] * 30, step=100)
    summarizer.chapter_draft = ChapterDraft(
        parts=[],
        chapters=[
            (None, 700.0, "셋째", ["a", "b", "c", "d"]),  # 요점 넷 → 셋
            (None, 30.0, "첫째", ["a", "b"]),  # 첫 챕터는 0초로 당긴다
            (None, 400.0, "둘째", ["a", "b"]),
            (None, 400.0, "둘째 또", ["a", "b"]),  # 같은 시각 → 뒤 것을 뺀다
            (None, 5000.0, "넷째", ["a", "b"]),  # 길이 밖 → 마지막 구간
        ],
    )
    await AnalysisService(db, summarizer).generate_chapters(video)
    rows = list(await db.scalars(select(ChapterRow).order_by(ChapterRow.seq)))
    assert [(r.seq, r.start_sec, r.title) for r in rows] == [
        (1, 0, "첫째"),
        (2, 400, "둘째"),
        (3, 700, "셋째"),
        (4, 2900, "넷째"),
    ]
    assert rows[2].bullets == ["a", "b", "c"]
    assert all(r.part_id is None for r in rows)
    assert await _count(db, PartRow) == 0


async def test_generate_chapters_twice_one_set(db, make, summarizer, env_file) -> None:
    video = await _video(db, make, duration_sec=3000)
    await make.transcript(video.id, ["x"] * 30, step=100)
    svc = AnalysisService(db, summarizer)
    await svc.generate_chapters(video)
    await svc.generate_chapters(video)
    assert await _count(db, ChapterRow) == 8


async def _parts_and_chapters(db, summarizer, video_id: int) -> tuple[list, list]:
    parts = [(p.seq, p.title, p.start_sec) for p in await crud.parts(db, video_id)]
    chapters = await AnalysisService(db, summarizer).chapters_of(video_id)
    return parts, [(c.part_seq, c.start_sec) for c in chapters]


async def test_generate_chapters_150_minutes_model_parts(db, make, summarizer, env_file) -> None:
    video = await _video(db, make, duration_sec=9000)
    await make.transcript(video.id, ["x"] * 90, step=100)  # 0 ~ 8900초
    summarizer.chapter_draft = ChapterDraft(
        parts=[("오전 1", 300.0), ("오후", 5400.0), ("오전 2", 2400.0), ("빈 파트", 8950.0)],
        chapters=[
            (1, 0.0, "시작", ["a", "b"]),
            (1, 1200.0, "둘", ["a", "b"]),
            (3, 2500.0, "셋", ["a", "b"]),  # 모델의 파트 번호가 아니라 시각으로 정한다
            (2, 3600.0, "넷", ["a", "b"]),
            (3, 6000.0, "다섯", ["a", "b"]),
        ],
    )
    await AnalysisService(db, summarizer).generate_chapters(video)
    parts, chapters = await _parts_and_chapters(db, summarizer, video.id)
    # 시각순 · 첫 파트 0초로 당김 · 챕터가 없는 파트(8900초)는 빠진다
    assert parts == [(1, "오전 1", 0), (2, "오전 2", 2400), (3, "오후", 5400)]
    assert chapters == [(1, 0), (1, 1200), (2, 2500), (2, 3600), (3, 6000)]


async def test_generate_chapters_one_model_part_groups_by_hour(
    db, make, summarizer, env_file
) -> None:
    video = await _video(db, make, duration_sec=9000)
    await make.transcript(video.id, ["x"] * 90, step=100)
    starts = [0.0, 1800.0, 3700.0, 5000.0, 7300.0, 7400.0]
    summarizer.chapter_draft = ChapterDraft(
        parts=[("하나뿐", 0.0)],
        chapters=[(None, st, f"챕터 {int(st)}", ["a", "b"]) for st in starts],
    )
    await AnalysisService(db, summarizer).generate_chapters(video)
    parts, chapters = await _parts_and_chapters(db, summarizer, video.id)
    # 60분 묶음 — 제목은 묶음의 첫 챕터 제목, 시작은 그 챕터(첫 파트는 0초)
    assert parts == [(1, "챕터 0", 0), (2, "챕터 3700", 3700), (3, "챕터 7300", 7300)]
    assert [p for p, _ in chapters] == [1, 1, 2, 2, 3, 3]


async def test_generate_chapters_by_windows(db, make, summarizer, env_file) -> None:
    video = await _video(db, make, duration_sec=9000)
    await make.transcript(video.id, ["가" * 1000] * 90, step=100)  # 토큰이 상한을 넘는다
    windows: list[float] = []

    async def chapters(segments, duration_sec, model):
        start = segments[0].start_sec
        windows.append(start)
        return ChapterDraft(
            parts=[("무시", 0.0)],  # 구간 갈래는 파트를 60분 묶음으로 만든다
            chapters=[(None, start, f"{int(start)}", ["a", "b"]), (None, start + 600, "뒤", ["a"])],
        )

    summarizer.chapters = chapters
    await AnalysisService(db, summarizer).generate_chapters(video)
    assert windows == [0, 1800, 3600, 5400, 7200]  # 30분 구간 다섯
    parts, chapters_ = await _parts_and_chapters(db, summarizer, video.id)
    assert len(chapters_) == 10
    assert parts == [(1, "0", 0), (2, "3600", 3600), (3, "7200", 7200)]


# --- generate_questions


async def test_generate_questions(db, make, summarizer, env_file) -> None:
    video = await _video(db, make)
    await make.transcript(video.id, ["문장"] * 10)
    summarizer.question_list = ["하나?", "둘?", " ", "둘?", "셋?", "넷?", "다섯?"]
    svc = AnalysisService(db, summarizer)
    await svc.generate_questions(video)
    await svc.generate_questions(video)  # 두 번 돌려도 셋
    rows = list(await db.scalars(select(SuggestedQuestionRow).order_by(SuggestedQuestionRow.seq)))
    assert [r.text for r in rows] == ["하나?", "둘?", "셋?"]


async def test_generate_questions_samples_long_script(db, make, summarizer, env_file) -> None:
    video = await _video(db, make, duration_sec=9000)
    await make.transcript(video.id, ["가" * 1000] * 90)
    await AnalysisService(db, summarizer).generate_questions(video)
    _, sent = summarizer.calls[0]
    assert sum(len(s.text) for s in sent) // 2 <= 40000 + 1000  # 앞 · 가운데 · 끝에서 상한의 셋째씩
    seqs = [s.seq for s in sent]
    assert seqs[0] == 1 and seqs[-1] == 90 and 45 in seqs


# --- result_of


async def test_result_not_ready(db, make, summarizer) -> None:
    video = await _video(db, make, JobStatus.running)
    with pytest.raises(ResultNotReady) as e:
        await AnalysisService(db, summarizer).result_of(video)
    assert e.value.extra == {"video_status": "in_progress"}


async def test_result_of(db, make, summarizer, youtube, env_file, queries) -> None:
    video = await _video(db, make, duration_sec=3000)
    await make.transcript(video.id, ["x"] * 30, step=100)
    svc = AnalysisService(db, summarizer)
    await svc.generate_summary(video)
    await svc.generate_chapters(video)
    await svc.generate_questions(video)
    await make.job(video.id, JobStatus.done)
    done = (await VideoService(db, youtube, None).get(video.id)).video
    queries.clear()
    result = await svc.result_of(done)
    assert len(queries) <= 6  # 쿼리 여섯을 넘지 않는다
    assert len(result.transcript.segments) == 30
    assert (result.transcript.source, result.models.stt, result.models.text) == (
        "caption_manual",
        None,
        "gpt-5-mini",
    )
    assert len(result.summary.insights) == 6
    assert (len(result.chapters), result.parts) == (8, [])
    assert [q.text for q in result.suggested_questions] == summarizer.question_list
    assert result.analyzed_at == done.analyzed_at
    assert result.video == done


async def test_result_of_parts_end_and_counts(db, make, summarizer, env_file) -> None:
    row = await make.video(duration_sec=9000)
    await make.transcript(row.id, ["x"] * 90, step=100)
    s = SummaryRow(video_id=row.id, one_liner="한 줄", model="gpt-5-mini")
    db.add(s)
    p1 = PartRow(video_id=row.id, seq=1, title="앞", start_sec=0)
    p2 = PartRow(video_id=row.id, seq=2, title="뒤", start_sec=4000)
    db.add_all([p1, p2])
    await db.flush()
    db.add_all(
        [
            ChapterRow(video_id=row.id, part_id=p1.id, seq=1, start_sec=0, title="가", bullets=[]),
            ChapterRow(
                video_id=row.id, part_id=p1.id, seq=2, start_sec=2000, title="나", bullets=[]
            ),
            ChapterRow(
                video_id=row.id, part_id=p2.id, seq=3, start_sec=4000, title="다", bullets=[]
            ),
        ]
    )
    await db.commit()
    await make.job(row.id, JobStatus.done)
    video = VideoService.to_dto(row, await JobService(db).latest(row.id), 0)
    result = await AnalysisService(db, summarizer).result_of(video)
    assert [(p.seq, p.start_sec, p.end_sec, p.chapter_count) for p in result.parts] == [
        (1, 0, 4000, 2),
        (2, 4000, 9000, 1),
    ]
    assert [c.part_seq for c in result.chapters] == [1, 1, 2]

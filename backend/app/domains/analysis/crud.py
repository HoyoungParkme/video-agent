"""결과 테이블 일곱 접근 — DB만. 판단은 service가 한다.

여러 줄을 넣을 때는 한 번에(executemany) — 3,000줄 스크립트도 쿼리 하나다.
"""

from __future__ import annotations

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.domains.analysis.schemas import CaptionLine


async def replace_transcript(
    session: AsyncSession,
    video_id: int,
    source: TranscriptSource,
    language: str,
    model: str | None,
    lines: list[CaptionLine],
) -> None:
    """스크립트를 갈아 끼운다 — 지우면 구간도 cascade로 지워진다. 커밋은 service가."""
    await session.execute(delete(TranscriptRow).where(TranscriptRow.video_id == video_id))
    row = TranscriptRow(video_id=video_id, source=source, language=language, model=model)
    session.add(row)
    await session.flush()
    await session.execute(
        insert(SegmentRow),
        [
            {
                "transcript_id": row.id,
                "seq": i,
                "start_sec": line.start_sec,
                "end_sec": line.end_sec,
                "text": line.text,
            }
            for i, line in enumerate(lines, 1)
        ],
    )


async def transcript(session: AsyncSession, video_id: int) -> TranscriptRow | None:
    return await session.scalar(select(TranscriptRow).where(TranscriptRow.video_id == video_id))


async def segments_of_transcript(session: AsyncSession, transcript_id: int) -> list[SegmentRow]:
    return list(
        await session.scalars(
            select(SegmentRow)
            .where(SegmentRow.transcript_id == transcript_id)
            .order_by(SegmentRow.seq)
        )
    )


async def segments(session: AsyncSession, video_id: int) -> list[SegmentRow]:
    """영상의 구간들, 시각순 — 스크립트와 이어 한 쿼리."""
    return list(
        await session.scalars(
            select(SegmentRow)
            .join(TranscriptRow, TranscriptRow.id == SegmentRow.transcript_id)
            .where(TranscriptRow.video_id == video_id)
            .order_by(SegmentRow.seq)
        )
    )


async def replace_summary(
    session: AsyncSession,
    video_id: int,
    one_liner: str,
    model: str,
    insights: list[tuple[str, list[float]]],
) -> None:
    """요약을 갈아 끼운다 — 지우면 인사이트도 cascade로 지워진다."""
    await session.execute(delete(SummaryRow).where(SummaryRow.video_id == video_id))
    row = SummaryRow(video_id=video_id, one_liner=one_liner, model=model)
    session.add(row)
    await session.flush()
    if insights:
        await session.execute(
            insert(InsightRow),
            [
                {"summary_id": row.id, "seq": i, "text": text, "source_secs": secs}
                for i, (text, secs) in enumerate(insights, 1)
            ],
        )


async def summary_with_insights(
    session: AsyncSession, video_id: int
) -> tuple[SummaryRow | None, list[InsightRow]]:
    """요약과 인사이트(번호순) — 한 쿼리."""
    rows = (
        await session.execute(
            select(SummaryRow, InsightRow)
            .outerjoin(InsightRow, InsightRow.summary_id == SummaryRow.id)
            .where(SummaryRow.video_id == video_id)
            .order_by(InsightRow.seq)
        )
    ).all()
    if not rows:
        return None, []
    return rows[0][0], [ins for _, ins in rows if ins is not None]


async def replace_chapters(
    session: AsyncSession,
    video_id: int,
    parts: list[tuple[str, float]],
    chapters: list[tuple[int | None, float, str, list[str]]],
) -> None:
    """파트와 챕터를 갈아 끼운다. 파트는 (제목, 시작), 챕터는 (파트 번호 1부터 또는 None, 시작,
    제목, 요점). 파트 행을 먼저 넣어 id를 받고 챕터에 잇는다(복합 FK)."""
    await session.execute(delete(ChapterRow).where(ChapterRow.video_id == video_id))
    await session.execute(delete(PartRow).where(PartRow.video_id == video_id))
    part_rows = [
        PartRow(video_id=video_id, seq=i, title=title, start_sec=start)
        for i, (title, start) in enumerate(parts, 1)
    ]
    session.add_all(part_rows)
    await session.flush()
    ids = {p.seq: p.id for p in part_rows}
    if chapters:
        await session.execute(
            insert(ChapterRow),
            [
                {
                    "video_id": video_id,
                    "part_id": ids.get(part) if part is not None else None,
                    "seq": i,
                    "start_sec": start,
                    "title": title,
                    "bullets": bullets,
                }
                for i, (part, start, title, bullets) in enumerate(chapters, 1)
            ],
        )


async def parts(session: AsyncSession, video_id: int) -> list[PartRow]:
    return list(
        await session.scalars(
            select(PartRow).where(PartRow.video_id == video_id).order_by(PartRow.seq)
        )
    )


async def chapters_with_part_seq(
    session: AsyncSession, video_id: int
) -> list[tuple[ChapterRow, int | None]]:
    """챕터(번호순)와 그 파트의 번호 — 한 쿼리. 파트가 없으면 None."""
    rows = await session.execute(
        select(ChapterRow, PartRow.seq)
        .outerjoin(PartRow, PartRow.id == ChapterRow.part_id)
        .where(ChapterRow.video_id == video_id)
        .order_by(ChapterRow.seq)
    )
    return [(c, seq) for c, seq in rows.tuples()]


async def replace_questions(session: AsyncSession, video_id: int, texts: list[str]) -> None:
    await session.execute(
        delete(SuggestedQuestionRow).where(SuggestedQuestionRow.video_id == video_id)
    )
    if texts:
        await session.execute(
            insert(SuggestedQuestionRow),
            [{"video_id": video_id, "seq": i, "text": t} for i, t in enumerate(texts, 1)],
        )


async def questions(session: AsyncSession, video_id: int) -> list[SuggestedQuestionRow]:
    return list(
        await session.scalars(
            select(SuggestedQuestionRow)
            .where(SuggestedQuestionRow.video_id == video_id)
            .order_by(SuggestedQuestionRow.seq)
        )
    )

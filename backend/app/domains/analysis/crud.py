"""결과 테이블 여덟 접근 — DB만. 판단은 service가 한다.

여러 줄을 넣을 때는 한 번에(executemany) — 3,000줄 스크립트도 쿼리 하나다.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ImageQuality
from app.domains.analysis.models import (
    ChapterFrameRow,
    ChapterRow,
    FrameSource,
    InfographicRow,
    InfographicState,
    InsightRow,
    PartRow,
    SegmentRow,
    SuggestedQuestionRow,
    SummaryRow,
    TranscriptRow,
    TranscriptSource,
)
from app.domains.analysis.schemas import CaptionLine
from app.domains.video.models import VideoRow


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


async def chapter_rows(session: AsyncSession, video_id: int) -> list[ChapterRow]:
    """챕터 행, 번호순."""
    return list(
        await session.scalars(
            select(ChapterRow).where(ChapterRow.video_id == video_id).order_by(ChapterRow.seq)
        )
    )


async def frames(session: AsyncSession, video_id: int) -> list[ChapterFrameRow]:
    """영상의 장면 행(그림 컬럼이 null인 「해 봤다」 행 포함) — 챕터와 조인, 챕터 번호순."""
    return list(
        await session.scalars(
            select(ChapterFrameRow)
            .join(ChapterRow, ChapterRow.id == ChapterFrameRow.chapter_id)
            .where(ChapterRow.video_id == video_id)
            .order_by(ChapterRow.seq)
        )
    )


async def add_frame(
    session: AsyncSession,
    chapter_id: int,
    sec: float | None = None,
    source: FrameSource | None = None,
    width: int | None = None,
    height: int | None = None,
    path: str | None = None,
) -> None:
    """장면 행 하나. 그림 없이 부르면 「해 봤지만 없다」 행이다(CHECK — 모두 있거나 모두 null)."""
    session.add(
        ChapterFrameRow(
            chapter_id=chapter_id, sec=sec, source=source, width=width, height=height, path=path
        )
    )
    await session.flush()


async def frame_by_seq(session: AsyncSession, video_id: int, seq: int) -> ChapterFrameRow | None:
    """그 영상의 seq번 챕터의 장면 행."""
    return await session.scalar(
        select(ChapterFrameRow)
        .join(ChapterRow, ChapterRow.id == ChapterFrameRow.chapter_id)
        .where(ChapterRow.video_id == video_id, ChapterRow.seq == seq)
    )


async def infographic(session: AsyncSession, video_id: int) -> InfographicRow | None:
    """그 영상의 인포그래픽 행. 없으면 None(만든 적 없음). 행은 SQL 한 문장(claim · finish)으로도
    바뀌어 세션에 든 옛 값을 쓰지 않게 늘 새로 읽는다."""
    return await session.scalar(
        select(InfographicRow)
        .where(InfographicRow.video_id == video_id)
        .execution_options(populate_existing=True)
    )


async def claim_infographic(session: AsyncSession, video_id: int) -> bool:
    """그리는 중(making)으로 — 행이 없으면 만들고, making이 아니면 바꾼다. 한 문장이라 겹친 요청은
    하나만 바꾼다. 그림 컬럼은 건드리지 않는다(이전 그림이 보인다). 이미 making이면 False."""
    stmt = (
        pg_insert(InfographicRow)
        .values(video_id=video_id, state=InfographicState.making)
        .on_conflict_do_update(
            index_elements=[InfographicRow.video_id],
            set_={"state": InfographicState.making, "error_reason": None},
            where=InfographicRow.state != InfographicState.making,
        )
        .returning(InfographicRow.id)
    )
    return await session.scalar(stmt) is not None


async def video_title(session: AsyncSession, video_id: int) -> str | None:
    """영상 제목 — 인포그래픽 재료. 뒤 태스크는 영상 DTO가 없어 id로 읽는다."""
    return await session.scalar(select(VideoRow.title).where(VideoRow.id == video_id))


async def finish_infographic(
    session: AsyncSession,
    video_id: int,
    *,
    model: str,
    quality: ImageQuality,
    width: int,
    height: int,
    cost_usd: float,
    path: str,
    created_at: datetime,
) -> None:
    """다 그렸다 — done과 새 그림 컬럼, 실패 이유는 지운다."""
    await session.execute(
        update(InfographicRow)
        .where(InfographicRow.video_id == video_id)
        .values(
            state=InfographicState.done,
            model=model,
            quality=quality,
            width=width,
            height=height,
            cost_usd=cost_usd,
            path=path,
            created_at=created_at,
            error_reason=None,
        )
    )


async def fail_infographic(session: AsyncSession, video_id: int, reason: str) -> None:
    """그리지 못했다 — failed와 이유. 그림 컬럼은 그대로(이전 그림이 남는다)."""
    await session.execute(
        update(InfographicRow)
        .where(InfographicRow.video_id == video_id)
        .values(state=InfographicState.failed, error_reason=reason)
    )


async def fail_making_infographics(session: AsyncSession, reason: str) -> int:
    """그리는 중(making)인 행 전부를 failed와 이유로 — 그림 컬럼은 그대로. 바꾼 행 수."""
    result = await session.execute(
        update(InfographicRow)
        .where(InfographicRow.state == InfographicState.making)
        .values(state=InfographicState.failed, error_reason=reason)
    )
    return result.rowcount

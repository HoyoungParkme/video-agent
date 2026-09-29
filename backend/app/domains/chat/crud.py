"""chat_turns 접근 — DB만. 판단은 service가 한다."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.chat.models import ChatTurnRow


async def counts(session: AsyncSession, video_ids: list[int]) -> dict[int, int]:
    """영상마다 턴 수 — 한 쿼리. 턴이 없는 영상은 키가 없다."""
    rows = await session.execute(
        select(ChatTurnRow.video_id, func.count())
        .where(ChatTurnRow.video_id.in_(video_ids))
        .group_by(ChatTurnRow.video_id)
    )
    return {video_id: n for video_id, n in rows.tuples()}


async def turns(session: AsyncSession, video_id: int) -> list[ChatTurnRow]:
    """영상의 턴 전부, 시간순(같은 시각이면 넣은 순서)."""
    rows = await session.scalars(
        select(ChatTurnRow)
        .where(ChatTurnRow.video_id == video_id)
        .order_by(ChatTurnRow.asked_at, ChatTurnRow.id)
    )
    return list(rows)


async def recent(session: AsyncSession, video_id: int, limit: int) -> list[ChatTurnRow]:
    """최근 턴 limit개, 새것부터."""
    rows = await session.scalars(
        select(ChatTurnRow)
        .where(ChatTurnRow.video_id == video_id)
        .order_by(ChatTurnRow.asked_at.desc(), ChatTurnRow.id.desc())
        .limit(limit)
    )
    return list(rows)


def add(
    session: AsyncSession,
    video_id: int,
    question: str,
    answer: str,
    cited_secs: list[float],
    model: str,
    asked_at: datetime,
) -> ChatTurnRow:
    """새 턴. 커밋은 service가 한다."""
    row = ChatTurnRow(
        video_id=video_id,
        question=question,
        answer=answer,
        cited_secs=cited_secs,
        model=model,
        asked_at=asked_at,
    )
    session.add(row)
    return row

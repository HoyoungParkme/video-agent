"""chat_turns 접근 — DB만. 판단은 service가 한다."""

from __future__ import annotations

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

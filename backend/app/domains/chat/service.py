"""ChatService — 영상에 질문하기(VA-MS-004). 기록 · 질문 · 맥락 고르기 · 영상 목록의 턴 수.

세션은 부르는 쪽(라우터 · VideoService)의 것이다.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.chat import crud
from app.domains.chat.models import ChatTurnRow
from app.domains.chat.schemas import ChatTurn


def _turn(row: ChatTurnRow) -> ChatTurn:
    return ChatTurn(
        id=row.id,
        question=row.question,
        answer=row.answer,
        cited_secs=row.cited_secs,
        asked_at=row.asked_at,
    )


class ChatService:
    """대화 턴을 읽고 쓴다.

    - history(): 영상의 대화 턴, 시간순
    - count_by_videos(): 영상마다 턴 수, 쿼리 하나
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def history(self, video_id: int) -> list[ChatTurn]:
        """VA-MS-004#ChatService.history

        영상의 대화 턴, 시간순(같은 시각이면 넣은 순서). 실패한 질문은 저장하지 않으므로 없다.
        영상이 있는지는 라우터가 VideoService.get으로 먼저 본다.

        Args:
            video_id: 영상 id

        Returns:
            턴 목록. 없으면 빈 목록(결과 없는 영상도 — 에러가 아니다)
        """
        return [_turn(r) for r in await crud.turns(self.session, video_id)]

    async def count_by_videos(self, video_ids: list[int]) -> dict[int, int]:
        """VA-MS-004#ChatService.count_by_videos

        영상마다 저장된 턴 수. 목록이 영상 수만큼 쿼리를 쓰지 않게 한 번에 센다.

        Args:
            video_ids: 영상 id들

        Returns:
            {영상 id: 턴 수}. 턴이 없는 영상은 키가 없다(부르는 쪽이 `.get(id, 0)`)
        """
        if not video_ids:
            return {}
        return await crud.counts(self.session, video_ids)

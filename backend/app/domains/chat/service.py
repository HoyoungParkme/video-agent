"""ChatService — 영상에 질문하기(VA-MS-004). B1은 영상 목록에 붙는 턴 수만 — 질문 · 기록은 B3.

세션은 부르는 쪽(라우터 · VideoService)의 것이다.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.chat import crud


class ChatService:
    """대화 턴을 읽고 쓴다.

    - count_by_videos(): 영상마다 턴 수, 쿼리 하나
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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

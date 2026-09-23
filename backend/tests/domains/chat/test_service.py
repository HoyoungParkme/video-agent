"""chat/service — B1은 count_by_videos 하나(VA-MS-004)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domains.chat.models import ChatTurnRow
from app.domains.chat.service import ChatService


async def test_count_by_videos(db, make, queries) -> None:
    videos = [await make.video() for _ in range(50)]
    for n, v in enumerate(videos[:3], 1):
        for _ in range(n):
            db.add(
                ChatTurnRow(
                    video_id=v.id,
                    question="q",
                    answer="a",
                    cited_secs=[],
                    model="m",
                    asked_at=datetime.now(UTC),
                )
            )
    await db.commit()
    queries.clear()
    counts = await ChatService(db).count_by_videos([v.id for v in videos])
    assert len(queries) == 1  # 영상 50개에 쿼리 하나
    assert counts == {videos[0].id: 1, videos[1].id: 2, videos[2].id: 3}  # 턴 0개 영상은 키 없음


async def test_count_by_videos_empty(db, queries) -> None:
    assert await ChatService(db).count_by_videos([]) == {}
    assert queries == []

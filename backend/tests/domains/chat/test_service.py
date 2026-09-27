"""chat/service — 대화 기록 · 질문 · 맥락 고르기 · 턴 수(VA-MS-004)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

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


# --- history

T0 = datetime(2026, 9, 27, 3, 0, tzinfo=UTC)


async def test_history_in_time_order(db, make) -> None:
    video = await make.video()
    await make.turn(video.id, "둘째", at=T0 + timedelta(seconds=5))
    await make.turn(video.id, "첫째", "근거 있는 답", cited=[60.0], at=T0)
    await make.turn(video.id, "같은 초", at=T0)  # 같은 시각이면 넣은 순서(id)
    turns = await ChatService(db).history(video.id)
    assert [t.question for t in turns] == ["첫째", "같은 초", "둘째"]
    assert (turns[0].answer, turns[0].cited_secs, turns[0].asked_at) == ("근거 있는 답", [60.0], T0)


async def test_history_empty_is_not_error(db, make) -> None:
    video = await make.video()  # 결과 없는 영상도 빈 목록
    assert await ChatService(db).history(video.id) == []

"""chat/service — 대화 기록 · 질문 · 맥락 고르기 · 턴 수(VA-MS-004)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.config import config
from app.domains.chat.models import ChatTurnRow
from app.domains.chat.service import ChatService
from app.domains.video.service import VideoService


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


# --- context_for

# 3시간 영상 — 줄마다 60초(180줄, 한 줄 30자). 챕터 여섯은 30분마다
TITLES = ["소개", "RAG 비용 이야기", "pgvector 선택", "재순위와 지연", "운영", "정리"]


async def _long_video(make):
    row = await make.video(duration_sec=10800)
    await make.transcript(row.id, [f"{i:03d}번째 줄 " + "가" * 22 for i in range(180)], step=60)
    await make.chapters(row.id, [(i * 1800.0, t, ["요점"]) for i, t in enumerate(TITLES)])
    return row


def _range(segments) -> tuple[float, float, int]:
    return segments[0].start_sec, segments[-1].start_sec, len(segments)


async def test_context_all_segments_when_short(db, make) -> None:
    row = await make.video()
    await make.transcript(row.id, ["하나", "둘", "셋"])  # 50분짜리 영상 — 상한 안
    context = await ChatService(db).context_for(VideoService.to_dto(row, None, 0), "아무 질문")
    assert [s.text for s in context] == ["하나", "둘", "셋"]


async def test_context_picks_matching_chapter(db, make, monkeypatch) -> None:
    # 전부(2,700)는 상한을 넘고 세 챕터(1,350)는 든다
    monkeypatch.setattr(config, "CHAT_TOKEN_LIMIT", 2000)
    row = await _long_video(make)
    video = VideoService.to_dto(row, None, 0)
    context = await ChatService(db).context_for(video, "RAG 비용 얼마였어?")
    assert _range(context) == (1800.0, 3540.0, 30)  # 제목에 '비용'이 든 챕터의 구간만, 시각순
    again = await ChatService(db).context_for(video, "RAG 비용은?")  # 조사가 붙어도 맞는다
    assert _range(again) == (1800.0, 3540.0, 30)


async def test_context_first_chapters_when_nothing_matches(db, make, monkeypatch) -> None:
    monkeypatch.setattr(config, "CHAT_TOKEN_LIMIT", 2000)
    row = await _long_video(make)
    context = await ChatService(db).context_for(VideoService.to_dto(row, None, 0), "날씨는 어때?")
    assert _range(context) == (0.0, 5340.0, 90)  # 앞 세 챕터


async def test_context_drops_lowest_chapters_over_limit(db, make, monkeypatch) -> None:
    monkeypatch.setattr(config, "CHAT_TOKEN_LIMIT", 1000)  # 세 챕터(1,350)는 넘는다
    row = await _long_video(make)
    context = await ChatService(db).context_for(VideoService.to_dto(row, None, 0), "날씨는 어때?")
    assert _range(context) == (0.0, 3540.0, 60)  # 뒤 챕터부터 뺀다


async def test_context_follow_up_uses_last_cited_chapter(db, make, monkeypatch) -> None:
    monkeypatch.setattr(config, "CHAT_TOKEN_LIMIT", 2000)
    row = await _long_video(make)
    await make.turn(row.id, "어떤 DB를 썼어?", "pgvector를 썼다고 합니다.", cited=[4000.0], at=T0)
    context = await ChatService(db).context_for(VideoService.to_dto(row, None, 0), "그거 성능은?")
    assert _range(context) == (3600.0, 5340.0, 30)  # 직전 턴의 근거가 든 'pgvector 선택' 챕터

"""chat/service — 대화 기록 · 질문 · 맥락 고르기 · 턴 수(VA-MS-004)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core.config import config
from app.core.errors import (
    KeyInvalid,
    KeyMissing,
    LlmUnavailable,
    ResultNotReady,
    Validation,
)
from app.core.settings import settings
from app.domains.chat.models import ChatTurnRow
from app.domains.chat.schemas import AnswerDraft
from app.domains.chat.service import ChatService
from app.domains.job.models import JobStatus
from app.domains.video.service import VideoService
from app.infra.openai import KeyCheck, KeyState, ReasonKind


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

# 3시간 영상 — 줄마다 60초(180줄, 한 줄 80바이트 → 28토큰). 챕터 여섯은 30분마다(30줄 → 840토큰)
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
    # 전부(5,040)는 상한을 넘고 세 챕터(2,520)는 든다
    monkeypatch.setattr(config, "CHAT_TOKEN_LIMIT", 3000)
    row = await _long_video(make)
    video = VideoService.to_dto(row, None, 0)
    context = await ChatService(db).context_for(video, "RAG 비용 얼마였어?")
    assert _range(context) == (1800.0, 3540.0, 30)  # 제목에 '비용'이 든 챕터의 구간만, 시각순
    again = await ChatService(db).context_for(video, "RAG 비용은?")  # 조사가 붙어도 맞는다
    assert _range(again) == (1800.0, 3540.0, 30)


async def test_context_first_chapters_when_nothing_matches(db, make, monkeypatch) -> None:
    monkeypatch.setattr(config, "CHAT_TOKEN_LIMIT", 3000)
    row = await _long_video(make)
    context = await ChatService(db).context_for(VideoService.to_dto(row, None, 0), "날씨는 어때?")
    assert _range(context) == (0.0, 5340.0, 90)  # 앞 세 챕터


async def test_context_drops_lowest_chapters_over_limit(db, make, monkeypatch) -> None:
    monkeypatch.setattr(config, "CHAT_TOKEN_LIMIT", 2000)  # 세 챕터(2,520)는 넘고 둘(1,680)은 든다
    row = await _long_video(make)
    context = await ChatService(db).context_for(VideoService.to_dto(row, None, 0), "날씨는 어때?")
    assert _range(context) == (0.0, 3540.0, 60)  # 뒤 챕터부터 뺀다


async def test_context_ignores_one_letter_words(db, make, monkeypatch) -> None:
    monkeypatch.setattr(config, "CHAT_TOKEN_LIMIT", 3000)
    row = await _long_video(make)
    video = VideoService.to_dto(row, None, 0)
    # 'a' · 'b'는 'RAG'에도 들어 있다 — 한 글자 낱말을 세면 비용 챕터가 뽑힌다
    context = await ChatService(db).context_for(video, "A/B 테스트 결과는?")
    assert _range(context) == (0.0, 5340.0, 90)  # 맞는 것이 없다 — 앞 세 챕터


async def test_context_keeps_one_chapter_over_limit(db, make, monkeypatch) -> None:
    monkeypatch.setattr(config, "CHAT_TOKEN_LIMIT", 100)  # 챕터 하나(840)도 넘는다
    row = await _long_video(make)
    context = await ChatService(db).context_for(VideoService.to_dto(row, None, 0), "RAG 비용은?")
    assert _range(context) == (1800.0, 3540.0, 30)  # 그 챕터를 통째로 — 안을 자르지 않는다


async def test_context_follow_up_uses_last_cited_chapter(db, make, monkeypatch) -> None:
    monkeypatch.setattr(config, "CHAT_TOKEN_LIMIT", 3000)
    row = await _long_video(make)
    await make.turn(row.id, "어떤 DB를 썼어?", "pgvector를 썼다고 합니다.", cited=[4000.0], at=T0)
    context = await ChatService(db).context_for(VideoService.to_dto(row, None, 0), "그거 성능은?")
    assert _range(context) == (3600.0, 5340.0, 30)  # 직전 턴의 근거가 든 'pgvector 선택' 챕터


# --- ask


async def _analyzed(db, make, youtube, probe):
    row = await make.video()  # 3,000초
    await make.job(row.id)  # 끝난 작업 — analyzed
    await make.transcript(row.id, ["하나", "둘", "셋"])
    return (await VideoService(db, youtube, probe).get(row.id)).video


async def test_ask_saves_turn(db, make, youtube, probe, key, answerer) -> None:
    video = await _analyzed(db, make, youtube, probe)
    svc = ChatService(db, answerer)
    turn = await svc.ask(video, "  어떤 DB를 썼어?  ")
    assert (turn.question, turn.answer, turn.cited_secs) == (
        "어떤 DB를 썼어?",
        "PostgreSQL을 썼다고 합니다.",
        [60.0, 120.0],
    )
    question, context, history, model = answerer.calls[0]
    assert (question, [s.text for s in context], history, model) == (
        "어떤 DB를 썼어?",
        ["하나", "둘", "셋"],
        [],
        "gpt-5.6-luna",
    )
    assert await svc.count_by_videos([video.id]) == {video.id: 1}
    assert (await db.get(ChatTurnRow, turn.id)).model == "gpt-5.6-luna"


async def test_ask_port_failure_keeps_nothing(db, make, youtube, probe, key, answerer) -> None:
    video = await _analyzed(db, make, youtube, probe)
    answerer.error = LlmUnavailable(reason="OpenAI 서버 오류")
    with pytest.raises(LlmUnavailable) as e:
        await ChatService(db, answerer).ask(video, "질문")
    assert e.value.extra == {"reason": "OpenAI 서버 오류"}  # 포트의 이유 그대로
    assert await ChatService(db).history(video.id) == []  # 실패한 질문은 저장하지 않는다


async def test_ask_timeout(db, make, youtube, probe, key, answerer, monkeypatch) -> None:
    video = await _analyzed(db, make, youtube, probe)
    monkeypatch.setattr(config, "CHAT_TIMEOUT_SEC", 0.05)
    answerer.delay = 1
    with pytest.raises(LlmUnavailable) as e:
        await ChatService(db, answerer).ask(video, "질문")
    assert e.value.extra == {"reason": "응답 시간 초과"}
    assert await ChatService(db).history(video.id) == []


async def test_ask_empty_question(db, make, youtube, probe, key, answerer) -> None:
    video = await _analyzed(db, make, youtube, probe)
    for question in ["", "   \n"]:
        with pytest.raises(Validation):
            await ChatService(db, answerer).ask(video, question)
    assert answerer.calls == []


async def test_ask_long_question_is_cut(db, make, youtube, probe, key, answerer) -> None:
    video = await _analyzed(db, make, youtube, probe)
    turn = await ChatService(db, answerer).ask(video, "가" * 2500)
    assert len(turn.question) == 2000


async def test_ask_needs_result(db, make, youtube, probe, key, answerer) -> None:
    row = await make.video()
    await make.job(row.id, JobStatus.running)
    video = (await VideoService(db, youtube, probe).get(row.id)).video
    with pytest.raises(ResultNotReady) as e:
        await ChatService(db, answerer).ask(video, "질문")
    assert e.value.extra == {"video_status": "in_progress"}
    assert answerer.calls == []


async def test_ask_sends_last_ten_turns_in_order(db, make, youtube, probe, key, answerer) -> None:
    video = await _analyzed(db, make, youtube, probe)
    for i in range(12):
        await make.turn(video.id, f"질문 {i}", at=T0 + timedelta(minutes=i))
    await ChatService(db, answerer).ask(video, "그거 성능은?")
    history = answerer.calls[0][2]
    assert [t.question for t in history] == [f"질문 {i}" for i in range(2, 12)]


async def test_ask_drops_times_outside_video(db, make, youtube, probe, key, answerer) -> None:
    video = await _analyzed(db, make, youtube, probe)
    answerer.draft = AnswerDraft("답", [120.0, -1.0, 99999.0, 60.0, 120.0])
    turn = await ChatService(db, answerer).ask(video, "질문")
    assert turn.cited_secs == [60.0, 120.0]  # 범위 밖은 버리고, 오름차순 · 중복 없이


async def test_ask_not_covered_saved_without_times(db, make, youtube, probe, key, answerer):
    video = await _analyzed(db, make, youtube, probe)
    answerer.draft = AnswerDraft(f"{config.NOT_COVERED_TEXT} 매출 이야기는 없어요.", [])
    turn = await ChatService(db, answerer).ask(video, "발표자 회사 매출은?")
    assert turn.cited_secs == []
    assert [t.id for t in await ChatService(db).history(video.id)] == [turn.id]


async def test_ask_without_key(db, make, youtube, probe, env_file, verify, answerer) -> None:
    video = await _analyzed(db, make, youtube, probe)
    with pytest.raises(KeyMissing):
        await ChatService(db, answerer).ask(video, "질문")
    assert answerer.calls == []


async def test_ask_rechecks_key_after_network_failure(
    db, make, youtube, probe, key, verify, answerer, monkeypatch
) -> None:
    video = await _analyzed(db, make, youtube, probe)
    offline = KeyCheck(KeyState.invalid, ReasonKind.network, "연결하지 못했습니다", T0)
    monkeypatch.setattr(settings, "last_check", offline)
    verify.fail = ReasonKind.network  # 다시 확인해도 닿지 못한다
    with pytest.raises(KeyInvalid) as e:
        await ChatService(db, answerer).ask(video, "질문")
    assert e.value.extra["reason_kind"] == ReasonKind.network
    assert (answerer.calls, await ChatService(db).history(video.id)) == ([], [])
    verify.fail = None  # 인터넷이 돌아왔다 — 다시 확인이 통과하면 답을 받아 저장한다
    turn = await ChatService(db, answerer).ask(video, "질문")
    assert [t.id for t in await ChatService(db).history(video.id)] == [turn.id]

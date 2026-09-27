"""chat/adapters/answerer_openai — 근거 있는 답(VA-MS-006 answerer_openai.answer). openai.chat은 가짜로."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx2
import openai as sdk
import pytest

from app import prompts
from app.core.config import config
from app.core.errors import LlmUnavailable
from app.domains.analysis.schemas import Segment
from app.domains.chat.adapters.answerer_openai import AnswererOpenAI
from app.domains.chat.schemas import ChatTurn
from app.infra import openai

T0 = datetime(2026, 9, 27, 3, 0, tzinfo=UTC)
REQ = httpx2.Request("POST", "http://fake/v1/chat/completions")


@dataclass
class FakeChat:
    """openai.chat 자리 — 응답(본문 또는 예외)을 차례로 준다. 받은 메시지를 적는다."""

    replies: list[str | Exception] = field(default_factory=list)
    calls: list[list[dict]] = field(default_factory=list)

    async def __call__(
        self, client, model: str, messages: list[dict], json_mode: bool = True
    ) -> str:
        assert json_mode
        self.calls.append(messages)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


@pytest.fixture
def chat(monkeypatch) -> FakeChat:
    fake = FakeChat()
    monkeypatch.setattr(openai, "chat", fake)
    return fake


@pytest.fixture
def answerer() -> AnswererOpenAI:
    return AnswererOpenAI(lambda: object())


def segs(end: float, n: int = 4) -> list[Segment]:
    step = end / n
    return [
        Segment(seq=i + 1, start_sec=i * step, end_sec=(i + 1) * step, text=f"{i + 1}번째 문장")
        for i in range(n)
    ]


def turn(i: int, cited: list[float]) -> ChatTurn:
    return ChatTurn(id=i, question=f"질문 {i}", answer=f"답 {i}", cited_secs=cited, asked_at=T0)


def js(answer: str, times: list[str]) -> str:
    return json.dumps({"answer": answer, "times": times}, ensure_ascii=False)


async def test_times_become_seconds(chat, answerer) -> None:
    chat.replies = [js("PostgreSQL을 썼다고 합니다.", ["12:40", "[24:02]"])]
    draft = await answerer.answer("어떤 DB를 썼어?", segs(3000), [], "gpt-5-mini")
    assert (draft.answer, draft.cited_secs) == ("PostgreSQL을 썼다고 합니다.", [760.0, 1442.0])


async def test_unreadable_times_dropped_and_three_at_most(chat, answerer) -> None:
    chat.replies = [js("답", ["01:00", "모름", "02:00", "03:00", "04:00"])]
    draft = await answerer.answer("질문", segs(3000), [], "gpt-5-mini")
    assert draft.cited_secs == [60.0, 120.0, 180.0]


async def test_not_covered_drops_times(chat, answerer) -> None:
    text = f"{config.NOT_COVERED_TEXT} 매출 이야기는 나오지 않아요."
    chat.replies = [js(text, ["05:00"])]  # 모델이 시각을 붙여도
    draft = await answerer.answer("발표자 회사 매출은?", segs(3000), [], "gpt-5-mini")
    assert (draft.answer, draft.cited_secs) == (text, [])


async def test_messages_history_then_transcript_last(chat, answerer) -> None:
    chat.replies = [js("답", [])]
    history = [turn(1, [760.0]), turn(2, []), turn(3, [4500.0])]
    await answerer.answer("그거 성능은?", segs(3000), history, "gpt-5-mini")
    messages = chat.calls[0]
    assert len(messages) == 8  # system + 앞선 턴 셋(질문 · 답) + 마지막 user
    assert [m["role"] for m in messages] == ["system"] + ["user", "assistant"] * 3 + ["user"]
    assert messages[1]["content"] == "질문 1"
    assert messages[2]["content"] == "답 1 (근거: 12:40)"  # 대명사가 풀리게 근거 시각을 붙인다
    assert messages[4]["content"] == "답 2"  # 근거 없는 답은 그대로
    assert messages[6]["content"] == "답 3 (근거: 75:00)"  # 본문(끝 50분)과 같은 표기
    users = [i for i, m in enumerate(messages) if m["role"] == "user"]
    assert [i for i in users if "<transcript>" in messages[i]["content"]] == [7]
    assert messages[7]["content"].startswith("<transcript>\n[00:00] 1번째 문장\n")
    assert messages[7]["content"].endswith("</transcript>\n\n그거 성능은?")


async def test_history_times_follow_transcript_format(chat, answerer) -> None:
    # 모델이 앞선 턴의 근거를 옮겨 적어도 본문과 같은 끝 시각으로 바로 읽힌다
    chat.replies = [js("답", ["70:00"]), js("답", ["0:30:00"])]
    short = await answerer.answer("그거는?", segs(1800), [turn(1, [4200.0])], "gpt-5-mini")
    assert chat.calls[0][2]["content"] == "답 1 (근거: 70:00)"  # '1:10:00'이면 70초로 읽힌다
    assert short.cited_secs == [4200.0]
    long = await answerer.answer("그거는?", segs(7200), [turn(1, [1800.0])], "gpt-5-mini")
    assert chat.calls[1][2]["content"] == "답 1 (근거: 0:30:00)"
    assert long.cited_secs == [1800.0]


async def test_system_prompt_fills_answer_md(chat, answerer) -> None:
    chat.replies = [js("답", []), js("답", [])]
    await answerer.answer("질문", segs(3000), [], "gpt-5-mini")
    await answerer.answer("질문", segs(7200), [], "gpt-5-mini")  # 1시간 넘는 맥락
    short = prompts.render("answer", time_format="mm:ss", not_covered=config.NOT_COVERED_TEXT)
    long = prompts.render("answer", time_format="h:mm:ss", not_covered=config.NOT_COVERED_TEXT)
    assert chat.calls[0][0]["content"] == short
    assert chat.calls[1][0]["content"] == long
    assert "[1:30:00] 4번째 문장" in chat.calls[1][-1]["content"]


async def test_sdk_error_becomes_llm_unavailable(chat, answerer) -> None:
    error = sdk.APIStatusError("error", response=httpx2.Response(503, request=REQ), body=None)
    chat.replies = [error]
    with pytest.raises(LlmUnavailable) as e:
        await answerer.answer("질문", segs(3000), [], "gpt-5-mini")
    assert e.value.extra == {"reason": "OpenAI 서버 오류"}
    assert len(chat.calls) == 1  # SDK 예외는 다시 부르지 않는다


async def test_format_failure_twice_becomes_llm_unavailable(chat, answerer) -> None:
    chat.replies = ["{깨짐", js("  ", [])]  # 두 번째는 다듬고 나니 빔
    with pytest.raises(LlmUnavailable) as e:
        await answerer.answer("질문", segs(3000), [], "gpt-5-mini")
    assert e.value.extra["reason"].startswith("모델 출력을 읽지 못했어요")
    assert len(chat.calls) == config.LLM_RETRY + 1

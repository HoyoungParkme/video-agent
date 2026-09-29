"""AnswererPort 구현 — OpenAI 채팅으로 근거 있는 답(VA-MS-006 answerer_openai).

지시는 system(prompts/answer.md), 앞선 턴은 user · assistant 쌍, 이번 질문에 맞춘 스크립트는 마지막
user 메시지의 `<transcript>` 안에 — 앞선 턴의 스크립트는 다시 보내지 않는다. 호출 · 형식 실패는
LlmUnavailable(이유 한 줄)로 바꿔 올린다 — 서비스가 SDK를 모르게. 키는 부를 때마다 client_for로.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from app import prompts
from app.core.config import config
from app.core.errors import LlmUnavailable
from app.domains.analysis.schemas import Segment
from app.domains.chat.schemas import AnswerDraft, ChatTurn
from app.infra import openai
from app.infra.errors import OpenAIOutputError
from app.shared import timecode

# 답 하나에 붙이는 근거 시각 상한
TIMES_MAX = 3


def _said(turn: ChatTurn, long: bool) -> str:
    # 앞선 답에 근거 시각을 붙여 보낸다 — '그거'가 무엇인지 모델이 알게. 표기는 본문과 같게 —
    # 모델이 옮겨 적어도 같은 끝 시각으로 읽힌다(짧은 본문의 '1:10:00'은 70초로 읽힌다)
    if not turn.cited_secs:
        return turn.answer
    times = ", ".join(timecode.label(s, long) for s in turn.cited_secs)
    return f"{turn.answer} (근거: {times})"


class AnswererOpenAI:
    """질문 + 맥락 구간 + 앞선 턴 → 답과 근거 시각."""

    def __init__(self, client_for: Callable[[], AsyncOpenAI]) -> None:
        self.client_for = client_for

    async def answer(
        self, question: str, context: list[Segment], history: list[ChatTurn], model: str
    ) -> AnswerDraft:
        """VA-MS-006#answerer_openai.answer

        근거 있는 답. 근거 시각은 초로 바꾸고 못 읽은 것은 버린다(셋까지). 답이 '영상에서 다루지
        않는다'로 시작하면 모델이 시각을 붙여도 근거를 비운다. 시간 제한은 서비스가 건다.

        Args:
            question: 다듬은 질문
            context: 이번 질문에 맞춘 구간들(시각순)
            history: 앞선 턴, 시간순
            model: 텍스트 모델

        Returns:
            답과 근거 시각(초)

        Raises:
            LlmUnavailable: OpenAI 호출 실패 · 다시 불러도 형식이 틀렸다(이유 한 줄)
        """
        end = context[-1].end_sec if context else 0.0
        long = end >= 3600
        lines = "\n".join(f"[{timecode.label(s.start_sec, long)}] {s.text}" for s in context)
        system = prompts.render(
            "answer",
            time_format="h:mm:ss" if long else "mm:ss",
            not_covered=config.NOT_COVERED_TEXT,
        )
        messages: list[dict] = [{"role": "system", "content": system}]
        for t in history:
            messages += [
                {"role": "user", "content": t.question},
                {"role": "assistant", "content": _said(t, long)},
            ]
        messages.append(
            {"role": "user", "content": f"<transcript>\n{lines}\n</transcript>\n\n{question}"}
        )

        def parse(obj: Any) -> AnswerDraft:
            text = obj["answer"]
            if not isinstance(text, str) or not text.strip():
                raise ValueError("답이 비었다")
            times = obj.get("times") or []
            if not isinstance(times, list):
                raise ValueError("times가 목록이 아니다")
            read = [timecode.parse(t, end) if isinstance(t, str) else None for t in times]
            secs = [s for s in read if s is not None]
            text = text.strip()
            cited = [] if text.startswith(config.NOT_COVERED_TEXT) else secs[:TIMES_MAX]
            return AnswerDraft(answer=text, cited_secs=cited)

        try:
            return await openai.chat_json(self.client_for(), model, messages, parse)
        except (OpenAIError, OpenAIOutputError) as e:
            raise LlmUnavailable(reason=openai.reason_of(e)) from e

"""대화 묶음이 밖에서 받는 것 — 답변 모델(VA-DOM-002 4.6). 구현은 adapters/answerer_openai.py."""

from __future__ import annotations

from typing import Protocol

from app.domains.analysis.schemas import Segment
from app.domains.chat.schemas import AnswerDraft, ChatTurn


class AnswererPort(Protocol):
    async def answer(
        self, question: str, context: list[Segment], history: list[ChatTurn], model: str
    ) -> AnswerDraft:
        """맥락 구간과 앞선 턴으로 답과 근거 시각. 실패하면 LlmUnavailable."""
        ...

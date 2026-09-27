"""대화 묶음의 형태 — 응답 ChatTurn · 요청 AskRequest(VA-API-001 4장), 포트가 주는 AnswerDraft."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel


class ChatTurn(BaseModel):
    """질문 하나와 답. cited_secs가 비면 '영상에 없는 내용'."""

    id: int
    question: str
    answer: str
    cited_secs: list[float]
    asked_at: datetime


class AskRequest(BaseModel):
    """질문 하나 — 입력칸 문장이든 추천 질문이든 같은 요청이다.

    글자 수는 여기서 막지 않는다 — 빈 질문도 결과 · 키 다음에 서비스가 본다(순서가 규칙).
    """

    question: str


@dataclass(frozen=True)
class AnswerDraft:
    """모델이 준 답과 근거 시각(초). 범위 밖 시각 거르기는 서비스가 한다."""

    answer: str
    cited_secs: list[float]

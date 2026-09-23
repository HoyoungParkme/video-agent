"""대화 묶음의 응답 형태 — VA-API-001 4장 ChatTurn. 질문 요청(AskRequest)은 B3에서."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ChatTurn(BaseModel):
    """질문 하나와 답. cited_secs가 비면 '영상에 없는 내용'."""

    id: int
    question: str
    answer: str
    cited_secs: list[float]
    asked_at: datetime

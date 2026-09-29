"""결과 묶음이 밖에서 받는 것 — 요약 모델(VA-DOM-002 4.6). 구현은 adapters/summarizer_openai.py."""

from __future__ import annotations

from typing import Protocol

from app.domains.analysis.schemas import ChapterDraft, Segment, SummaryDraft


class SummarizerPort(Protocol):
    async def summary(self, segments: list[Segment], duration_sec: int, model: str) -> SummaryDraft:
        """한 줄 요약 + 인사이트와 출처 시각."""
        ...

    async def chapters(
        self, segments: list[Segment], duration_sec: int, model: str
    ) -> ChapterDraft:
        """챕터(+ 60분 넘으면 파트)."""
        ...

    async def questions(self, segments: list[Segment], model: str) -> list[str]:
        """추천 질문."""
        ...

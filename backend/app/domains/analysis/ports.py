"""결과 묶음이 밖에서 받는 것 — 요약 모델 · 장면 · 인포그래픽(VA-DOM-002 4.6). 구현은 adapters/의
summarizer_openai.py · frames_storyboard.py · frames_local.py · image_openai.py."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from app.core.config import ImageQuality
from app.domains.analysis.schemas import (
    ChapterDraft,
    FrameShot,
    ImageShot,
    InfographicBrief,
    Segment,
    SummaryDraft,
)


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


class FrameSourcePort(Protocol):
    def frames(
        self, source: str, secs: list[float], dest_dir: str
    ) -> AsyncIterator[FrameShot | None]:
        """시각마다 장면 한 장을 순서대로 낸다. 못 얻은 시각은 None, 통째로 못 하면 예외."""
        ...


class ImageMakerPort(Protocol):
    async def infographic(
        self, brief: InfographicBrief, model: str, quality: ImageQuality, dest: str
    ) -> ImageShot:
        """재료 → 세로 한 장 PNG를 dest에. 실패는 LlmUnavailable(이유 한 줄)."""
        ...

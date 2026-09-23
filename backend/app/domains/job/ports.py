"""작업 묶음이 밖에서 받는 것 — 포트(VA-DOM-002 4.6). 구현은 adapters/, 테스트는 가짜로 바꿔 끼운다.

B1은 자막 가져오기 하나. 음성 내려받기 · 추출 · 자르기 · 받아쓰기는 B2에서 더한다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from app.domains.analysis.schemas import CaptionLine

if TYPE_CHECKING:
    from app.domains.video.models import CaptionKind


class AudioSourcePort(Protocol):
    async def captions(self, video_id: str) -> tuple[list[CaptionLine], str, CaptionKind] | None:
        """자막 → 줄 목록과 언어 · 종류. 자막이 없으면 None."""
        ...

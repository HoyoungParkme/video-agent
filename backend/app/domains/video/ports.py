"""영상 묶음이 밖에서 받는 것 — 포트(VA-DOM-002 4.6).

구현은 adapters/, 테스트는 가짜로 바꿔 끼운다.
"""

from __future__ import annotations

from typing import Protocol

from app.domains.video.schemas import SourceInfo


class YouTubeInfoPort(Protocol):
    async def info(self, url: str) -> SourceInfo:
        """주소 → 제목 · 채널 · 길이 · 자막. 못 가져오면 SourceUnavailable."""
        ...


class MediaProbePort(Protocol):
    async def probe(self, path: str) -> tuple[int, bool]:
        """파일 → (길이 초, 음성 트랙 유무). 못 열면 UnsupportedFile."""
        ...

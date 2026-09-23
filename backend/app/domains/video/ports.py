"""영상 묶음이 밖에서 받는 것 — 포트(VA-DOM-002 4.6). 구현은 adapters/, 테스트는 가짜로 바꿔 끼운다.

B1은 YouTube 정보 하나. 파일 길이 · 음성 재기(MediaProbePort)는 B2에서 더한다.
"""

from __future__ import annotations

from typing import Protocol

from app.domains.video.schemas import SourceInfo


class YouTubeInfoPort(Protocol):
    async def info(self, url: str) -> SourceInfo:
        """주소 → 제목 · 채널 · 길이 · 자막. 못 가져오면 SourceUnavailable."""
        ...

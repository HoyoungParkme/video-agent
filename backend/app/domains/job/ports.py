"""작업 묶음이 밖에서 받는 것 — 포트(VA-DOM-002 4.6).

구현은 adapters/, 테스트는 가짜로 바꿔 끼운다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from app.domains.analysis.schemas import CaptionLine
from app.domains.job.schemas import ChunkPlan, SttSegment

if TYPE_CHECKING:
    from app.domains.video.models import CaptionKind


class AudioSourcePort(Protocol):
    async def captions(self, video_id: str) -> tuple[list[CaptionLine], str, CaptionKind] | None:
        """자막 → 줄 목록과 언어 · 종류. 자막이 없으면 None."""
        ...

    async def download_audio(self, video_id: str, dest: str) -> str:
        """YouTube 음성만 내려받아 mp3로 — dest 안 경로."""
        ...

    async def extract_audio(self, src: str, dest: str) -> str:
        """영상 · 음성 파일 → mp3 64kbps 모노(src는 읽기만) — dest 안 경로."""
        ...


class AudioSplitPort(Protocol):
    async def split(self, path: str, dest_dir: str) -> list[ChunkPlan]:
        """무음 근처에서 조각으로 자른다. seq 순."""
        ...


class SttPort(Protocol):
    async def transcribe(self, path: str, model: str) -> list[SttSegment]:
        """조각 하나를 받아쓴다 — 조각 안 상대 시각. 예외는 그대로 올린다."""
        ...

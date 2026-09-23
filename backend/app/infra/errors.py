"""외부 프로그램이 실패했을 때의 예외 둘 — yt-dlp · ffmpeg(VA-MS-007 0장).

OpenAI는 SDK 예외를 그대로 쓴다. 어댑터 · 파이프라인이 이것으로 ErrorKind를 정한다.
"""

from __future__ import annotations

from typing import Literal

YtdlpKind = Literal["private", "unavailable", "geo", "network", "extractor", "other"]


class YtdlpError(Exception):
    """yt-dlp 실패. kind는 표준 오류에서 가른 종류, reason은 표준 오류 끝줄들."""

    def __init__(self, reason: str, kind: YtdlpKind) -> None:
        super().__init__(reason)
        self.reason = reason
        self.kind = kind


class FfmpegError(Exception):
    """ffmpeg · ffprobe 실패. reason은 표준 오류 끝줄들."""

    def __init__(self, reason: str, returncode: int) -> None:
        super().__init__(reason)
        self.reason = reason
        self.returncode = returncode

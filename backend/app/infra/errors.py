"""밖이 실패했을 때의 예외 셋 — yt-dlp · ffmpeg · 모델 출력 형식(VA-MS-007 0장).

OpenAI 호출 실패는 SDK 예외를 그대로 쓴다. 셋째는 OpenAI 어댑터가 모델 출력을 읽지 못할 때
던진다 — 여기 두어 파이프라인이 어댑터 묶음을 import하지 않고 ErrorKind를 가른다.
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


class OpenAIOutputError(Exception):
    """모델 출력이 형식에 맞지 않는다 — 다시 불러도 안 되면 어댑터가 던진다(VA-MS-006 0장)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason

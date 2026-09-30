"""FrameSourcePort 구현 — YouTube 스토리보드(재생 막대의 미리 보기 썸네일)에서 챕터 장면을 자른다
(VA-MS-006 frames_storyboard, VA-INFRA-001 C12). 영상은 내려받지 않는다.

영상 정보를 한 번 받아 스토리보드 격자(장마다 rows × columns 칸, 칸마다 1 / fps초)에서 시각이 든
칸을 고르고, 장 주소를 ffmpeg에 넘겨 그 칸만 자른다 — HTTP 클라이언트를 더하지 않는다.
"""

from __future__ import annotations

import math
from collections.abc import AsyncIterator
from typing import Any

from app.core.config import config
from app.domains.analysis.schemas import FrameShot, FrameSource
from app.infra import ffmpeg, ytdlp
from app.infra.errors import FfmpegError, YtdlpError

# 칸 번호를 셀 때 float 곱의 끝자리 오차(59.99999…)로 앞 칸을 고르지 않게
_EPS = 1e-9


def _storyboard(raw: dict[str, Any]) -> dict[str, Any]:
    """정해 둔 형식(sb0), 없으면 스토리보드 가운데 칸이 가장 큰 것. 없으면 YtdlpError."""
    formats = raw.get("formats") or []
    for f in formats:
        if f.get("format_id") == config.STORYBOARD_FORMAT:
            return f
    boards = [f for f in formats if f.get("format_note") == "storyboard"]
    if not boards:
        raise YtdlpError("스토리보드가 없음", "other")
    return max(boards, key=lambda f: (f.get("width") or 0) * (f.get("height") or 0))


class FramesStoryboard:
    """YouTube 영상 ID → 챕터 시각마다 스토리보드 칸 한 장."""

    async def frames(
        self, source: str, secs: list[float], dest_dir: str
    ) -> AsyncIterator[FrameShot | None]:
        """VA-MS-006#frames_storyboard.frames

        장 주소에는 서명이 있어 오래 두면 만료되므로 등록 때 받은 정보를 쓰지 않고 이때 새로 받는다.
        칸 하나의 실패는 그 시각만 None이고, 정보를 못 받거나 스토리보드가 없으면 통째로 실패한다.

        Args:
            source: YouTube 영상 ID
            secs: 챕터 시작 시각(오름차순)
            dest_dir: 장면을 쓸 폴더 — `sb-{i}.jpg`(i는 1부터)

        Yields:
            시각마다 FrameShot(sec는 실제 칸의 시각) 또는 None
        """
        raw = await ytdlp.info(
            f"https://www.youtube.com/watch?v={source}", timeout=config.INFO_TIMEOUT_SEC
        )
        sb = _storyboard(raw)
        w, h, rows, cols, fps = sb["width"], sb["height"], sb["rows"], sb["columns"], sb["fps"]
        sheets = sb["fragments"]
        per = rows * cols
        for i, sec in enumerate(secs, start=1):
            n = math.floor(sec * fps + _EPS)
            sheet, k = divmod(n, per)
            if sheet >= len(sheets):  # 마지막 장을 넘는 시각 — 영상 끝 가까이, 마지막 칸
                sheet, k = len(sheets) - 1, per - 1
                n = sheet * per + k
            row, col = divmod(k, cols)
            dest = f"{dest_dir}/sb-{i}.jpg"
            try:
                await ffmpeg.crop(sheets[sheet]["url"], col * w, row * h, w, h, dest)
            except FfmpegError:
                yield None
                continue
            yield FrameShot(n / fps, FrameSource.storyboard, w, h, dest)

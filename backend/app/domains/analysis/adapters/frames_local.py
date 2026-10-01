"""FrameSourcePort 구현 — 로컬 원본(inbox 파일 또는 올린 사본)에서 챕터 시각의 프레임 한 장씩
(VA-MS-006 frames_local, VA-INFRA-001 C12). 원본은 읽기만 한다. 음성 파일은 서비스가 부르지 않는다.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

from app.core.config import config
from app.domains.analysis.schemas import FrameShot, FrameSource
from app.infra import ffmpeg
from app.infra.errors import FfmpegError


class FramesLocal:
    """원본 경로 → 챕터 시각마다 프레임 한 장(폭 FRAME_WIDTH)."""

    async def frames(
        self, source: str, secs: list[float], dest_dir: str
    ) -> AsyncIterator[FrameShot | None]:
        """VA-MS-006#frames_local.frames

        원본이 없으면(옮겼거나 사본이 없다) 첫 시각 전에 FileNotFoundError로 통째로 실패한다.
        크기는 뽑은 그림을 재서 준다 — 세로 영상 · 회전도 실제 크기로.

        Args:
            source: 원본 경로(sources.local_path)
            secs: 챕터 시작 시각(오름차순)
            dest_dir: 장면을 쓸 폴더 — `lf-{i}.jpg`(i는 1부터)

        Yields:
            시각마다 FrameShot 또는 None(그 한 장을 못 뽑음)
        """
        if not os.path.isfile(source):
            raise FileNotFoundError(source)
        for i, sec in enumerate(secs, start=1):
            dest = f"{dest_dir}/lf-{i}.jpg"
            try:
                await ffmpeg.frame(source, sec, config.FRAME_WIDTH, dest)
                info = await ffmpeg.probe(dest)
            except FfmpegError:
                yield None
                continue
            video = next(s for s in info["streams"] if s.get("codec_type") == "video")
            yield FrameShot(sec, FrameSource.local_frame, video["width"], video["height"], dest)

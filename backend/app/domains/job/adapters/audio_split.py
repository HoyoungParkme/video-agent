"""AudioSplitPort 구현 — 음성을 무음 근처에서 조각으로 자른다(VA-MS-006 audio_split).

조각 파일은 `{dest_dir}/{seq}.mp3`. 들어오는 음성은 늘 임시 폴더 안의 mp3다 — 로컬 음성도
받아쓰기 단계가 먼저 바꾼다. 조각이 하나면 그 파일을 그대로 조각으로 쓴다.
"""

from __future__ import annotations

import os

from app.core.config import config
from app.domains.job.schemas import ChunkPlan
from app.infra import ffmpeg


class AudioSplitAdapter:
    """음성 → 조각 계획. 경계는 `CHUNK_SEC`마다, 그 앞뒤 `SPLIT_WINDOW_SEC` 안의 무음."""

    async def split(self, path: str, dest_dir: str) -> list[ChunkPlan]:
        """VA-MS-006#audio_split.split

        경계는 k × CHUNK_SEC마다 목표에 가장 가까운 무음 시각, 없으면 목표 그대로. 끝에서
        SPLIT_WINDOW_SEC 안에 드는 목표는 두지 않는다 — 마지막 조각이 몇 초짜리가 되지 않게
        (조각 하나로 끝나는 길이와 같은 여유). 자른 조각이 크기 상한을 넘으면 반으로 다시 자른다.

        Args:
            path: 임시 폴더 안 mp3
            dest_dir: 조각 파일을 쓸 폴더

        Returns:
            조각 계획, seq 순

        Raises:
            FfmpegError: 그대로
        """
        total = float((await ffmpeg.probe(path))["format"]["duration"])
        if total <= config.CHUNK_SEC + config.SPLIT_WINDOW_SEC:
            return [ChunkPlan(seq=1, offset_sec=0.0, duration_sec=total, path=path)]
        silences = await ffmpeg.silences(path)
        window = config.SPLIT_WINDOW_SEC
        bounds = [0.0]
        k = 1
        while k * config.CHUNK_SEC < total - window:
            target = float(k * config.CHUNK_SEC)
            near = [t for t in silences if abs(t - target) <= window and t > bounds[-1]]
            bounds.append(min(near, key=lambda t: abs(t - target)) if near else target)
            k += 1
        bounds.append(total)
        plans: list[ChunkPlan] = []
        for start, end in zip(bounds, bounds[1:], strict=False):
            plans += await _cut(path, start, end, dest_dir, len(plans) + 1)
        return plans


async def _cut(path: str, start: float, end: float, dest_dir: str, seq: int) -> list[ChunkPlan]:
    # 상한을 넘으면 무음 없이 반으로 — 64kbps라 10분이 4.8MB여서 사실상 일어나지 않는다
    out = await ffmpeg.cut(path, start, end, os.path.join(dest_dir, f"{seq}.mp3"))
    # 창보다 짧으면 더 자르지 않는다 — 크기가 줄지 않는 이상한 파일에서 끝없이 돌지 않게
    if os.path.getsize(out) <= config.CHUNK_MAX_BYTES or end - start <= config.SPLIT_WINDOW_SEC:
        return [ChunkPlan(seq=seq, offset_sec=start, duration_sec=end - start, path=out)]
    os.remove(out)
    mid = (start + end) / 2
    first = await _cut(path, start, mid, dest_dir, seq)
    return first + await _cut(path, mid, end, dest_dir, seq + len(first))

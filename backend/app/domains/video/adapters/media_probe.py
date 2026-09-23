"""MediaProbePort 구현 — ffprobe로 파일의 길이와 음성 트랙을 잰다(VA-MS-006 media_probe).

inbox 목록과 로컬 파일 등록이 부른다. 파일은 읽기만 한다.
"""

from __future__ import annotations

from app.core.config import config
from app.core.errors import UnsupportedFile
from app.infra import ffmpeg
from app.infra.errors import FfmpegError

# 열 수 없거나 영상 · 음성이 아닌 파일의 이유 한 줄(UC-H2 1a · UI-2 시작 불가 판 7.1)
NOT_MEDIA = "영상·음성 파일이 아닙니다"


class MediaProbeAdapter:
    """파일 → (길이, 음성 유무)."""

    async def probe(self, path: str) -> tuple[int, bool]:
        """VA-MS-006#media_probe.probe

        길이는 초 단위 반올림. 음성 트랙은 스트림 중 오디오가 하나라도 있으면 있다.

        Args:
            path: inbox 안 파일 경로

        Returns:
            (길이 초, 음성 트랙 유무)

        Raises:
            UnsupportedFile: 못 열었거나(ffprobe 실패) 길이가 없는 파일
        """
        try:
            raw = await ffmpeg.probe(path)
        except FfmpegError as e:
            raise UnsupportedFile(reason=NOT_MEDIA, accepted=_accepted()) from e
        duration = raw.get("format", {}).get("duration")
        if duration is None:  # 그림 파일 등 — 열리지만 길이가 없다
            raise UnsupportedFile(reason=NOT_MEDIA, accepted=_accepted())
        has_audio = any(s.get("codec_type") == "audio" for s in raw.get("streams", []))
        return int(round(float(duration))), has_audio


def _accepted() -> list[str]:
    return config.VIDEO_EXTS + config.AUDIO_EXTS

"""video/adapters/media_probe — 파일 → (길이, 음성 유무)(VA-MS-006 media_probe.probe). ffprobe는 가짜로."""

from __future__ import annotations

import pytest

from app.core.errors import UnsupportedFile
from app.domains.video.adapters.media_probe import MediaProbeAdapter
from app.infra import ffmpeg
from app.infra.errors import FfmpegError


@pytest.fixture
def probed(monkeypatch) -> dict:
    """ffmpeg.probe가 줄 JSON — 테스트가 고친다. error를 넣으면 던진다."""
    state: dict = {"raw": {}, "error": None, "paths": []}

    async def probe(path: str) -> dict:
        state["paths"].append(path)
        if state["error"]:
            raise state["error"]
        return state["raw"]

    monkeypatch.setattr(ffmpeg, "probe", probe)
    return state


def _raw(duration: object, *kinds: str) -> dict:
    return {"format": {"duration": duration}, "streams": [{"codec_type": k} for k in kinds]}


async def test_mp4_without_audio(probed) -> None:
    probed["raw"] = _raw("1800.2", "video")
    assert await MediaProbeAdapter().probe("/inbox/silent.mp4") == (1800, False)
    assert probed["paths"] == ["/inbox/silent.mp4"]


async def test_mp3_has_audio(probed) -> None:
    probed["raw"] = _raw("61.0", "audio")
    assert await MediaProbeAdapter().probe("a.mp3") == (61, True)


async def test_rounds_duration(probed) -> None:
    probed["raw"] = _raw("3011.6", "video", "audio")
    assert await MediaProbeAdapter().probe("a.mp4") == (3012, True)


async def test_broken_file_is_unsupported(probed) -> None:
    probed["error"] = FfmpegError("Invalid data found when processing input", 1)
    with pytest.raises(UnsupportedFile) as e:
        await MediaProbeAdapter().probe("broken.mp4")
    assert e.value.extra["reason"] == "영상·음성 파일이 아닙니다"
    assert e.value.extra["accepted"] == ["mp4", "mkv", "mov", "webm", "mp3", "m4a", "wav"]


async def test_no_duration_is_unsupported(probed) -> None:
    probed["raw"] = {"format": {}, "streams": [{"codec_type": "video"}]}  # 그림 파일처럼
    with pytest.raises(UnsupportedFile):
        await MediaProbeAdapter().probe("still.mp4")

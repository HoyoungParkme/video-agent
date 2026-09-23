"""infra/ffmpeg — VA-MS-007 ffmpeg.probe · extract_audio · silences · cut의 테스트 관점.

가짜 실행 파일로 인자와 해석을 본다. 진짜 ffmpeg가 있으면(이미지 안) 결과 파일까지 본다.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

import pytest

from app.core.config import config
from app.infra import ffmpeg
from app.infra.errors import FfmpegError

PROBE = {
    "streams": [{"codec_type": "video"}, {"codec_type": "audio"}],
    "format": {"duration": "9000.123"},
}
SILENCE_LOG = """Input #0, mp3, from 'audio.mp3':
[silencedetect @ 0x1] silence_start: 10.5
[silencedetect @ 0x1] silence_end: 11.5 | silence_duration: 1
size=N/A time=00:00:30.00 bitrate=N/A speed= 900x
[silencedetect @ 0x1] silence_start: 20
[silencedetect @ 0x1] silence_end: 23 | silence_duration: 3
[silencedetect @ 0x1] silence_start: 28.25
"""


async def test_probe(fake) -> None:
    fake.behave(stdout=json.dumps(PROBE))
    info = await ffmpeg.probe("/inbox/a b.mp4")
    assert info["format"]["duration"] == "9000.123"
    assert [s["codec_type"] for s in info["streams"]] == ["video", "audio"]
    assert fake.calls()[0][-1] == "/inbox/a b.mp4"


async def test_probe_broken_file(fake) -> None:
    fake.behave(stderr="a.mp4: Invalid data found when processing input\n", exit=1)
    with pytest.raises(FfmpegError) as e:
        await ffmpeg.probe("a.mp4")
    assert e.value.returncode == 1
    assert "Invalid data" in e.value.reason

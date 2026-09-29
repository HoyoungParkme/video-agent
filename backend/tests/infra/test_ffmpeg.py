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


async def test_extract_audio_args(fake, tmp_path: Path) -> None:
    fake.behave(write_last=1)
    out = await ffmpeg.extract_audio("/inbox/a.mp4", str(tmp_path))
    assert out == str(tmp_path / "audio.mp3")
    [args] = fake.calls()
    assert args[:5] == ["-y", "-v", "error", "-i", "/inbox/a.mp4"]
    assert "-vn" in args
    assert args[args.index("-vn") + 1 : -1] == config.AUDIO_FORMAT
    assert args[-1] == out


async def test_silences_midpoints(fake) -> None:
    fake.behave(stderr=SILENCE_LOG)
    assert await ffmpeg.silences("audio.mp3") == [11.0, 21.5]  # 짝 없는 마지막 start는 버린다
    [args] = fake.calls()
    assert args[args.index("-af") + 1] == "silencedetect=noise=-35dB:d=0.5"


async def test_silences_none(fake) -> None:
    fake.behave(stderr="size=N/A time=00:00:30.00\n")
    assert await ffmpeg.silences("audio.mp3") == []


async def test_cut_args(fake, tmp_path: Path) -> None:
    fake.behave(write_last=1)
    dest = str(tmp_path / "3.mp3")
    assert await ffmpeg.cut("audio.mp3", 1200.0, 1800.5, dest) == dest
    [args] = fake.calls()
    assert args[args.index("-ss") + 1] == "1200.000"
    assert args[args.index("-to") + 1] == "1800.500"
    assert args[args.index("-c") + 1] == "copy"


async def test_missing_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "FFPROBE_BIN", "/없는/ffprobe")
    with pytest.raises(FfmpegError):
        await ffmpeg.probe("a.mp4")


async def test_probe_not_json(fake) -> None:
    fake.behave(stdout="")
    with pytest.raises(FfmpegError):
        await ffmpeg.probe("a.mp4")


async def test_cancel_kills_child(fake, tmp_path: Path) -> None:
    assert await fake.cancelled_child_is_gone(ffmpeg.silences("audio.mp3"), tmp_path)


# 진짜 ffmpeg — 호스트에 없으면 건너뛴다(이미지에는 있다)
real = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg가 없다")


async def _make_video(path: Path, seconds: int) -> None:
    """앞 2초 소리 · 1초 무음 · 나머지 소리인 테스트 영상."""
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", f"color=size=64x64:duration={seconds}",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
        "-af", "volume=enable='between(t,2,3)':volume=0",
        "-shortest", "-c:v", "libx264", "-c:a", "aac", str(path),
    )  # fmt: skip
    assert await proc.wait() == 0


@real
async def test_real_extract_cut_silences(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("FFMPEG_BIN", "FFPROBE_BIN"):
        monkeypatch.setattr(config, name, name.split("_")[0].lower())
    src = tmp_path / "v.mp4"
    await _make_video(src, 8)
    info = await ffmpeg.probe(str(src))
    assert {s["codec_type"] for s in info["streams"]} == {"video", "audio"}

    audio = await ffmpeg.extract_audio(str(src), str(tmp_path))
    streams = (await ffmpeg.probe(audio))["streams"]
    assert [(s["codec_name"], s["channels"], s["sample_rate"]) for s in streams] == [
        ("mp3", 1, "16000")
    ]
    assert src.exists()

    mids = await ffmpeg.silences(audio)
    assert len(mids) == 1 and 2.2 < mids[0] < 2.8

    part = await ffmpeg.cut(audio, 1.0, 4.0, str(tmp_path / "1.mp3"))
    assert abs(float((await ffmpeg.probe(part))["format"]["duration"]) - 3.0) <= 0.1
    tail = await ffmpeg.cut(audio, 6.0, 100.0, str(tmp_path / "2.mp3"))  # 끝이 길이를 넘으면 끝까지
    assert abs(float((await ffmpeg.probe(tail))["format"]["duration"]) - 2.0) <= 0.1


@real
async def test_real_missing_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "FFPROBE_BIN", "ffprobe")
    with pytest.raises(FfmpegError):
        await ffmpeg.probe("/없는/파일.mp4")

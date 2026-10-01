"""infra/ffmpeg — VA-MS-007 ffmpeg.probe · extract_audio · silences · cut · frame · crop의 테스트 관점.

가짜 실행 파일로 인자와 해석을 본다. 진짜 ffmpeg가 있으면(이미지 안) 결과 파일까지 본다.
"""

from __future__ import annotations

import asyncio
import contextlib
import http.server
import json
import os
import shutil
import threading
import time
from collections.abc import Iterator
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


async def test_silences_threshold_from_caller(fake) -> None:
    # 15초 토막은 더 민감한 값으로 찾는다(VA-MS-006 stt_openai) — 안 주면 10분 조각 값
    fake.behave(stderr=SILENCE_LOG)
    await ffmpeg.silences("piece.mp3", -30, 0.2)
    [args] = fake.calls()
    assert args[args.index("-af") + 1] == "silencedetect=noise=-30dB:d=0.2"


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


async def test_frame_args(fake, tmp_path: Path) -> None:
    fake.behave(write_last=1)
    dest = str(tmp_path / "lf-0.jpg")
    assert await ffmpeg.frame("/inbox/강의 녹화.mp4", 591.0, 640, dest) == dest
    [args] = fake.calls()
    # -ss가 -i 앞 — 그 시각으로 바로 건너뛴다
    assert args[:7] == ["-y", "-v", "error", "-ss", "591.000", "-i", "/inbox/강의 녹화.mp4"]
    assert args[7:] == ["-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "3", dest]


async def test_frame_past_the_end_is_an_error(fake, tmp_path: Path) -> None:
    # ffmpeg는 끝을 넘는 시각에도 0으로 끝나고 파일을 만들지 않는다
    with pytest.raises(FfmpegError) as e:
        await ffmpeg.frame("a.mp4", 99999.0, 640, str(tmp_path / "lf-0.jpg"))
    assert e.value.reason == "프레임을 뽑지 못함"


async def test_frame_past_the_end_with_old_file_is_an_error(fake, tmp_path: Path) -> None:
    # 앞선 실행이 남긴 같은 이름의 파일을 새 프레임으로 돌려주지 않는다
    old = tmp_path / "lf-1.jpg"
    old.write_bytes(b"old")
    with pytest.raises(FfmpegError):
        await ffmpeg.frame("a.mp4", 99999.0, 640, str(old))
    assert not old.exists()


async def test_frame_timeout_kills_child(
    fake, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config, "FRAME_TIMEOUT_SEC", 0.5)
    pidfile = tmp_path / "pid"
    fake.behave(sleep=30, pidfile=pidfile)
    with pytest.raises(FfmpegError) as e:
        await ffmpeg.frame("a.mp4", 1.0, 640, str(tmp_path / "lf-0.jpg"))
    assert e.value.reason == "시간 제한을 넘었습니다"
    with pytest.raises(ProcessLookupError):
        os.kill(int(pidfile.read_text()), 0)


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


async def test_crop_args(fake, tmp_path: Path) -> None:
    fake.behave(write_last=1)
    dest = str(tmp_path / "sb-0.jpg")
    url = "https://i.ytimg.com/sb/abc/storyboard3_L2/M0.jpg?sigh=x"
    assert await ffmpeg.crop(url, 320, 180, 320, 180, dest) == dest
    [args] = fake.calls()
    # 칸이 그림 밖이면 폭 · 높이가 0이 되어 실패한다 — 그냥 crop=w:h:x:y면 가장자리로 당겨 붙인다
    crop = "crop=w='if(lte(320+320,iw),320,0)':h='if(lte(180+180,ih),180,0)':x=320:y=180"
    assert args == ["-y", "-v", "error", "-i", url, "-vf", crop] + [
        "-frames:v",
        "1",
        "-q:v",
        "3",
        dest,
    ]


async def test_crop_failure(fake, tmp_path: Path) -> None:
    fake.behave(
        stderr="Invalid too big or non positive size for width '320' or height '180'\n", exit=1
    )
    with pytest.raises(FfmpegError) as e:
        await ffmpeg.crop("grid.png", 900, 500, 320, 180, str(tmp_path / "sb-0.jpg"))
    assert "Invalid too big" in e.value.reason


@real
async def test_real_frame(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("FFMPEG_BIN", "FFPROBE_BIN"):
        monkeypatch.setattr(config, name, name.split("_")[0].lower())
    src = tmp_path / "강의 녹화 1.mp4"  # 공백 · 한글이 든 경로
    await _make_video(src, 8)
    before = (src.stat().st_mtime_ns, src.stat().st_size)
    dest = await ffmpeg.frame(str(src), 3.0, 640, str(tmp_path / "lf-0.jpg"))
    [stream] = (await ffmpeg.probe(dest))["streams"]
    assert stream["codec_name"] == "mjpeg"
    assert (stream["width"], stream["height"] % 2) == (640, 0)
    assert (src.stat().st_mtime_ns, src.stat().st_size) == before  # 원본은 읽기만
    with pytest.raises(FfmpegError):
        await ffmpeg.frame(str(src), 60.0, 640, str(tmp_path / "lf-1.jpg"))  # 영상 끝을 넘음


@real
async def test_real_missing_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "FFPROBE_BIN", "ffprobe")
    with pytest.raises(FfmpegError):
        await ffmpeg.probe("/없는/파일.mp4")


async def _make_grid(path: Path) -> None:
    """3×3 격자 그림(960×540) — 가운데 칸만 흰색, 나머지는 검정."""
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=960x540",
        "-vf", "drawbox=x=320:y=180:w=320:h=180:color=white:t=fill", "-frames:v", "1", str(path),
    )  # fmt: skip
    assert await proc.wait() == 0


async def _gray(path: str) -> bytes:
    """JPEG를 흑백 원시 픽셀로 — 칸이 흰색인지 본다."""
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "gray", "-",
        stdout=asyncio.subprocess.PIPE,
    )  # fmt: skip
    out, _ = await proc.communicate()
    return out


@contextlib.contextmanager
def _serve(folder: Path, stall: bool = False) -> Iterator[str]:
    """그 폴더를 주는 HTTP 서버(스토리보드 장 주소 자리). stall이면 머리도 보내지 않고 붙든다."""

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, directory=str(folder), **kwargs)

        def do_GET(self) -> None:
            if stall:
                time.sleep(5)
                return
            super().do_GET()

        def log_message(self, *args) -> None:
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


@real
async def test_real_crop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("FFMPEG_BIN", "FFPROBE_BIN"):
        monkeypatch.setattr(config, name, name.split("_")[0].lower())
    grid = tmp_path / "grid.png"
    await _make_grid(grid)
    dest = await ffmpeg.crop(str(grid), 320, 180, 320, 180, str(tmp_path / "sb-0.jpg"))
    [stream] = (await ffmpeg.probe(dest))["streams"]
    assert (stream["codec_name"], stream["width"], stream["height"]) == ("mjpeg", 320, 180)
    pixels = await _gray(dest)
    assert len(pixels) == 320 * 180 and min(pixels) > 200  # 가운데 칸 — 흰색
    with pytest.raises(FfmpegError):  # 그림 밖 — 가장자리 칸이 아니라 실패
        await ffmpeg.crop(str(grid), 900, 500, 320, 180, str(tmp_path / "sb-1.jpg"))

    with _serve(tmp_path) as base:  # 주소도 받는다
        dest = await ffmpeg.crop(f"{base}/grid.png", 0, 0, 320, 180, str(tmp_path / "sb-2.jpg"))
        assert max(await _gray(dest)) < 60  # 왼쪽 위 칸 — 검정


@real
async def test_real_crop_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "FFMPEG_BIN", "ffmpeg")
    monkeypatch.setattr(config, "FRAME_TIMEOUT_SEC", 1)
    with _serve(tmp_path, stall=True) as base, pytest.raises(FfmpegError) as e:
        await ffmpeg.crop(f"{base}/grid.png", 0, 0, 320, 180, str(tmp_path / "sb-0.jpg"))
    assert e.value.reason == "시간 제한을 넘었습니다"

"""analysis/adapters/frames_local — VA-MS-006 frames_local.frames의 테스트 관점. infra는 가짜로."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.domains.analysis.adapters.frames_local import FramesLocal
from app.domains.analysis.schemas import FrameShot, FrameSource
from app.infra import ffmpeg
from app.infra.errors import FfmpegError


@pytest.fixture
def fake(monkeypatch):
    """ffmpeg.frame · probe 자리 — 부른 인자를 적고 640×360 그림이라고 답한다. fail에 든 차례는 실패."""
    state = {"frames": [], "fail": set()}

    async def frame(src: str, sec: float, width: int, dest: str) -> str:
        if len(state["frames"]) in state["fail"]:
            state["frames"].append(None)
            raise FfmpegError("프레임을 뽑지 못함", 0)
        state["frames"].append((src, sec, width, dest))
        return dest

    async def probe(path: str) -> dict:
        return {"streams": [{"codec_type": "video", "width": 640, "height": 360}]}

    monkeypatch.setattr(ffmpeg, "frame", frame)
    monkeypatch.setattr(ffmpeg, "probe", probe)
    return state


@pytest.fixture
def source(tmp_path: Path) -> Path:
    path = tmp_path / "inbox" / "워크숍 녹화.mp4"
    path.parent.mkdir()
    path.write_bytes(b"video")
    return path


async def shots(source: Path | str, secs: list[float], dest: str = "/d") -> list[FrameShot | None]:
    return [s async for s in FramesLocal().frames(str(source), secs, dest)]


async def test_three_times_three_shots(fake, source: Path) -> None:
    before = (source.stat().st_mtime_ns, source.stat().st_size)
    got = await shots(source, [0.0, 380.0, 4500.0])
    assert got == [
        FrameShot(0.0, FrameSource.local_frame, 640, 360, "/d/lf-1.jpg"),
        FrameShot(380.0, FrameSource.local_frame, 640, 360, "/d/lf-2.jpg"),
        FrameShot(4500.0, FrameSource.local_frame, 640, 360, "/d/lf-3.jpg"),
    ]
    assert [f[2] for f in fake["frames"]] == [640, 640, 640]  # 폭은 FRAME_WIDTH
    assert (source.stat().st_mtime_ns, source.stat().st_size) == before  # 원본은 읽기만


async def test_missing_source_fails_before_first_time(fake, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        await shots(tmp_path / "inbox" / "옮긴 파일.mp4", [0.0, 60.0])
    assert fake["frames"] == []


async def test_one_failed_frame_is_none_only(fake, source: Path) -> None:
    fake["fail"] = {1}
    got = await shots(source, [0.0, 60.0, 120.0])
    assert [s is None for s in got] == [False, True, False]


async def test_uploaded_copy_path_the_same(fake, tmp_path: Path) -> None:
    copy = tmp_path / "uploads" / ("ab" * 32 + ".mov")
    copy.parent.mkdir()
    copy.write_bytes(b"video")
    [shot] = await shots(copy, [30.0])
    assert shot is not None and fake["frames"][0][0] == str(copy)

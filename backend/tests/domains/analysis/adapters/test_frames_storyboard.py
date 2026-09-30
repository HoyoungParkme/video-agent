"""analysis/adapters/frames_storyboard — VA-MS-006 frames_storyboard.frames의 테스트 관점. infra는 가짜로."""

from __future__ import annotations

import pytest

from app.domains.analysis.adapters.frames_storyboard import FramesStoryboard
from app.domains.analysis.schemas import FrameShot, FrameSource
from app.infra import ffmpeg, ytdlp
from app.infra.errors import FfmpegError, YtdlpError


def board(fid: str, w: int, h: int, rows: int, cols: int, fps: float, sheets: int) -> dict:
    """yt-dlp가 주는 스토리보드 형식 하나 — 장 주소는 M0 ~ M{n-1}."""
    return {
        "format_id": fid,
        "format_note": "storyboard",
        "width": w,
        "height": h,
        "rows": rows,
        "columns": cols,
        "fps": fps,
        "fragments": [
            {"url": f"https://i.ytimg.com/sb/{fid}/M{i}.jpg", "duration": 90} for i in range(sheets)
        ],
    }


@pytest.fixture
def fake(monkeypatch):
    """ytdlp.info · ffmpeg.crop 자리 — 정한 정보를 주고, 자른 칸을 적는다. fail에 든 시각의 칸은 실패."""
    state = {
        "raw": {
            "formats": [board("sb0", 320, 180, 3, 3, 0.1, 10), board("sb1", 160, 90, 5, 5, 0.1, 4)]
        },
        "infos": [],
        "crops": [],
        "fail": set(),
    }

    async def info(url: str, timeout: float | None = None) -> dict:
        state["infos"].append((url, timeout))
        return state["raw"]

    async def crop(src: str, x: int, y: int, w: int, h: int, dest: str) -> str:
        if len(state["crops"]) in state["fail"]:
            state["crops"].append(None)
            raise FfmpegError("받지 못함", 1)
        state["crops"].append((src, x, y, w, h, dest))
        return dest

    monkeypatch.setattr(ytdlp, "info", info)
    monkeypatch.setattr(ffmpeg, "crop", crop)
    return state


async def shots(secs: list[float], dest: str = "/d") -> list[FrameShot | None]:
    return [s async for s in FramesStoryboard().frames("abcdefghijk", secs, dest)]


async def test_763_seconds_is_sheet_8_fifth_cell(fake) -> None:
    # 칸 76 = 장 8(9칸씩)의 5번째 칸(k=4) → 둘째 줄 둘째 칸
    [shot] = await shots([763.0])
    assert fake["crops"] == [
        ("https://i.ytimg.com/sb/sb0/M8.jpg", 320, 180, 320, 180, "/d/sb-1.jpg")
    ]
    assert shot == FrameShot(760.0, FrameSource.storyboard, 320, 180, "/d/sb-1.jpg")


async def test_info_once_for_many_times(fake) -> None:
    got = await shots([0.0, 95.0, 600.0])
    assert [s.sec for s in got if s] == [0.0, 90.0, 600.0]
    assert [c[-1] for c in fake["crops"]] == ["/d/sb-1.jpg", "/d/sb-2.jpg", "/d/sb-3.jpg"]
    assert fake["infos"] == [("https://www.youtube.com/watch?v=abcdefghijk", 40)]


async def test_biggest_storyboard_when_no_sb0(fake) -> None:
    fake["raw"] = {
        "formats": [
            board("sb2", 80, 45, 10, 10, 0.1, 1),
            board("sb1", 160, 90, 5, 5, 0.1, 4),
            {"format_id": "18", "format_note": "360p", "width": 640, "height": 360},
        ]
    }
    [shot] = await shots([35.0])
    assert fake["crops"] == [("https://i.ytimg.com/sb/sb1/M0.jpg", 480, 0, 160, 90, "/d/sb-1.jpg")]
    assert (shot.width, shot.height) == (160, 90)


async def test_no_storyboard_fails_whole(fake) -> None:
    fake["raw"] = {"formats": [{"format_id": "18", "format_note": "360p"}]}
    with pytest.raises(YtdlpError) as e:
        await shots([0.0])
    assert (e.value.reason, e.value.kind) == ("스토리보드가 없음", "other")


async def test_one_failed_crop_is_none_only(fake) -> None:
    fake["fail"] = {1}
    got = await shots([0.0, 100.0, 200.0])
    assert [s is None for s in got] == [False, True, False]


async def test_past_last_sheet_is_last_cell(fake) -> None:
    # 장 10개 × 9칸 = 90칸(900초). 1000초는 마지막 장(M9)의 마지막 칸 — 셋째 줄 셋째 칸
    [shot] = await shots([1000.0])
    assert fake["crops"] == [
        ("https://i.ytimg.com/sb/sb0/M9.jpg", 640, 360, 320, 180, "/d/sb-1.jpg")
    ]
    assert shot.sec == 890.0


async def test_info_failure_goes_up(monkeypatch) -> None:
    async def info(url: str, timeout: float | None = None) -> dict:
        raise YtdlpError("YouTube 연결 실패", "network")

    monkeypatch.setattr(ytdlp, "info", info)
    with pytest.raises(YtdlpError):
        await shots([0.0])

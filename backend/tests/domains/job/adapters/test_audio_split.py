"""job/adapters/audio_split — 무음 근처에서 조각 자르기(VA-MS-006 audio_split.split). ffmpeg는 가짜로."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import config
from app.domains.job.adapters.audio_split import AudioSplitAdapter
from app.infra import ffmpeg


@pytest.fixture
def fake_ffmpeg(monkeypatch):
    """probe(길이) · silences(무음 가운데 시각) · cut 자리. cut은 작은 파일을 쓰고, big에 든 구간은
    크기 상한을 넘는 파일로 보이게 한다(getsize만 속인다). 자른 구간을 적는다."""
    state: dict = {"duration": 9000.0, "silences": [], "cuts": [], "big": set(), "sizes": {}}

    async def probe(path: str) -> dict:
        return {"format": {"duration": str(state["duration"])}, "streams": []}

    async def silences(path: str) -> list[float]:
        return state["silences"]

    async def cut(path: str, start: float, end: float, dest: str) -> str:
        state["cuts"].append((round(start, 3), round(end, 3)))
        Path(dest).write_bytes(b"x" * 10)
        big = (start, end) in state["big"]
        state["sizes"][dest] = config.CHUNK_MAX_BYTES + 1 if big else 10
        return dest

    monkeypatch.setattr(ffmpeg, "probe", probe)
    monkeypatch.setattr(ffmpeg, "silences", silences)
    monkeypatch.setattr(ffmpeg, "cut", cut)
    monkeypatch.setattr(
        "app.domains.job.adapters.audio_split.os.path.getsize", lambda p: state["sizes"][p]
    )
    return state


async def test_150_minutes_is_15_chunks_on_silences(fake_ffmpeg, tmp_path: Path) -> None:
    # 목표(600의 배수)마다 12초 뒤에 무음 — 창(±30초) 안이라 경계가 무음으로 간다
    fake_ffmpeg["silences"] = [k * 600 + 12.0 for k in range(1, 15)] + [3000.0 + 45]
    plans = await AudioSplitAdapter().split(str(tmp_path / "audio.mp3"), str(tmp_path))
    assert [p.seq for p in plans] == list(range(1, 16))
    assert [p.offset_sec for p in plans][1:] == [k * 600 + 12.0 for k in range(1, 15)]
    assert all(abs(p.offset_sec - (p.seq - 1) * 600) <= 30 for p in plans)
    assert sum(p.duration_sec for p in plans) == pytest.approx(9000.0)
    assert [Path(p.path).name for p in plans] == [f"{i}.mp3" for i in range(1, 16)]


async def test_no_silence_cuts_every_600(fake_ffmpeg, tmp_path: Path) -> None:
    plans = await AudioSplitAdapter().split(str(tmp_path / "audio.mp3"), str(tmp_path))
    assert [p.offset_sec for p in plans] == [k * 600.0 for k in range(15)]


async def test_silence_outside_window_is_ignored(fake_ffmpeg, tmp_path: Path) -> None:
    fake_ffmpeg["silences"] = [640.0, 1170.0]  # 600+40(밖) · 1200−30(안, 가장자리)
    plans = await AudioSplitAdapter().split(str(tmp_path / "audio.mp3"), str(tmp_path))
    assert [p.offset_sec for p in plans][:3] == [0.0, 600.0, 1170.0]


async def test_short_file_is_one_chunk_without_cut(fake_ffmpeg, tmp_path: Path) -> None:
    fake_ffmpeg["duration"] = 480.0  # 8분
    audio = str(tmp_path / "audio.mp3")
    plans = await AudioSplitAdapter().split(audio, str(tmp_path))
    assert [(p.seq, p.offset_sec, p.duration_sec, p.path) for p in plans] == [
        (1, 0.0, 480.0, audio)
    ]
    assert fake_ffmpeg["cuts"] == []


async def test_no_tiny_last_chunk(fake_ffmpeg, tmp_path: Path) -> None:
    fake_ffmpeg["duration"] = 9010.0  # 목표 9000은 끝에서 30초 안 — 두지 않는다
    plans = await AudioSplitAdapter().split(str(tmp_path / "audio.mp3"), str(tmp_path))
    assert len(plans) == 15
    assert plans[-1].duration_sec == pytest.approx(610.0)


async def test_oversize_chunk_is_halved(fake_ffmpeg, tmp_path: Path) -> None:
    fake_ffmpeg["duration"] = 1800.0
    fake_ffmpeg["big"] = {(600.0, 1200.0)}
    plans = await AudioSplitAdapter().split(str(tmp_path / "audio.mp3"), str(tmp_path))
    assert [(p.seq, p.offset_sec, p.duration_sec) for p in plans] == [
        (1, 0.0, 600.0),
        (2, 600.0, 300.0),
        (3, 900.0, 300.0),
        (4, 1200.0, 600.0),
    ]
    assert all(Path(p.path).exists() for p in plans)

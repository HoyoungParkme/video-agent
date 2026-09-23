"""job/adapters/audio_source — 자막 · 음성 확보(VA-MS-006 audio_source). infra는 가짜로."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.domains.job.adapters.audio_source import AudioSourceAdapter
from app.infra import ffmpeg, ytdlp
from app.infra.errors import FfmpegError, YtdlpError

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fake_ytdlp(monkeypatch):
    """ytdlp.info · captions 자리 — 정한 목록과 VTT를 준다. 부른 인자를 적는다."""
    state = {
        "raw": {"id": "abcdefghijk", "subtitles": {"ko": []}, "automatic_captions": {}},
        "vtt": "manual.vtt",
        "calls": [],
    }

    async def info(url: str) -> dict:
        state["calls"].append(("info", url))
        return state["raw"]

    async def captions(video_id: str, lang: str, kind: str) -> str:
        state["calls"].append(("captions", video_id, lang, kind))
        return (FIXTURES / state["vtt"]).read_text(encoding="utf-8")

    monkeypatch.setattr(ytdlp, "info", info)
    monkeypatch.setattr(ytdlp, "captions", captions)
    return state


async def test_manual_30_lines(fake_ytdlp) -> None:
    lines, lang, kind = await AudioSourceAdapter().captions("abcdefghijk")
    assert (lang, kind) == ("ko", "manual")
    assert len(lines) == 30
    assert (lines[0].start_sec, lines[0].end_sec) == (0.0, 7.0)
    assert (lines[1].start_sec, lines[1].end_sec) == (7.5, 14.5)  # 시가 없는 표기도 초로
    assert lines[3].text == "넷째 줄은 화자 태그가 있어요."  # 태그를 뗀다
    assert lines[4].text == "다섯째 줄은 두 줄로 나뉘어 있어요."  # 한 큐의 여러 줄은 한 줄로
    assert lines[5].text == "여섯째 줄 & 엔티티 <코드>"
    assert fake_ytdlp["calls"] == [
        ("info", "https://www.youtube.com/watch?v=abcdefghijk"),
        ("captions", "abcdefghijk", "ko", "manual"),
    ]


async def test_auto_rolling_cues_once_each(fake_ytdlp) -> None:
    fake_ytdlp["raw"] = {
        "id": "abcdefghijk",
        "subtitles": {},
        "automatic_captions": {"ko-orig": [], "en": []},
    }
    fake_ytdlp["vtt"] = "auto.vtt"
    lines, lang, kind = await AudioSourceAdapter().captions("abcdefghijk")
    assert (lang, kind) == ("ko", "auto")
    assert [line.text for line in lines] == [
        "안녕하세요 오늘은 파이썬을 배워 봅니다",
        "먼저 설치부터 해 볼게요",
        "설치가 끝나면 첫 코드를 씁니다",
        "마지막으로 정리합니다",
    ]  # 굴러가는 큐의 되풀이 · 10ms 전환 큐 · 태그가 없다
    assert [line.start_sec for line in lines] == [0.0, 4.01, 8.02, 12.03]
    assert fake_ytdlp["calls"][1] == (
        "captions",
        "abcdefghijk",
        "ko-orig",
        "auto",
    )  # 원래 언어 키로 받는다


async def test_same_text_in_a_row_merges(fake_ytdlp, monkeypatch) -> None:
    vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n음악\n\n00:00:02.000 --> 00:00:03.000\n음악\n\n00:00:03.000 --> 00:00:04.000\n노래 시작\n"
    fake_ytdlp["raw"] = {
        "id": "abcdefghijk",
        "subtitles": {},
        "automatic_captions": {"ko-orig": []},
    }

    async def captions(video_id: str, lang: str, kind: str) -> str:
        return vtt

    monkeypatch.setattr(ytdlp, "captions", captions)
    lines, _, _ = await AudioSourceAdapter().captions("abcdefghijk")
    assert [(line.start_sec, line.end_sec, line.text) for line in lines] == [
        (1.0, 3.0, "음악"),  # 끝 시각은 뒤 것
        (3.0, 4.0, "노래 시작"),
    ]


async def test_new_line_starting_like_previous_keeps_words(fake_ytdlp, monkeypatch) -> None:
    # 되풀이는 줄 단위다 — 앞 텍스트와 같은 글자로 시작하는 새 줄은 자르지 않는다
    vtt = (
        "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n \n네\n\n"
        "00:00:02.000 --> 00:00:04.000\n \n네 맞습니다\n\n"
        "00:00:04.000 --> 00:00:06.000\n네 맞습니다\n그래서 시작합니다\n"
    )
    fake_ytdlp["raw"] = {
        "id": "abcdefghijk",
        "subtitles": {},
        "automatic_captions": {"ko-orig": []},
    }

    async def captions(video_id: str, lang: str, kind: str) -> str:
        return vtt

    monkeypatch.setattr(ytdlp, "captions", captions)
    lines, _, _ = await AudioSourceAdapter().captions("abcdefghijk")
    assert [line.text for line in lines] == ["네", "네 맞습니다", "그래서 시작합니다"]


async def test_no_captions(fake_ytdlp) -> None:
    fake_ytdlp["raw"] = {"id": "abcdefghijk", "subtitles": {}, "automatic_captions": {}}
    assert await AudioSourceAdapter().captions("abcdefghijk") is None
    assert [c[0] for c in fake_ytdlp["calls"]] == ["info"]  # 자막을 받으러 가지 않는다


async def test_ytdlp_error_goes_up(monkeypatch) -> None:
    async def info(url: str) -> dict:
        raise YtdlpError("Video unavailable", "unavailable")

    monkeypatch.setattr(ytdlp, "info", info)
    with pytest.raises(YtdlpError):
        await AudioSourceAdapter().captions("abcdefghijk")


@pytest.fixture
def fake_media(monkeypatch):
    """ytdlp.download_audio · ffmpeg.extract_audio 자리 — 작은 파일을 실제로 쓴다. error를 넣으면 던진다."""
    state: dict = {"calls": [], "download_error": None, "extract_error": None}

    async def download_audio(video_id: str, dest: str) -> str:
        state["calls"].append(("download", video_id, dest))
        if state["download_error"]:
            raise state["download_error"]
        path = Path(dest) / "source.m4a"
        path.write_bytes(b"m4a")
        return str(path)

    async def extract_audio(src: str, dest: str) -> str:
        state["calls"].append(("extract", src, dest))
        if state["extract_error"]:
            raise state["extract_error"]
        out = Path(dest) / "audio.mp3"
        out.write_bytes(b"mp3")
        return str(out)

    monkeypatch.setattr(ytdlp, "download_audio", download_audio)
    monkeypatch.setattr(ffmpeg, "extract_audio", extract_audio)
    return state


async def test_download_audio_leaves_only_mp3(fake_media, tmp_path: Path) -> None:
    path = await AudioSourceAdapter().download_audio("abcdefghijk", str(tmp_path))
    assert path == str(tmp_path / "audio.mp3")
    assert [p.name for p in tmp_path.iterdir()] == ["audio.mp3"]  # 내려받은 원본이 남지 않는다
    assert [c[0] for c in fake_media["calls"]] == ["download", "extract"]


async def test_download_failure_goes_up(fake_media, tmp_path: Path) -> None:
    fake_media["download_error"] = YtdlpError("Video unavailable", "unavailable")
    with pytest.raises(YtdlpError):
        await AudioSourceAdapter().download_audio("abcdefghijk", str(tmp_path))


async def test_convert_failure_removes_download(fake_media, tmp_path: Path) -> None:
    fake_media["extract_error"] = FfmpegError("Invalid data", 1)
    with pytest.raises(FfmpegError):
        await AudioSourceAdapter().download_audio("abcdefghijk", str(tmp_path))
    assert list(tmp_path.iterdir()) == []

"""video/adapters/youtube_info — 주소 → SourceInfo(VA-MS-006 youtube_info.info). ytdlp는 가짜로."""

from __future__ import annotations

import pytest

from app.core.config import config
from app.core.errors import SourceUnavailable
from app.domains.video.adapters.youtube_info import YouTubeInfoAdapter
from app.infra import ytdlp
from app.infra.errors import YtdlpError

URL = "https://youtu.be/abcdefghijk"


@pytest.fixture
def raw(monkeypatch) -> dict:
    """ytdlp.info가 줄 JSON — 테스트가 고친다."""
    data = {
        "id": "abcdefghijk",
        "title": "파이썬 기초 강의",
        "channel": "코딩 채널",
        "uploader": "올린 사람",
        "duration": 3011.6,
        "subtitles": {"ko": []},
        "automatic_captions": {"en-orig": [], "en": [], "ko": []},
    }

    async def info(url: str, timeout: float | None = None) -> dict:
        return data

    monkeypatch.setattr(ytdlp, "info", info)
    return data


async def test_manual_ko_with_auto_en(raw) -> None:
    info = await YouTubeInfoAdapter().info(URL)
    assert (info.source_kind, info.source_id, info.title, info.channel) == (
        "youtube",
        "abcdefghijk",
        "파이썬 기초 강의",
        "코딩 채널",
    )
    assert info.duration_sec == 3011
    assert info.origin == "https://www.youtube.com/watch?v=abcdefghijk"  # 정규화한 주소
    assert (info.has_captions, info.caption_language, info.caption_kind) == (True, "ko", "manual")


async def test_auto_original_only(raw) -> None:
    raw["subtitles"] = {}
    info = await YouTubeInfoAdapter().info(URL)
    assert (info.has_captions, info.caption_language, info.caption_kind) == (True, "en", "auto")


async def test_translated_auto_only_is_no_captions(raw) -> None:
    raw["subtitles"] = {}
    raw["automatic_captions"] = {"ko": [], "ja": []}
    info = await YouTubeInfoAdapter().info(URL)
    assert (info.has_captions, info.caption_language, info.caption_kind) == (False, None, None)


async def test_channel_falls_back_to_uploader(raw) -> None:
    raw["channel"] = None
    assert (await YouTubeInfoAdapter().info(URL)).channel == "올린 사람"


async def test_no_duration(raw) -> None:
    raw["duration"] = None  # 라이브 · 예정
    with pytest.raises(SourceUnavailable) as e:
        await YouTubeInfoAdapter().info(URL)
    assert e.value.extra["reason"] == "길이를 알 수 없는 영상(라이브 · 예정)"


@pytest.mark.parametrize(
    ("kind", "reason", "hint"),
    [
        # 분석 실패 알림과 같은 명사구 — 시작 불가 판 '영상 정보를 가져오지 못했어요 — {이유}'
        ("private", "비공개 영상", None),
        ("unavailable", "삭제되었거나 볼 수 없는 영상", None),
        ("geo", "이 지역에서 볼 수 없는 영상", None),
        ("network", "YouTube 연결 실패", None),
        ("extractor", "yt-dlp가 영상을 읽지 못함 — yt-dlp 업데이트", "yt-dlp 업데이트"),
        ("other", "yt-dlp 오류", None),
    ],
)
async def test_ytdlp_errors(monkeypatch, kind, reason, hint) -> None:
    async def info(url: str, timeout: float | None = None) -> dict:
        raise YtdlpError("ERROR: [youtube] abcdefghijk: Private video", kind)

    monkeypatch.setattr(ytdlp, "info", info)
    with pytest.raises(SourceUnavailable) as e:
        await YouTubeInfoAdapter().info(URL)
    assert e.value.extra == {"reason": reason, "hint": hint}  # 한국어 이유, 영어 원문은 싣지 않는다


async def test_info_read_has_register_limit(monkeypatch) -> None:
    # 등록 요청 안이라 INFO_TIMEOUT_SEC를 준다 — 파이프라인의 자막 고르기는 주지 않는다(MS-006 v13)
    seen: list[float | None] = []

    async def info(url: str, timeout: float | None = None) -> dict:
        seen.append(timeout)
        return {"id": "abcdefghijk", "title": "제목", "duration": 60}

    monkeypatch.setattr(ytdlp, "info", info)
    await YouTubeInfoAdapter().info(URL)
    assert seen == [config.INFO_TIMEOUT_SEC]

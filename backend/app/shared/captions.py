"""자막 트랙 고르기 — yt-dlp 정보에서 수동 · 원래 언어 자동 자막 하나(VA-MS-006 captions.pick).

영상 등록(video의 youtube_info)과 자막 가져오기(job의 audio_source)가 같은 규칙을 쓴다 —
등록 때 알린 자막과 분석 때 받는 자막이 같게. 도메인 타입을 모르는 순수 함수다.
"""

from __future__ import annotations

from app.core.config import config

# 라이브 방송 다시 보기의 채팅 기록 — subtitles에 오지만 자막이 아니다
LIVE_CHAT = "live_chat"


def _lang(key: str) -> str:
    return key.split("-", 1)[0]


def pick(raw: dict) -> tuple[str, str, str] | None:
    """VA-MS-006#captions.pick

    수동 자막을 먼저 보고, 자동 자막은 원래 언어의 받아쓰기 하나만 본다. 나머지 자동 키는
    YouTube가 기계 번역한 것이라 고르지 않는다.

    Args:
        raw: ytdlp.info가 준 JSON — subtitles · automatic_captions · language

    Returns:
        (내려받을 키, 언어, "manual" 또는 "auto"). 고를 자막이 없으면 None
    """
    manual = [k for k in raw.get("subtitles") or {} if k != LIVE_CHAT]
    auto_keys = list(raw.get("automatic_captions") or {})
    orig = next((k for k in auto_keys if k.endswith("-orig")), None)
    if orig is None and raw.get("language") in auto_keys:
        orig = raw["language"]
    for lang in config.CAPTION_LANGS:
        for key in manual:
            if _lang(key) == lang:
                return key, lang, "manual"
    if orig is not None and _lang(orig) in config.CAPTION_LANGS:
        return orig, _lang(orig), "auto"
    if manual:
        return manual[0], _lang(manual[0]), "manual"
    if orig is not None:
        return orig, _lang(orig), "auto"
    return None

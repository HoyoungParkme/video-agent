"""shared/captions — 자막 트랙 고르기(VA-MS-006 captions.pick). 실제 yt-dlp 목록의 모양으로."""

from __future__ import annotations

from app.shared.captions import pick

# 자동 자막 목록 — 원래 언어의 받아쓰기 하나(-orig)와 YouTube가 번역한 것들
TRANSLATED = {k: [] for k in ("ab", "af", "ja", "ko", "de-DE", "zh-Hans")}


def test_manual_first_in_caption_langs() -> None:
    raw = {"subtitles": {"ko": []}, "automatic_captions": {"en-orig": [], **TRANSLATED}}
    assert pick(raw) == ("ko", "ko", "manual")


def test_auto_original_not_translation() -> None:
    raw = {"subtitles": {}, "automatic_captions": {"en": [], "en-orig": [], **TRANSLATED}}
    assert pick(raw) == ("en-orig", "en", "auto")  # 번역 ko를 고르지 않는다


def test_manual_key_with_track_name() -> None:
    raw = {"subtitles": {"en-FmoQciUtYSc": [], "ko-FmoQciUtYSc": []}, "automatic_captions": {}}
    assert pick(raw) == ("ko-FmoQciUtYSc", "ko", "manual")  # 키는 그대로, 언어는 앞 부분


def test_auto_in_caption_langs_beats_other_manual() -> None:
    raw = {"subtitles": {"ja": []}, "automatic_captions": {"en-orig": [], **TRANSLATED}}
    assert pick(raw) == ("en-orig", "en", "auto")


def test_other_manual_beats_other_auto() -> None:
    raw = {"subtitles": {"ja": []}, "automatic_captions": {"fr-orig": [], **TRANSLATED}}
    assert pick(raw) == ("ja", "ja", "manual")


def test_other_auto_last() -> None:
    raw = {"subtitles": {}, "automatic_captions": {"fr-orig": [], **TRANSLATED}}
    assert pick(raw) == ("fr-orig", "fr", "auto")


def test_live_chat_is_not_a_caption() -> None:
    assert pick({"subtitles": {"live_chat": []}, "automatic_captions": {}}) is None


def test_language_key_when_no_orig() -> None:
    raw = {"subtitles": {}, "automatic_captions": {"ko": [], "en": []}, "language": "ko"}
    assert pick(raw) == ("ko", "ko", "auto")
    only_translations = {"subtitles": {}, "automatic_captions": TRANSLATED, "language": "fr"}
    assert pick(only_translations) is None


def test_nothing() -> None:
    assert pick({"subtitles": {}, "automatic_captions": {}}) is None
    assert pick({}) is None

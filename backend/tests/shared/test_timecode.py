"""shared/timecode — label · parse(VA-MS-006 테스트 관점)."""

from __future__ import annotations

import pytest

from app.shared import timecode


@pytest.mark.parametrize(
    ("sec", "long", "text"),
    [
        (760.12, False, "12:40"),
        (380, True, "0:06:20"),
        (3600, True, "1:00:00"),
        (3900, False, "65:00"),
    ],
)
def test_label(sec: float, long: bool, text: str) -> None:
    assert timecode.label(sec, long) == text


@pytest.mark.parametrize(
    ("text", "end", "sec"),
    [
        ("12:40", 3000, 760),
        ("[12:40]", 3000, 760),
        (" 12:40 ", 3000, 760),
        ("1:02:03", 9000, 3723),
        ("65:00", 9000, 3900),
        ("12:40:00", 3000, 760),  # 60분 미만 스크립트 — 모델이 바꿔 쓴 표기
        ("12:4a", 3000, None),
        ("12:75", 3000, None),
        ("1:75:00", 9000, None),
        ("12", 3000, None),
        ("", 3000, None),
    ],
)
def test_parse(text: str, end: float, sec: float | None) -> None:
    assert timecode.parse(text, end) == sec

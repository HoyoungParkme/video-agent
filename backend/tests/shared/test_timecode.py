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

"""shared/tokens — estimate(VA-MS-006 테스트 관점)."""

from __future__ import annotations

import pytest

from app.shared import tokens


@pytest.mark.parametrize(
    ("texts", "expected"),
    [
        ([], 0),
        (["abcd"], 9),  # 4바이트 ÷ 4 + 줄 몫 8
        (["가나다라"], 11),  # 한글은 한 글자 3바이트 — 12 ÷ 4 + 8
        (["abcd", "가나다라", ""], 28),  # 줄 수만큼 8씩 — 빈 줄도 시각 표기는 붙는다
    ],
)
def test_estimate(texts: list[str], expected: int) -> None:
    assert tokens.estimate(texts) == expected


def test_estimate_takes_generator() -> None:
    segments = [("[00:00]", "abcd"), ("[00:10]", "가나다라")]
    assert tokens.estimate(text for _, text in segments) == 20

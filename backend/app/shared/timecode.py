"""시각 표기 — 초 ↔ `mm:ss` · `h:mm:ss`(VA-MS-006). OpenAI 어댑터 둘과 내보내기가 쓰는 순수 함수."""

from __future__ import annotations


def label(sec: float, long: bool) -> str:
    """VA-MS-006#timecode.label

    초를 시각 표기로 바꾼다. 소수는 버린다. 짧은 표기는 분이 60을 넘어도 그대로 쓴다(`65:00`).

    Args:
        sec: 초
        long: 참이면 `h:mm:ss`, 아니면 `mm:ss`

    Returns:
        시각 표기
    """
    s = int(sec)
    if long:
        return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"
    return f"{s // 60:02d}:{s % 60:02d}"

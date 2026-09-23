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


def parse(text: str, end_sec: float) -> float | None:
    """VA-MS-006#timecode.parse

    모델이 쓴 시각을 초로 되돌린다. 60분 미만 스크립트의 `12:40`을 모델이 `12:40:00`으로
    바꿔 쓴 경우는 앞 두 칸을 분 · 초로 읽는다.

    Args:
        text: `12:40` · `[12:40]` · `1:02:03` 같은 표기
        end_sec: 보낸 스크립트의 끝 시각(초)

    Returns:
        초. 읽을 수 없으면 None
    """
    parts = text.strip().strip("[]").split(":")
    if not all(p.isdigit() for p in parts):
        return None
    if len(parts) == 2:
        m, s = (int(p) for p in parts)
        return None if s >= 60 else float(m * 60 + s)
    if len(parts) == 3:
        h, m, s = (int(p) for p in parts)
        if m >= 60 or s >= 60:
            return None
        v = h * 3600 + m * 60 + s
        if v > end_sec + 60 and h * 60 + m <= end_sec + 60:
            return float(h * 60 + m)
        return float(v)
    return None

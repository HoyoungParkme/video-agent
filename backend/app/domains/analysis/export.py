"""내보내기 마크다운 — 순수 함수(VA-MS-003 export). 결과 서비스(`export_markdown`)가 부른다.

시각 표기는 영상 길이로 정하고(`timecode`), YouTube면 그 시점 링크를 건다(`link`).
"""

from __future__ import annotations

from app.shared.timecode import label


def timecode(sec: float, duration_sec: int) -> str:
    """VA-MS-003#export.timecode

    초 → 시각 표기. 1시간 이상 영상은 `h:mm:ss`, 아니면 `mm:ss` — 한 영상 안에서 섞이지 않는다.
    표기 규칙은 공용 `timecode.label` 하나에만 둔다.

    Args:
        sec: 초
        duration_sec: 영상 길이(초) — 표기를 정한다

    Returns:
        `12:40` 또는 `1:02:03`
    """
    return label(sec, duration_sec >= 3600)

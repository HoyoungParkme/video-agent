"""analysis/export — 내보내기 마크다운의 순수 함수(VA-MS-003 export)."""

from __future__ import annotations

from app.domains.analysis import export


def test_timecode_follows_video_length() -> None:
    assert export.timecode(760.12, 3000) == "12:40"  # 50분 영상
    assert export.timecode(380, 9000) == "0:06:20"  # 150분 영상은 h:mm:ss
    assert export.timecode(3600, 9000) == "1:00:00"

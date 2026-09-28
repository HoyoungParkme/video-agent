"""analysis/export — 내보내기 마크다운의 순수 함수(VA-MS-003 export)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domains.analysis import export
from app.domains.video.models import CaptionKind, SourceKind
from app.domains.video.schemas import Video, VideoStatus

T0 = datetime(2026, 9, 28, 1, 0, tzinfo=UTC)


def video(kind: SourceKind = SourceKind.youtube, duration: int = 3000, **extra) -> Video:
    youtube = kind == SourceKind.youtube
    values = {
        "id": 12,
        "source_kind": kind,
        "source_id": "dQw4w9WgXcQ" if youtube else "a" * 64,
        "title": "RAG 서비스 1년 운영기",
        "channel": "E2E 채널" if youtube else None,
        "duration_sec": duration,
        "origin": "https://youtu.be/dQw4w9WgXcQ" if youtube else "workshop_0912.mp4",
        "has_captions": youtube,
        "caption_language": "ko" if youtube else None,
        "caption_kind": CaptionKind.manual if youtube else None,
        "status": VideoStatus.analyzed,
        "analyzed_at": T0,
        "created_at": T0,
        "chat_turn_count": 0,
    }
    return Video(**(values | extra))


def test_timecode_follows_video_length() -> None:
    assert export.timecode(760.12, 3000) == "12:40"  # 50분 영상
    assert export.timecode(380, 9000) == "0:06:20"  # 150분 영상은 h:mm:ss
    assert export.timecode(3600, 9000) == "1:00:00"


def test_link_youtube_goes_to_that_second() -> None:
    assert export.link(760.9, video()) == "[12:40](https://youtu.be/dQw4w9WgXcQ?t=760)"


def test_link_local_file_is_text_only() -> None:
    assert export.link(760, video(SourceKind.local)) == "[12:40]"
    assert export.link(380, video(SourceKind.local, duration=9000)) == "[0:06:20]"

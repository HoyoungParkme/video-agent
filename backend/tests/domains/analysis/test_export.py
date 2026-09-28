"""analysis/export — 내보내기 마크다운의 순수 함수(VA-MS-003 export)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.core.settings import Models
from app.domains.analysis import export
from app.domains.analysis.models import TranscriptSource
from app.domains.analysis.schemas import (
    Chapter,
    Insight,
    Part,
    Result,
    Segment,
    Summary,
    Transcript,
)
from app.domains.chat.schemas import ChatTurn
from app.domains.video.models import CaptionKind, SourceKind
from app.domains.video.schemas import Video, VideoStatus

T0 = datetime(2026, 9, 28, 1, 0, tzinfo=UTC)
SNAP = Path(__file__).parent / "snapshots"


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


def segs(*rows: tuple[float, str]) -> list[Segment]:
    return [
        Segment(seq=i + 1, start_sec=start, end_sec=start + 20, text=text)
        for i, (start, text) in enumerate(rows)
    ]


def youtube_50m() -> Result:
    """자막 있는 50분 YouTube — 파트 없음."""
    return Result(
        video=video(),
        transcript=Transcript(
            source=TranscriptSource.caption_manual,
            language="ko",
            model=None,
            segments=segs(
                (0, "안녕하세요, 검색 품질 이야기를 하겠습니다."),
                (100, "틀린 답의 원인은 대부분 검색 단계에 있었습니다."),
                (600, "청킹 크기를 512에서 256 토큰으로 줄였습니다."),
                (1200, "pgvector로 원본과 같은 DB에 두었습니다."),
            ),
        ),
        summary=Summary(
            one_liner="RAG 서비스를 1년 운영하며 검색 품질 문제를 찾고 고친 과정을 공유하는 발표.",
            model="gpt-5-mini",
            insights=[
                Insight(
                    seq=1, text="틀린 답의 원인은 대부분 검색 단계에 있었다.", source_secs=[100]
                ),
                Insight(seq=2, text="청킹 크기를 줄이자 재현율이 올랐다.", source_secs=[600, 700]),
            ],
        ),
        parts=[],
        chapters=[
            Chapter(
                seq=1,
                part_seq=None,
                start_sec=0,
                title="발표자 소개",
                bullets=["팀과 서비스", "오늘 주제"],
            ),
            Chapter(
                seq=2,
                part_seq=None,
                start_sec=600,
                title="청킹 다시 보기",
                bullets=["256 토큰으로"],
            ),
            Chapter(
                seq=3, part_seq=None, start_sec=1200, title="pgvector 선택", bullets=["같은 DB"]
            ),
        ],
        suggested_questions=[],
        models=Models(stt="whisper-1", text="gpt-5-mini"),
        analyzed_at=T0,
    )


def local_150m() -> Result:
    """받아쓰기한 150분 로컬 파일 — 파트 둘, 링크 없음."""
    return Result(
        video=video(
            SourceKind.local, duration=9000, title="workshop_0912.mp4", origin="workshop_0912.mp4"
        ),
        transcript=Transcript(
            source=TranscriptSource.stt,
            language="ko",
            model="whisper-1",
            segments=segs(
                (0, "워크숍을 시작하겠습니다."),
                (380, "오늘은 데이터 카탈로그를 다룹니다."),
                (3600, "두 번째 세션입니다."),
                (5400, "소유자를 정하는 방법입니다."),
            ),
        ),
        summary=Summary(
            one_liner="데이터 카탈로그를 처음부터 만드는 종일 워크숍.",
            model="gpt-5-mini",
            insights=[Insight(seq=1, text="카탈로그는 소유자부터 정한다.", source_secs=[5400])],
        ),
        parts=[
            Part(seq=1, title="1부 — 기초", start_sec=0, end_sec=3600, chapter_count=2),
            Part(seq=2, title="2부 — 운영", start_sec=3600, end_sec=9000, chapter_count=2),
        ],
        chapters=[
            Chapter(seq=1, part_seq=1, start_sec=0, title="소개", bullets=["목표와 일정"]),
            Chapter(
                seq=2, part_seq=1, start_sec=380, title="카탈로그란", bullets=["메타데이터", "검색"]
            ),
            Chapter(
                seq=3, part_seq=2, start_sec=3600, title="두 번째 세션", bullets=["운영 이야기"]
            ),
            Chapter(
                seq=4, part_seq=2, start_sec=5400, title="소유자 정하기", bullets=["팀마다 한 명"]
            ),
        ],
        suggested_questions=[],
        models=Models(stt="whisper-1", text="gpt-5-mini"),
        analyzed_at=T0,
    )


def turn(i: int, question: str, answer: str, cited: list[float]) -> ChatTurn:
    return ChatTurn(id=i, question=question, answer=answer, cited_secs=cited, asked_at=T0)


def test_build_youtube_50m_snapshot() -> None:
    # 제목 → 원본 링크 → 한 줄 요약 → 인사이트(시각 둘 다) → 챕터 → 출처 줄 · 스크립트, 질문 기록 절 없음
    expected = (SNAP / "export_youtube_50m.md").read_text(encoding="utf-8")
    assert export.build(youtube_50m(), None) == expected


def test_build_local_150m_snapshot() -> None:
    # 원본 줄에 링크 없음 · 파트 머리 · 시각은 h:mm:ss 글자 · 받아쓰기 출처 · 빈 질문 기록
    expected = (SNAP / "export_local_150m.md").read_text(encoding="utf-8")
    assert export.build(local_150m(), []) == expected


def test_build_chat_section_at_the_end() -> None:
    turns = [
        turn(1, "어떤 DB를 썼어?", "pgvector를 썼다고 합니다.", [1200.0]),
        turn(2, "매출은?", "이 영상에서는 다루지 않습니다.", []),
    ]
    md = export.build(youtube_50m(), turns)
    assert md.endswith(
        "## 질문 기록\n"
        "**Q.** 어떤 DB를 썼어?\n"
        "**A.** pgvector를 썼다고 합니다.\n"
        "근거: [20:00](https://youtu.be/dQw4w9WgXcQ?t=1200)\n"
        "\n"
        "**Q.** 매출은?\n"
        "**A.** 이 영상에서는 다루지 않습니다.\n"
    )
    assert "## 질문 기록" not in export.build(youtube_50m(), None)  # None이면 절이 없다


def test_build_source_line_like_the_screen() -> None:
    result = youtube_50m()
    result.transcript.source = TranscriptSource.caption_auto
    result.transcript.language = "xx"  # 표에 없는 코드는 그대로
    assert "## 스크립트\n자막(자동) · xx\n\n" in export.build(result, None)

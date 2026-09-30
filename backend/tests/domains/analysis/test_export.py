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


def glance_42m(chapter_count: int = 8) -> Result:
    """42:24 YouTube — 와이어프레임 UI-7 4.1(그림이 든 노트)의 한눈에 보기 블록과 같은 값."""
    starts = [0, 96, 195, 591, 738, 1454, 1872, 2429]
    titles = [
        "강사 소개와 목표",
        "제품 성장 단계 비유",
        "초기 단계의 핵심 이슈",
        "코어 이벤트와 지표 정의",
        "성장기: 문제 세분화와 운영",
        "성숙기: 확장과 본부 관점",
        "의사결정 어려움과 해법",
        "정리 및 권장 실천",
    ]
    bullets = [
        [
            "발표자 소개(카일 스쿨, 데이터 교육·코칭)와 발표에서 다룰 주제 안내.",
            "청중이 얻어가길 바라는 것(지표 활용, 지표 발굴 과정, 의사결정 감각)을 설명.",
        ],
        [
            "식당을 예로 들어 제품의 초기·성장·성숙 단계를 정의하고 각 단계의 목표 설명.",
            "초기: 고객의 문제를 찾아 제품을 맞추기, 성장: PMF 이후 문제 해결·확장, "
            "성숙: 기존 강점 유지와 관련 분야 확장.",
        ],
        [
            "초기 식당에서 발생 가능한 상황(무관심, 유입 후 이탈, 주문·만족·후기 등) 정리.",
            "초기 핵심 지표 제안: 방문자 수, 재방문(리텐션), 매출·이익 등 소수 지표에 집중할 것 권장.",
        ],
    ] + [["요점"]] * 5
    firsts = [122, 319, 591, 942, 1230, 1970, 2223, 1771]
    return Result(
        video=video(duration=2544, title="제품 성장 단계에 따른 지표 찾기 여정 | 인프콘2024"),
        transcript=Transcript(
            source=TranscriptSource.caption_auto, language="ko", model=None, segments=segs()
        ),
        summary=Summary(
            one_liner="제품의 성장 단계(초기·성장기·성숙기)에 따라 어떤 지표를 골라 집중해야 하는지와 "
            "의사결정을 돕는 실무적 방법(코어 이벤트, 퍼널/기능 지표, 페르미 추정, 지표의 위계 및 "
            "지표 기반 회의)을 정리한 강연입니다.",
            model="gpt-5-mini",
            insights=[
                Insight(seq=n + 1, text=f"인사이트 {n + 1}", source_secs=[sec, sec + 30])
                for n, sec in enumerate(firsts)
            ],
        ),
        parts=[],
        chapters=[
            Chapter(seq=n + 1, part_seq=None, start_sec=s, title=t, bullets=b)
            for n, (s, t, b) in enumerate(zip(starts, titles, bullets, strict=True))
        ][:chapter_count],
        suggested_questions=[],
        models=Models(stt=None, text="gpt-5-mini"),
        analyzed_at=T0,
    )


def test_gantt_matches_the_wireframe_block() -> None:
    # 챕터 구간(끝은 다음 챕터의 시작, 마지막은 영상 길이) · 인사이트 이정표(첫 출처 시각)
    expected = (SNAP / "glance_42m_gantt.md").read_text(encoding="utf-8")
    assert export.gantt(glance_42m()) + "\n" == expected


def test_gantt_long_video_has_part_sections_and_hour_axis() -> None:
    md = export.gantt(local_150m())
    assert "  axisFormat %-H:%M:%S" in md  # 1시간 이상은 앱의 h:mm:ss 모양
    assert (
        "  section 1부 — 기초\n  소개 : 00:00:00, 00:06:20\n  카탈로그란 : 00:06:20, 01:00:00" in md
    )
    assert "  section 2부 — 운영\n" in md and "  소유자 정하기 : 01:30:00, 02:30:00\n" in md
    assert "  section 챕터" not in md
    assert md.endswith("  section 인사이트\n  01 : milestone, 01:30:00, 0s\n```")


def test_gantt_escapes_what_gantt_reads_as_separators() -> None:
    result = youtube_50m()
    result.chapters[0].title = "A: B; C #1 `x`\n줄"
    result.chapters[1].title = "   "
    md = export.gantt(result)
    assert "  A∶ B； C ＃1 'x' 줄 : 00:00:00, 00:10:00\n" in md
    assert "  챕터 2 : 00:10:00, 00:20:00\n" in md  # 비면 번호로


def test_gantt_zero_length_chapter_gets_one_second() -> None:
    result = youtube_50m()
    result.chapters[2].start_sec = 3000  # 영상 끝과 같은 시각
    assert "  pgvector 선택 : 00:50:00, 00:50:01\n" in export.gantt(result)


def test_mindmap_matches_the_wireframe_block() -> None:
    # 뿌리 = 한 줄 요약 → 챕터(시각 · 제목) → 요점, 괄호는 전각(와이어프레임은 셋째 챕터까지 보인다)
    expected = (SNAP / "glance_42m_mindmap.md").read_text(encoding="utf-8")
    assert export.mindmap(glance_42m(chapter_count=3)) + "\n" == expected


def test_mindmap_long_video_goes_root_part_chapter_bullet() -> None:
    assert export.mindmap(local_150m()) == (
        "```mermaid\n"
        "mindmap\n"
        "  root(데이터 카탈로그를 처음부터 만드는 종일 워크숍.)\n"
        "    0:00:00 1부 — 기초\n"
        "      0:00:00 소개\n"
        "        목표와 일정\n"
        "      0:06:20 카탈로그란\n"
        "        메타데이터\n"
        "        검색\n"
        "    1:00:00 2부 — 운영\n"
        "      1:00:00 두 번째 세션\n"
        "        운영 이야기\n"
        "      1:30:00 소유자 정하기\n"
        "        팀마다 한 명\n"
        "```"
    )


def test_mindmap_brackets_do_not_close_nodes() -> None:
    result = youtube_50m()
    result.summary.one_liner = "요약 (a) [b] {c} `d`\n끝"
    result.chapters[0].bullets = ["괄호 ) 하나"]
    md = export.mindmap(result)
    assert "  root(요약 （a） ［b］ ｛c｝ 'd' 끝)\n" in md
    assert "      괄호 ） 하나\n" in md


def turn(i: int, question: str, answer: str, cited: list[float]) -> ChatTurn:
    return ChatTurn(id=i, question=question, answer=answer, cited_secs=cited, asked_at=T0)


def test_build_youtube_50m_snapshot() -> None:
    # 제목 → 원본 링크 → 한 줄 요약 → 인사이트(시각 둘 다) → 챕터, 스크립트 · 질문 기록 절 없음
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


def test_build_glance_section_between_one_liner_and_insights() -> None:
    # 한눈에 보기 절 — Mermaid 블록 둘(gantt · mindmap). 파일로 저장이든 복사든 들어간다
    result = youtube_50m()
    for md in (export.build(result, None), export.build(result, None, "RAG 서비스 1년 운영기")):
        assert md.index("> RAG 서비스") < md.index("## 한눈에 보기") < md.index("## 핵심 인사이트")
        assert f"## 한눈에 보기\n{export.gantt(result)}\n\n{export.mindmap(result)}\n\n" in md


def test_build_note_has_no_script_lines() -> None:
    # 스크립트 줄은 노트에 없다 — 따로 쓰는 파일이다(MS-003 v8)
    md = export.build(youtube_50m(), None)
    assert "## 스크립트" not in md and "안녕하세요, 검색 품질 이야기를" not in md


def test_build_links_script_file_between_chapters_and_chat() -> None:
    # 파일로 저장할 때만 — 챕터 다음, 질문 기록 앞에 위키링크 한 줄
    md = export.build(youtube_50m(), [], "RAG 서비스 1년 운영기")
    tail = (
        "\n## 스크립트\n[[RAG 서비스 1년 운영기 스크립트]]\n\n## 질문 기록\n질문 기록이 없습니다\n"
    )
    assert md.endswith(tail)
    assert md.index("## 챕터") < md.index("## 스크립트")


def test_build_script_youtube_50m_snapshot() -> None:
    # 제목 — 스크립트 → 원본 링크 → 출처 줄 → 구간마다 시점 링크와 문장
    expected = (SNAP / "export_youtube_50m_script.md").read_text(encoding="utf-8")
    assert export.build_script(youtube_50m()) == expected


def test_build_script_local_150m_snapshot() -> None:
    # 원본 줄에 링크 없음 · 시각은 h:mm:ss 글자 · 받아쓰기 출처
    expected = (SNAP / "export_local_150m_script.md").read_text(encoding="utf-8")
    assert export.build_script(local_150m()) == expected


def test_build_script_source_line_like_the_screen() -> None:
    result = youtube_50m()
    result.transcript.source = TranscriptSource.caption_auto
    result.transcript.language = "xx"  # 표에 없는 코드는 그대로
    assert "\n\n자막(자동) · xx\n\n" in export.build_script(result)

"""내보내기 마크다운 — 순수 함수(VA-MS-003 export). 결과 서비스(`export_markdown`)가 부른다.

시각 표기는 영상 길이로 정하고(`timecode`), YouTube면 그 시점 링크를 건다(`link`). `build`가
제목 → 원본 → 한 줄 요약 → 핵심 인사이트 → 챕터 → 스크립트 → (질문 기록) 순서로 잇는다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domains.analysis.models import TranscriptSource
from app.domains.analysis.schemas import Chapter, Result, Transcript
from app.domains.video.models import SourceKind
from app.domains.video.schemas import Video
from app.shared.timecode import label

if TYPE_CHECKING:  # 타입만 — 결과 묶음은 대화 묶음을 import하지 않는다(DOM-002 3.2)
    from app.domains.chat.schemas import ChatTurn

# 언어 코드 → 이름. 화면(frontend/src/labels.ts)과 같은 표의 사본 — 서버와 화면이 따로 그린다
LANGUAGES = {
    "ko": "한국어",
    "en": "영어",
    "ja": "일본어",
    "zh": "중국어",
    "es": "스페인어",
    "fr": "프랑스어",
    "de": "독일어",
    "pt": "포르투갈어",
    "ru": "러시아어",
    "vi": "베트남어",
}
NO_CHAT = "질문 기록이 없습니다"


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


def link(sec: float, video: Video) -> str:
    """VA-MS-003#export.link

    시각 → 마크다운 링크 또는 글자. YouTube면 그 시점(`?t=초`)으로 가는 링크, 로컬 파일은 글자만.

    Args:
        sec: 초
        video: 그 영상 — 출처 · 영상 ID · 길이

    Returns:
        `[12:40](https://youtu.be/{영상ID}?t=760)` 또는 `[12:40]`
    """
    t = timecode(sec, video.duration_sec)
    if video.source_kind == SourceKind.youtube:
        return f"[{t}](https://youtu.be/{video.source_id}?t={int(sec)})"
    return f"[{t}]"


def build(result: Result, turns: list[ChatTurn] | None) -> str:
    """VA-MS-003#export.build

    결과 → 마크다운 하나. 옵시디언 · 노션에 그대로 붙는다. 시각은 문장 끝에 전부 남긴다.

    Args:
        result: 결과 화면이 받는 것 전부
        turns: 질문 기록. None이면 절을 붙이지 않고, 빈 목록이면 절 제목과 '질문 기록이 없습니다'

    Returns:
        마크다운(줄바꿈 `\n`, 끝에 줄바꿈 하나)
    """
    v = result.video

    def at(sec: float) -> str:
        return timecode(sec, v.duration_sec)

    origin = f"[{v.origin}]({v.origin})" if v.source_kind == SourceKind.youtube else v.origin
    lines = [f"# {v.title}", f"원본: {origin} · {at(v.duration_sec)}"]
    lines += ["", f"> {result.summary.one_liner}", "", "## 핵심 인사이트"]
    for i in result.summary.insights:
        lines.append(" ".join([f"{i.seq}. {i.text}", *(link(s, v) for s in i.source_secs)]))
    lines += ["", "## 챕터"]
    if result.parts:
        for n, part in enumerate(result.parts):
            span = f"{at(part.start_sec)} – {at(part.end_sec)}"
            lines += [""] * (n > 0) + [f"### {part.title} ({span})"]
            inside = [c for c in result.chapters if c.part_seq == part.seq]
            lines += _chapters(inside, v, "####")
    else:
        lines += _chapters(result.chapters, v, "###")
    lines += ["", "## 스크립트", _source(result.transcript), ""]
    lines += [f"{link(s.start_sec, v)} {s.text}" for s in result.transcript.segments]
    if turns is not None:
        lines += ["", "## 질문 기록"]
        if not turns:
            lines.append(NO_CHAT)
        for t in turns:
            lines += [f"**Q.** {t.question}", f"**A.** {t.answer}"]
            if t.cited_secs:
                lines.append(" ".join(["근거:", *(link(s, v) for s in t.cited_secs)]))
            lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def _chapters(chapters: list[Chapter], video: Video, mark: str) -> list[str]:
    # 챕터마다 머리 줄과 요점 — 챕터 사이는 빈 줄
    lines: list[str] = []
    for n, c in enumerate(chapters):
        lines += [""] * (n > 0) + [f"{mark} {link(c.start_sec, video)} {c.title}"]
        lines += [f"- {b}" for b in c.bullets]
    return lines


def _source(t: Transcript) -> str:
    # 스크립트 출처 — 화면 8.1과 같은 문구
    lang = LANGUAGES.get(t.language, t.language)
    if t.source == TranscriptSource.caption_manual:
        return f"자막(수동) · {lang}"
    if t.source == TranscriptSource.caption_auto:
        return f"자막(자동) · {lang}"
    return f"받아쓰기 {t.model or ''} · {lang}"

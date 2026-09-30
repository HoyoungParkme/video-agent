"""내보내기 마크다운 — 순수 함수(VA-MS-003 export). 결과 서비스(`export_markdown`)가 부른다.

시각 표기는 영상 길이로 정하고(`timecode`), YouTube면 그 시점 링크를 건다(`link`). `build`가
노트를 제목 → 원본 → 한 줄 요약 → 핵심 인사이트 → 챕터 → (스크립트 파일 링크) → (질문 기록)
순서로 잇는다. 스크립트는 노트에 없다 — 따로 쓰는 파일이다(PRD R10).
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
# Mermaid gantt가 구분자로 읽는 글자 → 비슷해 보이는 다른 글자(MS-003 export.gantt)
GANTT_CHARS = str.maketrans({":": "∶", ";": "；", "#": "＃", "`": "'", "\n": " "})
# Mermaid mindmap이 노드 모양으로 읽는 괄호 → 전각(MS-003 export.mindmap)
MIND_CHARS = str.maketrans("()[]{}`\n", "（）［］｛｝' ")


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


def gantt(result: Result) -> str:
    """VA-MS-003#export.gantt

    한눈에 보기 — 타임라인. Mermaid `gantt` 블록(울타리 포함)이고 옵시디언이 그대로 그린다.
    챕터는 시작부터 다음 챕터의 시작까지(마지막은 영상 길이)의 막대, 파트가 있으면 파트마다
    구역, 인사이트는 첫 출처 시각의 이정표다. `timeline`은 시각 `00:00`의 쌍점을 구분자로 읽어
    깨져 `gantt`를 쓴다(INFRA 3절).

    Args:
        result: 결과 화면이 받는 것 전부

    Returns:
        ```` ```mermaid ````로 시작해 ```` ``` ````로 끝나는 블록(끝에 줄바꿈 없음)
    """
    v = result.video
    axis = "%-H:%M:%S" if v.duration_sec >= 3600 else "%M:%S"  # 앱의 h:mm:ss와 같은 모양
    lines = ["```mermaid", "gantt", "  dateFormat HH:mm:ss", f"  axisFormat {axis}"]
    ends = [c.start_sec for c in result.chapters[1:]] + [v.duration_sec]
    bars = {c.seq: _bar(c, end) for c, end in zip(result.chapters, ends, strict=True)}
    if result.parts:
        for p in result.parts:
            lines.append(f"  section {_gantt_name(p.title, f'파트 {p.seq}')}")
            lines += [bars[c.seq] for c in result.chapters if c.part_seq == p.seq]
    else:
        lines.append("  section 챕터")
        lines += bars.values()
    lines.append("  section 인사이트")
    lines += [
        f"  {i.seq:02d} : milestone, {_hms(i.source_secs[0])}, 0s"
        for i in result.summary.insights
        if i.source_secs
    ]
    lines.append("```")
    return "\n".join(lines)


def mindmap(result: Result) -> str:
    """VA-MS-003#export.mindmap

    한눈에 보기 — 마인드맵. Mermaid `mindmap` 블록(울타리 포함). 뿌리는 한 줄 요약, 그 아래
    파트(있으면) → 챕터(시각과 제목) → 요점. 들여쓰기 두 칸이 한 단계다. mindmap은 괄호를 노드
    모양으로 읽어 글 속 괄호를 전각으로 바꾼다.

    Args:
        result: 결과 화면이 받는 것 전부

    Returns:
        ```` ```mermaid ````로 시작해 ```` ``` ````로 끝나는 블록(끝에 줄바꿈 없음)
    """
    v = result.video

    def chapter(c: Chapter, pad: str) -> list[str]:
        head = f"{pad}{timecode(c.start_sec, v.duration_sec)} {_mind_text(c.title)}"
        return [head] + [f"{pad}  {_mind_text(b)}" for b in c.bullets]

    lines = ["```mermaid", "mindmap", f"  root({_mind_text(result.summary.one_liner)})"]
    if result.parts:
        for p in result.parts:
            lines.append(f"    {timecode(p.start_sec, v.duration_sec)} {_mind_text(p.title)}")
            for c in result.chapters:
                if c.part_seq == p.seq:
                    lines += chapter(c, "      ")
    else:
        for c in result.chapters:
            lines += chapter(c, "    ")
    lines.append("```")
    return "\n".join(lines)


def build(result: Result, turns: list[ChatTurn] | None, script_name: str | None = None) -> str:
    """VA-MS-003#export.build

    결과 → 노트 마크다운. 옵시디언 · 노션에 그대로 붙는다. 시각은 문장 끝에 전부 남긴다. 스크립트
    줄은 노트에 없다 — 길면 노트가 스크립트로 가득 찬다(2시간 30분에 5천 줄). 따로 쓰는 파일이다.

    Args:
        result: 결과 화면이 받는 것 전부
        turns: 질문 기록. None이면 절을 붙이지 않고, 빈 목록이면 절 제목과 '질문 기록이 없습니다'
        script_name: 파일로 저장할 때의 스크립트 파일 이름(확장자 없이). 오면 챕터 다음에 그 파일을
            가리키는 위키링크 절을 둔다. 미리 보기 · 복사는 None — 가리킬 파일이 없다

    Returns:
        마크다운(줄바꿈 `\n`, 끝에 줄바꿈 하나)
    """
    v = result.video

    def at(sec: float) -> str:
        return timecode(sec, v.duration_sec)

    lines = [f"# {v.title}", _origin(v)]
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
    if script_name:
        lines += ["", "## 스크립트", f"[[{script_name}]]"]
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


def build_script(result: Result) -> str:
    """VA-MS-003#export.build_script

    결과 → 스크립트 마크다운. 노트 곁에 `{파일 이름} 스크립트.md`로 쓰이고, 노트가 위키링크로
    가리킨다. 구간마다 시각(YouTube면 그 시점 링크)과 문장 한 줄 — 줄바꿈 하나로 잇는다.

    Args:
        result: 결과 화면이 받는 것 전부

    Returns:
        마크다운(줄바꿈 `\n`, 끝에 줄바꿈 하나)
    """
    v = result.video
    lines = [f"# {v.title} — 스크립트", _origin(v), "", _source(result.transcript), ""]
    lines += [f"{link(s.start_sec, v)} {s.text}" for s in result.transcript.segments]
    return "\n".join(lines).rstrip("\n") + "\n"


def _origin(video: Video) -> str:
    # 원본 줄 — YouTube면 주소 링크, 로컬 파일이면 파일 이름만(UI-7 규칙). 길이 붙음
    at = timecode(video.duration_sec, video.duration_sec)
    if video.source_kind == SourceKind.youtube:
        return f"원본: [{video.origin}]({video.origin}) · {at}"
    return f"원본: {video.origin} · {at}"


def _chapters(chapters: list[Chapter], video: Video, mark: str) -> list[str]:
    # 챕터마다 머리 줄과 요점 — 챕터 사이는 빈 줄
    lines: list[str] = []
    for n, c in enumerate(chapters):
        lines += [""] * (n > 0) + [f"{mark} {link(c.start_sec, video)} {c.title}"]
        lines += [f"- {b}" for b in c.bullets]
    return lines


def _bar(chapter: Chapter, end: float) -> str:
    # gantt 막대 한 줄 — 초 단위로 길이가 0이면 1초로(그리지 않는 막대가 생기지 않게)
    start = int(chapter.start_sec)
    stop = int(end) if int(end) > start else start + 1
    return f"  {_gantt_name(chapter.title, f'챕터 {chapter.seq}')} : {_hms(start)}, {_hms(stop)}"


def _hms(sec: float) -> str:
    # gantt의 dateFormat HH:mm:ss — 늘 두 자리씩
    s = int(sec)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def _gantt_name(text: str, fallback: str) -> str:
    # gantt가 구분자로 읽는 글자를 바꾼다(쌍점은 이름과 시각을 가른다) · 비면 번호로
    name = text.translate(GANTT_CHARS).strip()
    return name or fallback


def _mind_text(text: str) -> str:
    # mindmap이 노드 모양으로 읽는 괄호 셋을 전각으로 · 줄바꿈은 공백
    return text.translate(MIND_CHARS).strip()


def _source(t: Transcript) -> str:
    # 스크립트 출처 — 화면 8.1과 같은 문구
    lang = LANGUAGES.get(t.language, t.language)
    if t.source == TranscriptSource.caption_manual:
        return f"자막(수동) · {lang}"
    if t.source == TranscriptSource.caption_auto:
        return f"자막(자동) · {lang}"
    return f"받아쓰기 {t.model or ''} · {lang}"

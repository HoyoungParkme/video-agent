"""AudioSourcePort 구현 — YouTube 자막을 받아 줄 목록으로(VA-MS-006 audio_source). B1은 자막만.

고르는 규칙은 등록(youtube_info)과 같은 captions.pick 하나다 — 등록 때 알린 자막을 받는다.
"""

from __future__ import annotations

import html
import re

from app.domains.analysis.schemas import CaptionLine
from app.domains.video.models import CaptionKind
from app.infra import ytdlp
from app.shared import captions as picker

# 00:01:02.345 또는 01:02.345(시가 없는 표기도 WebVTT에 맞다)
_TIME = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})")
# <c> · </c> · <00:00:01.000> 같은 태그
_TAG = re.compile(r"<[^>]*>")


def _sec(text: str) -> float | None:
    m = _TIME.fullmatch(text.strip())
    if m is None:
        return None
    h, mi, s, ms = (int(g) if g else 0 for g in m.groups())
    return h * 3600 + mi * 60 + s + ms / 1000


def _cues(vtt: str) -> list[CaptionLine]:
    # 빈 줄로 나뉜 블록 중 시각 줄(-->)이 있는 것만 — 머리(WEBVTT) · NOTE · STYLE은 건너뛴다.
    # 공백 한 칸짜리 줄은 빈 줄이 아니다 — YouTube 자동 자막은 큐 첫 줄에 그것을 둔다
    out = []
    for block in re.split(r"\n{2,}", vtt.replace("\r\n", "\n").replace("\r", "\n")):
        lines = block.split("\n")
        at = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if at is None:
            continue
        left, _, right = lines[at].partition("-->")
        start, end = _sec(left), _sec(right.split()[0] if right.split() else "")
        if start is None or end is None:
            continue
        texts = [html.unescape(_TAG.sub("", line)).strip() for line in lines[at + 1 :]]
        out.append(CaptionLine(start, end, "\n".join(t for t in texts if t)))
    return out


def _unroll(cues: list[CaptionLine]) -> list[CaptionLine]:
    # 자동 자막은 앞 큐의 줄을 다음 큐 첫 줄로 되풀이한다 — 겹친 앞부분을 떼고, 비면 빼고,
    # 같은 텍스트가 잇달아 오면 하나로(끝 시각은 뒤 것)
    out: list[CaptionLine] = []
    for cue in cues:
        text = cue.text
        if out and text == out[-1].text:
            out[-1] = CaptionLine(out[-1].start_sec, cue.end_sec, text)
            continue
        if out and text.startswith(out[-1].text):
            text = text[len(out[-1].text) :].strip()
        if text:
            out.append(CaptionLine(cue.start_sec, cue.end_sec, text))
    return out


class AudioSourceAdapter:
    """YouTube 자막(B1). 음성 내려받기 · 추출은 B2."""

    async def captions(self, video_id: str) -> tuple[list[CaptionLine], str, CaptionKind] | None:
        """VA-MS-006#audio_source.captions

        자막 하나를 VTT로 받아 줄 목록으로 바꾼다. 태그를 떼고, 자동 자막이면 굴러가는 중복을
        없앤다. 한 큐 안의 여러 줄은 한 줄로 잇는다.

        Args:
            video_id: YouTube 영상 ID

        Returns:
            (줄 목록, 언어, 종류). 고를 자막이 없으면 None — 파이프라인이 실패로 접는다

        Raises:
            YtdlpError: 정보 · 자막을 받지 못했다 — 파이프라인이 youtube로 접는다
        """
        raw = await ytdlp.info(ytdlp.WATCH.format(video_id))
        picked = picker.pick(raw)
        if picked is None:
            return None
        key, lang, kind = picked
        cues = [c for c in _cues(await ytdlp.captions(video_id, key, kind)) if c.text]
        if kind == CaptionKind.auto:
            cues = _unroll(cues)
        lines = [CaptionLine(c.start_sec, c.end_sec, " ".join(c.text.split("\n"))) for c in cues]
        return lines, lang, CaptionKind(kind)

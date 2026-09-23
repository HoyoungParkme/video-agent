"""SummarizerPort 구현 — OpenAI 채팅으로 요약 · 챕터 · 추천 질문(VA-MS-006 summarizer_openai).

지시는 system(프롬프트 파일), 스크립트는 user 메시지의 `<transcript>` 안에 — 섞지 않는다.
출력은 JSON 모드. 형식이 틀리면 `config.LLM_RETRY`만큼 다시 부르고, 그래도 틀리면
OpenAIOutputError. 키는 부를 때마다 client_for로 받는다 — 어댑터는 키 문자열을 보지 않는다.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, TypeVar

from openai import AsyncOpenAI

from app import prompts
from app.core.config import config
from app.domains.analysis.schemas import ChapterDraft, Segment, SummaryDraft
from app.infra import openai
from app.infra.errors import OpenAIOutputError
from app.shared import timecode

T = TypeVar("T")
# 인사이트 하나에 붙이는 출처 시각 상한
TIMES_MAX = 3
BULLETS_MAX = 3


def _script(segments: list[Segment]) -> tuple[str, float, bool]:
    # 보내는 구간의 끝이 1시간 이상이면 h:mm:ss — 긴 영상의 뒤쪽 구간도 절대 시각으로 읽힌다
    end = segments[-1].end_sec if segments else 0.0
    long = end >= 3600
    lines = "\n".join(f"[{timecode.label(s.start_sec, long)}] {s.text}" for s in segments)
    return f"<transcript>\n{lines}\n</transcript>", end, long


def _fmt(long: bool) -> str:
    return "h:mm:ss" if long else "mm:ss"


def _text(value: Any) -> str:
    # 문자열이 아니면 형식 실패 — 앞뒤 공백은 뗀다
    if not isinstance(value, str):
        raise ValueError("문자열이 아니다")
    return value.strip()


def _list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError("목록이 아니다")
    return value


def _obj(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("객체가 아니다")
    return value


class SummarizerOpenAI:
    """스크립트 → 요약 · 챕터 · 추천 질문."""

    def __init__(self, client_for: Callable[[], AsyncOpenAI]) -> None:
        self.client_for = client_for

    async def _ask(self, model: str, system: str, user: str, parse: Callable[[Any], T]) -> T:
        # 형식 실패(JSON 아님 · 키 없음 · 타입 틀림 · 다듬고 나니 빔)면 다시 부른다
        why = ""
        for _ in range(config.LLM_RETRY + 1):
            raw = await openai.chat(
                self.client_for(),
                model,
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
            )
            try:
                return parse(json.loads(raw))
            except (ValueError, KeyError, TypeError) as e:
                why = str(e) or type(e).__name__
        raise OpenAIOutputError(f"모델 출력을 읽지 못했어요({why})")

    async def summary(self, segments: list[Segment], duration_sec: int, model: str) -> SummaryDraft:
        """VA-MS-006#summarizer_openai.summary

        한 줄 요약과 인사이트(문장 · 출처 시각 1~3개). 개수와 시각 범위 보정은 서비스가 한다.

        Args:
            segments: 보낼 구간들
            duration_sec: 영상 길이 — 인사이트 상한(1시간 넘으면 10, 아니면 8)
            model: 텍스트 모델

        Returns:
            SummaryDraft. 5개보다 적어도 그대로

        Raises:
            OpenAIOutputError: 다시 불러도 형식이 틀렸다
        """
        n = 10 if duration_sec > config.PART_THRESHOLD_SEC else 8
        user, end, long = _script(segments)
        system = prompts.render("summary", insight_max=n, time_format=_fmt(long))

        def parse(data: Any) -> SummaryDraft:
            data = _obj(data)
            one_liner = _text(data["one_liner"])
            if not one_liner:
                raise ValueError("한 줄 요약이 비었다")
            insights = []
            for item in map(_obj, _list(data["insights"])[:n]):
                text = _text(item["text"])
                secs = [timecode.parse(_text(t), end) for t in _list(item["times"])]
                kept = [s for s in secs if s is not None][:TIMES_MAX]
                if text and kept:  # 시각을 하나도 못 읽은 인사이트는 버린다
                    insights.append((text, kept))
            if not insights:
                raise ValueError("인사이트가 없다")
            return SummaryDraft(one_liner=one_liner, insights=insights)

        return await self._ask(model, system, user, parse)

    async def chapters(
        self, segments: list[Segment], duration_sec: int, model: str
    ) -> ChapterDraft:
        """VA-MS-006#summarizer_openai.chapters

        챕터(시작 · 제목 · 요점 2~3줄)와, 60분 넘는 영상이면 파트. 시작 순으로 정렬한다.

        Args:
            segments: 보낼 구간들
            duration_sec: 영상 길이 — 목표 챕터 수(6분에 하나, 적어도 셋)와 파트 수
            model: 텍스트 모델

        Returns:
            ChapterDraft. 60분 이하면 parts가 비고 part_seq가 모두 None

        Raises:
            OpenAIOutputError: 다시 불러도 형식이 틀렸다
        """
        target = max(3, round(duration_sec / 60 / 6))
        with_parts = duration_sec > config.PART_THRESHOLD_SEC
        user, end, long = _script(segments)
        system = prompts.render(
            "chapters",
            chapter_target=target,
            part_count="2~5" if with_parts else "0",
            time_format=_fmt(long),
        )

        def parse(data: Any) -> ChapterDraft:
            data = _obj(data)
            parts: list[tuple[str, float]] = []
            renumber: dict[int, int] = {}  # 응답의 파트 번호 → 읽을 수 있던 파트만 센 번호
            if with_parts:
                for i, p in enumerate(map(_obj, _list(data.get("parts", []))), 1):
                    title, start = _text(p["title"]), timecode.parse(_text(p["start"]), end)
                    if title and start is not None:
                        parts.append((title, start))
                        renumber[i] = len(parts)
            chapters = []
            for c in map(_obj, _list(data["chapters"])):
                start = timecode.parse(_text(c["start"]), end)
                title = _text(c["title"])
                if start is None or not title:  # 시작을 못 읽거나 제목이 없으면 버린다
                    continue
                bullets = [b.strip() for b in _list(c.get("bullets", [])) if isinstance(b, str)]
                part = c.get("part")
                part_seq = renumber.get(part) if isinstance(part, int) else None
                chapters.append((part_seq, start, title, [b for b in bullets if b][:BULLETS_MAX]))
            if not chapters:
                raise ValueError("챕터가 없다")
            chapters.sort(key=lambda c: c[1])
            return ChapterDraft(parts=parts, chapters=chapters)

        return await self._ask(model, system, user, parse)

    async def questions(self, segments: list[Segment], model: str) -> list[str]:
        """VA-MS-006#summarizer_openai.questions

        이 스크립트만으로 답할 수 있는 질문 `config.QUESTION_COUNT`개. 물음표로 끝나게 한다.

        Args:
            segments: 보낼 구간들
            model: 텍스트 모델

        Returns:
            질문들 — 빈 문장과 중복을 뺀 앞 QUESTION_COUNT개

        Raises:
            OpenAIOutputError: 다시 불러도 형식이 틀렸다
        """
        user, _, _ = _script(segments)
        system = prompts.render("questions", question_count=config.QUESTION_COUNT)

        def parse(data: Any) -> list[str]:
            out: list[str] = []
            for q in _list(_obj(data)["questions"]):
                q = _text(q)
                if q and not q.endswith(("?", "？")):
                    q += "?"
                if q and q not in out:
                    out.append(q)
            if not out:
                raise ValueError("질문이 없다")
            return out[: config.QUESTION_COUNT]

        return await self._ask(model, system, user, parse)

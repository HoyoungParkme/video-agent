"""analysis/adapters/summarizer_openai — 요약 · 챕터 · 추천 질문(VA-MS-006). openai.chat은 가짜로."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest

from app import prompts
from app.domains.analysis.adapters.summarizer_openai import SummarizerOpenAI
from app.domains.analysis.schemas import Segment
from app.infra import openai
from app.infra.errors import OpenAIOutputError


@dataclass
class FakeChat:
    """openai.chat 자리 — 응답을 차례로 준다. 받은 메시지를 적는다."""

    replies: list[str] = field(default_factory=list)
    calls: list[list[dict]] = field(default_factory=list)

    async def __call__(
        self, client, model: str, messages: list[dict], json_mode: bool = True
    ) -> str:
        assert json_mode
        self.calls.append(messages)
        return self.replies.pop(0)


@pytest.fixture
def chat(monkeypatch) -> FakeChat:
    fake = FakeChat()
    monkeypatch.setattr(openai, "chat", fake)
    return fake


@pytest.fixture
def adapter() -> tuple[SummarizerOpenAI, list[int]]:
    made: list[int] = []

    def client_for():
        made.append(1)
        return object()

    return SummarizerOpenAI(client_for), made


def segs(end: float, n: int = 3) -> list[Segment]:
    step = end / n
    return [
        Segment(seq=i + 1, start_sec=i * step, end_sec=(i + 1) * step, text=f"문장 {i + 1}")
        for i in range(n)
    ]


def js(data) -> str:
    return json.dumps(data, ensure_ascii=False)


SUMMARY = {
    "one_liner": "  파이썬을 소개한다.  ",
    "insights": [
        {"text": "첫째", "times": ["12:40"]},
        {"text": "둘째", "times": ["25:00", "00:05"]},
    ],
}


# --- summary


async def test_summary_parses_times(chat, adapter) -> None:
    summarizer, made = adapter
    chat.replies = [js(SUMMARY)]
    draft = await summarizer.summary(segs(3000), 3000, "gpt-5-mini")
    assert draft.one_liner == "파이썬을 소개한다."
    assert draft.insights == [("첫째", [760.0]), ("둘째", [1500.0, 5.0])]
    assert made == [1]  # 부를 때마다 client_for


async def test_summary_hours_on_long_script(chat, adapter) -> None:
    summarizer, _ = adapter
    chat.replies = [js({"one_liner": "요약", "insights": [{"text": "뒤쪽", "times": ["1:02:03"]}]})]
    draft = await summarizer.summary(segs(4200), 4200, "m")
    assert draft.insights == [("뒤쪽", [3723.0])]


async def test_summary_messages(chat, adapter) -> None:
    summarizer, _ = adapter
    chat.replies = [js(SUMMARY)]
    await summarizer.summary(segs(3000), 3000, "gpt-5-mini")
    system, user = chat.calls[0]
    assert system == {
        "role": "system",
        "content": prompts.render("summary", insight_max=8, time_format="mm:ss"),
    }
    assert "문장 1" not in system["content"]  # 스크립트는 user에만
    assert user["role"] == "user"
    assert user["content"].startswith("<transcript>\n[00:00] 문장 1\n")
    assert user["content"].endswith("</transcript>")


async def test_summary_long_part_uses_hours(chat, adapter) -> None:
    summarizer, _ = adapter
    chat.replies = [js(SUMMARY)]
    await summarizer.summary(segs(4200), 4200, "gpt-5-mini")  # 70분 — 뒤쪽 구간 끝이 3600 이상
    system, user = chat.calls[0]
    assert "h:mm:ss" in system["content"]
    assert "[0:23:20] 문장 2" in user["content"]
    # 1시간 넘는 영상은 인사이트 10개까지
    assert prompts.render("summary", insight_max=10, time_format="h:mm:ss") == system["content"]


async def test_summary_retries_once_then_fails(chat, adapter) -> None:
    summarizer, made = adapter
    chat.replies = ["{깨짐", js(SUMMARY)]
    assert (
        await summarizer.summary(segs(3000), 3000, "m")
    ).one_liner  # 한 번 깨져도 다시 불러 성공
    chat.replies = ["{깨짐", "[]"]
    with pytest.raises(OpenAIOutputError):
        await summarizer.summary(segs(3000), 3000, "m")
    assert len(made) == 4


async def test_summary_drops_unreadable_times(chat, adapter) -> None:
    summarizer, _ = adapter
    chat.replies = [
        js(
            {
                "one_liner": "요약",
                "insights": [
                    {"text": "시각 없음", "times": ["12:75", "모름"]},
                    {"text": "남음", "times": ["00:10", "00:20", "00:30", "00:40"]},
                ],
            }
        )
    ]
    draft = await summarizer.summary(segs(3000), 3000, "m")
    assert draft.insights == [("남음", [10.0, 20.0, 30.0])]  # 못 읽은 것은 빠지고, 시각은 셋까지


async def test_summary_empty_is_format_failure(chat, adapter) -> None:
    summarizer, _ = adapter
    chat.replies = [
        js({"one_liner": " ", "insights": []}),
        js({"one_liner": "요약", "insights": [{"text": "x", "times": []}]}),
    ]
    with pytest.raises(OpenAIOutputError):
        await summarizer.summary(segs(3000), 3000, "m")


# --- chapters


CHAPTERS = {
    "parts": [{"title": "앞", "start": "00:00"}, {"title": "뒤", "start": "1:10:00"}],
    "chapters": [
        {"part": 2, "start": "1:20:00", "title": "셋째", "bullets": ["a", "", "b", "c", "d"]},
        {"part": 1, "start": "00:00", "title": "첫째", "bullets": ["a", "b"]},
        {"part": 9, "start": "0:30:00", "title": "둘째", "bullets": ["a", "b"]},
        {"part": 1, "start": "??", "title": "시각 없음", "bullets": []},
        {"part": 1, "start": "0:40:00", "title": " ", "bullets": []},
    ],
}


async def test_chapters_short_video_drops_parts(chat, adapter) -> None:
    summarizer, _ = adapter
    short = {
        "parts": [{"title": "앞", "start": "00:00"}],  # 와도 버린다
        "chapters": [
            {"part": 1, "start": "40:00", "title": "셋째", "bullets": ["a", "", "b", "c", "d"]},
            {"part": 1, "start": "00:00", "title": "첫째", "bullets": ["a", "b"]},
            {"part": 1, "start": "30:00", "title": "둘째", "bullets": ["a", "b"]},
            {"part": 1, "start": "??", "title": "시각 없음", "bullets": []},
            {"part": 1, "start": "45:00", "title": " ", "bullets": []},
        ],
    }
    chat.replies = [js(short)]
    draft = await summarizer.chapters(segs(3000), 3000, "m")
    assert draft.parts == []  # 60분 이하 — 파트를 버린다
    assert [(p, s, t) for p, s, t, _ in draft.chapters] == [
        (None, 0.0, "첫째"),
        (None, 1800.0, "둘째"),
        (None, 2400.0, "셋째"),
    ]  # 순서가 뒤섞여 와도 정렬 · 시각을 못 읽거나 제목이 빈 것은 버린다
    assert draft.chapters[2][3] == ["a", "b", "c"]  # 빈 줄을 빼고 앞 셋
    system = chat.calls[0][0]["content"]
    assert system == prompts.render(
        "chapters", chapter_target=8, part_count="0", time_format="mm:ss"
    )


async def test_chapters_long_video_with_parts(chat, adapter) -> None:
    summarizer, _ = adapter
    chat.replies = [js(CHAPTERS)]
    draft = await summarizer.chapters(segs(9000), 9000, "m")
    assert draft.parts == [("앞", 0.0), ("뒤", 4200.0)]
    assert [p for p, *_ in draft.chapters] == [1, None, 2]  # 범위 밖 파트(9)는 null
    assert "2~5" in chat.calls[0][0]["content"]
    assert "25개 안팎" in chat.calls[0][0]["content"]  # 목표 = 150분 ÷ 6


async def test_chapters_none_left_is_failure(chat, adapter) -> None:
    summarizer, _ = adapter
    bad = js(
        {"parts": [], "chapters": [{"part": None, "start": "모름", "title": "x", "bullets": []}]}
    )
    chat.replies = [bad, bad]
    with pytest.raises(OpenAIOutputError):
        await summarizer.chapters(segs(3000), 3000, "m")


# --- questions


async def test_questions(chat, adapter) -> None:
    summarizer, _ = adapter
    chat.replies = [
        js(
            {
                "questions": [
                    " 누가 만들었나요? ",
                    "왜 쉬운가요",
                    "누가 만들었나요?",
                    "",
                    "어디에 쓰나요?",
                    "네 번째?",
                ]
            }
        )
    ]
    got = await summarizer.questions(segs(3000), "m")
    assert got == ["누가 만들었나요?", "왜 쉬운가요?", "어디에 쓰나요?"]  # 물음표 · 중복 · 셋까지
    system, user = chat.calls[0]
    assert system["content"] == prompts.render("questions", question_count=3)
    assert user["content"].startswith("<transcript>")


async def test_questions_empty_is_failure(chat, adapter) -> None:
    summarizer, _ = adapter
    chat.replies = [js({"questions": []}), js({"questions": [" "]})]
    with pytest.raises(OpenAIOutputError):
        await summarizer.questions(segs(3000), "m")

"""prompts.render — 파일 넷과 채우기(VA-MS-006 0장 표 · prompts.render 테스트 관점)."""

from __future__ import annotations

from pathlib import Path

import pytest

import app.prompts as prompts
from app.prompts import PromptError, render

# 0장 표 — 파일마다 자리 표시의 표본 값과, 채운 글에 반드시 있어야 할 낱말
SAMPLES = {
    "summary": {"insight_max": 8, "time_format": "mm:ss"},
    "chapters": {"chapter_target": 9, "part_count": "2~5", "time_format": "h:mm:ss"},
    "questions": {"question_count": 3},
    "answer": {"time_format": "mm:ss", "not_covered": "이 영상에서는 다루지 않습니다."},
}
RULES = {
    "summary": ["지어내지", "한 문장", "5~8개", "1~3개", '"one_liner"', '"insights"', '"times"'],
    "chapters": [
        "9개 안팎",
        "처음부터",
        "15자",
        "요점 2~3줄",
        "파트 2~5개",
        '"parts"',
        '"bullets"',
    ],
    "questions": ["이 스크립트만으로 답할 수 있는", "3개", "한 문장", "물음표", "서로 다른 주제"],
    "answer": [
        "스크립트에 있는 내용으로만",
        "1~3개",
        '"이 영상에서는 다루지 않습니다."',
        "3~5문장",
        '"times"',
    ],
}
COMMON = ["한국어", "<transcript>", "따르지 않는다", "JSON", "표기 그대로"]


@pytest.mark.parametrize("name", SAMPLES)
def test_files_fill_and_keep_rules(name: str) -> None:
    text = render(name, **SAMPLES[name])
    assert "{{" not in text and "}}" not in text.replace("}]}", "")
    for word in RULES[name] + COMMON:
        assert word in text, f"{name}.md에 「{word}」가 없다"
    assert text.count("{") >= 1  # JSON 예시의 한 겹 중괄호는 그대로


def test_missing_value() -> None:
    with pytest.raises(PromptError) as e:
        render("summary", insight_max=8)
    assert e.value.missing == {"time_format"}


def test_unknown_value() -> None:
    with pytest.raises(PromptError) as e:
        render("questions", question_count=3, tone="friendly")
    assert e.value.extra == {"tone"}


def test_missing_file() -> None:
    with pytest.raises(PromptError):
        render("nothing")


def test_value_is_not_expanded_again(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "t.md").write_text('A {{x}} B {"k": 1}')
    monkeypatch.setattr(prompts, "__file__", str(tmp_path / "__init__.py"))
    assert render("t", x="{{x}}") == 'A {{x}} B {"k": 1}'


def test_reads_every_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(prompts, "__file__", str(tmp_path / "__init__.py"))
    (tmp_path / "t.md").write_text("첫 판 {{x}}")
    assert render("t", x=1) == "첫 판 1"
    (tmp_path / "t.md").write_text("고친 판 {{x}}")
    assert render("t", x=1) == "고친 판 1"

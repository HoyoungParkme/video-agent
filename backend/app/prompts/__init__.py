"""모델에 보내는 지시문 — 이 폴더의 마크다운 넷을 읽어 `{{이름}}`을 채운다(VA-MS-006 0장).

OpenAI 어댑터(analysis · chat)만 부른다. 문장은 파일에서 고치고, 명세는 자리 표시 · 반드시
들어갈 규칙 · 출력 형식만 정한다.
"""

from __future__ import annotations

import re
from pathlib import Path

HOLE = re.compile(r"\{\{([a-z_]+)\}\}")


class PromptError(Exception):
    """프롬프트 파일이 없거나 자리 표시와 값이 어긋났다 — 코드 실수다."""

    def __init__(self, name: str, missing: set[str], extra: set[str]) -> None:
        super().__init__(f"{name}.md — 빠진 값 {sorted(missing)}, 남는 값 {sorted(extra)}")
        self.name = name
        self.missing = missing
        self.extra = extra


def render(name: str, **values: str | int) -> str:
    """VA-MS-006#prompts.render

    프롬프트 파일을 읽어 자리 표시를 채운다. 부를 때마다 읽는다 — 고친 글이 다음 호출에 바로 쓰인다.
    한 번만 바꾸므로 값 안의 `{{…}}`는 그대로이고, JSON 예시의 한 겹 중괄호도 그대로다.

    Args:
        name: 파일 이름(확장자 없이) — summary · chapters · questions · answer
        values: 자리 표시 이름과 값. 파일의 자리 표시와 정확히 같아야 한다

    Returns:
        system 메시지 문자열

    Raises:
        PromptError: 파일이 없거나, 값이 빠졌거나 남는다
    """
    path = Path(__file__).parent / f"{name}.md"
    if not path.is_file():
        raise PromptError(name, set(values), set())
    text = path.read_text(encoding="utf-8")
    names = set(HOLE.findall(text))
    if names != set(values):
        raise PromptError(name, names - set(values), set(values) - names)
    return HOLE.sub(lambda m: str(values[m.group(1)]), text)

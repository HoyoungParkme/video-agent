"""analysis/adapters/image_openai — VA-MS-006 image_openai.infographic의 테스트 관점. infra는 가짜로."""

from __future__ import annotations

import struct
from pathlib import Path

import httpx2
import openai as sdk
import pytest

from app.core.config import ImageQuality, config
from app.core.errors import LlmUnavailable
from app.domains.analysis.adapters.image_openai import ImageOpenAI
from app.domains.analysis.schemas import ImageShot, InfographicBrief
from app.infra import openai
from app.infra.errors import OpenAIOutputError

BRIEF = InfographicBrief(
    title="RAG 서비스 1년 운영기",
    one_liner="검색 품질을 올린 1년의 기록이다.",
    insights=["청킹을 256 토큰으로 줄였다", "pgvector로 옮겼다"],
    chapter_titles=["발표자 소개", "청킹 다시 보기", "운영과 리뷰"],
)
REQ = httpx2.Request("POST", "http://fake/v1/images/generations")


def png(width: int = 1024, height: int = 1536) -> bytes:
    """PNG 머리(시그니처 + IHDR)까지 — 크기 읽기는 앞 24바이트만 본다."""
    return (
        b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height)
    )


@pytest.fixture
def image(monkeypatch) -> dict:
    """openai.image 자리 — 받은 인자를 적고, 정한 결과(바이트 또는 예외)를 낸다."""
    state: dict = {"calls": [], "result": png()}

    async def fake(client, model: str, prompt: str, size: str, quality: str) -> bytes:
        state["calls"].append((client, model, prompt, size, quality))
        if isinstance(state["result"], Exception):
            raise state["result"]
        return state["result"]

    monkeypatch.setattr(openai, "image", fake)
    return state


def adapter() -> tuple[ImageOpenAI, list[int]]:
    made: list[int] = []

    def client_for() -> object:
        made.append(1)
        return object()

    return ImageOpenAI(client_for), made


async def test_writes_png_and_reads_size(image, tmp_path: Path) -> None:
    dest = tmp_path / "12.png.part"
    shot = await adapter()[0].infographic(BRIEF, "gpt-image-2", ImageQuality.low, str(dest))
    assert shot == ImageShot(1024, 1536, str(dest))
    assert dest.read_bytes() == png()


async def test_prompt_has_brief_only(image, tmp_path: Path) -> None:
    svc, made = adapter()
    await svc.infographic(BRIEF, "gpt-image-2", ImageQuality.medium, str(tmp_path / "a"))
    await svc.infographic(BRIEF, "gpt-image-2", ImageQuality.medium, str(tmp_path / "b"))
    assert len(made) == 2  # 부를 때마다 client_for
    _, model, prompt, size, quality = image["calls"][0]
    assert (model, size, quality) == ("gpt-image-2", config.INFOGRAPHIC_SIZE, "medium")
    assert "<content>" in prompt and "인사이트 2개" in prompt and "챕터 제목 3개" in prompt
    for text in [BRIEF.title, BRIEF.one_liner, *BRIEF.insights, *BRIEF.chapter_titles]:
        assert text in prompt
    assert "[00:" not in prompt  # 스크립트 줄은 없다


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (
            sdk.APIStatusError("error", response=httpx2.Response(503, request=REQ), body=None),
            "OpenAI 서버 오류",
        ),
        (
            sdk.APIStatusError(
                "error",
                response=httpx2.Response(400, request=REQ),
                body={"code": "moderation_blocked", "message": "blocked"},
            ),
            "안전 정책에 걸려 그리지 않음",
        ),
        (OpenAIOutputError("그림을 받지 못했어요"), "그림을 받지 못했어요"),
        (b"not a png", "그림을 읽지 못했어요"),
    ],
)
async def test_failures_become_llm_unavailable(image, tmp_path: Path, error, reason) -> None:
    image["result"] = error
    dest = tmp_path / "12.png.part"
    with pytest.raises(LlmUnavailable) as e:
        await adapter()[0].infographic(BRIEF, "gpt-image-2", ImageQuality.low, str(dest))
    assert e.value.extra == {"reason": reason}
    assert not dest.exists()

"""ImageMakerPort 구현 — OpenAI 이미지 모델로 인포그래픽 한 장(VA-MS-006 image_openai, INFRA C11).

재료는 제목 · 한 줄 요약 · 인사이트 · 챕터 제목뿐이다 — 스크립트는 보내지 않는다(UC-H9 4번, PRD N3).
지시는 prompts/infographic.md, 재료는 그 뒤 `<content>` 안이다. 호출 실패는 LlmUnavailable(이유
한 줄)로 바꿔 올린다 — 서비스가 SDK를 모르게. 키는 부를 때마다 client_for로 받는다.
"""

from __future__ import annotations

import asyncio
import struct
from collections.abc import Callable
from pathlib import Path

from openai import AsyncOpenAI, OpenAIError

from app import prompts
from app.core.config import ImageQuality, config
from app.core.errors import LlmUnavailable
from app.domains.analysis.schemas import ImageShot, InfographicBrief
from app.infra import openai
from app.infra.errors import OpenAIOutputError

PNG_HEAD = b"\x89PNG\r\n\x1a\n"


def _png_size(png: bytes) -> tuple[int, int]:
    """PNG 머리(IHDR — 파일 앞 24바이트)의 폭 · 높이. 그림 라이브러리를 더하지 않는다."""
    if png[:8] != PNG_HEAD or png[12:16] != b"IHDR":
        raise OpenAIOutputError("그림을 읽지 못했어요")
    width, height = struct.unpack(">II", png[16:24])
    return width, height


def _content(brief: InfographicBrief) -> str:
    insights = "\n".join(f"{i}. {text}" for i, text in enumerate(brief.insights, start=1))
    chapters = "\n".join(f"{i}. {title}" for i, title in enumerate(brief.chapter_titles, start=1))
    return (
        f"<content>\n제목: {brief.title}\n한 줄 요약: {brief.one_liner}\n"
        f"인사이트:\n{insights}\n챕터:\n{chapters}\n</content>"
    )


class ImageOpenAI:
    """요약 재료 → 세로 인포그래픽 한 장."""

    def __init__(self, client_for: Callable[[], AsyncOpenAI]) -> None:
        self.client_for = client_for

    async def infographic(
        self, brief: InfographicBrief, model: str, quality: ImageQuality, dest: str
    ) -> ImageShot:
        """VA-MS-006#image_openai.infographic

        재료로 프롬프트를 만들어 한 장 그리고 PNG를 dest에 쓴다. 크기는 PNG 머리에서 읽는다.

        Args:
            brief: 제목 · 한 줄 요약 · 인사이트 · 챕터 제목
            model: 이미지 모델
            quality: low · medium
            dest: 쓸 파일 경로

        Returns:
            크기와 쓴 파일 경로

        Raises:
            LlmUnavailable: OpenAI 호출 실패 · 그림이 없거나 읽을 수 없다(이유 한 줄)
            OSError: 파일을 쓰지 못했다
        """
        prompt = prompts.render(
            "infographic",
            insight_count=len(brief.insights),
            chapter_count=len(brief.chapter_titles),
        )
        try:
            png = await openai.image(
                self.client_for(),
                model,
                f"{prompt}\n\n{_content(brief)}",
                size=config.INFOGRAPHIC_SIZE,
                quality=str(quality),
            )
            width, height = _png_size(png)
        except (OpenAIError, OpenAIOutputError) as e:
            raise LlmUnavailable(reason=openai.reason_of(e)) from e
        await asyncio.to_thread(Path(dest).write_bytes, png)
        return ImageShot(width, height, dest)

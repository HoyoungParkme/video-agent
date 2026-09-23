"""SttPort 구현 — OpenAI 받아쓰기로 조각 하나를 구간들로(VA-MS-006 stt_openai).

키는 부를 때마다 client_for로 받는다. 예외는 그대로 올린다 — 재시도 · 분류 · 이유 한 줄은
파이프라인의 몫이다(VA-MS-002 transcribe_stage · error_kind · reason_of).
"""

from __future__ import annotations

from collections.abc import Callable

from openai import AsyncOpenAI

from app.domains.job.schemas import SttSegment
from app.infra import openai

# whisper-1이 주는 언어 이름 → ISO 639-1. 자주 나오는 것만 — 표에 없으면 받은 값 그대로(MS-006 미결)
LANGS = {
    "korean": "ko",
    "english": "en",
    "japanese": "ja",
    "chinese": "zh",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "russian": "ru",
    "vietnamese": "vi",
    "thai": "th",
    "indonesian": "id",
    "hindi": "hi",
    "arabic": "ar",
    "turkish": "tr",
    "dutch": "nl",
    "polish": "pl",
    "swedish": "sv",
    "ukrainian": "uk",
}


class SttOpenAI:
    """조각 파일 → 받아쓰기 구간들."""

    def __init__(self, client_for: Callable[[], AsyncOpenAI]) -> None:
        self.client_for = client_for

    async def transcribe(self, path: str, model: str) -> list[SttSegment]:
        """VA-MS-006#stt_openai.transcribe

        verbose_json · 구간 시각으로 받아쓴다. 언어는 지정하지 않는다(자동 감지). 빈 구간은 뺀다.

        Args:
            path: 조각 파일(25MB 이하)
            model: 받아쓰기 모델

        Returns:
            구간들 — 시각은 조각 안 상대 시각. 오프셋은 파이프라인이 더한다
        """
        raw = await openai.transcribe(self.client_for(), path, model)
        name = str(raw.get("language") or "").strip().lower()
        lang = LANGS.get(name, name)
        return [
            SttSegment(float(s["start"]), float(s["end"]), text, lang)
            for s in raw.get("segments") or []
            if (text := str(s.get("text") or "").strip())
        ]

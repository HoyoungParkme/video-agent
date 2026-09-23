"""설정값 전부 — MS 문서들의 「설정값(첫 값)」 표. 모든 모듈이 `config.X`로 읽는다.

환경 변수로 바꿀 수 있다(같은 이름). 키와 고른 모델은 여기 없다 — 돌면서 바뀌므로
SettingsService가 `.env` 파일에서 읽는다(VA-MS-005 0장).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, model_serializer
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelPrice(BaseModel):
    """단가(USD). 받아쓰기는 분당, 텍스트는 100만 토큰당 입력 · 출력.

    해당 없는 칸은 응답에서 뺀다(VA-API-001 4장 ModelPrice).
    """

    per_min_usd: float | None = None
    input_per_mtok_usd: float | None = None
    output_per_mtok_usd: float | None = None

    @model_serializer(mode="wrap")
    def _omit_none(self, handler: Any) -> dict[str, float]:
        return {k: v for k, v in handler(self).items() if v is not None}


class ModelOption(BaseModel):
    """고를 수 있는 모델 하나."""

    id: str
    label: str
    price: ModelPrice


class ModelOptions(BaseModel):
    """받아쓰기 목록(구간 시각을 주는 모델만, INFRA C3)과 텍스트 목록."""

    stt: list[ModelOption]
    text: list[ModelOption]


def _text(model: str, input_usd: float, output_usd: float) -> ModelOption:
    return ModelOption(
        id=model,
        label=model,
        price=ModelPrice(input_per_mtok_usd=input_usd, output_per_mtok_usd=output_usd),
    )


class Config(BaseSettings):
    """설정값. 이름 옆 주석이 출처 문서."""

    model_config = SettingsConfigDict(extra="ignore")

    # 접속 · 경로 — 기본값은 컨테이너 안(compose). 호스트 개발은 AGENTS.md의 환경 변수로
    DATABASE_URL: str = "postgresql+asyncpg://va:va@127.0.0.1:5433/va"
    ENV_PATH: str = "/app/.env"  # MS-005
    INBOX_DIR: str = "/app/inbox"  # MS-001 — 컨테이너 안 마운트 경로
    INBOX_DISPLAY_PATH: str = "inbox"  # MS-001 — 사용자에게 보일 호스트 경로. compose가 채운다
    DATA_DIR: str = "/app/data"  # MS-001 — tmp/{video_id}/ · export/

    # 영상 — MS-001
    MAX_DURATION_SEC: int = 10800
    PROBE_CONCURRENCY: int = 4

    # 작업 · 파이프라인 — MS-002
    CHUNK_SEC: int = 600
    STT_CONCURRENCY: int = 3
    CHUNK_MAX_ATTEMPTS: int = 3
    CHUNK_EST_SEC: int = 45
    TEXT_EST_SEC: int = 60
    TOKENS_PER_MIN: int = 200
    WORKER_IDLE_SEC: float = 5

    # 결과 — MS-003
    TEXT_WINDOW_SEC: int = 1800
    TEXT_TOKEN_LIMIT: int = 40000
    CHAPTER_MINUTES: int = 6
    PART_THRESHOLD_SEC: int = 3600

    # 대화 — MS-004
    CHAT_HISTORY_TURNS: int = 10
    CHAT_TOKEN_LIMIT: int = 30000
    CHAT_CHAPTERS: int = 3
    CHAT_TIMEOUT_SEC: float = 20

    # 설정 — MS-005. 단가는 2026-09-23 OpenAI 가격표(표준 요금)
    MODEL_OPTIONS: ModelOptions = ModelOptions(
        stt=[ModelOption(id="whisper-1", label="whisper-1", price=ModelPrice(per_min_usd=0.006))],
        text=[
            _text("gpt-5-mini", 0.25, 2.00),
            _text("gpt-5.4-mini", 0.75, 4.50),
            _text("gpt-5.4", 2.50, 15.00),
        ],
    )
    DEFAULT_MODELS: dict[str, str] = {"stt": "whisper-1", "text": "gpt-5-mini"}
    KEY_CHECK_TIMEOUT_SEC: float = 10

    # 어댑터 — MS-006
    CAPTION_LANGS: list[str] = ["ko", "en"]
    AUDIO_FORMAT: list[str] = ["-ac", "1", "-ar", "16000", "-b:a", "64k", "-codec:a", "libmp3lame"]
    SPLIT_WINDOW_SEC: float = 30
    SILENCE_DB: float = -35
    SILENCE_MIN_SEC: float = 0.5
    CHUNK_MAX_BYTES: int = 24_000_000
    LLM_RETRY: int = 1
    NOT_COVERED_TEXT: str = "이 영상에서는 다루지 않습니다."
    QUESTION_COUNT: int = 3

    # infra — MS-007
    PROC_TIMEOUT_SEC: float = 1800
    YTDLP_BIN: str = "yt-dlp"
    FFMPEG_BIN: str = "ffmpeg"
    FFPROBE_BIN: str = "ffprobe"
    OPENAI_TIMEOUT_SEC: float = 120
    OPENAI_BASE_URL: str | None = None  # E2E의 가짜 OpenAI 서버만 채운다
    OPENAI_MAX_RETRIES: int = 0

    @property
    def EXPORT_DIR(self) -> str:
        """내보낸 마크다운을 쓰는 곳 — data 폴더 안 export/(MS-003)."""
        return f"{self.DATA_DIR}/export"


config = Config()

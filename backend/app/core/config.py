"""설정값 전부 — MS 문서들의 「설정값(첫 값)」 표. 모든 모듈이 `config.X`로 읽는다.

환경 변수로 바꿀 수 있다(같은 이름). 키와 고른 모델은 여기 없다 — 돌면서 바뀌므로
SettingsService가 `.env` 파일에서 읽는다(VA-MS-005 0장).
"""

from __future__ import annotations

from enum import StrEnum
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


class ImageQuality(StrEnum):
    """인포그래픽 품질 — `.env`의 IMAGE_QUALITY(VA-DOM-002 2장 열거형)."""

    low = "low"
    medium = "medium"


class ImageQualityOption(BaseModel):
    """고를 수 있는 품질 하나와 한 장 값(VA-API-001 4장). UI-4 · UI-5 · UI-8이 같은 값을 쓴다."""

    id: ImageQuality
    label: str
    price_usd: float


class ImageOptions(BaseModel):
    """인포그래픽 이미지 모델 목록과 품질 목록."""

    models: list[str]
    qualities: list[ImageQualityOption]


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
    # 받는 Host — DNS 리바인딩을 막는다(INFRA 5절). api는 compose 안에서 web이 `api`로 부른다
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1", "api"]

    # 영상 — MS-001
    MAX_DURATION_SEC: int = 10800
    PROBE_CONCURRENCY: int = 4
    # 받는 확장자(ACCEPTED) — 영상 등록 · inbox 목록 · 파일 재기 · 단계 목록이 같이 쓴다
    VIDEO_EXTS: list[str] = ["mp4", "mkv", "mov", "webm"]
    AUDIO_EXTS: list[str] = ["mp3", "m4a", "wav"]

    # 작업 · 파이프라인 — MS-002
    CHUNK_SEC: int = 600
    STT_CONCURRENCY: int = 3
    CHUNK_MAX_ATTEMPTS: int = 3
    CHUNK_RETRY_WAIT_SEC: float = 2  # 다시 보내기 전 첫 기다림, 다음은 두 배
    CHUNK_EST_SEC: int = 45
    # 요약 세 단계 합 — 추론 강도 low 실측 21~22초. 장면 몫과 합쳐 자막 있음이 '약 1분'(카드 D2)
    TEXT_EST_SEC: int = 45
    # 장면 단계 전체의 예상 · 그 단계 안에서 남은 한 장의 예상 — 실측 YouTube 5~13초(칸마다 약 1초),
    # 로컬 27장 12초(카드 D2)
    FRAMES_EST_SEC: int = 15
    FRAME_EST_SEC: int = 1
    # 스크립트를 한 번 보낼 때 영상 1분당 입력 토큰 — 실측 323~497(줄 앞 시각 표기까지, 카드 C)
    TOKENS_PER_MIN: int = 450
    WORKER_IDLE_SEC: float = 5

    # 결과 — MS-003
    TEXT_WINDOW_SEC: int = 1800
    # 3시간 안은 대부분 한 번에 — 받아쓰기 스크립트는 영상 1분에 약 500토큰(카드 C 실측)
    TEXT_TOKEN_LIMIT: int = 100000
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
    # 인포그래픽(INFRA C11) — 한 장 값은 1024×1024 기준 첫 값이다. 카드 D3에서 실제 한 장으로 고친다
    IMAGE_OPTIONS: ImageOptions = ImageOptions(
        models=["gpt-image-2"],
        qualities=[
            ImageQualityOption(id=ImageQuality.low, label="낮음", price_usd=0.006),
            ImageQualityOption(id=ImageQuality.medium, label="중간", price_usd=0.05),
        ],
    )
    # 파일에 선택이 없을 때 — 사용자 결정 2026-09-29(「좀 비싸다, 싼 걸로」)
    DEFAULT_IMAGE: dict[str, str] = {"model": "gpt-image-2", "quality": "low"}
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
    # 장면 — 스토리보드 가운데 가장 큰 칸(1080p 영상 320×180) · 로컬 프레임 폭(높이는 비율대로)
    STORYBOARD_FORMAT: str = "sb0"
    FRAME_WIDTH: int = 640

    # infra — MS-007
    PROC_TIMEOUT_SEC: float = 1800
    # 장면 한 장(로컬 프레임 · 스토리보드 장 받아 칸 자르기) 상한 — 한 장 1~2초라 넉넉하다(MS-007)
    FRAME_TIMEOUT_SEC: float = 30
    # 등록 때 yt-dlp 영상 정보 읽기 상한 — 누를 때의 키 확인(10초)과 더해 web 프록시 60초 안(MS-007)
    INFO_TIMEOUT_SEC: float = 40
    YTDLP_BIN: str = "yt-dlp"
    FFMPEG_BIN: str = "ffmpeg"
    FFPROBE_BIN: str = "ffprobe"
    OPENAI_TIMEOUT_SEC: float = 120
    # 인포그래픽 한 장의 상한 — 세로 한 장이 수십 초 걸린다. 뒤에서 돌아 web 넘기기 60초와 무관
    IMAGE_TIMEOUT_SEC: float = 180
    OPENAI_BASE_URL: str | None = None  # E2E의 가짜 OpenAI 서버만 채운다
    OPENAI_MAX_RETRIES: int = 0
    # 텍스트 모델의 추론 강도 — low면 답 2~3초 · 47분 요약 8초(기본은 3~4배, 카드 C 실측)
    TEXT_REASONING_EFFORT: str = "low"

    @property
    def EXPORT_DIR(self) -> str:
        """내보낸 마크다운을 쓰는 곳 — data 폴더 안 export/(MS-003)."""
        return f"{self.DATA_DIR}/export"

    @property
    def FRAMES_DIR(self) -> str:
        """챕터 대표 장면 — data 폴더 안 frames/{video_id}/{chapter_seq}.jpg(MS-003)."""
        return f"{self.DATA_DIR}/frames"

    @property
    def UPLOAD_DIR(self) -> str:
        """브라우저로 올린 사본의 자리 — data 폴더 안 uploads/(MS-001, INFRA C4)."""
        return f"{self.DATA_DIR}/uploads"


config = Config()

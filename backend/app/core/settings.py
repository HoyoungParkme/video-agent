"""SettingsService — 키 상태와 모델 선택(VA-MS-005). `.env` 파일 하나를 읽고 쓰고, DB가 없다.

라우터(settings_router.py)와 다른 묶음의 서비스가 이 모듈의 `settings` 하나를 쓴다.
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from app.core.config import ModelOption, ModelOptions, config
from app.core.errors import (
    Internal,
    KeyInvalid,
    KeyMissing,
    KeyRejected,
    LlmUnavailable,
    Validation,
)
from app.infra import openai
from app.infra.openai import KeyCheck, KeyState, ReasonKind

log = logging.getLogger(__name__)

# 이 서비스가 읽고 쓰는 줄은 셋뿐이다. DB 비밀번호 같은 다른 줄은 건드리지 않는다
NAMES = ("OPENAI_API_KEY", "STT_MODEL", "TEXT_MODEL")
STORED_IN = ".env에 저장됨"


class KeyStatus(BaseModel):
    """키 상태 — 마지막 확인 결과와 가린 키(VA-API-001 4장)."""

    state: KeyState
    masked: str | None
    stored_in: str | None
    checked_at: datetime | None
    reason_kind: ReasonKind | None
    reason: str | None


class Models(BaseModel):
    """고른 모델의 id 둘(VA-API-001 4장). 받아쓰기는 자막으로 만든 결과면 None."""

    stt: str | None
    text: str


class ChosenModels(BaseModel):
    """지금 고른 모델의 id와 단가(VA-DOM-002 2.6)."""

    stt: ModelOption
    text: ModelOption


class Settings(BaseModel):
    """설정 전부(VA-API-001 4장)."""

    key: KeyStatus
    models: Models
    model_options: ModelOptions
    inbox_path: str


def _parse(line: str) -> tuple[str, str] | None:
    """`.env` 한 줄 → (이름, 값). 빈 줄 · 주석이면 None.

    앞의 `export `와 값을 감싼 따옴표 한 쌍은 뗀다.
    """
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        return None
    s = s.removeprefix("export ").lstrip()
    name, value = s.split("=", 1)
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return name.strip(), value


def _pick(options: list[ModelOption], wanted: str | None, default: str) -> ModelOption:
    by_id = {o.id: o for o in options}
    return by_id.get(wanted or "") or by_id[default]


def _mask(key: str) -> str:
    # 앞 3자 · 끝 4자만. 짧은 값(손으로 잘못 적은 것)은 끝을 보이지 않는다
    return f"{key[:3]}…{key[-4:]}" if len(key) >= 12 else f"{key[:3]}…"


class SettingsService:
    """키 상태 · 모델 선택. `.env`의 세 줄만 읽고 쓰고, 마지막 키 확인 결과를 메모리에 둔다.

    - read_env() · write_env(): `.env`의 세 줄을 읽고, 그 줄만 제자리에서 고친다
    - current_models() · api_key(): 지금 모델과 단가 · 지금 키(어댑터의 클라이언트용)
    - get(): 설정 전부. OpenAI에 아무것도 보내지 않는다
    - set_key() · set_models(): 새 키를 확인하고 저장 · 모델 선택 저장
    - check_stored_key() · require_key(): 저장된 키 확인 · 마지막 결과로 막기
    """

    def __init__(self) -> None:
        # 서버 시작(main.py)이 곧바로 check_stored_key로 바꾼다
        self.last_check = KeyCheck(KeyState.missing, None, None, datetime.now(UTC))
        self._lock = threading.Lock()

    def read_env(self) -> dict[str, str]:
        """VA-MS-005#SettingsService.read_env

        `.env`에서 세 값(키 · 받아쓰기 모델 · 텍스트 모델)만 읽는다. 같은 이름이 두 번이면 뒤의 것.

        Returns:
            있는 것만 담긴 dict. 파일이 없으면 빈 dict
        """
        try:
            text = Path(config.ENV_PATH).read_text(encoding="utf-8")
        except FileNotFoundError:
            return {}
        out: dict[str, str] = {}
        for line in text.splitlines():
            parsed = _parse(line)
            if parsed and parsed[0] in NAMES:
                out[parsed[0]] = parsed[1]
        return out

    def write_env(self, values: dict[str, str]) -> None:
        """VA-MS-005#SettingsService.write_env

        그 이름의 마지막 줄만 `이름=값`으로 바꾸고, 없으면 끝에 더한다.
        다른 줄 · 주석 · 순서는 그대로다. 파일을 제자리에서 쓴다 —
        바인드 마운트한 파일은 rename으로 바꿀 수 없다(EBUSY).

        Args:
            values: OPENAI_API_KEY · STT_MODEL · TEXT_MODEL 중에서만. 다른 이름이면 ValueError

        Raises:
            OSError: 파일을 쓰지 못했다(읽기 전용 마운트 등). 부르는 쪽이 internal로 접는다
        """
        unknown = set(values) - set(NAMES)
        if unknown:
            raise ValueError(f".env에 쓸 수 없는 이름: {sorted(unknown)}")
        with self._lock:
            path = Path(config.ENV_PATH)
            exists = path.exists()
            lines = path.read_text(encoding="utf-8").splitlines() if exists else []
            for name, value in values.items():
                found = [i for i, line in enumerate(lines) if (_parse(line) or ("",))[0] == name]
                if found:
                    lines[found[-1]] = f"{name}={value}"
                else:
                    lines.append(f"{name}={value}")
            with open(path, "r+" if exists else "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
                f.truncate()
                f.flush()
                os.fsync(f.fileno())


settings = SettingsService()

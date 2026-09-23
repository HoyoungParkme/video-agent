"""OpenAI 공용 클라이언트 — 클라이언트 · 키 확인 · 받아쓰기 · 채팅(VA-MS-007).

키는 늘 인자로 받는다 — SDK가 OPENAI_API_KEY 환경 변수를 스스로 읽지 않게(MS-005 3장).
SDK 예외는 그대로 올린다. 키 원문과 메시지 본문은 로그에 남기지 않는다(DEV-6).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)

from app.core.config import config

log = logging.getLogger(__name__)


class KeyState(StrEnum):
    ok = "ok"
    missing = "missing"
    invalid = "invalid"


class ReasonKind(StrEnum):
    format = "format"
    auth = "auth"
    quota = "quota"
    network = "network"


@dataclass(frozen=True)
class KeyCheck:
    """키 확인 결과(DOM-002 2.6). infra가 만드는 유일한 DTO — 도메인 개념이 아니라 허용한다."""

    state: KeyState
    reason_kind: ReasonKind | None
    reason: str | None
    checked_at: datetime


# 마지막으로 만든 (키, 클라이언트) 한 쌍
_last: tuple[str, AsyncOpenAI] | None = None


def client(key: str) -> AsyncOpenAI:
    """VA-MS-007#openai.client

    키로 클라이언트를 준다. 같은 키면 전에 만든 것을, 다르면 새로 만든다.
    옛 클라이언트는 닫지 않는다 — 옛 키로 보낸 요청이 아직 돌 수 있다.

    Args:
        key: OpenAI API 키

    Returns:
        SDK 자체 재시도를 끈 async 클라이언트
    """
    global _last
    if _last is not None and _last[0] == key:
        return _last[1]
    c = AsyncOpenAI(
        api_key=key,
        base_url=config.OPENAI_BASE_URL,
        timeout=config.OPENAI_TIMEOUT_SEC,
        max_retries=config.OPENAI_MAX_RETRIES,
    )
    _last = (key, c)
    return c


def _invalid(kind: ReasonKind, reason: str) -> KeyCheck:
    return KeyCheck(KeyState.invalid, kind, reason, datetime.now(UTC))


async def verify_key(key: str) -> KeyCheck:
    """VA-MS-007#openai.verify_key

    모델 목록을 한 번 조회해 키를 확인한다. 던지지 않는다 — 결과를 상태로 준다.

    Args:
        key: 확인할 키

    Returns:
        ok, 또는 invalid와 이유(format · auth · quota · network)
    """
    if not key.startswith("sk-") or len(key) < 20:
        return _invalid(ReasonKind.format, "키 형식이 아닙니다")
    try:
        await client(key).models.list(timeout=config.KEY_CHECK_TIMEOUT_SEC)
    except AuthenticationError:
        return _invalid(ReasonKind.auth, "인증에 실패했습니다")
    except RateLimitError as e:
        if e.code == "insufficient_quota":
            return _invalid(ReasonKind.quota, "잔액이 없습니다")
        return _invalid(ReasonKind.auth, f"{e.status_code} {_first_line(e.message)}")
    except APIConnectionError:  # 시간 초과(APITimeoutError)도 여기
        return _invalid(ReasonKind.network, "연결하지 못했습니다")
    except APIStatusError as e:
        return _invalid(ReasonKind.auth, f"{e.status_code} {_first_line(e.message)}")
    return KeyCheck(KeyState.ok, None, None, datetime.now(UTC))


def _first_line(message: str) -> str:
    return message.strip().splitlines()[0] if message.strip() else ""

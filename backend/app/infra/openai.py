"""OpenAI 공용 클라이언트 — 클라이언트 · 키 확인 · 받아쓰기 · 채팅 · 예외 한 줄(VA-MS-007).

키는 늘 인자로 받는다 — SDK가 OPENAI_API_KEY 환경 변수를 스스로 읽지 않게(MS-005 3장).
SDK 예외는 그대로 올린다. 키 원문과 메시지 본문은 로그에 남기지 않는다(DEV-6).
"""

from __future__ import annotations

import base64
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
)

from app.core.config import config
from app.infra.errors import OpenAIOutputError

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


def _format_ok(key: str) -> bool:
    # HTTP 헤더에 넣을 수 없는 글자(한글 · 보이지 않는 U+200B · U+FEFF 등)와 공백을 여기서 거른다
    return (
        key.startswith("sk-")
        and len(key) >= 20
        and key.isascii()
        and key.isprintable()
        and " " not in key
    )


async def verify_key(key: str) -> KeyCheck:
    """VA-MS-007#openai.verify_key

    모델 목록을 한 번 조회해 키를 확인한다. 던지지 않는다 — 결과를 상태로 준다.
    실패는 둘로 가른다 — 키 탓(format · auth · quota, 다시 확인해도 같다)과
    잠깐의 실패(network, 다시 확인하면 풀릴 수 있다).

    Args:
        key: 확인할 키

    Returns:
        ok, 또는 invalid와 이유(한국어 한 줄)
    """
    if not _format_ok(key):
        return _invalid(ReasonKind.format, "키 형식이 아닙니다")
    try:
        await client(key).models.list(timeout=config.KEY_CHECK_TIMEOUT_SEC)
    except AuthenticationError:
        return _invalid(ReasonKind.auth, "인증에 실패했습니다")
    except PermissionDeniedError:
        return _invalid(ReasonKind.auth, "이 키로는 쓸 수 없습니다")
    except RateLimitError as e:
        if e.code == "insufficient_quota":
            return _invalid(ReasonKind.quota, "잔액이 없습니다")
        return _invalid(ReasonKind.network, f"OpenAI가 잠시 답하지 못했습니다({e.status_code})")
    except APIConnectionError:  # 시간 초과(APITimeoutError)도 여기
        return _invalid(ReasonKind.network, "연결하지 못했습니다")
    except APIStatusError as e:
        if e.status_code in (408, 409) or e.status_code >= 500:
            return _invalid(ReasonKind.network, f"OpenAI가 잠시 답하지 못했습니다({e.status_code})")
        return _invalid(ReasonKind.auth, f"OpenAI가 키를 받지 않았습니다({e.status_code})")
    except Exception:  # 응답을 읽지 못함 등 — 던지지 않는다
        return _invalid(ReasonKind.network, "응답을 읽지 못했습니다")
    return KeyCheck(KeyState.ok, None, None, datetime.now(UTC))


async def transcribe(client: AsyncOpenAI, path: str, model: str) -> dict:
    """VA-MS-007#openai.transcribe

    음성 파일 하나를 받아쓴다 — verbose_json, 구간 단위 시각. 언어는 자동 감지.

    Args:
        client: `client(key)`가 준 클라이언트
        path: 음성 파일(25MB 이하)
        model: 받아쓰기 모델

    Returns:
        응답 dict — language · duration · segments[{start, end, text}]
    """
    with open(path, "rb") as f:
        resp = await client.audio.transcriptions.create(
            model=model,
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    return resp.model_dump()


async def chat(
    client: AsyncOpenAI, model: str, messages: list[dict], json_mode: bool = True
) -> str:
    """VA-MS-007#openai.chat

    채팅 완성 한 번. 파싱은 어댑터가 한다. 토큰 사용량만 로그에 남긴다.

    Args:
        client: `client(key)`가 준 클라이언트
        model: 텍스트 모델
        messages: 대화 메시지 목록
        json_mode: 참이면 JSON 객체로만 답하게 한다

    Returns:
        첫 선택지의 본문. 비었으면 빈 문자열
    """
    extra: dict[str, Any] = {"response_format": {"type": "json_object"}} if json_mode else {}
    resp = await client.chat.completions.create(
        model=model,
        messages=messages,
        reasoning_effort=config.TEXT_REASONING_EFFORT,  # 속도 · 비용 — 카드 C 실측
        **extra,
    )
    if resp.usage is not None:
        log.info(
            "chat %s 토큰 입력 %d · 출력 %d",
            model,
            resp.usage.prompt_tokens,
            resp.usage.completion_tokens,
        )
    return resp.choices[0].message.content or ""


async def chat_json[T](
    client: AsyncOpenAI, model: str, messages: list[dict], parse: Callable[[Any], T]
) -> T:
    """VA-MS-007#openai.chat_json

    JSON 모드로 부르고 파싱 · 다듬기까지. 형식이 틀리면(JSON 아님 · 키 없음 · 타입 틀림 · 다듬고
    나니 빔 — parse가 던진다) config.LLM_RETRY만큼 다시 부른다. SDK 예외는 다시 부르지 않는다 —
    재시도 수는 부르는 쪽이 센다. 요약 · 챕터 · 추천 질문 · 답변이 같이 쓴다.

    Args:
        client: `client(key)`가 준 클라이언트
        model: 텍스트 모델
        messages: 대화 메시지 목록
        parse: JSON 값 → 결과. 형식이 틀리면 ValueError · KeyError · TypeError

    Returns:
        parse의 결과

    Raises:
        OpenAIOutputError: 다시 불러도 형식이 틀렸다(마지막 까닭이 메시지에)
    """
    why = ""
    for _ in range(config.LLM_RETRY + 1):
        raw = await chat(client, model, messages)
        try:
            return parse(json.loads(raw))
        except (ValueError, KeyError, TypeError) as e:
            why = str(e) or type(e).__name__
    raise OpenAIOutputError(f"모델 출력을 읽지 못했어요({why})")


# 이미지 모델의 안전 검사에 걸렸을 때 400의 code
MODERATION_CODES = ("moderation_blocked", "content_policy_violation")


async def image(client: AsyncOpenAI, model: str, prompt: str, size: str, quality: str) -> bytes:
    """VA-MS-007#openai.image

    이미지 생성 한 번 — 인포그래픽 세로 한 장. 이 호출만 시간 제한이 길다(IMAGE_TIMEOUT_SEC).
    사용량(입력 · 출력 이미지 토큰)만 로그에 남긴다 — 한 장 값을 재는 근거다. 프롬프트는 찍지
    않는다. SDK 예외는 그대로 올린다(어댑터가 llm-unavailable로 바꾼다).

    Args:
        client: `client(key)`가 준 클라이언트
        model: 이미지 모델
        prompt: 지시문과 재료
        size: `1024x1536` 같은 크기
        quality: low · medium

    Returns:
        PNG 바이트

    Raises:
        OpenAIOutputError: 응답에 그림이 없다
    """
    resp = await client.with_options(timeout=config.IMAGE_TIMEOUT_SEC).images.generate(
        model=model, prompt=prompt, size=size, quality=quality, n=1
    )
    usage = getattr(resp, "usage", None)
    if usage is not None:
        tokens = (usage.input_tokens, usage.output_tokens)
        log.info("image %s %s 토큰 입력 %d · 출력 %d", model, quality, *tokens)
    b64 = resp.data[0].b64_json if resp.data else None
    if not b64:
        raise OpenAIOutputError("그림을 받지 못했어요")
    return base64.b64decode(b64)


def reason_of(e: BaseException) -> str:
    """VA-MS-007#openai.reason_of

    OpenAI 호출 예외 → 한국어 한 줄. 실패 알림(파이프라인) · 답변 실패(대화) · 인포그래픽 실패의
    '왜'가 이 표 하나를 쓴다. 시간 초과가 연결 오류보다 먼저다(하위 클래스).

    Args:
        e: OpenAI 호출에서 난 예외

    Returns:
        한 줄
    """
    if isinstance(e, APITimeoutError | TimeoutError):
        return "네트워크 시간 초과"
    if isinstance(e, APIConnectionError):
        return "네트워크에 연결할 수 없음"
    if isinstance(e, OpenAIOutputError):
        return e.reason
    status = getattr(e, "status_code", None)
    if status == 401:
        return "API 키 인증 실패"
    if status == 403:
        return "OpenAI 권한 없음"
    if status == 429:
        quota = getattr(e, "code", None) == "insufficient_quota"
        return "OpenAI 잔액 부족" if quota else "OpenAI 요청 한도 초과"
    if isinstance(status, int) and status >= 500:
        return "OpenAI 서버 오류"
    if isinstance(status, int):
        return f"OpenAI가 요청을 거절함({status})"
    return "OpenAI 오류"

"""infra/openai — VA-MS-007 openai.client · verify_key · transcribe · chat의 테스트 관점."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx2
import openai as sdk
import pytest

from app.core.config import config
from app.infra import openai
from app.infra.openai import KeyState, ReasonKind

KEY = "sk-test-abcdefghijklmnop1234"


@pytest.fixture(autouse=True)
def fresh_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """테스트마다 마지막 클라이언트 기억을 비운다."""
    monkeypatch.setattr(openai, "_last", None)


class FakeServer:
    """가짜 OpenAI — 응답 하나를 정해 두고 받은 요청을 센다."""

    def __init__(self) -> None:
        self.requests: list[httpx2.Request] = []
        self.reply: Any = httpx2.Response(
            200, json={"object": "list", "data": [{"id": "gpt-5-mini", "object": "model",
                                                     "created": 0, "owned_by": "openai"}]}
        )  # fmt: skip

    def handle(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch) -> FakeServer:
    """openai.client가 가짜 서버로 가는 클라이언트를 주게 한다."""
    s = FakeServer()

    def fake_client(key: str) -> sdk.AsyncOpenAI:
        return sdk.AsyncOpenAI(
            api_key=key,
            base_url="http://fake/v1",
            max_retries=0,
            http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(s.handle)),
        )

    monkeypatch.setattr(openai, "client", fake_client)
    return s


def _error(status: int, code: str) -> httpx2.Response:
    return httpx2.Response(status, json={"error": {"message": "안 됨", "type": "x", "code": code}})


def test_client_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    c = openai.client(KEY)
    assert c.max_retries == 0
    assert c.timeout == config.OPENAI_TIMEOUT_SEC


def test_client_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "OPENAI_BASE_URL", "http://127.0.0.1:8190/v1")
    assert str(openai.client(KEY).base_url).startswith("http://127.0.0.1:8190/v1")


def test_client_keeps_one_pair() -> None:
    a = openai.client(KEY)
    assert openai.client(KEY) is a
    b = openai.client(KEY + "x")
    assert b is not a
    assert openai.client(KEY) is not a  # 한 쌍만 둔다 — 옛 키면 또 새 객체


@pytest.mark.parametrize(
    "key",
    [
        "abc",
        KEY + "\u200b",
        "\ufeff" + KEY,
        "sk-키가아닌글자000000000000",
        "sk-with space 000000000000",
    ],
)
async def test_verify_format_without_request(server: FakeServer, key: str) -> None:
    check = await openai.verify_key(key)
    assert (check.state, check.reason_kind) == (KeyState.invalid, ReasonKind.format)
    assert server.requests == []


@pytest.mark.parametrize(
    ("reply", "kind", "reason"),
    [
        (_error(401, "invalid_api_key"), ReasonKind.auth, "인증에 실패했습니다"),
        (_error(403, "unsupported_country"), ReasonKind.auth, "이 키로는 쓸 수 없습니다"),
        (_error(404, "not_found"), ReasonKind.auth, "OpenAI가 키를 받지 않았습니다(404)"),
        (_error(429, "insufficient_quota"), ReasonKind.quota, "잔액이 없습니다"),
        # 잠깐의 실패 — 다시 확인하면 풀릴 수 있어 막지 않는다(API-001 ReasonKind)
        (
            _error(429, "rate_limit_exceeded"),
            ReasonKind.network,
            "OpenAI가 잠시 답하지 못했습니다(429)",
        ),
        (_error(500, "server_error"), ReasonKind.network, "OpenAI가 잠시 답하지 못했습니다(500)"),
        (_error(503, "overloaded"), ReasonKind.network, "OpenAI가 잠시 답하지 못했습니다(503)"),
        (_error(408, "timeout"), ReasonKind.network, "OpenAI가 잠시 답하지 못했습니다(408)"),
        (httpx2.ConnectError("연결 거부"), ReasonKind.network, "연결하지 못했습니다"),
        (httpx2.ReadTimeout("시간 초과"), ReasonKind.network, "연결하지 못했습니다"),
        (
            httpx2.Response(200, text="<html>점검 중</html>"),
            ReasonKind.network,
            "응답을 읽지 못했습니다",
        ),
    ],
)
async def test_verify_failures(
    server: FakeServer, reply: Any, kind: ReasonKind, reason: str
) -> None:
    server.reply = reply
    check = await openai.verify_key(KEY)
    assert (check.state, check.reason_kind, check.reason) == (KeyState.invalid, kind, reason)
    assert check.checked_at


async def test_verify_ok(server: FakeServer) -> None:
    check = await openai.verify_key(KEY)
    assert check.state == KeyState.ok and check.reason_kind is None
    assert check.checked_at is not None
    [req] = server.requests
    assert req.url.path == "/v1/models"
    assert req.headers["authorization"] == f"Bearer {KEY}"


async def test_key_not_logged(server: FakeServer, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="app")
    openai.client(KEY)
    await openai.verify_key(KEY)
    server.reply = _error(401, "invalid_api_key")
    await openai.verify_key(KEY)
    assert KEY not in caplog.text


class _Recorder:
    """가짜 SDK 메서드 — 받은 인자를 적고 정한 값을 돌려준다."""

    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self.kwargs: dict[str, Any] = {}
        self.result, self.error = result, error

    async def create(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.result


async def test_transcribe(tmp_path: Path) -> None:
    audio = tmp_path / "1.mp3"
    audio.write_bytes(b"mp3")
    body = {"language": "korean", "duration": 600.0, "segments": [{"start": 0.0, "end": 4.2}]}
    rec = _Recorder(SimpleNamespace(model_dump=lambda: body))
    fake = SimpleNamespace(audio=SimpleNamespace(transcriptions=rec))
    assert await openai.transcribe(fake, str(audio), "whisper-1") == body
    assert rec.kwargs["response_format"] == "verbose_json"
    assert rec.kwargs["timestamp_granularities"] == ["segment"]
    assert rec.kwargs["model"] == "whisper-1"
    assert "language" not in rec.kwargs
    assert rec.kwargs["file"].closed


def _chat_client(rec: _Recorder) -> Any:
    return SimpleNamespace(chat=SimpleNamespace(completions=rec))


def _completion(content: str | None) -> Any:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=1200, completion_tokens=300),
    )


async def test_chat_json_mode(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app")
    rec = _Recorder(_completion('{"one_liner": "요약"}'))
    messages = [{"role": "user", "content": "<transcript>비밀 스크립트</transcript>"}]
    assert await openai.chat(_chat_client(rec), "gpt-5-mini", messages) == '{"one_liner": "요약"}'
    assert rec.kwargs["response_format"] == {"type": "json_object"}
    assert "1200" in caplog.text and "300" in caplog.text
    assert "비밀 스크립트" not in caplog.text


async def test_chat_plain_and_empty() -> None:
    rec = _Recorder(_completion(None))
    assert await openai.chat(_chat_client(rec), "gpt-5-mini", [], json_mode=False) == ""
    assert "response_format" not in rec.kwargs


async def test_chat_passes_sdk_errors() -> None:
    error = sdk.APIConnectionError(request=httpx2.Request("POST", "http://fake/v1/chat"))
    with pytest.raises(sdk.APIConnectionError):
        await openai.chat(_chat_client(_Recorder(error=error)), "gpt-5-mini", [])

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


async def test_verify_format_without_request(server: FakeServer) -> None:
    check = await openai.verify_key("abc")
    assert (check.state, check.reason_kind) == (KeyState.invalid, ReasonKind.format)
    assert server.requests == []


@pytest.mark.parametrize(
    ("reply", "kind"),
    [
        (_error(401, "invalid_api_key"), ReasonKind.auth),
        (_error(429, "insufficient_quota"), ReasonKind.quota),
        (_error(429, "rate_limit_exceeded"), ReasonKind.auth),
        (_error(500, "server_error"), ReasonKind.auth),
        (httpx2.ConnectError("연결 거부"), ReasonKind.network),
        (httpx2.ReadTimeout("시간 초과"), ReasonKind.network),
    ],
)
async def test_verify_failures(server: FakeServer, reply: Any, kind: ReasonKind) -> None:
    server.reply = reply
    check = await openai.verify_key(KEY)
    assert (check.state, check.reason_kind) == (KeyState.invalid, kind)
    assert check.reason and check.checked_at


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

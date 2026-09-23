"""core/settings_router — GET · POST key · PUT models(VA-API-001 3.1)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
import pytest

from app.core.settings import settings
from app.infra.openai import KeyCheck, KeyState, ReasonKind
from app.main import app

KEY = "sk-abcdefghijklmnop1234"
PROBLEM = "application/problem+json"


@pytest.fixture
async def client(env_file, verify, monkeypatch) -> AsyncIterator[httpx.AsyncClient]:
    """시작 이벤트 없이 앱에 바로 붙는다. 마지막 확인 결과는 키 없음에서 시작."""
    monkeypatch.setattr(
        settings, "last_check", KeyCheck(KeyState.missing, None, None, datetime.now(UTC))
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_get_settings(client, env_file) -> None:
    env_file.write_text(f"OPENAI_API_KEY={KEY}\n")
    r = await client.get("/api/settings")
    assert r.status_code == 200
    body = r.json()
    assert body["key"] == {
        "state": "missing",
        "masked": "sk-…1234",
        "stored_in": ".env에 저장됨",
        "checked_at": body["key"]["checked_at"],
        "reason_kind": None,
        "reason": None,
    }
    assert body["models"] == {"stt": "whisper-1", "text": "gpt-5-mini"}
    assert body["model_options"]["stt"] == [
        {"id": "whisper-1", "label": "whisper-1", "price": {"per_min_usd": 0.006}}
    ]
    assert [o["id"] for o in body["model_options"]["text"]] == [
        "gpt-5-mini",
        "gpt-5.4-mini",
        "gpt-5.4",
    ]
    assert body["model_options"]["text"][0]["price"] == {
        "input_per_mtok_usd": 0.25,
        "output_per_mtok_usd": 2.0,
    }
    assert "inbox_path" in body


async def test_post_key_ok(client, env_file, verify) -> None:
    r = await client.post("/api/settings/key", json={"key": KEY})
    assert r.status_code == 200
    assert r.json()["key"]["state"] == "ok"
    assert KEY not in r.text  # 전체 키는 어떤 응답에도 없다
    assert f"OPENAI_API_KEY={KEY}" in env_file.read_text()


@pytest.mark.parametrize(
    ("fail", "status", "kind"),
    [(ReasonKind.auth, 422, "key-rejected"), (ReasonKind.network, 502, "llm-unavailable")],
)
async def test_post_key_failures(client, env_file, verify, fail, status, kind) -> None:
    verify.fail = fail
    r = await client.post("/api/settings/key", json={"key": KEY})
    assert r.status_code == status
    assert r.headers["content-type"].startswith(PROBLEM)
    body = r.json()
    assert body["type"] == f"urn:va:{kind}"
    assert body["reason"]
    if kind == "key-rejected":
        assert body["reason_kind"] == "auth"
    assert not env_file.exists()


@pytest.mark.parametrize("key", ["", "   "])
async def test_post_key_empty(client, verify, key) -> None:
    r = await client.post("/api/settings/key", json={"key": key})
    assert r.status_code == 422
    body = r.json()
    assert body["type"] == "urn:va:validation"
    assert body["errors"][0]["field"] == "key"
    assert verify.calls == []


async def test_validation_does_not_echo_input(client) -> None:
    r = await client.post("/api/settings/key", json={"key": 12345678901234567890})
    assert r.status_code == 422
    assert "12345678901234567890" not in r.text


async def test_put_models(client, env_file) -> None:
    r = await client.put(
        "/api/settings/models", json={"stt_model": "whisper-1", "text_model": "gpt-5.4-mini"}
    )
    assert r.status_code == 200
    assert r.json()["models"] == {"stt": "whisper-1", "text": "gpt-5.4-mini"}
    assert "TEXT_MODEL=gpt-5.4-mini" in env_file.read_text()


async def test_put_models_unknown(client, env_file) -> None:
    r = await client.put(
        "/api/settings/models", json={"stt_model": "whisper-1", "text_model": "gpt-4o"}
    )
    assert r.status_code == 422
    assert r.json()["type"] == "urn:va:validation"
    assert not env_file.exists()

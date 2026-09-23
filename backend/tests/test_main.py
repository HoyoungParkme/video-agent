"""main — 앱 조립 · 시작 때 키 확인 · /health."""

from __future__ import annotations

import httpx

from app.core.settings import settings
from app.infra.openai import KeyState
from app.main import app


async def test_health() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/health")
    assert r.json() == {"status": "ok"}


async def test_lifespan_checks_stored_key(env_file, verify, monkeypatch) -> None:
    monkeypatch.setattr(settings, "last_check", settings.last_check)  # 끝나면 되돌린다
    env_file.write_text("OPENAI_API_KEY=sk-abcdefghijklmnop1234\n")
    async with app.router.lifespan_context(app):
        assert settings.last_check.state == KeyState.ok
    assert verify.calls == ["sk-abcdefghijklmnop1234"]

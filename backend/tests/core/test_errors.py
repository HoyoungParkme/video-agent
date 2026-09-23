"""core/errors — problem+json 17종과 핸들러 셋(VA-API-001 2장)."""

from __future__ import annotations

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from app.core import errors

# API-001 2장 표 그대로 — 종류와 상태 코드
TABLE = {
    "not-found": 404,
    "validation": 422,
    "key-missing": 503,
    "key-invalid": 503,
    "key-rejected": 422,
    "url-invalid": 422,
    "source-unavailable": 502,
    "video-too-long": 422,
    "no-audio-track": 422,
    "unsupported-file": 422,
    "path-outside-inbox": 422,
    "job-exists": 409,
    "job-not-failed": 409,
    "result-not-ready": 409,
    "llm-unavailable": 502,
    "export-failed": 500,
    "internal": 500,
}


def test_seventeen_kinds() -> None:
    classes = [errors.Problem, *errors.Problem.__subclasses__()]
    assert {c.kind: c.status for c in classes if c is not errors.Problem} | {
        "internal": errors.Internal.status
    } == TABLE


class Body(BaseModel):
    question: str


def _app() -> FastAPI:
    app = FastAPI()
    errors.install(app)

    @app.get("/missing")
    def missing() -> None:
        raise errors.NotFound(resource="video", id=3)

    @app.post("/ask")
    def ask(body: Body) -> None:
        return None

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("내부 사정 — 밖으로 나가면 안 된다")

    return app


async def _call(method: str, path: str, **kw) -> httpx.Response:
    transport = httpx.ASGITransport(app=_app(), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        return await c.request(method, path, **kw)


async def test_problem_response() -> None:
    r = await _call("GET", "/missing")
    assert r.status_code == 404
    assert r.headers["content-type"] == "application/problem+json"
    body = r.json()
    assert body["type"] == "urn:va:not-found"
    assert (body["resource"], body["id"]) == ("video", 3)
    assert {"title", "status", "detail"} <= body.keys()


async def test_request_validation() -> None:
    r = await _call("POST", "/ask", json={"question": 1234567})
    assert r.status_code == 422
    body = r.json()
    assert body["type"] == "urn:va:validation"
    assert body["errors"][0]["field"] == "question"
    assert "1234567" not in r.text


async def test_catch_all_is_internal() -> None:
    r = await _call("GET", "/boom")
    assert r.status_code == 500
    assert r.headers["content-type"] == "application/problem+json"
    assert r.json()["type"] == "urn:va:internal"
    assert "내부 사정" not in r.text

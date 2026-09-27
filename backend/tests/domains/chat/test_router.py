"""chat/router — /api/videos/{id}/chat(VA-API-001 3.6). 기록과 질문, 에러는 problem+json."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.errors import LlmUnavailable
from app.domains.job.models import JobStatus

T0 = datetime(2026, 9, 27, 3, 0, tzinfo=UTC)


async def _analyzed(make):
    row = await make.video()
    await make.job(row.id)
    await make.transcript(row.id, ["하나", "둘", "셋"])
    return row


async def test_get_chat_history(api, make) -> None:
    row = await make.video()
    assert (await api.get(f"/api/videos/{row.id}/chat")).json() == []  # 결과가 없어도 빈 목록
    await make.turn(row.id, "둘째", at=T0 + timedelta(seconds=1))
    await make.turn(row.id, "첫째", "근거 있는 답", cited=[60.0], at=T0)
    r = await api.get(f"/api/videos/{row.id}/chat")
    assert r.status_code == 200
    assert [(t["question"], t["cited_secs"]) for t in r.json()] == [("첫째", [60.0]), ("둘째", [])]
    missing = await api.get("/api/videos/999/chat")
    assert (missing.status_code, missing.json()["type"]) == (404, "urn:va:not-found")


async def test_post_chat_saves_turn(api, make, key, answerer) -> None:
    row = await _analyzed(make)
    r = await api.post(f"/api/videos/{row.id}/chat", json={"question": "어떤 DB를 썼어?"})
    assert r.status_code == 201
    body = r.json()
    assert (body["question"], body["answer"], body["cited_secs"]) == (
        "어떤 DB를 썼어?",
        "PostgreSQL을 썼다고 합니다.",
        [60.0, 120.0],
    )
    video = (await api.get(f"/api/videos/{row.id}")).json()["video"]
    assert video["chat_turn_count"] == 1


async def test_post_chat_errors(api, make, key, answerer) -> None:
    row = await _analyzed(make)
    url = f"/api/videos/{row.id}/chat"
    for body in ({"question": ""}, {}):
        r = await api.post(url, json=body)
        assert (r.status_code, r.json()["type"]) == (422, "urn:va:validation")
    r = await api.post("/api/videos/999/chat", json={"question": "왜?"})
    assert (r.status_code, r.json()["type"]) == (404, "urn:va:not-found")
    running = await make.video()
    await make.job(running.id, JobStatus.running)
    r = await api.post(f"/api/videos/{running.id}/chat", json={"question": "왜?"})
    assert (r.status_code, r.json()["type"], r.json()["video_status"]) == (
        409,
        "urn:va:result-not-ready",
        "in_progress",
    )
    answerer.error = LlmUnavailable(reason="OpenAI 서버 오류")
    r = await api.post(url, json={"question": "왜?"})
    assert (r.status_code, r.json()["type"], r.json()["reason"]) == (
        502,
        "urn:va:llm-unavailable",
        "OpenAI 서버 오류",
    )
    assert (await api.get(url)).json() == []  # 실패한 질문은 저장하지 않는다


async def test_post_chat_without_key(api, make, env_file, verify, answerer) -> None:
    row = await _analyzed(make)
    r = await api.post(f"/api/videos/{row.id}/chat", json={"question": "왜?"})
    assert (r.status_code, r.json()["type"]) == (503, "urn:va:key-missing")
    assert answerer.calls == []

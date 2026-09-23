"""chat/router — /api/videos/{id}/chat(VA-API-001 3.6). 스텁 — 질문하기는 B3."""

from __future__ import annotations


async def test_chat_stub(api, make) -> None:
    row = await make.video()
    r = await api.get(f"/api/videos/{row.id}/chat")
    assert (r.status_code, r.json()) == (200, [])
    assert (await api.get("/api/videos/999/chat")).status_code == 404
    r = await api.post(f"/api/videos/{row.id}/chat", json={"question": "왜?"})
    assert (r.status_code, r.json()["type"]) == (501, "urn:va:not-implemented")

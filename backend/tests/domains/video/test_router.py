"""video/router — /api/inbox · /api/videos · /api/videos/{id}(VA-API-001 3.2 · 3.3)."""

from __future__ import annotations

from app.domains.job.models import JobStatus

PROBLEM = "application/problem+json"
URL = "https://youtu.be/dQw4w9WgXcQ"


async def test_post_video_registers_with_estimate(api, key) -> None:
    r = await api.post("/api/videos", json={"source": "youtube", "url": URL})
    assert r.status_code == 200
    body = r.json()
    assert body["video"]["status"] == "registered"
    assert body["video"]["source_id"] == "dQw4w9WgXcQ"
    assert body["estimate"]["needs_stt"] is False
    assert body["estimate"]["seconds"] == 60


async def test_post_video_existing_job_has_no_estimate(api, key, make) -> None:
    first = (await api.post("/api/videos", json={"source": "youtube", "url": URL})).json()
    await make.job(first["video"]["id"], JobStatus.done)
    again = await api.post(
        "/api/videos",
        json={"source": "youtube", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )
    assert again.status_code == 200  # 중복이어도 200
    assert again.json()["video"]["status"] == "analyzed"
    assert again.json()["estimate"] is None


async def test_post_video_errors(api, key, env_file) -> None:
    r = await api.post("/api/videos", json={"source": "youtube", "url": "https://vimeo.com/1"})
    assert (r.status_code, r.headers["content-type"], r.json()["type"]) == (
        422,
        PROBLEM,
        "urn:va:url-invalid",
    )
    r = await api.post("/api/videos", json={"source": "nope"})
    assert (r.status_code, r.json()["type"]) == (422, "urn:va:validation")
    env_file.write_text("")
    r = await api.post("/api/videos", json={"source": "youtube", "url": URL})
    assert (r.status_code, r.json()["type"]) == (503, "urn:va:key-missing")


async def test_get_videos(api, make) -> None:
    assert (await api.get("/api/videos")).json() == []
    row = await make.video()
    await make.job(row.id, JobStatus.queued)
    body = (await api.get("/api/videos")).json()
    assert [
        (v["id"], v["status"], v["job"]["status"], v["job"]["queue_position"]) for v in body
    ] == [(row.id, "in_progress", "queued", 1)]


async def test_get_video(api, make) -> None:
    r = await api.get("/api/videos/999")
    assert (r.status_code, r.json()["type"], r.json()["resource"]) == (
        404,
        "urn:va:not-found",
        "video",
    )
    row = await make.video()
    body = (await api.get(f"/api/videos/{row.id}")).json()
    assert (body["video"]["id"], body["job"]) == (row.id, None)


async def test_inbox_is_empty_stub(api) -> None:
    body = (await api.get("/api/inbox")).json()
    assert body["files"] == []
    assert "path" in body


async def test_delete_is_stub(api, make) -> None:
    row = await make.video()
    r = await api.delete(f"/api/videos/{row.id}")
    assert (r.status_code, r.headers["content-type"], r.json()["type"]) == (
        501,
        PROBLEM,
        "urn:va:not-implemented",
    )

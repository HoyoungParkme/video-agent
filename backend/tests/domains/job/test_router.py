"""job/router — /api/videos/{id}/job · …/retry(VA-API-001 3.4)."""

from __future__ import annotations

from app.domains.job.models import JobStatus


async def test_post_job_starts(api, key, make) -> None:
    row = await make.video()
    r = await api.post(f"/api/videos/{row.id}/job")
    assert r.status_code == 201
    body = r.json()
    assert (body["status"], body["stage"], body["queue_position"]) == ("queued", "pending", 1)
    assert body["stages"] == ["download", "summarize", "chapter", "suggest"]
    assert body["models"] == {"stt": None, "text": "gpt-5-mini"}
    again = await api.post(f"/api/videos/{row.id}/job")
    assert (again.status_code, again.json()["type"], again.json()["job_status"]) == (
        409,
        "urn:va:job-exists",
        "queued",
    )


async def test_post_job_missing_video(api, key) -> None:
    r = await api.post("/api/videos/999/job")
    assert (r.status_code, r.json()["resource"]) == (404, "video")


async def test_get_job(api, make) -> None:
    row = await make.video()
    r = await api.get(f"/api/videos/{row.id}/job")
    assert (r.status_code, r.json()["resource"]) == (404, "job")  # 작업 없음 → UI-1
    await make.job(row.id, JobStatus.running, stage="summarize", progress_pct=25)
    body = (await api.get(f"/api/videos/{row.id}/job")).json()
    assert (body["status"], body["stage_index"], body["progress_pct"], body["chunks"]) == (
        "running",
        2,
        25,
        None,
    )
    assert (await api.get("/api/videos/999/job")).json()["resource"] == "video"


async def test_retry_is_stub(api, make) -> None:
    row = await make.video()
    await make.job(row.id, JobStatus.failed)
    r = await api.post(f"/api/videos/{row.id}/job/retry")
    assert (r.status_code, r.json()["type"]) == (501, "urn:va:not-implemented")

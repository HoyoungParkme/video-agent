"""analysis/router — /api/videos/{id}/result · …/export(VA-API-001 3.5)."""

from __future__ import annotations

from app.domains.analysis.service import AnalysisService
from app.domains.job.models import JobStatus
from app.domains.job.service import JobService
from app.domains.video.service import VideoService


async def test_result_not_ready_then_ready(api, db, make, summarizer, env_file) -> None:
    row = await make.video()
    r = await api.get(f"/api/videos/{row.id}/result")
    assert (r.status_code, r.json()["type"], r.json()["video_status"]) == (
        409,
        "urn:va:result-not-ready",
        "registered",
    )
    await make.transcript(row.id, ["x"] * 30, step=100)
    video = VideoService.to_dto(row, await JobService(db).latest(row.id), 0)
    svc = AnalysisService(db, summarizer)
    await svc.generate_summary(video)
    await svc.generate_chapters(video)
    await svc.generate_questions(video)
    await make.job(row.id, JobStatus.done)
    body = (await api.get(f"/api/videos/{row.id}/result")).json()
    assert body["video"]["status"] == "analyzed"
    assert len(body["transcript"]["segments"]) == 30
    assert body["summary"]["one_liner"] == "이 영상은 파이썬을 소개한다."
    assert len(body["chapters"]) == 8
    assert body["parts"] == []
    assert [q["seq"] for q in body["suggested_questions"]] == [1, 2, 3]
    assert (await api.get("/api/videos/999/result")).status_code == 404


async def test_export_is_stub(api, make) -> None:
    row = await make.video()
    for method in ("GET", "POST"):
        r = await api.request(method, f"/api/videos/{row.id}/export")
        assert (r.status_code, r.json()["type"]) == (501, "urn:va:not-implemented")

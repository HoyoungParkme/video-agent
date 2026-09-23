"""video/router — /api/inbox · /api/videos · /api/videos/{id}(VA-API-001 3.2 · 3.3)."""

from __future__ import annotations

from app.core.config import config
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


async def test_post_video_local_needs_stt(api, key, probe, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    (tmp_path / "workshop_0912.mp4").write_bytes(b"recording")
    probe.files = {"workshop_0912.mp4": (9000, True)}
    r = await api.post("/api/videos", json={"source": "local", "path": "workshop_0912.mp4"})
    assert r.status_code == 200
    video, est = r.json()["video"], r.json()["estimate"]
    assert (video["status"], video["source_kind"], video["has_captions"]) == (
        "registered",
        "local",
        False,
    )
    assert (est["needs_stt"], est["chunks"], est["concurrency"], est["stt_minutes"]) == (
        True,
        15,
        3,
        150.0,
    )
    assert est["stt_cost_usd"] == 0.9


async def test_post_video_local_without_audio(api, key, probe, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    (tmp_path / "silent.mp4").write_bytes(b"x")
    probe.files = {"silent.mp4": (1800, False)}
    r = await api.post("/api/videos", json={"source": "local", "path": "silent.mp4"})
    assert (r.status_code, r.json()["type"], r.json()["duration_sec"]) == (
        422,
        "urn:va:no-audio-track",
        1800,
    )


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


async def test_inbox_lists_files(api, probe, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    monkeypatch.setattr(config, "INBOX_DISPLAY_PATH", "~/video-agent/inbox")
    (tmp_path / "workshop_0912.mp4").write_bytes(b"mp4")
    probe.files = {"workshop_0912.mp4": (9000, True)}
    r = await api.get("/api/inbox")
    assert r.status_code == 200
    assert r.json()["path"] == "~/video-agent/inbox"
    [f] = r.json()["files"]
    assert (f["name"], f["duration_sec"], f["kind"], f["size_bytes"]) == (
        "workshop_0912.mp4",
        9000,
        "video",
        3,
    )


async def test_inbox_empty_is_200(api, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    r = await api.get("/api/inbox")
    assert (r.status_code, r.json()["files"]) == (200, [])


async def test_inbox_without_mount_is_internal(api, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path / "없음"))
    r = await api.get("/api/inbox")
    assert (r.status_code, r.json()["type"]) == (500, "urn:va:internal")


async def test_delete_is_stub(api, make) -> None:
    row = await make.video()
    r = await api.delete(f"/api/videos/{row.id}")
    assert (r.status_code, r.headers["content-type"], r.json()["type"]) == (
        501,
        PROBLEM,
        "urn:va:not-implemented",
    )

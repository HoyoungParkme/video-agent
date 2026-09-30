"""video/router — /api/inbox · /api/videos · /api/videos/{id}(VA-API-001 3.2 · 3.3)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from app.core.config import config
from app.core.errors import SourceUnavailable
from app.domains.analysis.service import AnalysisService
from app.domains.job.models import JobStatus
from app.domains.job.service import JobService
from app.infra.openai import ReasonKind

PROBLEM = "application/problem+json"
URL = "https://youtu.be/dQw4w9WgXcQ"


async def test_post_video_registers_with_estimate(api, key) -> None:
    r = await api.post("/api/videos", json={"source": "youtube", "url": URL})
    assert r.status_code == 200
    body = r.json()
    assert body["video"]["status"] == "registered"
    assert body["video"]["source_id"] == "dQw4w9WgXcQ"
    assert body["estimate"]["needs_stt"] is False
    assert body["estimate"]["seconds"] == 90  # 텍스트 60 + 장면 30


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


async def test_delete_video(api, make) -> None:
    row = await make.video()
    await make.job(row.id)  # 끝난 작업
    r = await api.delete(f"/api/videos/{row.id}")
    assert (r.status_code, r.content) == (204, b"")
    assert (await api.get(f"/api/videos/{row.id}")).status_code == 404
    again = await api.delete(f"/api/videos/{row.id}")
    assert (again.status_code, again.headers["content-type"], again.json()["type"]) == (
        404,
        PROBLEM,
        "urn:va:not-found",
    )


async def test_delete_running_stops_task_then_wakes(api, make) -> None:
    running = await make.video()
    await make.job(running.id, JobStatus.running)
    waiting = await make.video()
    await make.job(waiting.id, JobStatus.queued)
    task = asyncio.create_task(asyncio.sleep(30))  # 도는 파이프라인 자리
    JobService.tasks[running.id] = task
    JobService.work_event.clear()
    try:
        r = await api.delete(f"/api/videos/{running.id}")
    finally:
        JobService.tasks.pop(running.id, None)
    assert r.status_code == 204
    assert task.cancelled()  # 먼저 멈췄다
    assert JobService.work_event.is_set()  # 지운 뒤 워커를 깨웠다 — 기다리던 영상이 돈다
    job = (await api.get(f"/api/videos/{waiting.id}/job")).json()
    assert (job["status"], job["queue_position"]) == ("queued", 1)  # 워커가 곧 꺼낸다


async def test_delete_stops_frame_fill_first(api, make, storyboard, tmp_path, monkeypatch) -> None:
    """채우는 중인 장면을 먼저 멈추고 지운다 — 지운 장면 폴더에 다시 쓰지 않는다."""
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    storyboard.gate = asyncio.Event()  # 첫 장 앞에서 기다린다
    row = await make.video()
    await make.job(row.id, JobStatus.done)
    await make.chapters(row.id, [(0.0, "하나", ["a"])])
    assert (await api.post(f"/api/videos/{row.id}/frames")).status_code == 202
    task = AnalysisService._frame_tasks[row.id]
    assert (await api.delete(f"/api/videos/{row.id}")).status_code == 204
    assert task.cancelled()
    assert row.id not in AnalysisService._frame_tasks
    storyboard.gate.set()
    await asyncio.sleep(0.05)
    assert not (tmp_path / "frames" / str(row.id)).exists()


async def test_delete_queued_moves_queue_up(api, make) -> None:
    ahead = await make.video()
    await make.job(ahead.id, JobStatus.running)
    rows = [await make.video() for _ in range(2)]
    t0 = datetime.now(UTC)
    for i, row in enumerate(rows):
        await make.job(row.id, JobStatus.queued, at=t0 + timedelta(seconds=i))
    last = f"/api/videos/{rows[1].id}/job"
    assert (await api.get(last)).json()["queue_position"] == 2
    assert (await api.delete(f"/api/videos/{rows[0].id}")).status_code == 204
    assert (await api.get(last)).json()["queue_position"] == 1  # 차례가 당겨진다


def _problem(r, status: int, kind: str) -> dict:
    # problem+json 모양 — 공통 넷(type · title · status · detail)과 content-type(API-001 2장)
    assert (r.status_code, r.headers["content-type"]) == (status, PROBLEM)
    body = r.json()
    assert (body["type"], body["status"]) == (f"urn:va:{kind}", status)
    assert body["title"] and body["detail"]
    return body


async def test_register_problems(api, key, verify, youtube, probe, tmp_path, monkeypatch) -> None:
    """등록이 내는 에러 — 종류마다 problem+json과 확장 필드. 화면이 시작 불가 판 · 배너를 고른다."""
    yt = {"source": "youtube", "url": URL}
    youtube.error = SourceUnavailable(reason="비공개 영상", hint=None)
    body = _problem(await api.post("/api/videos", json=yt), 502, "source-unavailable")
    assert (body["reason"], body["hint"]) == ("비공개 영상", None)

    youtube.error, youtube.duration = None, 15150  # 4:12:30
    body = _problem(await api.post("/api/videos", json=yt), 422, "video-too-long")
    assert (body["duration_sec"], body["max_sec"]) == (15150, 10800)

    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    local = {"source": "local", "path": "notes.txt"}
    body = _problem(await api.post("/api/videos", json=local), 422, "unsupported-file")
    assert body["reason"] and "mp4" in body["accepted"]
    local["path"] = "../a.mp4"
    _problem(await api.post("/api/videos", json=local), 422, "path-outside-inbox")
    (tmp_path / "marathon.mp4").write_bytes(b"x")
    probe.files = {"marathon.mp4": (15150, True)}
    local["path"] = "marathon.mp4"
    body = _problem(await api.post("/api/videos", json=local), 422, "video-too-long")
    assert body["duration_sec"] == 15150

    verify.fail = ReasonKind.auth  # 누를 때 키 확인이 실패한다 — 다른 무엇보다 먼저
    body = _problem(await api.post("/api/videos", json=yt), 503, "key-invalid")
    assert (body["reason_kind"], body["reason"]) == ("auth", "인증에 실패했습니다")
    assert body["checked_at"]

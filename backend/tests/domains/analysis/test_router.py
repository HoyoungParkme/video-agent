"""analysis/router — /api/videos/{id}/result · …/export(VA-API-001 3.5)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.config import config
from app.domains.analysis.service import AnalysisService
from app.domains.job.models import JobStatus
from app.domains.job.service import JobService
from app.domains.video.service import VideoService

T0 = datetime(2026, 9, 28, 1, 0, tzinfo=UTC)


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


async def _analyzed(db, make, summarizer, **kw):
    row = await make.video(**kw)
    await make.transcript(row.id, ["x"] * 30, step=100)
    video = VideoService.to_dto(row, await JobService(db).latest(row.id), 0)
    svc = AnalysisService(db, summarizer)
    await svc.generate_summary(video)
    await svc.generate_chapters(video)
    await make.job(row.id, JobStatus.done)
    return row


async def test_get_export(api, db, make, summarizer, env_file) -> None:
    row = await _analyzed(db, make, summarizer, title="RAG 서비스 1년 운영기")
    await make.turn(row.id, "어떤 DB를 썼어?", "pgvector를 썼다고 합니다.", cited=[60.0], at=T0)
    r = await api.get(f"/api/videos/{row.id}/export")
    assert r.status_code == 200
    body = r.json()
    assert (body["filename"], body["path"]) == (
        "RAG 서비스 1년 운영기",
        "data/export/RAG 서비스 1년 운영기.md",
    )
    assert body["markdown"].startswith("# RAG 서비스 1년 운영기\n")
    assert "## 질문 기록" not in body["markdown"]  # 기본은 넣지 않는다
    # 방법의 기본은 파일로 저장 — 스크립트 파일 링크와 함께 쓸 파일 둘
    assert body["markdown"].endswith("## 스크립트\n[[RAG 서비스 1년 운영기 스크립트]]\n")
    assert body["files"] == [
        {"kind": "note", "name": "RAG 서비스 1년 운영기.md"},
        {"kind": "script", "name": "RAG 서비스 1년 운영기 스크립트.md"},
    ]
    copy = (await api.get(f"/api/videos/{row.id}/export?method=clipboard")).json()
    assert "## 스크립트" not in copy["markdown"] and copy["files"] == []
    bad = await api.get(f"/api/videos/{row.id}/export?method=pdf")
    assert (bad.status_code, bad.json()["type"]) == (422, "urn:va:validation")
    chat = (await api.get(f"/api/videos/{row.id}/export?with_chat=true")).json()["markdown"]
    assert (
        "## 질문 기록\n**Q.** 어떤 DB를 썼어?\n**A.** pgvector를 썼다고 합니다.\n근거: [01:00]("
        in chat
    )


async def test_post_export(api, db, make, summarizer, env_file, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    row = await _analyzed(db, make, summarizer, title="제목")
    r = await api.post(f"/api/videos/{row.id}/export", json={"with_chat": True})
    assert r.status_code == 201
    assert r.json()["path"] == "data/export/제목.md"
    written = (tmp_path / "export" / "제목.md").read_text(encoding="utf-8")
    script = (tmp_path / "export" / "제목 스크립트.md").read_text(encoding="utf-8")
    assert written.endswith(
        "## 스크립트\n[[제목 스크립트]]\n\n## 질문 기록\n질문 기록이 없습니다\n"
    )
    assert script.startswith("# 제목 — 스크립트\n")  # 스크립트는 따로(API-001 v10)
    assert r.json()["bytes"] == len(written.encode()) + len(script.encode())  # 두 파일 합
    assert r.json()["images"] == 0
    assert [f["name"] for f in r.json()["files"]] == ["제목.md", "제목 스크립트.md"]


async def test_export_errors(api, db, make, summarizer, env_file, tmp_path, monkeypatch) -> None:
    row = await make.video()
    for method in ("GET", "POST"):
        r = await api.request(method, f"/api/videos/{row.id}/export", json={})
        assert (r.status_code, r.json()["type"]) == (409, "urn:va:result-not-ready")
        r = await api.request(method, "/api/videos/999/export", json={})
        assert (r.status_code, r.json()["type"]) == (404, "urn:va:not-found")
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    (tmp_path / "export").write_text("")  # 저장 폴더 자리에 파일
    done = await _analyzed(db, make, summarizer, title="제목")
    r = await api.post(f"/api/videos/{done.id}/export", json={})
    assert (r.status_code, r.json()["type"], r.json()["path"], r.json()["reason"]) == (
        500,
        "urn:va:export-failed",
        "data/export/제목 스크립트.md",  # 먼저 쓰는 스크립트에서 멈춘다
        "저장 폴더를 만들 수 없음(그 자리에 파일이 있다)",
    )

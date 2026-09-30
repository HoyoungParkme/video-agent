"""analysis/service — 인포그래픽(VA-MS-003 infographic_of …, 카드 D3). 이미지 포트는 가짜로."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.core.config import ImageQuality, config
from app.core.db import SessionLocal
from app.core.errors import (
    ExportFailed,
    InfographicBusy,
    KeyMissing,
    LlmUnavailable,
    NotFound,
    ResultNotReady,
)
from app.core.settings import settings
from app.domains.analysis import crud
from app.domains.analysis.models import InfographicRow, InfographicState, SummaryRow
from app.domains.analysis.schemas import ExportMethod
from app.domains.analysis.service import AnalysisService
from app.domains.job.models import JobStatus
from app.domains.job.service import JobService
from app.domains.video.service import VideoService

T1 = datetime(2026, 9, 30, 6, 0, tzinfo=UTC)
T2 = datetime(2026, 9, 30, 7, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path / "data"))
    return tmp_path / "data"


async def _video(db, make, status: JobStatus = JobStatus.done, **kw):
    row = await make.video(**kw)
    await make.job(row.id, status)
    return VideoService.to_dto(row, await JobService(db).latest(row.id), 0)


def _picture(data_dir: Path, video_id: int, at: datetime = T1) -> dict:
    """그린 그림의 컬럼과 파일 — data/infographics/{id}.png."""
    folder = data_dir / "infographics"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{video_id}.png"
    path.write_bytes(b"png")
    return {
        "model": "gpt-image-2",
        "quality": ImageQuality.low,
        "width": 1024,
        "height": 1536,
        "cost_usd": 0.006,
        "path": str(path),
        "created_at": at,
    }


async def _row(db, video_id: int, state: InfographicState, reason: str | None = None, **pic):
    db.add(InfographicRow(video_id=video_id, state=state, error_reason=reason, **pic))
    await db.commit()


# --- infographic_of


async def test_infographic_of_without_row_is_none(db, make) -> None:
    video = await _video(db, make)
    got = await AnalysisService(db).infographic_of(video)
    assert (got.state, got.image, got.error_reason) == ("none", None, None)


async def test_infographic_of_keeps_previous_picture(db, make, data_dir: Path) -> None:
    video = await _video(db, make)
    svc = AnalysisService(db)
    await _row(db, video.id, InfographicState.making, **_picture(data_dir, video.id))
    got = await svc.infographic_of(video)  # 다시 그리는 중 — 이전 그림이 보인다
    assert got.state == "making"
    assert got.image.url == f"/api/videos/{video.id}/infographic/image?v={int(T1.timestamp())}"
    assert (got.image.width, got.image.height, got.image.cost_usd) == (1024, 1536, 0.006)
    row = await crud.infographic(db, video.id)
    row.state, row.error_reason = InfographicState.failed, "OpenAI 서버 오류"
    await db.commit()
    got = await svc.infographic_of(video)  # 다시 그리기가 실패 — 이유와 이전 그림 둘 다
    assert (got.state, got.error_reason, got.image is not None) == (
        "failed",
        "OpenAI 서버 오류",
        True,
    )


async def test_infographic_of_url_changes_with_new_picture(db, make, data_dir: Path) -> None:
    video = await _video(db, make)
    await _row(db, video.id, InfographicState.done, **_picture(data_dir, video.id))
    svc = AnalysisService(db)
    before = (await svc.infographic_of(video)).image.url
    row = await crud.infographic(db, video.id)
    row.created_at = T2  # 다시 그렸다
    await db.commit()
    after = (await svc.infographic_of(video)).image.url
    assert before != after and after.endswith(f"?v={int(T2.timestamp())}")


async def test_infographic_of_missing_file_is_no_image(db, make, data_dir: Path) -> None:
    video = await _video(db, make)
    picture = _picture(data_dir, video.id)
    Path(picture["path"]).unlink()
    await _row(db, video.id, InfographicState.done, **picture)
    got = await AnalysisService(db).infographic_of(video)
    assert (got.state, got.image) == ("done", None)


async def test_infographic_of_before_result_is_not_ready(db, make) -> None:
    video = await _video(db, make, status=JobStatus.running)
    with pytest.raises(ResultNotReady):
        await AnalysisService(db).infographic_of(video)


# --- draw_infographic


async def _analyzed(db, make, **kw):
    """결과가 다 있는 영상 — 스크립트 · 요약 · 인사이트 · 챕터."""
    video = await _video(db, make, title="RAG 서비스 1년 운영기", **kw)
    await make.transcript(video.id, ["스크립트 줄 비밀"] * 5, step=100)
    db.add(SummaryRow(video_id=video.id, one_liner="검색 품질을 올린 기록", model="gpt-5-mini"))
    await db.commit()
    await make.chapters(video.id, [(0.0, "발표자 소개", ["a"]), (200.0, "운영과 리뷰", ["b"])])
    return video


async def test_draw_done_writes_picture_and_columns(
    db, make, image_maker, env_file, data_dir
) -> None:
    video = await _analyzed(db, make)
    await _row(db, video.id, InfographicState.making)
    choice = settings.current_models()
    await AnalysisService(db, image_maker=image_maker).draw_infographic(video.id, choice)
    await db.refresh(row := await crud.infographic(db, video.id))
    assert (row.state, row.model, row.quality, row.width, row.height) == (
        "done",
        "gpt-image-2",
        "low",
        1024,
        1536,
    )
    assert row.cost_usd == choice.image_quality.price_usd == 0.006  # 그 품질의 한 장 값
    assert row.path == str(data_dir / "infographics" / f"{video.id}.png")
    assert (data_dir / "infographics" / f"{video.id}.png").read_bytes() == b"png-new"
    assert sorted(p.name for p in (data_dir / "infographics").iterdir()) == [f"{video.id}.png"]
    brief, model, quality = image_maker.calls[0]
    assert (brief.title, brief.one_liner, brief.chapter_titles) == (
        "RAG 서비스 1년 운영기",
        "검색 품질을 올린 기록",
        ["발표자 소개", "운영과 리뷰"],
    )
    assert "스크립트 줄 비밀" not in repr(brief)  # 스크립트는 보내지 않는다
    assert (model, quality) == ("gpt-image-2", "low")


async def test_draw_failure_keeps_previous_picture(
    db, make, image_maker, env_file, data_dir
) -> None:
    video = await _analyzed(db, make)
    await _row(db, video.id, InfographicState.making, **_picture(data_dir, video.id))
    image_maker.fail = LlmUnavailable(reason="OpenAI 연결 시간 초과")
    svc = AnalysisService(db, image_maker=image_maker)
    await svc.draw_infographic(video.id, settings.current_models())
    await db.refresh(row := await crud.infographic(db, video.id))
    assert (row.state, row.error_reason, row.created_at) == ("failed", "OpenAI 연결 시간 초과", T1)
    assert (data_dir / "infographics" / f"{video.id}.png").read_bytes() == b"png"  # 이전 그림
    assert sorted(p.name for p in (data_dir / "infographics").iterdir()) == [f"{video.id}.png"]


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (OSError(28, "No space left"), "그림 파일을 저장하지 못함"),
        (ValueError("?"), "알 수 없는 오류"),
    ],
)
async def test_draw_other_failures(db, make, image_maker, env_file, error, reason) -> None:
    video = await _analyzed(db, make)
    await _row(db, video.id, InfographicState.making)
    image_maker.fail = error
    await AnalysisService(db, image_maker=image_maker).draw_infographic(
        video.id, settings.current_models()
    )
    await db.refresh(row := await crud.infographic(db, video.id))
    assert (row.state, row.error_reason, row.path) == ("failed", reason, None)


async def test_draw_again_replaces_picture(db, make, image_maker, env_file, data_dir) -> None:
    video = await _analyzed(db, make)
    await _row(db, video.id, InfographicState.making, **_picture(data_dir, video.id))
    await AnalysisService(db, image_maker=image_maker).draw_infographic(
        video.id, settings.current_models()
    )
    await db.refresh(row := await crud.infographic(db, video.id))
    assert row.state == "done" and row.created_at > T1  # 새 그림 — 주소의 ?v=가 바뀐다
    assert (data_dir / "infographics" / f"{video.id}.png").read_bytes() == b"png-new"


# --- start_infographic


async def test_start_returns_at_once_and_is_busy_while_drawing(
    db, make, image_maker, key, data_dir
) -> None:
    video = await _analyzed(db, make)
    image_maker.gate = asyncio.Event()  # 오래 걸리는 그리기
    svc = AnalysisService(db, image_maker=image_maker)
    got = await svc.start_infographic(video)
    assert (got.state, got.image) == ("making", None)  # 다 그릴 때까지 기다리지 않는다
    task = AnalysisService._image_tasks[video.id]
    assert not task.done()
    with pytest.raises(InfographicBusy):  # 그리는 중에 또
        await svc.start_infographic(video)
    image_maker.gate.set()
    await task
    assert (await svc.infographic_of(video)).state == "done"
    assert video.id not in AnalysisService._image_tasks


async def test_start_again_shows_previous_picture(db, make, image_maker, key, data_dir) -> None:
    video = await _analyzed(db, make)
    await _row(db, video.id, InfographicState.failed, "이전 실패", **_picture(data_dir, video.id))
    image_maker.gate = asyncio.Event()
    got = await AnalysisService(db, image_maker=image_maker).start_infographic(video)
    assert (got.state, got.error_reason, got.image is not None) == ("making", None, True)
    image_maker.gate.set()
    await AnalysisService._image_tasks[video.id]


async def test_start_without_key_makes_no_row(db, make, image_maker, env_file, verify) -> None:
    video = await _analyzed(db, make)
    with pytest.raises(KeyMissing):
        await AnalysisService(db, image_maker=image_maker).start_infographic(video)
    assert await crud.infographic(db, video.id) is None
    assert image_maker.calls == [] and video.id not in AnalysisService._image_tasks


async def test_start_twice_at_once_only_one(db, make, image_maker, key, data_dir) -> None:
    video = await _analyzed(db, make)
    image_maker.gate = asyncio.Event()

    async def start():
        async with SessionLocal() as session:
            return await AnalysisService(session, image_maker=image_maker).start_infographic(video)

    got = await asyncio.gather(start(), start(), return_exceptions=True)
    assert sorted(type(g).__name__ for g in got) == ["Infographic", "InfographicBusy"]
    image_maker.gate.set()
    await AnalysisService._image_tasks[video.id]
    assert len(image_maker.calls) == 1


async def test_start_before_result_is_not_ready(db, make, image_maker, key) -> None:
    video = await _video(db, make, status=JobStatus.running)
    with pytest.raises(ResultNotReady):
        await AnalysisService(db, image_maker=image_maker).start_infographic(video)


# --- infographic_file · fail_orphans


async def test_infographic_file(db, make, image_maker, key, data_dir) -> None:
    video = await _analyzed(db, make)
    svc = AnalysisService(db, image_maker=image_maker)
    with pytest.raises(NotFound) as e:  # 만든 적 없음
        await svc.infographic_file(video.id)
    assert e.value.extra == {"resource": "infographic", "id": video.id}
    image_maker.gate = asyncio.Event()
    await svc.start_infographic(video)
    with pytest.raises(NotFound):  # 처음 그리는 중 — 그림이 없다
        await svc.infographic_file(video.id)
    image_maker.gate.set()
    await AnalysisService._image_tasks[video.id]
    path = await svc.infographic_file(video.id)
    assert path == str(data_dir / "infographics" / f"{video.id}.png")
    image_maker.gate = asyncio.Event()
    await svc.start_infographic(video)  # 다시 그리는 중 — 이전 그림
    assert await svc.infographic_file(video.id) == path
    image_maker.gate.set()
    await AnalysisService._image_tasks[video.id]


async def test_fail_orphans(db, make, data_dir) -> None:
    drawing, again, done = [await _video(db, make) for _ in range(3)]
    await _row(db, drawing.id, InfographicState.making)
    await _row(db, again.id, InfographicState.making, **_picture(data_dir, again.id))
    await _row(db, done.id, InfographicState.done, **_picture(data_dir, done.id))
    assert await AnalysisService(db).fail_orphans() == 2
    rows = {v.id: await crud.infographic(db, v.id) for v in (drawing, again, done)}
    assert (rows[drawing.id].state, rows[drawing.id].error_reason) == (
        "failed",
        "서버가 다시 시작됨",
    )
    assert (rows[again.id].state, rows[again.id].created_at) == ("failed", T1)  # 이전 그림 그대로
    assert (rows[done.id].state, rows[done.id].error_reason) == ("done", None)


# --- result_of


async def test_result_carries_infographic(db, make, data_dir, queries) -> None:
    video = await _analyzed(db, make)
    svc = AnalysisService(db)
    assert (await svc.result_of(video)).infographic.state == "none"
    await _row(db, video.id, InfographicState.done, **_picture(data_dir, video.id))
    queries.clear()
    got = await svc.result_of(video)
    assert len(queries) <= 8  # 쿼리 여덟을 넘지 않는다
    assert got.infographic == await svc.infographic_of(video)  # 같은 모양
    assert got.infographic.image.url.endswith(f"?v={int(T1.timestamp())}")


# --- 내보내기


async def test_export_file_lists_infographic_last(db, make, env_file, data_dir) -> None:
    video = await _analyzed(db, make)
    svc = AnalysisService(db)
    got = await svc.export_markdown(video, False, [], ExportMethod.file)
    assert [f.kind for f in got.files] == ["note", "script"]  # 그림이 없으면 둘
    await _row(db, video.id, InfographicState.done, **_picture(data_dir, video.id))
    got = await svc.export_markdown(video, False, [], ExportMethod.file)
    assert [(f.kind, f.name) for f in got.files][-1] == (
        "infographic",
        "RAG 서비스 1년 운영기 인포그래픽.png",
    )
    assert "![[RAG 서비스 1년 운영기 인포그래픽.png]]" in got.markdown
    copied = await svc.export_markdown(video, False, [], ExportMethod.clipboard)
    assert copied.files == [] and "인포그래픽" not in copied.markdown


async def test_export_to_file_copies_infographic(db, make, env_file, data_dir) -> None:
    video = await _analyzed(db, make)
    await _row(db, video.id, InfographicState.done, **_picture(data_dir, video.id))
    got = await AnalysisService(db).export_to_file(video, False, [])
    folder = data_dir / "export"
    name = "RAG 서비스 1년 운영기"
    assert (folder / f"{name} 인포그래픽.png").read_bytes() == b"png"
    assert got.images == 1
    assert sorted(f.name for f in got.files) == sorted(p.name for p in folder.iterdir())
    assert f"![[{name} 인포그래픽.png]]" in (folder / f"{name}.md").read_text(encoding="utf-8")


async def test_export_infographic_gone_meanwhile_is_export_failed(
    db, make, env_file, data_dir, monkeypatch
) -> None:
    video = await _analyzed(db, make)
    await _row(db, video.id, InfographicState.done, **_picture(data_dir, video.id))
    svc = AnalysisService(db)

    async def gone(video_id: int) -> str:
        raise NotFound(resource="infographic", id=video_id)

    monkeypatch.setattr(svc, "infographic_file", gone)
    with pytest.raises(ExportFailed) as e:
        await svc.export_to_file(video, False, [])
    assert e.value.extra == {
        "path": "data/export/RAG 서비스 1년 운영기 인포그래픽.png",
        "reason": "그림 파일을 찾을 수 없음",
    }

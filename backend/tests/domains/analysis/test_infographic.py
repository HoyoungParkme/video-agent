"""analysis/service — 인포그래픽(VA-MS-003 infographic_of …, 카드 D3). 이미지 포트는 가짜로."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.core.config import ImageQuality, config
from app.core.errors import ResultNotReady
from app.domains.analysis import crud
from app.domains.analysis.models import InfographicRow, InfographicState
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

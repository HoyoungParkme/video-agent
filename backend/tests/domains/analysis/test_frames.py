"""analysis/service — 대표 장면(VA-MS-003 make_frames …, 카드 D2). 장면 포트는 가짜로."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.core.config import config
from app.domains.analysis import crud
from app.domains.analysis.models import FrameSource
from app.domains.analysis.service import AnalysisService
from app.domains.job.models import JobStatus
from app.domains.job.service import JobService
from app.domains.video.models import SourceKind
from app.domains.video.service import VideoService

CHAPTERS = [(0.0, "하나", ["a"]), (600.0, "둘", ["b"]), (1200.0, "셋", ["c"])]


@pytest.fixture(autouse=True)
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path / "inbox"))
    return tmp_path


async def _video(db, make, **kw):
    row = await make.video(**kw)
    await make.job(row.id, JobStatus.done)
    await make.chapters(row.id, CHAPTERS)
    return VideoService.to_dto(row, await JobService(db).latest(row.id), 0)


def _svc(db, storyboard, local_frames) -> AnalysisService:
    return AnalysisService(db, storyboard=storyboard, local_frames=local_frames)


async def _rows(db, video_id: int):
    return [(f.path is not None, f.sec, f.source) for f in await crud.frames(db, video_id)]


async def test_all_chapters_got(db, make, storyboard, local_frames, data_dir: Path) -> None:
    video = await _video(db, make)
    await _svc(db, storyboard, local_frames).make_frames(video)
    frames = await crud.frames(db, video.id)
    assert [(f.sec, f.source, f.width, f.height) for f in frames] == [
        (1.0, FrameSource.storyboard, 320, 180),
        (601.0, FrameSource.storyboard, 320, 180),
        (1201.0, FrameSource.storyboard, 320, 180),
    ]
    folder = data_dir / "data" / "frames" / str(video.id)
    assert [f.path for f in frames] == [str(folder / f"{i}.jpg") for i in (1, 2, 3)]
    assert sorted(p.name for p in folder.iterdir()) == ["1.jpg", "2.jpg", "3.jpg"]  # 옮겼다
    assert storyboard.calls == [(video.source_id, [0.0, 600.0, 1200.0], str(folder))]
    assert local_frames.calls == []


async def test_none_is_a_row_without_picture(db, make, storyboard, local_frames) -> None:
    video = await _video(db, make)
    storyboard.none_at = {1}
    await _svc(db, storyboard, local_frames).make_frames(video)
    assert [got for got, *_ in await _rows(db, video.id)] == [True, False, True]


async def test_port_failure_leaves_null_rows_and_no_error(
    db, make, storyboard, local_frames
) -> None:
    video = await _video(db, make)
    storyboard.fail_at = 1  # 첫 장 뒤에 통째로 실패
    await _svc(db, storyboard, local_frames).make_frames(video)  # 밖으로 나오지 않는다
    assert await _rows(db, video.id) == [
        (True, 1.0, FrameSource.storyboard),
        (False, None, None),
        (False, None, None),
    ]
    assert video.id not in AnalysisService._making


async def test_tried_chapters_are_skipped(db, make, storyboard, local_frames) -> None:
    video = await _video(db, make)
    first = (await crud.chapter_rows(db, video.id))[0]
    await crud.add_frame(db, first.id)  # 해 봤지만 없다
    await db.commit()
    await _svc(db, storyboard, local_frames).make_frames(video)
    assert storyboard.calls[0][1] == [600.0, 1200.0]
    storyboard.calls.clear()
    await _svc(db, storyboard, local_frames).make_frames(video)  # 다 해 봤다 — 부르지 않는다
    assert storyboard.calls == []


async def test_local_video_goes_to_local_frames_with_path(
    db, make, storyboard, local_frames, data_dir: Path
) -> None:
    video = await _video(
        db, make, source_kind=SourceKind.local, origin="워크숍 녹화.mp4", channel=None
    )
    await _svc(db, storyboard, local_frames).make_frames(video)
    assert local_frames.calls[0][0] == str(data_dir / "inbox" / "워크숍 녹화.mp4")
    assert storyboard.calls == []
    assert {src for _, _, src in await _rows(db, video.id)} == {FrameSource.local_frame}


async def test_making_while_running_and_cleared_on_cancel(
    db, make, storyboard, local_frames
) -> None:
    video = await _video(db, make)
    storyboard.gate = asyncio.Event()
    task = asyncio.create_task(_svc(db, storyboard, local_frames).make_frames(video))
    for _ in range(100):
        if storyboard.calls:
            break
        await asyncio.sleep(0.01)
    assert video.id in AnalysisService._making  # 도는 동안
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert video.id not in AnalysisService._making  # 취소돼도 빠진다

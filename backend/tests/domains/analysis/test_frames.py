"""analysis/service — 대표 장면(VA-MS-003 make_frames …, 카드 D2). 장면 포트는 가짜로."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.core.config import config
from app.core.errors import ExportFailed, FramesUnavailable, NotFound, ResultNotReady
from app.domains.analysis import crud
from app.domains.analysis.models import FrameSource, SummaryRow
from app.domains.analysis.schemas import ExportMethod, FramesState
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


# --- frames_state


async def _state(db, video) -> FramesState:
    chapters, frames = await crud.chapter_rows(db, video.id), await crud.frames(db, video.id)
    return AnalysisService.frames_state(video, chapters, frames)


async def test_state_making_while_running(db, make) -> None:
    video = await _video(db, make)
    first = (await crud.chapter_rows(db, video.id))[0]
    await crud.add_frame(db, first.id)
    await db.commit()
    AnalysisService._making.add(video.id)
    assert await _state(db, video) == FramesState.making  # 행이 일부여도


async def test_state_done_when_every_chapter_tried(db, make) -> None:
    video = await _video(db, make)
    for c in await crud.chapter_rows(db, video.id):
        await crud.add_frame(db, c.id)  # 그림 없는 행도 「해 봤다」
    await db.commit()
    assert await _state(db, video) == FramesState.done


async def test_state_youtube_without_or_partial_rows_is_absent(db, make) -> None:
    video = await _video(db, make)
    assert await _state(db, video) == FramesState.absent
    first = (await crud.chapter_rows(db, video.id))[0]
    await crud.add_frame(db, first.id)  # 채우다 죽었다
    await db.commit()
    assert await _state(db, video) == FramesState.absent


async def test_state_audio_file_is_unavailable(db, make, data_dir: Path) -> None:
    (data_dir / "inbox").mkdir()
    (data_dir / "inbox" / "memo.m4a").write_bytes(b"audio")
    video = await _video(db, make, source_kind=SourceKind.local, origin="memo.m4a", channel=None)
    assert await _state(db, video) == FramesState.unavailable


async def test_state_moved_original_is_unavailable(db, make, data_dir: Path) -> None:
    video = await _video(db, make, source_kind=SourceKind.local, origin="옮긴 파일.mp4")
    assert await _state(db, video) == FramesState.unavailable
    (data_dir / "inbox").mkdir()
    (data_dir / "inbox" / "옮긴 파일.mp4").write_bytes(b"video")
    assert await _state(db, video) == FramesState.absent  # 원본이 있으면 채울 수 있다


async def test_state_done_even_if_original_is_gone(db, make) -> None:
    # 원본이 없어도 챕터마다 행이 있으면 끝난 것이다(올린 사본을 지운 영상도 같다)
    video = await _video(db, make, source_kind=SourceKind.local, origin="없는 파일.mp4")
    for c in await crud.chapter_rows(db, video.id):
        await crud.add_frame(db, c.id)
    await db.commit()
    assert await _state(db, video) == FramesState.done


# --- fill_frames


async def test_fill_absent_starts_one_task_until_done(db, make, storyboard, local_frames) -> None:
    video = await _video(db, make)
    svc = _svc(db, storyboard, local_frames)
    got = await svc.fill_frames(video)
    assert (got.state, got.frames) == (FramesState.making, [])  # 202 — 바로 돌려준다
    task = AnalysisService._frame_tasks[video.id]
    again = await svc.fill_frames(video)  # 곧바로 다시 불러도 태스크는 하나
    assert again.state == FramesState.making
    assert AnalysisService._frame_tasks[video.id] is task
    await task
    assert video.id not in AnalysisService._frame_tasks
    assert await _state(db, video) == FramesState.done
    assert len(storyboard.calls) == 1
    assert [got for got, *_ in await _rows(db, video.id)] == [True, True, True]


async def test_fill_done_starts_nothing(db, make, storyboard, local_frames) -> None:
    video = await _video(db, make)
    for c in await crud.chapter_rows(db, video.id):
        await crud.add_frame(db, c.id)
    await db.commit()
    got = await _svc(db, storyboard, local_frames).fill_frames(video)
    assert got.state == FramesState.done
    assert AnalysisService._frame_tasks == {} and storyboard.calls == []


async def test_fill_task_failure_is_logged_not_raised(db, make, storyboard, local_frames) -> None:
    video = await _video(db, make)
    storyboard.fail_at = 0  # 스토리보드가 없다 — 챕터마다 그림 없는 행
    await _svc(db, storyboard, local_frames).fill_frames(video)
    await AnalysisService._frame_tasks[video.id]
    assert await _state(db, video) == FramesState.done  # 다시 채우지 않는다
    assert [got for got, *_ in await _rows(db, video.id)] == [False, False, False]


async def test_fill_audio_file_is_unavailable(db, make, storyboard, local_frames, data_dir) -> None:
    (data_dir / "inbox").mkdir()
    (data_dir / "inbox" / "memo.m4a").write_bytes(b"audio")
    video = await _video(db, make, source_kind=SourceKind.local, origin="memo.m4a", channel=None)
    with pytest.raises(FramesUnavailable) as e:
        await _svc(db, storyboard, local_frames).fill_frames(video)
    assert e.value.extra == {"reason": "음성 파일이라 장면이 없어요"}


async def test_fill_missing_original_is_unavailable(db, make, storyboard, local_frames) -> None:
    video = await _video(db, make, source_kind=SourceKind.local, origin="옮긴 파일.mp4")
    with pytest.raises(FramesUnavailable) as e:
        await _svc(db, storyboard, local_frames).fill_frames(video)
    assert e.value.extra == {"reason": "원본 파일을 찾을 수 없어요"}


async def test_fill_while_analyzing_is_not_ready(db, make, storyboard, local_frames) -> None:
    row = await make.video()
    await make.job(row.id, JobStatus.running)
    video = VideoService.to_dto(row, await JobService(db).latest(row.id), 0)
    with pytest.raises(ResultNotReady):
        await _svc(db, storyboard, local_frames).fill_frames(video)


# --- frames_of


async def test_frames_of_lists_only_pictures_with_files(
    db, make, storyboard, local_frames, queries
) -> None:
    video = await _video(db, make)
    storyboard.none_at = {1}
    svc = _svc(db, storyboard, local_frames)
    await svc.make_frames(video)
    rows = await crud.frames(db, video.id)
    Path(rows[2].path).unlink()  # 파일이 지워진 행
    queries.clear()
    got = await svc.frames_of(video)
    assert got.state == FramesState.done
    assert [(f.chapter_seq, f.sec, f.url) for f in got.frames] == [
        (1, 1.0, f"/api/videos/{video.id}/frames/1")
    ]  # 그림 없는 행 · 파일이 없는 행은 없다
    assert len(queries) == 2  # 챕터 · 장면


async def test_frames_of_while_analyzing_is_not_ready(db, make) -> None:
    row = await make.video()
    await make.job(row.id, JobStatus.failed)
    video = VideoService.to_dto(row, await JobService(db).latest(row.id), 0)
    with pytest.raises(ResultNotReady):
        await AnalysisService(db).frames_of(video)


# --- frame_progress


async def _four_with_two_rows(db, make):
    row = await make.video()
    await make.job(row.id, JobStatus.running)
    await make.chapters(row.id, [(i * 600.0, f"챕터 {i}", []) for i in range(4)])
    first, second, *_ = await crud.chapter_rows(db, row.id)
    await crud.add_frame(db, first.id, 1.0, FrameSource.storyboard, 320, 180, "/d/1.jpg")
    await crud.add_frame(db, second.id)  # 얻지 못함
    await db.commit()
    return row.id


async def test_progress_cells_while_running(db, make, queries) -> None:
    video_id = await _four_with_two_rows(db, make)
    AnalysisService._making.add(video_id)
    queries.clear()
    got = await AnalysisService(db).frame_progress(video_id)
    assert [(i.state, i.url) for i in got.items] == [
        ("done", f"/api/videos/{video_id}/frames/1"),
        ("missing", None),
        ("in_flight", None),
        ("waiting", None),
    ]
    assert (got.done, got.total) == (1, 4)
    assert len(queries) == 2


async def test_progress_not_running_has_no_in_flight(db, make) -> None:
    video_id = await _four_with_two_rows(db, make)
    got = await AnalysisService(db).frame_progress(video_id)
    assert [i.state for i in got.items] == ["done", "missing", "waiting", "waiting"]


async def test_progress_without_chapters_is_zero(db, make) -> None:
    row = await make.video()
    got = await AnalysisService(db).frame_progress(row.id)
    assert (got.done, got.total, got.items) == (0, 0, [])


# --- frame_file


async def test_frame_file(db, make, storyboard, local_frames) -> None:
    video = await _video(db, make)
    storyboard.none_at = {1}
    svc = _svc(db, storyboard, local_frames)
    await svc.make_frames(video)
    path = await svc.frame_file(video.id, 1)
    assert Path(path).read_bytes() == b"jpeg"
    for vid, seq in (
        (video.id, 2),
        (video.id, 9),
        (video.id + 1, 1),
    ):  # 그림 없음 · 없는 챕터 · 다른 영상
        with pytest.raises(NotFound) as e:
            await svc.frame_file(vid, seq)
        assert e.value.extra == {"resource": "frame", "id": seq}
    Path(path).unlink()  # 파일이 지워졌다
    with pytest.raises(NotFound):
        await svc.frame_file(video.id, 1)


# --- cancel_tasks


async def test_cancel_stops_only_that_videos_fill(db, make, storyboard, local_frames) -> None:
    one, other = await _video(db, make), await _video(db, make)
    storyboard.gate = asyncio.Event()  # 첫 장 앞에서 붙든다
    svc = _svc(db, storyboard, local_frames)
    await svc.fill_frames(one)
    await svc.fill_frames(other)
    task = AnalysisService._frame_tasks[one.id]
    await svc.cancel_tasks(one.id)
    assert task.cancelled()
    assert one.id not in AnalysisService._frame_tasks and one.id not in AnalysisService._making
    assert other.id in AnalysisService._frame_tasks  # 다른 영상은 그대로
    storyboard.gate.set()
    await AnalysisService._frame_tasks[other.id]
    assert await crud.frames(db, one.id) == []  # 멈춘 영상은 행을 쓰지 않았다


async def test_cancel_without_task_is_quiet(db, make) -> None:
    await AnalysisService(db).cancel_tasks(12345)


# --- result_of의 장면


async def test_result_has_frame_only_where_picture_and_file(
    db, make, storyboard, local_frames, youtube, env_file
) -> None:
    video = await _video(db, make)
    await make.transcript(video.id, ["x"] * 30, step=100)
    db.add(SummaryRow(video_id=video.id, one_liner="한 줄", model="gpt-5-mini"))
    await db.commit()
    storyboard.none_at = {1}
    svc = _svc(db, storyboard, local_frames)
    await svc.make_frames(video)
    Path((await crud.frames(db, video.id))[2].path).unlink()  # 셋째 파일이 지워졌다
    result = await svc.result_of(video)
    assert result.frames_state == FramesState.done
    first, second, third = result.chapters
    assert first.frame is not None and first.frame.url == f"/api/videos/{video.id}/frames/1"
    assert (first.frame.sec, first.frame.source) == (1.0, FrameSource.storyboard)
    assert second.frame is None and third.frame is None  # 그림 없는 행 · 파일 없는 행


# --- 내보내기의 장면


async def _with_frames(db, make, storyboard, local_frames, none_at: set[int]):
    """결과가 다 있는 영상(챕터 셋)과 장면 — none_at 차례는 장면이 없다."""
    video = await _video(db, make, title="RAG 운영기")
    await make.transcript(video.id, ["x"] * 30, step=100)
    db.add(SummaryRow(video_id=video.id, one_liner="한 줄", model="gpt-5-mini"))
    await db.commit()
    storyboard.none_at = none_at
    svc = _svc(db, storyboard, local_frames)
    await svc.make_frames(video)
    return video, svc


async def test_export_file_lists_frames_in_chapter_order(
    db, make, storyboard, local_frames, env_file
) -> None:
    video, svc = await _with_frames(db, make, storyboard, local_frames, {1})
    got = await svc.export_markdown(video, False, [], ExportMethod.file)
    assert [(f.kind, f.name) for f in got.files] == [
        ("note", "RAG 운영기.md"),
        ("script", "RAG 운영기 스크립트.md"),
        ("frame", "RAG 운영기 00-00.jpg"),
        ("frame", "RAG 운영기 20-00.jpg"),
    ]
    assert got.markdown.count("![[RAG 운영기 ") == 2  # 장면이 있는 챕터에만
    copied = await svc.export_markdown(video, False, [], ExportMethod.clipboard)
    assert copied.files == [] and "![[" not in copied.markdown


async def test_export_without_frames_has_two_files(
    db, make, storyboard, local_frames, env_file
) -> None:
    video, svc = await _with_frames(db, make, storyboard, local_frames, {0, 1, 2})
    got = await svc.export_markdown(video, False, [], ExportMethod.file)
    assert [f.kind for f in got.files] == ["note", "script"]


async def test_export_to_file_copies_frames_beside_note(
    db, make, storyboard, local_frames, env_file, data_dir: Path
) -> None:
    video, svc = await _with_frames(db, make, storyboard, local_frames, {1})
    got = await svc.export_to_file(video, False, [])
    folder = data_dir / "data" / "export"
    assert sorted(p.name for p in folder.iterdir()) == [
        "RAG 운영기 00-00.jpg",
        "RAG 운영기 20-00.jpg",
        "RAG 운영기 스크립트.md",
        "RAG 운영기.md",
    ]  # 임시 파일이 남지 않는다
    assert got.images == 2
    assert [f.name for f in got.files][2:] == ["RAG 운영기 00-00.jpg", "RAG 운영기 20-00.jpg"]
    note = (folder / "RAG 운영기.md").read_text(encoding="utf-8")
    assert "![[RAG 운영기 00-00.jpg]]" in note and "![[RAG 운영기 20-00.jpg]]" in note
    assert (folder / "RAG 운영기 00-00.jpg").read_bytes() == b"jpeg"
    assert got.bytes == sum(p.stat().st_size for p in folder.iterdir())


async def test_export_frame_gone_meanwhile_is_export_failed(
    db, make, storyboard, local_frames, env_file, data_dir: Path, monkeypatch
) -> None:
    # 결과를 읽은 뒤 그림이 없어졌다 — 없음(404)이 아니라 저장 실패로, 그 그림의 보일 경로와 함께
    video, svc = await _with_frames(db, make, storyboard, local_frames, set())

    async def gone(video_id: int, seq: int) -> str:
        raise NotFound(resource="frame", id=seq)

    monkeypatch.setattr(svc, "frame_file", gone)
    with pytest.raises(ExportFailed) as e:
        await svc.export_to_file(video, False, [])
    assert e.value.extra == {
        "path": "data/export/RAG 운영기 00-00.jpg",
        "reason": "그림 파일을 찾을 수 없음",
    }

    async def missing(video_id: int, seq: int) -> str:
        return str(data_dir / "없는 그림.jpg")  # 행은 있는데 읽는 사이 지워졌다

    monkeypatch.setattr(svc, "frame_file", missing)
    with pytest.raises(ExportFailed) as e:
        await svc.export_to_file(video, False, [])
    assert e.value.extra["reason"] == "그림 파일을 찾을 수 없음"


async def test_export_frame_copy_failure_names_that_picture(
    db, make, storyboard, local_frames, env_file, data_dir: Path
) -> None:
    video, svc = await _with_frames(db, make, storyboard, local_frames, set())
    (data_dir / "data" / "export" / "RAG 운영기 10-00.jpg").mkdir(parents=True)  # 그 자리에 폴더
    with pytest.raises(ExportFailed) as e:
        await svc.export_to_file(video, False, [])
    assert e.value.extra["path"] == "data/export/RAG 운영기 10-00.jpg"

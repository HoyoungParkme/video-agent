"""video/service — 등록 · 목록 · 하나 · 정보 조회 · 상태 계산(VA-MS-001). B1 몫(로컬 정보 조회는 B2)."""

from __future__ import annotations

import ast
import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.core.config import config
from app.core.db import SessionLocal
from app.core.errors import (
    KeyMissing,
    NotFound,
    NotImplementedYet,
    PathOutsideInbox,
    SourceUnavailable,
    UnsupportedFile,
    UrlInvalid,
    VideoTooLong,
)
from app.domains.job.models import JobStatus
from app.domains.job.service import JobService
from app.domains.video.models import VideoRow
from app.domains.video.schemas import LocalSource, YouTubeSource
from app.domains.video.service import VideoService

APP = Path(__file__).resolve().parents[3] / "app"
WATCH = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
T0 = datetime(2026, 9, 23, 3, 0, tzinfo=UTC)


def yt(url: str = WATCH) -> YouTubeSource:
    return YouTubeSource(source="youtube", url=url)


async def _count(db) -> int:
    return await db.scalar(select(func.count()).select_from(VideoRow))


# --- to_dto


async def test_to_dto_status(db, make) -> None:
    row = await make.video()
    assert VideoService.to_dto(row, None, 0).status == "registered"
    jobs = JobService(db)
    for status, expected in [
        (JobStatus.queued, "in_progress"),  # 대기 중도 진행 중
        (JobStatus.running, "in_progress"),
        (JobStatus.failed, "failed"),
        (JobStatus.done, "analyzed"),
    ]:
        v = await make.video()
        await make.job(v.id, status)
        summary = await jobs.latest(v.id)
        video = VideoService.to_dto(v, summary, 2)
        assert video.status == expected
        assert video.chat_turn_count == 2
        if status == JobStatus.done:
            assert video.analyzed_at == summary.finished_at
        else:
            assert video.analyzed_at is None


def test_status_is_made_only_in_to_dto() -> None:
    """이 함수 말고 status를 만드는 곳이 없다 — VideoStatus 값을 쓰는 함수가 to_dto 하나."""
    users = []
    for path in APP.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in ast.walk(tree):
            if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
                names = {
                    n.value.id
                    for n in ast.walk(fn)
                    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                }
                if "VideoStatus" in names:
                    users.append(f"{path.relative_to(APP)}:{fn.name}")
    assert users == ["domains/video/service.py:to_dto"]


# --- info_of


async def test_info_of_youtube_asks_port(db, youtube) -> None:
    info = await VideoService(db, youtube).info_of(yt())
    assert youtube.calls == [WATCH]
    assert (info.source_id, info.has_captions, info.caption_kind) == ("dQw4w9WgXcQ", True, "manual")


async def test_info_of_youtube_unavailable(db, youtube, unavailable) -> None:
    youtube.error = unavailable
    with pytest.raises(SourceUnavailable) as e:
        await VideoService(db, youtube).info_of(yt())
    assert e.value.extra["reason"] == "비공개 영상이에요"


async def test_info_of_local_is_stub(db, youtube) -> None:
    with pytest.raises(NotImplementedYet):
        await VideoService(db, youtube).info_of(LocalSource(source="local", path="a.mp4"))


# --- register


async def test_register_without_key_touches_nothing(db, youtube, env_file, verify) -> None:
    with pytest.raises(KeyMissing):
        await VideoService(db, youtube).register(yt())
    assert youtube.calls == []  # YouTube에 닿지 않는다
    assert await _count(db) == 0


async def test_register_checks_key_each_time(db, youtube, key, verify) -> None:
    await VideoService(db, youtube).register(yt())
    assert len(verify.calls) == 1  # 분석 버튼을 누를 때 확인한다


async def test_register_new_video(db, youtube, key) -> None:
    video = await VideoService(db, youtube).register(yt())
    assert (video.status, video.source_id, video.title) == (
        "registered",
        "dQw4w9WgXcQ",
        "자막 있는 강의",
    )
    assert (video.has_captions, video.caption_language, video.caption_kind) == (
        True,
        "ko",
        "manual",
    )
    assert video.created_at is not None
    assert video.chat_turn_count == 0


async def test_register_same_video_other_url(db, youtube, key) -> None:
    svc = VideoService(db, youtube)
    first = await svc.register(yt("https://youtu.be/dQw4w9WgXcQ"))
    second = await svc.register(yt(WATCH))
    shorts = await svc.register(yt("https://m.youtube.com/shorts/dQw4w9WgXcQ"))
    assert first.id == second.id == shorts.id
    assert await _count(db) == 1


async def test_register_url_invalid(db, youtube, key) -> None:
    for url in [
        "https://vimeo.com/123456",
        "https://www.youtube.com/watch?v=short",
        "",
        "ftp://youtu.be/dQw4w9WgXcQ",
    ]:
        with pytest.raises(UrlInvalid) as e:
            await VideoService(db, youtube).register(yt(url))
        assert e.value.extra == {"accepted": ["watch", "youtu.be", "shorts"]}
    assert youtube.calls == []


async def test_register_url_without_scheme(db, youtube, key) -> None:
    video = await VideoService(db, youtube).register(yt("youtu.be/dQw4w9WgXcQ"))
    assert video.source_id == "dQw4w9WgXcQ"


async def test_register_local_name_checks(db, youtube, key, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    (tmp_path / "notes.txt").write_text("x")
    svc = VideoService(db, youtube)
    for name in ["../etc/passwd", "sub/a.mp4", ".hidden.mp4", "a\\b.mp4"]:
        with pytest.raises(PathOutsideInbox):
            await svc.register(LocalSource(source="local", path=name))
    with pytest.raises(UnsupportedFile):
        await svc.register(LocalSource(source="local", path="notes.txt"))
    with pytest.raises(NotFound) as e:
        await svc.register(LocalSource(source="local", path="gone.mp4"))
    assert e.value.extra == {"resource": "inbox_file", "id": "gone.mp4"}
    (tmp_path / "talk.MP4").write_text("x")
    with pytest.raises(NotImplementedYet):  # 형식은 통과, 정보 조회는 B2
        await svc.register(LocalSource(source="local", path="talk.MP4"))


async def test_register_too_long(db, youtube, key) -> None:
    youtube.duration = 10801
    with pytest.raises(VideoTooLong) as e:
        await VideoService(db, youtube).register(yt())
    assert e.value.extra == {"duration_sec": 10801, "max_sec": 10800}
    assert await _count(db) == 0  # 행이 안 생긴다


async def test_register_again_after_cancel_overwrites(db, youtube, key) -> None:
    svc = VideoService(db, youtube)
    first = await svc.register(yt())
    youtube.title = "제목이 바뀐 강의"
    again = await svc.register(yt())
    assert again.id == first.id
    assert (again.title, again.status) == ("제목이 바뀐 강의", "registered")
    assert again.created_at == first.created_at


async def test_register_again_with_job_keeps_row(db, youtube, key, make) -> None:
    svc = VideoService(db, youtube)
    first = await svc.register(yt())
    await make.job(first.id, JobStatus.running)
    youtube.title = "다른 제목"
    again = await svc.register(yt())
    assert (again.title, again.status) == ("자막 있는 강의", "in_progress")  # 작업을 따른다


async def test_register_twice_at_once_makes_one_row(db, youtube, key) -> None:
    async def one() -> int:
        async with SessionLocal() as s:
            return (await VideoService(s, youtube).register(yt())).id

    ids = await asyncio.gather(one(), one())
    assert ids[0] == ids[1]
    assert await _count(db) == 1


# --- list


async def test_list_only_videos_with_jobs(db, make, youtube) -> None:
    await make.video()  # 사전 안내에서 취소 — 작업이 없다
    done = await make.video()
    await make.job(done.id, JobStatus.done, at=T0)
    failed = await make.video()
    await make.job(failed.id, JobStatus.failed, at=T0 + timedelta(minutes=1))
    got = await VideoService(db, youtube).list()
    assert [v.id for v in got] == [failed.id, done.id]  # 작업 시작 최근 순
    assert [v.status for v in got] == ["failed", "analyzed"]
    assert got[0].job.status == JobStatus.failed


async def test_list_order_is_job_start_not_video_creation(db, make, youtube) -> None:
    older = await make.video()
    newer = await make.video()
    await make.job(newer.id, JobStatus.done, at=T0)
    await make.job(older.id, JobStatus.done, at=T0 + timedelta(hours=1))
    assert [v.id for v in await VideoService(db, youtube).list()] == [older.id, newer.id]


async def test_list_queries_do_not_grow(db, make, youtube, queries) -> None:
    for i in range(3):
        v = await make.video()
        await make.job(v.id, JobStatus.done, at=T0 + timedelta(minutes=i))
    queries.clear()
    await VideoService(db, youtube).list()
    three = len(queries)
    for i in range(3):
        v = await make.video()
        await make.job(v.id, JobStatus.done, at=T0 + timedelta(hours=i))
    queries.clear()
    await VideoService(db, youtube).list()
    assert len(queries) == three == 4  # 영상 · 작업 · 조각 · 대화 — 영상 수에 비례하지 않는다


async def test_list_empty(db, youtube) -> None:
    assert await VideoService(db, youtube).list() == []

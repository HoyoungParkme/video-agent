"""video/service — inbox 목록 · 등록 · 목록 · 하나 · 정보 조회 · 상태 계산(VA-MS-001)."""

from __future__ import annotations

import ast
import asyncio
import hashlib
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.core.config import config
from app.core.db import SessionLocal
from app.core.errors import (
    Internal,
    KeyMissing,
    NoAudioTrack,
    NotFound,
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


# --- list_inbox


def _touch(folder: Path, name: str, at: datetime, size: int = 3) -> None:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    os.utime(path, (at.timestamp(), at.timestamp()))


async def test_list_inbox_filters_and_orders(db, youtube, probe, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    monkeypatch.setattr(config, "INBOX_DISPLAY_PATH", "~/video-agent/inbox")
    _touch(tmp_path, "old.mp4", T0, size=10)
    _touch(tmp_path, "talk.M4A", T0 + timedelta(minutes=1))  # 대문자 확장자도 받는다
    _touch(tmp_path, "new.MP4", T0 + timedelta(minutes=2))
    _touch(tmp_path, "broken.mkv", T0 + timedelta(seconds=30))
    _touch(tmp_path, "notes.txt", T0 + timedelta(minutes=3))  # 받지 않는 형식
    _touch(tmp_path, ".DS_Store", T0 + timedelta(minutes=4))  # 숨김
    _touch(tmp_path, "sub/inner.mp4", T0 + timedelta(minutes=5))  # 하위 폴더
    probe.files = {"broken.mkv": None, "talk.M4A": (600, True)}
    listing = await VideoService(db, youtube, probe).list_inbox()
    assert listing.path == "~/video-agent/inbox"  # 마운트 경로가 아니라 표시 경로
    assert [f.name for f in listing.files] == ["new.MP4", "talk.M4A", "broken.mkv", "old.mp4"]
    by = {f.name: f for f in listing.files}
    assert by["broken.mkv"].duration_sec is None  # 깨진 파일도 목록에는 보인다
    assert (by["talk.M4A"].kind, by["talk.M4A"].duration_sec) == ("audio", 600)
    assert (by["old.mp4"].kind, by["old.mp4"].size_bytes, by["old.mp4"].modified_at) == (
        "video",
        10,
        T0,
    )


async def test_list_inbox_empty_folder(db, youtube, probe, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    assert (await VideoService(db, youtube, probe).list_inbox()).files == []


async def test_list_inbox_without_mount_is_internal(db, youtube, probe, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path / "없음"))
    with pytest.raises(Internal):
        await VideoService(db, youtube, probe).list_inbox()


async def test_list_inbox_skips_file_gone_while_listing(db, youtube, tmp_path, monkeypatch) -> None:
    # 목록을 읽은 뒤 재기 전에 파일이 사라졌다(옮기는 중) — 그 파일만 빠지고 나머지는 보인다
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    _touch(tmp_path, "a.mp4", T0)
    _touch(tmp_path, "b.mp4", T0 + timedelta(seconds=1))

    class Mover:
        moved = False

        async def probe(self, path: str) -> tuple[int, bool]:
            if not Mover.moved:  # 처음 재는 파일이 아닌 다른 파일이 그사이 옮겨진다
                (tmp_path / ("b.mp4" if path.endswith("a.mp4") else "a.mp4")).unlink()
                Mover.moved = True
            return 60, True

    listing = await VideoService(db, youtube, Mover()).list_inbox()
    assert len(listing.files) == 1


async def test_list_inbox_probes_a_few_at_a_time(db, youtube, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    for i in range(10):
        _touch(tmp_path, f"{i}.mp4", T0 + timedelta(seconds=i))

    class Slow:
        running = peak = 0

        async def probe(self, path: str) -> tuple[int, bool]:
            Slow.running += 1
            Slow.peak = max(Slow.peak, Slow.running)
            await asyncio.sleep(0.01)
            Slow.running -= 1
            return 60, True

    listing = await VideoService(db, youtube, Slow()).list_inbox()
    assert len(listing.files) == 10
    assert Slow.peak == config.PROBE_CONCURRENCY


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


async def test_info_of_youtube_asks_port(db, youtube, probe) -> None:
    info = await VideoService(db, youtube, probe).info_of(yt())
    assert youtube.calls == [WATCH]
    assert (info.source_id, info.has_captions, info.caption_kind) == ("dQw4w9WgXcQ", True, "manual")


async def test_info_of_youtube_unavailable(db, youtube, unavailable, probe) -> None:
    youtube.error = unavailable
    with pytest.raises(SourceUnavailable) as e:
        await VideoService(db, youtube, probe).info_of(yt())
    assert e.value.extra["reason"] == "비공개 영상이에요"


def local(name: str) -> LocalSource:
    return LocalSource(source="local", path=name)


async def test_info_of_local(db, youtube, probe, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    (tmp_path / "talk.mp3").write_bytes(b"voice")
    probe.files = {"talk.mp3": (3011, True)}  # 음성 파일도 음성 트랙이 있어 통과
    info = await VideoService(db, youtube, probe).info_of(local("talk.mp3"))
    assert (info.source_kind, info.title, info.origin, info.channel) == (
        "local",
        "talk.mp3",
        "talk.mp3",
        None,
    )
    assert (info.duration_sec, info.has_captions, info.caption_language) == (3011, False, None)
    assert info.source_id == hashlib.sha256(b"voice").hexdigest()
    assert probe.calls == [str(tmp_path / "talk.mp3")]


async def test_info_of_local_same_content_same_id(db, youtube, probe, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    (tmp_path / "a.mp4").write_bytes(b"same")
    (tmp_path / "b.mp4").write_bytes(b"same")
    svc = VideoService(db, youtube, probe)
    a, b = await svc.info_of(local("a.mp4")), await svc.info_of(local("b.mp4"))
    assert a.source_id == b.source_id and a.origin != b.origin


async def test_info_of_local_without_audio(db, youtube, probe, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    (tmp_path / "silent.mp4").write_bytes(b"x")
    probe.files = {"silent.mp4": (1800, False)}
    with pytest.raises(NoAudioTrack) as e:
        await VideoService(db, youtube, probe).info_of(local("silent.mp4"))
    assert e.value.extra == {"duration_sec": 1800}  # 길이는 알려 시작 불가 판에 보인다


async def test_info_of_local_unreadable(db, youtube, probe, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    (tmp_path / "broken.mkv").write_bytes(b"x")
    probe.files = {"broken.mkv": None}
    with pytest.raises(UnsupportedFile):
        await VideoService(db, youtube, probe).info_of(local("broken.mkv"))


# --- register


async def test_register_without_key_touches_nothing(db, youtube, env_file, verify, probe) -> None:
    with pytest.raises(KeyMissing):
        await VideoService(db, youtube, probe).register(yt())
    assert youtube.calls == []  # YouTube에 닿지 않는다
    assert await _count(db) == 0


async def test_register_checks_key_each_time(db, youtube, key, verify, probe) -> None:
    await VideoService(db, youtube, probe).register(yt())
    assert len(verify.calls) == 1  # 분석 버튼을 누를 때 확인한다


async def test_register_new_video(db, youtube, key, probe) -> None:
    video = await VideoService(db, youtube, probe).register(yt())
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


async def test_register_same_video_other_url(db, youtube, key, probe) -> None:
    svc = VideoService(db, youtube, probe)
    first = await svc.register(yt("https://youtu.be/dQw4w9WgXcQ"))
    second = await svc.register(yt(WATCH))
    shorts = await svc.register(yt("https://m.youtube.com/shorts/dQw4w9WgXcQ"))
    assert first.id == second.id == shorts.id
    assert await _count(db) == 1


async def test_register_url_invalid(db, youtube, key, probe) -> None:
    for url in [
        "https://vimeo.com/123456",
        "https://www.youtube.com/watch?v=short",
        "",
        "ftp://youtu.be/dQw4w9WgXcQ",
    ]:
        with pytest.raises(UrlInvalid) as e:
            await VideoService(db, youtube, probe).register(yt(url))
        assert e.value.extra == {"accepted": ["watch", "youtu.be", "shorts"]}
    assert youtube.calls == []


async def test_register_url_without_scheme(db, youtube, key, probe) -> None:
    video = await VideoService(db, youtube, probe).register(yt("youtu.be/dQw4w9WgXcQ"))
    assert video.source_id == "dQw4w9WgXcQ"


async def test_register_local_name_checks(db, youtube, key, tmp_path, monkeypatch, probe) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    (tmp_path / "notes.txt").write_text("x")
    svc = VideoService(db, youtube, probe)
    for name in ["../etc/passwd", "sub/a.mp4", ".hidden.mp4", "a\\b.mp4"]:
        with pytest.raises(PathOutsideInbox):
            await svc.register(LocalSource(source="local", path=name))
    with pytest.raises(UnsupportedFile):
        await svc.register(LocalSource(source="local", path="notes.txt"))
    with pytest.raises(NotFound) as e:
        await svc.register(LocalSource(source="local", path="gone.mp4"))
    assert e.value.extra == {"resource": "inbox_file", "id": "gone.mp4"}
    (tmp_path / "talk.MP4").write_text("x")  # 대문자 확장자도 받는다
    video = await svc.register(LocalSource(source="local", path="talk.MP4"))
    assert (video.status, video.source_kind, video.title) == ("registered", "local", "talk.MP4")


async def test_register_local_renamed_is_same_video(db, youtube, probe, key, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    (tmp_path / "workshop.mp4").write_bytes(b"recording")
    svc = VideoService(db, youtube, probe)
    first = await svc.register(local("workshop.mp4"))
    (tmp_path / "workshop.mp4").rename(tmp_path / "workshop_0912.mp4")
    again = await svc.register(local("workshop_0912.mp4"))
    assert again.id == first.id and await _count(db) == 1
    assert again.origin == "workshop_0912.mp4"  # 작업이 없던 영상이라 새 이름으로 덮어쓴다


async def test_register_local_renamed_after_failure_updates_origin(
    db, youtube, probe, key, make, tmp_path, monkeypatch
) -> None:
    # 작업이 실패한 파일을 이름만 바꿔 다시 넣는다 — 다시 시도가 지금 이름을 읽게 origin만 고친다
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    (tmp_path / "talk.mp4").write_bytes(b"recording")
    svc = VideoService(db, youtube, probe)
    first = await svc.register(local("talk.mp4"))
    await make.job(first.id, JobStatus.failed)
    (tmp_path / "talk.mp4").rename(tmp_path / "talk2.mp4")
    again = await svc.register(local("talk2.mp4"))
    assert again.id == first.id
    assert (again.origin, again.title, again.status) == ("talk2.mp4", "talk.mp4", "failed")
    assert (await db.get(VideoRow, first.id)).origin == "talk2.mp4"


async def test_register_local_too_long(db, youtube, probe, key, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path))
    (tmp_path / "all_day.mp4").write_bytes(b"x")
    probe.files = {"all_day.mp4": (10801, True)}
    with pytest.raises(VideoTooLong):
        await VideoService(db, youtube, probe).register(local("all_day.mp4"))
    assert await _count(db) == 0


async def test_register_too_long(db, youtube, key, probe) -> None:
    youtube.duration = 10801
    with pytest.raises(VideoTooLong) as e:
        await VideoService(db, youtube, probe).register(yt())
    assert e.value.extra == {"duration_sec": 10801, "max_sec": 10800}
    assert await _count(db) == 0  # 행이 안 생긴다


async def test_register_again_after_cancel_overwrites(db, youtube, key, probe) -> None:
    svc = VideoService(db, youtube, probe)
    first = await svc.register(yt())
    youtube.title = "제목이 바뀐 강의"
    again = await svc.register(yt())
    assert again.id == first.id
    assert (again.title, again.status) == ("제목이 바뀐 강의", "registered")
    assert again.created_at == first.created_at


async def test_register_again_with_job_keeps_row(db, youtube, key, make, probe) -> None:
    svc = VideoService(db, youtube, probe)
    first = await svc.register(yt())
    await make.job(first.id, JobStatus.running)
    youtube.title = "다른 제목"
    again = await svc.register(yt())
    assert (again.title, again.status) == ("자막 있는 강의", "in_progress")  # 작업을 따른다


async def test_register_twice_at_once_makes_one_row(db, youtube, key, probe) -> None:
    async def one() -> int:
        async with SessionLocal() as s:
            return (await VideoService(s, youtube, probe).register(yt())).id

    ids = await asyncio.gather(one(), one())
    assert ids[0] == ids[1]
    assert await _count(db) == 1


# --- list


async def test_list_only_videos_with_jobs(db, make, youtube, probe) -> None:
    await make.video()  # 사전 안내에서 취소 — 작업이 없다
    done = await make.video()
    await make.job(done.id, JobStatus.done, at=T0)
    failed = await make.video()
    await make.job(failed.id, JobStatus.failed, at=T0 + timedelta(minutes=1))
    got = await VideoService(db, youtube, probe).list()
    assert [v.id for v in got] == [failed.id, done.id]  # 작업 시작 최근 순
    assert [v.status for v in got] == ["failed", "analyzed"]
    assert got[0].job.status == JobStatus.failed


async def test_list_order_is_job_start_not_video_creation(db, make, youtube, probe) -> None:
    older = await make.video()
    newer = await make.video()
    await make.job(newer.id, JobStatus.done, at=T0)
    await make.job(older.id, JobStatus.done, at=T0 + timedelta(hours=1))
    assert [v.id for v in await VideoService(db, youtube, probe).list()] == [older.id, newer.id]


async def test_list_queries_do_not_grow(db, make, youtube, queries, probe) -> None:
    for i in range(3):
        v = await make.video()
        await make.job(v.id, JobStatus.done, at=T0 + timedelta(minutes=i))
    queries.clear()
    await VideoService(db, youtube, probe).list()
    three = len(queries)
    for i in range(3):
        v = await make.video()
        await make.job(v.id, JobStatus.done, at=T0 + timedelta(hours=i))
    queries.clear()
    await VideoService(db, youtube, probe).list()
    assert len(queries) == three == 4  # 영상 · 작업 · 조각 · 대화 — 영상 수에 비례하지 않는다


async def test_list_empty(db, youtube, probe) -> None:
    assert await VideoService(db, youtube, probe).list() == []


# --- get


async def test_get(db, make, youtube, probe) -> None:
    with pytest.raises(NotFound) as e:
        await VideoService(db, youtube, probe).get(999)
    assert e.value.extra == {"resource": "video", "id": 999}
    row = await make.video()
    detail = await VideoService(db, youtube, probe).get(row.id)
    assert (detail.job, detail.video.status) == (None, "registered")


async def test_get_after_finish(db, make, youtube, probe) -> None:
    """JobService.finish 테스트 관점 — finish 뒤 get의 status=analyzed, analyzed_at = 끝난 시각."""
    video = await make.video()
    job = await make.job(video.id, JobStatus.running, stage="suggest")
    await JobService(db).finish(job.id)
    detail = await VideoService(db, youtube, probe).get(video.id)
    assert detail.video.status == "analyzed"
    assert detail.video.analyzed_at == detail.job.finished_at is not None

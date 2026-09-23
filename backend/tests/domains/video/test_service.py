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

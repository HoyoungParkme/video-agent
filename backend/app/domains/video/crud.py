"""videos 접근 — DB만. 판단은 service가 한다."""

from __future__ import annotations

from sqlalchemy import column, select, table
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.video.models import VideoRow
from app.domains.video.schemas import SourceInfo

# 작업이 있는 영상만 고를 때 — 작업 테이블은 이름과 열 하나만 안다(작업 묶음의 ORM을 쓰지 않는다)
_jobs = table("analysis_jobs", column("video_id"))
# 다시 넣을 때 덮어쓰는 값. id · 출처 · created_at은 그대로
_OVERWRITE = (
    "title",
    "channel",
    "duration_sec",
    "origin",
    "has_captions",
    "caption_language",
    "caption_kind",
)


async def by_id(session: AsyncSession, video_id: int) -> VideoRow | None:
    return await session.scalar(select(VideoRow).where(VideoRow.id == video_id))


async def by_source_id(session: AsyncSession, source_id: str) -> VideoRow | None:
    """출처 식별자(YouTube 영상 ID · 파일 내용 해시)로 — 중복 판정."""
    return await session.scalar(select(VideoRow).where(VideoRow.source_id == source_id))


async def with_jobs(session: AsyncSession) -> list[VideoRow]:
    """작업이 하나라도 있는 영상들. 사전 안내에서 취소한 영상은 빠진다."""
    return list(
        await session.scalars(select(VideoRow).where(VideoRow.id.in_(select(_jobs.c.video_id))))
    )


def insert(session: AsyncSession, info: SourceInfo) -> VideoRow:
    """새 영상 행. 커밋은 service가 한다."""
    row = VideoRow(**info.model_dump())
    session.add(row)
    return row


def overwrite(row: VideoRow, info: SourceInfo) -> None:
    """작업이 없는 영상을 새로 읽은 정보로 덮어쓴다."""
    for name in _OVERWRITE:
        setattr(row, name, getattr(info, name))


def rename(row: VideoRow, origin: str) -> None:
    """로컬 파일의 지금 이름 — 작업이 있어도 origin만 고친다(다시 시도가 이 경로를 읽는다)."""
    row.origin = origin

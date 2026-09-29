"""영상 테이블(VA-DOM-003 videos)과 그 열거형(VA-DOM-002 2.5)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, str_enum


class SourceKind(StrEnum):
    youtube = "youtube"
    local = "local"


class CaptionKind(StrEnum):
    manual = "manual"
    auto = "auto"


class VideoRow(Base):
    """영상 하나 — YouTube 영상 또는 inbox 파일(DOM-002 2.1 Video).

    상태와 분석 완료 시각은 컬럼이 아니다. 가장 최근 작업에서 계산한다.
    """

    __tablename__ = "videos"
    __table_args__ = (
        CheckConstraint("duration_sec > 0 AND duration_sec <= 10800", name="duration_range"),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    source_kind: Mapped[SourceKind] = mapped_column(str_enum(SourceKind, 10))
    source_id: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    channel: Mapped[str | None] = mapped_column(String(200))
    duration_sec: Mapped[int]
    origin: Mapped[str] = mapped_column(String(500))
    has_captions: Mapped[bool]
    caption_language: Mapped[str | None] = mapped_column(String(10))
    caption_kind: Mapped[CaptionKind | None] = mapped_column(str_enum(CaptionKind, 10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

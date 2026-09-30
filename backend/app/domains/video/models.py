"""영상 테이블(VA-DOM-003 videos)과 그 열거형(VA-DOM-002 2.5)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, Identity, String, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, str_enum


class SourceKind(StrEnum):
    youtube = "youtube"
    local = "local"


class CaptionKind(StrEnum):
    manual = "manual"
    auto = "auto"


class VideoRow(Base):
    """영상 하나 — YouTube 영상 또는 로컬 파일(inbox 파일 · 올린 사본, DOM-002 2.1 Video).

    상태와 분석 완료 시각은 컬럼이 아니다. 가장 최근 작업에서 계산한다. 올린 사본의 경로도 컬럼이
    아니다 — `uploaded`와 source_id · origin의 확장자로 정해진다(shared/sources.py).
    """

    __tablename__ = "videos"
    __table_args__ = (
        CheckConstraint("duration_sec > 0 AND duration_sec <= 10800", name="duration_range"),
        CheckConstraint("NOT uploaded OR source_kind = 'local'", name="uploaded_is_local"),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    source_kind: Mapped[SourceKind] = mapped_column(str_enum(SourceKind, 10))
    source_id: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    channel: Mapped[str | None] = mapped_column(String(200))
    duration_sec: Mapped[int]
    origin: Mapped[str] = mapped_column(String(500))
    # 원본 자리 — true면 올린 사본(data/uploads). 사본을 지운 뒤에도 그대로다(다시 시도가 읽는 곳)
    uploaded: Mapped[bool] = mapped_column(server_default=false(), default=False)
    has_captions: Mapped[bool]
    caption_language: Mapped[str | None] = mapped_column(String(10))
    caption_kind: Mapped[CaptionKind | None] = mapped_column(str_enum(CaptionKind, 10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

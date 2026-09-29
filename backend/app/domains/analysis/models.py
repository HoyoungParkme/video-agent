"""결과 테이블 일곱(VA-DOM-003 transcripts ~ suggested_questions)과 그 열거형(VA-DOM-002 2.5)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, str_enum

# 시각은 numeric(9,3) — 밀리초까지. 파이썬에서는 float로 읽는다(DOM-003 4장 1)
SEC = Numeric(9, 3, asdecimal=False)


class TranscriptSource(StrEnum):
    caption_manual = "caption_manual"
    caption_auto = "caption_auto"
    stt = "stt"


class TranscriptRow(Base):
    """영상과 1:1인 스크립트(DOM-002 2.3 Transcript). 재분석은 행을 바꾼다."""

    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), unique=True)
    source: Mapped[TranscriptSource] = mapped_column(str_enum(TranscriptSource, 15))
    language: Mapped[str] = mapped_column(String(10))
    model: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SegmentRow(Base):
    """스크립트의 구간 한 줄(DOM-002 2.3 Segment)."""

    __tablename__ = "segments"
    __table_args__ = (
        UniqueConstraint("transcript_id", "seq"),
        CheckConstraint("seq >= 1", name="seq_positive"),
        CheckConstraint("start_sec >= 0", name="start_nonnegative"),
        CheckConstraint("end_sec >= start_sec", name="end_after_start"),
        Index("ix_segments_transcript_id_start_sec", "transcript_id", "start_sec"),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    transcript_id: Mapped[int] = mapped_column(ForeignKey("transcripts.id", ondelete="CASCADE"))
    seq: Mapped[int]
    start_sec: Mapped[float] = mapped_column(SEC)
    end_sec: Mapped[float] = mapped_column(SEC)
    text: Mapped[str] = mapped_column(Text)


class SummaryRow(Base):
    """영상과 1:1인 핵심 요약(DOM-002 2.3 Summary)."""

    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), unique=True)
    one_liner: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InsightRow(Base):
    """요약의 인사이트 한 줄과 출처 시각들(DOM-002 2.3 Insight)."""

    __tablename__ = "insights"
    __table_args__ = (
        UniqueConstraint("summary_id", "seq"),
        CheckConstraint("seq >= 1", name="seq_positive"),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    summary_id: Mapped[int] = mapped_column(ForeignKey("summaries.id", ondelete="CASCADE"))
    seq: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    source_secs: Mapped[list[float]] = mapped_column(JSONB)


class PartRow(Base):
    """60분 넘는 영상의 파트(DOM-002 2.3 Part). 끝 시각은 읽을 때 계산한다."""

    __tablename__ = "parts"
    __table_args__ = (
        UniqueConstraint("video_id", "seq"),
        UniqueConstraint("id", "video_id"),
        CheckConstraint("seq >= 1", name="seq_positive"),
        CheckConstraint("start_sec >= 0", name="start_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))
    seq: Mapped[int]
    title: Mapped[str] = mapped_column(String(200))
    start_sec: Mapped[float] = mapped_column(SEC)


class ChapterRow(Base):
    """챕터와 요점(DOM-002 2.3 Chapter). 파트는 같은 영상 것만 — 복합 FK가 막는다(DOM-003 4장 4)."""

    __tablename__ = "chapters"
    __table_args__ = (
        UniqueConstraint("video_id", "seq"),
        ForeignKeyConstraint(
            ["part_id", "video_id"],
            ["parts.id", "parts.video_id"],
            ondelete="CASCADE",
            name="fk_chapters_part_id_video_id_parts",
        ),
        CheckConstraint("seq >= 1", name="seq_positive"),
        CheckConstraint("start_sec >= 0", name="start_nonnegative"),
        Index("ix_chapters_part_id_video_id", "part_id", "video_id"),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))
    part_id: Mapped[int | None]
    seq: Mapped[int]
    start_sec: Mapped[float] = mapped_column(SEC)
    title: Mapped[str] = mapped_column(String(200))
    bullets: Mapped[list[str]] = mapped_column(JSONB)


class SuggestedQuestionRow(Base):
    """영상마다 셋인 추천 질문(DOM-002 2.3 SuggestedQuestion)."""

    __tablename__ = "suggested_questions"
    __table_args__ = (
        UniqueConstraint("video_id", "seq"),
        CheckConstraint("seq BETWEEN 1 AND 3", name="seq_range"),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))
    seq: Mapped[int]
    text: Mapped[str] = mapped_column(Text)

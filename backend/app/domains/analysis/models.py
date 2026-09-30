"""결과 테이블 여덟(VA-DOM-003 transcripts ~ suggested_questions · chapter_frames)과 그 열거형
(VA-DOM-002 2.5)."""

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
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import ImageQuality
from app.core.db import Base, str_enum

# 시각은 numeric(9,3) — 밀리초까지. 파이썬에서는 float로 읽는다(DOM-003 4장 1)
SEC = Numeric(9, 3, asdecimal=False)


class TranscriptSource(StrEnum):
    caption_manual = "caption_manual"
    caption_auto = "caption_auto"
    stt = "stt"


class FrameSource(StrEnum):
    """장면을 어디서 얻었나 — YouTube 스토리보드 칸 · 로컬 원본 프레임."""

    storyboard = "storyboard"
    local_frame = "local_frame"


class InfographicState(StrEnum):
    """인포그래픽 상태 — none은 행이 없을 때의 응답값이라 저장하지 않는다(DOM-002 2장 열거형)."""

    none = "none"
    making = "making"
    done = "done"
    failed = "failed"


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


class ChapterFrameRow(Base):
    """챕터의 대표 장면(DOM-002 2.3 ChapterFrame). 챕터마다 0..1.

    얻지 못한 챕터도 그림 컬럼이 모두 null인 행으로 남긴다 — 「해 봤다」를 알아야 옛 결과를
    다시 채우지 않는다. CHECK가 반쪽 행을 막는다(DOM-003 4장 7). 그림 파일은 DB 밖이다.
    """

    __tablename__ = "chapter_frames"
    __table_args__ = (
        UniqueConstraint("chapter_id"),
        CheckConstraint(
            "(path IS NULL AND sec IS NULL AND source IS NULL AND width IS NULL AND height IS NULL)"
            " OR (path IS NOT NULL AND sec IS NOT NULL AND source IS NOT NULL"
            " AND width IS NOT NULL AND height IS NOT NULL)",
            name="all_or_none",
        ),
        CheckConstraint("sec >= 0", name="sec_nonnegative"),
        CheckConstraint("width > 0 AND height > 0", name="size_positive"),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"))
    sec: Mapped[float | None] = mapped_column(SEC)
    source: Mapped[FrameSource | None] = mapped_column(str_enum(FrameSource, 12))
    width: Mapped[int | None] = mapped_column(SmallInteger)
    height: Mapped[int | None] = mapped_column(SmallInteger)
    path: Mapped[str | None] = mapped_column(String(500))


PICTURE = ("model", "quality", "width", "height", "cost_usd", "path", "created_at")


class InfographicRow(Base):
    """영상의 인포그래픽(DOM-002 2.3 Infographic). 영상마다 0..1이고 다시 만들면 같은 행을 고친다.

    그림 컬럼은 지금 쓰는 그림의 것이다 — 다시 그리는 동안 · 다시 그리기가 실패한 뒤에도 이전 그림이
    그대로다. CHECK가 반쪽 그림 · 그림 없는 done · 이유 없는 실패를 막는다(DOM-003 3장). 그림
    파일은 DB 밖(data/infographics)이다.
    """

    __tablename__ = "infographics"
    __table_args__ = (
        UniqueConstraint("video_id"),
        CheckConstraint(
            "("
            + " AND ".join(f"{c} IS NULL" for c in PICTURE)
            + ") OR ("
            + " AND ".join(f"{c} IS NOT NULL" for c in PICTURE)
            + ")",
            name="picture_all_or_none",
        ),
        CheckConstraint("state <> 'done' OR path IS NOT NULL", name="done_has_picture"),
        CheckConstraint(
            "(state = 'failed') = (error_reason IS NOT NULL)", name="reason_when_failed"
        ),
        CheckConstraint("width > 0 AND height > 0", name="size_positive"),
        CheckConstraint("cost_usd >= 0", name="cost_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))
    state: Mapped[InfographicState] = mapped_column(str_enum(InfographicState, 10))
    model: Mapped[str | None] = mapped_column(String(50))
    quality: Mapped[ImageQuality | None] = mapped_column(str_enum(ImageQuality, 10))
    width: Mapped[int | None] = mapped_column(SmallInteger)
    height: Mapped[int | None] = mapped_column(SmallInteger)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(8, 4, asdecimal=False))
    path: Mapped[str | None] = mapped_column(String(500))
    error_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

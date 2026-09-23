"""작업 · 조각 테이블(VA-DOM-003 analysis_jobs · audio_chunks)과 그 열거형(VA-DOM-002 2.5)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, str_enum


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    failed = "failed"
    done = "done"


class JobStage(StrEnum):
    pending = "pending"
    download = "download"
    extract = "extract"
    transcribe = "transcribe"
    summarize = "summarize"
    chapter = "chapter"
    suggest = "suggest"


class ChunkState(StrEnum):
    waiting = "waiting"
    in_flight = "in_flight"
    done = "done"
    failed = "failed"


class ErrorKind(StrEnum):
    network = "network"
    openai = "openai"
    youtube = "youtube"
    ffmpeg = "ffmpeg"
    disk = "disk"
    unknown = "unknown"


class AnalysisJobRow(Base):
    """영상 하나의 분석 시도(DOM-002 2.2 AnalysisJob). 재시도는 같은 행을 이어간다.

    `running`은 프로세스 전체에 하나 — 부분 unique 인덱스가 막는다. 대기열은 `queued` 행이다.
    영상 하나에 기다리는 · 도는 작업도 하나다(부분 unique, 0002).
    """

    __tablename__ = "analysis_jobs"
    __table_args__ = (
        CheckConstraint("progress_pct BETWEEN 0 AND 100", name="progress_range"),
        CheckConstraint(
            "(status = 'failed' AND error_kind IS NOT NULL AND error_reason IS NOT NULL)"
            " OR (status <> 'failed' AND error_kind IS NULL AND error_reason IS NULL)",
            name="error_when_failed",
        ),
        Index("ix_analysis_jobs_video_id_started_at", "video_id", text("started_at DESC")),
        Index(
            "uq_analysis_jobs_running",
            "status",
            unique=True,
            postgresql_where=text("status = 'running'"),
        ),
        Index(
            "ix_analysis_jobs_queued_at",
            "queued_at",
            postgresql_where=text("status = 'queued'"),
        ),
        Index(
            "uq_analysis_jobs_video_id_active",
            "video_id",
            unique=True,
            postgresql_where=text("status IN ('queued', 'running')"),
        ),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))
    status: Mapped[JobStatus] = mapped_column(str_enum(JobStatus, 10))
    stage: Mapped[JobStage] = mapped_column(str_enum(JobStage, 12))
    stages: Mapped[list[str]] = mapped_column(JSONB)
    progress_pct: Mapped[int] = mapped_column(SmallInteger)
    est_seconds: Mapped[int]
    est_cost_usd: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    concurrency: Mapped[int] = mapped_column(SmallInteger)
    stt_model: Mapped[str | None] = mapped_column(String(50))
    text_model: Mapped[str] = mapped_column(String(50))
    error_kind: Mapped[ErrorKind | None] = mapped_column(str_enum(ErrorKind, 10))
    error_reason: Mapped[str | None] = mapped_column(Text)
    error_chunk_seq: Mapped[int | None]
    error_attempts: Mapped[int | None]
    stage_durations_sec: Mapped[dict[str, float]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    stage_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AudioChunkRow(Base):
    """받아쓰기 단위 조각(DOM-002 2.2 AudioChunk). 작업이 끝나도 행은 남는다."""

    __tablename__ = "audio_chunks"
    __table_args__ = (
        UniqueConstraint("job_id", "seq"),
        CheckConstraint("seq >= 1", name="seq_positive"),
        Index("ix_audio_chunks_job_id_state", "job_id", "state"),
    )

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("analysis_jobs.id", ondelete="CASCADE"))
    seq: Mapped[int]
    offset_sec: Mapped[float] = mapped_column(Numeric(9, 3, asdecimal=False))
    duration_sec: Mapped[float] = mapped_column(Numeric(9, 3, asdecimal=False))
    path: Mapped[str | None] = mapped_column(String(500))
    state: Mapped[ChunkState] = mapped_column(str_enum(ChunkState, 10))
    attempts: Mapped[int] = mapped_column(SmallInteger, default=0, server_default=text("0"))
    result: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

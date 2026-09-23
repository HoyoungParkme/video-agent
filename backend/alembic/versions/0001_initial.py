"""0001_initial — 테이블 11개와 인덱스 · 제약 전부(VA-DOM-003 1 · 2 · 3장).

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-23
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None

SEC = sa.Numeric(9, 3)
TS = sa.DateTime(timezone=True)


def _id() -> sa.Column:
    return sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False)


def _video_fk(table: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        ["video_id"], ["videos.id"], ondelete="CASCADE", name=f"fk_{table}_video_id_videos"
    )


def upgrade() -> None:
    op.create_table(
        "videos",
        _id(),
        sa.Column("source_kind", sa.String(10), nullable=False),
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("channel", sa.String(200), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=False),
        sa.Column("origin", sa.String(500), nullable=False),
        sa.Column("has_captions", sa.Boolean(), nullable=False),
        sa.Column("caption_language", sa.String(10), nullable=True),
        sa.Column("caption_kind", sa.String(10), nullable=True),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_videos"),
        sa.UniqueConstraint("source_id", name="uq_videos_source_id"),
        sa.CheckConstraint(
            "duration_sec > 0 AND duration_sec <= 10800", name="ck_videos_duration_range"
        ),
    )

    op.create_table(
        "analysis_jobs",
        _id(),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("stage", sa.String(12), nullable=False),
        sa.Column("stages", JSONB(), nullable=False),
        sa.Column("progress_pct", sa.SmallInteger(), nullable=False),
        sa.Column("est_seconds", sa.Integer(), nullable=False),
        sa.Column("est_cost_usd", sa.Numeric(8, 4), nullable=False),
        sa.Column("concurrency", sa.SmallInteger(), nullable=False),
        sa.Column("stt_model", sa.String(50), nullable=True),
        sa.Column("text_model", sa.String(50), nullable=False),
        sa.Column("error_kind", sa.String(10), nullable=True),
        sa.Column("error_reason", sa.Text(), nullable=True),
        sa.Column("error_chunk_seq", sa.Integer(), nullable=True),
        sa.Column("error_attempts", sa.Integer(), nullable=True),
        sa.Column(
            "stage_durations_sec", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("stage_started_at", TS, nullable=False),
        sa.Column("queued_at", TS, nullable=False),
        sa.Column("started_at", TS, nullable=False),
        sa.Column("finished_at", TS, nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_analysis_jobs"),
        _video_fk("analysis_jobs"),
        sa.CheckConstraint(
            "progress_pct BETWEEN 0 AND 100", name="ck_analysis_jobs_progress_range"
        ),
        sa.CheckConstraint(
            "(status = 'failed' AND error_kind IS NOT NULL AND error_reason IS NOT NULL)"
            " OR (status <> 'failed' AND error_kind IS NULL AND error_reason IS NULL)",
            name="ck_analysis_jobs_error_when_failed",
        ),
    )
    op.create_index(
        "ix_analysis_jobs_video_id_started_at",
        "analysis_jobs",
        ["video_id", sa.text("started_at DESC")],
    )
    # running은 프로세스 전체에 하나 — 두 워커가 동시에 꺼내도 하나만 성공한다(DOM-003 4장 2)
    op.create_index(
        "uq_analysis_jobs_running",
        "analysis_jobs",
        ["status"],
        unique=True,
        postgresql_where=sa.text("status = 'running'"),
    )
    op.create_index(
        "ix_analysis_jobs_queued_at",
        "analysis_jobs",
        ["queued_at"],
        postgresql_where=sa.text("status = 'queued'"),
    )

    op.create_table(
        "audio_chunks",
        _id(),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("offset_sec", SEC, nullable=False),
        sa.Column("duration_sec", SEC, nullable=False),
        sa.Column("path", sa.String(500), nullable=True),
        sa.Column("state", sa.String(10), nullable=False),
        sa.Column("attempts", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("result", JSONB(), nullable=True),
        sa.Column("done_at", TS, nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_audio_chunks"),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["analysis_jobs.id"],
            ondelete="CASCADE",
            name="fk_audio_chunks_job_id_analysis_jobs",
        ),
        sa.UniqueConstraint("job_id", "seq", name="uq_audio_chunks_job_id_seq"),
        sa.CheckConstraint("seq >= 1", name="ck_audio_chunks_seq_positive"),
    )
    op.create_index("ix_audio_chunks_job_id_state", "audio_chunks", ["job_id", "state"])

    op.create_table(
        "transcripts",
        _id(),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(15), nullable=False),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("model", sa.String(50), nullable=True),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_transcripts"),
        _video_fk("transcripts"),
        sa.UniqueConstraint("video_id", name="uq_transcripts_video_id"),
    )

    op.create_table(
        "segments",
        _id(),
        sa.Column("transcript_id", sa.Integer(), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("start_sec", SEC, nullable=False),
        sa.Column("end_sec", SEC, nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_segments"),
        sa.ForeignKeyConstraint(
            ["transcript_id"],
            ["transcripts.id"],
            ondelete="CASCADE",
            name="fk_segments_transcript_id_transcripts",
        ),
        sa.UniqueConstraint("transcript_id", "seq", name="uq_segments_transcript_id_seq"),
        sa.CheckConstraint("seq >= 1", name="ck_segments_seq_positive"),
        sa.CheckConstraint("start_sec >= 0", name="ck_segments_start_nonnegative"),
        sa.CheckConstraint("end_sec >= start_sec", name="ck_segments_end_after_start"),
    )
    op.create_index(
        "ix_segments_transcript_id_start_sec", "segments", ["transcript_id", "start_sec"]
    )

    op.create_table(
        "summaries",
        _id(),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("one_liner", sa.Text(), nullable=False),
        sa.Column("model", sa.String(50), nullable=False),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_summaries"),
        _video_fk("summaries"),
        sa.UniqueConstraint("video_id", name="uq_summaries_video_id"),
    )

    op.create_table(
        "insights",
        _id(),
        sa.Column("summary_id", sa.Integer(), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source_secs", JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_insights"),
        sa.ForeignKeyConstraint(
            ["summary_id"],
            ["summaries.id"],
            ondelete="CASCADE",
            name="fk_insights_summary_id_summaries",
        ),
        sa.UniqueConstraint("summary_id", "seq", name="uq_insights_summary_id_seq"),
        sa.CheckConstraint("seq >= 1", name="ck_insights_seq_positive"),
    )

    op.create_table(
        "parts",
        _id(),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("start_sec", SEC, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_parts"),
        _video_fk("parts"),
        sa.UniqueConstraint("video_id", "seq", name="uq_parts_video_id_seq"),
        # chapters의 복합 FK 대상(DOM-003 3장)
        sa.UniqueConstraint("id", "video_id", name="uq_parts_id_video_id"),
        sa.CheckConstraint("seq >= 1", name="ck_parts_seq_positive"),
        sa.CheckConstraint("start_sec >= 0", name="ck_parts_start_nonnegative"),
    )

    op.create_table(
        "chapters",
        _id(),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("part_id", sa.Integer(), nullable=True),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("start_sec", SEC, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("bullets", JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_chapters"),
        _video_fk("chapters"),
        # 파트는 같은 영상 것만(DOM-003 4장 4)
        sa.ForeignKeyConstraint(
            ["part_id", "video_id"],
            ["parts.id", "parts.video_id"],
            ondelete="CASCADE",
            name="fk_chapters_part_id_video_id_parts",
        ),
        sa.UniqueConstraint("video_id", "seq", name="uq_chapters_video_id_seq"),
        sa.CheckConstraint("seq >= 1", name="ck_chapters_seq_positive"),
        sa.CheckConstraint("start_sec >= 0", name="ck_chapters_start_nonnegative"),
    )
    op.create_index("ix_chapters_part_id_video_id", "chapters", ["part_id", "video_id"])

    op.create_table(
        "suggested_questions",
        _id(),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_suggested_questions"),
        _video_fk("suggested_questions"),
        sa.UniqueConstraint("video_id", "seq", name="uq_suggested_questions_video_id_seq"),
        sa.CheckConstraint("seq BETWEEN 1 AND 3", name="ck_suggested_questions_seq_range"),
    )

    op.create_table(
        "chat_turns",
        _id(),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("cited_secs", JSONB(), nullable=False),
        sa.Column("model", sa.String(50), nullable=False),
        sa.Column("asked_at", TS, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_chat_turns"),
        _video_fk("chat_turns"),
    )
    op.create_index("ix_chat_turns_video_id_asked_at", "chat_turns", ["video_id", "asked_at"])


def downgrade() -> None:
    # 자식부터. 인덱스는 테이블과 함께 사라진다
    for table in (
        "chat_turns",
        "suggested_questions",
        "chapters",
        "parts",
        "insights",
        "summaries",
        "segments",
        "transcripts",
        "audio_chunks",
        "analysis_jobs",
        "videos",
    ):
        op.drop_table(table)

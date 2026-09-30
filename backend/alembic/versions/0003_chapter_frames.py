"""0003_chapter_frames — 챕터 대표 장면(VA-DOM-003 3장 chapter_frames · 4장 7, 카드 D2).

챕터마다 0..1. 얻지 못한 챕터도 그림 컬럼이 모두 null인 행으로 남겨 「해 봤다」를 안다 — CHECK가
반쪽 행(경로는 있는데 시각이 없는 것)을 막는다. 그림 파일은 DB 밖(data/frames)이다.

Revision ID: 0003_chapter_frames
Revises: 0002_job_active_per_video
Create Date: 2026-09-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0003_chapter_frames"
down_revision: str | None = "0002_job_active_per_video"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "chapter_frames",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("sec", sa.Numeric(9, 3), nullable=True),
        sa.Column("source", sa.String(12), nullable=True),
        sa.Column("width", sa.SmallInteger(), nullable=True),
        sa.Column("height", sa.SmallInteger(), nullable=True),
        sa.Column("path", sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_chapter_frames"),
        sa.ForeignKeyConstraint(
            ["chapter_id"],
            ["chapters.id"],
            ondelete="CASCADE",
            name="fk_chapter_frames_chapter_id_chapters",
        ),
        sa.UniqueConstraint("chapter_id", name="uq_chapter_frames_chapter_id"),
        sa.CheckConstraint(
            "(path IS NULL AND sec IS NULL AND source IS NULL AND width IS NULL AND height IS NULL)"
            " OR (path IS NOT NULL AND sec IS NOT NULL AND source IS NOT NULL"
            " AND width IS NOT NULL AND height IS NOT NULL)",
            name="ck_chapter_frames_all_or_none",
        ),
        sa.CheckConstraint("sec >= 0", name="ck_chapter_frames_sec_nonnegative"),
        sa.CheckConstraint("width > 0 AND height > 0", name="ck_chapter_frames_size_positive"),
    )


def downgrade() -> None:
    op.drop_table("chapter_frames")

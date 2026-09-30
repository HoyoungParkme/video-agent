"""0004_infographics — 인포그래픽(VA-DOM-003 3장 infographics · 4장 8, 카드 D3).

영상마다 0..1이고 다시 만들면 같은 행을 고친다. 그림 컬럼은 지금 쓰는 그림의 것이라 다시 그리는
동안 · 다시 그리기가 실패한 뒤에도 이전 그림이 남는다 — CHECK가 반쪽 그림 · 그림 없는 done ·
이유 없는 실패를 막는다. 그림 파일은 DB 밖(data/infographics)이다.

Revision ID: 0004_infographics
Revises: 0003_chapter_frames
Create Date: 2026-09-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0004_infographics"
down_revision: str | None = "0003_chapter_frames"
branch_labels: str | None = None
depends_on: str | None = None

PICTURE = ("model", "quality", "width", "height", "cost_usd", "path", "created_at")


def upgrade() -> None:
    op.create_table(
        "infographics",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(10), nullable=False),
        sa.Column("model", sa.String(50), nullable=True),
        sa.Column("quality", sa.String(10), nullable=True),
        sa.Column("width", sa.SmallInteger(), nullable=True),
        sa.Column("height", sa.SmallInteger(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(8, 4), nullable=True),
        sa.Column("path", sa.String(500), nullable=True),
        sa.Column("error_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_infographics"),
        sa.ForeignKeyConstraint(
            ["video_id"], ["videos.id"], ondelete="CASCADE", name="fk_infographics_video_id_videos"
        ),
        sa.UniqueConstraint("video_id", name="uq_infographics_video_id"),
        sa.CheckConstraint(
            "("
            + " AND ".join(f"{c} IS NULL" for c in PICTURE)
            + ") OR ("
            + " AND ".join(f"{c} IS NOT NULL" for c in PICTURE)
            + ")",
            name="ck_infographics_picture_all_or_none",
        ),
        sa.CheckConstraint(
            "state <> 'done' OR path IS NOT NULL", name="ck_infographics_done_has_picture"
        ),
        sa.CheckConstraint(
            "(state = 'failed') = (error_reason IS NOT NULL)",
            name="ck_infographics_reason_when_failed",
        ),
        sa.CheckConstraint("width > 0 AND height > 0", name="ck_infographics_size_positive"),
        sa.CheckConstraint("cost_usd >= 0", name="ck_infographics_cost_nonnegative"),
    )


def downgrade() -> None:
    op.drop_table("infographics")

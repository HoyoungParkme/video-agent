"""0005_videos_uploaded — 올린 사본(VA-DOM-003 3장 videos · 4장 9, 카드 D4).

로컬 영상의 원본 자리 — true면 끌어 놓아 올린 사본(data/uploads), false면 inbox 파일 또는 YouTube.
경로는 저장하지 않는다(source_id와 원래 이름의 확장자로 정해진다). 있던 영상은 모두 올린 것이
아니라 default false다. CHECK가 YouTube 영상의 true를 막는다.

Revision ID: 0005_videos_uploaded
Revises: 0004_infographics
Create Date: 2026-09-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0005_videos_uploaded"
down_revision: str | None = "0004_infographics"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "videos",
        sa.Column("uploaded", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_check_constraint(
        "ck_videos_uploaded_is_local", "videos", "NOT uploaded OR source_kind = 'local'"
    )


def downgrade() -> None:
    op.drop_constraint("ck_videos_uploaded_is_local", "videos", type_="check")
    op.drop_column("videos", "uploaded")

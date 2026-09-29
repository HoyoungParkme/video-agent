"""0002_job_active_per_video — 영상 하나에 기다리는 · 도는 작업은 하나(VA-DOM-003 3장 · 4장 6).

같은 영상에 [분석 시작]이 동시에 두 번 오면(탭 둘) `start`의 확인을 둘 다 지나 행이 둘 생겼다.
영상과 작업은 1:N(분석 시도)이라 `video_id` 전체가 아니라 `queued` · `running`만 막는다.

Revision ID: 0002_job_active_per_video
Revises: 0001_initial
Create Date: 2026-09-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0002_job_active_per_video"
down_revision: str | None = "0001_initial"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_index(
        "uq_analysis_jobs_video_id_active",
        "analysis_jobs",
        ["video_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )


def downgrade() -> None:
    op.drop_index("uq_analysis_jobs_video_id_active", table_name="analysis_jobs")

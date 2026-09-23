"""작업 묶음의 응답 형태 — VA-API-001 4장 그대로.

Job · JobSummary · Chunks · Chunk · JobError · Estimate.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.core.settings import Models
from app.domains.job.models import ChunkState, ErrorKind, JobStage, JobStatus


class JobSummary(BaseModel):
    """목록 행 · 영상 하나에 붙는 최근 작업 요약."""

    id: int
    status: JobStatus
    stage: JobStage
    queue_position: int | None
    progress_pct: int
    chunks_done: int | None
    chunks_total: int | None
    failed_chunk_seq: int | None
    started_at: datetime
    finished_at: datetime | None


class Chunk(BaseModel):
    seq: int
    state: ChunkState


class Chunks(BaseModel):
    """조각 격자 · 범례의 숫자. next_seq는 완료하지 않은 첫 조각(r)."""

    total: int
    done: int
    in_flight: int
    failed: int
    waiting: int
    next_seq: int | None
    items: list[Chunk]


class JobError(BaseModel):
    """실패 알림의 재료. chunk_seq는 받아쓰기 밖 단계면 None."""

    kind: ErrorKind
    reason: str
    chunk_seq: int | None
    attempts: int


class Estimate(BaseModel):
    """사전 안내의 예상 시간 · 비용. 화면은 계산하지 않고 그대로 보인다."""

    needs_stt: bool
    seconds: int
    chunks: int | None
    concurrency: int | None
    stt_minutes: float | None
    stt_price_per_min: float | None
    stt_cost_usd: float
    text_cost_usd: float
    total_cost_usd: float
    stt_model: str
    text_model: str


class Job(BaseModel):
    """폴링 응답 — UI-3이 그리는 값 전부(VA-API-001 GET …/job의 요소 ↔ 필드 표)."""

    id: int
    video_id: int
    status: JobStatus
    stage: JobStage
    queue_position: int | None
    stages: list[JobStage]
    stage_index: int
    progress_pct: int
    remaining_sec: int | None
    chunks: Chunks | None
    concurrency: int | None
    models: Models
    error: JobError | None
    est_seconds: int
    est_cost_usd: float
    stage_durations_sec: dict[str, int]
    started_at: datetime
    finished_at: datetime | None

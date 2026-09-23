"""analysis_jobs · audio_chunks 접근 — DB만. 판단은 service가 한다.

대기열 순서는 (queued_at, id) — 같은 때 들어온 둘도 차례가 갈린다.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.domains.job.models import AnalysisJobRow, AudioChunkRow, ChunkState, JobStatus
from app.domains.job.schemas import ChunkPlan

Job = AnalysisJobRow


async def latest(session: AsyncSession, video_id: int) -> AnalysisJobRow | None:
    """영상의 가장 최근 작업."""
    return await session.scalar(
        select(Job).where(Job.video_id == video_id).order_by(Job.started_at.desc()).limit(1)
    )


async def latest_many(session: AsyncSession, video_ids: list[int]) -> list[AnalysisJobRow]:
    """영상마다 가장 최근 작업 하나 — distinct on, 한 쿼리."""
    return list(
        await session.scalars(
            select(Job)
            .where(Job.video_id.in_(video_ids))
            .distinct(Job.video_id)
            .order_by(Job.video_id, Job.started_at.desc())
        )
    )


async def by_id(session: AsyncSession, job_id: int) -> AnalysisJobRow:
    """작업 하나. 없으면 NoResultFound — 파이프라인이 넘긴 id라 있어야 한다."""
    return (await session.scalars(select(Job).where(Job.id == job_id))).one()


async def chunks(session: AsyncSession, job_id: int) -> list[AudioChunkRow]:
    """작업의 조각들, 번호순. result는 읽지 않는다 — 폴링 응답에 안 나간다."""
    return list(
        await session.scalars(
            select(AudioChunkRow)
            .where(AudioChunkRow.job_id == job_id)
            .order_by(AudioChunkRow.seq)
            .options(defer(AudioChunkRow.result))
        )
    )


async def chunks_with_results(session: AsyncSession, job_id: int) -> list[AudioChunkRow]:
    """작업의 조각들, 번호순 — 받아쓰기 결과까지(이어 붙일 때)."""
    return list(
        await session.scalars(
            select(AudioChunkRow).where(AudioChunkRow.job_id == job_id).order_by(AudioChunkRow.seq)
        )
    )


async def has_chunks(session: AsyncSession, job_id: int) -> bool:
    """조각 행이 하나라도 있는지 — 이미 나눴으면 다시 만들지 않는다."""
    found = await session.scalar(
        select(AudioChunkRow.id).where(AudioChunkRow.job_id == job_id).limit(1)
    )
    return found is not None


def add_chunks(session: AsyncSession, job_id: int, plans: list[ChunkPlan]) -> None:
    """조각 행을 넣는다 — 전부 waiting, 보낸 횟수 0."""
    session.add_all(
        AudioChunkRow(
            job_id=job_id,
            seq=p.seq,
            offset_sec=p.offset_sec,
            duration_sec=p.duration_sec,
            path=p.path,
            state=ChunkState.waiting,
            attempts=0,
        )
        for p in plans
    )


async def chunk(session: AsyncSession, job_id: int, seq: int) -> AudioChunkRow:
    """조각 하나 — 바꿀 것이라 결과까지 읽는다."""
    return (
        await session.scalars(
            select(AudioChunkRow).where(AudioChunkRow.job_id == job_id, AudioChunkRow.seq == seq)
        )
    ).one()


async def raise_progress(session: AsyncSession, job_id: int, pct: int) -> None:
    """진행률을 올린다 — 동시에 끝난 조각들이 겹쳐 써도 뒤로 가지 않게(GREATEST)."""
    await session.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(progress_pct=func.greatest(Job.progress_pct, pct))
    )


async def chunk_counts(session: AsyncSession, job_ids: list[int]) -> dict[int, tuple[int, int]]:
    """작업마다 (완료 조각 수, 전체 조각 수) — 한 쿼리. 조각이 없는 작업은 키가 없다."""
    rows = await session.execute(
        select(
            AudioChunkRow.job_id,
            func.count().filter(AudioChunkRow.state == ChunkState.done),
            func.count(),
        )
        .where(AudioChunkRow.job_id.in_(job_ids))
        .group_by(AudioChunkRow.job_id)
    )
    return {job_id: (done, total) for job_id, done, total in rows.tuples()}


async def queued_ids(session: AsyncSession) -> list[int]:
    """기다리는 작업 id들, 차례대로."""
    return list(
        await session.scalars(
            select(Job.id).where(Job.status == JobStatus.queued).order_by(Job.queued_at, Job.id)
        )
    )


async def count_queued_before(session: AsyncSession, queued_at: datetime, job_id: int) -> int:
    """이 작업보다 먼저 들어와 기다리는 작업 수."""
    n = await session.scalar(
        select(func.count())
        .select_from(Job)
        .where(Job.status == JobStatus.queued, tuple_(Job.queued_at, Job.id) < (queued_at, job_id))
    )
    return n or 0


async def any_running(session: AsyncSession) -> bool:
    """도는 작업이 있는지."""
    found = await session.scalar(select(Job.id).where(Job.status == JobStatus.running).limit(1))
    return found is not None


async def next_queued(session: AsyncSession) -> AnalysisJobRow | None:
    """가장 오래 기다린 작업을 잠그고 읽는다. 다른 트랜잭션이 잠근 행은 건너뛴다."""
    return await session.scalar(
        select(Job)
        .where(Job.status == JobStatus.queued)
        .order_by(Job.queued_at, Job.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )


async def running_all(session: AsyncSession) -> list[AnalysisJobRow]:
    """running인 작업 전부 — 서버가 죽어 남은 것."""
    return list(await session.scalars(select(Job).where(Job.status == JobStatus.running)))


async def failed_to_waiting(session: AsyncSession, job_id: int) -> None:
    """실패한 조각을 기다림으로 — 다시 시도가 다시 보낸다. 보낸 횟수는 그대로(누적 이력)."""
    await session.execute(
        update(AudioChunkRow)
        .where(AudioChunkRow.job_id == job_id, AudioChunkRow.state == ChunkState.failed)
        .values(state=ChunkState.waiting)
    )


async def in_flight_to_waiting(session: AsyncSession, job_ids: list[int]) -> None:
    """보내던 조각을 기다림으로 — 응답을 받지 못한 채 서버가 죽었다."""
    await session.execute(
        update(AudioChunkRow)
        .where(AudioChunkRow.job_id.in_(job_ids), AudioChunkRow.state == ChunkState.in_flight)
        .values(state=ChunkState.waiting)
    )

"""job/service — 작업 시작 · 진행 · 대기열(VA-MS-002 JobService). B1 몫 전부와 스텁 둘."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.config import config
from app.core.errors import JobExists, KeyMissing, NotFound, NotImplementedYet
from app.domains.job.models import (
    AnalysisJobRow,
    AudioChunkRow,
    ChunkState,
    ErrorKind,
    JobStage,
    JobStatus,
)
from app.domains.job.schemas import JobError
from app.domains.job.service import JobService
from app.domains.video.models import SourceKind
from app.domains.video.schemas import Video

T0 = datetime(2026, 9, 23, 3, 0, tzinfo=UTC)
STT_STAGES = ["download", "transcribe", "summarize", "chapter", "suggest"]


def _video(row, status: str = "registered") -> Video:
    # 영상 묶음을 부르지 않고 DTO를 바로 — 작업 묶음은 Video를 받기만 한다
    return Video(
        **{c: getattr(row, c) for c in Video.model_fields if hasattr(row, c)},
        status=status,
        analyzed_at=None,
        chat_turn_count=0,
    )


async def _job_row(db, job_id: int) -> AnalysisJobRow:
    # 서비스가 쓴 값을 DB에서 다시 — 다른 객체는 건드리지 않는다
    return await db.scalar(
        select(AnalysisJobRow)
        .where(AnalysisJobRow.id == job_id)
        .execution_options(populate_existing=True)
    )


# --- stages_for


async def test_stages_for_four_sources(make) -> None:
    yt = await make.video()
    yt_no = await make.video(has_captions=False, caption_language=None, caption_kind=None)
    mp4 = await make.video(
        source_kind=SourceKind.local,
        channel=None,
        origin="talk.MP4",
        has_captions=False,
        caption_language=None,
        caption_kind=None,
    )
    mp3 = await make.video(
        source_kind=SourceKind.local,
        channel=None,
        origin="call.m4a",
        has_captions=False,
        caption_language=None,
        caption_kind=None,
    )
    assert JobService.stages_for(_video(yt)) == ["download", "summarize", "chapter", "suggest"]
    assert JobService.stages_for(_video(yt_no)) == STT_STAGES
    assert JobService.stages_for(_video(mp4)) == ["extract", *STT_STAGES[1:]]
    assert JobService.stages_for(_video(mp3)) == STT_STAGES[1:]  # 로컬 음성은 origin의 확장자


# --- remaining_sec


def _row(**kw) -> AnalysisJobRow:
    values = {
        "status": JobStatus.running,
        "stage": JobStage.summarize,
        "stages": ["download", "summarize", "chapter", "suggest"],
        "est_seconds": 60,
        "stage_durations_sec": {"download": 3},
        "stage_started_at": datetime.now(UTC) - timedelta(seconds=10),
        "progress_pct": 25,
        "concurrency": 3,
        "stt_model": None,
        "text_model": "gpt-5-mini",
        "est_cost_usd": Decimal("0.02"),
        "id": 1,
        "video_id": 1,
        "started_at": T0,
        "queued_at": T0,
        "finished_at": None,
    }
    return AnalysisJobRow(**(values | kw))


def test_remaining_sec_without_chunks() -> None:
    assert JobService.remaining_sec(_row(), []) in (46, 47)  # 60 − 3 − 10(남짓)
    late = _row(stage_started_at=datetime.now(UTC) - timedelta(seconds=300))
    assert JobService.remaining_sec(late, []) == 0  # 예상보다 오래 걸리면 0 — 화면이 비운다
    for status in (JobStatus.queued, JobStatus.failed, JobStatus.done):
        assert JobService.remaining_sec(_row(status=status), []) is None


def test_remaining_sec_chunks_is_stub() -> None:
    with pytest.raises(NotImplementedYet):
        JobService.remaining_sec(_row(stage=JobStage.transcribe, stages=STT_STAGES), [])


# --- to_job


def _chunk(seq: int, state: ChunkState) -> AudioChunkRow:
    return AudioChunkRow(job_id=1, seq=seq, offset_sec=0, duration_sec=600, state=state, attempts=1)


def test_to_job_stage_index_and_models() -> None:
    job = JobService.to_job(_row(stage=JobStage.chapter), [])
    assert job.stages == ["download", "summarize", "chapter", "suggest"]
    assert job.stage_index == 3
    assert job.chunks is None
    assert job.concurrency is None  # 받아쓰기가 없는 작업
    assert job.models.model_dump() == {"stt": None, "text": "gpt-5-mini"}
    assert job.error is None
    assert JobService.to_job(_row(stage=JobStage.pending), []).stage_index == 1


def test_to_job_failed_chunk_and_next_seq() -> None:
    # 16번 실패, 17번 완료 — 화면의 k는 16, 다시 시도할 r도 16
    states = (
        [ChunkState.done] * 15 + [ChunkState.failed, ChunkState.done] + [ChunkState.waiting] * 7
    )
    row = _row(
        status=JobStatus.failed,
        stage=JobStage.transcribe,
        stages=STT_STAGES,
        error_kind=ErrorKind.network,
        error_reason="시간 초과",
        error_chunk_seq=16,
        error_attempts=3,
    )
    job = JobService.to_job(row, [_chunk(i, s) for i, s in enumerate(states, 1)])
    assert job.error == JobError(
        kind=ErrorKind.network, reason="시간 초과", chunk_seq=16, attempts=3
    )
    assert job.chunks.next_seq == 16
    assert (job.chunks.total, job.chunks.done, job.chunks.failed, job.chunks.waiting) == (
        24,
        16,
        1,
        7,
    )
    assert job.concurrency == 3
    assert job.remaining_sec is None


# --- queue_position


async def test_queue_position(db, make) -> None:
    videos = [await make.video() for _ in range(3)]
    jobs = [
        await make.job(v.id, JobStatus.queued, at=T0 + timedelta(seconds=i))
        for i, v in enumerate(videos)
    ]
    svc = JobService(db)
    assert [await svc.queue_position(j) for j in jobs] == [1, 2, 3]
    jobs[0].status = JobStatus.running
    await db.commit()
    assert [await svc.queue_position(j) for j in jobs[1:]] == [1, 2]
    assert await svc.queue_position(jobs[0]) is None  # running
    for status in (JobStatus.failed, JobStatus.done):
        v = await make.video()
        assert await svc.queue_position(await make.job(v.id, status)) is None


# --- wake · wait_for_work


async def test_wait_for_work_returns_on_wake(db) -> None:
    JobService.work_event.clear()
    waiting = asyncio.create_task(JobService.wait_for_work())
    await asyncio.sleep(0)
    JobService.wake()
    await asyncio.wait_for(waiting, timeout=1)  # 곧바로 돌아온다


async def test_wait_for_work_times_out_quietly(db, monkeypatch) -> None:
    monkeypatch.setattr(config, "WORKER_IDLE_SEC", 0.05)
    JobService.work_event.clear()
    started = time.monotonic()
    await JobService.wait_for_work()  # 신호가 없어도 돌아오고, 예외가 나가지 않는다
    assert 0.04 <= time.monotonic() - started < 1


# --- estimate


async def test_estimate_captions(db, make, env_file) -> None:
    row = await make.video(duration_sec=3012)
    est = await JobService(db).estimate(_video(row))
    assert est is not None
    assert (est.needs_stt, est.chunks, est.concurrency, est.stt_minutes) == (
        False,
        None,
        None,
        None,
    )
    assert (est.stt_cost_usd, est.seconds) == (0, 60)
    assert est.text_cost_usd > 0
    assert est.total_cost_usd == round(est.text_cost_usd, 2)
    assert (est.stt_model, est.text_model) == ("whisper-1", "gpt-5-mini")


async def test_estimate_local_150_minutes(db, make, env_file) -> None:
    row = await make.video(
        source_kind=SourceKind.local,
        channel=None,
        origin="workshop.mp4",
        duration_sec=9000,
        has_captions=False,
        caption_language=None,
        caption_kind=None,
    )
    est = await JobService(db).estimate(_video(row))
    assert (est.chunks, est.concurrency, est.stt_minutes, est.stt_cost_usd) == (15, 3, 150, 0.9)
    assert est.stt_price_per_min == 0.006
    assert est.seconds == 5 * 45 + 60 + 150  # 조각 · 텍스트 · 추출 몫


async def test_estimate_none_when_job_exists(db, make, env_file) -> None:
    row = await make.video()
    await make.job(row.id, JobStatus.running)
    assert await JobService(db).estimate(_video(row, "in_progress")) is None


async def test_estimate_follows_model_price(db, make, env_file) -> None:
    row = await make.video()
    cheap = await JobService(db).estimate(_video(row))
    env_file.write_text("TEXT_MODEL=gpt-5.4\n")  # 설정에서 읽는다
    dear = await JobService(db).estimate(_video(row))
    assert dear.text_model == "gpt-5.4"
    assert dear.text_cost_usd > cheap.text_cost_usd


# --- start


async def test_start_queues_and_wakes(db, make, key) -> None:
    row = await make.video()
    job = await JobService(db).start(_video(row))
    assert job.status == JobStatus.queued  # 워커가 없으니 그대로 — 파이프라인을 기다리지 않는다
    assert job.queue_position == 1
    assert job.stage == JobStage.pending
    assert JobService.work_event.is_set()
    saved = await _job_row(db, job.id)
    assert saved.stages == ["download", "summarize", "chapter", "suggest"]
    assert saved.stt_model is None  # 자막 있는 YouTube
    assert (saved.text_model, saved.concurrency, saved.est_seconds) == ("gpt-5-mini", 3, 60)
    assert saved.queued_at == saved.started_at == saved.stage_started_at


async def test_start_twice_is_job_exists(db, make, key) -> None:
    row = await make.video()
    first = await JobService(db).start(_video(row))
    with pytest.raises(JobExists) as e:
        await JobService(db).start(_video(row))
    assert e.value.extra == {"job_id": first.id, "job_status": "queued"}


async def test_start_while_another_runs(db, make, key) -> None:
    other = await make.video()
    await make.job(other.id, JobStatus.running)
    first = await JobService(db).start(_video(await make.video()))
    assert (first.status, first.queue_position) == (JobStatus.queued, 1)  # 거절하지 않는다
    second = await JobService(db).start(_video(await make.video()))
    assert second.queue_position == 2


async def test_start_without_key_makes_no_row(db, make, env_file) -> None:
    row = await make.video()
    with pytest.raises(KeyMissing):
        await JobService(db).start(_video(row))
    assert await db.scalar(select(AnalysisJobRow)) is None

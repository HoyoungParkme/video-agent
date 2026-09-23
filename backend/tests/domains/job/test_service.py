"""job/service — 작업 시작 · 진행 · 조각 · 다시 시도 · 대기열(VA-MS-002 JobService)."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.config import config
from app.core.errors import JobExists, JobNotFailed, KeyMissing, NotFound
from app.domains.job import crud
from app.domains.job.models import (
    AnalysisJobRow,
    AudioChunkRow,
    ChunkState,
    ErrorKind,
    JobStage,
    JobStatus,
)
from app.domains.job.schemas import ChunkPlan, JobError, SttSegment
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


def _transcribe_row(started_ago: float) -> AnalysisJobRow:
    return _row(
        stage=JobStage.transcribe,
        stages=STT_STAGES,
        est_seconds=600,
        stage_durations_sec={"download": 30},
        stage_started_at=datetime.now(UTC) - timedelta(seconds=started_ago),
    )


def _chunks(row: AnalysisJobRow, done_now: int, done_before: int, total: int) -> list:
    # done_now개는 이번 실행에서, done_before개는 단계 시작 전(이전 실행)에 끝났다
    now, before = row.stage_started_at + timedelta(seconds=1), T0
    out = [_chunk(i, ChunkState.done) for i in range(1, done_now + done_before + 1)]
    for i, c in enumerate(out):
        c.done_at = now if i < done_now else before
    return out + [_chunk(i, ChunkState.waiting) for i in range(len(out) + 1, total + 1)]


def test_remaining_sec_transcribe_from_this_run_rate() -> None:
    row = _transcribe_row(started_ago=240)  # 12개가 4분 — 초당 0.05개
    got = JobService.remaining_sec(row, _chunks(row, done_now=12, done_before=0, total=30))
    assert got in (360, 361)  # 남은 18개는 6분


def test_remaining_sec_transcribe_before_first_chunk() -> None:
    row = _transcribe_row(started_ago=20)
    assert JobService.remaining_sec(row, _chunks(row, 0, 0, 30)) == 10 * 45  # 30 ÷ 동시 3 × 45초


def test_remaining_sec_transcribe_after_retry_ignores_old_chunks() -> None:
    # 다시 시도 — 이전 실행의 15개는 속도에 안 든다. 이번 실행에서 끝난 것이 없으면 예상치
    row = _transcribe_row(started_ago=2)
    assert JobService.remaining_sec(row, _chunks(row, 0, 15, 30)) == 5 * 45


def test_remaining_sec_transcribe_while_splitting() -> None:
    row = _transcribe_row(started_ago=100)  # 조각 행이 아직 없다 — 예상 전체 − 지난 시간
    assert JobService.remaining_sec(row, []) in (469, 470)  # 600 − 30 − 100


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


async def test_estimate_local_audio_counts_conversion(db, make, env_file) -> None:
    row = await make.video(
        source_kind=SourceKind.local,
        channel=None,
        origin="call.m4a",
        duration_sec=1800,
        has_captions=False,
        caption_language=None,
        caption_kind=None,
    )
    est = await JobService(db).estimate(_video(row))
    assert (est.chunks, est.stt_minutes) == (3, 30)
    assert est.seconds == 1 * 45 + 60 + 30  # 조각 · 텍스트 · mp3 변환 몫


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


async def test_start_race_is_job_exists(db, make, key, monkeypatch) -> None:
    # 확인과 넣기 사이에 같은 영상의 [분석 시작]이 먼저 들어간 경우(탭 둘) — 확인이 못 보게 한다
    row = await make.video()
    first = await JobService(db).start(_video(row))
    real, calls = crud.latest, []

    async def stale(session, video_id):
        calls.append(video_id)
        return None if len(calls) == 1 else await real(session, video_id)

    monkeypatch.setattr(crud, "latest", stale)
    with pytest.raises(JobExists) as e:
        await JobService(db).start(_video(row))
    assert e.value.extra == {"job_id": first.id, "job_status": "queued"}  # 먼저 들어간 것
    assert (await db.scalars(select(AnalysisJobRow.id))).all() == [first.id]  # 행은 하나


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


# --- progress


async def test_progress_without_job(db, make) -> None:
    row = await make.video()
    with pytest.raises(NotFound) as e:
        await JobService(db).progress(row.id)
    assert e.value.extra["resource"] == "job"


async def test_progress_queued(db, make) -> None:
    await make.job((await make.video()).id, JobStatus.running)
    row = await make.video()
    await make.job(row.id, JobStatus.queued)
    job = await JobService(db).progress(row.id)
    assert (job.status, job.queue_position, job.remaining_sec, job.chunks) == (
        JobStatus.queued,
        1,
        None,
        None,
    )
    assert job.progress_pct == 0


async def test_progress_counts_chunks_without_result(db, make, queries) -> None:
    row = await make.video(has_captions=False)
    job = await make.job(row.id, JobStatus.failed, stage="transcribe", stages=STT_STAGES)
    await make.chunks(
        job.id, [ChunkState.done] * 12 + [ChunkState.in_flight] * 3 + [ChunkState.waiting] * 15
    )
    queries.clear()
    got = await JobService(db).progress(row.id)
    assert (got.chunks.done, got.chunks.in_flight, got.chunks.waiting, got.chunks.next_seq) == (
        12,
        3,
        15,
        13,
    )
    assert len(queries) == 2  # 작업 · 조각(대기 중이 아니라 차례를 세지 않는다)
    assert all("result" not in q for q in queries)  # 받아쓰기 결과는 읽지 않는다


# --- latest · latest_by_videos


async def test_latest(db, make) -> None:
    plain = await make.video()
    await make.job(plain.id, JobStatus.running)
    s = await JobService(db).latest(plain.id)
    assert (s.chunks_done, s.chunks_total, s.failed_chunk_seq) == (None, None, None)
    failed = await make.video()
    job = await make.job(
        failed.id, JobStatus.failed, stage="transcribe", stages=STT_STAGES, error_chunk_seq=16
    )
    await make.chunks(job.id, [ChunkState.done] * 15 + [ChunkState.failed])
    s = await JobService(db).latest(failed.id)
    assert (s.chunks_done, s.chunks_total, s.failed_chunk_seq) == (15, 16, 16)
    queued = await make.video()
    await make.job(queued.id, JobStatus.queued)
    assert (await JobService(db).latest(queued.id)).queue_position == 1
    assert await JobService(db).latest((await make.video()).id) is None


async def test_latest_by_videos_constant_queries(db, make, queries) -> None:
    videos = [await make.video() for _ in range(50)]
    for i, v in enumerate(videos):
        await make.job(v.id, JobStatus.done, at=T0 + timedelta(minutes=i))
    newer = await make.job(videos[0].id, JobStatus.done, at=T0 + timedelta(days=1))
    queries.clear()
    got = await JobService(db).latest_by_videos([v.id for v in videos])
    assert len(queries) == 2  # 영상 50개에 작업 · 조각 두 쿼리
    assert len(got) == 50
    assert got[videos[0].id].id == newer.id  # 영상마다 최근 것 하나만
    await make.job((await make.video()).id, JobStatus.running)
    waiting = await make.video()
    await make.job(waiting.id, JobStatus.queued)
    queries.clear()
    got = await JobService(db).latest_by_videos([waiting.id])
    assert len(queries) == 3  # 기다리는 작업이 있으면 차례를 한 번 읽는다
    assert got[waiting.id].queue_position == 1


async def test_latest_by_videos_empty(db, queries) -> None:
    assert await JobService(db).latest_by_videos([]) == {}
    assert queries == []


# --- plan_chunks


async def test_plan_chunks_makes_rows_once(db, make) -> None:
    job = await make.job((await make.video()).id, JobStatus.running, stage="transcribe")
    plans = [ChunkPlan(i, (i - 1) * 600.0, 600.0, f"/tmp/{i}.mp3") for i in range(1, 31)]
    svc = JobService(db)
    await svc.plan_chunks(job.id, plans)
    await svc.plan_chunks(job.id, plans[:3])  # 다시 불러도 늘지 않는다(다시 시도)
    rows = (await db.scalars(select(AudioChunkRow).order_by(AudioChunkRow.seq))).all()
    assert [r.seq for r in rows] == list(range(1, 31))
    assert {(r.state, r.attempts) for r in rows} == {(ChunkState.waiting, 0)}
    assert (rows[1].offset_sec, rows[1].duration_sec, rows[1].path) == (600.0, 600.0, "/tmp/2.mp3")


# --- mark_chunk


async def _chunk_row(db, job_id: int, seq: int) -> AudioChunkRow:
    return await db.scalar(
        select(AudioChunkRow)
        .where(AudioChunkRow.job_id == job_id, AudioChunkRow.seq == seq)
        .execution_options(populate_existing=True)
    )


async def _transcribing(make, n: int, done: int = 0) -> AnalysisJobRow:
    job = await make.job(
        (await make.video()).id, JobStatus.running, stage="transcribe", stages=STT_STAGES
    )
    await make.chunks(job.id, [ChunkState.done] * done + [ChunkState.waiting] * (n - done))
    return job


async def test_mark_chunk_in_flight_counts_sends(db, make) -> None:
    job = await _transcribing(make, 3)
    svc = JobService(db)
    await svc.mark_chunk(job.id, 2, ChunkState.in_flight)
    await svc.mark_chunk(job.id, 2, ChunkState.waiting)
    await svc.mark_chunk(job.id, 2, ChunkState.in_flight)
    await svc.mark_chunk(job.id, 2, ChunkState.failed)  # 실패는 횟수를 올리지 않는다
    chunk = await _chunk_row(db, job.id, 2)
    assert (chunk.state, chunk.attempts) == (ChunkState.failed, 2)


async def test_mark_chunk_done_keeps_result_and_raises_progress(db, make) -> None:
    job = await _transcribing(make, 30, done=14)
    segs = [SttSegment(0.0, 4.2, "첫 문장", "ko"), SttSegment(4.2, 9.0, "둘째", "ko")]
    await JobService(db).mark_chunk(job.id, 15, ChunkState.done, segs)
    chunk = await _chunk_row(db, job.id, 15)
    assert chunk.state == ChunkState.done and chunk.path is None
    assert (datetime.now(UTC) - chunk.done_at).total_seconds() < 5
    assert chunk.result == [
        {"start_sec": 0.0, "end_sec": 4.2, "text": "첫 문장", "language": "ko"},
        {"start_sec": 4.2, "end_sec": 9.0, "text": "둘째", "language": "ko"},
    ]
    # 30개 중 15 완료 — 받아쓰기 몫(70)의 절반 + 앞 단계(내려받기 7.5), 내림
    assert (await _job_row(db, job.id)).progress_pct == 42


async def test_mark_chunk_progress_never_goes_back(db, make) -> None:
    job = await _transcribing(make, 30, done=1)
    row = await _job_row(db, job.id)
    row.progress_pct = 60  # 동시에 끝난 다른 조각이 먼저 더 크게 적었다
    await db.commit()
    await JobService(db).mark_chunk(job.id, 2, ChunkState.done, [])
    assert (await _job_row(db, job.id)).progress_pct == 60


# --- mark_stage · finish · fail


async def test_mark_stage_captions(db, make) -> None:
    job = await make.job((await make.video()).id, JobStatus.running)
    await JobService(db).mark_stage(job.id, JobStage.download)
    row = await _job_row(db, job.id)
    assert row.stage_durations_sec == {}  # pending에서 첫 단계로 — 걸린 시간 없음
    assert row.progress_pct == 0
    row.stage_started_at -= timedelta(seconds=3)
    await db.commit()
    await JobService(db).mark_stage(job.id, JobStage.summarize)
    row = await _job_row(db, job.id)
    assert row.stage_durations_sec == {"download": 3}
    assert row.progress_pct == 25
    assert (row.stage, (datetime.now(UTC) - row.stage_started_at).total_seconds() < 5) == (
        JobStage.summarize,
        True,
    )


async def test_mark_stage_with_transcribe(db, make) -> None:
    job = await make.job(
        (await make.video()).id, JobStatus.running, stage="transcribe", stages=STT_STAGES
    )
    await JobService(db).mark_stage(job.id, JobStage.summarize)
    assert (await _job_row(db, job.id)).progress_pct == 77  # 70 + 7.5 → 내림


async def test_mark_stage_reentering_transcribe_keeps_done_share(db, make) -> None:
    # 다시 시도 — 30개 중 15 완료에서 받아쓰기로 다시 들어가면 진행률이 앞 단계 몫으로 떨어지지 않는다
    job = await _transcribing(make, 30, done=15)
    row = await _job_row(db, job.id)
    row.stage_durations_sec = {"download": 40, "transcribe": 300}
    row.stage_started_at = datetime.now(UTC) - timedelta(seconds=2)  # claim_next가 막 적은 때
    await db.commit()
    await JobService(db).mark_stage(job.id, JobStage.transcribe)
    row = await _job_row(db, job.id)
    assert row.progress_pct == 42  # 7.5 + 70 × 15/30, 내림
    assert row.stage_durations_sec == {"download": 40, "transcribe": 302}  # 걸린 시간은 더한다


async def test_finish(db, make) -> None:
    video = await make.video()
    job = await make.job(video.id, JobStatus.running, stage="suggest")
    await JobService(db).finish(job.id)
    row = await _job_row(db, job.id)
    assert (row.status, row.progress_pct) == (JobStatus.done, 100)
    assert "suggest" in row.stage_durations_sec  # 마지막 단계의 걸린 시간
    assert (datetime.now(UTC) - row.finished_at).total_seconds() < 5
    # 영상의 analyzed · 분석 완료 시각은 영상 테스트의 test_get_after_finish가 본다


async def test_fail_keeps_stage_and_progress(db, make) -> None:
    video = await make.video()
    job = await make.job(video.id, JobStatus.running, stage="summarize", progress_pct=25)
    error = JobError(kind=ErrorKind.openai, reason="형식이 틀렸어요", chunk_seq=None, attempts=1)
    await JobService(db).fail(job.id, error)
    got = await JobService(db).progress(video.id)
    assert got.status == JobStatus.failed
    assert got.error == error
    assert (got.stage, got.progress_pct) == (JobStage.summarize, 25)


# --- fail_orphans · claim_next


async def test_fail_orphans(db, make) -> None:
    running = await make.job(
        (await make.video()).id, JobStatus.running, stage="transcribe", stages=STT_STAGES
    )
    await make.chunks(running.id, [ChunkState.done, ChunkState.in_flight, ChunkState.in_flight])
    queued = await make.job((await make.video()).id, JobStatus.queued)
    assert await JobService(db).fail_orphans() == 1
    row = await _job_row(db, running.id)
    assert (row.status, row.error_kind, row.error_reason) == (
        JobStatus.failed,
        ErrorKind.unknown,
        "서버가 다시 시작됨",
    )
    assert (row.error_chunk_seq, row.error_attempts) == (None, 1)
    states = list(
        await db.scalars(
            select(AudioChunkRow.state)
            .where(AudioChunkRow.job_id == running.id)
            .order_by(AudioChunkRow.seq)
        )
    )
    assert states == [ChunkState.done, ChunkState.waiting, ChunkState.waiting]
    assert (await _job_row(db, queued.id)).status == JobStatus.queued  # 기다리던 것은 그대로
    assert await JobService(db).fail_orphans() == 0


async def test_claim_next_order(db, make) -> None:
    jobs = [
        await make.job((await make.video()).id, JobStatus.queued, at=T0 + timedelta(seconds=s))
        for s in (30, 10, 20)
    ]
    got = await JobService(db).claim_next()
    assert got.id == jobs[1].id  # 가장 오래 기다린 것
    assert got.status == JobStatus.running
    assert (datetime.now(UTC) - got.stage_started_at).total_seconds() < 5
    assert await JobService(db).claim_next() is None  # 도는 작업이 있으면 꺼내지 않는다


async def test_claim_next_retried_job_waits_behind(db, make) -> None:
    first = await make.job((await make.video()).id, JobStatus.queued, at=T0)
    # 다시 시도한 작업 — started_at은 이르지만 queued_at이 늦다
    retried = await make.job(
        (await make.video()).id,
        JobStatus.queued,
        at=T0 - timedelta(hours=1),
        queued_at=T0 + timedelta(minutes=1),
        stage="summarize",
    )
    assert (await JobService(db).claim_next()).id == first.id
    assert retried.stage == JobStage.summarize


async def test_claim_next_empty(db) -> None:
    assert await JobService(db).claim_next() is None


# --- retry


async def test_retry_same_row_back_in_queue(db, make, key) -> None:
    video = await make.video(has_captions=False, caption_language=None, caption_kind=None)
    job = await make.job(
        video.id,
        JobStatus.failed,
        stage="transcribe",
        stages=STT_STAGES,
        at=T0,
        error_kind=ErrorKind.network,
        error_reason="네트워크 시간 초과",
        error_chunk_seq=2,
        error_attempts=3,
    )
    await make.chunks(job.id, [ChunkState.done, ChunkState.failed, ChunkState.waiting])
    JobService.work_event.clear()
    got = await JobService(db).retry(_video(video, "failed"))
    assert (got.id, got.status, got.stage, got.error) == (
        job.id,
        JobStatus.queued,
        JobStage.transcribe,
        None,
    )
    assert got.queue_position == 1 and JobService.work_event.is_set()
    row = await _job_row(db, job.id)
    assert (row.started_at, row.stages) == (T0, STT_STAGES)  # 같은 행 — 목록 순서도 그대로
    assert (datetime.now(UTC) - row.queued_at).total_seconds() < 5  # 대기열 끝으로 — 지금
    assert (row.error_kind, row.error_reason, row.error_chunk_seq, row.error_attempts) == (
        None,
        None,
        None,
        None,
    )
    chunks = [await _chunk_row(db, job.id, i) for i in (1, 2, 3)]
    assert [(c.state, c.attempts) for c in chunks] == [
        (ChunkState.done, 1),
        (ChunkState.waiting, 1),  # 실패 조각도 다시 보낸다. 보낸 횟수는 누적 그대로
        (ChunkState.waiting, 0),
    ]


async def test_retry_waits_behind_others(db, make, key) -> None:
    await make.job((await make.video()).id, JobStatus.running)
    await make.job((await make.video()).id, JobStatus.queued, at=datetime.now(UTC))
    video = await make.video()
    await make.job(video.id, JobStatus.failed, stage="summarize", at=T0)
    got = await JobService(db).retry(_video(video, "failed"))
    assert (got.status, got.queue_position) == (JobStatus.queued, 2)


async def test_retry_only_failed(db, make, key) -> None:
    video = await make.video()
    await make.job(video.id, JobStatus.running, stage="summarize")
    with pytest.raises(JobNotFailed) as e:
        await JobService(db).retry(_video(video, "in_progress"))
    assert e.value.extra == {"job_status": "running"}
    with pytest.raises(NotFound) as e2:
        await JobService(db).retry(_video(await make.video()))
    assert e2.value.extra["resource"] == "job"


async def test_retry_without_key_changes_nothing(db, make, env_file) -> None:
    video = await make.video()
    job = await make.job(video.id, JobStatus.failed, stage="summarize")
    with pytest.raises(KeyMissing):
        await JobService(db).retry(_video(video, "failed"))
    assert (await _job_row(db, job.id)).status == JobStatus.failed


async def test_cancel_is_noop(db) -> None:
    assert await JobService(db).cancel(1) is None

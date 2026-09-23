"""job/pipeline — 오류 종류 · 이유 한 줄 · 받아쓰기 · 첫 단계부터 · 이어서 · 대기열 워커(VA-MS-002 pipeline).

포트는 가짜로.
"""

from __future__ import annotations

import asyncio
import errno
import socket
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import openai as sdk
import pytest
from sqlalchemy import select

from app.core.config import config
from app.core.db import SessionLocal
from app.core.errors import NotImplementedYet
from app.domains.analysis.models import SegmentRow, SummaryRow, TranscriptRow
from app.domains.job import pipeline
from app.domains.job.models import (
    AnalysisJobRow,
    AudioChunkRow,
    ChunkState,
    ErrorKind,
    JobStage,
    JobStatus,
)
from app.domains.job.service import JobService
from app.domains.video.models import SourceKind, VideoRow
from app.domains.video.service import VideoService
from app.infra.errors import FfmpegError, OpenAIOutputError, YtdlpError

T0 = datetime(2026, 9, 23, 3, 0, tzinfo=UTC)
REQ = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")


STT_STAGES = ["download", "transcribe", "summarize", "chapter", "suggest"]


@pytest.fixture
def ports(monkeypatch, audio_source, audio_split, stt, summarizer, tmp_path):
    """파이프라인에 가짜 포트를 끼우고 data · inbox 폴더를 임시로."""
    monkeypatch.setattr(pipeline, "audio_source", audio_source)
    monkeypatch.setattr(pipeline, "audio_split", audio_split)
    monkeypatch.setattr(pipeline, "stt", stt)
    monkeypatch.setattr(pipeline, "summarizer", summarizer)
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(config, "INBOX_DIR", str(tmp_path / "inbox"))
    (tmp_path / "inbox").mkdir()
    return audio_source, summarizer


async def _row(job_id: int) -> AnalysisJobRow:
    async with SessionLocal() as s:
        return await s.scalar(select(AnalysisJobRow).where(AnalysisJobRow.id == job_id))


async def _running(make, **kw):
    """자막 있는 YouTube 영상과, 워커가 막 꺼낸 작업."""
    row = await make.video(**kw)
    job = await make.job(row.id, JobStatus.running)
    return VideoService.to_dto(row, None, 0), job


# --- error_kind


def test_error_kind_each() -> None:
    kind = pipeline.error_kind
    assert kind(TimeoutError()) == ErrorKind.network
    assert kind(ConnectionResetError()) == ErrorKind.network
    assert kind(socket.gaierror()) == ErrorKind.network
    assert kind(sdk.APIConnectionError(request=REQ)) == ErrorKind.network  # SDK 예외지만 네트워크
    assert kind(sdk.APITimeoutError(request=REQ)) == ErrorKind.network
    status = sdk.InternalServerError("x", response=httpx.Response(500, request=REQ), body=None)
    assert kind(status) == ErrorKind.openai
    assert kind(OpenAIOutputError("형식")) == ErrorKind.openai
    assert kind(YtdlpError("Video unavailable", "unavailable")) == ErrorKind.youtube
    assert kind(FfmpegError("bad", 1)) == ErrorKind.ffmpeg
    assert kind(OSError(errno.ENOSPC, "No space left on device")) == ErrorKind.disk
    assert kind(ValueError("x")) == ErrorKind.unknown
    assert kind(NotImplementedYet("아직")) == ErrorKind.unknown


# --- reason_of


def _status_error(code: int, body_code: str | None = None) -> sdk.APIStatusError:
    resp = httpx.Response(code, request=REQ)
    body = (
        {"code": body_code, "message": "error"} if body_code else None
    )  # SDK는 error 안쪽을 넘긴다
    return sdk.APIStatusError("error", response=resp, body=body)


def test_reason_of_each() -> None:
    reason = pipeline.reason_of
    assert reason(sdk.APITimeoutError(request=REQ)) == "네트워크 시간 초과"
    assert reason(TimeoutError()) == "네트워크 시간 초과"
    assert reason(sdk.APIConnectionError(request=REQ)) == "네트워크에 연결할 수 없음"
    assert reason(_status_error(401)) == "API 키 인증 실패"
    assert reason(_status_error(429, "insufficient_quota")) == "OpenAI 잔액 부족"
    assert reason(_status_error(429, "rate_limit_exceeded")) == "OpenAI 요청 한도 초과"
    assert reason(_status_error(503)) == "OpenAI 서버 오류"
    assert reason(_status_error(400)) == "OpenAI가 요청을 거절함(400)"
    stderr = "WARNING: [youtube] slow\nERROR: [youtube] abc: Private video"
    assert reason(YtdlpError(stderr, "private")) == "비공개 영상"  # 영어 표준 오류 → 표
    assert reason(YtdlpError("자막을 찾지 못했습니다", "unavailable")) == "자막을 찾지 못했습니다"
    assert reason(FfmpegError("Invalid data found", 1)) == "ffmpeg 처리 실패"
    assert reason(OSError(errno.ENOSPC, "No space left on device")) == "저장 공간 부족"
    assert reason(NotImplementedYet("아직 지원하지 않아요")) == "아직 지원하지 않아요"
    assert (
        reason(OpenAIOutputError("모델 출력을 읽지 못했어요(형식)"))
        == "모델 출력을 읽지 못했어요(형식)"
    )
    assert reason(ValueError("첫 줄이에요\n둘째 줄")) == "첫 줄이에요"
    assert reason(KeyError("x")) == "알 수 없는 오류(KeyError)"


# --- run


async def test_run_captions_to_done(db, make, ports, tmp_path) -> None:
    audio_source, summarizer = ports
    video, job = await _running(make)
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.progress_pct, row.stage) == (JobStatus.done, 100, JobStage.suggest)
    assert set(row.stage_durations_sec) == {"download", "summarize", "chapter", "suggest"}
    assert audio_source.calls == [video.source_id]
    assert [name for name, _ in summarizer.calls] == [
        "summary",
        "chapters",
        "questions",
    ]  # 받아쓰기 0회
    t = await db.scalar(select(TranscriptRow))
    assert (t.source, t.language, t.model) == ("caption_manual", "ko", None)
    assert not (tmp_path / "tmp" / str(video.id)).exists()  # 끝나면 임시 폴더가 없다


async def test_run_auto_captions_source(db, make, ports) -> None:
    audio_source, _ = ports
    lines, _, _ = audio_source.result
    audio_source.result = (lines, "en", "auto")
    video, job = await _running(make)
    await pipeline.run(job.id, video)
    t = await db.scalar(select(TranscriptRow))
    assert (t.source, t.language) == ("caption_auto", "en")


async def test_run_summary_fails(db, make, ports) -> None:
    _, summarizer = ports
    summarizer.fail["summary"] = OpenAIOutputError("모델 출력을 읽지 못했어요(형식)")
    video, job = await _running(make)
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.stage, row.progress_pct) == (JobStatus.failed, JobStage.summarize, 25)
    assert (row.error_kind, row.error_reason, row.error_attempts) == (
        ErrorKind.openai,
        "모델 출력을 읽지 못했어요(형식)",
        1,
    )
    assert await db.scalar(select(SegmentRow).limit(1)) is not None  # 스크립트는 남아 있다
    assert await db.scalar(select(SummaryRow)) is None


async def test_run_download_fails_removes_tmp(db, make, ports, tmp_path) -> None:
    audio_source, _ = ports
    audio_source.error = YtdlpError("ERROR: Private video\nsecond line", "private")
    video, job = await _running(make)
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.stage, row.error_kind) == (
        JobStatus.failed,
        JobStage.download,
        ErrorKind.youtube,
    )
    assert row.error_reason == "비공개 영상"  # 영어 표준 오류는 종류별 한국어로
    assert not (tmp_path / "tmp" / str(video.id)).exists()


async def test_run_captions_vanished(db, make, ports) -> None:
    audio_source, _ = ports
    audio_source.result = None  # 등록 뒤 자막이 사라졌다
    video, job = await _running(make)
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.error_kind, row.error_reason) == (
        JobStatus.failed,
        ErrorKind.youtube,
        "자막을 찾지 못했습니다",
    )


# --- 받아쓰기 갈래


async def _stt_job(make, stages: list[str], **video_kw):
    """자막 없는 영상과 워커가 막 꺼낸 받아쓰기 작업."""
    kw = {"has_captions": False, "caption_language": None, "caption_kind": None} | video_kw
    row = await make.video(**kw)
    job = await make.job(row.id, JobStatus.running, stages=stages, stt_model="whisper-1")
    return VideoService.to_dto(row, None, 0), job


def _local(origin: str) -> dict:
    return {"source_kind": SourceKind.local, "channel": None, "origin": origin}


async def _chunks(job_id: int) -> list[AudioChunkRow]:
    async with SessionLocal() as s:
        rows = await s.scalars(
            select(AudioChunkRow).where(AudioChunkRow.job_id == job_id).order_by(AudioChunkRow.seq)
        )
        return list(rows)


async def _segments(db) -> list[tuple[float, str]]:
    rows = await db.scalars(select(SegmentRow).order_by(SegmentRow.seq))
    return [(r.start_sec, r.text) for r in rows]


async def test_run_youtube_without_captions(db, make, ports, audio_split, stt, tmp_path) -> None:
    audio_source, summarizer = ports
    video, job = await _stt_job(make, STT_STAGES)
    tmp = tmp_path / "tmp" / str(video.id)
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.progress_pct) == (JobStatus.done, 100)
    assert audio_source.audio_calls == [("download", video.source_id, str(tmp))]
    assert audio_split.calls == [(str(tmp / "audio.mp3"), str(tmp))]
    assert sorted(stt.calls) == [1, 2, 3]
    t = await db.scalar(select(TranscriptRow))
    assert (t.source, t.language, t.model) == ("stt", "ko", "whisper-1")
    segs = await _segments(db)
    assert len(segs) == 6
    assert segs[2] == (600.0, "2번 조각 첫 문장")  # 2번 조각의 0초 → 600초
    assert [name for name, _ in summarizer.calls] == ["summary", "chapters", "questions"]
    assert not tmp.exists()


async def test_run_local_audio_converts_before_split(db, make, ports, audio_split, tmp_path):
    audio_source, _ = ports
    original = tmp_path / "inbox" / "call.wav"
    original.write_bytes(b"wav")
    video, job = await _stt_job(make, STT_STAGES[1:], **_local("call.wav"))
    tmp = tmp_path / "tmp" / str(video.id)
    await pipeline.run(job.id, video)
    assert (await _row(job.id)).status == JobStatus.done
    # 추출 단계는 없지만 받아쓰기 단계가 mp3로 바꾼 뒤 나눈다 — inbox 원본은 그대로
    assert audio_source.audio_calls == [("extract", str(original), str(tmp))]
    assert audio_split.calls == [(str(tmp / "audio.mp3"), str(tmp))]
    assert original.read_bytes() == b"wav"


async def test_run_local_video_extracts(db, make, ports, tmp_path) -> None:
    audio_source, _ = ports
    (tmp_path / "inbox" / "talk.mp4").write_bytes(b"mp4")
    video, job = await _stt_job(make, ["extract", *STT_STAGES[1:]], **_local("talk.mp4"))
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert row.status == JobStatus.done
    assert [c[0] for c in audio_source.audio_calls] == ["extract"]
    assert set(row.stage_durations_sec) == {
        "extract",
        "transcribe",
        "summarize",
        "chapter",
        "suggest",
    }


async def test_run_audio_download_fails_removes_tmp(db, make, ports, tmp_path) -> None:
    audio_source, _ = ports
    audio_source.audio_error = YtdlpError("ERROR: [youtube] abc: Video unavailable", "unavailable")
    video, job = await _stt_job(make, STT_STAGES)
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.stage, row.error_kind, row.error_reason) == (
        JobStatus.failed,
        JobStage.download,
        ErrorKind.youtube,
        "삭제되었거나 볼 수 없는 영상",
    )
    assert not (tmp_path / "tmp" / str(video.id)).exists()


async def test_transcribe_chunk_fails_after_three(db, make, ports, stt, tmp_path) -> None:
    stt.fail = {2: 99}
    video, job = await _stt_job(make, STT_STAGES)
    tmp = tmp_path / "tmp" / str(video.id)
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.stage, row.error_kind, row.error_reason) == (
        JobStatus.failed,
        JobStage.transcribe,
        ErrorKind.network,
        "네트워크 시간 초과",
    )
    assert (row.error_chunk_seq, row.error_attempts) == (2, 3)
    chunks = await _chunks(job.id)
    assert [(c.seq, c.state, c.attempts) for c in chunks] == [
        (1, ChunkState.done, 1),
        (2, ChunkState.failed, 3),
        (3, ChunkState.done, 1),  # 하나가 실패해도 돌던 조각은 끝까지
    ]
    assert stt.calls.count(2) == 3
    assert sorted(p.name for p in tmp.iterdir()) == [
        "2.mp3",
        "audio.mp3",
    ]  # done 조각 파일만 지운다
    assert await db.scalar(select(TranscriptRow)) is None


async def test_transcribe_keeps_concurrency(db, make, ports, audio_split, stt) -> None:
    audio_split.n, stt.delay = 7, 0.02
    video, job = await _stt_job(make, STT_STAGES)
    await pipeline.run(job.id, video)
    assert (await _row(job.id)).status == JobStatus.done
    assert stt.peak == 3  # 작업의 동시 수를 넘지 않는다


async def test_transcribe_failure_starts_no_new_chunks(db, make, ports, audio_split, stt) -> None:
    # 1번이 곧바로 세 번 실패 — 돌던 2 · 3번은 끝까지, 기다리던 4 ~ 6번은 보내지 않는다(UC-S3 3a2)
    audio_split.n = 6
    stt.fail, stt.delays = {1: 99}, {seq: 1.0 for seq in range(2, 7)}
    video, job = await _stt_job(make, STT_STAGES)
    await pipeline.run(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.error_chunk_seq, row.error_attempts) == (JobStatus.failed, 1, 3)
    assert sorted(stt.calls) == [1, 1, 1, 2, 3]
    assert [(c.seq, c.state, c.attempts) for c in await _chunks(job.id)] == [
        (1, ChunkState.failed, 3),
        (2, ChunkState.done, 1),
        (3, ChunkState.done, 1),
        (4, ChunkState.waiting, 0),
        (5, ChunkState.waiting, 0),
        (6, ChunkState.waiting, 0),
    ]


async def test_transcribe_waits_before_resending(db, make, ports, stt, monkeypatch) -> None:
    # SDK 재시도를 껐다 — 다시 보내기 전에 설정값, 그다음은 두 배를 기다린다
    monkeypatch.setattr(config, "CHUNK_RETRY_WAIT_SEC", 0.5)
    stt.fail = {2: 2}  # 두 번 실패하고 셋째에 된다
    video, job = await _stt_job(make, STT_STAGES)
    started = time.monotonic()
    await pipeline.run(job.id, video)
    assert (await _row(job.id)).status == JobStatus.done
    assert stt.calls.count(2) == 3
    assert time.monotonic() - started >= 1.45  # 0.5 + 1.0 — 기다리지 않으면 1초도 안 걸린다


# --- resume


async def _retried(job_id: int) -> None:
    # 다시 시도 — 같은 행을 queued로(JobService.retry와 같은 결과), 워커 대신 테스트가 resume을 부른다
    async with SessionLocal() as s:
        row = await s.get(AnalysisJobRow, job_id)
        row.status = JobStatus.running
        row.error_kind = row.error_reason = None
        row.error_chunk_seq = row.error_attempts = None
        await s.execute(
            AudioChunkRow.__table__.update()
            .where(AudioChunkRow.job_id == job_id, AudioChunkRow.state == ChunkState.failed)
            .values(state=ChunkState.waiting)
        )
        await s.commit()


async def test_resume_sends_only_unfinished_chunks(db, make, ports, stt) -> None:
    stt.fail = {2: 99}
    video, job = await _stt_job(make, STT_STAGES)
    await pipeline.run(job.id, video)
    stt.fail, stt.calls = {}, []
    await _retried(job.id)
    await pipeline.resume(job.id, video)
    row = await _row(job.id)
    assert (row.status, row.progress_pct) == (JobStatus.done, 100)
    assert stt.calls == [2]  # 1 · 3번은 다시 보내지 않는다 — 조각 행의 결과를 쓴다
    assert len(await _segments(db)) == 6


async def test_resume_counts_limit_again(db, make, ports, stt) -> None:
    stt.fail = {2: 99}
    video, job = await _stt_job(make, STT_STAGES)
    await pipeline.run(job.id, video)
    await _retried(job.id)
    await pipeline.resume(job.id, video)  # 또 실패 — 상한은 이번 실행에서 새로 센다
    row = await _row(job.id)
    assert (row.status, row.error_chunk_seq, row.error_attempts) == (JobStatus.failed, 2, 3)
    assert (await _chunks(job.id))[1].attempts == 6  # 누적


async def test_resume_after_summary_skips_transcription(db, make, ports, audio_split, stt) -> None:
    _, summarizer = ports
    summarizer.fail["summary"] = OpenAIOutputError("모델 출력을 읽지 못했어요(형식)")
    video, job = await _stt_job(make, STT_STAGES)
    await pipeline.run(job.id, video)
    assert (await _row(job.id)).stage == JobStage.summarize
    summarizer.fail, summarizer.calls, stt.calls, audio_split.calls = {}, [], [], []
    await _retried(job.id)
    await pipeline.resume(job.id, video)
    assert (await _row(job.id)).status == JobStatus.done
    assert (stt.calls, audio_split.calls) == ([], [])  # 스크립트가 있다 — 받아쓰기를 다시 안 한다
    assert [name for name, _ in summarizer.calls] == ["summary", "chapters", "questions"]


async def test_resume_without_chunks_or_audio_starts_from_extract(db, make, ports, audio_split):
    audio_source, _ = ports
    audio_split.error = FfmpegError("silencedetect failed", 1)
    video, job = await _stt_job(make, ["extract", *STT_STAGES[1:]], **_local("talk.mp4"))
    await pipeline.run(job.id, video)  # 나누다 멈췄다 — 조각 행이 없다
    row = await _row(job.id)
    assert (row.stage, row.error_kind, row.error_reason) == (
        JobStage.transcribe,
        ErrorKind.ffmpeg,
        "ffmpeg 처리 실패",
    )
    tmp = Path(config.DATA_DIR) / "tmp" / str(video.id)
    (tmp / "audio.mp3").unlink()  # 음성도 없어졌다
    audio_split.error, audio_source.audio_calls = None, []
    await _retried(job.id)
    await pipeline.resume(job.id, video)
    assert (await _row(job.id)).status == JobStatus.done
    assert [c[0] for c in audio_source.audio_calls] == ["extract"]  # 앞 단계부터


async def test_resume_local_audio_converts_again(db, make, ports, audio_split, tmp_path) -> None:
    audio_source, _ = ports
    (tmp_path / "inbox" / "call.m4a").write_bytes(b"m4a")
    audio_split.error = FfmpegError("bad", 1)
    video, job = await _stt_job(make, STT_STAGES[1:], **_local("call.m4a"))
    await pipeline.run(job.id, video)
    audio_split.error, audio_source.audio_calls = None, []
    await _retried(job.id)
    await pipeline.resume(job.id, video)  # 반쯤 쓴 mp3일 수 있어 늘 다시 바꾼다
    assert (await _row(job.id)).status == JobStatus.done
    assert [c[0] for c in audio_source.audio_calls] == ["extract"]


async def test_run_cancelled_writes_nothing(db, make, ports) -> None:
    _, summarizer = ports
    summarizer.delay = 5
    video, job = await _running(make)
    task = asyncio.create_task(pipeline.run(job.id, video))
    while not summarizer.calls:
        await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):  # 예외가 밖으로
        await task
    row = await _row(job.id)
    assert (row.status, row.stage, row.error_kind) == (JobStatus.running, JobStage.summarize, None)


# --- worker


async def load_video(video_id: int):
    """main.py의 load_video와 같은 일 — 짧은 세션으로 VideoService.get."""
    async with SessionLocal() as s:
        return (await VideoService(s, None, None).get(video_id)).video


def _worker(load=load_video) -> asyncio.Task:
    return asyncio.create_task(pipeline.worker(load))


async def _stop(task: asyncio.Task) -> None:
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


async def _wait_status(job_id: int, status: JobStatus, timeout: float = 5) -> None:
    async def loop():
        while (await _row(job_id)).status != status:
            await asyncio.sleep(0.02)

    await asyncio.wait_for(loop(), timeout)


async def test_worker_runs_queue_one_by_one(db, make, ports, monkeypatch) -> None:
    monkeypatch.setattr(config, "WORKER_IDLE_SEC", 0.05)
    running_seen: list[int] = []

    async def fake_run(job_id: int, video) -> None:
        async with SessionLocal() as s:
            n = len(
                list(
                    await s.scalars(
                        select(AnalysisJobRow.id).where(AnalysisJobRow.status == JobStatus.running)
                    )
                )
            )
        running_seen.append(n)
        await asyncio.sleep(0.05)
        if job_id == first.id:
            raise RuntimeError("첫 작업이 예외로 끝난다")
        async with SessionLocal() as s:
            await JobService(s).finish(job_id)

    monkeypatch.setattr(pipeline, "run", fake_run)
    first = await make.job((await make.video()).id, JobStatus.queued, at=T0)
    second = await make.job((await make.video()).id, JobStatus.queued, at=T0 + timedelta(seconds=1))
    worker = _worker()
    try:
        await _wait_status(second.id, JobStatus.done)  # 첫 작업이 예외로 끝나도 둘째가 돈다
    finally:
        await _stop(worker)
    assert running_seen == [1, 1]  # 동시에 running 둘이 없다
    assert JobService.tasks == {}
    failed = await _row(first.id)  # 예외로 끝난 작업은 실패로 접혀 대기열을 막지 않는다
    assert (failed.status, failed.error_kind, failed.error_reason) == (
        JobStatus.failed,
        ErrorKind.unknown,
        "첫 작업이 예외로 끝난다",
    )


async def test_worker_resumes_retried_and_skips_deleted(db, make, ports, monkeypatch) -> None:
    monkeypatch.setattr(config, "WORKER_IDLE_SEC", 0.05)
    calls: list[tuple[str, int]] = []

    async def fake_resume(job_id: int, video) -> None:
        calls.append(("resume", job_id))
        async with SessionLocal() as s:
            await JobService(s).finish(job_id)

    monkeypatch.setattr(pipeline, "resume", fake_resume)
    retried = await make.job((await make.video()).id, JobStatus.queued, stage="summarize")
    gone = await make.job((await make.video()).id, JobStatus.queued, at=T0 - timedelta(days=1))

    loaded: list[int] = []

    async def load(video_id: int):
        loaded.append(video_id)
        if video_id == gone.video_id:  # 그 사이 지워졌다 — 작업 행도 cascade로 없다
            async with SessionLocal() as s:
                await s.delete(await s.get(VideoRow, video_id))
                await s.commit()
            return None
        return await load_video(video_id)

    worker = _worker(load)
    try:
        await _wait_status(retried.id, JobStatus.done)
    finally:
        await _stop(worker)
    assert calls == [("resume", retried.id)]  # stage가 pending이 아니면 resume
    assert loaded[0] == gone.video_id


async def test_worker_cancel_cancels_task(db, make, ports, monkeypatch) -> None:
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def fake_run(job_id: int, video) -> None:
        started.set()
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            cancelled.set()
            raise

    monkeypatch.setattr(pipeline, "run", fake_run)
    job = await make.job((await make.video()).id, JobStatus.queued)
    worker = _worker()
    await asyncio.wait_for(started.wait(), 5)
    await _stop(worker)  # 서버 종료 — 워커 자신의 취소는 다시 던진다
    assert cancelled.is_set()  # 돌던 태스크도 취소된다
    assert (await _row(job.id)).status == JobStatus.running  # 다음 시작 때 fail_orphans가 되돌린다


async def test_worker_survives_deleted_task(db, make, ports, monkeypatch) -> None:
    monkeypatch.setattr(config, "WORKER_IDLE_SEC", 0.05)
    started = asyncio.Event()

    async def fake_run(job_id: int, video) -> None:
        if job_id == first.id:
            started.set()
            await asyncio.sleep(30)
        async with SessionLocal() as s:
            await JobService(s).finish(job_id)

    monkeypatch.setattr(pipeline, "run", fake_run)
    first = await make.job((await make.video()).id, JobStatus.queued, at=T0)
    second = await make.job((await make.video()).id, JobStatus.queued, at=T0 + timedelta(seconds=1))
    worker = _worker()
    try:
        await asyncio.wait_for(started.wait(), 5)
        JobService.tasks[first.video_id].cancel()  # 삭제가 도는 태스크를 취소한 것처럼
        async with SessionLocal() as s:  # 삭제 라우터가 행을 지운 것처럼 — 도는 작업이 없어진다
            await s.delete(await s.get(AnalysisJobRow, first.id))
            await s.commit()
        JobService.wake()
        await _wait_status(second.id, JobStatus.done)  # 워커는 살아 다음 작업을 꺼낸다
    finally:
        await _stop(worker)

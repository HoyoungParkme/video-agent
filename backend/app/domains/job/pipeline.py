"""파이프라인 — 대기열 워커와 단계 순서(VA-MS-002 pipeline). 함수 모듈이고 JobService만 띄운다.

서비스를 부를 때마다 짧은 세션을 열고 닫는다 — 십여 분 도는 태스크가 세션 하나를 잡지 않게.
작업 행은 JobService로만 만진다. 결과 저장은 AnalysisService가 한다. 영상 묶음은 import하지
않는다 — 워커는 main.py가 넘긴 load_video로 영상을 얻는다.
"""

from __future__ import annotations

import asyncio
import contextlib
import errno
import logging
import os
import re
import shutil
import socket
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING

from openai import APIConnectionError, APITimeoutError, OpenAIError

from app.core.config import config
from app.core.db import SessionLocal
from app.core.errors import NotImplementedYet
from app.domains.analysis.models import TranscriptSource
from app.domains.analysis.ports import SummarizerPort
from app.domains.analysis.schemas import CaptionLine
from app.domains.analysis.service import AnalysisService
from app.domains.job import crud
from app.domains.job.models import AudioChunkRow, ChunkState, ErrorKind, JobStage
from app.domains.job.ports import AudioSourcePort, AudioSplitPort, SttPort
from app.domains.job.schemas import JobError
from app.domains.job.service import JobService
from app.infra.errors import FfmpegError, OpenAIOutputError, YtdlpError

if TYPE_CHECKING:
    from app.domains.video.schemas import Video

log = logging.getLogger(__name__)

# main.py가 시작 때 넣는다(VA-DOM-002 6장 서비스 조립). 테스트는 가짜로 바꿔 끼운다
audio_source: AudioSourcePort | None = None
audio_split: AudioSplitPort | None = None
stt: SttPort | None = None
summarizer: SummarizerPort | None = None

# 내려받기 · 추출 · 로컬 음성 변환이 쓰는 이름(infra/ffmpeg.extract_audio)
AUDIO_NAME = "audio.mp3"
_HANGUL = re.compile(r"[가-힣]")
# yt-dlp 실패 종류 → 이유 한 줄(실패 알림 본문의 '왜')
_YTDLP_REASONS = {
    "private": "비공개 영상",
    "unavailable": "삭제되었거나 볼 수 없는 영상",
    "geo": "이 지역에서 볼 수 없는 영상",
    "network": "YouTube 연결 실패",
    "extractor": "yt-dlp가 영상을 읽지 못함 — yt-dlp 업데이트",
    "other": "yt-dlp 오류",
}


def _need[P](port: P | None, name: str) -> P:
    if port is None:
        raise RuntimeError(f"파이프라인의 포트 {name}가 조립되지 않았다(main.py)")
    return port


class JobFailure(Exception):
    """조각 상한을 넘은 받아쓰기 — 조각 번호 · 보낸 횟수를 채운 JobError를 run에 넘긴다."""

    def __init__(self, error: JobError) -> None:
        super().__init__(error.reason)
        self.error = error


class _ChunkFailed(Exception):
    # 조각 하나가 이번 실행에서 상한만큼 보내고도 실패했다
    def __init__(self, seq: int, sent: int, cause: Exception) -> None:
        super().__init__(seq)
        self.seq, self.sent, self.cause = seq, sent, cause


def error_kind(e: BaseException) -> ErrorKind:
    """VA-MS-002#pipeline.error_kind

    예외 → 실패 종류. 화면이 이것으로 실패 알림 제목을 고른다. OpenAI SDK의 연결 오류는
    SDK 예외이지만 네트워크다 — 먼저 검사한다(시간 초과 APITimeoutError도 그 하위).

    Args:
        e: 단계에서 난 예외

    Returns:
        network · openai · youtube · ffmpeg · disk · unknown
    """
    if isinstance(e, TimeoutError | ConnectionError | socket.gaierror | APIConnectionError):
        return ErrorKind.network
    if isinstance(e, OpenAIError | OpenAIOutputError):
        return ErrorKind.openai
    if isinstance(e, YtdlpError):
        return ErrorKind.youtube
    if isinstance(e, FfmpegError):
        return ErrorKind.ffmpeg
    if isinstance(e, OSError) and e.errno == errno.ENOSPC:
        return ErrorKind.disk
    return ErrorKind.unknown


def reason_of(e: BaseException) -> str:
    """VA-MS-002#pipeline.reason_of

    예외 → 실패 이유 한 줄(한국어). 화면 실패 알림 본문의 '왜'다. 메시지 첫 줄에 한글이 있으면
    앱이 만든 문장이라 그대로, 없으면(영어 SDK · yt-dlp 문구) 종류별 표로 바꾼다. 어댑터는 예외를
    그대로 올린다 — 감싸 바꾸면 error_kind가 종류를 가를 수 없다.

    Args:
        e: 단계에서 난 예외

    Returns:
        한 줄
    """
    line = _first_line(e)
    if _HANGUL.search(line):
        return line
    kind = error_kind(e)
    if kind == ErrorKind.network:
        timeout = isinstance(e, TimeoutError | APITimeoutError)
        return "네트워크 시간 초과" if timeout else "네트워크에 연결할 수 없음"
    if kind == ErrorKind.openai:
        return _openai_reason(e)
    if kind == ErrorKind.youtube:
        return _YTDLP_REASONS.get(getattr(e, "kind", "other"), _YTDLP_REASONS["other"])
    if kind == ErrorKind.ffmpeg:
        return "ffmpeg 처리 실패"
    if kind == ErrorKind.disk:
        return "저장 공간 부족"
    return f"알 수 없는 오류({type(e).__name__})"


def _openai_reason(e: BaseException) -> str:
    status = getattr(e, "status_code", None)
    if status == 401:
        return "API 키 인증 실패"
    if status == 403:
        return "OpenAI 권한 없음"
    if status == 429:
        quota = getattr(e, "code", None) == "insufficient_quota"
        return "OpenAI 잔액 부족" if quota else "OpenAI 요청 한도 초과"
    if isinstance(status, int) and status >= 500:
        return "OpenAI 서버 오류"
    if isinstance(status, int):
        return f"OpenAI가 요청을 거절함({status})"
    return "OpenAI 오류"


def _first_line(e: BaseException) -> str:
    text = str(e).strip()
    return text.splitlines()[0].strip() if text else type(e).__name__


async def transcribe_stage(job_id: int, video: Video, audio: str | None, tmp: str) -> None:
    """VA-MS-002#pipeline.transcribe_stage

    조각 병렬 받아쓰기. 조각 행이 없으면 음성을 나눠 만든다. done이 아닌 조각만 동시 수만큼
    보내고, 조각마다 이번 실행에서 상한만큼 자동으로 다시 보낸다(다시 시도하면 새로 센다).
    하나가 상한을 넘어도 돌던 조각은 끝까지 기다린다 — 완료 수와 다음 조각 번호가 맞게. 다
    끝나면 조각 결과에 오프셋을 더해 이어 붙여 스크립트로 저장한다.

    Args:
        job_id: 작업 id
        video: 영상
        audio: 나눌 음성(tmp 안 mp3). 조각 행이 이미 있으면(다시 시도) 쓰지 않는다
        tmp: 임시 폴더 — 조각 파일을 쓴다

    Raises:
        JobFailure: 조각 하나가 상한을 넘었다 — 가장 작은 번호의 조각으로
    """
    split_port, stt_port = _need(audio_split, "audio_split"), _need(stt, "stt")
    async with SessionLocal() as s:
        row = await crud.by_id(s, job_id)
        concurrency, model = row.concurrency, row.stt_model or ""
        chunks = await crud.chunks(s, job_id)
    if not chunks:
        plans = await split_port.split(_need(audio, "audio"), tmp)
        async with SessionLocal() as s:
            await JobService(s).plan_chunks(job_id, plans)
            chunks = await crud.chunks(s, job_id)
    sem = asyncio.Semaphore(concurrency)

    async def one(c: AudioChunkRow) -> None:
        sent = 0  # 이번 실행에서 보낸 횟수
        async with sem:
            while True:
                async with SessionLocal() as s:
                    await JobService(s).mark_chunk(job_id, c.seq, ChunkState.in_flight)
                sent += 1
                try:
                    segments = await stt_port.transcribe(_need(c.path, "조각 파일"), model)
                except Exception as e:
                    state = ChunkState.waiting
                    if sent >= config.CHUNK_MAX_ATTEMPTS:
                        state = ChunkState.failed
                    async with SessionLocal() as s:
                        await JobService(s).mark_chunk(job_id, c.seq, state)
                    if state == ChunkState.failed:
                        raise _ChunkFailed(c.seq, sent, e) from e
                    continue
                async with SessionLocal() as s:
                    await JobService(s).mark_chunk(job_id, c.seq, ChunkState.done, segments)
                with contextlib.suppress(FileNotFoundError):
                    os.remove(c.path)
                return

    todo = [c for c in chunks if c.state != ChunkState.done]
    results = await asyncio.gather(*(one(c) for c in todo), return_exceptions=True)
    failed = sorted((r for r in results if isinstance(r, _ChunkFailed)), key=lambda f: f.seq)
    if failed:
        f = failed[0]
        reason, kind = reason_of(f.cause), error_kind(f.cause)
        raise JobFailure(JobError(kind=kind, reason=reason, chunk_seq=f.seq, attempts=f.sent))
    for r in results:
        if isinstance(r, BaseException):
            raise r
    await _save_stt(job_id, video, model)


async def _save_stt(job_id: int, video: Video, model: str) -> None:
    # 조각 순서대로, 결과 시각에 조각 오프셋을 더해 이어 붙인다. 언어는 처음 나온 조각의 것
    async with SessionLocal() as s:
        rows = await crud.chunks_with_results(s, job_id)
    lines: list[CaptionLine] = []
    language = ""
    for c in rows:
        for seg in c.result or []:
            language = language or seg.get("language", "")
            start, end = c.offset_sec + seg["start_sec"], c.offset_sec + seg["end_sec"]
            lines.append(CaptionLine(start, end, seg["text"]))
    async with SessionLocal() as s:
        await AnalysisService(s, _need(summarizer, "summarizer")).save_transcript(
            video.id, TranscriptSource.stt, language or "und", model, lines
        )


async def run(job_id: int, video: Video) -> None:
    """VA-MS-002#pipeline.run

    첫 단계부터 끝까지. 워커가 띄운 태스크 안에서 돈다. 단계마다 mark_stage 뒤 실행하고,
    끝나면 finish와 임시 폴더 정리. 실패하면 fail로 접고, 취소되면 아무것도 쓰지 않는다.

    Args:
        job_id: 작업 id
        video: 영상(load_video가 준 것)
    """
    await _drive(job_id, video)


async def resume(job_id: int, video: Video) -> None:
    """VA-MS-002#pipeline.resume

    실패한 단계부터 이어서. 스텁 — B2(VA-CODE-001 B1). 다시 시도가 501이라 B1에서는
    stage가 pending이 아닌 작업이 대기열에 들어오지 않는다.

    Raises:
        NotImplementedYet: 아직 없다
    """
    raise NotImplementedYet("이어서 다시 시도는 아직 지원하지 않아요")


async def _drive(job_id: int, video: Video) -> None:
    # run의 몸 — 첫 단계부터
    tmp = Path(config.DATA_DIR) / "tmp" / str(video.id)
    stage: JobStage | None = None
    try:
        async with SessionLocal() as s:
            row = await crud.by_id(s, job_id)
            stages = [JobStage(name) for name in row.stages]
        tmp.mkdir(parents=True, exist_ok=True)
        audio: str | None = None
        for stage in stages:
            async with SessionLocal() as s:
                await JobService(s).mark_stage(job_id, stage)
            audio = await _stage(stage, job_id, video, stages, tmp, audio)
        async with SessionLocal() as s:
            await JobService(s).finish(job_id)
        shutil.rmtree(tmp, ignore_errors=True)
    except asyncio.CancelledError:
        raise  # 삭제 · 서버 종료 — 행과 조각 파일은 그대로 둔다
    except Exception as e:
        log.warning("작업 %d이 %s 단계에서 실패: %s", job_id, stage, type(e).__name__)
        error = e.error if isinstance(e, JobFailure) else _error_of(e)
        async with SessionLocal() as s:
            await JobService(s).fail(job_id, error)
        if stage in (None, JobStage.download, JobStage.extract):  # 임시 파일이 쓸모없다
            shutil.rmtree(tmp, ignore_errors=True)


def _local_audio(stages: list[JobStage]) -> bool:
    # 로컬 음성은 내려받기 · 추출 단계가 없다(UC-H2 2b)
    return JobStage.download not in stages and JobStage.extract not in stages


async def _stage(
    stage: JobStage, job_id: int, video: Video, stages: list[JobStage], tmp: Path, audio: str | None
) -> str | None:
    # 단계 하나. 서비스 호출마다 짧은 세션. 음성을 마련한 단계는 그 경로를 돌려준다
    source = _need(audio_source, "audio_source")
    if stage == JobStage.download:
        if video.has_captions:
            got = await source.captions(video.source_id)
            if got is None:  # 등록 뒤 자막이 사라졌다 — 단계 목록에 받아쓰기가 없다
                raise YtdlpError("자막을 찾지 못했습니다", "unavailable")
            lines, lang, kind = got
            src = (
                TranscriptSource.caption_manual
                if kind == "manual"
                else TranscriptSource.caption_auto
            )
            async with SessionLocal() as s:
                await AnalysisService(s, _need(summarizer, "summarizer")).save_transcript(
                    video.id, src, lang, None, lines
                )
            return None
        return await source.download_audio(video.source_id, str(tmp))
    if stage == JobStage.extract:
        return await source.extract_audio(str(Path(config.INBOX_DIR) / video.origin), str(tmp))
    if stage == JobStage.transcribe:
        if audio is None:
            async with SessionLocal() as s:
                has_chunks = await crud.has_chunks(s, job_id)
            if not has_chunks and _local_audio(stages):
                # 로컬 음성 — 추출 단계가 없어 여기서 mp3로 바꾼다. inbox 원본은 읽기만 한다
                inbox = str(Path(config.INBOX_DIR) / video.origin)
                audio = await source.extract_audio(inbox, str(tmp))
            elif not has_chunks:
                audio = str(tmp / AUDIO_NAME)  # 다시 시도 — 앞 단계가 다 써 둔 음성
        await transcribe_stage(job_id, video, audio, str(tmp))
        return None
    async with SessionLocal() as s:
        analysis = AnalysisService(s, _need(summarizer, "summarizer"))
        if stage == JobStage.summarize:
            await analysis.generate_summary(video)
        elif stage == JobStage.chapter:
            await analysis.generate_chapters(video)
        elif stage == JobStage.suggest:
            await analysis.generate_questions(video)
    return None


def _error_of(e: Exception) -> JobError:
    return JobError(kind=error_kind(e), reason=reason_of(e), chunk_seq=None, attempts=1)


async def worker(load_video: Callable[[int], Awaitable[Video | None]]) -> None:
    """VA-MS-002#pipeline.worker

    대기열 워커 — 한 번에 하나씩 차례로 돌린다. main.py lifespan이 태스크 하나로 띄우고
    끝없이 돈다. 태스크의 취소(삭제)는 삼키고, 예외는 그 작업을 실패로 접고 다음 작업으로
    간다 — running으로 남으면 대기열이 막힌다. 워커 자신이 취소되면(서버 종료) 돌던 태스크도
    취소하고 끝난다 — 그 작업은 running으로 남고 다음 시작 때 fail_orphans가 되돌린다.

    Args:
        load_video: 영상 id → Video(없으면 None). main.py가 VideoService.get을 감싸 넘긴다
    """
    while True:
        JobService.work_event.clear()  # 확인하기 전에 — 확인과 잠들기 사이에 온 신호를 잃지 않게
        try:
            async with SessionLocal() as s:
                row = await JobService(s).claim_next()
        except Exception:  # DB가 잠깐 안 되는 등 — 워커는 죽지 않고 조금 뒤 다시 본다
            log.exception("대기열을 보지 못했다")
            row = None
        if row is None:
            await JobService.wait_for_work()
            continue
        try:
            video = await load_video(row.video_id)
        except Exception as e:  # running으로 꺼낸 채 두면 대기열이 막힌다 — 실패로 접는다
            log.exception("작업 %d의 영상을 읽지 못했다", row.id)
            await _fail_quietly(row.id, e)
            continue
        if video is None:  # 그 사이 지워졌다 — 행도 cascade로 없다
            continue
        coro = run(row.id, video) if row.stage == JobStage.pending else resume(row.id, video)
        task = asyncio.create_task(coro)
        JobService.tasks[video.id] = task
        try:
            await asyncio.wait({task})
        except asyncio.CancelledError:  # 워커 자신이 취소됐다(서버 종료)
            task.cancel()
            await asyncio.wait({task})
            raise
        finally:
            JobService.tasks.pop(video.id, None)
        error = None if task.cancelled() else task.exception()
        if isinstance(
            error, Exception
        ):  # run이 fail로 접지 못했다 — running으로 두면 대기열이 막힌다
            log.error("작업 %d의 태스크가 예외로 끝났다", row.id, exc_info=error)
            await _fail_quietly(row.id, error)


async def _fail_quietly(job_id: int, e: Exception) -> None:
    try:
        async with SessionLocal() as s:
            await JobService(s).fail(job_id, _error_of(e))
    except Exception:
        log.exception("작업 %d을 실패로 적지 못했다 — 다음 시작 때 fail_orphans가 되돌린다", job_id)

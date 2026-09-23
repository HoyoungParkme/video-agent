"""파이프라인 — 대기열 워커와 단계 순서(VA-MS-002 pipeline). 함수 모듈이고 JobService만 띄운다.

서비스를 부를 때마다 짧은 세션을 열고 닫는다 — 십여 분 도는 태스크가 세션 하나를 잡지 않게.
작업 행은 JobService로만 만진다. 결과 저장은 AnalysisService가 한다. 영상 묶음은 import하지
않는다 — 워커는 main.py가 넘긴 load_video로 영상을 얻는다.
"""

from __future__ import annotations

import asyncio
import errno
import logging
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
from app.domains.analysis.service import AnalysisService
from app.domains.job import crud
from app.domains.job.models import ErrorKind, JobStage
from app.domains.job.ports import AudioSourcePort
from app.domains.job.schemas import JobError
from app.domains.job.service import JobService
from app.infra.errors import FfmpegError, OpenAIOutputError, YtdlpError

if TYPE_CHECKING:
    from app.domains.video.schemas import Video

log = logging.getLogger(__name__)

# main.py가 시작 때 넣는다(VA-DOM-002 6장 서비스 조립). 테스트는 가짜로 바꿔 끼운다
audio_source: AudioSourcePort | None = None
summarizer: SummarizerPort | None = None

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


def _ports() -> tuple[AudioSourcePort, SummarizerPort]:
    if audio_source is None or summarizer is None:
        raise RuntimeError("파이프라인의 포트가 조립되지 않았다(main.py)")
    return audio_source, summarizer


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


async def transcribe_stage(job_id: int, video: Video, audio: str, tmp: str) -> None:
    """VA-MS-002#pipeline.transcribe_stage

    조각 병렬 받아쓰기. 스텁 — B2(VA-CODE-001 B1). 자막 없는 영상은 화면이 시작 전에 막는다.

    Raises:
        NotImplementedYet: 아직 없다
    """
    raise NotImplementedYet("받아쓰기는 아직 지원하지 않아요")


async def run(job_id: int, video: Video) -> None:
    """VA-MS-002#pipeline.run

    첫 단계부터 끝까지. 워커가 띄운 태스크 안에서 돈다. 단계마다 mark_stage 뒤 실행하고,
    끝나면 finish와 임시 폴더 정리. 실패하면 fail로 접고, 취소되면 아무것도 쓰지 않는다.
    B1은 자막 갈래만 — 음성 내려받기 · 추출 · 받아쓰기는 스텁(VA-CODE-001 B1).

    Args:
        job_id: 작업 id
        video: 영상(load_video가 준 것)
    """
    tmp = Path(config.DATA_DIR) / "tmp" / str(video.id)
    stage: JobStage | None = None
    try:
        async with SessionLocal() as s:
            stages = (await crud.by_id(s, job_id)).stages
        tmp.mkdir(parents=True, exist_ok=True)
        for name in stages:
            stage = JobStage(name)
            async with SessionLocal() as s:
                await JobService(s).mark_stage(job_id, stage)
            await _stage(stage, job_id, video, tmp)
        async with SessionLocal() as s:
            await JobService(s).finish(job_id)
        shutil.rmtree(tmp, ignore_errors=True)
    except asyncio.CancelledError:
        raise  # 삭제 · 서버 종료 — 행은 그대로 둔다
    except Exception as e:
        log.warning("작업 %d이 %s 단계에서 실패: %s", job_id, stage, type(e).__name__)
        error = JobError(kind=error_kind(e), reason=reason_of(e), chunk_seq=None, attempts=1)
        async with SessionLocal() as s:
            await JobService(s).fail(job_id, error)
        if stage in (None, JobStage.download, JobStage.extract):  # 임시 파일이 쓸모없다
            shutil.rmtree(tmp, ignore_errors=True)


async def _stage(stage: JobStage, job_id: int, video: Video, tmp: Path) -> None:
    # 단계 하나. 서비스 호출마다 짧은 세션
    source_port, summarizer_port = _ports()
    if stage == JobStage.download:
        if not video.has_captions:
            raise NotImplementedYet("자막 없는 영상의 음성 내려받기는 아직 지원하지 않아요")
        got = await source_port.captions(video.source_id)
        if got is None:  # 등록 뒤 자막이 사라졌다 — 단계 목록에 받아쓰기가 없다
            raise YtdlpError("자막을 찾지 못했습니다", "unavailable")
        lines, lang, kind = got
        source = (
            TranscriptSource.caption_manual if kind == "manual" else TranscriptSource.caption_auto
        )
        async with SessionLocal() as s:
            await AnalysisService(s, summarizer_port).save_transcript(
                video.id, source, lang, None, lines
            )
    elif stage == JobStage.extract:
        raise NotImplementedYet("영상 파일의 음성 추출은 아직 지원하지 않아요")
    elif stage == JobStage.transcribe:
        audio = str(Path(config.INBOX_DIR) / video.origin)  # 로컬 음성 파일(B2가 갈래를 채운다)
        await transcribe_stage(job_id, video, audio, str(tmp))
    else:
        async with SessionLocal() as s:
            analysis = AnalysisService(s, summarizer_port)
            if stage == JobStage.summarize:
                await analysis.generate_summary(video)
            elif stage == JobStage.chapter:
                await analysis.generate_chapters(video)
            elif stage == JobStage.suggest:
                await analysis.generate_questions(video)


async def resume(job_id: int, video: Video) -> None:
    """VA-MS-002#pipeline.resume

    실패한 단계부터 이어서. 스텁 — B2(VA-CODE-001 B1). 다시 시도가 501이라 B1에서는
    stage가 pending이 아닌 작업이 대기열에 들어오지 않는다.

    Raises:
        NotImplementedYet: 아직 없다
    """
    raise NotImplementedYet("이어서 다시 시도는 아직 지원하지 않아요")


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
        error = JobError(kind=error_kind(e), reason=reason_of(e), chunk_seq=None, attempts=1)
        async with SessionLocal() as s:
            await JobService(s).fail(job_id, error)
    except Exception:
        log.exception("작업 %d을 실패로 적지 못했다 — 다음 시작 때 fail_orphans가 되돌린다", job_id)

"""파이프라인 — 대기열 워커와 단계 순서(VA-MS-002 pipeline). 함수 모듈이고 JobService만 띄운다.

서비스를 부를 때마다 짧은 세션을 열고 닫는다 — 십여 분 도는 태스크가 세션 하나를 잡지 않게.
작업 행은 JobService로만 만진다. 결과 저장은 AnalysisService가 한다. 영상 묶음은 import하지
않는다 — 워커는 main.py가 넘긴 load_video로 영상을 얻는다.
"""

from __future__ import annotations

import asyncio
import errno
import logging
import shutil
import socket
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING

from openai import APIConnectionError, OpenAIError

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


async def transcribe_stage(job_id: int, video: Video, audio: str, tmp: str) -> None:
    """VA-MS-002#pipeline.transcribe_stage

    조각 병렬 받아쓰기. 스텁 — B2(VA-CODE-001 B1). 자막 없는 영상은 화면이 시작 전에 막는다.

    Raises:
        NotImplementedYet: 아직 없다
    """
    raise NotImplementedYet("받아쓰기는 아직 지원하지 않아요")


def _first_line(e: BaseException) -> str:
    # 실패 이유 한 줄 — 한국어 문구는 어댑터 · 서비스가 만든다
    text = str(e).strip()
    return text.splitlines()[0] if text else type(e).__name__

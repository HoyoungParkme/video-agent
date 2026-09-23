"""JobService — 분석 작업의 시작 · 진행 · 대기열(VA-MS-002). 단계를 도는 것은 pipeline.py.

세션은 부르는 쪽(라우터 · 파이프라인의 짧은 세션)의 것이다. 도는 태스크의 핸들과 워커를 깨우는
신호는 프로세스에 하나라 클래스 속성이다(VA-DOM-002 6장). 영상은 `Video` DTO로만 받는다 —
영상 묶음을 import하지 않는다(타입 검사 때만).
"""

from __future__ import annotations

import asyncio
import contextlib
import math
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import PurePath
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.core.errors import JobExists, NotFound, NotImplementedYet
from app.core.settings import Models, settings
from app.domains.job import crud
from app.domains.job.models import (
    AnalysisJobRow,
    AudioChunkRow,
    ChunkState,
    ErrorKind,
    JobStage,
    JobStatus,
)
from app.domains.job.schemas import Chunk, Chunks, Estimate, Job, JobError, JobSummary

if TYPE_CHECKING:
    from app.domains.video.schemas import Video

# 로컬 음성 파일 — 음성 추출 단계가 없다(UC-H2 2b)
AUDIO_EXTS = {"mp3", "m4a", "wav"}
# 받아쓰기가 있는 작업에서 받아쓰기 몫. 나머지 단계가 100에서 이것을 뺀 몫을 똑같이 나눈다(0장)
TRANSCRIBE_WEIGHT = 70
# 서버가 죽어 running인 채 남은 작업의 실패 이유
ORPHAN_REASON = "서버가 다시 시작됨"


def _weights(stages: list[str]) -> dict[str, float]:
    t = JobStage.transcribe.value
    if t in stages:
        rest = [s for s in stages if s != t]
        return {t: TRANSCRIBE_WEIGHT} | {s: (100 - TRANSCRIBE_WEIGHT) / len(rest) for s in rest}
    return {s: 100 / len(stages) for s in stages}


def _done_pct(stages: list[str], stage: str) -> int:
    # 앞선 단계들의 가중치 합을 내림한다 — 7.5 + 70 = 77(마지막은 finish가 100으로 맞춘다)
    w = _weights(stages)
    return int(sum(w[s] for s in stages[: stages.index(stage)]))


def _elapsed(since: datetime) -> float:
    return (datetime.now(UTC) - since).total_seconds()


def _is_audio(video: Video) -> bool:
    # 로컬 음성 판정은 파일 이름(origin)의 확장자
    suffix = PurePath(video.origin).suffix.lower().lstrip(".")
    return video.source_kind == "local" and suffix in AUDIO_EXTS


class JobService:
    """작업 행과 조각 행을 만지고, 응답 형태로 바꾸고, 대기열 워커를 깨운다.

    - estimate() · start() · progress(): 사전 안내 예상치 · 작업 시작(늘 queued) · 폴링 응답
    - latest() · latest_by_videos(): 영상에 붙는 최근 작업 요약
    - mark_stage() · finish() · fail(): 파이프라인이 단계마다 부른다
    - fail_orphans() · claim_next() · wake() · wait_for_work(): 서버 시작 정리와 대기열
    - retry() · cancel(): 스텁 — B2 · B4에서 채운다(VA-CODE-001 B1)
    """

    # 도는 파이프라인 태스크(영상 id → 태스크). 워커가 넣고 빼며, 삭제가 취소한다(B4)
    tasks: ClassVar[dict[int, asyncio.Task[None]]] = {}
    # 워커를 깨우는 신호 — 메모리에 있는 것은 이것뿐이고 대기열은 DB의 queued 행이다
    work_event: ClassVar[asyncio.Event] = asyncio.Event()

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def stages_for(video: Video) -> list[JobStage]:
        """VA-MS-002#JobService.stages_for

        출처에 필요한 단계만, 순서대로 — 화면의 단계 목록이 이것을 그대로 그린다.

        Args:
            video: 영상(출처 · 자막 유무 · 파일 이름)

        Returns:
            단계 목록
        """
        tail = [JobStage.summarize, JobStage.chapter, JobStage.suggest]
        if video.source_kind == "youtube":
            if video.has_captions:
                return [JobStage.download, *tail]
            return [JobStage.download, JobStage.transcribe, *tail]
        if _is_audio(video):
            return [JobStage.transcribe, *tail]
        return [JobStage.extract, JobStage.transcribe, *tail]

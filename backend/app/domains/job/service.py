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

    @staticmethod
    def remaining_sec(row: AnalysisJobRow, chunks: list[AudioChunkRow]) -> int | None:
        """VA-MS-002#JobService.remaining_sec

        남은 시간. 조각이 없는 단계는 예상 전체 시간에서 지난 시간을 뺀다(0 아래로 가지 않는다).
        받아쓰기 단계(조각 갈래)는 스텁 — B2(VA-CODE-001 B1).

        Args:
            row: 작업 행
            chunks: 작업의 조각들

        Returns:
            초. 돌고 있지 않으면 None, 0이면 화면이 비운다
        """
        if row.status != JobStatus.running:
            return None
        if row.stage == JobStage.transcribe:
            raise NotImplementedYet("받아쓰기의 남은 시간은 아직 지원하지 않아요")
        spent = sum(row.stage_durations_sec.values()) + _elapsed(row.stage_started_at)
        return max(round(row.est_seconds - spent), 0)

    @staticmethod
    def to_job(
        row: AnalysisJobRow, chunks: list[AudioChunkRow], queue_position: int | None = None
    ) -> Job:
        """VA-MS-002#JobService.to_job

        행 + 조각 → 폴링 응답. 차례는 DB를 읽어야 해서 부르는 쪽이 세어 넘긴다 — 순수 함수.

        Args:
            row: 작업 행
            chunks: 조각들(번호순)
            queue_position: 대기열에서의 차례

        Returns:
            Job
        """
        items = [Chunk(seq=c.seq, state=c.state) for c in chunks]
        states = [c.state for c in chunks]
        chunks_dto = (
            Chunks(
                total=len(chunks),
                done=states.count(ChunkState.done),
                in_flight=states.count(ChunkState.in_flight),
                failed=states.count(ChunkState.failed),
                waiting=states.count(ChunkState.waiting),
                next_seq=next((c.seq for c in chunks if c.state != ChunkState.done), None),
                items=items,
            )
            if chunks
            else None
        )
        error = (
            JobError(
                kind=row.error_kind,
                reason=row.error_reason,
                chunk_seq=row.error_chunk_seq,
                attempts=row.error_attempts,
            )
            if row.status == JobStatus.failed
            else None
        )
        return Job(
            id=row.id,
            video_id=row.video_id,
            status=row.status,
            stage=row.stage,
            queue_position=queue_position,
            stages=row.stages,
            stage_index=row.stages.index(row.stage) + 1 if row.stage != JobStage.pending else 1,
            progress_pct=row.progress_pct,
            remaining_sec=JobService.remaining_sec(row, chunks),
            chunks=chunks_dto,
            concurrency=row.concurrency if JobStage.transcribe in row.stages else None,
            models=Models(stt=row.stt_model, text=row.text_model),
            error=error,
            est_seconds=row.est_seconds,
            est_cost_usd=float(row.est_cost_usd),
            stage_durations_sec=row.stage_durations_sec,
            started_at=row.started_at,
            finished_at=row.finished_at,
        )

    async def queue_position(self, row: AnalysisJobRow) -> int | None:
        """VA-MS-002#JobService.queue_position

        대기열에서의 차례 — 1이 바로 다음. UI-1 '{n}번째'와 UI-3 '앞 영상 {n}개'가 같은 값이다.

        Args:
            row: 작업 행

        Returns:
            차례. queued가 아니면 None
        """
        if row.status != JobStatus.queued:
            return None
        return await crud.count_queued_before(self.session, row.queued_at, row.id) + 1

    @classmethod
    def wake(cls) -> None:
        """VA-MS-002#JobService.wake

        워커를 깨운다. start · retry(커밋 뒤)와 삭제 라우터(삭제 뒤)가 부른다.
        """
        cls.work_event.set()

    @classmethod
    async def wait_for_work(cls) -> None:
        """VA-MS-002#JobService.wait_for_work

        깨울 때까지, 길어야 `config.WORKER_IDLE_SEC`만큼 기다린다 — 신호를 놓쳐도 다시 본다.
        신호를 지우는 것은 워커가 claim_next 전에 한다.
        """
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(cls.work_event.wait(), timeout=config.WORKER_IDLE_SEC)

    async def estimate(self, video: Video) -> Estimate | None:
        """VA-MS-002#JobService.estimate

        사전 안내의 예상 시간 · 비용. 작업이 있는 영상이면 None — 라우터는 그대로 싣는다.

        Args:
            video: register가 돌려준 영상(status · 길이 · 자막 유무 · 출처)

        Returns:
            예상치, 또는 작업이 있으면 None
        """
        if video.status != "registered":
            return None
        return self._estimate(video)

    def _estimate(self, video: Video) -> Estimate:
        # start도 부른다 — 거기서는 상태를 보지 않는다(작업이 없다는 것을 먼저 확인했다)
        models = settings.current_models()
        needs_stt = not video.has_captions
        chunks = concurrency = None
        stt_minutes = stt_price = None
        stt_cost = 0.0
        seconds = config.TEXT_EST_SEC
        if needs_stt:
            chunks = math.ceil(video.duration_sec / config.CHUNK_SEC)
            concurrency = config.STT_CONCURRENCY
            stt_minutes = round(video.duration_sec / 60, 1)
            stt_price = models.stt.price.per_min_usd or 0.0
            stt_cost = stt_minutes * stt_price
            seconds += math.ceil(chunks / concurrency) * config.CHUNK_EST_SEC
            if not _is_audio(video):  # YouTube 내려받기 · 로컬 영상 추출 몫 — 길이(분)만큼의 초
                seconds += math.ceil(video.duration_sec / 60)
        # 스크립트를 세 번(요약 · 챕터 · 추천 질문) 보내고 출력은 합쳐 6천 토큰으로 본다
        in_tokens = video.duration_sec / 60 * config.TOKENS_PER_MIN
        text_cost = (
            in_tokens * 3 * (models.text.price.input_per_mtok_usd or 0.0)
            + 6000 * (models.text.price.output_per_mtok_usd or 0.0)
        ) / 1_000_000
        return Estimate(
            needs_stt=needs_stt,
            seconds=seconds,
            chunks=chunks,
            concurrency=concurrency,
            stt_minutes=stt_minutes,
            stt_price_per_min=stt_price,
            stt_cost_usd=round(stt_cost, 4),
            text_cost_usd=round(text_cost, 4),
            total_cost_usd=round(stt_cost + text_cost, 2),
            stt_model=models.stt.id,
            text_model=models.text.id,
        )

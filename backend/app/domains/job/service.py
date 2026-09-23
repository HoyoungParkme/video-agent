"""JobService — 분석 작업의 시작 · 진행 · 대기열(VA-MS-002). 단계를 도는 것은 pipeline.py.

세션은 부르는 쪽(라우터 · 파이프라인의 짧은 세션)의 것이다. 도는 태스크의 핸들과 워커를 깨우는
신호는 프로세스에 하나라 클래스 속성이다(VA-DOM-002 6장). 영상은 `Video` DTO로만 받는다 —
영상 묶음을 import하지 않는다(타입 검사 때만).
"""

from __future__ import annotations

import asyncio
import contextlib
import math
from dataclasses import asdict
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
from app.domains.job.schemas import (
    Chunk,
    ChunkPlan,
    Chunks,
    Estimate,
    Job,
    JobError,
    JobSummary,
    SttSegment,
)

if TYPE_CHECKING:
    from app.domains.video.schemas import Video

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


def _transcribe_pct(stages: list[str], done: int, total: int) -> int:
    # 받아쓰기 앞 단계들의 몫 + 받아쓰기 몫 × 완료 비율 — 내림
    w = _weights(stages)
    base = sum(w[s] for s in stages[: stages.index(JobStage.transcribe.value)])
    return int(base + w[JobStage.transcribe.value] * done / total)


def _elapsed(since: datetime) -> float:
    return (datetime.now(UTC) - since).total_seconds()


def _is_audio(video: Video) -> bool:
    # 로컬 음성 판정은 파일 이름(origin)의 확장자 — 음성 파일은 추출 단계가 없다(UC-H2 2b)
    suffix = PurePath(video.origin).suffix.lower().lstrip(".")
    return video.source_kind == "local" and suffix in config.AUDIO_EXTS


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

    async def start(self, video: Video) -> Job:
        """VA-MS-002#JobService.start

        작업 행을 늘 `queued`로 넣고 워커를 깨운다. 다른 영상이 돌고 있어도 거절하지 않는다 —
        `running`으로 바꾸는 것은 워커 하나다. 파이프라인을 기다리지 않는다.

        Args:
            video: 라우터가 VideoService.get으로 받아 넘긴 영상

        Returns:
            만든 작업. 워커가 벌써 꺼냈으면 running, 아니면 queued와 차례

        Raises:
            KeyMissing · KeyInvalid: 키가 없거나 확인에 실패했다
            JobExists: 이 영상에 이미 작업이 있다(실패한 작업은 다시 시도로). 같은 영상에
                동시에 두 번 오면 둘째는 영상 하나에 작업 하나인 부분 unique에 걸려 이것이 된다
        """
        await settings.require_key()
        existing = await crud.latest(self.session, video.id)
        if existing is not None:
            raise self._exists(existing)
        est = self._estimate(video)
        models = settings.current_models()
        now = datetime.now(UTC)
        row = AnalysisJobRow(
            video_id=video.id,
            status=JobStatus.queued,
            stage=JobStage.pending,
            stages=[s.value for s in self.stages_for(video)],
            progress_pct=0,
            est_seconds=est.seconds,
            est_cost_usd=Decimal(str(est.total_cost_usd)),
            concurrency=config.STT_CONCURRENCY,
            stt_model=models.stt.id if est.needs_stt else None,
            text_model=models.text.id,
            stage_durations_sec={},
            started_at=now,
            queued_at=now,
            stage_started_at=now,
        )
        self.session.add(row)
        try:
            await self.session.commit()
        except IntegrityError:  # 확인과 넣기 사이에 같은 영상의 [분석 시작]이 먼저 들어갔다
            await self.session.rollback()
            existing = await crud.latest(self.session, video.id)
            if existing is None:
                raise
            raise self._exists(existing) from None
        self.wake()
        await asyncio.sleep(0)  # 워커에게 한 번 양보한다 — 도는 작업이 없으면 곧 꺼낸다
        await self.session.refresh(row)
        return self.to_job(row, [], await self.queue_position(row))

    @staticmethod
    def _exists(row: AnalysisJobRow) -> JobExists:
        return JobExists(job_id=row.id, job_status=row.status.value)

    async def progress(self, video_id: int) -> Job:
        """VA-MS-002#JobService.progress

        폴링 응답 — 영상의 가장 최근 작업. 1초마다 불리므로 쿼리 둘(대기 중이면 셋)로 끝난다.

        Args:
            video_id: 영상 id

        Returns:
            단계 · 진행률 · 조각 · 남은 시간 · 실패 내용

        Raises:
            NotFound: 작업이 없다(resource=job)
        """
        row = await crud.latest(self.session, video_id)
        if row is None:
            raise NotFound(resource="job", id=video_id)
        chunks = await crud.chunks(self.session, row.id)
        return self.to_job(row, chunks, await self.queue_position(row))

    async def latest(self, video_id: int) -> JobSummary | None:
        """VA-MS-002#JobService.latest

        영상의 가장 최근 작업 요약 — 영상 하나(VideoService.get · register)에 붙는다.

        Args:
            video_id: 영상 id

        Returns:
            작업 요약. 작업이 없으면 None
        """
        row = await crud.latest(self.session, video_id)
        if row is None:
            return None
        counts = await crud.chunk_counts(self.session, [row.id])
        done, total = counts.get(row.id, (None, None))
        return self._summary(row, done, total, await self.queue_position(row))

    @staticmethod
    def _summary(
        row: AnalysisJobRow, done: int | None, total: int | None, position: int | None
    ) -> JobSummary:
        return JobSummary(
            id=row.id,
            status=row.status,
            stage=row.stage,
            queue_position=position,
            progress_pct=row.progress_pct,
            chunks_done=done,
            chunks_total=total,
            failed_chunk_seq=row.error_chunk_seq,
            started_at=row.started_at,
            finished_at=row.finished_at,
        )

    async def latest_by_videos(self, video_ids: list[int]) -> dict[int, JobSummary]:
        """VA-MS-002#JobService.latest_by_videos

        여러 영상의 최근 작업 요약. 영상 수와 상관없이 쿼리 둘(기다리는 작업이 있으면 셋).

        Args:
            video_ids: 영상 id들

        Returns:
            {영상 id: 작업 요약}. 작업 없는 영상은 키가 없다
        """
        if not video_ids:
            return {}
        rows = await crud.latest_many(self.session, video_ids)
        if not rows:
            return {}
        counts = await crud.chunk_counts(self.session, [r.id for r in rows])
        positions: dict[int, int] = {}
        if any(r.status == JobStatus.queued for r in rows):  # 차례는 한 번 읽어 매긴다
            positions = {
                job_id: i + 1 for i, job_id in enumerate(await crud.queued_ids(self.session))
            }
        return {
            r.video_id: self._summary(r, *counts.get(r.id, (None, None)), positions.get(r.id))
            for r in rows
        }

    async def mark_stage(self, job_id: int, stage: JobStage) -> None:
        """VA-MS-002#JobService.mark_stage

        단계 전환 — 끝난 단계의 걸린 시간, 새 단계의 시작 시각, 진행률(앞선 단계 가중치 합).
        받아쓰기로 다시 들어가면(다시 시도) 이미 끝난 조각 몫까지 넣는다 — 진행률이 뒤로 가지 않게.

        Args:
            job_id: 작업 id
            stage: 이제 시작하는 단계
        """
        row = await crud.by_id(self.session, job_id)
        self._close_stage(row)
        row.stage = stage
        row.stage_started_at = datetime.now(UTC)
        row.progress_pct = _done_pct(row.stages, stage)
        if stage == JobStage.transcribe:
            counts = (await crud.chunk_counts(self.session, [job_id])).get(job_id)
            if counts:
                row.progress_pct = _transcribe_pct(row.stages, *counts)
        await self.session.commit()

    @staticmethod
    def _close_stage(row: AnalysisJobRow) -> None:
        # 처음(pending)에서 넘어갈 때는 걸린 시간이 없다. 다시 시도로 같은 단계를 또 돌면 더한다
        if row.stage != JobStage.pending:
            took = round(_elapsed(row.stage_started_at))
            key = row.stage.value
            row.stage_durations_sec = {
                **row.stage_durations_sec,
                key: row.stage_durations_sec.get(key, 0) + took,
            }

    async def plan_chunks(self, job_id: int, plans: list[ChunkPlan]) -> None:
        """VA-MS-002#JobService.plan_chunks

        조각 행을 만든다 — 전부 waiting. 이미 있으면(다시 시도) 만들지 않는다.

        Args:
            job_id: 작업 id
            plans: 자른 조각들(seq 순)
        """
        if await crud.has_chunks(self.session, job_id):
            return
        crud.add_chunks(self.session, job_id, plans)
        await self.session.commit()

    async def mark_chunk(
        self, job_id: int, seq: int, state: ChunkState, result: list[SttSegment] | None = None
    ) -> None:
        """VA-MS-002#JobService.mark_chunk

        조각 상태 전이. in_flight로 바꿀 때 보낸 횟수를 올린다. done이면 끝난 때 · 결과를 적고
        경로를 비운다(파일은 파이프라인이 지운다) — 진행률은 완료 조각 비율로 올리기만 한다.
        waiting(다시 보낼 차례) · failed는 상태만.

        Args:
            job_id: 작업 id
            seq: 조각 번호
            state: 바꿀 상태
            result: done일 때의 받아쓰기 구간들(오프셋을 더하기 전)
        """
        chunk = await crud.chunk(self.session, job_id, seq)
        if state == ChunkState.in_flight:
            chunk.attempts += 1
        elif state == ChunkState.done:
            chunk.done_at = datetime.now(UTC)
            chunk.result = [asdict(s) for s in result or []]
            chunk.path = None
        chunk.state = state
        if state == ChunkState.done:
            await self.session.flush()
            row = await crud.by_id(self.session, job_id)
            done, total = (await crud.chunk_counts(self.session, [job_id]))[job_id]
            await crud.raise_progress(
                self.session, job_id, _transcribe_pct(row.stages, done, total)
            )
        await self.session.commit()

    async def finish(self, job_id: int) -> None:
        """VA-MS-002#JobService.finish

        완료 — 마지막 단계의 걸린 시간, 진행률 100, 끝난 시각(= 영상의 분석 완료 시각).

        Args:
            job_id: 작업 id
        """
        row = await crud.by_id(self.session, job_id)
        self._close_stage(row)
        row.status = JobStatus.done
        row.progress_pct = 100
        row.finished_at = datetime.now(UTC)
        await self.session.commit()

    async def fail(self, job_id: int, error: JobError) -> None:
        """VA-MS-002#JobService.fail

        실패 — 이유를 남긴다. 단계와 진행률은 멈춘 그대로다.

        Args:
            job_id: 작업 id
            error: 종류 · 이유 · 조각 번호 · 보낸 횟수
        """
        row = await crud.by_id(self.session, job_id)
        row.status = JobStatus.failed
        row.error_kind = error.kind
        row.error_reason = error.reason
        row.error_chunk_seq = error.chunk_seq
        row.error_attempts = error.attempts
        await self.session.commit()

    async def fail_orphans(self) -> int:
        """VA-MS-002#JobService.fail_orphans

        서버가 죽어 running인 채 남은 작업을 failed로 되돌린다 — 다시 시도할 수 있게.
        queued는 건드리지 않는다. main.py가 워커를 띄우기 **전에** 부른다(SEQ-13).

        Returns:
            되돌린 작업 수
        """
        rows = await crud.running_all(self.session)
        for row in rows:
            row.status = JobStatus.failed
            row.error_kind = ErrorKind.unknown
            row.error_reason = ORPHAN_REASON
            row.error_chunk_seq = None
            row.error_attempts = 1
        if rows:
            await crud.in_flight_to_waiting(self.session, [r.id for r in rows])
        await self.session.commit()
        return len(rows)

    async def claim_next(self) -> AnalysisJobRow | None:
        """VA-MS-002#JobService.claim_next

        대기열에서 가장 오래 기다린 작업을 running으로 바꿔 준다 — 한 트랜잭션.
        도는 작업이 있으면 꺼내지 않는다(동시에 도는 분석은 하나).

        Returns:
            running이 된 행, 또는 None(도는 작업이 있거나 기다리는 작업이 없거나 부분 unique 위반)
        """
        if await crud.any_running(self.session):
            return None
        row = await crud.next_queued(self.session)
        if row is None:
            return None
        row.status = JobStatus.running
        row.stage_started_at = datetime.now(UTC)
        try:
            await self.session.commit()
        except IntegrityError:  # running 둘 — 서버가 두 번 떴다
            await self.session.rollback()
            return None
        return row

    async def retry(self, video: Video) -> Job:
        """VA-MS-002#JobService.retry

        실패한 작업을 같은 행으로 대기열 끝에. 스텁 — B2에서 채운다(VA-CODE-001 B1).

        Raises:
            NotImplementedYet: 아직 없다
        """
        raise NotImplementedYet("다시 시도는 아직 지원하지 않아요")

    async def cancel(self, video_id: int) -> None:
        """VA-MS-002#JobService.cancel

        도는 태스크 취소. 스텁 — 아무것도 하지 않는다. 삭제(B4)가 채운다(VA-CODE-001 B1).
        """
        return None

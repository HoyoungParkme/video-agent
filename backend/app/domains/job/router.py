"""/api/videos/{id}/job · …/job/retry — HTTP 입출력만(VA-API-001 3.4).

영상을 먼저 읽는다(없으면 404 video) — JobService는 Video DTO를 받고 영상 테이블을 모른다.
진행 상태의 장면 칸은 결과 서비스가 세어 넘긴다 — 작업 묶음은 장면 테이블을 모른다(DOM-002 5장 14).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.domains.analysis.service import AnalysisService
from app.domains.job.schemas import Job
from app.domains.video.router import Jobs, Session, Videos

router = APIRouter(prefix="/api/videos/{video_id}/job", tags=["작업"])


@router.post("", status_code=201)
async def post_job(video_id: int, videos: Videos, jobs: Jobs) -> Job:
    """분석을 시작한다 — 늘 대기열에 넣고 워커를 깨운다. running 또는 queued."""
    detail = await videos.get(video_id)
    return await jobs.start(detail.video)


@router.get("")
async def get_job(video_id: int, videos: Videos, jobs: Jobs, session: Session) -> Job:
    """진행 상태 — 화면이 1초마다 부른다. 장면 단계가 있는 작업은 장면 칸을 싣는다."""
    await videos.get(video_id)
    frames = await AnalysisService(session).frame_progress(video_id)
    return await jobs.progress(video_id, frames)


@router.post("/retry")
async def post_retry(video_id: int, videos: Videos, jobs: Jobs) -> Job:
    """실패한 단계부터 같은 작업으로 다시 — 대기열 끝에 든다(JobService.retry)."""
    detail = await videos.get(video_id)
    return await jobs.retry(detail.video)

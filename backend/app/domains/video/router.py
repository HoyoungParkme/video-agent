"""/api/inbox · /api/videos · /api/videos/{id} — HTTP 입출력만(VA-API-001 3.2 · 3.3).

라우터가 서비스 둘을 차례로 부르는 곳이 있다 — 등록 뒤의 예상치(JobService.estimate).
판단 없이 A의 결과를 B에 넘길 뿐이다(VA-DOM-002 3.1). 다른 묶음의 라우터도
video_service로 영상을 먼저 읽는다.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.core.db import get_session
from app.core.errors import NotImplementedYet
from app.domains.job.service import JobService
from app.domains.video.schemas import (
    InboxListing,
    RegisterRequest,
    RegisterResponse,
    VideoDetail,
    VideoSummary,
)
from app.domains.video.service import VideoService

router = APIRouter(prefix="/api", tags=["영상"])

Session = Annotated[AsyncSession, Depends(get_session)]


def video_service(request: Request, session: Session) -> VideoService:
    """요청 세션과 main.py가 조립한 어댑터로(VA-DOM-002 6장 서비스 조립)."""
    return VideoService(session, request.app.state.youtube_info)


def job_service(session: Session) -> JobService:
    return JobService(session)


Videos = Annotated[VideoService, Depends(video_service)]
Jobs = Annotated[JobService, Depends(job_service)]


@router.get("/inbox")
async def get_inbox() -> InboxListing:
    """inbox 파일 목록 — 스텁, 빈 목록(B2가 VideoService.list_inbox로 채운다)."""
    return InboxListing(path=config.INBOX_DISPLAY_PATH, files=[])


@router.get("/videos")
async def get_videos(videos: Videos) -> list[VideoSummary]:
    """분석한 영상 목록 — 작업이 있는 것만, 최근 순."""
    return await videos.list()


@router.post("/videos")
async def post_video(req: RegisterRequest, videos: Videos, jobs: Jobs) -> RegisterResponse:
    """영상을 등록하고 사전 안내를 만든다. 중복이면 기존 것 — 늘 200."""
    video = await videos.register(req)
    return RegisterResponse(video=video, estimate=await jobs.estimate(video))


@router.get("/videos/{video_id}")
async def get_video(video_id: int, videos: Videos) -> VideoDetail:
    """영상 하나와 최근 작업 요약."""
    return await videos.get(video_id)


@router.delete("/videos/{video_id}", status_code=204)
async def delete_video(video_id: int) -> None:
    """영상 삭제 — 스텁(B4)."""
    raise NotImplementedYet("삭제는 아직 지원하지 않아요")

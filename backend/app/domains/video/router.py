"""/api/inbox · /api/videos · /api/uploads · /api/videos/{id} — HTTP 입출력만(VA-API-001 3.2 · 3.3).

라우터가 서비스 둘을 차례로 부르는 곳이 있다 — 등록 뒤의 예상치(JobService.estimate), 삭제 전의
취소(JobService.cancel · AnalysisService.cancel_tasks)와 삭제 뒤의 깨우기(JobService.wake).
판단 없이 A의 결과를 B에 넘길 뿐이다(VA-DOM-002 3.1). 다른 묶음의 라우터도
video_service로 영상을 먼저 읽는다.
"""

from __future__ import annotations

from typing import Annotated
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import Validation
from app.domains.analysis.service import AnalysisService
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
    return VideoService(session, request.app.state.youtube_info, request.app.state.media_probe)


def job_service(session: Session) -> JobService:
    return JobService(session)


Videos = Annotated[VideoService, Depends(video_service)]
Jobs = Annotated[JobService, Depends(job_service)]


@router.get("/inbox")
async def get_inbox(videos: Videos) -> InboxListing:
    """inbox 파일 목록 — 길이까지, 수정 시각 최근 순. 빈 폴더면 files=[]."""
    return await videos.list_inbox()


@router.get("/videos")
async def get_videos(videos: Videos) -> list[VideoSummary]:
    """분석한 영상 목록 — 작업이 있는 것만, 최근 순."""
    return await videos.list()


@router.post("/videos")
async def post_video(req: RegisterRequest, videos: Videos, jobs: Jobs) -> RegisterResponse:
    """영상을 등록하고 사전 안내를 만든다. 중복이면 기존 것 — 늘 200."""
    video = await videos.register(req)
    return RegisterResponse(video=video, estimate=await jobs.estimate(video))


@router.post("/uploads")
async def post_upload(request: Request, videos: Videos, jobs: Jobs) -> RegisterResponse:
    """올린 파일 하나를 등록하고 사전 안내를 만든다 — 본문은 파일 바이트 그대로(스트림).

    원래 이름은 X-File-Name(UTF-8 퍼센트 인코딩), 크기는 Content-Length. 둘 중 하나가 없으면
    validation. 판정 · 사본은 VideoService.upload가 한다. 응답은 POST /api/videos와 같다.
    """
    name = request.headers.get("x-file-name")
    length = request.headers.get("content-length")
    errors = []
    try:
        name = unquote(name, errors="strict") if name else None
    except UnicodeDecodeError:
        name = None
    if not name:
        errors.append({"field": "X-File-Name", "message": "파일 이름이 없어요"})
    if length is None or not length.isdigit():
        errors.append({"field": "Content-Length", "message": "크기가 없어요"})
    if name is None or length is None or errors:
        raise Validation(errors=errors)
    video = await videos.upload(name, int(length), request.stream())
    return RegisterResponse(video=video, estimate=await jobs.estimate(video))


@router.get("/videos/{video_id}")
async def get_video(video_id: int, videos: Videos) -> VideoDetail:
    """영상 하나와 최근 작업 요약."""
    return await videos.get(video_id)


@router.delete("/videos/{video_id}", status_code=204)
async def delete_video(video_id: int, videos: Videos, jobs: Jobs, session: Session) -> None:
    """영상과 딸린 것 전부. 도는 작업과 장면 채우기를 먼저 멈추고, 지운 뒤 워커를 깨운다(SEQ-11).

    깨우기가 먼저면 워커가 곧 지워질 행을 꺼내거나, 취소된 작업의 running 행 때문에 다시 잠든다.
    장면 채우기를 멈추지 않으면 지운 장면 폴더에 다시 쓴다.
    """
    await jobs.cancel(video_id)
    await AnalysisService(session).cancel_tasks(video_id)
    await videos.delete(video_id)
    jobs.wake()

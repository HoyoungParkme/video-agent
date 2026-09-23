"""/api/videos/{id}/result · …/export — HTTP 입출력만(VA-API-001 3.5). 내보내기는 B4."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.errors import NotImplementedYet
from app.domains.analysis.schemas import Result
from app.domains.analysis.service import AnalysisService
from app.domains.video.router import Session, Videos

router = APIRouter(prefix="/api/videos/{video_id}", tags=["결과"])


def analysis_service(request: Request, session: Session) -> AnalysisService:
    return AnalysisService(session, request.app.state.summarizer)


Analysis = Annotated[AnalysisService, Depends(analysis_service)]


@router.get("/result")
async def get_result(video_id: int, videos: Videos, analysis: Analysis) -> Result:
    """분석 결과 전부. 끝나지 않았으면 409 result-not-ready."""
    detail = await videos.get(video_id)
    return await analysis.result_of(detail.video)


@router.get("/export")
async def get_export(video_id: int) -> None:
    """마크다운 본문 — 스텁(B4)."""
    raise NotImplementedYet("내보내기는 아직 지원하지 않아요")


@router.post("/export")
async def post_export(video_id: int) -> None:
    """마크다운을 파일로 — 스텁(B4)."""
    raise NotImplementedYet("내보내기는 아직 지원하지 않아요")

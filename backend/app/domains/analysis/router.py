"""/api/videos/{id}/result · …/export — HTTP 입출력만(VA-API-001 3.5).

내보내기는 영상(VideoService.get)과, 질문 기록을 넣으면 대화 턴(ChatService.history)을 받아
결과 서비스에 넘긴다 — 라우터가 서비스 둘을 차례로 부르는 곳이다(DOM-002 3.1).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.domains.analysis.schemas import ExportPreview, ExportRequest, ExportResult, Result
from app.domains.analysis.service import AnalysisService
from app.domains.chat.service import ChatService
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
async def get_export(
    video_id: int, videos: Videos, analysis: Analysis, session: Session, with_chat: bool = False
) -> ExportPreview:
    """마크다운 본문 — UI-7 미리 보기와 복사용. with_chat이면 질문 기록을 맨 끝에 붙인다."""
    detail = await videos.get(video_id)
    turns = await ChatService(session).history(video_id) if with_chat else []
    return await analysis.export_markdown(detail.video, with_chat, turns)


@router.post("/export", status_code=201)
async def post_export(
    video_id: int, req: ExportRequest, videos: Videos, analysis: Analysis, session: Session
) -> ExportResult:
    """같은 마크다운을 data/export/{이름}.md에 쓴다. 쓰지 못하면 500 export-failed."""
    detail = await videos.get(video_id)
    turns = await ChatService(session).history(video_id) if req.with_chat else []
    return await analysis.export_to_file(detail.video, req.with_chat, turns)

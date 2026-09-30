"""/api/videos/{id}/result · …/frames · …/export — HTTP 입출력만(VA-API-001 3.5).

내보내기는 영상(VideoService.get)과, 질문 기록을 넣으면 대화 턴(ChatService.history)을 받아
결과 서비스에 넘긴다 — 라우터가 서비스 둘을 차례로 부르는 곳이다(DOM-002 3.1). 장면 채우기는
app.state의 장면 어댑터로 만든 서비스가 뒤에서 돈다.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse

from app.domains.analysis.schemas import (
    ExportMethod,
    ExportPreview,
    ExportRequest,
    ExportResult,
    FrameSet,
    Result,
)
from app.domains.analysis.service import AnalysisService
from app.domains.chat.service import ChatService
from app.domains.video.router import Session, Videos

router = APIRouter(prefix="/api/videos/{video_id}", tags=["결과"])


def analysis_service(request: Request, session: Session) -> AnalysisService:
    state = request.app.state
    return AnalysisService(
        session, state.summarizer, state.storyboard, state.local_frames, state.image_maker
    )


Analysis = Annotated[AnalysisService, Depends(analysis_service)]


@router.get("/result")
async def get_result(video_id: int, videos: Videos, analysis: Analysis) -> Result:
    """분석 결과 전부. 끝나지 않았으면 409 result-not-ready."""
    detail = await videos.get(video_id)
    return await analysis.result_of(detail.video)


@router.get("/frames")
async def get_frames(video_id: int, videos: Videos, analysis: Analysis) -> FrameSet:
    """대표 장면 상태와 장면들 — 채우는 동안 화면이 3초마다 부른다. 끝나지 않았으면 409."""
    detail = await videos.get(video_id)
    return await analysis.frames_of(detail.video)


@router.post("/frames", status_code=202)
async def post_frames(video_id: int, videos: Videos, analysis: Analysis) -> FrameSet:
    """옛 결과에 장면 채우기를 맡기고 지금 상태를 바로 준다. 채울 수 없으면 409."""
    detail = await videos.get(video_id)
    return await analysis.fill_frames(detail.video)


@router.get("/frames/{seq}")
async def get_frame(video_id: int, seq: int, analysis: Analysis) -> FileResponse:
    """챕터 seq의 장면 JPEG. 없으면 404(frame). 다시 채우면 바뀔 수 있어 캐시는 매번 확인한다."""
    path = await analysis.frame_file(video_id, seq)
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "no-cache"})


@router.get("/export")
async def get_export(
    video_id: int,
    videos: Videos,
    analysis: Analysis,
    session: Session,
    with_chat: bool = False,
    method: ExportMethod = ExportMethod.file,
) -> ExportPreview:
    """고른 방법의 노트 — UI-7 미리 보기와 복사용. with_chat이면 질문 기록을 맨 끝에 붙인다."""
    detail = await videos.get(video_id)
    turns = await ChatService(session).history(video_id) if with_chat else []
    return await analysis.export_markdown(detail.video, with_chat, turns, method)


@router.post("/export", status_code=201)
async def post_export(
    video_id: int, req: ExportRequest, videos: Videos, analysis: Analysis, session: Session
) -> ExportResult:
    """같은 마크다운을 data/export/{이름}.md에 쓴다. 쓰지 못하면 500 export-failed."""
    detail = await videos.get(video_id)
    turns = await ChatService(session).history(video_id) if req.with_chat else []
    return await analysis.export_to_file(detail.video, req.with_chat, turns)

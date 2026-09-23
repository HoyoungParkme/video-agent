"""/api/videos/{id}/chat — HTTP 입출력만(VA-API-001 3.6). 스텁 — 질문하기는 B3."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.errors import NotImplementedYet
from app.domains.chat.schemas import ChatTurn
from app.domains.video.router import Videos

router = APIRouter(prefix="/api/videos/{video_id}/chat", tags=["대화"])


@router.get("")
async def get_chat(video_id: int, videos: Videos) -> list[ChatTurn]:
    """질문 · 답변 기록 — 스텁, 빈 목록(B3). 영상이 없으면 404."""
    await videos.get(video_id)
    return []


@router.post("")
async def post_chat(video_id: int) -> ChatTurn:
    """질문하고 답을 받는다 — 스텁(B3)."""
    raise NotImplementedYet("질문하기는 아직 지원하지 않아요")

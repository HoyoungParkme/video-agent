"""/api/videos/{id}/chat — HTTP 입출력만(VA-API-001 3.6). 기록과 질문."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.domains.chat.schemas import AskRequest, ChatTurn
from app.domains.chat.service import ChatService
from app.domains.video.router import Session, Videos

router = APIRouter(prefix="/api/videos/{video_id}/chat", tags=["대화"])


def chat_service(request: Request, session: Session) -> ChatService:
    return ChatService(session, request.app.state.answerer)


Chats = Annotated[ChatService, Depends(chat_service)]


@router.get("")
async def get_chat(video_id: int, videos: Videos, chats: Chats) -> list[ChatTurn]:
    """질문 · 답변 기록, 시간순. 결과가 없어도 빈 목록이고, 영상이 없으면 404."""
    await videos.get(video_id)
    return await chats.history(video_id)


@router.post("", status_code=201)
async def post_chat(video_id: int, req: AskRequest, videos: Videos, chats: Chats) -> ChatTurn:
    """질문하고 답을 받는다 — 저장한 턴(201). 실패하면 저장하지 않는다."""
    detail = await videos.get(video_id)
    return await chats.ask(detail.video, req.question)

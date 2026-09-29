"""/api/settings 셋 — 설정 조회 · 키 저장 · 모델 저장(VA-API-001 3.1). HTTP 입출력만 한다.

core에 라우터가 있는 유일한 곳이다 — 설정은 도메인이 아니라 `.env`의 값이라서(VA-DOM-002 1장).
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.settings import Settings, settings

router = APIRouter(prefix="/api/settings", tags=["설정"])


class KeyRequest(BaseModel):
    """새 키(VA-API-001 4장)."""

    key: str = Field(min_length=1)


class ModelsRequest(BaseModel):
    """모델 선택(VA-API-001 4장)."""

    stt_model: str
    text_model: str


@router.get("")
def get_settings() -> Settings:
    """설정과 키 상태 — 다시 확인하지 않는다."""
    return settings.get()


@router.post("/key")
async def post_key(req: KeyRequest) -> Settings:
    """새 키를 확인하고 저장."""
    return await settings.set_key(req.key)


@router.put("/models")
def put_models(req: ModelsRequest) -> Settings:
    """모델 선택 저장."""
    return settings.set_models(req.stt_model, req.text_model)

"""앱 조립 — 어댑터 · 라우터 · Host 확인 · 시작 때 키 확인 · /health(VA-DOM-002 1장).

어댑터를 한 번 만들어 라우터(app.state)에 건넨다 — 테스트는 여기서 가짜로 바꿔 끼운다.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from openai import AsyncOpenAI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core import errors, settings_router
from app.core.config import config
from app.core.errors import KeyMissing
from app.core.settings import settings
from app.domains.analysis import router as analysis_router
from app.domains.analysis.adapters.summarizer_openai import SummarizerOpenAI
from app.domains.chat import router as chat_router
from app.domains.job import router as job_router
from app.domains.video import router as video_router
from app.domains.video.adapters.youtube_info import YouTubeInfoAdapter
from app.infra import openai

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def client_for() -> AsyncOpenAI:
    """지금 키로 OpenAI 클라이언트 — 부를 때마다 `.env`에서 읽는다(VA-MS-006 0장).

    화면이나 `.env`에서 키를 바꾸면 서버를 다시 띄우지 않아도 다음 호출부터 새 키다.
    """
    key = settings.api_key()
    if not key:
        raise KeyMissing()
    return openai.client(key)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """시작할 때 저장된 키를 한 번 확인한다(VA-SEQ-001 SEQ-13). 실패해도 서버는 뜬다."""
    status = await settings.check_stored_key()
    log.info("키 확인: %s %s", status.state.value, status.reason or "")
    yield


app = FastAPI(title="Video Agent API", lifespan=lifespan)
# Host가 다르면 입구 앞에서 400 — 인증이 없어 바인딩만으로는 DNS 리바인딩을 못 막는다(INFRA 5절)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.ALLOWED_HOSTS)
errors.install(app)

app.state.youtube_info = YouTubeInfoAdapter()
app.state.summarizer = SummarizerOpenAI(client_for)

app.include_router(settings_router.router)
app.include_router(video_router.router)
app.include_router(job_router.router)
app.include_router(analysis_router.router)
app.include_router(chat_router.router)


@app.get("/health")
def health() -> dict[str, str]:
    """살아 있는지."""
    return {"status": "ok"}

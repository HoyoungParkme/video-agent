"""앱 조립 — 어댑터 · 라우터 · Host 확인 · 시작과 끝(lifespan) · /health(VA-DOM-002 1장).

어댑터를 한 번 만들어 라우터(app.state)와 파이프라인(모듈 속성)에 건넨다 — 테스트는 여기서
가짜로 바꿔 끼운다. 영상 묶음과 작업 묶음을 둘 다 아는 곳은 여기뿐이다(load_video).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from openai import AsyncOpenAI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core import errors, settings_router
from app.core.config import config
from app.core.db import SessionLocal
from app.core.errors import KeyMissing, NotFound
from app.core.settings import settings
from app.domains.analysis import router as analysis_router
from app.domains.analysis.adapters.summarizer_openai import SummarizerOpenAI
from app.domains.chat import router as chat_router
from app.domains.job import pipeline
from app.domains.job import router as job_router
from app.domains.job.adapters.audio_source import AudioSourceAdapter
from app.domains.job.service import JobService
from app.domains.video import router as video_router
from app.domains.video.adapters.media_probe import MediaProbeAdapter
from app.domains.video.adapters.youtube_info import YouTubeInfoAdapter
from app.domains.video.schemas import Video
from app.domains.video.service import VideoService
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


async def load_video(video_id: int) -> Video | None:
    """워커에게 넘기는 영상 읽기 — 짧은 세션으로 VideoService.get. 없으면 None."""
    async with SessionLocal() as session:
        try:
            detail = await VideoService(session, app.state.youtube_info, app.state.media_probe).get(
                video_id
            )
        except NotFound:
            return None
    return detail.video


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """시작 — 저장된 키 확인 → 죽은 작업 되돌리기 → 대기열 워커(순서가 있다, SEQ-13).

    끌 때 워커를 취소한다. 돌던 작업은 running으로 남고 다음 시작 때 되돌린다.
    """
    status = await settings.check_stored_key()
    log.info("키 확인: %s %s", status.state.value, status.reason or "")
    async with SessionLocal() as session:
        orphans = await JobService(session).fail_orphans()
    if orphans:
        log.info("서버가 죽어 멈춘 작업 %d개를 실패로 되돌렸다", orphans)
    worker = asyncio.create_task(pipeline.worker(load_video))
    try:
        yield
    finally:
        worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker


app = FastAPI(title="Video Agent API", lifespan=lifespan)
# Host가 다르면 입구 앞에서 400 — 인증이 없어 바인딩만으로는 DNS 리바인딩을 못 막는다(INFRA 5절)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.ALLOWED_HOSTS)
errors.install(app)

app.state.youtube_info = YouTubeInfoAdapter()
app.state.media_probe = MediaProbeAdapter()
app.state.summarizer = SummarizerOpenAI(client_for)
pipeline.audio_source = AudioSourceAdapter()
pipeline.summarizer = app.state.summarizer

app.include_router(settings_router.router)
app.include_router(video_router.router)
app.include_router(job_router.router)
app.include_router(analysis_router.router)
app.include_router(chat_router.router)


@app.get("/health")
def health() -> dict[str, str]:
    """살아 있는지."""
    return {"status": "ok"}

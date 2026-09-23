"""앱 조립 — Host 확인, 라우터 등록, 시작 때 저장된 키 확인, /health(VA-DOM-002 1장).

카드 A의 lifespan은 키 확인만 한다. 서버가 죽어 running인 채 남은 작업 되돌리기(fail_orphans)와
대기열 워커는 B1에서 넣는다(VA-CODE-001 A 스텁).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core import errors, settings_router
from app.core.config import config
from app.core.settings import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


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
app.include_router(settings_router.router)


@app.get("/health")
def health() -> dict[str, str]:
    """살아 있는지."""
    return {"status": "ok"}

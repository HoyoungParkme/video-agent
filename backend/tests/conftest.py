"""테스트 공용 — 전용 테스트 DB만 쓴다(DEV-14). 앱을 import하기 전에 접속 주소를 덮어쓴다."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from pathlib import Path

import asyncpg
import pytest
from sqlalchemy.engine import make_url

TEST_DB_URL = os.environ.get(
    "VA_TEST_DATABASE_URL", "postgresql+asyncpg://va:va@127.0.0.1:5433/va_test"
)
if "test" not in (make_url(TEST_DB_URL).database or ""):
    pytest.exit(f"테스트 DB 이름에 test가 없다 — 시작하지 않는다: {make_url(TEST_DB_URL).database}")
# setdefault가 아니라 덮어쓴다 — 셸에 떠 있는 값이 이기면 개발 DB가 지워진다
os.environ["DATABASE_URL"] = TEST_DB_URL


async def _ensure_database() -> None:
    url = make_url(TEST_DB_URL)
    conn = await asyncpg.connect(
        host=url.host, port=url.port, user=url.username, password=url.password, database="postgres"
    )
    try:
        if not await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", url.database):
            await conn.execute(f'CREATE DATABASE "{url.database}"')
    finally:
        await conn.close()


asyncio.run(_ensure_database())

from alembic.config import Config as AlembicConfig  # noqa: E402

from alembic import command  # noqa: E402 — 주소를 덮어쓴 뒤에
from app.core.config import config  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]


def alembic_config() -> AlembicConfig:
    """backend/alembic.ini — 로그 설정은 건드리지 않게."""
    cfg = AlembicConfig(str(BACKEND / "alembic.ini"))
    cfg.attributes["configure_logger"] = False
    return cfg


async def _alembic(action: str, target: str) -> None:
    # env.py가 asyncio.run을 부르므로 다른 스레드에서
    await asyncio.to_thread(getattr(command, action), alembic_config(), target)


@pytest.fixture(scope="session")
def alembic() -> Callable[[str, str], Awaitable[None]]:
    """`await alembic("upgrade", "head")` — 리비전을 올리고 내린다."""
    return _alembic


@pytest.fixture(scope="session")
async def migrated() -> AsyncIterator[None]:
    """테스트 DB를 마지막 리비전으로."""
    await _alembic("upgrade", "head")
    yield


@pytest.fixture
def env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """테스트마다 새 `.env` 자리. 파일은 만들지 않는다 — 테스트가 필요하면 쓴다."""
    path = tmp_path / ".env"
    monkeypatch.setattr(config, "ENV_PATH", str(path))
    yield path

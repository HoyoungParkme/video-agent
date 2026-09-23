"""Alembic 실행 환경 — config.DATABASE_URL에 async 엔진으로 붙어 리비전을 돌린다(DEV-7)."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import config
from app.core.db import Base
from app.domains.analysis import models as _analysis  # noqa: F401 — 테이블을 metadata에 올린다
from app.domains.chat import models as _chat  # noqa: F401
from app.domains.job import models as _job  # noqa: F401
from app.domains.video import models as _video  # noqa: F401

if context.config.config_file_name is not None and context.config.attributes.get(
    "configure_logger", True
):
    fileConfig(context.config.config_file_name)


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


async def _online() -> None:
    engine = create_async_engine(config.DATABASE_URL, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


asyncio.run(_online())

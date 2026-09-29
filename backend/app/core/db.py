"""async 엔진 · 세션 · ORM 기반 클래스. 세션은 입구 층(라우터 · 파이프라인)이 연다(DOM-002 6장)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from enum import StrEnum

from sqlalchemy import Enum, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import config

# 제약 이름을 정해 두면 마이그레이션의 이름이 늘 같다
NAMING = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """ORM 모델의 뿌리. 테이블 11개가 이 metadata에 모인다."""

    metadata = MetaData(naming_convention=NAMING)


def str_enum(enum: type[StrEnum], length: int) -> Enum:
    """열거형 컬럼 — DB는 varchar, 값 검증은 앱이 한다(DOM-003 1장).

    값을 더해도 마이그레이션이 없다.
    """
    return Enum(
        enum,
        native_enum=False,
        create_constraint=False,
        length=length,
        validate_strings=True,
        values_callable=lambda e: [m.value for m in e],
    )


engine = create_async_engine(config.DATABASE_URL, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """요청마다 세션 하나(FastAPI 의존성). 트랜잭션은 서비스가 정한 범위에서 연다."""
    async with SessionLocal() as session:
        yield session

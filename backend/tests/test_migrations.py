"""마이그레이션 — 테이블 11개 · 인덱스 · 제약이 ERD(VA-DOM-003)대로인지, 올리고 내릴 수 있는지.

0001_initial이 전부를 만들고 0002가 영상 하나에 기다리는 · 도는 작업 하나를 더한다.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

import app.domains.analysis.models  # noqa: F401 — 테이블을 metadata에 올린다
import app.domains.chat.models  # noqa: F401
import app.domains.job.models  # noqa: F401
import app.domains.video.models  # noqa: F401
from app.core.config import config
from app.core.db import Base

TABLES = {
    "videos",
    "analysis_jobs",
    "audio_chunks",
    "transcripts",
    "segments",
    "summaries",
    "insights",
    "parts",
    "chapters",
    "suggested_questions",
    "chat_turns",
}
NOW = datetime(2026, 9, 23, tzinfo=UTC)


@pytest.fixture
async def conn(migrated: None) -> AsyncIterator[AsyncConnection]:
    """테스트마다 트랜잭션 하나 — 끝나면 되돌린다."""
    engine = create_async_engine(config.DATABASE_URL)
    async with engine.connect() as c:
        tx = await c.begin()
        yield c
        await tx.rollback()
    await engine.dispose()


async def _tables(c: AsyncConnection) -> set[str]:
    return set(await c.run_sync(lambda s: inspect(s).get_table_names())) - {"alembic_version"}


async def _insert_video(c: AsyncConnection, source_id: str = "dQw4w9WgXcQ") -> int:
    return await c.scalar(
        text(
            "INSERT INTO videos (source_kind, source_id, title, duration_sec, origin, has_captions)"
            " VALUES ('youtube', :s, '제목', 3012, 'https://youtu.be/x', true) RETURNING id"
        ),
        {"s": source_id},
    )


async def _insert_job(
    c: AsyncConnection, video_id: int, status: str = "queued", **error: object
) -> int:
    return await c.scalar(
        text(
            "INSERT INTO analysis_jobs (video_id, status, stage, stages, progress_pct, est_seconds,"
            " est_cost_usd, concurrency, text_model, error_kind, error_reason, stage_started_at,"
            " queued_at, started_at) VALUES (:v, :st, 'pending', '[]', 0, 60, 0.01, 3,"
            " 'gpt-5-mini', :ek, :er, :t, :t, :t) RETURNING id"
        ),
        {"v": video_id, "st": status, "ek": error.get("kind"), "er": error.get("reason"), "t": NOW},
    )


JOB_SQL = (
    "INSERT INTO analysis_jobs (video_id, status, stage, stages, progress_pct, est_seconds,"
    " est_cost_usd, concurrency, text_model, stage_started_at, queued_at, started_at)"
    " VALUES (:v, :st, 'pending', '[]', 0, 60, 0, 3, 'gpt-5-mini', now(), now(), now())"
)


async def _expect_violation(c: AsyncConnection, sql: str, params: dict | None = None) -> None:
    sp = await c.begin_nested()
    with pytest.raises(IntegrityError):
        await c.execute(text(sql), params or {})
    await sp.rollback()


async def test_head_matches_models(conn: AsyncConnection) -> None:
    """마지막 리비전의 스키마와 ORM 모델 사이에 차이가 없다."""

    def diff(sync_conn):
        return compare_metadata(MigrationContext.configure(sync_conn), Base.metadata)

    assert await _tables(conn) == TABLES
    assert await conn.run_sync(diff) == []


async def test_partial_indexes(conn: AsyncConnection) -> None:
    """대기열 · running 하나 · 영상 하나에 작업 하나 — 부분 인덱스 셋이 조건과 함께(DOM-003 3장)."""
    rows = await conn.execute(
        text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'analysis_jobs'")
    )
    defs = dict(rows.all())
    assert "UNIQUE" in defs["uq_analysis_jobs_running"]
    assert "WHERE ((status)::text = 'running'::text)" in defs["uq_analysis_jobs_running"]
    assert "WHERE ((status)::text = 'queued'::text)" in defs["ix_analysis_jobs_queued_at"]
    assert "started_at DESC" in defs["ix_analysis_jobs_video_id_started_at"]
    active = defs["uq_analysis_jobs_video_id_active"]
    assert "UNIQUE" in active
    assert "(video_id)" in active
    assert "'queued'" in active and "'running'" in active


async def test_running_is_one(conn: AsyncConnection) -> None:
    """running은 전체에 하나. queued는 여럿이어도 된다(영상이 다르면)."""
    v1, v2, v3, v4 = [await _insert_video(conn, c * 11) for c in "abcd"]
    await _insert_job(conn, v1, "running")
    await _insert_job(conn, v2, "queued")
    await _insert_job(conn, v3, "queued")
    await _expect_violation(conn, JOB_SQL, {"v": v4, "st": "running"})


async def test_active_job_is_one_per_video(conn: AsyncConnection) -> None:
    """영상 하나에 기다리는 · 도는 작업은 하나. 끝난 · 실패한 작업은 막지 않는다(0002)."""
    v = await _insert_video(conn)
    await _insert_job(conn, v, "done")
    await _insert_job(conn, v, "failed", kind="unknown", reason="서버가 다시 시작됨")
    await _insert_job(conn, v, "queued")
    for status in ("queued", "running"):  # 같은 영상에 [분석 시작]이 동시에 두 번
        await _expect_violation(conn, JOB_SQL, {"v": v, "st": status})


async def test_error_fields_only_when_failed(conn: AsyncConnection) -> None:
    """failed면 error_kind · error_reason이 있고, 아니면 둘 다 없다."""
    v = await _insert_video(conn)
    await _insert_job(conn, v, "failed", kind="network", reason="네트워크 시간 초과")
    for status, kind, reason in (("failed", None, None), ("done", "network", "x")):
        await _expect_violation(
            conn,
            "INSERT INTO analysis_jobs (video_id, status, stage, stages, progress_pct,"
            " est_seconds, est_cost_usd, concurrency, text_model, error_kind, error_reason,"
            " stage_started_at, queued_at, started_at) VALUES (:v, :s, 'pending', '[]', 0, 60,"
            " 0, 3, 'gpt-5-mini', :k, :r, now(), now(), now())",
            {"v": v, "s": status, "k": kind, "r": reason},
        )


async def test_checks(conn: AsyncConnection) -> None:
    """길이 상한 · 진행률 범위 · 순번 · 시각 순서 · 추천 질문 1~3."""
    await _expect_violation(
        conn,
        "INSERT INTO videos (source_kind, source_id, title, duration_sec, origin, has_captions)"
        " VALUES ('local', 'x', 't', 10801, 'a.mp4', false)",
    )
    v = await _insert_video(conn)
    t = await conn.scalar(
        text(
            "INSERT INTO transcripts (video_id, source, language) VALUES (:v, 'stt', 'ko')"
            " RETURNING id"
        ),
        {"v": v},
    )
    await _expect_violation(
        conn,
        "INSERT INTO segments (transcript_id, seq, start_sec, end_sec, text)"
        " VALUES (:t, 1, 10, 9, 'x')",
        {"t": t},
    )
    await _expect_violation(
        conn,
        "INSERT INTO segments (transcript_id, seq, start_sec, end_sec, text)"
        " VALUES (:t, 0, 1, 2, 'x')",
        {"t": t},
    )
    await _expect_violation(
        conn,
        "INSERT INTO suggested_questions (video_id, seq, text) VALUES (:v, 4, '질문')",
        {"v": v},
    )
    await _expect_violation(
        conn,
        "UPDATE analysis_jobs SET progress_pct = 101 WHERE id = :j",
        {"j": await _insert_job(conn, v)},
    )


async def test_chapter_part_same_video(conn: AsyncConnection) -> None:
    """챕터는 다른 영상의 파트를 가리킬 수 없다 — 복합 FK."""
    v1, v2 = await _insert_video(conn, "aaaaaaaaaaa"), await _insert_video(conn, "bbbbbbbbbbb")
    p1 = await conn.scalar(
        text(
            "INSERT INTO parts (video_id, seq, title, start_sec) VALUES (:v, 1, '파트', 0)"
            " RETURNING id"
        ),
        {"v": v1},
    )
    await conn.execute(
        text(
            "INSERT INTO chapters (video_id, part_id, seq, start_sec, title, bullets)"
            " VALUES (:v, :p, 1, 0, '챕터', '[]')"
        ),
        {"v": v1, "p": p1},
    )
    await _expect_violation(
        conn,
        "INSERT INTO chapters (video_id, part_id, seq, start_sec, title, bullets)"
        " VALUES (:v, :p, 1, 0, '챕터', '[]')",
        {"v": v2, "p": p1},
    )


async def test_delete_video_cascades(conn: AsyncConnection) -> None:
    """영상 행 하나를 지우면 딸린 것이 전부 사라진다(DOM-003 4장 5)."""
    v = await _insert_video(conn)
    j = await _insert_job(conn, v)
    await conn.execute(
        text(
            "INSERT INTO audio_chunks (job_id, seq, offset_sec, duration_sec, state)"
            " VALUES (:j, 1, 0, 600, 'waiting')"
        ),
        {"j": j},
    )
    s = await conn.scalar(
        text(
            "INSERT INTO summaries (video_id, one_liner, model) VALUES (:v, '요약', 'm')"
            " RETURNING id"
        ),
        {"v": v},
    )
    await conn.execute(
        text(
            "INSERT INTO insights (summary_id, seq, text, source_secs) VALUES (:s, 1, 'x', '[1]')"
        ),
        {"s": s},
    )
    await conn.execute(
        text(
            "INSERT INTO chat_turns (video_id, question, answer, cited_secs, model, asked_at)"
            " VALUES (:v, 'q', 'a', '[]', 'm', now())"
        ),
        {"v": v},
    )
    await conn.execute(text("DELETE FROM videos WHERE id = :v"), {"v": v})
    # 이 영상의 것만 센다 — 앞서 돈 테스트 · E2E가 같은 DB에 남긴 행과 섞이지 않게
    left = {
        "analysis_jobs": ("video_id", v),
        "audio_chunks": ("job_id", j),
        "summaries": ("video_id", v),
        "insights": ("summary_id", s),
        "chat_turns": ("video_id", v),
    }
    for table, (column, owner) in left.items():
        count = f"SELECT count(*) FROM {table} WHERE {column} = :o"
        assert await conn.scalar(text(count), {"o": owner}) == 0


async def test_downgrade_then_upgrade(
    migrated: None, alembic: Callable[[str, str], Awaitable[None]]
) -> None:
    """내리면 테이블이 없고, 다시 올리면 11개."""
    engine = create_async_engine(config.DATABASE_URL)
    try:
        await alembic("downgrade", "base")
        async with engine.connect() as c:
            assert await _tables(c) == set()
        await alembic("upgrade", "head")
        async with engine.connect() as c:
            assert await _tables(c) == TABLES
    finally:
        await engine.dispose()

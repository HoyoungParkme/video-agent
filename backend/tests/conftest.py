"""테스트 공용 — 전용 테스트 DB만 쓴다(DEV-14). 앱을 import하기 전에 접속 주소를 덮어쓴다.

뒤쪽은 앱 테스트 공용 — 빈 테이블 세션 · 쿼리 세기 · 키 있음 · 행 만들기 · 가짜 포트 · API 클라이언트.
"""

from __future__ import annotations

import asyncio
import itertools
import os
import re
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import asyncpg
import httpx
import pytest
from sqlalchemy import event, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

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


# 여기부터는 접속 주소를 덮어쓴 뒤에 — 앱 모듈이 import 때 설정을 읽는다
from alembic import command  # noqa: E402
from alembic.config import Config as AlembicConfig  # noqa: E402

from app.core.config import config  # noqa: E402
from app.core.db import SessionLocal, engine  # noqa: E402
from app.core.errors import SourceUnavailable, UnsupportedFile  # noqa: E402
from app.core.settings import settings  # noqa: E402
from app.domains.analysis.models import TranscriptSource  # noqa: E402
from app.domains.analysis.schemas import (  # noqa: E402
    CaptionLine,
    ChapterDraft,
    Segment,
    SummaryDraft,
)
from app.domains.job.models import (  # noqa: E402
    AnalysisJobRow,
    AudioChunkRow,
    ChunkState,
    ErrorKind,
    JobStatus,
)
from app.domains.job.service import JobService  # noqa: E402
from app.domains.video.models import CaptionKind, SourceKind, VideoRow  # noqa: E402
from app.domains.video.schemas import SourceInfo  # noqa: E402
from app.infra import openai  # noqa: E402
from app.infra.openai import KeyCheck, KeyState, ReasonKind  # noqa: E402

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
    """테스트 DB를 만들고(없으면) 마지막 리비전으로. DB가 필요한 테스트만 부른다."""
    await _ensure_database()
    await _alembic("upgrade", "head")
    yield


@pytest.fixture
def env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """테스트마다 새 `.env` 자리. 파일은 만들지 않는다 — 테스트가 필요하면 쓴다."""
    path = tmp_path / ".env"
    monkeypatch.setattr(config, "ENV_PATH", str(path))
    yield path


REASONS = {
    ReasonKind.format: "키 형식이 아닙니다",
    ReasonKind.auth: "인증에 실패했습니다",
    ReasonKind.quota: "잔액이 없습니다",
    ReasonKind.network: "연결하지 못했습니다",
}


@dataclass
class FakeVerify:
    """openai.verify_key 자리. fail을 정하면 그 이유로 실패하고, error를 정하면 던진다."""

    fail: ReasonKind | None = None
    error: Exception | None = None
    calls: list[str] = field(default_factory=list)

    async def __call__(self, key: str) -> KeyCheck:
        self.calls.append(key)
        if self.error:
            raise self.error
        if self.fail:
            return KeyCheck(KeyState.invalid, self.fail, REASONS[self.fail], datetime.now(UTC))
        return KeyCheck(KeyState.ok, None, None, datetime.now(UTC))


@pytest.fixture
def verify(monkeypatch: pytest.MonkeyPatch) -> FakeVerify:
    fake = FakeVerify()
    monkeypatch.setattr(openai, "verify_key", fake)
    return fake


# --- 앱 테스트 공용

TABLES = (
    "videos, analysis_jobs, audio_chunks, transcripts, segments, summaries, insights, parts, "
    "chapters, suggested_questions, chat_turns"
)
KEY = "sk-abcdefghijklmnop1234"
CAPTION_STAGES = ["download", "summarize", "chapter", "suggest"]
STT_STAGES = ["download", "transcribe", "summarize", "chapter", "suggest"]


@pytest.fixture
async def db(migrated: None) -> AsyncIterator[AsyncSession]:
    """테스트마다 빈 테이블과 세션 하나. 워커 신호 · 태스크 핸들도 비운다."""
    async with SessionLocal() as s:
        await s.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
        await s.commit()
        JobService.work_event.clear()
        JobService.tasks.clear()
        yield s


@pytest.fixture
def queries() -> Iterator[list[str]]:
    """앱이 DB에 보낸 SQL 문. 잴 호출 앞에서 `.clear()`한다."""
    seen: list[str] = []

    def on(conn: Any, cursor: Any, statement: str, *_: Any) -> None:
        seen.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", on)
    yield seen
    event.remove(engine.sync_engine, "before_cursor_execute", on)


@pytest.fixture
def key(env_file, verify, monkeypatch) -> None:
    """키가 `.env`에 있고 마지막 확인이 통과한 상태."""
    env_file.write_text(f"OPENAI_API_KEY={KEY}\n")
    monkeypatch.setattr(
        settings, "last_check", KeyCheck(KeyState.ok, None, None, datetime.now(UTC))
    )


@dataclass
class Make:
    """행을 바로 넣는다 — 서비스를 거치지 않고 상태를 차린다."""

    s: AsyncSession
    _n: itertools.count = field(default_factory=lambda: itertools.count(1))

    async def video(self, **kw: Any) -> VideoRow:
        n = next(self._n)
        values: dict[str, Any] = {
            "source_kind": SourceKind.youtube,
            "source_id": f"vid{n:08d}",
            "title": f"영상 {n}",
            "channel": "채널",
            "duration_sec": 3000,
            "origin": f"https://www.youtube.com/watch?v=vid{n:08d}",
            "has_captions": True,
            "caption_language": "ko",
            "caption_kind": CaptionKind.manual,
        } | kw
        row = VideoRow(**values)
        self.s.add(row)
        await self.s.commit()
        await self.s.refresh(row)
        return row

    async def job(
        self, video_id: int, status: JobStatus = JobStatus.done, **kw: Any
    ) -> AnalysisJobRow:
        """작업 행. at으로 시작 · 대기열에 든 때를 정한다(기본 지금)."""
        at: datetime = kw.pop("at", datetime.now(UTC))
        values: dict[str, Any] = {
            "video_id": video_id,
            "status": status,
            "stage": "suggest" if status == JobStatus.done else "pending",
            "stages": CAPTION_STAGES,
            "progress_pct": 100 if status == JobStatus.done else 0,
            "est_seconds": 60,
            "est_cost_usd": Decimal("0.02"),
            "concurrency": 3,
            "stt_model": None,
            "text_model": "gpt-5-mini",
            "stage_durations_sec": {},
            "started_at": at,
            "queued_at": at,
            "stage_started_at": at,
            "finished_at": at + timedelta(seconds=60) if status == JobStatus.done else None,
        }
        if status == JobStatus.failed:
            values |= {"error_kind": ErrorKind.openai, "error_reason": "실패", "error_attempts": 1}
        row = AnalysisJobRow(**(values | kw))
        self.s.add(row)
        await self.s.commit()
        await self.s.refresh(row)
        return row

    async def chunks(self, job_id: int, states: list[ChunkState]) -> None:
        for seq, state in enumerate(states, 1):
            self.s.add(
                AudioChunkRow(
                    job_id=job_id,
                    seq=seq,
                    offset_sec=(seq - 1) * 600,
                    duration_sec=600,
                    path=None,
                    state=state,
                    attempts=1 if state != ChunkState.waiting else 0,
                    result=[{"start_sec": 0, "end_sec": 1, "text": "x"}]
                    if state == ChunkState.done
                    else None,
                )
            )
        await self.s.commit()

    async def transcript(self, video_id: int, texts: list[str], step: float = 10) -> None:
        """자막 스크립트 — 줄마다 step초."""
        from app.domains.analysis import crud

        lines = [CaptionLine(i * step, (i + 1) * step, t) for i, t in enumerate(texts)]
        await crud.replace_transcript(
            self.s, video_id, TranscriptSource.caption_manual, "ko", None, lines
        )
        await self.s.commit()


@pytest.fixture
def make(db: AsyncSession) -> Make:
    return Make(db)


def youtube_id(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", url)
    assert m, url
    return m.group(1)


@dataclass
class FakeYouTube:
    """YouTubeInfoPort 자리. 주소에서 영상 ID를 뽑아 정한 값으로 SourceInfo를 준다."""

    title: str = "자막 있는 강의"
    duration: int = 3012
    captions: tuple[str, CaptionKind] | None = ("ko", CaptionKind.manual)
    error: Exception | None = None
    calls: list[str] = field(default_factory=list)

    async def info(self, url: str) -> SourceInfo:
        self.calls.append(url)
        if self.error:
            raise self.error
        vid = youtube_id(url)
        return SourceInfo(
            source_kind=SourceKind.youtube,
            source_id=vid,
            title=self.title,
            channel="채널",
            duration_sec=self.duration,
            origin=f"https://www.youtube.com/watch?v={vid}",
            has_captions=self.captions is not None,
            caption_language=self.captions[0] if self.captions else None,
            caption_kind=self.captions[1] if self.captions else None,
        )


@pytest.fixture
def youtube() -> FakeYouTube:
    return FakeYouTube()


@dataclass
class FakeMediaProbe:
    """MediaProbePort 자리. 파일 이름으로 정한 (길이, 음성 유무)를 주고, 없는 이름은 default.
    default가 None이거나 이름의 값이 None이면 열 수 없는 파일(unsupported-file)."""

    files: dict[str, tuple[int, bool] | None] = field(default_factory=dict)
    default: tuple[int, bool] | None = (1800, True)
    calls: list[str] = field(default_factory=list)

    async def probe(self, path: str) -> tuple[int, bool]:
        self.calls.append(path)
        got = self.files.get(Path(path).name, self.default)
        if got is None:
            raise UnsupportedFile(reason="영상·음성 파일이 아닙니다", accepted=[])
        return got


@pytest.fixture
def probe() -> FakeMediaProbe:
    return FakeMediaProbe()


@pytest.fixture
def unavailable() -> SourceUnavailable:
    return SourceUnavailable(reason="비공개 영상이에요", hint=None)


@dataclass
class FakeSummarizer:
    """SummarizerPort 자리. 부른 것을 적고 정한 값을 준다. fail에 단계 이름을 넣으면 던진다."""

    summary_draft: SummaryDraft = field(
        default_factory=lambda: SummaryDraft(
            one_liner="이 영상은 파이썬을 소개한다.",
            insights=[(f"인사이트 {i}", [i * 60.0]) for i in range(1, 7)],
        )
    )
    chapter_draft: ChapterDraft = field(
        default_factory=lambda: ChapterDraft(
            parts=[],
            chapters=[
                (None, i * 360.0, f"챕터 {i + 1}", ["요점 하나", "요점 둘"]) for i in range(8)
            ],
        )
    )
    question_list: list[str] = field(
        default_factory=lambda: ["파이썬은 누가 만들었나요?", "왜 쉬운가요?", "어디에 쓰나요?"]
    )
    fail: dict[str, Exception] = field(default_factory=dict)
    delay: float = 0
    calls: list[tuple[str, list[Segment]]] = field(default_factory=list)

    async def _call(self, name: str, segments: list[Segment]) -> None:
        self.calls.append((name, segments))
        if self.delay:
            await asyncio.sleep(self.delay)
        if name in self.fail:
            raise self.fail[name]

    async def summary(self, segments: list[Segment], duration_sec: int, model: str) -> SummaryDraft:
        await self._call("summary", segments)
        return self.summary_draft

    async def chapters(
        self, segments: list[Segment], duration_sec: int, model: str
    ) -> ChapterDraft:
        await self._call("chapters", segments)
        return self.chapter_draft

    async def questions(self, segments: list[Segment], model: str) -> list[str]:
        await self._call("questions", segments)
        return self.question_list


@pytest.fixture
def summarizer() -> FakeSummarizer:
    return FakeSummarizer()


@dataclass
class FakeAudioSource:
    """AudioSourcePort 자리 — 자막."""

    result: tuple[list[CaptionLine], str, CaptionKind] | None = field(
        default_factory=lambda: (
            [CaptionLine(i * 10.0, i * 10.0 + 9, f"문장 {i}") for i in range(30)],
            "ko",
            CaptionKind.manual,
        )
    )
    error: Exception | None = None
    calls: list[str] = field(default_factory=list)

    async def captions(self, video_id: str) -> tuple[list[CaptionLine], str, CaptionKind] | None:
        self.calls.append(video_id)
        if self.error:
            raise self.error
        return self.result


@pytest.fixture
def audio_source() -> FakeAudioSource:
    return FakeAudioSource()


@pytest.fixture
async def api(db, youtube, probe, summarizer, monkeypatch) -> AsyncIterator[httpx.AsyncClient]:
    """앱에 바로 붙는 클라이언트 — 시작 이벤트(워커) 없이, 어댑터는 가짜로."""
    from app.main import app

    monkeypatch.setattr(app.state, "youtube_info", youtube)
    monkeypatch.setattr(app.state, "media_probe", probe)
    monkeypatch.setattr(app.state, "summarizer", summarizer)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as c:
        yield c

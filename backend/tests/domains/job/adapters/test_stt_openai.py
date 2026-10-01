"""job/adapters/stt_openai — 조각 → 15초 이하 토막 → 구간(VA-MS-006 stt_openai.transcribe).

ffmpeg(길이 · 무음 · 자르기)은 가짜로 바꾸고, infra의 openai.transcribe는 그대로 부르되 클라이언트만
가짜로 둔다 — 요청 인자 · 동시 수 · 토막 파일까지 본다.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import httpx
import openai as sdk
import pytest

from app.core.config import config
from app.domains.job.adapters.stt_openai import SttOpenAI
from app.domains.job.schemas import SttSegment
from app.infra import ffmpeg


class FakeFfmpeg:
    """길이 · 무음은 정한 값, 자르기는 토막 파일을 만들고 잘린 범위를 적는다."""

    def __init__(self, total: float, mids: list[float]) -> None:
        self.total, self.mids = total, mids
        self.cuts: list[tuple[float, float]] = []
        self.silence_args: tuple = ()

    async def probe(self, path: str) -> dict:
        return {"format": {"duration": str(self.total)}}

    async def silences(self, path: str, noise_db: float, min_sec: float) -> list[float]:
        self.silence_args = (noise_db, min_sec)
        return self.mids

    async def cut(self, path: str, start: float, end: float, dest: str) -> str:
        self.cuts.append((start, end))
        Path(dest).write_text(f"{start}-{end}")
        return dest


class FakeTranscriptions:
    """client.audio.transcriptions 자리 — 토막 범위로 글을 정하고, 동시 수를 센다."""

    def __init__(self, texts: dict[str, str] | None = None, fail_at: str | None = None) -> None:
        self.texts = texts or {}
        self.fail_at = fail_at
        self.calls: list[dict] = []
        self.now = self.peak = 0
        self.cancelled = 0

    async def create(self, **kwargs):
        span = kwargs["file"].read().decode()
        self.calls.append({**kwargs, "span": span})
        self.now += 1
        self.peak = max(self.peak, self.now)
        try:
            if span == self.fail_at:  # 곧바로 실패 — 함께 돌던 토막은 아직 기다리는 중이다
                resp = httpx.Response(429, request=httpx.Request("POST", "https://x/v1"))
                raise sdk.RateLimitError("rate limit", response=resp, body=None)
            await asyncio.sleep(0.01)
            body = {"text": self.texts.get(span, f" {span} 말 "), "languages": [{"code": "ko"}]}
            return SimpleNamespace(model_dump=lambda: body)
        except asyncio.CancelledError:
            self.cancelled += 1
            raise
        finally:
            self.now -= 1


@pytest.fixture
def chunk(tmp_path: Path) -> str:
    path = tmp_path / "3.mp3"
    path.write_bytes(b"mp3")
    return str(path)


def _run(monkeypatch, fake_ff: FakeFfmpeg, fake_tr: FakeTranscriptions) -> SttOpenAI:
    monkeypatch.setattr(ffmpeg, "probe", fake_ff.probe)
    monkeypatch.setattr(ffmpeg, "silences", fake_ff.silences)
    monkeypatch.setattr(ffmpeg, "cut", fake_ff.cut)
    client = SimpleNamespace(audio=SimpleNamespace(transcriptions=fake_tr))
    return SttOpenAI(lambda: client)


def _left(chunk: str) -> list[str]:
    # 조각 곁에 남은 토막 파일
    return sorted(p.name for p in Path(chunk).parent.iterdir() if p.name != "3.mp3")


async def test_boundaries_on_silences(monkeypatch, chunk: str) -> None:
    fake_ff = FakeFfmpeg(40.0, [3.0 * k for k in range(1, 14)])  # 3초마다 무음
    got = await _run(monkeypatch, fake_ff, FakeTranscriptions()).transcribe(chunk, "gpt-transcribe")
    assert fake_ff.cuts == [(0.0, 15.0), (15.0, 30.0), (30.0, 40.0)]
    assert all(e - s <= config.PIECE_SEC for s, e in fake_ff.cuts)
    assert fake_ff.silence_args == (config.PIECE_SILENCE_DB, config.PIECE_SILENCE_MIN_SEC)
    assert [(s.start_sec, s.end_sec) for s in got] == fake_ff.cuts


async def test_latest_silence_inside_the_limit(monkeypatch, chunk: str) -> None:
    fake_ff = FakeFfmpeg(40.0, [4.0, 11.5, 16.0, 27.2])
    await _run(monkeypatch, fake_ff, FakeTranscriptions()).transcribe(chunk, "gpt-transcribe")
    assert fake_ff.cuts == [(0.0, 11.5), (11.5, 16.0), (16.0, 27.2), (27.2, 40.0)]


async def test_no_silence_cuts_every_15_seconds(monkeypatch, chunk: str) -> None:
    fake_ff = FakeFfmpeg(40.0, [])
    await _run(monkeypatch, fake_ff, FakeTranscriptions()).transcribe(chunk, "gpt-transcribe")
    assert fake_ff.cuts == [(0.0, 15.0), (15.0, 30.0), (30.0, 40.0)]


async def test_short_tail_joins_the_piece_before(monkeypatch, chunk: str) -> None:
    fake_ff = FakeFfmpeg(15.5, [])
    await _run(monkeypatch, fake_ff, FakeTranscriptions()).transcribe(chunk, "gpt-transcribe")
    assert fake_ff.cuts == [(0.0, 15.5)]  # 0.5초 자투리를 따로 보내지 않는다


async def test_silence_in_first_two_seconds_not_used(monkeypatch, chunk: str) -> None:
    fake_ff = FakeFfmpeg(20.0, [1.5])
    await _run(monkeypatch, fake_ff, FakeTranscriptions()).transcribe(chunk, "gpt-transcribe")
    assert fake_ff.cuts == [(0.0, 15.0), (15.0, 20.0)]


async def test_segments_in_piece_order_without_empty(monkeypatch, chunk: str) -> None:
    fake_ff = FakeFfmpeg(40.0, [])
    fake_tr = FakeTranscriptions({"15.0-30.0": "   "})
    got = await _run(monkeypatch, fake_ff, fake_tr).transcribe(chunk, "gpt-transcribe")
    assert got == [
        SttSegment(0.0, 15.0, "0.0-15.0 말", "ko"),
        SttSegment(30.0, 40.0, "30.0-40.0 말", "ko"),
    ]
    assert {c["model"] for c in fake_tr.calls} == {"gpt-transcribe"}
    assert {c["response_format"] for c in fake_tr.calls} == {"json"}
    assert _left(chunk) == []  # 토막 파일이 남지 않는다


async def test_language_empty_when_not_detected(monkeypatch, chunk: str) -> None:
    fake_ff = FakeFfmpeg(5.0, [])
    fake_tr = FakeTranscriptions()

    async def create(**kwargs):
        return SimpleNamespace(model_dump=lambda: {"text": "말", "languages": []})

    fake_tr.create = create
    got = await _run(monkeypatch, fake_ff, fake_tr).transcribe(chunk, "gpt-transcribe")
    assert got == [SttSegment(0.0, 5.0, "말", "")]


async def test_concurrency_limit(monkeypatch, chunk: str) -> None:
    fake_ff = FakeFfmpeg(600.0, [])  # 40토막
    fake_tr = FakeTranscriptions()
    got = await _run(monkeypatch, fake_ff, fake_tr).transcribe(chunk, "gpt-transcribe")
    assert len(got) == 40
    assert fake_tr.peak == config.PIECE_CONCURRENCY


async def test_first_error_goes_up_and_rest_stop(monkeypatch, chunk: str) -> None:
    fake_ff = FakeFfmpeg(600.0, [])
    fake_tr = FakeTranscriptions(fail_at="15.0-30.0")
    with pytest.raises(sdk.RateLimitError):
        await _run(monkeypatch, fake_ff, fake_tr).transcribe(chunk, "gpt-transcribe")
    assert len(fake_tr.calls) < 40  # 남은 토막은 보내지 않았다
    assert fake_tr.cancelled >= 1  # 함께 돌던 토막은 멈췄다
    assert _left(chunk) == []

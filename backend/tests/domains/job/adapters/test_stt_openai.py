"""job/adapters/stt_openai — 조각 → 구간(VA-MS-006 stt_openai.transcribe).

infra의 openai.transcribe는 그대로 부르고 클라이언트만 가짜로 둔다 — 요청 인자까지 본다.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import httpx
import openai as sdk
import pytest

from app.domains.job.adapters.stt_openai import SttOpenAI
from app.domains.job.schemas import SttSegment


class FakeTranscriptions:
    """client.audio.transcriptions 자리 — 받은 인자를 적고 정한 응답을 준다."""

    def __init__(self, resp: dict | None = None, error: Exception | None = None) -> None:
        self.resp = resp or {}
        self.error = error
        self.kwargs: dict = {}

    async def create(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(model_dump=lambda: self.resp)


def _adapter(fake: FakeTranscriptions) -> SttOpenAI:
    client = SimpleNamespace(audio=SimpleNamespace(transcriptions=fake))
    return SttOpenAI(lambda: client)


@pytest.fixture
def chunk(tmp_path: Path) -> str:
    path = tmp_path / "3.mp3"
    path.write_bytes(b"mp3")
    return str(path)


async def test_segments_without_empty_text(chunk: str) -> None:
    segments = [{"start": i * 5.0, "end": i * 5.0 + 4.5, "text": f" 문장 {i} "} for i in range(20)]
    segments.insert(3, {"start": 99.0, "end": 99.5, "text": "   "})
    fake = FakeTranscriptions({"language": "korean", "duration": 100.0, "segments": segments})
    got = await _adapter(fake).transcribe(chunk, "whisper-1")
    assert len(got) == 20
    assert got[0] == SttSegment(0.0, 4.5, "문장 0", "ko")
    assert all(s.language == "ko" for s in got)


async def test_request_asks_verbose_json_segments(chunk: str) -> None:
    fake = FakeTranscriptions({"language": "english", "segments": []})
    assert await _adapter(fake).transcribe(chunk, "whisper-1") == []
    assert fake.kwargs["model"] == "whisper-1"
    assert fake.kwargs["response_format"] == "verbose_json"
    assert fake.kwargs["timestamp_granularities"] == ["segment"]
    assert "language" not in fake.kwargs  # 자동 감지


async def test_unknown_language_name_kept(chunk: str) -> None:
    fake = FakeTranscriptions(
        {"language": "Welsh", "segments": [{"start": 0, "end": 1, "text": "Bore da"}]}
    )
    assert (await _adapter(fake).transcribe(chunk, "whisper-1"))[0].language == "welsh"


async def test_rate_limit_goes_up(chunk: str) -> None:
    resp = httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com/v1/x"))
    fake = FakeTranscriptions(error=sdk.RateLimitError("rate limit", response=resp, body=None))
    with pytest.raises(sdk.RateLimitError):
        await _adapter(fake).transcribe(chunk, "whisper-1")

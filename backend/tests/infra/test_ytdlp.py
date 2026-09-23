"""infra/ytdlp — VA-MS-007 ytdlp.info · captions · download_audio의 테스트 관점."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.config import config
from app.infra import ytdlp
from app.infra.errors import YtdlpError

INFO = {"id": "dQw4w9WgXcQ", "title": "제목", "channel": "채널", "duration": 3012}


async def test_info_returns_json_as_is(fake) -> None:
    fake.behave(stdout=json.dumps(INFO))
    assert await ytdlp.info("https://youtu.be/dQw4w9WgXcQ") == INFO
    [args] = fake.calls()
    assert args[:4] == ["--dump-single-json", "--skip-download", "--no-playlist", "--no-warnings"]


@pytest.mark.parametrize(
    ("stderr", "kind"),
    [
        ("ERROR: [youtube] x: Private video. Sign in if you've been granted access", "private"),
        ("ERROR: [youtube] x: Video unavailable. This video has been removed", "unavailable"),
        ("ERROR: [youtube] x: Video unavailable. This video is private", "private"),
        (
            "ERROR: [youtube] x: Video unavailable. The uploader has not made this video"
            " available in your country",
            "geo",
        ),
        ("ERROR: [youtube] x: This video is not available in your country", "geo"),
        ("ERROR: Unable to download webpage: <urlopen error getaddrinfo failed>", "network"),
        ("ERROR: [youtube] x: Unable to extract initial player response", "extractor"),
        ("ERROR: something else", "other"),
    ],
)
async def test_info_failure_kinds(fake, stderr: str, kind: str) -> None:
    fake.behave(stderr="WARNING: 앞줄\n" + stderr + "\n", exit=1)
    with pytest.raises(YtdlpError) as e:
        await ytdlp.info("https://youtu.be/x")
    assert e.value.kind == kind
    assert stderr in e.value.reason


async def test_info_timeout_is_network(fake, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "PROC_TIMEOUT_SEC", 0.3)
    fake.behave(sleep=5)
    with pytest.raises(YtdlpError) as e:
        await ytdlp.info("https://youtu.be/x")
    assert e.value.kind == "network"


async def test_no_shell(fake, tmp_path: Path) -> None:
    """인자에 `;`가 있어도 명령이 되지 않는다 — 인자 하나로 그대로 간다."""
    marker = tmp_path / "pwned"
    url = f"https://youtu.be/x; touch {marker}"
    fake.behave(stdout="{}")
    await ytdlp.info(url)
    assert fake.calls()[0][-1] == url
    assert not marker.exists()


@pytest.mark.parametrize(
    ("kind", "flag"), [("manual", "--write-subs"), ("auto", "--write-auto-subs")]
)
async def test_captions_reads_vtt(fake, kind: str, flag: str) -> None:
    fake.behave(write_ext="unused", file="WEBVTT\n\n00:00.000 --> 00:02.000\n안녕하세요\n")
    text = await ytdlp.captions("dQw4w9WgXcQ", "ko", kind)
    assert text.startswith("WEBVTT") and "안녕하세요" in text
    [args] = fake.calls()
    assert flag in args
    assert args[args.index("--sub-langs") + 1] == "ko"
    assert args[-1] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


async def test_captions_missing_file(fake) -> None:
    fake.behave()  # 성공하지만 파일을 만들지 않는다
    with pytest.raises(YtdlpError):
        await ytdlp.captions("dQw4w9WgXcQ", "ko", "manual")

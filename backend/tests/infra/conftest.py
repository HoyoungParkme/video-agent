"""가짜 실행 파일 — yt-dlp · ffmpeg · ffprobe 자리에 둔다. 받은 인자를 적고, 시킨 대로 출력한다."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import stat
from collections.abc import Awaitable
from dataclasses import dataclass
from pathlib import Path

import pytest

from app.core.config import config

# FAKE_* 환경 변수로 동작을 정한다. 인자는 줄마다 JSON으로 FAKE_LOG에
FAKE = r"""#!/usr/bin/env python3
import json, os, sys, time
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a") as f:
    f.write(json.dumps(args) + "\n")
if os.environ.get("FAKE_PIDFILE"):
    with open(os.environ["FAKE_PIDFILE"], "w") as f:
        f.write(str(os.getpid()))
if os.environ.get("FAKE_SLEEP"):
    time.sleep(float(os.environ["FAKE_SLEEP"]))
sys.stdout.write(os.environ.get("FAKE_STDOUT", ""))
sys.stderr.write(os.environ.get("FAKE_STDERR", ""))
code = int(os.environ.get("FAKE_EXIT", "0"))
ext = os.environ.get("FAKE_WRITE_EXT")
if code == 0 and ext and "-o" in args:
    out = args[args.index("-o") + 1]
    path = out.replace("%(id)s", args[-1].rsplit("=", 1)[-1]).replace("%(ext)s", ext)
    if "--sub-langs" in args:
        path = f"{path}.{args[args.index('--sub-langs') + 1]}.vtt"
    with open(path, "w") as f:
        f.write(os.environ.get("FAKE_FILE", ""))
if code == 0 and os.environ.get("FAKE_WRITE_LAST"):
    with open(args[-1], "w") as f:
        f.write("fake")
sys.exit(code)
"""


@dataclass
class Fake:
    """가짜 실행 파일 하나와 그 기록."""

    path: Path
    log: Path
    monkeypatch: pytest.MonkeyPatch

    def behave(self, **env: str | int | float) -> None:
        """FAKE_STDOUT · FAKE_STDERR · FAKE_EXIT · FAKE_SLEEP · FAKE_WRITE_EXT 등."""
        for name, value in env.items():
            self.monkeypatch.setenv(f"FAKE_{name.upper()}", str(value))

    async def cancelled_child_is_gone(self, call: Awaitable[object], tmp: Path) -> bool:
        """call을 띄워 자식이 뜬 것을 본 뒤 취소하고, 그 자식이 죽었는지."""
        pidfile = tmp / "pid"
        self.behave(sleep=30, pidfile=pidfile)
        task = asyncio.ensure_future(call)
        for _ in range(200):
            if pidfile.exists() and pidfile.read_text():
                break
            await asyncio.sleep(0.05)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        try:
            os.kill(int(pidfile.read_text()), 0)
        except ProcessLookupError:
            return True
        return False

    def calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]


@pytest.fixture
def fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Fake:
    """세 실행 파일 자리를 모두 같은 가짜로."""
    path = tmp_path / "fake-bin"
    path.write_text(FAKE)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("FAKE_LOG", str(log))
    for name in ("STDOUT", "STDERR", "EXIT", "SLEEP", "WRITE_EXT", "FILE", "WRITE_LAST", "PIDFILE"):
        monkeypatch.delenv(f"FAKE_{name}", raising=False)
    for name in ("YTDLP_BIN", "FFMPEG_BIN", "FFPROBE_BIN"):
        monkeypatch.setattr(config, name, str(path))
    assert os.access(path, os.X_OK)
    return Fake(path, log, monkeypatch)

"""yt-dlp 공용 클라이언트 — 영상 정보 · 자막 · 음성(VA-MS-007). 어댑터만 부른다.

셸 없이 인자 목록으로 띄운다. 실패는 표준 오류에서 종류를 갈라 YtdlpError로.
"""

from __future__ import annotations

import asyncio
import glob
import json
import os
import tempfile

from app.core.config import config
from app.infra.errors import YtdlpError, YtdlpKind

WATCH = "https://www.youtube.com/watch?v={}"

# 앞의 것이 이긴다 — YouTube는 비공개 · 지역 제한도 'Video unavailable. …'로 시작한다
_KINDS: list[tuple[YtdlpKind, tuple[str, ...]]] = [
    ("private", ("private video", "video is private")),
    ("geo", ("available in your country", "geo restriction")),
    ("unavailable", ("video unavailable", "removed")),
    ("network", ("unable to download webpage", "getaddrinfo", "timed out")),
    ("extractor", ("unsupported url", "unable to extract")),
]


def _kind(stderr: str) -> YtdlpKind:
    low = stderr.lower()
    for kind, needles in _KINDS:
        if any(n in low for n in needles):
            return kind
    return "other"


def _tail(stderr: str) -> str:
    lines = [line for line in stderr.splitlines() if line.strip()]
    return "\n".join(lines[-3:])


async def _run(*args: str) -> bytes:
    """yt-dlp 한 번. 성공하면 표준 출력, 아니면 YtdlpError. 시간 제한을 넘으면 network."""
    proc = await asyncio.create_subprocess_exec(
        config.YTDLP_BIN,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), config.PROC_TIMEOUT_SEC)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise YtdlpError("시간 제한을 넘었습니다", "network") from None
    if proc.returncode != 0:
        text = err.decode(errors="replace")
        raise YtdlpError(_tail(text) or f"종료 코드 {proc.returncode}", _kind(text))
    return out


async def info(url: str) -> dict:
    """VA-MS-007#ytdlp.info

    영상 정보를 JSON으로 받는다. 내려받지 않는다.

    Args:
        url: YouTube 주소. 재생 목록 주소면 그 영상 하나만

    Returns:
        yt-dlp의 JSON 그대로 — id · title · channel · duration · subtitles · automatic_captions 등
    """
    out = await _run("--dump-single-json", "--skip-download", "--no-playlist", "--no-warnings", url)
    return json.loads(out)

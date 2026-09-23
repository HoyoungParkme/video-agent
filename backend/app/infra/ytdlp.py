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


async def captions(video_id: str, lang: str, kind: str) -> str:
    """VA-MS-007#ytdlp.captions

    자막 하나를 VTT로 받아 문자열로 돌려준다. 임시 파일은 읽은 뒤 지운다.

    Args:
        video_id: YouTube 영상 ID
        lang: 자막 언어 코드
        kind: `manual`이면 수동 자막, `auto`면 자동 자막

    Returns:
        VTT 원문
    """
    flag = "--write-subs" if kind == "manual" else "--write-auto-subs"
    with tempfile.TemporaryDirectory() as tmp:
        await _run(
            "--skip-download",
            "--no-playlist",
            "--sub-format",
            "vtt",
            "--sub-langs",
            lang,
            flag,
            "-o",
            os.path.join(tmp, "%(id)s"),
            WATCH.format(video_id),
        )
        path = os.path.join(tmp, f"{video_id}.{lang}.vtt")
        if not os.path.exists(path):
            raise YtdlpError(f"자막 파일이 만들어지지 않았습니다({lang}, {kind})", "other")
        with open(path, encoding="utf-8") as f:
            return f.read()

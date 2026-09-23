"""ffmpeg · ffprobe 공용 클라이언트 — 길이 · 음성 추출 · 무음 · 자르기(VA-MS-007). 어댑터만 부른다.

셸 없이 인자 목록으로 띄운다. 실패는 FfmpegError(표준 오류 끝줄들, 종료 코드).
"""

from __future__ import annotations

import asyncio
import json
import os
import re

from app.core.config import config
from app.infra.errors import FfmpegError

_SILENCE = re.compile(r"silence_(start|end): (-?\d+(?:\.\d+)?)")


async def _run(*args: str) -> tuple[bytes, str]:
    """ffmpeg · ffprobe 한 번. 성공하면 (표준 출력, 표준 오류), 아니면 FfmpegError."""
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), config.PROC_TIMEOUT_SEC)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise FfmpegError("시간 제한을 넘었습니다", -1) from None
    text = err.decode(errors="replace")
    if proc.returncode != 0:
        tail = "\n".join([line for line in text.splitlines() if line.strip()][-3:])
        raise FfmpegError(tail or f"종료 코드 {proc.returncode}", proc.returncode or -1)
    return out, text


async def probe(path: str) -> dict:
    """VA-MS-007#ffmpeg.probe

    파일의 길이와 스트림 정보를 읽는다.

    Args:
        path: 영상 · 음성 파일 경로

    Returns:
        ffprobe의 JSON 그대로 — format.duration(문자열 초) · streams[].codec_type
    """
    out, _ = await _run(
        config.FFPROBE_BIN,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        path,
    )
    return json.loads(out)


async def extract_audio(src: str, dest: str) -> str:
    """VA-MS-007#ffmpeg.extract_audio

    음성만 뽑아 mp3 64kbps 모노 16kHz로 바꾼다(config.AUDIO_FORMAT). 원본은 읽기만 한다.

    Args:
        src: 원본 영상 · 음성 파일
        dest: 결과를 둘 폴더

    Returns:
        `{dest}/audio.mp3`
    """
    out = os.path.join(dest, "audio.mp3")
    await _run(config.FFMPEG_BIN, "-y", "-v", "error", "-i", src, "-vn", *config.AUDIO_FORMAT, out)
    return out

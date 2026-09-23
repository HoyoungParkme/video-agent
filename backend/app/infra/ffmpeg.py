"""ffmpeg · ffprobe 공용 클라이언트 — 길이 · 음성 추출 · 무음 · 자르기(VA-MS-007). 어댑터만 부른다.

셸 없이 인자 목록으로 띄운다. 실패는 FfmpegError(표준 오류 끝줄들, 종료 코드).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re

from app.core.config import config
from app.infra.errors import FfmpegError

_SILENCE = re.compile(r"silence_(start|end): (-?\d+(?:\.\d+)?)")


async def _reap(proc: asyncio.subprocess.Process) -> None:
    # 시간 제한 · 취소로 끝나면 자식 프로세스를 죽인다 — 주인 없이 돌며 임시 폴더에 쓰지 않게
    if proc.returncode is None:
        with contextlib.suppress(ProcessLookupError):
            proc.kill()
        await proc.wait()


async def _run(*args: str) -> tuple[bytes, str]:
    """ffmpeg · ffprobe 한 번. 성공하면 (표준 출력, 표준 오류), 아니면 FfmpegError."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as e:
        raise FfmpegError(f"{args[0]}를 실행하지 못했습니다({type(e).__name__})", -1) from None
    try:
        out, err = await asyncio.wait_for(proc.communicate(), config.PROC_TIMEOUT_SEC)
    except TimeoutError:
        raise FfmpegError("시간 제한을 넘었습니다", -1) from None
    finally:
        await _reap(proc)
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
    try:
        return json.loads(out)
    except ValueError:
        raise FfmpegError("ffprobe 출력을 읽지 못했습니다(JSON이 아님)", 0) from None


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


async def silences(path: str) -> list[float]:
    """VA-MS-007#ffmpeg.silences

    무음 구간을 찾아 각 구간의 가운데 시각을 돌려준다. 끝이 없는 마지막 구간은 버린다.

    Args:
        path: 음성 파일

    Returns:
        가운데 시각(초) 오름차순. 무음이 없으면 빈 목록
    """
    _, err = await _run(
        config.FFMPEG_BIN,
        "-v",
        "info",
        "-i",
        path,
        "-af",
        f"silencedetect=noise={config.SILENCE_DB:g}dB:d={config.SILENCE_MIN_SEC:g}",
        "-f",
        "null",
        "-",
    )
    mids: list[float] = []
    start: float | None = None
    for which, value in _SILENCE.findall(err):
        if which == "start":
            start = float(value)
        elif start is not None:
            mids.append((start + float(value)) / 2)
            start = None
    return sorted(mids)


async def cut(path: str, start: float, end: float, dest: str) -> str:
    """VA-MS-007#ffmpeg.cut

    구간을 다시 인코딩하지 않고 잘라 새 파일로 쓴다(-c copy). 끝이 길이를 넘으면 끝까지.

    Args:
        path: 음성 파일
        start: 시작(초)
        end: 끝(초)
        dest: 쓸 파일 경로

    Returns:
        dest
    """
    await _run(
        config.FFMPEG_BIN,
        "-y",
        "-v",
        "error",
        "-ss",
        f"{start:.3f}",
        "-to",
        f"{end:.3f}",
        "-i",
        path,
        "-c",
        "copy",
        dest,
    )
    return dest

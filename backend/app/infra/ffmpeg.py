"""ffmpeg · ffprobe 공용 클라이언트(VA-MS-007) — 길이 · 음성 추출 · 무음 · 자르기 · 장면 한 장 ·
칸 자르기. 어댑터만 부른다.

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


async def _run(*args: str, timeout: float | None = None) -> tuple[bytes, str]:
    """ffmpeg · ffprobe 한 번. 성공하면 (표준 출력, 표준 오류), 아니면 FfmpegError.

    시간 제한은 없으면 config.PROC_TIMEOUT_SEC — 장면 한 장은 config.FRAME_TIMEOUT_SEC를 준다.
    """
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
        out, err = await asyncio.wait_for(
            proc.communicate(), timeout if timeout is not None else config.PROC_TIMEOUT_SEC
        )
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


async def silences(
    path: str, noise_db: float = config.SILENCE_DB, min_sec: float = config.SILENCE_MIN_SEC
) -> list[float]:
    """VA-MS-007#ffmpeg.silences

    무음 구간을 찾아 각 구간의 가운데 시각을 돌려준다. 끝이 없는 마지막 구간은 버린다. 기준은
    부르는 쪽이 준다 — 10분 조각은 기본값, 15초 토막은 더 민감한 값(VA-MS-006 stt_openai).

    Args:
        path: 음성 파일
        noise_db: 이보다 작은 소리를 무음으로 본다(dB)
        min_sec: 이만큼 이어져야 무음이다(초)

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
        f"silencedetect=noise={noise_db:g}dB:d={min_sec:g}",
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


async def frame(src: str, sec: float, width: int, dest: str) -> str:
    """VA-MS-007#ffmpeg.frame

    그 시각의 프레임 한 장을 JPEG로 뽑는다. -ss를 -i 앞에 두어 그 시각으로 바로 건너뛴다 —
    수 GB 원본도 1초 안팎. 높이는 비율대로 짝수. 원본은 읽기만 한다. 먼저 dest를 지운다 —
    앞선 실행이 남긴 같은 이름의 파일을 새 프레임으로 보지 않게.

    Args:
        src: 원본 영상 파일
        sec: 뽑을 시각(초)
        width: 결과 폭(px)
        dest: 쓸 JPEG 경로

    Returns:
        dest. 시각이 영상 끝을 넘어 파일이 생기지 않았으면 FfmpegError
    """
    with contextlib.suppress(FileNotFoundError):
        os.remove(dest)
    await _run(
        config.FFMPEG_BIN,
        "-y",
        "-v",
        "error",
        "-ss",
        f"{sec:.3f}",
        "-i",
        src,
        "-frames:v",
        "1",
        "-vf",
        f"scale={width}:-2",
        "-q:v",
        "3",
        dest,
        timeout=config.FRAME_TIMEOUT_SEC,
    )
    if not os.path.exists(dest):
        raise FfmpegError("프레임을 뽑지 못함", 0)
    return dest


async def crop(src: str, x: int, y: int, w: int, h: int, dest: str) -> str:
    """VA-MS-007#ffmpeg.crop

    그림에서 칸 하나를 잘라 JPEG로 쓴다. src는 파일 경로도, 스토리보드 장의 https 주소도 된다 —
    ffmpeg가 직접 받아 자르므로 HTTP 클라이언트 의존성을 더하지 않는다(VA-INFRA-001 C12).
    칸이 그림 밖이면 폭 · 높이 식이 0이 되어 ffmpeg가 실패한다 — crop 필터는 x · y가 그림을 넘으면
    오류 없이 그림 안으로 당겨 붙여, 덜 찬 마지막 장에서 엉뚱한 칸을 자르기 때문이다.

    Args:
        src: 그림 파일 경로 또는 주소
        x: 칸 왼쪽(px)
        y: 칸 위(px)
        w: 칸 폭(px)
        h: 칸 높이(px)
        dest: 쓸 JPEG 경로

    Returns:
        dest. 주소를 못 받거나 칸이 그림 밖이면 FfmpegError
    """
    await _run(
        config.FFMPEG_BIN,
        "-y",
        "-v",
        "error",
        "-i",
        src,
        "-vf",
        f"crop=w='if(lte({x}+{w},iw),{w},0)':h='if(lte({y}+{h},ih),{h},0)':x={x}:y={y}",
        "-frames:v",
        "1",
        "-q:v",
        "3",
        dest,
        timeout=config.FRAME_TIMEOUT_SEC,
    )
    return dest

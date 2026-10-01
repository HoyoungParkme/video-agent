"""SttPort 구현 — 조각 하나를 15초 이하 토막으로 나눠 받아쓴다(VA-MS-006 stt_openai).

시각을 주는 받아쓰기 모델이 2027-02-26에 없어져, 토막의 경계를 구간 시각으로 쓴다
(VA-INFRA-001 C3, 사용자 결정 2026-10-01). 토막은 이 어댑터 안의 일이다 — 조각 행 · 화면 ·
다시 시도는 10분 조각 그대로다. 키는 부를 때마다 client_for로 받는다. 예외는 그대로 올린다 —
재시도 · 분류 · 이유 한 줄은 파이프라인의 몫이다(VA-MS-002 transcribe_stage · error_kind ·
reason_of).
"""

from __future__ import annotations

import asyncio
import contextlib
import os
from collections.abc import Callable

from openai import APIConnectionError, AsyncOpenAI, InternalServerError, RateLimitError

from app.core.config import config
from app.domains.job.schemas import SttSegment
from app.infra import ffmpeg, openai

# 이보다 짧은 끝 자투리는 따로 보내지 않고 앞 토막에 붙인다 — 그 토막만 15초를 조금 넘는다
TAIL_SEC = 1.0
# 일시 오류 — 그 토막만 다시 보낸다(연결 · 시간 초과 · 429 · 5xx). 키 · 400 같은 것은 곧바로 올린다
TRANSIENT = (APIConnectionError, RateLimitError, InternalServerError)


def _pieces(total: float, mids: list[float]) -> list[tuple[float, float]]:
    # 토막 경계 — (시작 + PIECE_MIN_SEC, 시작 + PIECE_SEC] 안의 가장 늦은 무음, 없으면 PIECE_SEC에서
    out: list[tuple[float, float]] = []
    start = 0.0
    while total - start > 0:
        if total - start <= config.PIECE_SEC:
            end = total
        else:
            limit = start + config.PIECE_SEC
            near = [m for m in mids if start + config.PIECE_MIN_SEC < m <= limit]
            end = max(near) if near else limit
            if total - end < TAIL_SEC:
                end = total
        out.append((start, end))
        start = end
    return out


def _remove(path: str) -> None:
    with contextlib.suppress(FileNotFoundError):
        os.remove(path)


class SttOpenAI:
    """조각 파일 → 받아쓰기 구간들(토막 하나가 구간 하나)."""

    def __init__(self, client_for: Callable[[], AsyncOpenAI]) -> None:
        self.client_for = client_for

    async def transcribe(self, path: str, model: str) -> list[SttSegment]:
        """VA-MS-006#stt_openai.transcribe

        조각을 무음에서 15초 이하 토막으로 나눠 동시에 받아쓰고, 토막의 경계를 구간 시각으로
        쓴다. 일시 오류는 그 토막만 몇 번 다시 보낸다. 그래도 실패하거나 다른 오류면 남은 토막을
        멈추고 그 예외를 그대로 올린다. 토막 파일은 남기지 않는다.

        Args:
            path: 조각 파일(tmp 안 mp3). 토막 파일은 그 곁에 `{조각}_{번호}.mp3`로 잠깐 생긴다
            model: 받아쓰기 모델

        Returns:
            구간들 — 시각은 조각 안 상대 시각(토막 경계). 글이 빈 토막은 뺀다. 언어는 감지한 ISO
            코드, 없으면 ''
        """
        total = float((await ffmpeg.probe(path))["format"]["duration"])
        mids = await ffmpeg.silences(path, config.PIECE_SILENCE_DB, config.PIECE_SILENCE_MIN_SEC)
        plan = _pieces(total, mids)
        stem = os.path.splitext(path)[0]
        files = [f"{stem}_{i:03d}.mp3" for i in range(len(plan))]
        sem = asyncio.Semaphore(config.PIECE_CONCURRENCY)
        client = self.client_for()  # 조각 하나에 한 번 — 키를 바꾸면 다음 조각부터

        async def send(piece: str) -> dict:
            # 일시 오류는 이 토막만 다시 — 조각 하나가 약 40토막이라 하나 때문에 조각을 버리지 않게
            sent = 1
            while True:
                try:
                    return await openai.transcribe(client, piece, model)
                except TRANSIENT:
                    if sent >= config.PIECE_MAX_ATTEMPTS:
                        raise
                    await asyncio.sleep(config.PIECE_RETRY_WAIT_SEC * 2 ** (sent - 1))
                    sent += 1

        async def one(i: int) -> dict:
            async with sem:
                start, end = plan[i]
                await ffmpeg.cut(path, start, end, files[i])
                try:
                    return await send(files[i])
                finally:
                    _remove(files[i])

        tasks = [asyncio.create_task(one(i)) for i in range(len(plan))]
        try:
            raws = await asyncio.gather(*tasks)
        except BaseException:
            # 첫 예외를 그대로 올린다 — 파이프라인이 예외 종류로 분류한다. 남은 토막은 멈춘다
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise
        finally:
            for f in files:
                _remove(f)
        out: list[SttSegment] = []
        for (start, end), raw in zip(plan, raws, strict=True):
            text = str(raw.get("text") or "").strip()
            if not text:
                continue
            langs = raw.get("languages") or []
            lang = str(langs[0].get("code") or "") if langs else ""
            out.append(SttSegment(start, end, text, lang))
        return out

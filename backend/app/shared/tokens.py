"""토큰 어림 — 스크립트를 모델에 보낼 때 몇 토큰인지(VA-MS-006). 요약(analysis)과 대화(chat)가
상한을 넘는지 볼 때 같은 식을 쓴다. tiktoken으로 정확히 세지 않는다 — 의존성과 인코딩 파일
내려받기가 늘고, 상한을 넘는지 가리는 데는 어림으로 충분하다.
"""

from __future__ import annotations

from collections.abc import Iterable

# 실측(카드 C, gpt-5-mini) — 한국어 · 영어 모두 한 토큰에 UTF-8 4바이트 안팎
BYTES_PER_TOKEN = 4
# 모델에 보낼 때 줄 앞에 붙는 시각 표기 몫 — `[mm:ss] ` 5토큰 · `[h:mm:ss] ` 8토큰 안팎
PER_LINE = 8


def estimate(texts: Iterable[str]) -> int:
    """VA-MS-006#tokens.estimate

    줄마다 UTF-8 바이트 ÷ 4 + 8을 더한다. 조금 넉넉하다 — 실측 한국어 스크립트 세 영상에서
    실제의 0.99~1.18배.

    Args:
        texts: 스크립트 줄 텍스트

    Returns:
        토큰 어림
    """
    return int(sum(len(t.encode()) / BYTES_PER_TOKEN + PER_LINE for t in texts))

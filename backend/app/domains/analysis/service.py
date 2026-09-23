"""AnalysisService — 스크립트 · 요약 · 챕터 · 추천 질문과 결과 조회(VA-MS-003).

파이프라인이 단계마다 짧은 세션으로 부르고, 결과 라우터가 요청 세션으로 부른다. 작업 묶음을
모른다 — 부르는 순서는 파이프라인의 것이다. 세 generate_*는 서로를 부르지 않고 각자
구간을 읽으며, 자기 결과를 갈아 끼운다(재시도가 같은 단계를 다시 돌려도 중복이 없다).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.core.errors import NotImplementedYet, ResultNotReady
from app.core.settings import Models, settings
from app.domains.analysis import crud
from app.domains.analysis.models import TranscriptSource
from app.domains.analysis.ports import SummarizerPort
from app.domains.analysis.schemas import (
    CaptionLine,
    Chapter,
    Insight,
    Part,
    Result,
    Segment,
    SuggestedQuestion,
    Summary,
    Transcript,
)

if TYPE_CHECKING:
    from app.domains.video.schemas import Video

# 인사이트 수 상한 — 1시간 이하 8, 넘으면 10(PRD R4). 5개보다 적으면 있는 만큼 둔다
INSIGHTS_MAX, INSIGHTS_MAX_LONG = 8, 10
# 챕터 요점 줄 수 상한
BULLETS_MAX = 3


def _tokens(segments: list[Segment]) -> int:
    # 첫 버전은 어림 — 글자 수 ÷ 2(MS-003 3장 미결). 상한에 여유가 있어 오차가 문제되지 않는다
    return sum(len(s.text) for s in segments) // 2


def _sample(segments: list[Segment], limit: int) -> list[Segment]:
    # 앞 · 가운데 · 끝에서 limit / 3 토큰씩 — 질문은 전체를 다 볼 필요가 없다
    budget = limit // 3 * 2  # 토큰 → 글자(÷ 2의 반대)

    def take(ordered: list[Segment]) -> list[Segment]:
        out, used = [], 0
        for s in ordered:
            if used + len(s.text) > budget and out:
                break
            out.append(s)
            used += len(s.text)
        return out

    mid = len(segments) // 2
    around = sorted(segments, key=lambda s: abs(s.seq - segments[mid].seq))
    picked = take(segments) + take(around) + take(segments[::-1])
    return sorted({s.seq: s for s in picked}.values(), key=lambda s: s.seq)


class AnalysisService:
    """결과 일곱 테이블을 만들고 읽는다.

    - segments_of() · chapters_of() · clamp_secs(): 구간 · 챕터 목록과 시각 보정
    - save_transcript(): 자막 · 받아쓰기 결과를 스크립트로
    - generate_summary() · generate_chapters() · generate_questions(): 파이프라인 단계 셋
    - result_of(): 결과 화면 응답 전부
    """

    def __init__(self, session: AsyncSession, summarizer: SummarizerPort) -> None:
        self.session = session
        self.summarizer = summarizer

    async def segments_of(self, video_id: int) -> list[Segment]:
        """VA-MS-003#AnalysisService.segments_of

        영상의 구간 목록, 시각순. 요약 단계들과 대화(B3)가 부른다.

        Args:
            video_id: 영상 id

        Returns:
            구간들. 스크립트가 없으면 빈 목록(예외 아님)
        """
        rows = await crud.segments(self.session, video_id)
        return [
            Segment(seq=r.seq, start_sec=r.start_sec, end_sec=r.end_sec, text=r.text) for r in rows
        ]

    async def chapters_of(self, video_id: int) -> list[Chapter]:
        """VA-MS-003#AnalysisService.chapters_of

        영상의 챕터 목록, 번호순. 파트 번호를 같이 채운다.

        Args:
            video_id: 영상 id

        Returns:
            챕터들. 파트가 없는 영상은 part_seq가 모두 None
        """
        rows = await crud.chapters_with_part_seq(self.session, video_id)
        return [
            Chapter(
                seq=c.seq,
                part_seq=part_seq,
                start_sec=c.start_sec,
                title=c.title,
                bullets=c.bullets,
            )
            for c, part_seq in rows
        ]

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

    @staticmethod
    def clamp_secs(secs: list[float], duration_sec: int, segments: list[Segment]) -> list[float]:
        """VA-MS-003#AnalysisService.clamp_secs

        모델이 준 시각을 스크립트 범위로 보정한다. 범위 밖이면 시작 시각이 가장 가까운 구간의
        시작으로(길이를 넘으면 마지막 구간). 중복을 없애고 오름차순.

        Args:
            secs: 시각들(초)
            duration_sec: 영상 길이
            segments: 구간들 — 비어 있으면 범위 밖 시각을 뺀다

        Returns:
            보정한 시각들
        """
        out = set()
        for sec in secs:
            if 0 <= sec <= duration_sec:
                out.add(sec)
            elif segments:
                out.add(min(segments, key=lambda s: abs(s.start_sec - sec)).start_sec)
        return sorted(out)

    async def save_transcript(
        self,
        video_id: int,
        source: TranscriptSource,
        language: str,
        model: str | None,
        lines: list[CaptionLine],
    ) -> None:
        """VA-MS-003#AnalysisService.save_transcript

        스크립트와 구간을 갈아 끼운다 — 한 트랜잭션. 줄은 시각순으로 정렬하고 빈 줄은 뺀다.

        Args:
            video_id: 영상 id
            source: 수동 자막 · 자동 자막 · 받아쓰기
            language: 언어 코드
            model: 받아쓰기 모델(자막이면 None)
            lines: 줄들 — 시각순이 아닐 수 있다(조각 병렬)

        Raises:
            ValueError: 남는 줄이 없다 — 파이프라인이 unknown으로 접는다
        """
        clean = [
            CaptionLine(line.start_sec, max(line.end_sec, line.start_sec), line.text.strip())
            for line in sorted(lines, key=lambda x: x.start_sec)
            if line.text.strip()
        ]
        if not clean:
            raise ValueError("스크립트에 넣을 줄이 없어요")
        await crud.replace_transcript(self.session, video_id, source, language, model, clean)
        await self.session.commit()

    async def generate_summary(self, video: Video) -> None:
        """VA-MS-003#AnalysisService.generate_summary

        한 줄 요약과 인사이트를 만들어 갈아 끼운다. 인사이트는 앞 n개(1시간 넘으면 10, 아니면 8),
        출처 시각은 스크립트 범위로 보정하고, 출처가 남지 않은 인사이트는 뺀다.
        스크립트가 토큰 상한을 넘으면 구간별 중간 요약 — 스텁, B2(VA-CODE-001 B1).

        Args:
            video: 영상(id · 길이)

        Raises:
            포트 예외는 그대로 — 파이프라인이 fail로 접는다
        """
        segments = await self.segments_of(video.id)
        model = settings.current_models().text.id
        n_max = (
            INSIGHTS_MAX_LONG if video.duration_sec > config.PART_THRESHOLD_SEC else INSIGHTS_MAX
        )
        if _tokens(segments) > config.TEXT_TOKEN_LIMIT:
            raise NotImplementedYet("아주 긴 스크립트의 요약은 아직 지원하지 않아요")
        draft = await self.summarizer.summary(segments, video.duration_sec, model)
        insights = []
        for text, secs in draft.insights[:n_max]:
            clamped = self.clamp_secs(secs, video.duration_sec, segments)
            if clamped:
                insights.append((text, clamped))
        await crud.replace_summary(self.session, video.id, draft.one_liner, model, insights)
        await self.session.commit()

    async def generate_chapters(self, video: Video) -> None:
        """VA-MS-003#AnalysisService.generate_chapters

        챕터를 만들어 갈아 끼운다 — 시작 시각 보정, 같은 시각은 하나로, 첫 챕터는 0초부터,
        요점은 셋까지. 60분 넘는 영상의 파트 갈래(와 구간별 챕터)는 스텁 — B2(VA-CODE-001 B1).
        모델을 부르기 전에 막는다 — 쓸모없는 호출을 하지 않게.

        Args:
            video: 영상(id · 길이)

        Raises:
            NotImplementedYet: 60분 넘는 영상(B2)
        """
        if video.duration_sec > config.PART_THRESHOLD_SEC:
            raise NotImplementedYet("60분 넘는 영상의 챕터 묶기는 아직 지원하지 않아요")
        segments = await self.segments_of(video.id)
        model = settings.current_models().text.id
        draft = await self.summarizer.chapters(segments, video.duration_sec, model)
        placed = sorted(  # 시작 시각만으로 — 같은 시각이면 모델이 준 순서 그대로(안정 정렬)
            (
                (
                    (self.clamp_secs([start], video.duration_sec, segments) or [0.0])[0],
                    title,
                    bullets[:BULLETS_MAX],
                )
                for _, start, title, bullets in draft.chapters
            ),
            key=lambda c: c[0],
        )
        chapters: list[tuple[float, str, list[str]]] = []
        for start, title, bullets in placed:
            if chapters and chapters[-1][0] == start:  # 같은 시각이 둘이면 뒤 것을 뺀다
                continue
            chapters.append((start, title, bullets))
        if chapters and chapters[0][0] != 0:  # 스크립트 처음이 어느 챕터에도 안 들어가지 않게
            chapters[0] = (0.0, *chapters[0][1:])
        await crud.replace_chapters(self.session, video.id, chapters)
        await self.session.commit()

    async def generate_questions(self, video: Video) -> None:
        """VA-MS-003#AnalysisService.generate_questions

        추천 질문 셋을 만들어 갈아 끼운다. 스크립트가 길면 앞 · 가운데 · 끝만 보낸다.

        Args:
            video: 영상(id)
        """
        segments = await self.segments_of(video.id)
        if _tokens(segments) > config.TEXT_TOKEN_LIMIT:
            segments = _sample(segments, config.TEXT_TOKEN_LIMIT)
        model = settings.current_models().text.id
        texts: list[str] = []
        for q in await self.summarizer.questions(segments, model):
            q = q.strip()
            if q and q not in texts:
                texts.append(q)
        await crud.replace_questions(self.session, video.id, texts[: config.QUESTION_COUNT])
        await self.session.commit()

    async def result_of(self, video: Video) -> Result:
        """VA-MS-003#AnalysisService.result_of

        결과 화면 응답 전부 — 구간을 나누지 않는다. 읽기만 한다. 쿼리 여섯.

        Args:
            video: 라우터가 VideoService.get으로 받은 영상(상태 · 길이 · 대화 수)

        Returns:
            Result

        Raises:
            ResultNotReady: 분석이 끝나지 않았다(video_status)
        """
        if video.status != "analyzed":
            raise ResultNotReady(video_status=video.status)
        t = await crud.transcript(self.session, video.id)
        s, insights = await crud.summary_with_insights(self.session, video.id)
        if t is None or s is None:  # analyzed인데 결과가 없는 것은 있을 수 없지만 막는다
            raise ResultNotReady(video_status=video.status)
        segs = await crud.segments_of_transcript(self.session, t.id)
        part_rows = await crud.parts(self.session, video.id)
        chapter_rows = await crud.chapters_with_part_seq(self.session, video.id)
        questions = await crud.questions(self.session, video.id)
        parts = [
            Part(
                seq=p.seq,
                title=p.title,
                start_sec=p.start_sec,
                end_sec=part_rows[i + 1].start_sec
                if i + 1 < len(part_rows)
                else video.duration_sec,
                chapter_count=sum(1 for _, seq in chapter_rows if seq == p.seq),
            )
            for i, p in enumerate(part_rows)
        ]
        return Result(
            video=video,
            transcript=Transcript(
                source=t.source,
                language=t.language,
                model=t.model,
                segments=[
                    Segment(seq=g.seq, start_sec=g.start_sec, end_sec=g.end_sec, text=g.text)
                    for g in segs
                ],
            ),
            summary=Summary(
                one_liner=s.one_liner,
                model=s.model,
                insights=[
                    Insight(seq=i.seq, text=i.text, source_secs=i.source_secs) for i in insights
                ],
            ),
            parts=parts,
            chapters=[
                Chapter(
                    seq=c.seq,
                    part_seq=seq,
                    start_sec=c.start_sec,
                    title=c.title,
                    bullets=c.bullets,
                )
                for c, seq in chapter_rows
            ],
            suggested_questions=[SuggestedQuestion(seq=q.seq, text=q.text) for q in questions],
            models=Models(stt=t.model, text=s.model),
            analyzed_at=video.analyzed_at,
        )

"""ChatService — 영상에 질문하기(VA-MS-004). 기록 · 질문 · 맥락 고르기 · 영상 목록의 턴 수.

세션은 부르는 쪽(라우터 · VideoService)의 것이다.
"""

from __future__ import annotations

import asyncio
import bisect
import math
import re
from collections import Counter
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.core.errors import LlmUnavailable, ResultNotReady, Validation
from app.core.settings import settings
from app.domains.analysis.schemas import Chapter, Segment
from app.domains.analysis.service import AnalysisService
from app.domains.chat import crud
from app.domains.chat.models import ChatTurnRow
from app.domains.chat.ports import AnswererPort
from app.domains.chat.schemas import ChatTurn
from app.shared import tokens

if TYPE_CHECKING:
    from app.domains.video.schemas import Video

# 낱말 나누기 — 2자 이상(한글 어절 · 영문 · 숫자 모두), 영문은 소문자로. 조사 · 어미는 두 글자
# 조각이 흡수한다. 한 글자는 거의 모든 챕터 글에 들어 있어('a' · '2') 점수를 흐린다
_SPLIT = re.compile(r"[^\w]+")
# 질문 글자 상한 — 넘으면 자른다
QUESTION_MAX = 2000


def _turn(row: ChatTurnRow) -> ChatTurn:
    return ChatTurn(
        id=row.id,
        question=row.question,
        answer=row.answer,
        cited_secs=row.cited_secs,
        asked_at=row.asked_at,
    )


def _tokens(segments: list[Segment]) -> int:
    # 모델에 보낼 스크립트의 토큰 어림 — 요약과 같은 식(MS-006 tokens.estimate)
    return tokens.estimate(s.text for s in segments)


def _words(text: str) -> list[str]:
    return [w for w in _SPLIT.split(text.lower()) if len(w) >= 2]


def _grams(text: str) -> list[str]:
    # 두 글자 조각 — 낱말(2자 이상)마다 이웃한 두 글자를 모두. 조사 · 어미가 붙어도 앞 조각이 같아
    # 맞는다('비용은' → '비용' · '용은') — 형태소 분석기 없이(MS-004 context_for 4번)
    out: list[str] = []
    for w in _words(text):
        out += [w[i : i + 2] for i in range(len(w) - 1)]
    return out


def _bm25(query: list[str], docs: dict[int, list[str]]) -> dict[int, float]:
    # 챕터 글마다 BM25 점수 — 모든 챕터에 흔한 조각은 idf가 작아 점수를 거의 올리지 않는다
    n = len(docs)
    avg = sum(len(d) for d in docs.values()) / n or 1.0
    counts = {k: Counter(d) for k, d in docs.items()}
    df = Counter(g for c in counts.values() for g in c)
    k1, b = config.CHAT_BM25_K1, config.CHAT_BM25_B
    scores: dict[int, float] = {}
    for k, c in counts.items():
        norm = k1 * (1 - b + b * len(docs[k]) / avg)
        scores[k] = sum(
            math.log(1 + (n - df[g] + 0.5) / (df[g] + 0.5)) * c[g] * (k1 + 1) / (c[g] + norm)
            for g in set(query)
            if c[g]
        )
    return scores


def _chapter_at(chapters: list[Chapter], starts: list[float], sec: float) -> Chapter | None:
    # 그 시각이 든 챕터 — 시작이 그 시각 이하인 마지막 챕터. 첫 챕터 앞이면 None(첫 챕터는 0초다)
    i = bisect.bisect_right(starts, sec) - 1
    return chapters[i] if i >= 0 else None


class ChatService:
    """대화 턴을 읽고 쓴다.

    - history(): 영상의 대화 턴, 시간순
    - ask(): 질문 → 맥락 → 모델 → 저장
    - count_by_videos(): 영상마다 턴 수, 쿼리 하나
    - context_for(): 맥락 구간 고르기(전부 또는 관련 챕터)
    """

    def __init__(self, session: AsyncSession, answerer: AnswererPort | None = None) -> None:
        self.session = session
        self._port = answerer

    @property
    def answerer(self) -> AnswererPort:
        # 답변 포트는 ask만 쓴다 — 포트 없이 만든 서비스로 질문하면 코드 실수(500)
        if self._port is None:
            raise RuntimeError("답변 포트 없이 만든 ChatService로 질문했다")
        return self._port

    async def history(self, video_id: int) -> list[ChatTurn]:
        """VA-MS-004#ChatService.history

        영상의 대화 턴, 시간순(같은 시각이면 넣은 순서). 실패한 질문은 저장하지 않으므로 없다.
        영상이 있는지는 라우터가 VideoService.get으로 먼저 본다.

        Args:
            video_id: 영상 id

        Returns:
            턴 목록. 없으면 빈 목록(결과 없는 영상도 — 에러가 아니다)
        """
        return [_turn(r) for r in await crud.turns(self.session, video_id)]

    async def ask(self, video: Video, question: str) -> ChatTurn:
        """VA-MS-004#ChatService.ask

        질문 → 맥락(구간 · 최근 턴) → 모델 → 저장. 순서가 규칙이다 — 결과 · 키 · 빈 질문을 먼저 보고
        모델을 부른다. 답을 받은 뒤 한 번 저장하고, 실패하면 저장하지 않는다. 근거 시각은 영상 길이
        밖이면 버린다(보정하지 않는다 — 근거는 모델이 실제로 본 구간에서만).

        Args:
            video: 라우터가 VideoService.get으로 받은 영상
            question: 입력칸 문장 또는 추천 질문 문장

        Returns:
            저장한 턴

        Raises:
            ResultNotReady: 결과가 없다(video_status)
            KeyMissing · KeyInvalid: 키가 없거나 확인에 실패했다
            Validation: 빈 질문
            LlmUnavailable: 모델 호출 실패(포트의 이유) · 시간 초과('응답 시간 초과')
        """
        if video.status != "analyzed":
            raise ResultNotReady(video_status=video.status)
        await settings.require_key()  # 마지막 확인이 연결 실패였으면 여기서 한 번 다시
        q = question.strip()
        if not q:
            raise Validation(errors=[{"field": "question", "message": "비어 있음"}])
        q = q[:QUESTION_MAX]
        context = await self.context_for(video, q)
        recent = await crud.recent(self.session, video.id, config.CHAT_HISTORY_TURNS)
        history = [_turn(r) for r in reversed(recent)]  # 시간순 — 대명사가 풀린다
        model = settings.current_models().text.id
        try:
            async with asyncio.timeout(config.CHAT_TIMEOUT_SEC):
                draft = await self.answerer.answer(q, context, history, model)
        except TimeoutError as e:
            raise LlmUnavailable(reason="응답 시간 초과") from e
        cited = sorted({s for s in draft.cited_secs if 0 <= s <= video.duration_sec})
        row = crud.add(self.session, video.id, q, draft.answer, cited, model, datetime.now(UTC))
        await self.session.commit()
        await self.session.refresh(row)
        return _turn(row)

    async def count_by_videos(self, video_ids: list[int]) -> dict[int, int]:
        """VA-MS-004#ChatService.count_by_videos

        영상마다 저장된 턴 수. 목록이 영상 수만큼 쿼리를 쓰지 않게 한 번에 센다.

        Args:
            video_ids: 영상 id들

        Returns:
            {영상 id: 턴 수}. 턴이 없는 영상은 키가 없다(부르는 쪽이 `.get(id, 0)`)
        """
        if not video_ids:
            return {}
        return await crud.counts(self.session, video_ids)

    async def context_for(self, video: Video, question: str) -> list[Segment]:
        """VA-MS-004#ChatService.context_for

        맥락 구간. 스크립트가 토큰 상한 안이면 전부. 넘으면 챕터마다 글(제목 · 요점 × 배수 + 그
        챕터의 스크립트)과 질문의 두 글자 조각으로 BM25 점수를 내, 점수순 앞 설정값만큼 고르고 직전
        턴의 근거 챕터를 1위 바로 뒤에 둔다(이어지는 질문). 둘 다 없으면 앞 챕터들. 고른 챕터
        범위의 구간을 시각순으로 모으고, 상한을 넘으면 고른 순서의 뒤에서부터 뺀다.

        Args:
            video: 영상(analyzed)
            question: 다듬은 질문

        Returns:
            구간 목록, 시각순
        """
        analysis = AnalysisService(self.session)  # 구간 · 챕터만 읽는다 — 포트 없이
        segments = await analysis.segments_of(video.id)
        if _tokens(segments) <= config.CHAT_TOKEN_LIMIT:
            return segments
        chapters = sorted(await analysis.chapters_of(video.id), key=lambda c: c.start_sec)
        if not chapters:
            return segments
        # 구간을 챕터에 한 번 나눠 담는다 — 범위는 챕터 시작 ~ 다음 챕터 시작(마지막은 영상 끝).
        # 점수 · 고르기 · 근거 시각 찾기가 같은 나눔을 쓴다
        starts = [c.start_sec for c in chapters]
        parts: dict[int, list[Segment]] = {c.seq: [] for c in chapters}
        for s in segments:
            if (c := _chapter_at(chapters, starts, s.start_sec)) is not None:
                parts[c.seq].append(s)
        docs = {
            c.seq: _grams(" ".join([c.title, *c.bullets])) * config.CHAT_SUMMARY_WEIGHT
            + _grams(" ".join(s.text for s in parts[c.seq]))
            for c in chapters
        }
        scores = _bm25(_grams(question), docs)
        ranked = sorted(
            (c for c in chapters if scores[c.seq] > 0), key=lambda c: (-scores[c.seq], c.start_sec)
        )[: config.CHAT_CHAPTERS]
        cited = await self._cited_chapters(video.id, chapters, starts)
        # 1위 → 직전 턴 근거(점수로 2 · 3위에 들었어도 이리로) → 나머지. 넘치면 뒤에서부터 빼
        # 1위가 남고 근거는 2 · 3위보다 오래 남는다
        picked = ranked[:1] + [c for c in cited if c not in ranked[:1]]
        picked += [c for c in ranked[1:] if c not in picked]
        picked = picked or chapters[: config.CHAT_CHAPTERS]
        while True:
            chosen = sorted((s for c in picked for s in parts[c.seq]), key=lambda s: s.seq)
            # 하나만 남으면 넘어도 그대로 — 챕터 안을 자르면 맞는 구간을 잃는다
            if _tokens(chosen) <= config.CHAT_TOKEN_LIMIT or len(picked) == 1:
                return chosen
            picked = picked[:-1]

    async def _cited_chapters(
        self, video_id: int, chapters: list[Chapter], starts: list[float]
    ) -> list[Chapter]:
        # 근거가 있는 가장 최근 턴의 근거 시각이 든 챕터 — 이어지는 질문('그 실험은 누가 했어요?')은
        # 낱말로 못 찾는다. 바로 앞 답이 '다루지 않는다'여서 근거가 없으면 그 앞 턴의 것
        for turn in await crud.recent(self.session, video_id, config.CHAT_HISTORY_TURNS):
            if not turn.cited_secs:
                continue
            found: list[Chapter] = []
            for sec in turn.cited_secs:
                c = _chapter_at(chapters, starts, sec)
                if c is not None and c not in found:
                    found.append(c)
            return found
        return []

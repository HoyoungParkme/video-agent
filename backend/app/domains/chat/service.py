"""ChatService — 영상에 질문하기(VA-MS-004). 기록 · 질문 · 맥락 고르기 · 영상 목록의 턴 수.

세션은 부르는 쪽(라우터 · VideoService)의 것이다.
"""

from __future__ import annotations

import asyncio
import re
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

if TYPE_CHECKING:
    from app.domains.video.schemas import Video

# 낱말 나누기 — 한글이 든 어절은 2자 이상, 영문 · 숫자 단어는 소문자로. 조사 · 어미는 떼지 않는다
_SPLIT = re.compile(r"[^\w]+")
_HANGUL = re.compile(r"[가-힣]")
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


def _tokens(segments: list[Segment]) -> float:
    # 토큰 어림 — 글자 수 ÷ 2(MS-004)
    return sum(len(s.text) for s in segments) / 2


def _words(text: str) -> list[str]:
    return [w for w in _SPLIT.split(text.lower()) if w and not (_HANGUL.search(w) and len(w) < 2)]


def _score(chapter: Chapter, words: list[str]) -> int:
    # 질문 낱말이 챕터 글에 들어 있거나, 챕터 글의 2자 이상 낱말이 질문 낱말에 들어 있으면 맞다
    # — '비용'이 '비용은'과 맞게
    text = " ".join([chapter.title, *chapter.bullets]).lower()
    own = [w for w in _words(text) if len(w) >= 2]
    return sum(1 for w in words if w in text or any(o in w for o in own))


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

        맥락 구간. 스크립트가 토큰 상한 안이면 전부. 넘으면 질문 낱말이 맞는 챕터를 점수순으로
        설정값만큼, 맞는 것이 없으면 최근 턴의 근거가 든 챕터(이어지는 질문), 그것도 없으면 앞
        챕터들. 고른 챕터 범위의 구간을 시각순으로 모으고, 상한을 넘으면 점수 낮은 챕터부터 뺀다.

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
        words = _words(question)
        scored = sorted(
            ((c, _score(c, words)) for c in chapters), key=lambda x: (-x[1], x[0].start_sec)
        )
        picked = [c for c, n in scored if n > 0][: config.CHAT_CHAPTERS]
        if not picked:
            picked = await self._cited_chapters(video.id, chapters)
        if not picked:
            picked = chapters[: config.CHAT_CHAPTERS]
        # 범위는 챕터 시작 ~ 다음 챕터 시작(마지막은 영상 끝)
        ends = {c.seq: nxt.start_sec for c, nxt in zip(chapters, chapters[1:], strict=False)}
        while True:
            chosen = [
                s
                for s in segments
                if any(c.start_sec <= s.start_sec < ends.get(c.seq, float("inf")) for c in picked)
            ]
            if _tokens(chosen) <= config.CHAT_TOKEN_LIMIT or len(picked) == 1:
                return chosen
            picked = picked[:-1]

    async def _cited_chapters(self, video_id: int, chapters: list[Chapter]) -> list[Chapter]:
        # 최근 턴(새것부터)의 근거 시각이 든 챕터 — 이어지는 질문('그거 성능은?')의 맥락
        found: list[Chapter] = []
        for turn in await crud.recent(self.session, video_id, config.CHAT_HISTORY_TURNS):
            for sec in turn.cited_secs:
                inside = [c for c in chapters if c.start_sec <= sec]
                if inside and inside[-1] not in found:
                    found.append(inside[-1])
        return found[: config.CHAT_CHAPTERS]

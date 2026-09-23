"""결과 묶음의 응답 형태(VA-API-001 4장)와 내부 타입(VA-DOM-002 2.6).

내부 타입 — CaptionLine · SummaryDraft · ChapterDraft. 포트와 서비스 사이에서만 오간다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

from app.core.settings import Models
from app.domains.analysis.models import TranscriptSource
from app.domains.video.schemas import Video


class Segment(BaseModel):
    """스크립트 한 줄. 시각은 초."""

    seq: int
    start_sec: float
    end_sec: float
    text: str


class Transcript(BaseModel):
    source: TranscriptSource
    language: str
    model: str | None
    segments: list[Segment]


class Insight(BaseModel):
    seq: int
    text: str
    source_secs: list[float]


class Summary(BaseModel):
    one_liner: str
    model: str
    insights: list[Insight]


class Part(BaseModel):
    """60분 넘는 영상의 파트. end_sec는 다음 파트의 시작 또는 영상 길이."""

    seq: int
    title: str
    start_sec: float
    end_sec: float
    chapter_count: int


class Chapter(BaseModel):
    seq: int
    part_seq: int | None
    start_sec: float
    title: str
    bullets: list[str]


class SuggestedQuestion(BaseModel):
    seq: int
    text: str


class Result(BaseModel):
    """결과 화면(UI-4)이 받는 것 전부 — 구간을 나누지 않는다."""

    video: Video
    transcript: Transcript
    summary: Summary
    parts: list[Part]
    chapters: list[Chapter]
    suggested_questions: list[SuggestedQuestion]
    models: Models
    analyzed_at: datetime


@dataclass(frozen=True)
class CaptionLine:
    """저장 전의 스크립트 한 줄 — 자막 큐 하나 또는 받아쓰기 구간 하나."""

    start_sec: float
    end_sec: float
    text: str


@dataclass(frozen=True)
class SummaryDraft:
    """모델이 준 한 줄 요약과 인사이트(문장, 출처 시각들). 개수 · 시각 보정은 서비스가 한다."""

    one_liner: str
    insights: list[tuple[str, list[float]]]


@dataclass(frozen=True)
class ChapterDraft:
    """모델이 준 파트(제목, 시작)와 챕터(파트 번호, 시작, 제목, 요점)."""

    parts: list[tuple[str, float]]
    chapters: list[tuple[int | None, float, str, list[str]]]

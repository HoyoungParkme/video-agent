"""결과 묶음의 응답 형태(VA-API-001 4장)와 내부 타입(VA-DOM-002 2.6).

내부 타입 — CaptionLine · SummaryDraft · ChapterDraft · FrameShot. 포트와 서비스 사이에서만 오간다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel

from app.core.settings import Models
from app.domains.analysis.models import FrameSource, TranscriptSource
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


class FramesState(StrEnum):
    """결과의 장면 상태 — absent: 장면 단계 전 결과(채울 수 있다) · making: 만드는 중 · done: 끝남 ·
    unavailable: 음성 파일 · 원본 없음(VA-API-001 FramesState)."""

    absent = "absent"
    making = "making"
    done = "done"
    unavailable = "unavailable"


class ExportMethod(StrEnum):
    """내보내기 방법(미리 보기의 쿼리 `method`). 파일로 저장한 노트에만 스크립트 절 · 그림 줄."""

    file = "file"
    clipboard = "clipboard"


class ExportFile(BaseModel):
    """함께 쓰는 파일 하나(UI-7 2.3 칩). name은 `data/export/` 안의 파일 이름."""

    kind: Literal["note", "script", "frame", "infographic"]
    name: str


class ExportPreview(BaseModel):
    """내보낼 마크다운 전체와 파일 이름. path는 보일 경로 `data/export/{filename}.md`.

    files는 파일로 저장할 때 함께 쓸 파일(노트 · 스크립트, 있으면 장면 · 인포그래픽).
    복사는 빈 목록이다.
    """

    filename: str
    path: str
    markdown: str
    files: list[ExportFile]


class ExportResult(BaseModel):
    """쓴 파일 — path는 노트의 보일 경로, bytes는 쓴 파일 전부의 바이트 합.

    images는 쓴 그림 수(장면 + 인포그래픽) — 짧은 알림의 '· 그림 {n}장'. files는 쓴 파일.
    """

    filename: str
    path: str
    bytes: int
    images: int
    files: list[ExportFile]


class ExportRequest(BaseModel):
    """파일로 저장 요청. with_chat이면 질문 기록을 맨 끝에 붙인다."""

    with_chat: bool = False


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


@dataclass(frozen=True)
class FrameShot:
    """얻은 장면 한 장 — 실제 칸의 시각(챕터 시작과 몇 초 다를 수 있다) · 크기 · 임시 파일 경로."""

    sec: float
    source: FrameSource
    width: int
    height: int
    path: str

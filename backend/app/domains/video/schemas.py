"""영상 묶음의 요청 · 응답 형태(VA-API-001 4장)와 내부 타입 SourceInfo(VA-DOM-002 2.6)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.domains.job.schemas import Estimate, JobSummary
from app.domains.video.models import CaptionKind, SourceKind


class VideoStatus(StrEnum):
    """영상의 지금 상태 — 컬럼이 아니라 최근 작업에서 계산한다(VideoService.to_dto)."""

    registered = "registered"
    in_progress = "in_progress"
    failed = "failed"
    analyzed = "analyzed"


class Video(BaseModel):
    """영상 하나 — 행의 값 + 계산한 상태 · 분석 완료 시각 + 대화 수."""

    id: int
    source_kind: SourceKind
    source_id: str
    title: str
    channel: str | None
    duration_sec: int
    origin: str
    has_captions: bool
    caption_language: str | None
    caption_kind: CaptionKind | None
    status: VideoStatus
    analyzed_at: datetime | None
    created_at: datetime
    chat_turn_count: int


class VideoSummary(Video):
    """목록 행 — 영상 + 최근 작업 요약."""

    job: JobSummary


class VideoDetail(BaseModel):
    video: Video
    job: JobSummary | None


class YouTubeSource(BaseModel):
    source: Literal["youtube"]
    url: str


class LocalSource(BaseModel):
    source: Literal["local"]
    path: str


# `source`로 가른다 — youtube면 url, local이면 inbox 안 파일 이름
RegisterRequest = Annotated[YouTubeSource | LocalSource, Field(discriminator="source")]


class RegisterResponse(BaseModel):
    """영상(새로 만들었거나 기존 것)과 예상치. 예상치는 작업이 없을 때만."""

    video: Video
    estimate: Estimate | None


class InboxFile(BaseModel):
    name: str
    size_bytes: int
    duration_sec: int | None
    kind: Literal["video", "audio"]
    modified_at: datetime


class InboxListing(BaseModel):
    """inbox 파일 목록. path는 사용자에게 보일 호스트 쪽 경로."""

    path: str
    files: list[InboxFile]


class SourceInfo(BaseModel):
    """출처에서 읽은 영상 정보 — 포트가 만들어 VideoService.register가 행으로 쓴다."""

    source_kind: SourceKind
    source_id: str
    title: str
    channel: str | None
    duration_sec: int
    origin: str
    has_captions: bool
    caption_language: str | None
    caption_kind: CaptionKind | None

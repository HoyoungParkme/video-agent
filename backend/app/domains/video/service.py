"""VideoService — inbox 목록 · 영상 등록 · 목록 · 하나(VA-MS-001).

라우터와 main.py(load_video)가 부른다. 세션은 부르는 쪽의 것이다. 작업 요약과 대화 수는
JobService · ChatService에 id로 묻는다 — 같은 세션으로(VA-DOM-002 3.2).
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.core.errors import (
    Internal,
    NoAudioTrack,
    NotFound,
    PathOutsideInbox,
    UnsupportedFile,
    UrlInvalid,
    VideoTooLong,
)
from app.core.settings import settings
from app.domains.chat.service import ChatService
from app.domains.job.models import JobStatus
from app.domains.job.schemas import JobSummary
from app.domains.job.service import JobService
from app.domains.video import crud
from app.domains.video.models import SourceKind, VideoRow
from app.domains.video.ports import MediaProbePort, YouTubeInfoPort
from app.domains.video.schemas import (
    InboxFile,
    InboxListing,
    RegisterRequest,
    SourceInfo,
    Video,
    VideoDetail,
    VideoStatus,
    VideoSummary,
    YouTubeSource,
)

ACCEPTED_URLS = ["watch", "youtu.be", "shorts"]
_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")


def _youtube_id(url: str) -> str | None:
    # watch · youtu.be · shorts 셋만(www. · m. 허용). 주소 앞의 https://는 없어도 된다
    text = url.strip()
    u = urlsplit(text if "://" in text else f"https://{text}")
    if u.scheme not in ("http", "https"):
        return None
    host = (u.hostname or "").removeprefix("www.").removeprefix("m.")
    if host == "youtu.be":
        candidate = u.path.strip("/")
    elif host == "youtube.com" and u.path == "/watch":
        candidate = parse_qs(u.query).get("v", [""])[0]
    elif host == "youtube.com" and u.path.startswith("/shorts/"):
        candidate = u.path.removeprefix("/shorts/").strip("/")
    else:
        return None
    return candidate if _VIDEO_ID.fullmatch(candidate) else None


def accepted() -> list[str]:
    """받는 확장자 — 영상 넷 · 음성 셋(MS-001 설정값 ACCEPTED)."""
    return config.VIDEO_EXTS + config.AUDIO_EXTS


def _ext(name: str) -> str:
    return Path(name).suffix.lower().lstrip(".")


def _listed(entry: os.DirEntry[str]) -> bool:
    # inbox 바로 아래의 받는 형식 파일만 — 하위 폴더 · 숨김 파일 · 다른 확장자는 안 보인다
    return entry.is_file() and not entry.name.startswith(".") and _ext(entry.name) in accepted()


def _sha256(path: Path) -> str:
    # 1MB씩 — 수 GB 파일도 메모리를 조금만 쓴다. 이벤트 루프를 막지 않게 스레드에서 부른다
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def _check_inbox_name(name: str) -> None:
    # inbox 바로 아래 파일 이름만 — 하위 폴더 · 절대 경로 · 숨김 · ..는 막는다
    if "/" in name or "\\" in name or name.startswith(".") or ".." in name:
        raise PathOutsideInbox()
    if Path(name).suffix.lower().lstrip(".") not in config.VIDEO_EXTS + config.AUDIO_EXTS:
        raise UnsupportedFile(reason="받지 않는 형식이에요", accepted=accepted())
    if not (Path(config.INBOX_DIR) / name).is_file():
        raise NotFound(resource="inbox_file", id=name)


class VideoService:
    """영상 행과 그 응답 형태. 상태(status)를 계산하는 곳은 to_dto 하나다.

    - list_inbox(): inbox 파일 목록(길이까지)
    - register(): 키 확인 → 형식 → 정보 → 길이 상한 → 중복 → 생성 또는 덮어쓰기
    - list() · get(): 작업이 있는 영상 목록(최근 순) · 영상 하나와 최근 작업
    - info_of() · to_dto(): 출처별 정보 조회 · 행 → Video
    """

    def __init__(
        self, session: AsyncSession, youtube_info: YouTubeInfoPort, media_probe: MediaProbePort
    ) -> None:
        self.session = session
        self.youtube_info = youtube_info
        self.media_probe = media_probe
        self.jobs = JobService(session)
        self.chats = ChatService(session)

    @staticmethod
    def to_dto(row: VideoRow, job: JobSummary | None, chat_count: int) -> Video:
        """VA-MS-001#VideoService.to_dto

        행 + 최근 작업 + 대화 수 → Video. 상태와 분석 완료 시각은 컬럼이 아니라 여기서 계산한다 —
        이 함수 말고 status를 만드는 곳이 없다.

        Args:
            row: 영상 행
            job: 최근 작업 요약(없으면 None)
            chat_count: 저장된 대화 턴 수

        Returns:
            Video
        """
        if job is None:
            status = VideoStatus.registered
        elif job.status in (JobStatus.queued, JobStatus.running):  # 대기 중도 진행 중이다
            status = VideoStatus.in_progress
        elif job.status == JobStatus.failed:
            status = VideoStatus.failed
        else:
            status = VideoStatus.analyzed
        return Video(
            id=row.id,
            source_kind=row.source_kind,
            source_id=row.source_id,
            title=row.title,
            channel=row.channel,
            duration_sec=row.duration_sec,
            origin=row.origin,
            has_captions=row.has_captions,
            caption_language=row.caption_language,
            caption_kind=row.caption_kind,
            status=status,
            analyzed_at=job.finished_at if job and status == VideoStatus.analyzed else None,
            created_at=row.created_at,
            chat_turn_count=chat_count,
        )

    async def list_inbox(self) -> InboxListing:
        """VA-MS-001#VideoService.list_inbox

        inbox 폴더 바로 아래의 영상 · 음성 파일, 수정 시각 최근 순. 길이는 파일마다
        `config.PROBE_CONCURRENCY`개씩 동시에 잰다 — 못 재면 None(그 파일을 고르면 등록이
        unsupported-file을 낸다).

        Returns:
            사용자에게 보일 폴더 경로와 파일 목록. 빈 폴더면 files=[]

        Raises:
            Internal: inbox 폴더가 없거나 읽을 수 없다 — 마운트가 안 된 설치 오류(빈 폴더와 다르다)
        """
        try:
            entries = [e for e in os.scandir(config.INBOX_DIR) if _listed(e)]
        except OSError as e:
            raise Internal("inbox 폴더를 읽을 수 없어요") from e
        sem = asyncio.Semaphore(config.PROBE_CONCURRENCY)

        async def one(entry: os.DirEntry[str]) -> InboxFile | None:
            try:
                stat = entry.stat()
            except FileNotFoundError:  # 목록을 읽은 뒤 사라졌다(옮기는 중) — 그 파일만 뺀다
                return None
            duration: int | None = None
            async with sem:
                try:
                    duration = (await self.media_probe.probe(entry.path))[0]
                except Exception:  # 깨진 파일도 목록에는 보인다
                    duration = None
            return InboxFile(
                name=entry.name,
                size_bytes=stat.st_size,
                duration_sec=duration,
                kind="audio" if _ext(entry.name) in config.AUDIO_EXTS else "video",
                modified_at=datetime.fromtimestamp(stat.st_mtime, UTC),
            )

        files = [f for f in await asyncio.gather(*(one(e) for e in entries)) if f is not None]
        files.sort(key=lambda f: f.modified_at, reverse=True)
        return InboxListing(path=config.INBOX_DISPLAY_PATH, files=files)

    async def info_of(self, req: RegisterRequest) -> SourceInfo:
        """VA-MS-001#VideoService.info_of

        출처에서 영상 정보를 읽는다. YouTube는 포트가 정보만 받는다(내려받지 않는다).
        로컬 파일은 길이 · 음성 트랙을 재고 내용 SHA-256을 출처 식별자로 쓴다 — 이름을 바꿔도
        같은 영상이다. 해시는 스레드에서 1MB씩(수 GB면 몇 초 — 화면은 버튼 대기 표시).

        Args:
            req: YouTube 주소 또는 inbox 파일 이름

        Returns:
            출처 식별자 · 제목 · 채널 · 길이 · 자막

        Raises:
            SourceUnavailable: YouTube 정보를 못 가져왔다
            UnsupportedFile: 파일을 열 수 없다(포트)
            NoAudioTrack: 음성 트랙이 없는 파일
        """
        if isinstance(req, YouTubeSource):
            return await self.youtube_info.info(req.url)
        path = Path(config.INBOX_DIR) / req.path
        duration, has_audio = await self.media_probe.probe(str(path))
        if not has_audio:
            raise NoAudioTrack(duration_sec=duration)
        return SourceInfo(
            source_kind=SourceKind.local,
            source_id=await asyncio.to_thread(_sha256, path),
            title=req.path,
            channel=None,
            duration_sec=duration,
            origin=req.path,
            has_captions=False,
            caption_language=None,
            caption_kind=None,
        )

    async def register(self, req: RegisterRequest) -> Video:
        """VA-MS-001#VideoService.register

        영상을 등록한다 — 사전 안내 전까지. 걸리는 곳에서 멈추고, 순서가 규칙이다.
        같은 영상(출처 식별자)이 있으면 그것을 돌려주고, 작업이 없던 것이면 새 정보로 덮어쓴다.

        Args:
            req: YouTube 주소 또는 inbox 파일 이름

        Returns:
            영상. status는 registered · in_progress · failed · analyzed 중 하나

        Raises:
            KeyMissing · KeyInvalid: 키가 없거나 확인에 실패했다
            UrlInvalid · PathOutsideInbox · UnsupportedFile · NotFound: 형식
            SourceUnavailable · NoAudioTrack: 정보 조회(info_of)
            VideoTooLong: 3시간 초과
        """
        await settings.check_stored_key()  # 분석 버튼을 누를 때 확인한다(UI-5 규칙)
        await settings.require_key()
        if isinstance(req, YouTubeSource):
            if _youtube_id(req.url) is None:
                raise UrlInvalid(accepted=ACCEPTED_URLS)
        else:
            _check_inbox_name(req.path)
        info = await self.info_of(req)
        if info.duration_sec > config.MAX_DURATION_SEC:
            raise VideoTooLong(duration_sec=info.duration_sec, max_sec=config.MAX_DURATION_SEC)
        row = await crud.by_source_id(self.session, info.source_id)
        job: JobSummary | None = None
        if row is not None:
            job = await self.jobs.latest(row.id)
            if job is None:  # 사전 안내에서 취소했던 영상 — 처음 넣은 것과 같게
                crud.overwrite(row, info)
                await self.session.commit()
        else:
            row = await self._insert(info)
            job = await self.jobs.latest(row.id)
        count = (await self.chats.count_by_videos([row.id])).get(row.id, 0)
        return self.to_dto(row, job, count)

    async def _insert(self, info: SourceInfo) -> VideoRow:
        # 같은 영상을 동시에 두 번 넣으면 둘째가 unique 위반 — 다시 읽어 그 행으로(한 번만)
        try:
            row = crud.insert(self.session, info)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            found = await crud.by_source_id(self.session, info.source_id)
            if found is None:
                raise
            return found
        await self.session.refresh(row)  # created_at은 DB가 채운다
        return row

    async def list(self) -> list[VideoSummary]:
        """VA-MS-001#VideoService.list

        작업이 있는 영상 목록, 작업을 시작한 때의 최근 순. 작업 요약과 대화 수는 한 번에 받는다.

        Returns:
            목록 행들. 없으면 빈 목록(화면이 빈 상태 상자)
        """
        rows = await crud.with_jobs(self.session)
        ids = [r.id for r in rows]
        jobs = await self.jobs.latest_by_videos(ids)
        counts = await self.chats.count_by_videos(ids)
        out = [
            VideoSummary(
                **self.to_dto(r, jobs[r.id], counts.get(r.id, 0)).model_dump(), job=jobs[r.id]
            )
            for r in rows
            if r.id in jobs
        ]
        return sorted(out, key=lambda v: v.job.started_at, reverse=True)

    async def get(self, video_id: int) -> VideoDetail:
        """VA-MS-001#VideoService.get

        영상 하나와 최근 작업 요약. 작업 · 결과 · 대화 라우터가 인자용으로도 부른다.

        Args:
            video_id: 영상 id

        Returns:
            영상과 작업 요약(작업이 없으면 None)

        Raises:
            NotFound: 영상이 없다(resource=video)
        """
        row = await crud.by_id(self.session, video_id)
        if row is None:
            raise NotFound(resource="video", id=video_id)
        job = await self.jobs.latest(video_id)
        count = (await self.chats.count_by_videos([video_id])).get(video_id, 0)
        return VideoDetail(video=self.to_dto(row, job, count), job=job)

"""VideoService — inbox 목록 · 영상 등록 · 목록 · 하나(VA-MS-001).

라우터와 main.py(load_video)가 부른다. 세션은 부르는 쪽의 것이다. 작업 요약과 대화 수는
JobService · ChatService에 id로 묻는다 — 같은 세션으로(VA-DOM-002 3.2).
"""

from __future__ import annotations

import asyncio
import contextlib
import errno
import hashlib
import os
import re
import shutil
import unicodedata
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, BinaryIO
from urllib.parse import parse_qs, urlsplit

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import ClientDisconnect

from app.core.config import config
from app.core.errors import (
    Internal,
    NoAudioTrack,
    NoSpace,
    NotFound,
    PathOutsideInbox,
    UnsupportedFile,
    UploadIncomplete,
    UrlInvalid,
    Validation,
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
from app.shared import sources

ACCEPTED_URLS = ["watch", "youtu.be", "shorts"]
_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
NAME_MAX = 300  # 올린 파일 이름 — 제목 칸(videos.title varchar(300))에 그대로 들어간다


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


def _append(f: BinaryIO, sha: Any, block: bytes) -> None:
    # 받은 조각 묶음 — 해시와 쓰기를 스레드에서(수 GB도 이벤트 루프를 막지 않게)
    sha.update(block)
    f.write(block)


def _no_space(size: int, free: int) -> NoSpace:
    return NoSpace(needed_bytes=size + config.UPLOAD_SPARE_BYTES, free_bytes=free)


async def _free(folder: Path) -> int:
    return (await asyncio.to_thread(shutil.disk_usage, folder)).free


async def _receive(part: Path, size: int, body: AsyncIterator[bytes]) -> str:
    # 본문을 part에 쓰며 SHA-256(inbox 등록과 같은 해시). Content-Length보다 많이 오면 거기서 멈춘다
    sha = hashlib.sha256()
    got = 0
    buf = bytearray()
    f = await asyncio.to_thread(part.open, "wb")
    try:
        async for chunk in body:
            got += len(chunk)
            if got > size:
                break
            buf += chunk
            if len(buf) >= config.UPLOAD_WRITE_BYTES:
                await asyncio.to_thread(_append, f, sha, bytes(buf))
                buf.clear()
        if buf:
            await asyncio.to_thread(_append, f, sha, bytes(buf))
        await asyncio.to_thread(f.close)  # 남은 버퍼를 내보낸다 — 디스크가 차면 여기서도 난다
    except ClientDisconnect as e:  # 올리다 끊겼다 — 응답은 닿지 않는다
        raise UploadIncomplete(received_bytes=got, expected_bytes=size) from e
    except OSError as e:
        if e.errno == errno.ENOSPC:
            raise _no_space(size, await _free(part.parent)) from e
        raise
    finally:
        if not f.closed:
            with contextlib.suppress(OSError):
                await asyncio.to_thread(f.close)
    if got != size:
        raise UploadIncomplete(received_bytes=got, expected_bytes=size)
    return sha.hexdigest()


async def _remove_copy(origin: str, source_id: str) -> None:
    # 올린 사본을 지운다 — 없으면(이미 지웠다) 조용히. 놓기 · 지우기 · 청소가 같은 규칙이다
    await asyncio.to_thread(sources.local_path(origin, source_id, True).unlink, missing_ok=True)


def _check_inbox_name(name: str) -> None:
    # inbox 바로 아래 파일 이름만 — 하위 폴더 · 절대 경로 · 숨김 · ..는 막는다
    if "/" in name or "\\" in name or name.startswith(".") or ".." in name:
        raise PathOutsideInbox()
    if _ext(name) not in accepted():
        raise UnsupportedFile(reason="받지 않는 형식이에요", accepted=accepted())
    if not (Path(config.INBOX_DIR) / name).is_file():
        raise NotFound(resource="inbox_file", id=name)


def _check_length(duration_sec: int) -> None:
    # 3시간 상한(PRD N2) — 길이를 실어야 화면이 시작 불가 판에 보인다. info_of · _probed만 부른다
    if duration_sec > config.MAX_DURATION_SEC:
        raise VideoTooLong(duration_sec=duration_sec, max_sec=config.MAX_DURATION_SEC)


class VideoService:
    """영상 행과 그 응답 형태. 상태(status)를 계산하는 곳은 to_dto 하나다.

    - list_inbox(): inbox 파일 목록(길이까지)
    - register(): 키 확인 → 형식 → 정보 → 길이 상한 → 중복 → 생성 또는 덮어쓰기
    - upload(): 키 → 이름 · 형식 → 디스크 → 받으며 해시 → 판정 → 중복 → 사본(원본 자리)
    - list() · get(): 작업이 있는 영상 목록(최근 순) · 영상 하나와 최근 작업
    - delete(): 영상과 딸린 것 전부 — 행은 cascade, 임시 폴더는 커밋 뒤
    - release_upload(): 올린 사본을 놓는다(작업이 done이 된 뒤)
    - sweep_uploads(): 시작 때 올리다 만 것 · 주인 없는 사본 · 끝난 작업의 사본을 지운다
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
        이 함수 말고 status를 만드는 곳이 없다. 올린 사본의 크기는 파일을 봐서 붙인다(지웠으면
        None).

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
        upload_bytes = None
        if row.uploaded:
            copy = sources.local_path(row.origin, row.source_id, True)
            with contextlib.suppress(FileNotFoundError):  # 분석이 끝나 지웠다
                upload_bytes = copy.stat().st_size
        return Video(
            id=row.id,
            source_kind=row.source_kind,
            source_id=row.source_id,
            title=row.title,
            channel=row.channel,
            duration_sec=row.duration_sec,
            origin=row.origin,
            uploaded=row.uploaded,
            upload_bytes=upload_bytes,
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

    async def _probed(self, path: str) -> int:
        # 로컬 파일 판정 — 열기 · 음성 트랙 · 3시간 상한. inbox 등록(info_of)과 올리기(upload)가
        # 같은 판정을 지난다(두 벌이 되지 않게). 해시보다 먼저 부른다
        duration, has_audio = await self.media_probe.probe(path)
        if not has_audio:
            raise NoAudioTrack(duration_sec=duration)
        _check_length(duration)
        return duration

    async def info_of(self, req: RegisterRequest) -> SourceInfo:
        """VA-MS-001#VideoService.info_of

        출처에서 영상 정보를 읽는다. YouTube는 포트가 정보만 받는다(내려받지 않는다).
        로컬 파일은 길이 · 음성 트랙을 재고 내용 SHA-256을 출처 식별자로 쓴다 — 이름을 바꿔도
        같은 영상이다. 해시는 스레드에서 1MB씩(수 GB면 몇 초 — 화면은 버튼 대기 표시).
        길이 상한(3시간)은 여기서 본다 — YouTube는 정보를 받은 뒤, 로컬은 해시 전에(4시간짜리 큰
        파일을 다 읽고 나서 거절하지 않게). 로컬 판정은 올리기(upload)와 같은 함수다.

        Args:
            req: YouTube 주소 또는 inbox 파일 이름

        Returns:
            출처 식별자 · 제목 · 채널 · 길이 · 자막

        Raises:
            SourceUnavailable: YouTube 정보를 못 가져왔다
            UnsupportedFile: 파일을 열 수 없다(포트)
            NoAudioTrack: 음성 트랙이 없는 파일
            VideoTooLong: 3시간을 넘는다(로컬은 해시 전)
        """
        if isinstance(req, YouTubeSource):
            info = await self.youtube_info.info(req.url)
            _check_length(info.duration_sec)
            return info
        path = Path(config.INBOX_DIR) / req.path
        duration = await self._probed(str(path))  # 해시 전에
        return SourceInfo(
            source_kind=SourceKind.local,
            source_id=await asyncio.to_thread(_sha256, path),
            title=req.path,
            channel=None,
            duration_sec=duration,
            origin=req.path,
            uploaded=False,
            has_captions=False,
            caption_language=None,
            caption_kind=None,
        )

    async def register(self, req: RegisterRequest) -> Video:
        """VA-MS-001#VideoService.register

        영상을 등록한다 — 사전 안내 전까지. 걸리는 곳에서 멈추고, 순서가 규칙이다.
        같은 영상(출처 식별자)이 있으면 그것을 돌려주고, 작업이 없던 것이면 새 정보로 덮어쓴다(작업
        없는 올린 영상이면 inbox 영상이 된다). inbox 영상은 작업이 있어도 이름(origin)만 지금 것으로
        고친다 — 이름을 바꾼 뒤 다시 시도해도 파이프라인이 파일을 찾게. 올린 영상은 고치지 않는다 —
        다시 시도는 사본을 읽고, 사본 이름은 원래 이름의 확장자를 따른다.

        Args:
            req: YouTube 주소 또는 inbox 파일 이름

        Returns:
            영상. status는 registered · in_progress · failed · analyzed 중 하나

        Raises:
            KeyMissing · KeyInvalid: 키가 없거나 확인에 실패했다
            UrlInvalid · PathOutsideInbox · UnsupportedFile · NotFound: 형식
            SourceUnavailable · NoAudioTrack · VideoTooLong: 정보 조회와 길이 상한(info_of)
        """
        await settings.check_stored_key()  # 분석 버튼을 누를 때 확인한다(UI-5 규칙)
        await settings.require_key()
        if isinstance(req, YouTubeSource):
            if _youtube_id(req.url) is None:
                raise UrlInvalid(accepted=ACCEPTED_URLS)
        else:
            _check_inbox_name(req.path)
        info = await self.info_of(req)
        row = await crud.by_source_id(self.session, info.source_id)
        job: JobSummary | None = None
        if row is not None:
            job = await self.jobs.latest(row.id)
            if job is None:  # 사전 안내에서 취소했던 영상 — 처음 넣은 것과 같게
                crud.overwrite(row, info)
                await self.session.commit()
            elif (
                info.source_kind == SourceKind.local
                and not row.uploaded
                and row.origin != info.origin
            ):
                crud.rename(row, info.origin)  # 제목은 그대로
                await self.session.commit()
        else:
            row = await self._insert(info)
            job = await self.jobs.latest(row.id)
        count = (await self.chats.count_by_videos([row.id])).get(row.id, 0)
        return self.to_dto(row, job, count)

    async def upload(self, name: str, size: int, body: AsyncIterator[bytes]) -> Video:
        """VA-MS-001#VideoService.upload

        브라우저가 올린 파일 하나를 등록한다 — 사전 안내 전까지. 키 · 이름 · 디스크는 본문을 읽기
        전에 본다(큰 파일을 다 받은 뒤 멈추지 않게). 본문은 data/uploads/.part-*에 쓰며 SHA-256을
        재고, 로컬 판정(inbox 등록과 같은 _probed)을 지나면 같은 영상을 찾는다. 작업이 있는 영상이면
        그것을 돌려주고 사본은 두지 않는다. 없으면 사본을 {sha}{확장자}로 옮겨 원본 자리로 삼는다
        (작업이 없던 영상이면 올린 정보로 덮어쓴다). 옮기지 못한 채 끝나는 모든 길에서 .part를
        지운다.

        Args:
            name: 원래 파일 이름 — 라우터가 X-File-Name의 퍼센트 인코딩을 푼 것. 제목 · origin에만
                쓰고 사본 이름은 해시다
            size: Content-Length
            body: 본문 조각(request.stream())

        Returns:
            영상. 새로 · 덮어쓰기면 registered, 작업이 있는 영상이면 그 작업을 따른다

        Raises:
            KeyMissing · KeyInvalid: 키가 없거나 확인에 실패했다 — 본문을 읽지 않는다
            Validation: 이름이 비었거나 이상하다 · 크기가 없다
            UnsupportedFile: 받지 않는 확장자(본문을 읽지 않는다) · 열 수 없는 파일
            NoSpace: 디스크 여유가 크기 + 여유분보다 작다 · 받다가 찼다
            UploadIncomplete: 받은 크기가 Content-Length와 다르다 · 연결이 끊겼다
            NoAudioTrack · VideoTooLong: 음성 트랙이 없다 · 3시간을 넘는다
        """
        await settings.check_stored_key()  # 큰 파일을 다 받은 뒤 키 때문에 멈추지 않게 먼저
        await settings.require_key()
        name = unicodedata.normalize("NFC", name).strip()
        if not name or _CONTROL.search(name) or len(name) > NAME_MAX:
            message = f"파일 이름이 비었거나 제어 문자가 있거나 {NAME_MAX}자를 넘어요"
            raise Validation(errors=[{"field": "X-File-Name", "message": message}])
        if size <= 0:
            raise Validation(errors=[{"field": "Content-Length", "message": "크기가 없어요"}])
        if _ext(name) not in accepted():
            raise UnsupportedFile(reason="받지 않는 형식이에요", accepted=accepted())
        folder = Path(config.UPLOAD_DIR)
        await asyncio.to_thread(folder.mkdir, parents=True, exist_ok=True)
        free = await _free(folder)
        if free < size + config.UPLOAD_SPARE_BYTES:
            raise _no_space(size, free)
        # 확장자를 붙여 두면 ffprobe가 형식을 덜 헤맨다
        part = folder / f".part-{uuid.uuid4().hex}{Path(name).suffix.lower()}"
        moved = False
        try:
            sha = await _receive(part, size, body)
            info = SourceInfo(
                source_kind=SourceKind.local,
                source_id=sha,
                title=name,
                channel=None,
                duration_sec=await self._probed(str(part)),
                origin=name,
                uploaded=True,
                has_captions=False,
                caption_language=None,
                caption_kind=None,
            )
            row = await crud.by_source_id(self.session, sha)
            job = await self.jobs.latest(row.id) if row is not None else None
            if job is None:  # 새 영상이거나 작업이 없던 영상 — 이 사본이 원본 자리다
                copy = sources.local_path(name, sha, True)
                await asyncio.to_thread(os.replace, part, copy)
                moved = True
                if row is not None:  # 사전 안내에서 멈췄던 영상 — 올린 정보로 덮어쓴다
                    crud.overwrite(row, info)
                    await self.session.commit()
                else:
                    row = await self._insert(info)
                    job = await self.jobs.latest(row.id)
            # 작업이 있는 영상이면 그 영상 그대로 — 행 · 그 원본은 건드리지 않는다
        finally:
            if not moved:
                await asyncio.to_thread(part.unlink, missing_ok=True)
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

    async def delete(self, video_id: int) -> None:
        """VA-MS-001#VideoService.delete

        영상과 딸린 것 전부 — 작업 · 조각 · 스크립트 · 요약 · 챕터 · 장면 · 인포그래픽 · 추천
        질문 · 대화는 FK cascade가 지우고(앱이 자식을 차례로 지우지 않는다), 커밋 뒤 임시 폴더
        `data/tmp/{id}` · 장면 폴더 `data/frames/{id}` · 인포그래픽 `data/infographics/{id}.png` ·
        올린 사본을 지운다. 진행 중 작업은 라우터가 먼저 JobService.cancel로, 장면 채우기 ·
        인포그래픽 그리기는 AnalysisService.cancel_tasks로 멈춘다 — 여기서는 멈춰 있다고 본다.
        사전 안내에서 취소한 올린 영상도 이 길이다. inbox 원본 · 올린 파일의 원래 파일(PC에 있는
        것)과 내보낸 노트 · 그림은 건드리지 않는다(INFRA C4).

        Args:
            video_id: 영상 id

        Raises:
            NotFound: 영상이 없다(resource=video)
        """
        row = await crud.by_id(self.session, video_id)
        if row is None:
            raise NotFound(resource="video", id=video_id)
        copy = (row.origin, row.source_id) if row.uploaded else None  # 지운 뒤에는 행이 없다
        await crud.remove(self.session, video_id)
        await self.session.commit()
        # 수백 MB 음성 · 조각 파일일 수 있다 — 지우는 동안 다른 요청을 막지 않게 스레드로
        tmp = Path(config.DATA_DIR) / "tmp" / str(video_id)
        await asyncio.to_thread(shutil.rmtree, tmp, ignore_errors=True)
        frames = Path(config.FRAMES_DIR) / str(video_id)
        await asyncio.to_thread(shutil.rmtree, frames, ignore_errors=True)
        infographic = Path(config.INFOGRAPHICS_DIR) / f"{video_id}.png"
        await asyncio.to_thread(infographic.unlink, missing_ok=True)
        if copy is not None:  # 올린 사본 — release_upload와 같은 규칙
            await _remove_copy(*copy)

    @staticmethod
    async def release_upload(video: Video) -> None:
        """VA-MS-001#VideoService.release_upload

        올린 사본을 놓는다 — 작업이 done이 된 뒤 파이프라인이 부른다(main.py가 감싸 넘긴다).
        inbox · YouTube 영상이면 아무것도 하지 않는다. 행은 건드리지 않는다 — uploaded는 그대로다
        (다시 시도할 때 어디서 읽을지 정하는 값). 세션이 필요 없다.

        Args:
            video: 분석이 끝난 영상
        """
        if video.uploaded:
            await _remove_copy(video.origin, video.source_id)

    async def sweep_uploads(self) -> int:
        """VA-MS-001#VideoService.sweep_uploads

        시작 때 올린 사본을 청소한다 — main.py가 JobService.fail_orphans 뒤에 부른다(죽은 running이
        failed가 된 뒤라야 그 사본이 남는다). 올리다 만 `.part-*`는 지운다. 사본은 이름의 해시로
        주인을 찾아, 주인이 없거나 · 올린 영상이 아니거나 · 작업이 없거나(사전 안내에서 멈췄다) ·
        작업이 done이면 지운다. failed · queued · running은 남긴다 — 다시 시도 · 대기열이 읽는다.
        쿼리는 파일 수와 상관없이 영상 한 번 · 작업 요약 한 번이다.

        Returns:
            지운 파일 수(main.py가 로그 한 줄로 남긴다). 폴더가 없으면 0
        """
        folder = Path(config.UPLOAD_DIR)
        try:
            names = [e.name for e in os.scandir(folder) if e.is_file()]
        except FileNotFoundError:
            return 0
        doomed = [n for n in names if n.startswith(".part-")]  # 서버가 올리는 도중에 죽었다
        copies = {n: Path(n).stem for n in names if not n.startswith(".part-")}
        found = await crud.by_source_ids(self.session, set(copies.values()))
        rows = {r.source_id: r for r in found}
        jobs = await self.jobs.latest_by_videos([r.id for r in found])
        for name, sha in copies.items():
            row = rows.get(sha)
            job = jobs.get(row.id) if row is not None else None
            if row is None or not row.uploaded or job is None or job.status == JobStatus.done:
                doomed.append(name)
        for name in doomed:
            await asyncio.to_thread((folder / name).unlink, missing_ok=True)
        return len(doomed)

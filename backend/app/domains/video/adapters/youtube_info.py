"""YouTubeInfoPort 구현 — yt-dlp로 영상 정보만 받는다(VA-MS-006 youtube_info). 내려받지 않는다."""

from __future__ import annotations

from app.core.errors import SourceUnavailable
from app.domains.video.models import CaptionKind, SourceKind
from app.domains.video.schemas import SourceInfo
from app.infra import ytdlp
from app.infra.errors import YtdlpError, YtdlpKind
from app.shared import captions

# yt-dlp 실패 종류 → 사용자에게 보일 이유 한 줄
# (UI-2 시작 불가 판 '영상 정보를 가져오지 못했어요 — {이유}')
REASONS: dict[YtdlpKind, str] = {
    "private": "비공개 영상이에요",
    "unavailable": "삭제되었거나 볼 수 없는 영상이에요",
    "geo": "이 지역에서는 볼 수 없는 영상이에요",
    "network": "YouTube에 연결하지 못했어요",
    "extractor": "yt-dlp가 이 영상을 읽지 못했어요",
    "other": "영상 정보를 읽지 못했어요",
}
# YouTube가 바뀌어 추출기가 깨졌을 때 — 사용자가 할 수 있는 일(INFRA C7)
HINT = "yt-dlp 업데이트"


class YouTubeInfoAdapter:
    """YouTube 주소 → SourceInfo."""

    async def info(self, url: str) -> SourceInfo:
        """VA-MS-006#youtube_info.info

        제목 · 채널 · 길이 · 자막(수동 우선, 원래 언어 자동 자막)을 읽는다.

        Args:
            url: watch · youtu.be · shorts 주소

        Returns:
            SourceInfo — origin은 정규화한 watch 주소

        Raises:
            SourceUnavailable: 비공개 · 삭제 · 지역 제한 · 네트워크 · 추출기 오류,
                또는 길이가 없는 영상
        """
        try:
            raw = await ytdlp.info(url)
        except YtdlpError as e:
            raise SourceUnavailable(
                reason=REASONS[e.kind], hint=HINT if e.kind == "extractor" else None
            ) from e
        duration = raw.get("duration")
        if not duration or int(duration) <= 0:  # 라이브 · 예정 영상
            raise SourceUnavailable(reason="길이를 알 수 없는 영상이에요", hint=None)
        vid = raw["id"]
        picked = captions.pick(raw)
        return SourceInfo(
            source_kind=SourceKind.youtube,
            source_id=vid,
            title=raw.get("title") or vid,
            channel=raw.get("channel") or raw.get("uploader"),
            duration_sec=int(duration),
            origin=ytdlp.WATCH.format(vid),
            has_captions=picked is not None,
            caption_language=picked[1] if picked else None,
            caption_kind=CaptionKind(picked[2]) if picked else None,
        )

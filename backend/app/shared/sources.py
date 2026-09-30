"""로컬 영상의 원본 자리 — inbox 파일 또는 올린 사본(VA-MS-006). 음성 추출(파이프라인) · 장면
(결과 서비스) · 올리기(영상 서비스)가 같은 경로를 쓴다.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import config


def local_path(origin: str, source_id: str, uploaded: bool) -> Path:
    """VA-MS-006#sources.local_path

    로컬 영상의 원본 경로. 올린 사본은 `UPLOAD_DIR/{내용 해시}{확장자}`, 아니면
    `INBOX_DIR/{파일 이름}`. 파일이 있는지는 보지 않는다 — 부르는 쪽이 본다.

    Args:
        origin: inbox 파일 이름(올린 파일은 올릴 때의 이름)
        source_id: 내용 SHA-256
        uploaded: 올린 사본인가

    Returns:
        원본 경로
    """
    if uploaded:
        return Path(config.UPLOAD_DIR) / f"{source_id}{Path(origin).suffix.lower()}"
    return Path(config.INBOX_DIR) / origin

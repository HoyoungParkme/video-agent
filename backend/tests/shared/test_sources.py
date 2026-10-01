"""shared/sources — VA-MS-006 sources.local_path의 테스트 관점."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import config
from app.shared import sources

SHA = "ab" + "0" * 62


@pytest.fixture(autouse=True)
def dirs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "INBOX_DIR", "/app/inbox")
    monkeypatch.setattr(config, "DATA_DIR", "/app/data")


def test_inbox_file_is_under_inbox() -> None:
    assert sources.local_path("a.mp4", SHA, False) == Path("/app/inbox/a.mp4")


def test_uploaded_copy_is_hash_and_lowercase_extension() -> None:
    assert sources.local_path("Talk.MOV", SHA, True) == Path(f"/app/data/uploads/{SHA}.mov")


def test_uploaded_name_does_not_matter_only_extension() -> None:
    a = sources.local_path("발표 녹화.mp4", SHA, True)
    assert a == sources.local_path("other.mp4", SHA, True)


def test_last_dot_is_the_extension() -> None:
    assert sources.local_path("my.talk.mp4", SHA, True).suffix == ".mp4"

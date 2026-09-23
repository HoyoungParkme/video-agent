"""core/settings — VA-MS-005 SettingsService 9개의 테스트 관점."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.core.config import config
from app.core.errors import (
    Internal,
    KeyInvalid,
    KeyMissing,
    KeyRejected,
    LlmUnavailable,
    Validation,
)
from app.core.settings import SettingsService
from app.infra.openai import KeyCheck, KeyState, ReasonKind

KEY = "sk-abcdefghijklmnop1234"
NEW = "sk-newnewnewnewnewnew9876"
ENV = """# 복사해서 .env로 쓴다

# OpenAI API 키
OPENAI_API_KEY={key}
STT_MODEL=
TEXT_MODEL=

POSTGRES_PASSWORD=secret
"""


@pytest.fixture
def svc() -> SettingsService:
    return SettingsService()


def _write(path: Path, key: str = KEY) -> str:
    text = ENV.format(key=key)
    path.write_text(text)
    return text


# read_env


def test_read_env_missing_file(svc, env_file) -> None:
    assert svc.read_env() == {}


def test_read_env_rules(svc, env_file) -> None:
    env_file.write_text(
        '# OPENAI_API_KEY=sk-in-comment\nOPENAI_API_KEY="sk-abc"\nexport STT_MODEL=whisper-1\n'
        "TEXT_MODEL='gpt-5.4'\nTEXT_MODEL=gpt-5-mini\nPOSTGRES_PASSWORD=secret\n"
    )
    assert svc.read_env() == {
        "OPENAI_API_KEY": "sk-abc",
        "STT_MODEL": "whisper-1",
        "TEXT_MODEL": "gpt-5-mini",  # 같은 이름이면 뒤의 것
    }

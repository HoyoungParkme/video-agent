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


# write_env


def test_write_env_changes_only_that_line(svc, env_file) -> None:
    before = _write(env_file, "sk-" + "x" * 40)
    svc.write_env({"OPENAI_API_KEY": KEY})
    after = env_file.read_text()
    assert after == before.replace("sk-" + "x" * 40, KEY)  # 짧아져도 찌꺼기가 없다
    assert svc.read_env()["OPENAI_API_KEY"] == KEY


def test_write_env_appends_missing_line(svc, env_file) -> None:
    env_file.write_text("POSTGRES_USER=va")  # 끝에 줄바꿈이 없는 파일
    svc.write_env({"STT_MODEL": "whisper-1"})
    assert env_file.read_text() == "POSTGRES_USER=va\nSTT_MODEL=whisper-1\n"


def test_write_env_creates_file(svc, env_file) -> None:
    svc.write_env({"OPENAI_API_KEY": KEY})
    assert env_file.read_text() == f"OPENAI_API_KEY={KEY}\n"


def test_write_env_last_of_duplicates(svc, env_file) -> None:
    env_file.write_text("TEXT_MODEL=a\nexport TEXT_MODEL=b\n")
    svc.write_env({"TEXT_MODEL": "gpt-5.4"})
    assert env_file.read_text() == "TEXT_MODEL=a\nTEXT_MODEL=gpt-5.4\n"


def test_write_env_rejects_other_names(svc, env_file) -> None:
    with pytest.raises(ValueError):
        svc.write_env({"POSTGRES_PASSWORD": "x"})


@pytest.mark.skipif(os.geteuid() == 0, reason="root는 읽기 전용 파일도 쓴다")
def test_write_env_read_only(svc, env_file) -> None:
    _write(env_file)
    env_file.chmod(0o444)
    with pytest.raises(OSError):
        svc.write_env({"OPENAI_API_KEY": NEW})


# current_models · api_key


def test_current_models_defaults_and_prices(svc, env_file) -> None:
    _write(env_file)
    m = svc.current_models()
    assert (m.stt.id, m.text.id) == ("whisper-1", "gpt-5-mini")
    assert m.stt.price.per_min_usd == 0.006
    assert m.text.price.input_per_mtok_usd == 0.25
    env_file.write_text("STT_MODEL=whisper-9\nTEXT_MODEL=gpt-5.4\n")
    m = svc.current_models()
    assert (m.stt.id, m.text.id) == ("whisper-1", "gpt-5.4")  # 목록에 없으면 기본값
    assert m.text.price.output_per_mtok_usd == 15.00


def test_api_key(svc, env_file, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="app")
    _write(env_file)
    assert svc.api_key() == KEY
    _write(env_file, NEW)
    assert svc.api_key() == NEW  # 다시 띄우지 않아도 새 키
    _write(env_file, "")
    assert svc.api_key() is None
    assert KEY not in caplog.text and NEW not in caplog.text


# get


def test_get_masks_and_sends_nothing(svc, env_file, verify, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-environment-0000")
    _write(env_file)
    s = svc.get()
    assert s.key.masked == "sk-…1234"  # 환경 변수가 아니라 파일 것
    assert s.key.stored_in == ".env에 저장됨"
    assert s.models.model_dump() == {"stt": "whisper-1", "text": "gpt-5-mini"}
    assert s.model_options == config.MODEL_OPTIONS
    assert s.inbox_path == config.INBOX_DISPLAY_PATH
    assert verify.calls == []


def test_get_empty_key(svc, env_file) -> None:
    _write(env_file, "")
    k = svc.get().key
    assert (k.masked, k.stored_in, k.state) == (None, None, KeyState.missing)


def test_get_shows_last_failure(svc, env_file) -> None:
    _write(env_file)
    svc.last_check = KeyCheck(
        KeyState.invalid, ReasonKind.quota, "잔액이 없습니다", datetime.now(UTC)
    )
    k = svc.get().key
    assert (k.state, k.reason_kind, k.reason) == (
        KeyState.invalid,
        ReasonKind.quota,
        "잔액이 없습니다",
    )


# check_stored_key


async def test_check_without_key(svc, env_file, verify) -> None:
    assert (await svc.check_stored_key()).state == KeyState.missing
    assert verify.calls == []


async def test_check_ok_and_time_moves(svc, env_file, verify) -> None:
    _write(env_file)
    first = await svc.check_stored_key()
    second = await svc.check_stored_key()
    assert first.state == second.state == KeyState.ok
    assert second.checked_at > first.checked_at


async def test_check_folds_exceptions(svc, env_file, verify) -> None:
    _write(env_file)
    verify.error = RuntimeError("뜻밖의 오류")
    k = await svc.check_stored_key()
    assert (k.state, k.reason_kind) == (KeyState.invalid, ReasonKind.network)


async def test_check_reads_hand_edited_file(svc, env_file, verify) -> None:
    _write(env_file)
    await svc.check_stored_key()
    _write(env_file, NEW)
    await svc.check_stored_key()
    assert verify.calls == [KEY, NEW]

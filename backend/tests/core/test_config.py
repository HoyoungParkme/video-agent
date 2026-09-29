"""core/config — 설정값끼리 어긋나지 않는지."""

from __future__ import annotations

from app.core.config import config


def test_default_models_are_options() -> None:
    assert config.DEFAULT_MODELS["stt"] in {o.id for o in config.MODEL_OPTIONS.stt}
    assert config.DEFAULT_MODELS["text"] in {o.id for o in config.MODEL_OPTIONS.text}

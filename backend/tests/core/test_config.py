"""core/config — 설정값끼리 어긋나지 않는지."""

from __future__ import annotations

from app.core.config import config


def test_default_models_are_options() -> None:
    assert config.DEFAULT_MODELS["stt"] in {o.id for o in config.MODEL_OPTIONS.stt}
    assert config.DEFAULT_MODELS["text"] in {o.id for o in config.MODEL_OPTIONS.text}


def test_text_options_follow_spec_in_price_order() -> None:
    # VA-MS-005 0장 표 그대로 — 값 오름차순(UI-5 3.3). 새 모델을 더할 때 자리 · 단가 오타를 막는다
    got = [
        (o.id, o.price.input_per_mtok_usd, o.price.output_per_mtok_usd)
        for o in config.MODEL_OPTIONS.text
    ]
    assert got == [
        ("gpt-5.6-luna", 0.20, 1.20),
        ("gpt-5-mini", 0.25, 2.00),
        ("gpt-5.4-mini", 0.75, 4.50),
        ("gpt-5.6-terra", 2.00, 12.00),
        ("gpt-5.4", 2.50, 15.00),
        ("gpt-5.6-sol", 4.00, 20.00),
    ]
    prices = [(i, o) for _, i, o in got]
    assert prices == sorted(prices)

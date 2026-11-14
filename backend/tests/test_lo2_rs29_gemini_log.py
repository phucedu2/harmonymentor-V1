"""RS-29: Gemini lỗi thì log ghi lý do (mã, loại lỗi) nhưng không bao giờ ghi khóa."""

from __future__ import annotations

import logging

import pytest

from app.ai.tutor.llm import GeminiProvider, LLMUnavailable


class _Err(Exception):
    code = 503


class _Client:
    class models:  # noqa: N801 - giả lập đúng hình dạng SDK
        @staticmethod
        def generate_content(**_):
            raise _Err("503 UNAVAILABLE overloaded url=...?key=AIzaSyFAKEFAKEFAKEFAKE1234 token AQ.Ab8FAKEFAKEFAKEFAKE")


def test_log_co_ly_do_khong_co_khoa(caplog):
    p = GeminiProvider(api_key="x", model="m1", fallback_model="m2", client=_Client(), sleep=lambda _: None)
    with caplog.at_level(logging.WARNING, logger="harmonymentor.llm"), pytest.raises(LLMUnavailable) as e:
        p.generate("s", "u", {})
    assert e.value.reason == "unavailable"
    text = caplog.text
    assert "status=503" in text and "_Err" in text and "model=m1" in text and "model=m2" in text
    assert "AIza" not in text and "AQ.Ab8" not in text and "key=" not in text


"""Fixture chung cho mọi test backend."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _tat_goi_bu_cau_hoi(request, monkeypatch):
    """9A (23/11): bản nháp dưới 10 câu thì AI soạn bài gọi bù 1 lần. Các test cũ dựng FakeProvider theo kịch bản
    "mỗi bản nháp đúng 1 lượt gọi" nên lượt gọi bù sẽ lệch kịch bản. Tắt mặc định; test về gọi bù gắn @pytest.mark.top_up."""
    if request.node.get_closest_marker("top_up") is None:
        from app.admin import ai_service
        monkeypatch.setattr(ai_service, "MIN_QUESTIONS", 0)


@pytest.fixture(autouse=True)
def _hop_thu_va_gioi_han_sach():
    """ADR-040: mỗi test có hộp thư ConsoleSender riêng và bộ đếm giới hạn tần suất sạch
    (nhiều test cùng đăng ký từ IP "testclient", chung bộ đếm sẽ chạm trần 10 lần/giờ)."""
    from app.auth.rate_limit import rate_limits
    from app.email.sender import ConsoleSender, set_sender

    rate_limits.clear()
    sender = ConsoleSender()
    set_sender(sender)
    yield sender
    set_sender(None)

"""Định tuyến an toàn: khái niệm chưa bài nào dạy không được trả lời như bài đã dạy (lỗi nặng gấp đôi).

Luật tất định, chạy không cần mô hình nhúng."""

import pytest

from app.ai.tutor import router


@pytest.mark.parametrize("q", [
    "quãng 9 là gì", "quang 9 la gi", "quãng kép là gì", "đảo hợp âm C lần 1", "dao hop am la gi",
    "vòng quãng 5 là gì", "circle of fifths", "C/E là thế đảo nào",
])
def test_khai_niem_chua_day_bi_chan(q):
    assert router.untaught_concept(q) is not None


@pytest.mark.parametrize("q", [
    "quãng 3 trưởng là gì", "Cmaj7 gồm những nốt nào", "hợp âm Dm7 là gì", "giọng Sol trưởng có mấy dấu thăng",
])
def test_khai_niem_da_day_khong_bi_chan(q):
    assert router.untaught_concept(q) is None


def test_luat_tu_tat_khi_kho_bai_nhac_toi_khai_niem(monkeypatch):
    """Khi một bài mới vào kho và nhắc tới thế đảo, luật không còn chặn (không phải sửa tay)."""
    class _C:
        text = "Thế đảo của hợp âm là cách đổi nốt trầm."
    monkeypatch.setattr(router, "knowledge_base", lambda: [_C()])
    assert router.untaught_concept("đảo hợp âm C lần 1") is None


def test_later_lesson_khop_ca_khong_dau():
    assert router.later_lesson("muon hop am la gi") == "L06"
    assert router.later_lesson("mượn hợp âm là gì") == "L06"
    assert router.later_lesson("Cmaj9 co tension nao") == "L07"

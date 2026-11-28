"""RS-26: câu AI gọi sai tên quãng không còn được gắn "Engine xác nhận".

Ca thật khi đo AI bật 12/11/2026 (câu 18 "tại sao G7 muốn về C"): AI viết B–F là "quãng ba giảm"; đúng là quãng 5
giảm (d5, tritone). Trước đây bộ quét chỉ nhận chữ số và "là", nên khẳng định này lọt qua và câu trả lời vẫn được
gắn dấu kiểm. Engine vẫn là nguồn sự thật; ở đây chỉ nhận diện thêm cách viết của AI.
"""

import pytest

from app.ai.tutor.guardrail import scan_reply


def intervals(text):
    return [c for c in scan_reply(text) if c.tool == "identify_interval"]


@pytest.mark.parametrize("text,claimed,status", [
    ("Nốt B và F tạo quãng ba giảm, nên rất căng.", "d3", "contradicted"),
    ("Nốt B và F tạo quãng 5 giảm.", "d5", "verified"),
    ("F và B tạo thành quãng 4 tăng.", "A4", "verified"),
    ("B–F tạo quãng năm giảm.", "d5", "verified"),
    ("B–F là quãng ba giảm.", "d3", "contradicted"),
    ("C và E là quãng ba trưởng.", "M3", "verified"),
    ("C và E là quãng ba thứ.", "m3", "contradicted"),
])
def test_ten_quang_bang_chu_va_cau_noi_bang_va(text, claimed, status):
    (c,) = intervals(text)
    assert (c.claimed, c.status) == (claimed, status)


def test_phu_dinh_va_cau_khong_khang_dinh_khong_bi_bat():
    assert not intervals("B và F không phải quãng ba giảm.")
    assert not intervals("B và F nghe căng vì có hai nốt khó.")


def test_rs30_prompt_luong_b_cam_khang_dinh_hop_am_bai_hat_cu_the():
    from app.ai.tutor import prompt
    system = prompt.SYSTEM_GENERAL
    assert "chưa kiểm chứng được hợp âm của bài này" in system

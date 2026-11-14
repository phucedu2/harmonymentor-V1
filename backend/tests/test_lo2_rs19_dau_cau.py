"""RS-19: dấu câu cuối câu không làm hỏng việc đọc tên nốt."""

import pytest

from app.services.grading_service import grade_payload


@pytest.mark.parametrize("answer", ["Son Si Rê.", "Sol, Si, Rê!", "G B D?", "G: B: D…", "G B D."])
def test_dau_cau_cuoi_khong_lam_hong_ten_not(answer):
    out = grade_payload("music_engine", {}, {"kind": "build_chord", "symbol": "G"}, answer)
    assert out.correct is True


def test_van_cham_sai_khi_sai_not():
    out = grade_payload("music_engine", {}, {"kind": "build_chord", "symbol": "G"}, "Son Si Mi!")
    assert out.correct is False

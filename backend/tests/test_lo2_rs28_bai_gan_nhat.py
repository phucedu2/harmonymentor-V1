"""RS-28: điểm khớp dưới vùng xám thì không gợi ý "bài gần nhất" (tránh "hợp âm là gì" → bài hợp âm mượn).
Chạy BM25 như CI (không có embedder)."""

from app.ai.tutor.router import _th, decide


def test_diem_thap_khong_goi_y_bai_lac_de():
    d = decide("hợp âm là gì", None)
    assert d.lesson.best_score < _th(None)["lesson_gray"]
    assert d.nearest_lesson is None


def test_diem_du_thi_van_goi_y_bai():
    d = decide("át phụ là gì", None)
    assert d.nearest_lesson == "L05"

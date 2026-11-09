"""Định tuyến an toàn (09/11/2026): câu kho chưa dạy không được trả lời như bài học (luồng A).

Bốn câu hỏng trên phiếu dev 30 của Phúc. Chạy BM25 như CI."""

from __future__ import annotations

import pytest

from app.ai.tutor import router


@pytest.mark.parametrize("question, flow, reason", [
    ("dao hop am C lan 1 la sao", "B", "untaught_concept"),          # đảo hợp âm: không bài nào dạy
    ("quang 9 la gi", "B", "untaught_concept"),                       # quãng kép: kho chỉ tới quãng 8
    ("Fm trong C truong muon tu dau ra vay", "B", "later_lesson"),   # mượn hợp âm, gõ không dấu → L06
    ("cho minh link tai nhac lau free", "C", "unknown_terms_not_music"),
    ("Nhịp 6/8 đếm thế nào?", "B", "untaught_concept"),             # tập dev router_dev
    ("fmaj9 là hợp âm gì, gồm nốt nào", "B", "later_lesson"),        # hợp âm 9 → L07
    ("Gợi ý phim hay cuối tuần", "C", "weak_music_oos"),
    ("Hòa âm bốn bè cấm quãng năm song song vì sao?", "B", "untaught_concept"),
])
def test_cau_kho_chua_day_khong_vao_luong_A(question, flow, reason):
    d = router.decide(question, None)
    assert (d.flow, d.reason) == (flow, reason)


def test_muon_khong_nham_voi_muon_hoc():
    # "muốn" bỏ dấu cũng là "muon": không được đẩy câu A sang L06.
    assert router.later_lesson("minh muon hoc hop am ba") is None
    assert router.later_lesson("Fm muon tu giong thu") == "L06"


def test_luat_moi_tu_tat_khi_kho_co_doan(monkeypatch):
    from types import SimpleNamespace

    assert router.untaught_concept("hop am sus la gi") == "sus_chord"
    monkeypatch.setattr(router, "knowledge_base", lambda: [SimpleNamespace(text="Hợp âm sus4 thay nốt 3 bằng nốt 4.")])
    assert router.untaught_concept("hop am sus la gi") is None

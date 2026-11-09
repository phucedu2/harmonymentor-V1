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


def test_engine_hieu_chat_luong_bang_chu():
    # Phiếu dev Phúc P06: trước đây "B diminished" bị hiểu thành B trưởng (B D# F#).
    from app.ai.tutor.engine_query import engine_answer

    def tones(q):
        return [(f["args"]["symbol"], f["result"]) for f in engine_answer(q).facts if f["tool"] == "get_chord_tones"]

    assert tones("hợp âm B diminished bấm như thế nào") == [("Bdim", "B D F")]
    assert tones("hop am tang cua C la gi") == [("Caug", "C E G#")]
    assert tones("hợp âm A thứ gồm nốt gì") == [("Am", "A C E")]


@pytest.mark.parametrize("question", ["triad la gi", "perfetc la gi trong bai 1", "tonic va dominant la gi"])
def test_cau_dinh_nghia_ngan_kho_co_day_la_A(question):
    assert router.decide(question, None).flow == "A"


@pytest.mark.parametrize("question", ["hoa tri cua sat la may", "giong mi thu co may dau thang"])
def test_cau_toan_chu_thuong_khong_bi_keo_vao_A(question):
    assert router.decide(question, None).flow != "A"


def test_go_sai_truong_khong_bi_coi_la_am_giai_la():
    assert router._scale_typo("âm giai trởưng") and router._scale_typo("âm giai tưởng")
    assert not router._scale_typo("âm giai blues") and not router._scale_typo("âm giai lydian")


def test_muon_khong_nham_voi_muon_hoc():
    # "muốn" bỏ dấu cũng là "muon": không được đẩy câu A sang L06.
    assert router.later_lesson("minh muon hoc hop am ba") is None
    assert router.later_lesson("Fm muon tu giong thu") == "L06"


def test_luat_moi_tu_tat_khi_kho_co_doan(monkeypatch):
    from types import SimpleNamespace

    assert router.untaught_concept("hop am sus la gi") == "sus_chord"
    monkeypatch.setattr(router, "knowledge_base", lambda: [SimpleNamespace(text="Hợp âm sus4 thay nốt 3 bằng nốt 4.")])
    assert router.untaught_concept("hop am sus la gi") is None

"""RS-03: câu đã phát hành phải có lời giải, nếu không người học sai hai lần vẫn không biết vì sao (bị kẹt)."""

from app.content.curriculum_specs import LESSON_SPECS


def test_moi_cau_da_phat_hanh_co_loi_giai():
    thieu = [it["id"] for lesson in LESSON_SPECS for it in lesson["exercises"]
             if it["status"] == "published" and not it["retired"] and not (it["explanation"] or "").strip()]
    assert thieu == []


def test_loi_giai_moi_them_tang_version():
    # Lời giải nằm trong ảnh chụp phiên bản (ADR-006): câu L05–L08 vừa thêm lời giải phải là bản 2 trở lên.
    cac_cau = {it["id"]: it for lesson in LESSON_SPECS for it in lesson["exercises"]}
    for qid in ("L05-Q01", "L06-Q03", "L07-Q03", "L08-Q05"):
        assert (cac_cau[qid]["version"] or 1) >= 2, qid

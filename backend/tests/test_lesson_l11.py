"""Điểm lệch 1 (Lai): bài L11 "Vòng hợp âm Pop" và các câu bổ sung để mỗi kỹ năng L01–L04 có ít nhất 3 câu.

Mọi đáp án được dựng lại bằng Music Engine, không tin chữ trong file nội dung (nguyên tắc bất biến 1).
"""

from __future__ import annotations

from collections import Counter

import pytest

from app.content.curriculum_specs import LESSON_SPECS, lesson_by_id
from app.music_engine import chord_tones, diatonic_chords, interval_between
from app.services.grading_service import grade_payload

NEW_L01_L04 = ["L01-Q09", "L01-Q10", "L01-Q11", "L01-Q12", "L02-Q11", "L02-Q12", "L03-Q07", "L03-Q08", "L03-Q09",
               "L03-Q10", "L03-Q11", "L03-Q12", "L04-Q07", "L04-Q08", "L04-Q09"]


def exercise(item_id):
    return next(e for lesson in LESSON_SPECS for e in lesson["exercises"] if e["id"] == item_id)


def numeral_chords(key: str, numerals: list[str]) -> str:
    """Hợp âm ba của các bậc (số La Mã) trong giọng trưởng, nối bằng dấu -, tính bằng Engine."""
    by_degree = {r.degree: r.chord for r in diatonic_chords(key, sevenths=False)}
    order = {"I": 1, "ii": 2, "iii": 3, "IV": 4, "V": 5, "vi": 6}
    out = []
    for n in numerals:
        chord = by_degree[order[n]]
        out.append(chord.root.name + ("m" if n.islower() else ""))
    return "-".join(out)


def test_moi_ky_nang_l01_den_l04_co_it_nhat_3_cau_da_phat_hanh():
    count = Counter()
    for lesson in LESSON_SPECS:
        if lesson["id"] not in {"L01", "L02", "L03", "L04"}:
            continue
        for e in lesson["exercises"]:
            if e["status"] == "published" and not e["retired"]:
                count[e["skill"]] += 1
    assert count and min(count.values()) >= 3, dict(count)


@pytest.mark.parametrize("item_id", NEW_L01_L04 + [f"L11-Q0{i}" for i in range(1, 7)])
def test_cau_moi_dap_an_dung_duoc_cham_dung_va_phuong_an_sai_bi_cham_sai(item_id):
    e = exercise(item_id)
    expected = e["answer_key"].get("expected")
    if e["strategy"] == "rubric":
        expected = e["answer_key"]["accepted"][0]
    ok = grade_payload(e["strategy"], e["answer_key"], e["grader_config"], expected)
    assert ok.correct, (item_id, ok.feedback)
    for option in e["options"] or []:
        out = grade_payload(e["strategy"], e["answer_key"], e["grader_config"], option)
        assert out.correct == (option == expected), (item_id, option)
    assert e["explanation"], item_id


def test_cau_hoi_quang_dung_theo_engine():
    for item_id, low, high in (("L01-Q09", "C", "G"), ("L01-Q10", "E", "G")):
        interval = interval_between(low, high)
        want = exercise(item_id)["answer_key"]["expected"]
        assert str(interval) == want or interval.name == want, (item_id, interval)


def test_chuc_nang_va_ii_v_i_theo_engine():
    # Bậc ii–V–I của G major: Am7, D7, Gmaj7.
    names = [r.chord.root.name + r.chord.type.display for r in diatonic_chords("G", sevenths=True)]
    assert exercise("L04-Q07")["answer_key"]["expected"] == "-".join([names[1], names[4], names[0]])
    assert exercise("L03-Q12")["answer_key"]["expected"] == names[4]  # D7 là bậc V của G major
    assert exercise("L03-Q07")["answer_key"]["expected"] == names[0]
    f_names = [r.chord.root.name + r.chord.type.display for r in diatonic_chords("F", sevenths=True)]
    assert f_names[4] == "C7"  # L03-Q11: C7 là bậc V của F major
    # Guide tone của Dm7 và G7: quãng 3 và quãng 7, F giữ nguyên, C hạ nửa cung xuống B.
    dm7 = [n.name for n in chord_tones("Dm7")]
    g7 = [n.name for n in chord_tones("G7")]
    assert (dm7[1], dm7[3]) == ("F", "C") and (g7[1], g7[3]) == ("B", "F")


def test_l11_vong_hop_am_dung_theo_engine():
    assert exercise("L11-Q01")["answer_key"]["expected"] == numeral_chords("C", ["I", "V", "vi", "IV"])
    assert exercise("L11-Q02")["answer_key"]["expected"] == numeral_chords("C", ["vi", "IV", "I", "V"])
    assert exercise("L11-Q03")["answer_key"]["expected"] == numeral_chords("G", ["I", "V", "vi", "IV"])
    assert exercise("L11-Q04")["answer_key"]["expected"] == numeral_chords("C", ["I", "vi", "IV", "V"])
    assert [n.name for n in chord_tones("Em")] == exercise("L11-Q05")["answer_key"]["expected"]
    for card in lesson_by_id("L11")["review_items"][:4]:
        assert card["answer_key"]["expected"] == card["back"].replace(" – ", "-")


def test_l11_khong_ghi_hop_am_bai_hat_cu_the():
    text = repr(lesson_by_id("L11")).lower()
    for banned in ("let it be", "someone like you", "despacito", "no woman", "hey jude"):
        assert banned not in text


def test_l11_mo_ra_voi_thu_tu_bang_7_va_khong_con_la_ban_nhap():
    from app.content.draft_specs import DRAFT_LESSON_SPECS
    assert "L11" not in {d["id"] for d in DRAFT_LESSON_SPECS}
    spec = lesson_by_id("L11")
    assert spec["track"] == "M3. Pop" and 6 <= len([b for b in spec["blocks"]]) <= 12
    lab = next(b for b in spec["blocks"] if b[1] == "compose_link")
    assert lab[2]["lab_key"] == "C" and lab[2]["lab_numerals"] == ["I", "V", "vi", "IV"]

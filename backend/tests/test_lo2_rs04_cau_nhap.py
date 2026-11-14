"""RS-04 (14/11): 10 câu nháp để mỗi kỹ năng có ít nhất 3 câu. Mọi khẳng định nhạc lý trong đáp án và lời giải
được Music Engine kiểm lại (nguyên tắc 1); câu là bản nháp cho tới khi Đạt duyệt (nguyên tắc 17)."""

from __future__ import annotations

from collections import defaultdict

import pytest

from app.content.curriculum_specs import LESSON_SPECS
from app.music_engine.tools import get_chord_tones, get_scale
from app.services.grading_service import grade_payload

NEW = {"L05-Q07", "L05-Q08", "L05-Q09", "L06-Q07", "L06-Q08", "L06-Q09", "L06-Q10", "L07-Q07", "L07-Q08", "L07-Q09"}
ITEMS = {e["id"]: e for lesson in LESSON_SPECS for e in lesson["exercises"]}


def tones(symbol):
    return get_chord_tones(symbol=symbol)["notes"]


def scale(tonic, kind):
    return get_scale(tonic=tonic, scale_type=kind)["notes"]


@pytest.mark.parametrize("qid", sorted(NEW))
def test_cau_moi_la_nhap_co_nguon_va_dap_an_nam_trong_lua_chon(qid):
    e = ITEMS[qid]
    assert e["status"] == "draft" and e["provenance"] and e["explanation"]
    assert e["answer_key"]["expected"] in e["options"]
    assert grade_payload(e["strategy"], e["answer_key"], e["grader_config"], e["answer_key"]["expected"]).correct


def test_khang_dinh_nhac_ly_trong_loi_giai_khop_engine():
    assert tones("A7") == ["A", "C#", "E", "G"]           # L05-Q07
    assert tones("D7") == ["D", "F#", "A", "C"]           # L05-Q08, L05-Q09
    assert tones("Fm") == ["F", "Ab", "C"]                # L06-Q09
    assert tones("Ab") == ["Ab", "C", "Eb"]               # L06-Q10
    assert tones("Cmaj9") == ["C", "E", "G", "B", "D"]    # L07-Q07
    assert set(scale("C", "natural_minor")) - set(scale("C", "major")) == {"Eb", "Ab", "Bb"}   # L06-Q08
    assert scale("G", "mixolydian") == ["G", "A", "B", "C", "D", "E", "F"]                      # L07-Q09
    assert scale("C", "natural_minor")[5] == "Ab"         # L06-Q10: bậc 6 của C minor
    assert "C#" in tones("A") and "C#" in tones("A7")     # L06-Q10: A, A7 không thuộc C minor


def test_moi_ky_nang_co_it_nhat_3_cau_tinh_ca_ban_nhap():
    count = defaultdict(int)
    for lesson in LESSON_SPECS:
        for e in lesson["exercises"]:
            if not e["retired"]:
                count[e["skill"]] += 1
    assert {k: v for k, v in count.items() if v < 3} == {}


# --- RS-11: khối nháp "Nghe trong vòng hợp âm quen" -----------------------------------------------------------

def test_rs11_moi_bai_co_mot_khoi_nghe_nhap_hop_am_hop_le():
    from app.content.draft_specs import SONG_BLOCKS, blocks_with_drafts

    for lesson in LESSON_SPECS:
        if lesson["id"] not in SONG_BLOCKS:
            continue
        blocks = {b[0]: b for b in blocks_with_drafts(lesson)}
        _, kind, payload = blocks[f"{lesson['id']}-BNGHE"]
        assert kind == "audio" and payload["status"] == "draft" and payload["note"]
        for symbol in payload["progression"]:
            assert get_chord_tones(symbol=symbol)["ok"], symbol
    assert set(SONG_BLOCKS) == {"L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08"}


def test_rs11_khoi_nhap_khong_vao_kho_ai_tutor():
    from app.ai.tutor.chunker import lesson_chunks

    assert not any(c.block_id.endswith("-BNGHE") for c in lesson_chunks())

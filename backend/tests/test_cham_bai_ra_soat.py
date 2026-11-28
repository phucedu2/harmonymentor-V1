"""RS-01, RS-02: chấm câu gõ ký hiệu hợp âm/số La Mã/danh sách nốt theo nội dung, không theo chuỗi gõ.

Các ca lấy từ báo cáo rà soát 11/11/2026 (ket-qua-cham-bai.txt): trước khi sửa, 44/105 ca lệch kỳ vọng.
Chỉ đổi bộ chấm nên không phiên bản câu hỏi nào đổi (ADR-006).
"""

import pytest

from app.content.curriculum_specs import LESSON_SPECS
from app.services.grading_service import grade_payload

SPECS = {item["id"]: item for lesson in LESSON_SPECS for item in lesson["exercises"]}


def _grade(qid: str, answer: str, method: str = "text") -> bool:
    item = SPECS[qid]
    return grade_payload(item["strategy"], item["answer_key"], item["grader_config"], answer, method).correct


# (câu, đáp án gõ, kỳ vọng đúng?)
CASES = [
    # RS-01: chữ hoa/thường mang nghĩa nhạc lý thì không được bỏ qua
    ("L04-Q02", "GM7-C7-FMAJ7", False),      # GM7 = G trưởng bảy, không phải Gm7
    ("L04-Q01", "DM7-G7-CMAJ7", False),      # DM7 khác Dm7
    ("L05-Q04", "V7/II", False),             # II hoa = trưởng
    ("L05-Q04", "v7/ii", False),             # v thường = thứ
    ("L06-Q04", "FM", False),                # FM = F trưởng
    ("L06-Q04", "F", False),
    # RS-02: cách viết đúng khác chuỗi mẫu
    ("L04-Q02", "Gm7 C7 Fmaj7", True),
    ("L04-Q02", "gm7-c7-fmaj7", True),
    ("L04-Q02", "Gm7 → C7 → Fmaj7", True),
    ("L04-Q02", "Gm7 C7 FM7", True),
    ("L04-Q02", "Gm7 C7 F△7", True),
    ("L04-Q02", "Gmin7 C7 Fmaj7", True),
    ("L04-Q02", "Gm C F", False),
    ("L05-Q03", "E7", True),
    ("L05-Q03", "e7", True),
    ("L05-Q03", "E 7", True),
    ("L05-Q03", "Mi 7", True),
    ("L05-Q03", "E7 (E-G#-B-D)", True),
    ("L05-Q03", "Em7", False),
    ("L05-Q03", "E", False),
    ("L05-Q04", "V7/ii", True),
    ("L05-Q04", "V7 / ii", True),
    ("L05-Q04", "V/ii", True),
    ("L05-Q04", "V7 của ii", True),
    ("L06-Q03", "Ab", True),
    ("L06-Q03", "A♭", True),
    ("L06-Q03", "ab", True),
    ("L06-Q03", "La giáng", True),
    ("L06-Q03", "G#", False),                # đồng âm nhưng sai tên
    ("L06-Q04", "Fm", True),
    ("L06-Q04", "F thứ", True),
    ("L06-Q04", "Fmin", True),
    ("L06-Q04", "F minor", True),
    ("L08-Q03", "G B F", True),
    ("L08-Q03", "G, B, F", True),
    ("L08-Q03", "Sol Si Fa", True),
    ("L08-Q03", "G F B", True),
    ("L08-Q03", "G – B – F", True),
    ("L08-Q03", "G B D F", False),
    ("L04-Q04", "Si và Fa", True),
    ("L04-Q04", "B với F", True),
    ("L04-Q04", "B, F.", True),
    ("L04-Q04", "B", False),
    ("L03-Q04", "T - S - D - T", True),
    ("L03-Q04", "Chủ - Hạ át - Át - Chủ", True),
    ("L03-Q04", "T PD D T", True),
    ("L03-Q04", "T D PD T", False),
    ("L01-Q03", "1 3b 5", True),
    ("L01-Q03", "1-3-5", False),
    ("L01-Q05", "Có, cùng một phím thì luôn có cùng một tên", False),
    # câu dựng nốt bằng Engine: dấu tách khác và viết liền không còn văng lỗi
    ("L01-Q02", "GBD", True),
    ("L01-Q02", "G/B/D", True),
    ("L01-Q02", "G+B+D", True),
    ("L01-Q02", "G. B. D", True),
    ("L01-Q02", "Sol, Si, Rê.", True),
    ("L01-Q02", "G Cb D", False),
    # số La Mã chấm bằng Engine: iim7 là cách jazz viết ii7
    ("L02-Q03", "iim7", True),
    ("L02-Q03", "ii 7", False),             # nhóm chốt 10/11: viết liền, "V 7" cũng sai
    ("L02-Q03", "II7", False),
    ("L02-Q10", "vim7", True),
    ("L02-Q10", "VI7", False),
]


@pytest.mark.parametrize("qid,answer,expected", CASES, ids=[f"{q}:{a}" for q, a, _ in CASES])
def test_cham_theo_noi_dung(qid, answer, expected):
    assert _grade(qid, answer) is expected


def test_mcq_giu_nguyen_phan_biet_hoa_thuong_cua_ky_hieu():
    # Đáp án trắc nghiệm là đúng chuỗi lựa chọn; "D7" không thành "d7" của giọng khác nghĩa.
    assert _grade("L02-Q07", "D7") is True
    assert _grade("L02-Q07", "Dm7") is False
    assert _grade("L02-Q07", "Dmaj7") is False


@pytest.mark.parametrize("typed,ok", [("Imaj7", True), ("IMaj7", True), ("IMAJ7", True), ("I△7", True), ("Imaj 7", False), ("Im7", False)])
def test_rs21_imaj7_viet_hoa_thuong(typed, ok):
    from app.services.grading_service import grade_payload
    out = grade_payload("music_engine", {}, {"kind": "roman_numeral", "key": "C", "chord": "Cmaj7"}, typed)
    assert out.correct is ok

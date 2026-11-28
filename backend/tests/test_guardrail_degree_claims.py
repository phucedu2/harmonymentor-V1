"""Engine kiểm câu khẳng định bậc hợp âm trong giọng, dù model nào viết (lỗi Gm7 ngày 28/11)."""

import pytest

from app.ai.tutor.guardrail import check_answer, scan_reply


def _status(reply: str) -> list[tuple[str, str]]:
    return [(c.claimed, c.status) for c in scan_reply(reply)]


def test_gm7_wrong_degree_reply_is_contradicted():
    # Câu trả lời thật của model ngày 28/11: trước bản sửa, quét ra rỗng nên lọt qua.
    reply = ("Gm7 là hợp âm thứ ba trong giọng G major, ký hiệu là ii7. "
             "Trong giọng G major, ii7 là Am7, không phải Gm7.")
    claims = scan_reply(reply)
    assert ("bậc 3", "contradicted") in [(c.claimed, c.status) for c in claims]
    assert ("ii7", "verified") in [(c.claimed, c.status) for c in claims]   # vế "ii7 là Am7" đúng
    assert check_answer(reply, []).contradicted                             # vòng soạn lại sẽ bị kích hoạt


@pytest.mark.parametrize("reply", [
    "Gm7 là hợp âm bậc 2 trong giọng F trưởng.",
    "Gm7 là hợp âm thứ ba trong giọng Eb major.",
    "Gm7 là hợp âm bậc sáu của Bb trưởng.",
    "G7 là hợp âm bậc V của giọng C.",
    "Bm7 là bậc ba (iii7) trong giọng G major.",
])
def test_correct_degree_claims_verified(reply):
    assert [s for _, s in _status(reply)] == ["verified"]


def test_wrong_degree_for_diatonic_chord():
    assert _status("Am7 là hợp âm bậc 3 trong giọng G major.") == [("bậc 3", "contradicted")]


def test_borrowed_chord_on_right_root_is_unsupported_not_contradicted():
    # Fm trong C trưởng là hợp âm mượn trên bậc 4: không được gắn "sai", cũng không được "đã kiểm".
    assert _status("Fm là hợp âm bậc 4 trong giọng C trưởng.") == [("bậc 4", "unsupported")]


def test_minor_key_degree():
    assert _status("Bb là hợp âm bậc 3 trong giọng G thứ tự nhiên.") == [("bậc 3", "verified")]
    # "thứ" không rõ loại: Engine không đoán.
    assert _status("Bb là hợp âm bậc 3 trong giọng G thứ.") == [("bậc 3", "unsupported")]


def test_key_roman_is_chord_order():
    assert _status("Trong giọng G major, ii7 là Am7.") == [("ii7", "verified")]
    assert _status("Trong giọng G major, ii7 là Gm7.")[0][1] == "contradicted"


@pytest.mark.parametrize("reply", [
    "Gm7 là hợp âm thứ trong giọng F.",            # "thứ" = minor, không có số bậc
    "Gm7 là hợp âm thứ bảy trong giọng F.",        # dễ lẫn với "hợp âm bảy thứ": bỏ qua
    "Gm7 là hợp âm thứ ba.",                        # không có giọng thì không kiểm được
    "Gm7 gồm G, Bb, D, F là hợp âm bậc 2 trong F",  # chữ F cuối dãy nốt không phải hợp âm F
])
def test_no_degree_claim_extracted(reply):
    assert not [c for c in scan_reply(reply) if c.claimed.startswith("bậc")]

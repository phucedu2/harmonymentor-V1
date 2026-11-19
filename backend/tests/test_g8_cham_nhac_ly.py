"""G8: bộ 300 câu chấm nhạc lý — đáp án khớp Music Engine, bộ chấm tự động bắt đúng lỗi, script hỏi chạy được (AI giả)."""

from __future__ import annotations

import json

from app.eval.theory import build, grade, probe
from app.music_engine import tools as T


def test_bo_cau_hoi_300_cau_khop_tep_va_khong_trung():
    qs = probe.load(build.OUT)
    assert len(qs) == 300 == len(build.rows)
    assert [q["q"] for q in qs] == [r["q"] for r in build.rows]          # tệp đã sinh lại sau khi sửa build.py
    assert len({q["id"] for q in qs}) == 300 and len({q["q"] for q in qs}) == 300
    assert {q["group"] for q in qs} == {"bai", "ngoai"}


def test_dap_an_hop_am_lay_tu_engine():
    for q in probe.load(build.OUT):
        if q["topic"] == "thanh_phan_hop_am":
            assert q["subject"] in q["q"]
            assert T.get_chord_tones(symbol=q["subject"])["notes"] == q["expect"]["notes_all"], q["id"]


def _q(**expect):
    return {"id": "X", "expect": expect}


def test_guardrail_hieu_chu_va_trong_day_not():
    """Lỗi tìm thấy ở G8: "Eb, Gb, Bbb và Db" từng bị đọc thành 3 nốt nên Engine báo sai nhầm."""
    from app.ai.tutor.guardrail import scan_reply

    assert [c.status for c in scan_reply("Hợp âm Ebm7b5 gồm Eb, Gb, Bbb và Db.")] == ["verified"]
    assert [c.status for c in scan_reply("G7 = G, B, D, and F")] == ["verified"]
    assert [c.status for c in scan_reply("Cmaj7 gồm C, E, G và Bb.")] == ["contradicted"]


def test_bo_cham_bat_loi():
    ok = {"reply": "Hợp âm Ebm7b5 gồm Eb, Gb, Bbb và Db.", "status": "ok"}
    assert grade.auto_check(_q(notes_all=["Eb", "Gb", "Bbb", "Db"]), ok)["auto"] == "dat"
    wrong = {"reply": "Ebm7b5 gồm Eb Gb A Db.", "status": "ok"}       # A thay vì Bbb: Engine bác + thiếu nốt
    r = grade.auto_check(_q(notes_all=["Eb", "Gb", "Bbb", "Db"]), wrong)
    assert r["auto"] == "can_xem" and r["engine_contradicted"] >= 1
    assert grade.auto_check(_q(any=[["4 tăng", "A4"]]), {"reply": "Đó là quãng A4.", "status": "ok"})["auto"] == "dat"
    assert grade.auto_check(_q(roman_any=["vi"]), {"reply": "Vì Em là iii.", "status": "ok"})["auto"] == "can_xem"
    assert grade.auto_check(_q(), {"error": "boom"})["auto"] == "loi"


def test_probe_va_grade_chay_voi_ai_gia(tmp_path, monkeypatch):
    from app.ai.tutor import llm
    from app.eval.run import ScriptedProvider

    monkeypatch.setattr(llm, "get_provider", lambda cfg: ScriptedProvider())
    out = tmp_path / "answers.jsonl"
    assert probe.main(["--only", "T001,T013", "--pause", "0", "--out", str(out)]) == 0
    rows = probe.load(out)
    assert {r["id"] for r in rows} == {"T001", "T013"} and all("reply" in r for r in rows)
    assert probe.main(["--only", "T001,T013", "--pause", "0", "--out", str(out)]) == 0    # chạy lại: bỏ qua câu đã có
    assert len(probe.load(out)) == 2
    rev = tmp_path / "review.jsonl"
    rev.write_text(json.dumps({"id": "T001", "verdict": "sai", "note": "thử"}) + "\n", encoding="utf-8")
    md = tmp_path / "g.md"
    assert grade.main(["--answers", str(out), "--review", str(rev), "--out", str(md)]) == 0
    assert "T001" in md.read_text(encoding="utf-8")


# --- G8 lượt 1: các câu LLM từng tự tính sai nay phải có dữ kiện Engine trong ENGINE_FACTS --------------------------

import pytest

from app.ai.tutor.engine_query import engine_answer, fact_text


@pytest.mark.parametrize("q,want", [
    ("trong giong G truong, Em7 la bac may", "Em7 là vi7"),
    ("F#m7 trong key A major là số La Mã gì?", "F#m7 là vi7"),
    ("Trong giọng Eb trưởng, Fm là hợp âm bậc mấy?", "Fm là ii"),
    ("Bbm trong key Ab major là số La Mã gì?", "Bbm là ii"),
    ("E natural minor scale có nốt gì?", "E F# G A B C D"),
    ("D Mixolydian gồm những nốt nào?", "D E F# G A B C"),
    ("What interval is Bb up to D?", "quãng M3"),
    ("Nốt D và nốt C# phía trên cách nhau quãng gì?", "quãng M7"),
    ("Quãng M7 có bao nhiêu nửa cung?", "11 nửa cung"),
    ("Đảo quãng A4 thì được quãng gì?", "quãng d5"),
    ("Giọng B thứ có mấy dấu hóa?", "2 dấu thăng: F# C#"),
    ("Giọng thứ tương quan của Db trưởng là gì?", "Bb thứ"),
    ("Hóa biểu có 2 dấu giáng là giọng trưởng nào?", "Bb trưởng"),
    ("Thứ tự các dấu giáng trong hóa biểu là gì?", "Bb Eb Ab Db Gb Cb Fb"),
    # lượt 3: hòa âm chức năng và jazz
    ("What notes are in the Bb chord?", "Bb gồm các nốt Bb, D, F"),
    ("V7/ii trong giọng C trưởng là hợp âm gì?", "A7 (A C# E G)"),
    ("V7/iii trong giọng C trưởng là hợp âm gì?", "B7 (B D# F# A)"),
    ("V7/vi trong giọng Eb trưởng là hợp âm gì?", "G7 (G B D F)"),
    ("ii-V-I in Ab major là gì?", "Bbm7 – Eb7 – Abmaj7"),
    ("vong ii V I giong Db truong", "Ebm7 – Ab7 – Dbmaj7"),
    ("Guide tone (nốt 3 và nốt 7) của Bb7 là những nốt nào?", "nốt 3 là D, nốt 7 là Ab"),
    ("Shell voicing root–3–7 của Ebmaj7 gồm những nốt nào?", "Eb, G, D"),
    ("Ba hợp âm mượn phổ biến iv, ♭VI, ♭VII trong Bb trưởng là gì?", "Ebm, Gb, Ab"),
])
def test_engine_query_g8_nhan_dien_cau_engine_tinh_duoc(q, want):
    text = " ".join(fact_text(f) for f in engine_answer(q).facts)
    assert want in text, (q, text)


def test_engine_query_g8_khong_bat_nham():
    # "C major" trơ trọi hoặc câu thường không được hiểu là yêu cầu hóa biểu/âm giai.
    assert not engine_answer("Mình thích nghe nhạc jazz buổi tối").facts
    assert not [f for f in engine_answer("Hóa biểu là gì?").facts if f["tool"] == "key_signature"]


# --- G8: neo câu trả lời vào dữ kiện Engine -------------------------------------------------------------------------

from app.ai.tutor import fact_anchor


def _facts(q):
    return engine_answer(q).facts


@pytest.mark.parametrize("q,reply,ok", [
    ("Em7 trong key G trưởng là số La Mã gì?", "Em7 là bậc vi7 trong giọng G.", True),
    ("Trong giọng G trưởng, Em7 là bậc mấy?", "Em7 là bậc VI.", False),                       # sai hoa/thường
    ("Giọng B thứ có mấy dấu hóa?", "Giọng B thứ có 2 dấu giáng là Bb và Eb.", False),
    ("Giọng B thứ có mấy dấu hóa?", "B thứ có 2 dấu thăng là F# và C#.", True),
    ("Đảo quãng A4 thì được quãng gì?", "Bạn sẽ được quãng P5.", False),
    ("Đảo quãng A4 thì được quãng gì?", "Đảo A4 được quãng năm giảm (d5).", True),
    ("E natural minor scale có nốt gì?", "Mình không tự tính nốt để tránh sai sót.", False),
    ("E natural minor scale có nốt gì?", "Gồm E F# G A B C D.", True),
    ("Quãng M7 có bao nhiêu nửa cung?", "M7 rộng hơn m7 một nửa cung.", False),
    ("Quãng M7 có bao nhiêu nửa cung?", "Quãng M7 có 11 nửa cung.", True),
    ("Vì sao G7 muốn về C?", "Vì có nốt dẫn.", True),                                     # câu khái niệm: không ép nêu kết quả
])
def test_fact_anchor_nhan_ra_cau_tra_loi_khong_neu_ket_qua_engine(q, reply, ok):
    assert (not fact_anchor.missing(q, reply, _facts(q))) is ok, (q, reply)


def test_pipeline_ai_tu_choi_hai_lan_thi_tra_cau_engine(tmp_path, monkeypatch):
    """Gemini từ chối liệt kê nốt âm giai hai lần liền: người học vẫn nhận kết quả đúng từ Music Engine."""
    import json as _json

    from app.ai.tutor import llm
    from app.db.models import User
    from app.db.session import SessionLocal
    from app.main import app
    from app.services import ai_tutor_service as ts
    from fastapi.testclient import TestClient

    class Refuses:
        calls = 0

        def generate(self, system, prompt, schema):
            Refuses.calls += 1
            body = {"reply": "Mình không tự tính nốt các âm giai nên không liệt kê được.", "citations": [],
                    "engine_claims": [], "hint_level": 0, "suggested_actions": [], "intent": "concept"}
            return llm.LLMResult(_json.dumps(body, ensure_ascii=False), "fake", 1, 1, 1, 1)

    from datetime import datetime, timezone

    with TestClient(app), SessionLocal() as db:
        if db.get(User, "eval-user") is None:
            db.add(User(id="eval-user", display_name="eval", email="eval@example.test"))
            db.commit()
        d, _ = ts.answer_question(db, db.get(User, "eval-user"), "E natural minor scale có nốt gì?", [], None,
                                  Refuses(), datetime.now(timezone.utc))
    assert "E F# G A B C D" in d.reply and Refuses.calls == 2, (d.reply, Refuses.calls)


def test_cau_dao_quang_khong_bi_dinh_tuyen_sang_huong_dan_web():
    import json as _json
    from datetime import datetime, timezone

    from fastapi.testclient import TestClient

    from app.ai.tutor import llm
    from app.db.models import User
    from app.db.session import SessionLocal
    from app.main import app
    from app.services import ai_tutor_service as ts

    class Ok:
        def generate(self, system, prompt, schema):
            body = {"reply": "Đảo quãng P4 được quãng P5 (quãng năm đúng).", "citations": [], "engine_claims": [],
                    "hint_level": 0, "suggested_actions": [], "intent": "concept"}
            return llm.LLMResult(_json.dumps(body, ensure_ascii=False), "fake", 1, 1, 1, 1)

    with TestClient(app), SessionLocal() as db:
        if db.get(User, "eval-user") is None:
            db.add(User(id="eval-user", display_name="eval", email="eval@example.test"))
            db.commit()
        d, _ = ts.answer_question(db, db.get(User, "eval-user"), "Đảo quãng P4 thì được quãng gì?", [], None, Ok(),
                                  datetime.now(timezone.utc))
    assert d.route != "help" and "P5" in d.reply, (d.route, d.reply)


def test_v7_cua_hop_am_giam_khong_co_dap_an_engine():
    # vii° là hợp âm giảm, không làm chủ tạm thời: không được bịa dữ kiện.
    assert not [f for f in engine_answer("V7/vii° trong giọng C trưởng là hợp âm gì?").facts if f["tool"] == "secondary_dominant"]


def test_ai_tu_choi_hay_lo_chu_noi_bo_khi_engine_da_co_dap_an_thi_bi_coi_la_thieu():
    q = "Vì sao hợp âm Dm7b5 lại có nốt A?"
    facts = _facts(q)
    assert fact_anchor.missing(q, "Mình không tự tính nốt hợp âm mà không có dữ liệu từ hệ thống.", facts)
    assert fact_anchor.missing(q, "Dựa trên ENGINE_FACTS, Dm7b5 gồm D F Ab C.", facts)
    assert not fact_anchor.missing(q, "Dm7b5 gồm D, F, Ab, C nên không có nốt A.", facts)


@pytest.mark.parametrize("q,reply,ok", [
    ("ii-V-I in Ab major là gì?", "Gồm Bbm7, Eb7 và Ab.", False),                            # thiếu Abmaj7
    ("ii-V-I in Ab major là gì?", "Gồm Bbm7, Eb7 và Abmaj7.", True),
    ("V7/ii trong giọng C trưởng là hợp âm gì?", "Trong giọng C, V7/ii là E7.", False),
    ("V7/ii trong giọng C trưởng là hợp âm gì?", "Là A7: A C# E G.", True),
    ("Guide tone của G7 là nốt nào?", "Nốt 3 là B và nốt 7 là F.", True),
    ("Guide tone của G7 là nốt nào?", "Nốt 3 là B và nốt 7 là F#.", False),
])
def test_fact_anchor_cau_hoi_chuc_nang(q, reply, ok):
    assert (not fact_anchor.missing(q, reply, _facts(q))) is ok, (q, reply)


def test_guardrail_khong_hieu_nham_at_phu_thanh_bac_cua_giong():
    from app.ai.tutor.guardrail import scan_reply

    # V7/ii trong C là A7 (đúng); trước đây bị đọc thành "V7 trong C là A7" nên bị báo mâu thuẫn.
    assert not [c for c in scan_reply("V7/ii trong giọng C trưởng là A7 (A C# E G).") if c.status == "contradicted"]
    assert [c.status for c in scan_reply("G7 là V7 trong giọng C trưởng.")] == ["verified"]


@pytest.mark.parametrize("reply,status", [
    # G8 19/11: T219/T222/T224/T225 trả lời đúng shell voicing nhưng bị so với hợp âm đầy đủ và rơi vào dự phòng.
    ("Shell voicing root–3–7 của G7 gồm các nốt G, B và F.", ["verified"]),
    ("Shell root–3–7 của ii–V–I ở C major: Dm7: D–F–C. G7: G–B–F. Cmaj7: C–E–B.", ["verified"] * 3),
    ("Shell voicing của Ebmaj7: Eb, G, D.", ["verified"]),
    ("Shell voicing của G7 gồm G, B và D.", ["contradicted"]),        # shell bỏ quãng 5, không bỏ quãng 7
    ("Shell voicing của G7 gồm G, Bb, F.", ["contradicted"]),         # Bb không thuộc G7
    ("Voicing rút gọn của G7: G B F.", ["verified"]),                 # lược nốt: chỉ cần là tập con
    ("Voicing của G7: G B Eb.", ["contradicted"]),
    ("G7 gồm G B F.", ["contradicted"]),                              # không có ngữ cảnh lược nốt thì vẫn phải đủ
    ("Shell voicing của G7: G B D F.", ["verified"]),                 # liệt kê đủ nốt hợp âm vẫn đúng tên nốt
])
def test_guardrail_hieu_shell_voicing_va_voicing_rut_gon(reply, status):
    from app.ai.tutor.guardrail import scan_reply

    assert [c.status for c in scan_reply(reply)] == status, reply


@pytest.mark.parametrize("reply,expect", [
    # G8 19/11: câu sai thật trong answers_v5 (T011, T100, T110) giờ bị Engine bác.
    ("Db đến F là quãng ba trưởng và F đến Ab là quãng năm đúng.", [("M3", "verified"), ("P5", "contradicted")]),
    ("Từ A lên C# là quãng 3 trưởng (M3), vì A lên C là quãng 3 chứa 4 nửa cung.",
     [("M3", "verified"), ("4", "contradicted")]),
    ("Từ Ab lên F là quãng M6, tức là quãng sáu trưởng, có độ rộng bằng 8 nửa cung.",
     [("M6", "verified"), ("8", "contradicted")]),
    ("Quãng P5 có 7 nửa cung.", [("7", "verified")]),
    ("Quãng năm giảm có độ rộng sáu nửa cung.", [("6", "verified")]),
    # Không bắt nhầm: so sánh hai quãng, hay mệnh đề sau "và" nói về cặp nốt khác.
    ("Quãng M7 rộng hơn quãng m7 một nửa cung.", []),
    ("C lên Ab là quãng 6 thứ (m6). Bạn đếm chữ cái từ C lên A là quãng 6, và khoảng cách cao độ là 8 nửa cung.",
     [("m6", "verified")]),
])
def test_guardrail_kiem_loi_giai_thich_ve_quang(reply, expect):
    from app.ai.tutor.guardrail import scan_reply

    assert [(c.claimed, c.status) for c in scan_reply(reply)] == expect, reply


@pytest.mark.parametrize("raw,clean", [
    ("Hợp âm Bbm7 gồm bốn nốt theo ENGINE_FACTS là Bb Db F Ab.", "Hợp âm Bbm7 gồm bốn nốt theo Music Engine là Bb Db F Ab."),
    ("Âm giai C# thứ tự nhiên gồm C# D# E F# G# A B theo kết quả từ hệ thống.",
     "Âm giai C# thứ tự nhiên gồm C# D# E F# G# A B."),
    ("Giọng thứ tương quan của F trưởng là D thứ, theo kết quả từ hệ thống.", "Giọng thứ tương quan của F trưởng là D thứ."),
    ("Hệ thống hóa biểu có 7 dấu thăng.", "Hệ thống hóa biểu có 7 dấu thăng."),          # chữ "hệ thống" thường giữ nguyên
])
def test_an_chu_noi_bo_khoi_cau_tra_loi(raw, clean):
    assert fact_anchor.scrub_internal(raw) == clean


def test_probe_cho_va_hoi_lai_khi_gemini_qua_tai_va_bo_dong_du_phong_cu(tmp_path, monkeypatch):
    from app.ai.tutor import llm
    from app.eval.run import ScriptedProvider

    monkeypatch.setattr(llm, "get_provider", lambda cfg: ScriptedProvider())
    monkeypatch.setattr(probe.time, "sleep", lambda s: None)
    real, calls = probe.ask, {"n": 0}

    def flaky(db, user, q, embedder, provider, ts):
        calls["n"] += 1
        if calls["n"] <= 2:                              # hai lần đầu Gemini 503, lần ba mới trả lời
            return {"id": q["id"], "q": q["q"], "reply": "dự phòng", "status": "fallback", "fallback_reason": "unavailable"}
        return real(db, user, q, embedder, provider, ts)

    monkeypatch.setattr(probe, "ask", flaky)
    out = tmp_path / "a.jsonl"
    out.write_text(json.dumps({"id": "T013", "q": "x", "reply": "dự phòng", "fallback_reason": "unavailable"}) + "\n",
                   encoding="utf-8")                      # dòng dự phòng do 503 từ lượt trước phải bị bỏ để hỏi lại
    assert probe.main(["--only", "T001,T013", "--pause", "0", "--out", str(out)]) == 0
    rows = {r["id"]: r for r in probe.load(out)}
    assert set(rows) == {"T001", "T013"} and rows["T001"].get("fallback_reason") != "unavailable"

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

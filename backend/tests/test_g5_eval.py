"""G5 (T2): bộ ca đánh giá hợp lệ, các phép đo đúng, và chatbot/cổng nhạc lý không hồi quy so với eval/baseline.json."""

from __future__ import annotations

import json

import pytest

from app.db.models import User
from app.db.session import SessionLocal
from app.eval import cases as ec
from app.eval import metrics as m
from app.eval.run import evaluate


def test_bo_ca_hop_le_va_du_so_luong():
    cs = ec.load_cases()
    assert len(cs) >= 60
    types = {c["type"] for c in cs}
    assert {"retrieval", "followup", "untaught", "offtopic", "attack", "help", "greeting", "bad_citation", "gate"} <= types


@pytest.mark.parametrize("mutate,msg", [
    (lambda cs: cs.append(dict(cs[0])), "trùng"),
    (lambda cs: cs[0].update(type="la"), "type"),
    (lambda cs: cs[0].update(blocks=["L99-B99"]), "block"),
    (lambda cs: cs.__delitem__(slice(0, 80)), "ít nhất"),
])
def test_validate_bat_loi(mutate, msg):
    cs = ec.load_cases()
    mutate(cs)
    with pytest.raises(ec.CaseError, match=msg):
        ec.validate(cs)


def test_phep_do():
    assert m.rank_of(["a", "b", "c"], ["c", "x"]) == 3 and m.rank_of(["a"], ["z"]) is None
    assert m.hit_rate_and_mrr([1, 2, None, 6], k=5) == (50.0, 0.375)          # hạng 6 ngoài top 5 coi là trượt
    assert m.hit_rate_and_mrr([], 5) == (None, None)
    assert m.precision_recall(8, 2, 2) == (80.0, 80.0) and m.precision_recall(0, 0, 0) == (None, None)
    assert m.percentile([1, 2, 3, 4, 100], 0.95) == 100 and m.percentile([], 0.5) is None
    rows = m.best_threshold([0.9, 0.85], [0.8, 0.86], [0.82, 0.88])
    assert rows[0] == {"threshold": 0.82, "tpr": 100.0, "fpr": 50.0, "balanced": 75.0}


def test_kiem_hoi_quy_bat_duoc_tut_va_bo_qua_so_do_khong_chay():
    results = {"retrieval": {"qdrant": {"hit_rate_at_5": 80.0, "mrr": 0.8}}, "gate": {"gate_precision": 100.0}}
    base = {"retrieval/qdrant/hit_rate_at_5": 93.0, "retrieval/qdrant/mrr": 0.8, "gate/gate_precision": 100.0,
            "e2e/qdrant/route_accuracy": 97.0}                          # e2e không chạy lần này (thiếu e5): bỏ qua
    regs = m.regressions(results, base)
    assert [r.metric for r in regs] == ["retrieval/qdrant/hit_rate_at_5"] and "80.0 < baseline 93.0" in str(regs[0])
    assert m.regressions({"retrieval": {"qdrant": {"hit_rate_at_5": 91.5}}}, {"retrieval/qdrant/hit_rate_at_5": 93.0}) == []   # trong dung sai 2


def test_chatbot_va_cong_nhac_ly_khong_hoi_quy_so_voi_baseline():
    baseline = json.loads(ec.BASELINE_PATH.read_text(encoding="utf-8"))
    from fastapi.testclient import TestClient

    from app.main import app
    with TestClient(app), SessionLocal() as db:        # khởi tạo lược đồ giống các test khác
        if db.get(User, "eval-user") is None:
            db.add(User(id="eval-user", display_name="eval", email="eval@example.test"))
            db.commit()
        results = evaluate(db, db.get(User, "eval-user"))
    found = m.regressions(results, baseline)
    assert not found, "Hồi quy so với eval/baseline.json:\n" + "\n".join(map(str, found))
    # Những bất biến không cần baseline
    for cfg in results["e2e"].values():
        assert cfg["valid_citation_rate"] == 100.0 and cfg["bad_citation_caught"] == 100.0
        assert cfg["concept_wrongly_blocked"] == 0.0 and cfg["attack_handled"] == 100.0
    assert results["gate"]["gate_offtopic_reject"] == 100.0

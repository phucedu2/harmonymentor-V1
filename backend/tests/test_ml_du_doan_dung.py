"""Model dự đoán làm đúng câu tiếp theo (ADR-030): đặc trưng không rò rỉ, train tất định, model đã commit nạp được,
API sau cờ PREDICT_ENABLED và chỉ đọc dữ liệu của người trong token."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.ai import mastery as m
from app.db.models import Attempt, Exercise, ExerciseVersion, User
from app.db.session import SessionLocal
from app.main import app
from app.ml.correctness import dataset, predictor
from app.ml.correctness.features import FEATURE_NAMES, UserState, next_question_features, rows_for_user
from app.ml.correctness.train import build_matrix, train
from tests.auth_helpers import auth

client = TestClient(app)
COL = {n: i for i, n in enumerate(FEATURE_NAMES)}
T0 = 1_763_000_000


def ev(t, ok, skill="interval.naming", ex="ex1", kind="attempt", **kw):
    return {"user": "u", "t": T0 + t, "kind": kind, "skill": skill, "exercise": ex if kind == "attempt" else None,
            "correct": ok, **kw}


def test_dac_trung_chi_dung_qua_khu():
    """Dòng thứ i không đổi khi thêm/sửa sự kiện SAU nó: đặc trưng không nhìn thấy tương lai."""
    events = [ev(0, False), ev(60, True), ev(120, True, ex="ex2"), ev(86_400 * 3, False, kind="review")]
    X1, y1 = rows_for_user(events)
    flipped = events[:2] + [dict(e, correct=not e["correct"]) for e in events[2:]]
    X2, _ = rows_for_user(flipped)
    assert X1[:3] == X2[:3]
    assert y1 == [0, 1, 1, 0]
    assert X1[0][COL["seen_skill"]] == 0 and X1[0][COL["last_skill"]] == 0.5  # lượt đầu: chưa biết gì


def test_ema_trong_dac_trung_khop_luat_mastery():
    """sai → đúng sau sai (0,5) → đúng lần đầu câu khác: 0 → 0,15 → 0,405 theo app.ai.mastery."""
    events = [ev(0, False), ev(60, True), ev(120, True, ex="ex2"), ev(180, True)]
    X, _ = rows_for_user(events)
    expect = 0.0
    hist = {}
    for i, e in enumerate(events):
        assert X[i][COL["ema_skill"]] == pytest.approx(expect)
        res = m.exercise_result(hist.setdefault(e["exercise"], []), e["correct"])
        hist[e["exercise"]].append(e["correct"])
        expect = expect if res is None else m.ema(expect, res)
    assert X[2][COL["ema_skill"]] == pytest.approx(0.15)
    assert X[3][COL["ema_skill"]] == pytest.approx(0.405)
    assert X[3][COL["tries_exercise"]] == 2 and X[3][COL["last_ex_wrong"]] == 0.0  # lần trước của ex1 đúng


def test_on_luat_2a_mot_luot_moi_ngay_va_truoc_han_khong_tinh():
    s = UserState()
    s.update(ev(0, True, kind="review"))
    s.update(ev(60, False, kind="review"))  # cùng ngày VN: không tính vào EMA
    assert s.ema["interval.naming"] == pytest.approx(0.3)
    s.update(ev(86_400 * 2, False, kind="review", counts=False))  # ôn trước hạn
    assert s.ema["interval.naming"] == pytest.approx(0.3)
    assert s.n["interval.naming"] == 3  # vẫn đếm là một lượt đã làm


def test_cau_tiep_theo_la_cau_moi():
    events = [ev(0, False), ev(60, True)]
    (row,) = next_question_features(events, ["interval.naming"], T0 + 120)
    assert row[COL["tries_exercise"]] == 0 and row[COL["is_review"]] == 0
    assert row[COL["log_n_skill"]] == pytest.approx(np.log1p(2))


def test_mo_phong_co_p_true_khong_doi_du_lieu():
    a = dataset.sim_events(30, 7)
    b = dataset.sim_events(30, 7, with_true_p=True)
    strip = lambda d: {u: [{k: v for k, v in e.items() if k != "p_true"} for e in es] for u, es in d.items()}
    assert strip(b) == a  # bọc _p không làm lệch dãy ngẫu nhiên
    assert all(0.0 < e["p_true"] < 1.0 for es in b.values() for e in es)


def test_train_tat_dinh_chia_theo_nguoi_va_hon_hang_so():
    events = dataset.sim_events(120, 11, with_true_p=True)
    _, r1 = train(events, seed=11, cv_folds=3, curve=False)
    _, r2 = train(events, seed=11, cv_folds=3, curve=False)
    assert r1["ma_bam_du_lieu"] == r2["ma_bam_du_lieu"]
    assert r1["models"] == r2["models"]
    best = r1["models"][r1["model_chon"]]["test"]
    assert best["auc"] > r1["baseline_test"]["hang_so_ty_le_dung_chung"]["auc"]
    assert best["auc"] <= r1["tran_ly_thuyet_test"]["auc"] + 0.02  # không thể vượt trần đáng kể
    assert r1["so_nguoi_test"] + (r1["so_nguoi"] - r1["so_nguoi_test"]) == 120
    X, y, g, p = build_matrix(events)
    assert len(X) == len(y) == len(g) == len(p)


def test_model_da_commit_nap_duoc_va_tra_xac_suat():
    pipeline, manifest = predictor.load(predictor.DEFAULT_DIR)
    assert manifest["dac_trung"] == list(FEATURE_NAMES)
    assert "chưa chứng minh chất lượng với người học thật" in manifest["luu_y"]
    out = predictor.predict([ev(0, True), ev(60, True, ex="ex2")], predictor.mvp_skills(), path=predictor.DEFAULT_DIR)
    assert {i["skill_id"] for i in out["items"]} == set(predictor.mvp_skills())
    assert all(0.0 <= i["probability"] <= 1.0 and i["band"] in ("kho", "vua_suc", "de") for i in out["items"])


def test_thieu_model_thi_bao_khong_san_sang(tmp_path):
    with pytest.raises(predictor.ModelUnavailable):
        predictor.load(tmp_path)


@pytest.fixture(scope="module")
def _app():
    with TestClient(app):
        yield


def _user_with_attempts(n_correct: int) -> str:
    uid = "ml-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="ML", email=f"{uid}@example.test"))
        version = db.query(ExerciseVersion).join(Exercise).filter(Exercise.skill_id == "interval.naming").first()
        now = datetime.now(timezone.utc)
        for i in range(n_correct):
            db.add(Attempt(id=uuid4().hex, user_id=uid, exercise_version_id=version.id, answer="x", correct=True,
                           created_at=now - timedelta(minutes=10 - i)))
        db.add(Attempt(id=uuid4().hex, user_id=uid, exercise_version_id=version.id, answer="x", correct=False,
                       is_test=True, created_at=now))
        db.commit()
    return uid


def test_api_tat_co_tra_404(_app, monkeypatch):
    monkeypatch.delenv("PREDICT_ENABLED", raising=False)
    r = client.get("/api/v1/me/predictions", headers=auth(_user_with_attempts(1)))
    assert r.status_code == 404 and r.json()["error"]["code"] == "PREDICT_DISABLED"


def test_api_can_dang_nhap(_app, monkeypatch):
    monkeypatch.setenv("PREDICT_ENABLED", "1")
    assert client.get("/api/v1/me/predictions").status_code == 401


def test_api_bat_co_chi_doc_luot_cua_nguoi_trong_token(_app, monkeypatch):
    monkeypatch.setenv("PREDICT_ENABLED", "1")
    a, b = _user_with_attempts(3), _user_with_attempts(0)
    ra = client.get("/api/v1/me/predictions", headers=auth(a)).json()
    rb = client.get("/api/v1/me/predictions", headers=auth(b)).json()
    ia = {i["skill_id"]: i for i in ra["items"]}
    ib = {i["skill_id"]: i for i in rb["items"]}
    assert ia["interval.naming"]["attempts"] == 3  # lượt is_test không tính
    assert ib["interval.naming"]["attempts"] == 0
    assert ra["trained_on"] == "mo_phong" and "người học thật" in ra["note"]


def test_api_model_hong_tra_503(_app, monkeypatch, tmp_path):
    monkeypatch.setenv("PREDICT_ENABLED", "1")
    monkeypatch.setenv("PREDICT_MODEL_DIR", str(tmp_path))
    r = client.get("/api/v1/me/predictions", headers=auth(_user_with_attempts(1)))
    assert r.status_code == 503 and r.json()["error"]["code"] == "PREDICT_MODEL_UNAVAILABLE"


def test_db_events_bo_nguoi_mo_phong(_app):
    uid = _user_with_attempts(2)
    with SessionLocal() as db:
        db.get(User, uid).is_synthetic = True
        db.commit()
        assert uid not in dataset.db_events(db, [uid])


def test_xuat_du_lieu_that_thay_ma_nguoi_hoc(_app, tmp_path, monkeypatch):
    """File xuất để train không chứa user_id hay email thật."""
    import json
    import sys

    uid = _user_with_attempts(2)
    out = tmp_path / "that.jsonl"
    monkeypatch.setattr(sys, "argv", ["dataset", "--out", str(out)])
    dataset.export_main()
    text = out.read_text(encoding="utf-8")
    assert uid not in text and "@example.test" not in text
    rows = [json.loads(line) for line in text.splitlines()]
    assert any(r["user"] == dataset.pseudonym(uid) for r in rows)

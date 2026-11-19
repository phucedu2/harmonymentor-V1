"""Train model dự đoán làm đúng câu tiếp theo (ADR-031).

    cd backend && python -m app.ml.correctness.train                       # 2.000 người mô phỏng, seed cố định
    cd backend && python -m app.ml.correctness.train --data ../data/correctness/that.jsonl --source that

Các bước theo Hands-On ML chương 2–4:
1. Dựng bảng đặc trưng (features.py), mỗi dòng = một lượt làm/ôn, đặc trưng chỉ lấy từ quá khứ.
2. Chia train/test THEO NGƯỜI HỌC (GroupShuffleSplit): một người nằm trọn một bên, nên test đo đúng việc
   "đoán cho người học mới", không phải đoán lại lượt kế bên của người đã thấy.
3. Hai pipeline (chuẩn hóa → model): Logistic Regression và HistGradientBoosting; GridSearchCV với GroupKFold.
4. So với baseline: "xác suất = mastery EMA", "tỷ lệ đúng trước đó của kỹ năng", và hằng số (tỷ lệ đúng chung).
5. Chấm trên test MỘT lần: AUC, log loss, Brier, Precision/Recall/F1 ở ngưỡng 0,5, ECE (độ hiệu chỉnh).
6. Lưu pipeline tốt nhất bằng joblib + manifest.json; ghi số đo ra docs/giai-doan/ml-du-doan/KET_QUA.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, brier_score_loss, f1_score, log_loss, precision_score, recall_score,
                             roc_auc_score)
from sklearn.model_selection import GridSearchCV, GroupKFold, GroupShuffleSplit, learning_curve
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from . import dataset
from .features import FEATURE_NAMES, FEATURE_VERSION, NUMERIC, rows_for_user

ROOT = Path(__file__).resolve().parents[4]
MODEL_DIR = ROOT / "backend" / "models" / "correctness"
RESULT = ROOT / "docs" / "giai-doan" / "ml-du-doan" / "KET_QUA.json"
MODEL_VERSION = "1.0.0"
DEFAULT_SEED = 20261119
CAVEAT = "Số đo trên người học mô phỏng: chưa chứng minh chất lượng với người học thật."


def build_matrix(events_by_user: dict[str, list[dict]]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray | None]:
    """X, y, nhóm (người học) và p_true (chỉ có với mô phỏng, để đo trần; không phải đặc trưng)."""
    X, y, g, pt = [], [], [], []
    for uid in sorted(events_by_user):
        events = sorted((e for e in events_by_user[uid] if e["kind"] in ("attempt", "review")), key=lambda e: int(e["t"]))
        xs, ys = rows_for_user(events)
        X += xs
        y += ys
        g += [uid] * len(ys)
        pt += [e.get("p_true") for e in events]
    has_p = len(pt) > 0 and all(v is not None for v in pt)
    return (np.asarray(X, dtype=float), np.asarray(y, dtype=int), np.asarray(g),
            np.asarray(pt, dtype=float) if has_p else None)


def dataset_hash(X: np.ndarray, y: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(np.round(X, 9)).tobytes())
    h.update(y.astype(np.int8).tobytes())
    return h.hexdigest()[:16]


def ece(y: np.ndarray, p: np.ndarray, bins: int = 10) -> tuple[float, list[dict]]:
    """Expected Calibration Error: trung bình |xác suất đoán − tỷ lệ đúng thật| theo 10 khoảng xác suất."""
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    total, table = 0.0, []
    for b in range(bins):
        mask = idx == b
        if not mask.any():
            continue
        conf, acc = float(p[mask].mean()), float(y[mask].mean())
        total += mask.mean() * abs(conf - acc)
        table.append({"khoang": f"{edges[b]:.1f}-{edges[b + 1]:.1f}", "so_dong": int(mask.sum()),
                      "du_doan_tb": round(conf, 4), "ty_le_dung_that": round(acc, 4)})
    return round(float(total), 4), table


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    pred = (p >= 0.5).astype(int)
    e, table = ece(y, p)
    return {"auc": round(float(roc_auc_score(y, p)), 4), "log_loss": round(float(log_loss(y, p)), 4),
            "brier": round(float(brier_score_loss(y, p)), 4), "accuracy": round(float(accuracy_score(y, pred)), 4),
            "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y, pred, zero_division=0)), 4), "ece": e, "hieu_chinh": table}


def candidates(seed: int) -> dict[str, tuple[Pipeline, dict]]:
    lr = Pipeline([("scale", StandardScaler()), ("model", LogisticRegression(max_iter=2000))])
    # early_stopping=False để kết quả tất định (bật thì sklearn tự tách một phần dữ liệu ngẫu nhiên).
    hgb = Pipeline([("scale", "passthrough"),
                    ("model", HistGradientBoostingClassifier(early_stopping=False, random_state=seed))])
    return {
        "logistic_regression": (lr, {"model__C": [0.01, 0.1, 1.0, 10.0]}),
        "hist_gradient_boosting": (hgb, {"model__learning_rate": [0.05, 0.1], "model__max_depth": [3, 6],
                                         "model__max_iter": [150]}),
    }


def train(events_by_user: dict[str, list[dict]], *, seed: int = DEFAULT_SEED, source: str = "mo_phong",
          cv_folds: int = 5, curve: bool = True) -> tuple[Pipeline, dict]:
    t0 = time.time()
    X, y, groups, p_true = build_matrix(events_by_user)
    if len(np.unique(groups)) < 2 * cv_folds or len(np.unique(y)) < 2:
        raise ValueError("Quá ít người học hoặc chỉ có một loại kết quả: chưa train được.")
    split = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
    tr, te = next(split.split(X, y, groups))
    assert not set(groups[tr]) & set(groups[te]), "rò rỉ: một người nằm ở cả train và test"
    Xtr, ytr, gtr, Xte, yte = X[tr], y[tr], groups[tr], X[te], y[te]

    col = {n: i for i, n in enumerate(FEATURE_NAMES)}
    base_rate = float(ytr.mean())
    baselines = {
        "hang_so_ty_le_dung_chung": metrics(yte, np.full(len(yte), base_rate)),
        "mastery_ema": metrics(yte, Xte[:, col["ema_skill"]]),
        "ty_le_dung_truoc_do_cua_ky_nang": metrics(yte, Xte[:, col["acc_skill"]]),
    }
    # Trần lý thuyết: "đoán" bằng chính xác suất bộ mô phỏng dùng để tung. Không model nào vượt được mức này.
    ceiling = metrics(yte, p_true[te]) if p_true is not None else None

    models, fitted = {}, {}
    for name, (pipe, grid) in candidates(seed).items():
        search = GridSearchCV(pipe, grid, scoring="roc_auc", cv=GroupKFold(n_splits=cv_folds), refit=True)
        search.fit(Xtr, ytr, groups=gtr)
        best = search.best_estimator_
        fitted[name] = best
        models[name] = {
            "tham_so_tot_nhat": {k.replace("model__", ""): v for k, v in search.best_params_.items()},
            "auc_kiem_cheo": round(float(search.best_score_), 4),
            "bang_tham_so": [{"tham_so": {k.replace("model__", ""): v for k, v in prm.items()},
                              "auc_tb": round(float(mu), 4), "do_lech": round(float(sd), 4)}
                             for prm, mu, sd in zip(search.cv_results_["params"], search.cv_results_["mean_test_score"],
                                                    search.cv_results_["std_test_score"])],
            "train": {"auc": round(float(roc_auc_score(ytr, best.predict_proba(Xtr)[:, 1])), 4)},
            "test": metrics(yte, best.predict_proba(Xte)[:, 1]),
        }

    # Chọn theo AUC kiểm chéo (KHÔNG theo test, để test vẫn là bài thi chưa nhìn thấy).
    chosen = max(models, key=lambda n: models[n]["auc_kiem_cheo"])
    best = fitted[chosen]

    lr = fitted["logistic_regression"].named_steps["model"]
    coef = sorted(zip(FEATURE_NAMES, lr.coef_[0]), key=lambda kv: -abs(kv[1]))
    rng = np.random.RandomState(seed)
    sub = rng.choice(len(yte), size=min(20_000, len(yte)), replace=False)
    imp = permutation_importance(best, Xte[sub], yte[sub], scoring="roc_auc", n_repeats=3, random_state=seed)
    importance = sorted(zip(FEATURE_NAMES, imp.importances_mean), key=lambda kv: -kv[1])

    curve_rows = []
    if curve:
        sizes, tr_sc, va_sc = learning_curve(best, Xtr, ytr, groups=gtr, cv=GroupKFold(n_splits=3),
                                             train_sizes=[0.05, 0.15, 0.4, 1.0], scoring="roc_auc", shuffle=True,
                                             random_state=seed)
        curve_rows = [{"so_dong_train": int(n), "auc_train": round(float(a.mean()), 4),
                       "auc_validation": round(float(b.mean()), 4)} for n, a, b in zip(sizes, tr_sc, va_sc)]

    report = {
        "phien_ban_model": MODEL_VERSION, "phien_ban_dac_trung": FEATURE_VERSION,
        "nguon_du_lieu": source, "seed": seed,
        "so_nguoi": int(len(np.unique(groups))), "so_dong": int(len(y)),
        "so_dong_train": int(len(tr)), "so_dong_test": int(len(te)),
        "so_nguoi_test": int(len(np.unique(groups[te]))),
        "ty_le_dung_train": round(base_rate, 4), "ma_bam_du_lieu": dataset_hash(X, y),
        "dac_trung": list(FEATURE_NAMES), "dac_trung_so": list(NUMERIC),
        "baseline_test": baselines, "tran_ly_thuyet_test": ceiling, "models": models, "model_chon": chosen,
        "he_so_logistic_chuan_hoa": [{"dac_trung": n, "he_so": round(float(c), 4)} for n, c in coef],
        "do_quan_trong_hoan_vi": [{"dac_trung": n, "giam_auc": round(float(v), 4)} for n, v in importance],
        "duong_hoc": curve_rows,
        "moi_truong": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                       "numpy": np.__version__, "joblib": joblib.__version__},
        "ngay_chay": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "thoi_gian_giay": round(time.time() - t0, 1),
        "luu_y": CAVEAT if source == "mo_phong" else "Dữ liệu thật của nhóm/người thử: số người còn ít, xem so_nguoi.",
    }
    return best, report


def save(best: Pipeline, report: dict, model_dir: Path = MODEL_DIR) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(best, model_dir / "model.joblib", compress=3)
    manifest = {k: report[k] for k in ("phien_ban_model", "phien_ban_dac_trung", "nguon_du_lieu", "seed", "so_nguoi",
                                       "so_dong", "ma_bam_du_lieu", "model_chon", "dac_trung", "moi_truong",
                                       "ngay_chay", "luu_y")}
    manifest["test"] = {k: v for k, v in report["models"][report["model_chon"]]["test"].items() if k != "hieu_chinh"}
    manifest["baseline_test_auc"] = {k: v["auc"] for k, v in report["baseline_test"].items()}
    (model_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sim-users", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--data", help="file .jsonl xuất bằng `python -m app.ml.correctness.dataset` (thay cho mô phỏng)")
    ap.add_argument("--source", default=None, help="nhãn nguồn ghi vào manifest (mặc định mo_phong hoặc that)")
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()
    if args.data:
        events, source = dataset.read_jsonl(Path(args.data)), args.source or "that"
    else:
        events, source = dataset.sim_events(args.sim_users, args.seed, with_true_p=True), args.source or "mo_phong"
    best, report = train(events, seed=args.seed, source=source)
    if not args.no_save:
        save(best, report)
        RESULT.parent.mkdir(parents=True, exist_ok=True)
        RESULT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    chosen = report["model_chon"]
    print(f"{report['so_nguoi']} người, {report['so_dong']} lượt; test {report['so_nguoi_test']} người.")
    for name, b in report["baseline_test"].items():
        print(f"  baseline {name:34s} AUC {b['auc']:.4f}  logloss {b['log_loss']:.4f}  ECE {b['ece']:.4f}")
    if report["tran_ly_thuyet_test"]:
        c = report["tran_ly_thuyet_test"]
        print(f"  trần lý thuyết (biết p_true của mô phỏng)    AUC {c['auc']:.4f}  logloss {c['log_loss']:.4f}  ECE {c['ece']:.4f}")
    for name, r in report["models"].items():
        t = r["test"]
        print(f"  {name:43s} AUC {t['auc']:.4f}  logloss {t['log_loss']:.4f}  ECE {t['ece']:.4f}  "
              f"P {t['precision']:.3f} R {t['recall']:.3f}  (CV {r['auc_kiem_cheo']:.4f}, train {r['train']['auc']:.4f})")
    print(f"Chọn: {chosen}. {report['luu_y']}")


if __name__ == "__main__":
    main()

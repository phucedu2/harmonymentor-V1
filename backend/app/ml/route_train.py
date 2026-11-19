"""Train lại tầng 1 của bộ định tuyến AI Tutor (4 nhãn) theo quy trình handson-ml3 (ADR-030).

    cd backend && python -m app.ml.route_train            # train, chấm, lưu model + số đo
    cd backend && python -m app.ml.route_train --no-save  # chỉ in số đo

Quy trình (chương 2–4 của handson-ml3, áp vào dự án):
1. Chia dữ liệu 3 tập cố định: TRAIN (học), VALIDATION (chọn model), TEST (chấm một lần cuối, không chỉnh gì theo nó).
   Câu train gần trùng với validation/test bị loại trước khi học, để số đo không đẹp giả.
2. Pipeline scikit-learn gói "chuẩn hóa câu → biến thành vector → Logistic Regression" thành một khối, lưu bằng joblib.
3. GridSearchCV với GroupKFold (5 phần) trên TRAIN chọn tham số; các cách nói khác của cùng một ý nằm chung một nhóm
   nên không thể vừa ở phần học vừa ở phần chấm.
4. So 3 cách biến câu thành vector: TF-IDF n-gram ký tự, vector e5-small, gộp cả hai. Mốc so sánh là model cũ
   (route_classifier.train trên dữ liệu cũ).
5. Chấm: accuracy, Precision/Recall/F1 từng nhãn, macro-F1, ma trận nhầm lẫn, đường học (learning curve).
Model mới chỉ được BẬT (manifest "enabled": true) khi thắng model cũ cả trên VALIDATION lẫn TEST."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TUTOR = ROOT / "backend" / "app" / "ai" / "tutor"
DATA = ROOT / "scripts" / "ai" / "data"
PHIEU = ROOT / "docs" / "giai-doan" / "ai-gop-y" / "phieu-cau-hoi"
MODEL_DIR = ROOT / "backend" / "models" / "route"
RESULT_DIR = ROOT / "docs" / "giai-doan" / "ml-dinh-tuyen"
LABELS = ("nhac_ly", "huong_dan", "chao_hoi", "ngoai_pham_vi")
# Luồng A/B (trong bài / chưa dạy) đều là câu nhạc lý; nhãn tầng 1 không phân biệt A với B (route_classifier.py).
FLOW_LABEL = {"A": "nhac_ly", "B": "nhac_ly", "C": "ngoai_pham_vi", "D": "huong_dan", "G": "chao_hoi"}
NEAR = 0.8          # cùng ngưỡng gần trùng với scripts/ai/gop_y/kiem_trung_du_lieu.py
SEED = 0


# ---------------------------------------------------------------- dữ liệu

def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _row(q: str, label: str, group: str, src: str) -> dict:
    return {"q": q, "label": label, "group": group, "src": src}


def splits() -> dict[str, list[dict]]:
    """Ba tập cố định. Nguồn nào vào tập nào ghi rõ ở đây để giảng viên hỏi thì chỉ được ngay."""
    route = _load(TUTOR / "route_data.json")
    gd2 = _load(TUTOR / "route_data_gd2.json")
    train = [_row(q, lab, f"gd1-{lab}-{i}", "route_data.train") for lab, rows in route["train"].items()
             for i, q in enumerate(rows)]
    # route_data_gd2.json chỉ giữ câu; nhóm lấy từ file gốc gd2/train.json (cùng câu, cùng thứ tự sinh).
    gd2_groups = {it["q"]: it["group"] for it in _load(DATA / "gd2" / "train.json")["items"]}
    train += [_row(q, lab, gd2_groups.get(q, f"gd2-{lab}-{i}"), "route_data_gd2.train")
              for lab, rows in gd2["train"].items() for i, q in enumerate(rows)]
    train += [_row(it["q"], it["label"], it["group"], "route_data_ml (Claude 19/11)")
              for it in _load(TUTOR / "route_data_ml.json")["items"]]

    val = [_row(q, lab, "", "route_data.dev") for lab, rows in route["dev"].items() for q in rows]
    val += [_row(it["q"], FLOW_LABEL[it["flow"]], "", "router_dev") for it in _load(DATA / "router_dev.json")["items"]]
    val += [_row(it["q"], FLOW_LABEL[it["flow"]], "", "gd2.dev") for it in _load(DATA / "gd2" / "dev.json")["items"]]
    val += [_row(it["q"], FLOW_LABEL[it["flow"]], "", "phieu_Phuc_dev")
            for it in _load(PHIEU / "phieu_Phuc_dev.json")["items"]]

    test = [_row(it["q"], FLOW_LABEL[it["flow"]], "", "gd2.test_tam")
            for it in _load(DATA / "gd2" / "test_tam.json")["items"]]
    for name in ("phieu_Dat_test", "phieu_Thang_test"):
        test += [_row(it["q"], FLOW_LABEL[it["flow"]], "", name)
                 for it in _load(PHIEU / "claude-tham-khao" / f"{name}.json")["items"]]
    test += [_row(it["q"], FLOW_LABEL[it["flow"]], "", "gd0_cau_do_luong")
             for it in _load(DATA / "gd0_cau_do_luong.json")["items"]]
    # Câu tấn công (prompt injection) bị bộ lọc riêng chặn trước tầng 1 nên không tính ở đây.
    for line in (ROOT / "eval" / "cases.jsonl").read_text(encoding="utf-8").splitlines():
        c = json.loads(line)
        if c.get("flow") and c["type"] != "attack":
            test.append(_row(c["q"], FLOW_LABEL[c["flow"]], "", f"eval/cases {c['type']}"))
    return {"train": train, "val": val, "test": test}


def norm(text: str) -> str:
    t = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    return " ".join(re.findall(r"[a-z0-9#/]+", t))


def _grams(text: str) -> set[str]:
    t = f" {norm(text)} "
    return {t[i:i + 3] for i in range(len(t) - 2)}


def _near(a: tuple[str, set[str]], b: tuple[str, set[str]]) -> bool:
    return a[0] == b[0] or bool(a[1] and b[1] and len(a[1] & b[1]) / len(a[1] | b[1]) >= NEAR)


def remove_leaks(data: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Bỏ câu trùng/gần trùng: train ~ (val ∪ test) bỏ ở train; val ~ test bỏ ở val; trùng trong cùng tập giữ 1.
    Trả về danh sách câu đã bỏ để ghi vào số đo."""
    keyed = {k: [(r, (norm(r["q"]), _grams(r["q"]))) for r in rows] for k, rows in data.items()}
    dropped: dict[str, list[dict]] = {"train": [], "val": [], "test": []}

    def dedupe(name: str) -> None:
        seen, keep = set(), []
        for r, key in keyed[name]:
            if key[0] in seen:
                dropped[name].append({**r, "why": "trùng trong tập"})
                continue
            seen.add(key[0])
            keep.append((r, key))
        keyed[name] = keep

    for name in ("test", "val", "train"):
        dedupe(name)
    test_keys = [k for _, k in keyed["test"]]
    keep_val = []
    for r, k in keyed["val"]:
        (dropped["val"].append({**r, "why": "gần trùng test"}) if any(_near(k, t) for t in test_keys)
         else keep_val.append((r, k)))
    keyed["val"] = keep_val
    held = test_keys + [k for _, k in keyed["val"]]
    keep_train = []
    for r, k in keyed["train"]:
        (dropped["train"].append({**r, "why": "gần trùng val/test"}) if any(_near(k, t) for t in held)
         else keep_train.append((r, k)))
    keyed["train"] = keep_train
    out = {k: [r for r, _ in v] for k, v in keyed.items()}
    out["_dropped"] = dropped  # type: ignore[assignment]
    return out


def data_hash(rows: list[dict]) -> str:
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda r: (r["label"], r["q"])):
        h.update(f'{r["label"]}|{r["q"]}\n'.encode("utf-8"))
    return h.hexdigest()


# ---------------------------------------------------------------- model

def candidates() -> dict[str, tuple]:
    """(pipeline, lưới tham số). Lưới nhỏ có chủ đích: 1000 câu thì lưới to dễ chọn tham số "may mắn"."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import FeatureUnion, Pipeline

    from .route_features import E5Features, prep

    def tfidf():
        return TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True, preprocessor=prep)

    def lr():
        return LogisticRegression(max_iter=5000, random_state=SEED)

    return {
        "tfidf": (Pipeline([("vec", tfidf()), ("clf", lr())]),
                  {"vec__ngram_range": [(2, 4), (1, 5)], "clf__C": [3, 10, 30], "clf__class_weight": [None, "balanced"]}),
        "e5": (Pipeline([("vec", E5Features()), ("clf", lr())]),
               {"clf__C": [3, 10, 30, 100], "clf__class_weight": [None, "balanced"]}),
        "tfidf+e5": (Pipeline([("vec", FeatureUnion([("tfidf", tfidf()), ("e5", E5Features())])), ("clf", lr())]),
                     {"vec__tfidf__ngram_range": [(2, 4), (1, 5)], "vec__e5__weight": [0.5, 1.0],
                      "clf__C": [10, 30], "clf__class_weight": [None, "balanced"]}),
    }


def old_model():
    """Model đang chạy trên phuc-music: cùng tham số, cùng dữ liệu (route_data + gd2), train lúc khởi động."""
    from ..ai.tutor import route_classifier as rc
    return rc.train(*rc.pairs(rc.load_data(gd2=True)["train"]))


def evaluate(predict, rows: list[dict]) -> dict:
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

    y = [r["label"] for r in rows]
    p = list(predict([r["q"] for r in rows]))
    rep = classification_report(y, p, labels=list(LABELS), output_dict=True, zero_division=0)
    return {"n": len(rows), "accuracy": round(accuracy_score(y, p), 4),
            "macro_f1": round(f1_score(y, p, labels=list(LABELS), average="macro", zero_division=0), 4),
            "per_label": {lab: {k: round(rep[lab][k], 4) for k in ("precision", "recall", "f1-score", "support")}
                          for lab in LABELS},
            "confusion": {"labels": list(LABELS), "rows_true_cols_pred":
                          confusion_matrix(y, p, labels=list(LABELS)).tolist()},
            "errors": [{"q": r["q"], "true": t, "pred": q, "src": r["src"]}
                       for r, t, q in zip(rows, y, p) if t != q]}


def bootstrap_diff(rows: list[dict], pred_a: list[str], pred_b: list[str], n: int = 2000) -> dict:
    """Khoảng tin cậy 95% cho (macro-F1 của A) − (macro-F1 của B) trên cùng tập test, bốc lại câu có hoàn lại.
    Khoảng chứa 0 nghĩa là chênh lệch có thể chỉ do may rủi của vài câu, chưa kết luận A hơn B được."""
    import numpy as np
    from sklearn.metrics import f1_score

    y = np.array([r["label"] for r in rows])
    a, b = np.array(pred_a), np.array(pred_b)
    rng = np.random.default_rng(SEED)
    diffs = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        diffs.append(f1_score(y[i], a[i], labels=list(LABELS), average="macro", zero_division=0)
                     - f1_score(y[i], b[i], labels=list(LABELS), average="macro", zero_division=0))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {"mean": round(float(np.mean(diffs)), 4), "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "resamples": n}


def run(save: bool = True, n_jobs: int = 1) -> dict:
    import numpy as np
    import sklearn
    from sklearn.model_selection import GridSearchCV, GroupKFold, learning_curve

    from ..ai.tutor.intent import _prep

    data = remove_leaks(splits())
    tr, va, te = data["train"], data["val"], data["test"]
    x, y, g = [r["q"] for r in tr], [r["label"] for r in tr], [r["group"] for r in tr]
    cv = GroupKFold(n_splits=5)

    old = old_model()
    old_pred = lambda qs: old.predict([_prep(q) for q in qs])  # noqa: E731
    res: dict = {"models": {}, "old": {"val": evaluate(old_pred, va)}}

    # Mốc công bằng: model cũ học trên dữ liệu cũ, nhưng ĐÃ loại câu gần trùng với val/test. Model cũ đang chạy được
    # train trên cả những câu gần trùng đó nên điểm test của nó đẹp hơn thực tế (rò dữ liệu).
    from ..ai.tutor import route_classifier as rc
    recipes = {"old_recipe_clean": [r for r in tr if not r["src"].startswith("route_data_ml")],
               "old_recipe_clean_plus_new_data": tr}
    fair = {k: rc.train([_prep(r["q"]) for r in rows], [r["label"] for r in rows]) for k, rows in recipes.items()}

    best = {}
    for name, (pipe, grid) in candidates().items():
        gs = GridSearchCV(pipe, grid, cv=cv, scoring="f1_macro", n_jobs=n_jobs, refit=True)
        gs.fit(x, y, groups=g)
        best[name] = gs.best_estimator_
        res["models"][name] = {"cv_macro_f1": round(float(gs.best_score_), 4),
                               "best_params": {k: (list(v) if isinstance(v, tuple) else v)
                                               for k, v in gs.best_params_.items()},
                               "val": evaluate(gs.best_estimator_.predict, va)}
        print(f"{name:9} CV {gs.best_score_:.4f}  val macro-F1 {res['models'][name]['val']['macro_f1']:.4f}  {gs.best_params_}")

    # Chọn model chỉ dựa trên VALIDATION (không nhìn TEST).
    winner = max(best, key=lambda n: res["models"][n]["val"]["macro_f1"])
    no_e5 = "tfidf"   # dự phòng khi máy chưa tải e5 (AI Tutor khi đó cũng lùi về BM25)
    res["winner"] = winner

    # TEST: chấm đúng một lần, cho model cũ, model thắng và model dự phòng.
    res["old"]["test"] = evaluate(old_pred, te)
    for k, m in fair.items():
        pred = lambda qs, m=m: m.predict([_prep(q) for q in qs])  # noqa: E731
        res[k] = {"train": len(recipes[k]), "val": evaluate(pred, va), "test": evaluate(pred, te)}
        print(f"{k:30} val {res[k]['val']['macro_f1']:.4f}  test {res[k]['test']['macro_f1']:.4f}")
    for name in {winner, no_e5}:
        res["models"][name]["test"] = evaluate(best[name].predict, te)
    print(f"old       val {res['old']['val']['macro_f1']:.4f}  test {res['old']['test']['macro_f1']:.4f}")
    for name in {winner, no_e5}:
        print(f"{name:9} test {res['models'][name]['test']['macro_f1']:.4f}")

    # So từng model với model cũ đang chạy trên TEST, kèm khoảng tin cậy (test chỉ ~300 câu, nhãn nhỏ có 20–33 câu).
    old_te = list(old_pred([r["q"] for r in te]))
    preds = {name: list(best[name].predict([r["q"] for r in te])) for name in {winner, no_e5}}
    preds.update({k: list(m.predict([_prep(r["q"]) for r in te])) for k, m in fair.items()})
    res["vs_old_test"] = {k: bootstrap_diff(te, p, old_te) for k, p in preds.items()}
    for k, v in res["vs_old_test"].items():
        print(f"{k:30} − old: {v['mean']:+.4f}  CI95 {v['ci95']}")

    # Đường học: macro-F1 khi train bằng 10%…100% dữ liệu (CV theo nhóm). Hai đường còn cách xa nhau = model học vẹt,
    # thêm dữ liệu còn giúp; hai đường sát nhau mà thấp = model quá đơn giản.
    sizes, tr_sc, cv_sc = learning_curve(best[winner], x, y, groups=g, cv=cv, scoring="f1_macro",
                                         train_sizes=np.linspace(0.1, 1.0, 6), n_jobs=n_jobs, shuffle=True,
                                         random_state=SEED)
    res["learning_curve"] = {"train_sizes": sizes.tolist(), "train_f1": tr_sc.mean(axis=1).round(4).tolist(),
                             "cv_f1": cv_sc.mean(axis=1).round(4).tolist()}

    def beats(name: str) -> bool:
        m = res["models"][name]
        return (m["val"]["macro_f1"] > res["old"]["val"]["macro_f1"]
                and m["test"]["macro_f1"] > res["old"]["test"]["macro_f1"])

    res["enabled"] = {"primary": beats(winner), "no_e5": beats(no_e5)}
    res["data"] = {"train": len(tr), "val": len(va), "test": len(te), "train_hash": data_hash(tr),
                   "dropped": {k: len(v) for k, v in data["_dropped"].items()},
                   "dropped_rows": data["_dropped"],
                   "label_counts": {k: {lab: sum(r["label"] == lab for r in rows) for lab in LABELS}
                                    for k, rows in (("train", tr), ("val", va), ("test", te))}}
    res["run"] = {"date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "sklearn": sklearn.__version__, "command": "cd backend && python -m app.ml.route_train"}
    if save:
        save_models(best, winner, no_e5, res)
    return res


def save_models(best: dict, winner: str, no_e5: str, res: dict) -> None:
    import joblib
    import sklearn

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    files = {}
    for role, name in (("primary", winner), ("no_e5", no_e5)):
        path = MODEL_DIR / f"route-{name.replace('+', '-')}.joblib"
        joblib.dump(best[name], path, compress=3)
        files[role] = {"file": path.name, "kind": name, "needs_e5": "e5" in name,
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "enabled": res["enabled"][role],
                       "test_macro_f1": res["models"][name]["test"]["macro_f1"]}
    manifest = {"note": "Tầng 1 định tuyến AI Tutor (ADR-030). Sinh bởi app/ml/route_train.py; route_classifier.py chỉ "
                        "nạp file đúng sha256 và đúng phiên bản scikit-learn, không thì train lại model cũ lúc khởi động.",
                "sklearn": sklearn.__version__, "labels": list(LABELS), "embedder": "multilingual-e5-small",
                "train_hash": res["data"]["train_hash"], "date": res["run"]["date"], "models": files}
    (MODEL_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    (RESULT_DIR / "DO_LUONG.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--jobs", type=int, default=1)
    a = ap.parse_args(argv)
    run(save=not a.no_save, n_jobs=a.jobs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

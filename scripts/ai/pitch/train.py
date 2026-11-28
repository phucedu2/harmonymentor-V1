"""ADR-032 bước 2: train model nhận diện nốt (MLP scikit-learn) và so với YIN trên CÙNG bộ test.

Các bước theo handson-ml3:
  Ch.2  chia train/test theo NHÓM (bản thu gốc), không chia ngẫu nhiên từng khung.
  Ch.2/7 GridSearchCV + GroupKFold chọn kích thước lớp ẩn và hệ số chuẩn hóa L2 (alpha).
  Ch.3  độ chính xác, ma trận nhầm lẫn 12 lớp cao độ, tỉ lệ nhầm quãng tám.
  Ch.4  so điểm train và test để thấy model có học vẹt không.
  Ch.10 MLP (mạng nơ-ron nhiều lớp): Pipeline(StandardScaler → MLPClassifier).
Thêm một phép thử khó: giấu hẳn một nhạc cụ (cello) khỏi train, xem model có tổng quát được không.

    python scripts/ai/pitch/du_lieu.py --out /tmp/pitch_data.npz
    python scripts/ai/pitch/train.py --data /tmp/pitch_data.npz --report docs/giai-doan/nhan-dien-not-micro/KET_QUA_MODEL.md \
        --export frontend/public/models/pitch_mlp.json --fixture frontend/src/audio/pitch/__fixtures__/parity.json
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.model_selection import GridSearchCV, GroupKFold, GroupShuffleSplit
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dac_trung import N_FEATURES, features, refine_hz, yin_hz  # noqa: E402

SR = 48000
ABSTAIN = 0.5   # xác suất cao nhất < 0,5 thì model "không chắc", không trả lời (giống YIN trả null)
COND_ORDER = ["sach", "nhieu15", "nhieu5", "micro_laptop", "u_dien", "loa", "on_quat", "on_giong_noi", "on_nhac_nen", "on_tieng_dong"]
COND_VI = {"sach": "Sạch", "nhieu15": "Nhiễu trắng 15 dB", "nhieu5": "Nhiễu trắng 5 dB (rất ồn)",
           "micro_laptop": "Micro laptop (mất trầm < 250 Hz + nhiễu hồng)", "u_dien": "Tiếng ù điện 50 Hz",
           "loa": "Piano ảo qua loa laptop (vang phòng)", "on_quat": "Quạt/điều hòa, SNR −3…25 dB", "on_giong_noi": "Người nói chuyện/TV, SNR −3…25 dB",
           "on_nhac_nen": "Nhạc nền, SNR −3…25 dB", "on_tieng_dong": "Gõ bàn/đóng cửa, SNR −3…25 dB"}
PCS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def yin_midi(raw: np.ndarray) -> np.ndarray:
    out = np.full(len(raw), -1)
    for i, fr in enumerate(raw):
        hz = yin_hz(fr, SR)
        if hz is not None:
            out[i] = int(np.floor(69 + 12 * np.log2(hz / 440) + 0.5))
    return out


def model_midi(model, X: np.ndarray) -> np.ndarray:
    """Lớp 0 = "không có nốt"; không chắc (xác suất < 0,5) cũng coi là không trả lời (-1)."""
    proba = model.predict_proba(X)
    pred = model.classes_[proba.argmax(1)]
    return np.where((proba.max(1) >= ABSTAIN) & (pred > 0), pred, -1)


def scores(pred: np.ndarray, y: np.ndarray) -> dict:
    answered = pred >= 0
    ok = pred == y
    octave = answered & (pred % 12 == y % 12) & (pred != y)
    return {"dung": ok.mean(), "tra_loi": answered.mean(), "dung_khi_tra_loi": ok[answered].mean() if answered.any() else 0.0,
            "nham_quang_tam": octave.mean(), "dung_lop_cao_do": (answered & (pred % 12 == y % 12)).mean()}


def confusion_pc(pred: np.ndarray, y: np.ndarray) -> np.ndarray:
    m = np.zeros((12, 13), dtype=int)  # cột 13 = không trả lời
    for p, t in zip(pred, y):
        m[t % 12, 12 if p < 0 else p % 12] += 1
    return m


def pct(x: float) -> str:
    return f"{100 * x:.1f}%".replace(".", ",")


def export(model, path: Path) -> dict:
    """Ghi model thành JSON nhỏ (trọng số float32 base64) để trình duyệt tự tính, không cần thư viện ML."""
    scaler, mlp = model.named_steps["scale"], model.named_steps["mlp"]
    b64 = lambda a: base64.b64encode(np.asarray(a, dtype="<f4").tobytes()).decode()  # noqa: E731
    layers = [{"in": int(W.shape[0]), "out": int(W.shape[1]), "W": b64(W), "b": b64(b)} for W, b in zip(mlp.coefs_, mlp.intercepts_)]
    data = {"version": 1, "n_features": N_FEATURES, "classes": [int(c) for c in mlp.classes_], "abstain": ABSTAIN,
            "activation": mlp.activation, "mean": b64(scaler.mean_), "scale": b64(scaler.scale_), "layers": layers}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, separators=(",", ":")))
    kb = path.stat().st_size / 1024
    print(f"model {kb:.0f} KB")
    assert kb < 500, "model phải < 500 KB để tải nhanh (Phúc 8A)"
    return data


def fixture(model, raw: np.ndarray, y: np.ndarray, path: Path, n: int = 6):
    """Vài khung thật + đặc trưng + xác suất Python tính ra; Vitest kiểm bản TypeScript ra cùng số."""
    idx = np.linspace(0, len(raw) - 1, n).astype(int)
    items = []
    for i in idx:
        f, c = features(raw[i], SR)
        p = model.predict_proba(f[None, :].astype(np.float32))[0]
        k = int(p.argmax())
        items.append({"label": int(y[i]), "frame": base64.b64encode(raw[i].astype("<f4").tobytes()).decode(),
                      "features": [round(float(v), 6) for v in f], "top_class": int(model.classes_[k]), "top_prob": round(float(p[k]), 6),
                      "hz": round(refine_hz(c, SR, int(model.classes_[k])), 4)})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"sample_rate": SR, "items": items}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/tmp/pitch_data.npz")
    ap.add_argument("--report")
    ap.add_argument("--export")
    ap.add_argument("--fixture")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    d = np.load(a.data)
    X, y, groups, inst, raw, cond = d["X"], d["y"], d["groups"], d["inst"], d["raw"], d["cond"]

    # Ch.2: 20% bản thu để làm bộ test, không bao giờ dùng lúc train hay chọn tham số.
    tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=a.seed).split(X, y, groups))
    pipe = Pipeline([("scale", StandardScaler()),
                     ("mlp", MLPClassifier(max_iter=300, early_stopping=True, random_state=a.seed))])
    grid = {"mlp__hidden_layer_sizes": [(64,), (128,), (128, 64), (192, 96)], "mlp__alpha": [1e-4, 1e-2]}
    t0 = time.time()
    search = GridSearchCV(pipe, grid, cv=GroupKFold(n_splits=4), n_jobs=-1, return_train_score=True)
    search.fit(X[tr], y[tr], groups=groups[tr])
    best = search.best_estimator_
    train_s = time.time() - t0

    m_all, yin_all = model_midi(best, X[te]), yin_midi(raw[te])
    bg = y[te] == 0
    # Khung không có nốt: trả lời bất kỳ nốt nào là "báo nhầm" (người học chưa đàn mà máy đã ghi nốt).
    false_alarm = {"model": (m_all[bg] >= 0).mean(), "yin": (yin_all[bg] >= 0).mean(),
                   "hyb": (np.where(yin_all[bg] >= 0, yin_all[bg], m_all[bg]) >= 0).mean(), "n": int(bg.sum())}
    te = te[~bg]
    m_te, yin_te = m_all[~bg], yin_all[~bg]
    # Kết hợp: YIN trả lời thì dùng YIN (rất chính xác khi chắc chắn), YIN bỏ qua thì hỏi model.
    hyb_te = np.where(yin_te >= 0, yin_te, m_te)
    s_model, s_yin, s_hyb = scores(m_te, y[te]), scores(yin_te, y[te]), scores(hyb_te, y[te])
    per_cond = [(c, int((cond[te] == c).sum()), scores(m_te[cond[te] == c], y[te][cond[te] == c]),
                 scores(yin_te[cond[te] == c], y[te][cond[te] == c]), scores(hyb_te[cond[te] == c], y[te][cond[te] == c]))
                for c in COND_ORDER if (cond[te] == c).any()]
    train_acc = (best.predict(X[tr]) == y[tr]).mean()

    # Phép thử khó: train lại (tham số tốt nhất) khi giấu cello, test trên cello.
    hold = inst == "cello"
    # (khung nền vẫn ở lại train; cello chỉ có khung có nốt)
    held = Pipeline([("scale", StandardScaler()), ("mlp", MLPClassifier(max_iter=300, early_stopping=True, random_state=a.seed,
                     **{k.split("__")[1]: v for k, v in search.best_params_.items()}))]).fit(X[~hold], y[~hold])
    s_hold_m, s_hold_y = scores(model_midi(held, X[hold]), y[hold]), scores(yin_midi(raw[hold]), y[hold])

    per_inst = []
    for k in sorted(set(inst[te])):
        mask = inst[te] == k
        per_inst.append((k, int(mask.sum()), scores(m_te[mask], y[te][mask]), scores(yin_te[mask], y[te][mask])))

    print(f"Model: đúng {pct(s_model['dung'])}, YIN: đúng {pct(s_yin['dung'])}, kết hợp: {pct(s_hyb['dung'])}; train {pct(train_acc)}; tham số {search.best_params_}")
    if a.export:
        export(best, Path(a.export))
    if a.fixture:
        fixture(best, raw[te], y[te], Path(a.fixture))
    if a.report:
        write_report(Path(a.report), a, X, y, groups, inst, tr, te, search, train_acc, train_s, s_model, s_yin, s_hyb, per_cond, false_alarm,
                     s_hold_m, s_hold_y, per_inst, confusion_pc(m_te, y[te]), confusion_pc(yin_te, y[te]))


def write_report(path, a, X, y, groups, inst, tr, te, search, train_acc, train_s, s_model, s_yin, s_hyb, per_cond, false_alarm, s_hold_m, s_hold_y,
                 per_inst, cm_model, cm_yin):
    L = []
    w = L.append
    w("# Kết quả model nhận diện nốt so với YIN (ADR-032 bước 2)\n")
    w(f"Ngày chạy: {dt.date.today().isoformat()}. Lệnh: `python scripts/ai/pitch/du_lieu.py` rồi `python scripts/ai/pitch/train.py "
      f"--seed {a.seed}` (xem đầu file train.py). Máy: container cloud, CPU, scikit-learn.\n")
    w("> Đo trên mẫu nhạc cụ thu sẵn (thư viện CC0/CC BY) và giọng hát tổng hợp, có thêm nhiễu. "
      "**Chưa chứng minh chất lượng với micro thật của người học**: phòng ồn, micro laptop, đàn lệch dây sẽ khác.\n")
    w("## Dữ liệu\n")
    notes = y[y > 0]
    w(f"- {len(y)} khung 2048 mẫu (≈ 43 ms ở 48 kHz), {len(set(groups))} nhóm bản thu, nốt MIDI {notes.min()}–{notes.max()} "
      f"({len(set(notes))} nốt) + lớp 0 \"không có nốt\" ({int((y == 0).sum())} khung ù/ồn).")
    w(f"- Train: {len(tr)} khung / {len(set(groups[tr]))} nhóm. Test (khung có nốt): {len(te)} khung / {len(set(groups[te]))} nhóm "
      "(chia theo bản thu: mọi bản dịch cao độ/thêm nhiễu của một bản thu nằm cùng một phía).")
    w("- Nhạc cụ: " + ", ".join(f"{k} {int((inst == k).sum())}" for k in sorted(set(inst))) + ".")
    w("- Mỗi khung có 5 phiên bản điều kiện thu: " + ", ".join(COND_VI.values()) + ".\n")
    w("## Chọn tham số (GridSearchCV, GroupKFold 4 phần, chỉ trên tập train)\n")
    w("| Lớp ẩn | alpha (L2) | Điểm train | Điểm kiểm định |\n|---|---|---|---|")
    r = search.cv_results_
    for i in np.argsort(-r["mean_test_score"]):
        p = r["params"][i]
        w(f"| {p['mlp__hidden_layer_sizes']} | {p['mlp__alpha']:g} | {pct(r['mean_train_score'][i])} | {pct(r['mean_test_score'][i])} |")
    w(f"\nChọn: `{search.best_params_}`. Thời gian tìm + train: {train_s:.0f} giây.\n")
    w("## Kết quả trên bộ test\n")
    w("| Chỉ số | Model MLP | YIN (thuật toán) | Kết hợp (YIN, YIN bỏ qua thì hỏi model) |\n|---|---|---|---|")
    names = {"dung": "Đúng nốt (đúng cả quãng tám)", "tra_loi": "Có trả lời (không bỏ qua)", "dung_khi_tra_loi": "Đúng khi có trả lời",
             "dung_lop_cao_do": "Đúng tên nốt, bỏ qua quãng tám (cách chấm pitch_class_only)", "nham_quang_tam": "Nhầm quãng tám"}
    for k, label in names.items():
        w(f"| {label} | {pct(s_model[k])} | {pct(s_yin[k])} | {pct(s_hyb[k])} |")
    w(f"| Báo nhầm khi KHÔNG có nốt ({false_alarm['n']} khung ù/ồn) | {pct(false_alarm['model'])} | {pct(false_alarm['yin'])} | {pct(false_alarm['hyb'])} |")
    w(f"\nHọc vẹt (Ch.4): đúng trên train {pct(train_acc)} so với test {pct(s_model['dung'])}.\n")
    w("### Theo điều kiện thu (đúng nốt)\n\n| Điều kiện | Số khung test | Model | YIN | Kết hợp |\n|---|---|---|---|---|")
    for c, n, sm, sy, sh in per_cond:
        w(f"| {COND_VI[c]} | {n} | {pct(sm['dung'])} | {pct(sy['dung'])} | {pct(sh['dung'])} |")
    w("")
    w("### Theo nhạc cụ (đúng nốt)\n\n| Nhạc cụ | Số khung test | Model | YIN |\n|---|---|---|---|")
    for k, n, sm, sy in per_inst:
        w(f"| {k} | {n} | {pct(sm['dung'])} | {pct(sy['dung'])} |")
    w("\n### Phép thử khó: giấu hẳn cello khỏi train\n")
    w(f"Model chưa từng nghe cello: đúng {pct(s_hold_m['dung'])} (trả lời {pct(s_hold_m['tra_loi'])}). "
      f"YIN trên cùng các khung: đúng {pct(s_hold_y['dung'])}.\n")
    for title, cm in (("Model", cm_model), ("YIN", cm_yin)):
        w(f"### Ma trận nhầm lẫn 12 lớp cao độ: {title} (hàng = nốt thật, cột = nốt đoán, — = không trả lời)\n")
        w("| thật \\ đoán | " + " | ".join(PCS) + " | — |\n|" + "---|" * 14)
        for i, row in enumerate(cm):
            w(f"| **{PCS[i]}** | " + " | ".join(str(v) if v else "·" for v in row) + " |")
        w("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()

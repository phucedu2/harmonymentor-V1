"""Chọn ngưỡng bộ định tuyến 4 luồng trên tập dev (ADR-017). Không chọn tay.

    cd backend && python ../scripts/ai/gop_y/hieu_chinh_nguong.py                # tập dev Claude soạn (bản nháp)
    cd backend && python ../scripts/ai/gop_y/hieu_chinh_nguong.py --dev <file>   # tập dev của Phúc khi có

Với mỗi cách truy xuất (bm25, e5 cục bộ), dò lưới (ngưỡng xám, ngưỡng nhận, ngưỡng hướng dẫn) rồi chọn bộ:
  1. đạt cả hai mục tiêu: câu B/C bị trả lời như bài học ≤ 2%, câu A bị từ chối ≤ 5%; trong các bộ đạt, chọn bộ
     đúng luồng nhiều nhất;
  2. không bộ nào đạt: chọn bộ ít lỗi nhất, lỗi "trả lời sai" nặng gấp đôi "từ chối sai" (nghiêng về không biết).
Ghi kết quả vào backend/app/ai/tutor/router_thresholds.json kèm tên tập dev và số đo để truy vết.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
DEV = ROOT / "scripts" / "ai" / "data" / "router_dev.json"
GD2_DEV = ROOT / "scripts" / "ai" / "data" / "gd2" / "dev.json"
EXTRA_MODEL_DIRS = [ROOT / "backend" / "models" / "multilingual-e5-small-hm", ROOT / "backend" / "models" / "multilingual-e5-small-hm-gd2c"]
OUT = ROOT / "backend" / "app" / "ai" / "tutor" / "router_thresholds.json"
FIXED = {"greet_conf": 0.5, "help_conf": 0.45, "oos_conf": 0.5, "music_min": 0.3}
FLOWS = ("A", "B", "C", "D", "G")
# Khoảng hơn điểm (cosine) để đoạn bài thắng mục hướng dẫn; 1.0 = tắt luật. BM25 hai kho khác thang nên luôn tắt.
MARGINS = (0.0, 0.01, 0.02, 0.03, 0.05, 1.0)


_EMB: dict[str, object] = {"bm25": None}


def embedders() -> dict[str, object]:
    from app.ai.local_embedder import get_local_embedder
    from app.ai.tutor.router import method_key

    out = {"bm25": None}
    # Mô hình đang cấu hình (LOCAL_EMBED_DIR) + các thư mục mô hình khác đã có trên máy (bản gốc, bản fine-tune GĐ2b),
    # để một lần chạy ghi ngưỡng cho mọi bản và đổi bản không cần chạy lại.
    from app.ai.local_embedder import DEFAULT_DIR, model_dir
    for path in dict.fromkeys([model_dir(), DEFAULT_DIR, *EXTRA_MODEL_DIRS]):
        e = get_local_embedder(path)
        if e is not None:
            out[method_key(e)] = e
    _EMB.update(out)
    return out


def load_items(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["items"]


def score(router, items, sigs, table) -> dict:
    """Chạy route() với bảng ngưỡng cho trước, trả ma trận nhầm lẫn và các tỉ lệ lỗi."""
    conf = {t: {p: 0 for p in FLOWS} for t in FLOWS}
    wrong_answer = refused = a_mislabel = 0
    rows = []
    for it, sig in zip(items, sigs):
        dec = router.route(sig, table)
        conf[it["flow"]][dec.flow] += 1
        t = it["flow"]
        if t in ("B", "C") and dec.flow == "A":
            wrong_answer += 1
        if t == "C" and dec.flow == "B" and dec.kind == "engine":
            wrong_answer += 1
        if t == "A" and (dec.flow in ("C", "D", "G") or (dec.flow == "B" and dec.kind == "unknown")):
            refused += 1
        if t == "A" and dec.flow == "B" and dec.kind == "engine":
            a_mislabel += 1
        rows.append({"q": it["q"], "true": t, "pred": dec.flow, "kind": dec.kind, "reason": dec.reason})
    n_bc = sum(1 for it in items if it["flow"] in ("B", "C")) or 1
    n_a = sum(1 for it in items if it["flow"] == "A") or 1
    correct = sum(conf[t][t] for t in FLOWS)
    per = {}
    for f in FLOWS:
        tp = conf[f][f]
        pred = sum(conf[t][f] for t in FLOWS)
        true = sum(conf[f].values())
        per[f] = {"precision": round(tp / pred, 3) if pred else None, "recall": round(tp / true, 3) if true else None,
                  "n": true}
    return {"accuracy": round(correct / len(items), 4), "bc_answered_wrong": round(wrong_answer / n_bc, 4),
            "a_refused_wrong": round(refused / n_a, 4), "a_engine_instead_of_lesson": round(a_mislabel / n_a, 4),
            "confusion": conf, "per_flow": per, "rows": rows}


def _thin(values: list[float], k: int) -> list[float]:
    """Giữ tối đa k điểm thật, rải đều theo thứ hạng (phân vị). Tập dev GĐ2 có vài trăm điểm khác nhau; dò hết
    tổ hợp thì hàng chục triệu lượt. Vẫn là điểm thật trên dev, không phải số tròn chọn tay."""
    if len(values) <= k:
        return values
    return sorted({values[round(i * (len(values) - 1) / (k - 1))] for i in range(k)})


def calibrate(router, items, emb) -> tuple[dict, dict]:
    sigs = [router.gather(it["q"], emb) for it in items]
    # Ngưỡng ứng viên = các điểm thật xuất hiện trên tập dev, không phải số tròn chọn tay.
    # Làm tròn (cosine 3 chữ số, BM25 1 chữ số) để lưới đủ mịn mà chạy vài phút.
    nd = 3 if emb is not None else 1
    lesson = _thin(sorted({round(s.lesson.best_score, nd) for s in sigs if s.lesson.hits}), 40)
    helps = _thin(sorted({round(s.help.best_score, nd) for s in sigs if s.help.hits}), 25)
    best_key, best = None, None
    for gray, accept in itertools.combinations_with_replacement(lesson, 2):
        for h, margin in itertools.product(helps, MARGINS if emb is not None else (1.0,)):
            table = {**FIXED, "lesson_gray": gray, "lesson_accept": accept, "help_accept": h, "help_margin": margin}
            m = score(router, items, sigs, table)
            ok = m["bc_answered_wrong"] <= 0.02 and m["a_refused_wrong"] <= 0.05
            # Đạt mục tiêu: lấy bộ đúng nhiều nhất. Không đạt: lỗi trả lời sai nặng gấp đôi từ chối sai.
            # Hòa thì chọn ngưỡng nhận cao hơn (bảo thủ).
            key = (ok, m["accuracy"] if ok else -(2 * m["bc_answered_wrong"] + m["a_refused_wrong"]),
                   m["accuracy"], -m["bc_answered_wrong"], accept, gray, margin)
            if best_key is None or key > best_key:
                best_key, best = key, (table, m)
    return best


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", type=Path, nargs="+", default=[DEV, GD2_DEV],
                    help="một hay nhiều file dev, gộp lại (mặc định: dev GĐ1 + dev GĐ2)")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    from app.ai.tutor import router
    items = [it for p in args.dev for it in load_items(p)]
    names = [str(p.resolve().relative_to(ROOT)) if p.resolve().is_relative_to(ROOT) else str(p) for p in args.dev]
    result = {"note": "Do scripts/ai/gop_y/hieu_chinh_nguong.py chọn trên tập dev, không sửa tay (ADR-017).",
              "dev_set": " + ".join(names),
              "dev_size": len(items), "date": date.today().isoformat(), "thresholds": {}, "dev_metrics": {}}
    for key, emb in embedders().items():
        table, m = calibrate(router, items, emb)
        result["thresholds"][key] = {k: round(v, 4) for k, v in table.items()}
        result["dev_metrics"][key] = {k: v for k, v in m.items() if k != "rows"}
        print(f"{key}: {result['thresholds'][key]}")
        print(f"   accuracy {m['accuracy']}, B/C trả lời sai {m['bc_answered_wrong']}, A từ chối sai "
              f"{m['a_refused_wrong']}, A sang Engine {m['a_engine_instead_of_lesson']}")
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Đã ghi {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

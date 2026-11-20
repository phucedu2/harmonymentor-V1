"""Đo bộ định tuyến 4 luồng (ADR-017): ma trận nhầm lẫn, precision/recall từng luồng, 2 chỉ số mục tiêu.

    cd backend && python ../scripts/ai/gop_y/danh_gia_dinh_tuyen.py                     # bộ đo mặc định (dưới)
    cd backend && python ../scripts/ai/gop_y/danh_gia_dinh_tuyen.py --set <file.json>   # tập test khóa Đạt + Thắng

Bộ đo mặc định là các câu KHÔNG dùng để chọn ngưỡng hay viết luật: bộ chuẩn GĐ4 (30 câu A, 10 câu ngoài phạm vi,
10 câu tấn công) và 24 câu dò GĐ0. Cả hai do Claude soạn, nên con số chỉ là ước lượng; số chính thức lấy trên tập
test khóa do người viết (quyết định 11A).

Mục tiêu (đề GĐ1): câu B/C bị trả lời như bài học ≤ 2%; câu A bị từ chối sai ≤ 5%.
Câu tấn công đi qua bộ lọc injection trước, giống dịch vụ thật.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hieu_chinh_nguong import FLOWS, embedders, score  # noqa: E402

GOLD = ROOT / "scripts" / "ai" / "data" / "rag_gold.json"
PROBE = ROOT / "scripts" / "ai" / "data" / "gd0_cau_do_luong.json"


# Câu dò GĐ0 soạn trước khi chốt định nghĩa luồng. Theo quyết định 7A ("câu nhạc lý kho có đoạn dạy → A"), 3 câu
# dưới hỏi một trường hợp cụ thể của khái niệm kho ĐÃ dạy (quãng ở L01, âm giai trưởng và số La Mã ở L02), nên là
# A kèm dữ kiện Engine, không phải B. Sửa nhãn ở đây, có lý do, không sửa file GĐ0 đã nộp.
RELABEL = {"P-B02": "A", "P-B03": "A", "P-B04": "A"}


def default_set() -> list[dict]:
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    items = [{"q": x["q"], "flow": "A", "src": "gd4_concept"} for x in gold["concept"]]
    items += [{"q": q, "flow": "C", "src": "gd4_out_of_scope"} for q in gold["out_of_scope"]]
    items += [{"q": q, "flow": "C", "src": "gd4_attack"} for q in gold["attacks"]]
    items += [{"q": x["q"], "flow": RELABEL.get(x["id"], x["flow"]), "src": "gd0_probe"} for x in probe["items"]]
    return items


class _Injected:
    """Kết quả giả cho câu bị bộ lọc injection chặn: luồng C, như answer_question."""
    flow, kind, reason = "C", "refuse", "injection"


def evaluate(items: list[dict], emb, table) -> dict:
    from app.ai.tutor import router
    from app.ai.tutor.injection import looks_like_injection

    sigs = [None if looks_like_injection(it["q"]) else router.gather(it["q"], emb) for it in items]

    class _R:
        @staticmethod
        def route(sig, th):
            return _Injected() if sig is None else router.route(sig, th)

    return score(_R, items, sigs, table)


def to_markdown(name: str, m: dict) -> str:
    lines = [f"### {name}", "", f"Đúng luồng {m['accuracy']:.1%} · B/C bị trả lời như bài học "
             f"{m['bc_answered_wrong']:.1%} (mục tiêu ≤ 2%) · A bị từ chối sai {m['a_refused_wrong']:.1%} "
             f"(mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài {m['a_engine_instead_of_lesson']:.1%}", "",
             "| thật \\ đoán | " + " | ".join(FLOWS) + " | recall |", "|---" * (len(FLOWS) + 2) + "|"]
    for t in FLOWS:
        row = m["confusion"][t]
        if not sum(row.values()):
            continue
        rec = m["per_flow"][t]["recall"]
        lines.append(f"| **{t}** | " + " | ".join(str(row[p]) for p in FLOWS) + f" | {rec:.0%} |")
    prec = [m["per_flow"][f]["precision"] for f in FLOWS]
    lines.append("| precision | " + " | ".join("–" if p is None else f"{p:.0%}" for p in prec) + " | |")
    wrong = [r for r in m["rows"] if r["true"] != r["pred"]]
    if wrong:
        lines += ["", "Câu sai luồng:", ""]
        lines += [f"- {r['true']}→{r['pred']} ({r['reason']}): {r['q']}" for r in wrong]
    return "\n".join(lines)


def main(argv=None) -> int:
    from app.ai.tutor import router

    ap = argparse.ArgumentParser()
    ap.add_argument("--set", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    items = json.loads(args.set.read_text(encoding="utf-8"))["items"] if args.set else default_set()
    table = router.thresholds()
    report, md = {"set": str(args.set) if args.set else "mac_dinh(gd4+gd0)", "n": len(items), "results": {}}, []
    for key, emb in embedders().items():
        m = evaluate(items, emb, table.get(key) or table["bm25"])
        report["results"][key] = m
        md.append(to_markdown(key, m))
    text = "\n\n".join(md)
    print(text)
    if args.out:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        args.out.with_suffix(".md").write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Kiểm trùng giữa các tập dữ liệu định tuyến (ADR-017): train, dev, test không được chung câu.

    cd backend && python ../scripts/ai/gop_y/kiem_trung_du_lieu.py [--test <tập test khóa>]

Trùng = giống hệt sau khi bỏ dấu, chữ hoa, dấu câu; gần trùng = Jaccard 3-gram ký tự ≥ 0,8. Câu gần trùng giữa
train và dev/test làm số đo đẹp giả, nên script trả mã lỗi 1 khi có. Bộ chuẩn GĐ4 (rag_gold) cũng được so vì nó là
bộ đo không dùng để chỉnh. Test pytest gọi hàm find_overlaps để CI chặn.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTE = ROOT / "backend" / "app" / "ai" / "tutor" / "route_data.json"
DEV = ROOT / "scripts" / "ai" / "data" / "router_dev.json"
GOLD = ROOT / "scripts" / "ai" / "data" / "rag_gold.json"
HELP = ROOT / "backend" / "app" / "content" / "help" / "help_entries.json"
NEAR = 0.8


def norm(text: str) -> str:
    t = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    return " ".join(re.findall(r"[a-z0-9#]+", t))


def grams(text: str) -> set[str]:
    t = f" {norm(text)} "
    return {t[i:i + 3] for i in range(len(t) - 2)}


def sets(test: Path | None = None) -> dict[str, list[str]]:
    route = json.loads(ROUTE.read_text(encoding="utf-8"))
    out = {"route_train": [q for rows in route["train"].values() for q in rows],
           "route_dev": [q for rows in route["dev"].values() for q in rows],
           "router_dev": [it["q"] for it in json.loads(DEV.read_text(encoding="utf-8"))["items"]]}
    help_kb = json.loads(HELP.read_text(encoding="utf-8"))
    out["help_hints"] = [q for e in help_kb["entries"] for q in e.get("hoi", [])]
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    out["gd4_gold"] = [x["q"] for x in gold["concept"]] + gold["out_of_scope"] + gold["attacks"]
    if test:
        out["test"] = [it["q"] for it in json.loads(test.read_text(encoding="utf-8"))["items"]]
    return out


def find_overlaps(data: dict[str, list[str]]) -> list[dict]:
    """Cặp câu trùng/gần trùng giữa train và mọi tập đánh giá, và giữa các tập đánh giá với nhau."""
    names = list(data)
    found = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ga = [(q, grams(q), norm(q)) for q in data[a]]
            gb = [(q, grams(q), norm(q)) for q in data[b]]
            for (qa, sa, na), (qb, sb, nb) in product(ga, gb):
                if na == nb:
                    found.append({"a": a, "b": b, "qa": qa, "qb": qb, "kind": "exact"})
                elif sa and sb and len(sa & sb) / len(sa | sb) >= NEAR:
                    found.append({"a": a, "b": b, "qa": qa, "qb": qb, "kind": "near"})
    return found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", type=Path)
    args = ap.parse_args(argv)
    data = sets(args.test)
    for name, rows in data.items():
        dup = len(rows) - len({norm(q) for q in rows})
        print(f"{name}: {len(rows)} câu, trùng trong tập {dup}")
    found = find_overlaps(data)
    for f in found:
        print(f"{f['kind']:5} {f['a']} × {f['b']}: {f['qa']!r} ~ {f['qb']!r}")
    print("Không có câu trùng giữa các tập." if not found else f"{len(found)} cặp trùng/gần trùng.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())

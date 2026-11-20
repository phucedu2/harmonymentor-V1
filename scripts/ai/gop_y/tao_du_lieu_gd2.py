"""Sinh tập train / dev / test tạm GĐ2 từ câu gốc (gd2_cau_goc.py), tất định (seed cố định), không gọi mạng.

    cd backend && python ../scripts/ai/gop_y/tao_du_lieu_gd2.py

Cách làm (quyết định GĐ2 1A–5A, 07/11/2026):
1. Bung mẫu "t" + tham số "p" thành câu; nhóm câu tự do "q" dài được cắt thành nhóm con 4 câu (các câu khác ý nhau,
   không phải diễn đạt lại của nhau) để tách tập đều hơn.
2. Tách THEO NHÓM, phân tầng theo luồng: khoảng 64% nhóm vào train, 18% dev, 18% test tạm. Một mẫu chỉ ở một tập.
3. Biến thể kiểu người học (không dấu, gõ tắt, chữ thường, lỗi gõ, thêm lời gọi): train lấy câu gốc + biến thể,
   dev/test lấy câu gốc hoặc một biến thể (ngẫu nhiên, 50/50) và thêm một biến thể khác, để đo cả câu "bẩn".
4. Kiểm nhãn tự động: mã bài A có trong kho; mục hướng dẫn D có thật; nhóm B bài sau khớp router.later_lesson;
   ghi dữ kiện Engine cho câu B. Chỗ lệch được ghi vào báo cáo để người duyệt xem, KHÔNG tự sửa nhãn cho khớp router.
5. Ghi:
   scripts/ai/data/gd2/{train,dev,test_tam}.json        (mọi trường, để duyệt và đo)
   backend/app/ai/tutor/route_data_gd2.json             (câu train theo nhãn tầng 1, backend đọc lúc chạy)
   scripts/ai/data/gd2/kiem_nhan.md                     (báo cáo kiểm nhãn)
"""

from __future__ import annotations

import json
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gd2_cau_goc import GROUPS  # noqa: E402

OUT_DIR = ROOT / "scripts" / "ai" / "data" / "gd2"
ROUTE_GD2 = ROOT / "backend" / "app" / "ai" / "tutor" / "route_data_gd2.json"
SEED = 20261107
SPLIT = {"train": 0.64, "dev": 0.18, "test_tam": 0.18}
TIER1 = {"A": "nhac_ly", "B": "nhac_ly", "C": "ngoai_pham_vi", "D": "huong_dan", "G": "chao_hoi"}
SUBGROUP = 4
NOTE_AUTHOR = ("Claude viết 07/11/2026, đóng vai người học (quyết định GĐ2 2A), không dùng Gemini (4A). "
               "KHÔNG phải tập test chính thức: số chính thức lấy trên phiếu do Đạt/Thắng/Phúc viết (1A).")


# ───────────── biến thể kiểu người học ─────────────
def bo_dau(s: str) -> str:
    t = unicodedata.normalize("NFD", s).replace("đ", "d").replace("Đ", "D")
    return unicodedata.normalize("NFC", "".join(ch for ch in t if unicodedata.category(ch) != "Mn"))


_TEEN = [(r"\bkhông\b", "ko"), (r"\bgì\b", "j"), (r"\bvậy\b", "v"), (r"\bđược\b", "đc"), (r"\bmình\b", "mik"),
         (r"\bnhư thế nào\b", "ntn"), (r"\bbao nhiêu\b", "bn"), (r"\bthế nào\b", "sao"), (r"\bvới\b", "vs"),
         (r"\bnhững\b", "nhg"), (r"\bphải\b", "fai"), (r"\bcảm ơn\b", "cmon")]
_GOI = ["cho mình hỏi ", "bạn ơi ", "ad ơi ", "thầy ơi cho em hỏi ", "hỏi ngu tí: ", "em hỏi xíu "]
_DUOI = [" ạ", " vậy ạ", "???", " với", " nhỉ", " ạ?"]


def teen(s: str, rng: random.Random) -> str:
    out = s
    for pat, rep in _TEEN:
        if rng.random() < 0.8:
            out = re.sub(pat, rep, out, flags=re.IGNORECASE)
    return out


def loi_go(s: str, rng: random.Random) -> str:
    """Một lỗi gõ nhẹ ở một từ dài (≥ 4 ký tự, không phải ký hiệu nhạc): mất một chữ hoặc đảo hai chữ kề."""
    words = s.split()
    idx = [i for i, w in enumerate(words) if len(w) >= 4 and w.isalpha() and w.islower()]
    if not idx:
        return s
    i = rng.choice(idx)
    w = words[i]
    j = rng.randrange(1, len(w) - 1)
    words[i] = w[:j] + w[j + 1:] if rng.random() < 0.5 else w[:j] + w[j + 1] + w[j] + w[j + 2:]
    return " ".join(words)


STYLES = {
    "khong_dau": lambda s, r: bo_dau(s),
    "go_tat": teen,
    "chu_thuong": lambda s, r: s.lower(),
    "loi_go": loi_go,
    "loi_goi": lambda s, r: r.choice(_GOI) + s + r.choice(_DUOI),
    "khong_dau_go_tat": lambda s, r: bo_dau(teen(s, r)),
}


def variant(q: str, style: str, rng: random.Random) -> str:
    v = STYLES[style](q, rng)
    return v if v.strip() else q


# ───────────── bung nhóm ─────────────
def expand() -> list[dict]:
    """Mỗi phần tử: một nhóm (đơn vị tách tập) với danh sách câu gốc."""
    out = []
    for g in GROUPS:
        meta = {k: g[k] for k in ("flow", "lesson", "help", "expect") if k in g}
        if "t" in g:
            qs = [g["t"].format(*p) for p in g["p"]]
            out.append({"id": g["id"], **meta, "qs": qs})
        else:
            qs = g["q"]
            for k in range(0, len(qs), SUBGROUP):
                out.append({"id": f"{g['id']}#{k // SUBGROUP}", **meta, "qs": qs[k:k + SUBGROUP]})
    return out


def split_groups(groups: list[dict], rng: random.Random) -> dict[str, list[dict]]:
    by_flow = defaultdict(list)
    for g in groups:
        by_flow[g["flow"]].append(g)
    out = {k: [] for k in SPLIT}
    for flow in sorted(by_flow):
        gs = sorted(by_flow[flow], key=lambda g: g["id"])
        rng.shuffle(gs)
        # Chia theo SỐ CÂU chứ không theo số nhóm, để luồng ít câu (G) vẫn có đủ câu ở dev/test.
        total = sum(len(g["qs"]) for g in gs)
        got = {"dev": 0, "test_tam": 0}
        for g in gs:
            dest = next((k for k in ("dev", "test_tam") if got[k] < total * SPLIT[k]), "train")
            out[dest].append(g)
            if dest != "train":
                got[dest] += len(g["qs"])
    return out


def items_for(split: str, groups: list[dict], rng: random.Random) -> list[dict]:
    rows = []
    styles = list(STYLES)
    for g in groups:
        base = {k: g[k] for k in ("flow", "lesson", "help", "expect") if k in g}
        for q in g["qs"]:
            picks = rng.sample(styles, 2)
            if split == "train":
                forms = [("goc", q)] + [(s, variant(q, s, rng)) for s in picks]
            else:
                first = ("goc", q) if rng.random() < 0.5 else (picks[0], variant(q, picks[0], rng))
                forms = [first, (picks[1], variant(q, picks[1], rng))]
            seen = set()
            for style, text in forms:
                key = text.strip(" ?.!")   # câu không dấu là biến thể khác, giữ lại
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"q": text, **base, "group": g["id"], "style": style, "base": q})
    return rows


# ───────────── bỏ câu trùng với các tập đã có ─────────────
def drop_overlaps(data: dict[str, list[dict]]) -> tuple[dict[str, list[dict]], list[str]]:
    """Bỏ mọi biến thể của một câu gốc nếu BẤT KỲ biến thể nào trùng/gần trùng (cùng tiêu chí kiem_trung_du_lieu.py)
    với các tập đã có (train/dev GĐ1, bộ chuẩn GĐ4, gợi ý kho hướng dẫn) hoặc với tập GĐ2 xếp trước
    (train → dev → test tạm). Bỏ cả nhóm câu gốc để không còn biến thể "lọt" sang tập khác."""
    from kiem_trung_du_lieu import NEAR, grams, norm, sets

    seen = [(norm(q), grams(q)) for name, rows in sets().items() if not name.startswith("gd2_") for q in rows]
    probe = json.loads((ROOT / "scripts" / "ai" / "data" / "gd0_cau_do_luong.json").read_text(encoding="utf-8"))
    seen += [(norm(x["q"]), grams(x["q"])) for x in probe["items"]]

    def hit(text: str) -> bool:
        n, g = norm(text), grams(text)
        return any(n == sn or (g and sg and len(g & sg) / len(g | sg) >= NEAR) for sn, sg in seen)

    out, dropped = {}, []
    for name in ("train", "dev", "test_tam"):
        by_base = defaultdict(list)
        for r in data[name]:
            by_base[r["base"]].append(r)
        keep = []
        for base, rows in by_base.items():
            if any(hit(r["q"]) for r in rows):
                dropped.append(f"{name}: {base}")
                continue
            keep += rows
        out[name] = keep
        seen += [(norm(r["q"]), grams(r["q"])) for r in keep]
    return out, dropped


# ───────────── kiểm nhãn tự động ─────────────
def check_labels(rows: list[dict]) -> list[str]:
    from app.ai.tutor.engine_query import engine_answer
    from app.ai.tutor.retriever import help_base, knowledge_base
    from app.ai.tutor.router import later_lesson

    kb_lessons = {c.lesson_id for c in knowledge_base()}
    help_titles = {c.title for c in help_base()}
    notes = []
    for r in rows:
        if r["style"] != "goc":
            continue
        if r["flow"] == "A" and r.get("lesson") not in kb_lessons:
            notes.append(f"A nhưng bài {r.get('lesson')} không có trong kho: {r['q']}")
        if r["flow"] == "D" and r.get("help") not in help_titles:
            notes.append(f"D trỏ mục hướng dẫn không có: {r.get('help')!r}: {r['q']}")
        if r["flow"] == "B" and r.get("lesson") in {"L05", "L06", "L07", "L08"}:
            got = later_lesson(r["q"])
            if got != r["lesson"]:
                notes.append(f"B-{r['lesson']} nhưng luật bài sau thấy {got}: {r['q']}")
        if r["flow"] == "B":
            eng = engine_answer(r["q"])
            r["engine"] = [{"tool": f["tool"], "args": f["args"], "result": f["result"]} for f in eng.facts] or None
            if eng.unknown:
                r["engine_unknown"] = eng.unknown
    return notes


def relabel(data: dict[str, list[dict]]) -> None:
    """Câu B "bài sau" của bài nay đã vào kho thì đúng luồng là A. Đổi nhãn SAU khi chia tập để không câu nào đổi
    tập. Lý do đổi là nội dung kho thay đổi (L05 phát hành 07/11/2026), không phải kết quả đo."""
    from app.ai.tutor.engine_query import engine_answer
    from app.ai.tutor.retriever import knowledge_base

    kb_lessons = {c.lesson_id for c in knowledge_base()}
    for rows in data.values():
        for r in rows:
            if r["flow"] == "B" and r.get("lesson") in kb_lessons:
                r["flow"], r["relabel"] = "A", f"B→A: {r['lesson']} đã vào kho"
                r.pop("expect", None)
            # ADR-019 (11/11/2026): Engine hỗ trợ hợp âm 9/13, L07 dạy tension 9/13 và đã vào kho. Nhóm này ghi
            # "Engine chưa hỗ trợ" từ trước; chỉ đổi các câu mà Engine nay đọc được (không đổi nhóm để giữ cách chia tập).
            if r.get("group") == "B-chord-mo-rong" and "L07" in kb_lessons and not engine_answer(r["q"]).unknown:
                r["flow"], r["lesson"], r["relabel"] = "A", "L07", "B→A: Engine hỗ trợ từ ADR-019, L07 đã vào kho"
                r.pop("expect", None)


def main() -> int:
    rng = random.Random(SEED)
    groups = expand()
    parts = split_groups(groups, rng)
    data = {name: items_for(name, gs, rng) for name, gs in parts.items()}
    data, dropped = drop_overlaps(data)
    relabel(data)
    # Gán dữ kiện Engine cho mọi dòng B (cả biến thể) qua câu gốc.
    all_rows = [r for rows in data.values() for r in rows]
    notes = check_labels(all_rows)
    eng_by_base = {r["base"]: (r.get("engine"), r.get("engine_unknown")) for r in all_rows if r["style"] == "goc"}
    for r in all_rows:
        if r["flow"] == "B" and r["style"] != "goc" and r["base"] in eng_by_base:
            e, u = eng_by_base[r["base"]]
            if e:
                r["engine"] = e
            if u:
                r["engine_unknown"] = u

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    purpose = {"train": "Train tầng 1 và fine-tune e5 (GĐ2b).",
               "dev": "Chọn ngưỡng (hieu_chinh_nguong.py) và chọn mô hình fine-tune. Không train trên tập này.",
               "test_tam": "Test TẠM: chỉ đo, không chỉnh gì trên tập này. Số chính thức chờ phiếu nhóm."}
    summary = {}
    for name, rows in data.items():
        payload = {"note": f"{purpose[name]} {NOTE_AUTHOR}", "author": "claude", "status": "draft",
                   "seed": SEED, "groups": sorted({r["group"] for r in rows}), "items": rows}
        (OUT_DIR / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                                              encoding="utf-8")
        summary[name] = {"n": len(rows), "groups": len(payload["groups"]),
                         "flow": dict(sorted(Counter(r["flow"] for r in rows).items())),
                         "style": dict(sorted(Counter(r["style"] for r in rows).items()))}

    tier1 = {lab: [] for lab in ("nhac_ly", "huong_dan", "chao_hoi", "ngoai_pham_vi")}
    for r in data["train"]:
        tier1[TIER1[r["flow"]]].append(r["q"])
    ROUTE_GD2.write_text(json.dumps(
        {"note": "Câu train tầng 1 GĐ2 (sinh bởi scripts/ai/gop_y/tao_du_lieu_gd2.py, không sửa tay). "
                 "route_classifier gộp với route_data.json. " + NOTE_AUTHOR,
         "author": "claude", "status": "draft", "train": tier1,
         "a_rows": [r["q"] for r in data["train"] if r["flow"] == "A"]}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")

    md = ["# Kiểm nhãn tự động GĐ2", "", "Sinh bởi `scripts/ai/gop_y/tao_du_lieu_gd2.py`. " + NOTE_AUTHOR, "",
          "| Tập | Câu | Nhóm | Theo luồng | Theo kiểu |", "|---|---|---|---|---|"]
    for name, s in summary.items():
        md.append(f"| {name} | {s['n']} | {s['groups']} | {s['flow']} | {s['style']} |")
    md += ["", f"Lệch nhãn cần người xem: {len(notes)}", ""] + [f"- {n}" for n in notes]
    md += ["", f"Câu gốc bị bỏ vì trùng/gần trùng tập khác: {len(dropped)}", ""] + [f"- {d}" for d in dropped]
    (OUT_DIR / "kiem_nhan.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print(f"Lệch nhãn: {len(notes)}; bỏ vì trùng: {len(dropped)}")
    for n in notes:
        print(" -", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

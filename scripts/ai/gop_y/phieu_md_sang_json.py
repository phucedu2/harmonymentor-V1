"""Chuyển bảng phiếu câu hỏi nhóm tự viết (Markdown) sang JSON cho danh_gia_dinh_tuyen.py / hieu_chinh_nguong.py.

    cd backend
    python ../scripts/ai/gop_y/phieu_md_sang_json.py <phieu.md> --nguoi Phuc  --vai-tro dev  --out ../docs/giai-doan/ai-gop-y/phieu-cau-hoi/phieu_Phuc_dev.json
    python ../scripts/ai/gop_y/phieu_md_sang_json.py <phieu.md> --nguoi Dat   --vai-tro test --out <thư mục riêng của Thắng>/phieu_Dat_test.json

Đọc bảng (mẫu PHIEU_TU_VIET_CAU_HOI.md) nằm dưới tiêu đề "## ... <tên>" (tên không dấu: Phuc, Dat, Thang). Dòng bảng: | # | flow | câu hỏi | bài | ghi chú |.
Dừng với lỗi nếu còn ô câu hỏi trống, flow lạ, hoặc câu trùng: phiếu thiếu thì không đo, tránh số đẹp giả.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

FLOWS = set("ABCDG")


def _plain(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower()).replace("đ", "d")
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def read_table(text: str, nguoi: str) -> list[dict]:
    """Các dòng bảng của phần có tiêu đề '## ' chứa tên người viết."""
    rows, inside = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = _plain(nguoi) in _plain(line)
            continue
        if not inside or not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # STT dạng "7" hoặc "P07"/"Đ07"/"T07" (mẫu PHIEU_TU_VIET_CAU_HOI.md); bỏ dòng tiêu đề và dòng ---
        m = re.fullmatch(r"[A-Za-zĐđ]?(\d+)", cells[0]) if len(cells) >= 3 else None
        if not m:
            continue
        rows.append({"so": int(m[1]), "flow": cells[1].upper(), "q": cells[2],
                     "bai": cells[3] if len(cells) > 3 else "", "ghi_chu": cells[4] if len(cells) > 4 else ""})
    return rows


def check(rows: list[dict]) -> list[str]:
    errs, seen = [], set()
    for r in rows:
        if r["flow"] not in FLOWS:
            errs.append(f"câu {r['so']}: flow '{r['flow']}' không thuộc A/B/C/D/G")
        if not r["q"]:
            errs.append(f"câu {r['so']}: chưa viết câu hỏi")
        key = _plain(r["q"])
        if key and key in seen:
            errs.append(f"câu {r['so']}: trùng câu trước")
        seen.add(key)
    if not rows:
        errs.append("không tìm thấy bảng của người này")
    return errs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("md", type=Path)
    ap.add_argument("--nguoi", required=True)
    ap.add_argument("--vai-tro", choices=["dev", "test"], required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    rows = read_table(a.md.read_text(encoding="utf-8"), a.nguoi)
    errs = check(rows)
    if errs:
        print("\n".join(errs), file=sys.stderr)
        return 1
    data = {"nguoi_viet": a.nguoi, "vai_tro": a.vai_tro, "ngay": date.today().isoformat(), "status": "nhom_tu_viet",
            "ghi_chu": f"Chuyển từ {a.md.name} bằng phieu_md_sang_json.py",
            "items": [{"flow": r["flow"], "q": r["q"], "bai": r["bai"], "ghi_chu": r["ghi_chu"]} for r in rows]}
    a.out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    count = {f: sum(r["flow"] == f for r in rows) for f in "ABCDG"}
    print(f"Đã ghi {a.out}: {len(rows)} câu {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

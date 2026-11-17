"""Dựng bộ logo bản "Sân khấu" (ADR-026) từ bộ Đồng & Gỉ trong logo/.

Vì sao thay màu thay vì dựng lại từ build.js: bộ gốc cần npm + tải font + cairosvg.
Ở đây chỉ đổi màu vỏ/chữ/viền; 12 màu nốt và vị trí lỗ giữ nguyên (BRAND_NOTE luật 2).
Chạy: python3 docs/thuong-hieu/_nguon/san_khau.py   (từ gốc repo)
"""
import pathlib, re, shutil

GOC = pathlib.Path(__file__).resolve().parent.parent
SRC, DST = GOC / "logo", GOC / "logo" / "san-khau"
NOTE = {"#3CC3AB", "#28BFD2", "#58B5ED", "#8AA8F7", "#B49AED", "#D48FD1",
        "#E78AAA", "#ED8C80", "#E3975A", "#CAA647", "#A4B558", "#73C07F"}

# Bảng thay theo biến thể file (cùng một mã màu có vai khác nhau ở bản sáng/tối/đơn sắc)
MAP = {
    "sang":  {"#0C231F": "#17142B", "#F2F3EA": "#F4F2F8"},
    "toi":   {"#F2F3EA": "#ECEBF5", "#101F1C": "#1A1630", "#45C2AB": "#F2B33D", "#081613": "#0E0C1B"},
    "den":   {"#0C231F": "#17142B"},
    "trang": {"#F2F3EA": "#ECEBF5", "#0C231F": "#17142B"},
}

def bien_the(ten):
    for k in ("toi", "den", "trang"):
        if ten.endswith("-" + k):
            return k
    return "sang"  # app-icon, chuyen-dong*, *-sang

def doi_mau(svg, bang):
    assert not (set(bang) & NOTE), "không được đổi màu nốt"
    return re.sub(r"#[0-9A-Fa-f]{6}", lambda m: bang.get(m.group(0).upper(), m.group(0)), svg)

DST.mkdir(exist_ok=True)
for f in sorted(SRC.glob("*.svg")):
    if f.stem == "favicon":
        # favicon dùng biến CSS; bản Sân khấu đã có sẵn trong frontend/public
        shutil.copy(GOC.parent.parent / "frontend/public/favicon-san-khau.svg", DST / "favicon.svg")
        continue
    goc = f.read_text(encoding="utf-8")
    moi = doi_mau(goc, MAP[bien_the(f.stem)])
    # Kiểm: tập màu nốt trước và sau phải giống hệt
    nn = lambda s: sorted(c for c in re.findall(r"#[0-9A-Fa-f]{6}", s.upper()) if c in NOTE)
    assert nn(goc) == nn(moi), f.name
    (DST / f.name).write_text(moi, encoding="utf-8")
    print(f.name, bien_the(f.stem))

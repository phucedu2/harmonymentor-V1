"""Dựng bộ logo các bản màu (ADR-026) từ bộ Đồng & Gỉ trong logo/.

Vì sao thay màu thay vì dựng lại từ build.js: bộ gốc cần npm + tải font + cairosvg.
Ở đây chỉ đổi màu vỏ/chữ/viền; 12 màu nốt và vị trí lỗ giữ nguyên (BRAND_NOTE luật 2).
Chạy từ gốc repo:
  python3 docs/thuong-hieu/_nguon/san_khau.py              # Sân khấu -> logo/san-khau/ (mặc định của app)
  python3 docs/thuong-hieu/_nguon/san_khau.py giay-nhac    # Giấy nhạc (phương án dự phòng) -> logo/giay-nhac/
"""
import pathlib, re, shutil, sys

GOC = pathlib.Path(__file__).resolve().parent.parent
SRC = GOC / "logo"
REPO = GOC.parent.parent
NOTE = {"#3CC3AB", "#28BFD2", "#58B5ED", "#8AA8F7", "#B49AED", "#D48FD1",
        "#E78AAA", "#ED8C80", "#E3975A", "#CAA647", "#A4B558", "#73C07F"}

def bang(mực, nền_sáng, chữ_tối, ô_tối, viền_tối, nền_tối):
    # Bảng thay theo biến thể file (cùng một mã màu có vai khác nhau ở bản sáng/tối/đơn sắc)
    return {
        "sang":  {"#0C231F": mực, "#F2F3EA": nền_sáng},
        "toi":   {"#F2F3EA": chữ_tối, "#101F1C": ô_tối, "#45C2AB": viền_tối, "#081613": nền_tối},
        "den":   {"#0C231F": mực},
        "trang": {"#F2F3EA": chữ_tối, "#0C231F": mực},
    }

BRANDS = {
    # tên: (bảng màu, biến CSS favicon sáng, biến CSS favicon tối)
    "san-khau": (bang("#17142B", "#F4F2F8", "#ECEBF5", "#1A1630", "#F2B33D", "#0E0C1B"),
                 {"lacquer": "#17142B", "edge": "#17142B"}, {"lacquer": "#1A1630", "edge": "#F2B33D"}),
    "giay-nhac": (bang("#1D1B18", "#FBF8F1", "#F3EEE3", "#2A2620", "#F0938A", "#17150F"),
                  {"lacquer": "#1D1B18", "edge": "#1D1B18"}, {"lacquer": "#2A2620", "edge": "#F0938A"}),
}

def bien_the(ten):
    for k in ("toi", "den", "trang"):
        if ten.endswith("-" + k):
            return k
    return "sang"  # app-icon, chuyen-dong*, *-sang

def doi_mau(svg, b):
    assert not (set(b) & NOTE), "không được đổi màu nốt"
    return re.sub(r"#[0-9A-Fa-f]{6}", lambda m: b.get(m.group(0).upper(), m.group(0)), svg)

def favicon(svg, sang, toi):
    """favicon.svg dùng biến CSS: chỉ đổi lacquer/edge ở khối sáng và khối tối."""
    def sub(block, vals):
        for k, v in vals.items():
            block = re.sub(rf"(--{k}:)#[0-9A-Fa-f]{{6}}", rf"\g<1>{v}", block)
        return block
    m = re.search(r"<style>(.*?)@media \(prefers-color-scheme:dark\)\{svg\{(.*?)\}\}</style>", svg)
    return svg.replace(m.group(0), f"<style>{sub(m.group(1), sang)}@media (prefers-color-scheme:dark){{svg{{{sub(m.group(2), toi)}}}}}</style>")

def main(ten):
    mau, fav_sang, fav_toi = BRANDS[ten]
    dst = SRC / ten
    dst.mkdir(exist_ok=True)
    nn = lambda s: sorted(c for c in re.findall(r"#[0-9A-Fa-f]{6}", s.upper()) if c in NOTE)
    for f in sorted(SRC.glob("*.svg")):
        goc = f.read_text(encoding="utf-8")
        if f.stem == "favicon":
            moi = favicon(goc, fav_sang, fav_toi)
            (REPO / "frontend/public" / f"favicon-{ten}.svg").write_text(moi, encoding="utf-8")
        else:
            moi = doi_mau(goc, mau[bien_the(f.stem)])
        # Kiểm: tập màu nốt trước và sau phải giống hệt
        assert nn(goc) == nn(moi), f.name
        (dst / f.name).write_text(moi, encoding="utf-8")
        print(ten, f.name)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "san-khau")

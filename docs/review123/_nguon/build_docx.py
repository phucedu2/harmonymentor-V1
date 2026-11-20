"""Dựng file eProject_Sem-II_HarmonyMentor_Review01_02_03.docx (song ngữ Anh–Việt) theo khung trang của bản mẫu Aptech.

Nguồn số liệu: du_lieu/schema.json (models.py), so_do/png (Graphviz), anh/ (ảnh chụp thật), kiem_thu/ (test thủ công),
noi_dung.py (chữ của từng mục, kèm nguồn). Chạy lại được bất cứ lúc nào:

    python docs/review123/_nguon/build_docx.py            # dựng .docx
    python docs/review123/_nguon/build_docx.py --pdf      # dựng, render PDF bằng LibreOffice để soát, điền số trang Mục lục
    python docs/review123/_nguon/build_docx.py --vi --pdf # bản thuần tiếng Việt (cần gen_diagrams.py --vi trước)

PDF chỉ để tự kiểm (ghi vào thư mục tạm), không nộp.
"""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dich_vi  # noqa: E402
import mo_ta_bang  # noqa: E402
import noi_dung as ND  # noqa: E402

# --vi: bản thuần tiếng Việt (chữ thường, không in nghiêng xám), dùng phần vi của mọi cặp (en, vi) và dich_vi.py
VI = "--vi" in sys.argv
OUT = HERE.parent / ("eProject_Sem-II_HarmonyMentor_Review01_02_03_TiengViet.docx" if VI
                     else "eProject_Sem-II_HarmonyMentor_Review01_02_03.docx")
PNG = HERE / "so_do" / ("png_vi" if VI else "png")
ANH = HERE / "anh"
MAU = HERE / "mau"
SCHEMA = json.loads((HERE / "du_lieu" / "schema.json").read_text(encoding="utf-8"))
TABLES = {t["name"]: t for t in SCHEMA}
TOC_CACHE = HERE / "du_lieu" / ("toc_pages_vi.json" if VI else "toc_pages.json")

BODY_FONT, SMALL_FONT = "Times New Roman", "Arial"
GREY = RGBColor(0x59, 0x59, 0x59)
FILL_YELLOW = "FFF2CC"
TEXT_W = 17.0  # cm, A4 21 cm trừ lề 2 + 2
BLANK = "________"


def L(en, vi=None):
    """Chữ theo ngôn ngữ đang dựng: bản tiếng Việt lấy vi, thiếu vi thì tra dich_vi.T."""
    if not VI:
        return en
    return vi if vi else dich_vi.T(en)


BOLD_LEAD_VI = {"Solution:": "Giải pháp:", "Future scope.": "Hướng phát triển."}

DOCNAME_VI = {
    "Problem Definition": "Định nghĩa vấn đề", "Customer Requirements Specifications": "Đặc tả yêu cầu khách hàng",
    "Data Flow Diagram": "Sơ đồ luồng dữ liệu", "Entity Relationship Diagram": "Sơ đồ thực thể – quan hệ",
    "Table Design": "Thiết kế bảng", "Site Map": "Sơ đồ trang", "Algorithms": "Thuật toán", "Screen Design": "Thiết kế màn hình",
    "Testing Document": "Tài liệu kiểm thử", "Final Checklist": "Danh mục kiểm tra cuối", "Task Sheet": "Bảng phân công công việc",
}


# =============================================================================================== helpers XML
def _shade(el, fill: str) -> None:
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    el.append(shd)


def run_font(run, size=None, bold=None, italic=None, color=None, font=None):
    if font:
        run.font.name = font
        rpr = run._r.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts")
            rpr.insert(0, rf)
        for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rf.set(qn(k), font)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = color
    return run


def blank_run(p, text=BLANK, size=None, bold=None):
    """Ô nhóm tự điền: gạch dưới, nền vàng nhạt."""
    r = p.add_run(text)
    run_font(r, size=size, bold=bold)
    _shade(r._r.get_or_add_rPr(), FILL_YELLOW)
    return r


def add_field(p, instr: str, cached: str = "1", size=None, bold=None, font=None):
    def fc(kind):
        r = p.add_run()
        el = OxmlElement("w:fldChar")
        el.set(qn("w:fldCharType"), kind)
        r._r.append(el)
        run_font(r, size=size, bold=bold, font=font)
        return r
    fc("begin")
    r = p.add_run()
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = f" {instr} "
    r._r.append(it)
    fc("separate")
    run_font(p.add_run(cached), size=size, bold=bold, font=font)
    fc("end")


def set_cell_width(cell, cm):
    cell.width = Cm(cm)
    tcpr = cell._tc.get_or_add_tcPr()
    w = tcpr.find(qn("w:tcW"))
    if w is None:
        w = OxmlElement("w:tcW")
        tcpr.append(w)
    w.set(qn("w:w"), str(int(cm * 567)))
    w.set(qn("w:type"), "dxa")


def set_widths(table, widths):
    table.autofit = False
    tblpr = table._tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblpr.append(lay)
    grid = table._tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(int(w * 567)))
    for row in table.rows:
        for cell, w in zip(row.cells, widths):
            set_cell_width(cell, w)


def cell_shade(cell, fill):
    _shade(cell._tc.get_or_add_tcPr(), fill)


def repeat_header(row):
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trpr.append(el)


def no_split(row):
    trpr = row._tr.get_or_add_trPr()
    trpr.append(OxmlElement("w:cantSplit"))


def row_height(row, cm):
    trpr = row._tr.get_or_add_trPr()
    h = OxmlElement("w:trHeight")
    h.set(qn("w:val"), str(int(cm * 567)))
    h.set(qn("w:hRule"), "atLeast")
    trpr.append(h)


def page_border(section, sz=24):
    sp = section._sectPr
    b = OxmlElement("w:pgBorders")
    b.set(qn("w:offsetFrom"), "page")
    for side in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), str(sz))
        e.set(qn("w:space"), "24")
        e.set(qn("w:color"), "000000")
        b.append(e)
    # pgBorders phải đứng sau pgMar/pgSz theo lược đồ; chèn trước cols nếu có.
    cols = sp.find(qn("w:cols"))
    if cols is not None:
        cols.addprevious(b)
    else:
        sp.append(b)


def keep_next(p):
    p.paragraph_format.keep_with_next = True


# =============================================================================================== document
class Doc:
    def __init__(self, toc_pages: dict[str, int] | None):
        self.d = Document()
        self.toc_pages = toc_pages or {}
        self.headings: list[tuple[int, str]] = []
        self.first_section = True
        self._styles()
        self.fig = 0

    # ---------------------------------------------------------------- styles
    def _styles(self):
        st = self.d.styles
        n = st["Normal"]
        n.font.name = BODY_FONT
        n.font.size = Pt(11.5)
        rpr = n.element.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts")
            rpr.insert(0, rf)
        for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rf.set(qn(k), BODY_FONT)
        pf = n.paragraph_format
        pf.space_before = Pt(0)
        pf.space_after = Pt(3)
        pf.line_spacing = 1.08
        h1 = st["Heading 1"]
        h1.font.name, h1.font.size, h1.font.bold = BODY_FONT, Pt(15), True
        h1.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        h1.font.italic = False
        h1.paragraph_format.space_before = Pt(6)
        h1.paragraph_format.space_after = Pt(6)
        h1.paragraph_format.left_indent = Cm(0)
        h1.paragraph_format.right_indent = Cm(4.2)
        h1.paragraph_format.keep_with_next = True
        _shade(h1.element.get_or_add_pPr(), "000000")
        for name, size in (("Heading 2", 12.5), ("Heading 3", 11.5)):
            h = st[name]
            h.font.name, h.font.size, h.font.bold = BODY_FONT, Pt(size), True
            h.font.color.rgb = RGBColor(0, 0, 0)
            h.font.italic = False
            h.paragraph_format.space_before = Pt(8)
            h.paragraph_format.space_after = Pt(3)
            h.paragraph_format.keep_with_next = True
        for s in (h1, st["Heading 2"], st["Heading 3"]):
            r = s.element.get_or_add_rPr()
            f = r.find(qn("w:rFonts"))
            if f is None:
                f = OxmlElement("w:rFonts")
                r.insert(0, f)
            for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                f.set(qn(k), BODY_FONT)
            for th in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                if f.get(qn(th)) is not None:
                    del f.attrib[qn(th)]

    # ---------------------------------------------------------------- sections
    def section(self, form=None, docname=None, eff=None, border=False, margins=None, header=True):
        if self.first_section:
            s = self.d.sections[0]
            self.first_section = False
        else:
            s = self.d.add_section(WD_SECTION.NEW_PAGE)
        s.page_width, s.page_height = Cm(21.0), Cm(29.7)
        top, bottom, left, right = margins or ((3.5, 3.9, 2.0, 2.0) if header else (2.5, 2.5, 2.5, 2.5))
        s.top_margin, s.bottom_margin, s.left_margin, s.right_margin = Cm(top), Cm(bottom), Cm(left), Cm(right)
        s.header_distance, s.footer_distance = Cm(0.9), Cm(0.6)
        for hf in (s.header, s.footer):
            hf.is_linked_to_previous = False
            for p in hf.paragraphs:
                for r in list(p.runs):
                    r._r.getparent().remove(r._r)
        # add_section chép sectPr của mục trước, kể cả viền trang: xóa trước rồi mới thêm khi cần
        for old in s._sectPr.findall(qn("w:pgBorders")):
            s._sectPr.remove(old)
        if border:
            page_border(s)
        if header and form:
            self._header(s, form, docname, eff)
            self._footer(s)
        return s

    def _small(self, cell, label, value=None, blank=False, field_page=False):
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        run_font(p.add_run(label), size=8, bold=True, font=SMALL_FONT)
        if field_page:
            add_field(p, "PAGE", size=8, bold=True, font=SMALL_FONT)
            run_font(p.add_run(L(" of ", " / ")), size=8, font=SMALL_FONT)
            add_field(p, "NUMPAGES", "120", size=8, bold=True, font=SMALL_FONT)
        elif blank:
            r = blank_run(p, size=8)
            run_font(r, font=SMALL_FONT)
        elif value:
            q = cell.add_paragraph() if len(value) > 30 else p
            q.paragraph_format.space_after = Pt(0)
            run_font(q.add_run(value if q is not p else " " + value), size=8, font=SMALL_FONT)

    def _header(self, s, form, docname, eff):
        hdr = s.header
        t = hdr.add_table(2, 3, Cm(TEXT_W))
        t.style = self.d.styles["Table Grid"]
        set_widths(t, [4.2, 7.3, 5.5])
        self._small(t.cell(0, 0), L("Design Plan:", "Kế hoạch thiết kế:"), "HarmonyMentor")
        self._small(t.cell(0, 1), L("Document Name:", "Tên tài liệu:"), DOCNAME_VI.get(docname, docname) if VI else docname)
        self._small(t.cell(0, 2), L(f"SWD/Form No.{form}/Ver1.0", f"SWD/Mẫu số {form}/Phiên bản 1.0"))
        self._small(t.cell(1, 0), L("Effective Date:", "Ngày hiệu lực:"), eff)
        self._small(t.cell(1, 1), L("Version 1.0", "Phiên bản 1.0"))
        self._small(t.cell(1, 2), L("Page No: ", "Trang: "), field_page=True)
        hdr.paragraphs[0].paragraph_format.space_after = Pt(0)
        # đoạn trống của header nằm trước bảng: dời xuống sau để bảng sát lề trên
        p0 = hdr.paragraphs[0]._p
        p0.getparent().remove(p0)
        hdr._element.append(p0)

    def _footer(self, s):
        f = s.footer
        t = f.add_table(4, 3, Cm(TEXT_W))
        t.style = self.d.styles["Table Grid"]
        set_widths(t, [4.2, 6.4, 6.4])
        def put(r, c, text, bold=True, blank=False, center=True):
            p = t.cell(r, c).paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            if center:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if text:
                run_font(p.add_run(text), size=8, bold=bold, font=SMALL_FONT)
            if blank:
                run_font(blank_run(p, size=8), font=SMALL_FONT)
        put(0, 1, L("Prepared by (Student)", "Người lập (Sinh viên)"))
        put(0, 2, L("Approved by (Faculty)", "Người duyệt (Giảng viên)"))
        put(1, 1, L("Project Group No: ", "Nhóm đồ án số: "), blank=True)
        put(1, 2, "", blank=True)
        put(2, 0, L("Signature", "Chữ ký"), center=False)
        put(3, 0, L("Date", "Ngày"), center=False)
        row_height(t.rows[2], 0.9)
        p0 = f.paragraphs[0]._p
        p0.getparent().remove(p0)
        f._element.append(p0)

    # ---------------------------------------------------------------- text
    def h(self, level, en, vi=None, toc=True):
        if VI:
            text = vi or dich_vi.T(en)
        else:
            text = f"{en} ({vi})" if vi else en
        p = self.d.add_paragraph(text, style=f"Heading {level}")
        if toc and level <= 2:
            self.headings.append((level, text))
        return p

    def p(self, en, vi=None, bold_lead=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=None, indent=None):
        q = self.d.add_paragraph()
        q.alignment = align
        if indent:
            q.paragraph_format.left_indent = Cm(indent)
        if VI:
            if bold_lead:
                run_font(q.add_run(BOLD_LEAD_VI.get(bold_lead, bold_lead) + " "), bold=True, size=size)
            run_font(q.add_run(vi or dich_vi.T(en)), size=size)
            return q
        if bold_lead:
            run_font(q.add_run(bold_lead + " "), bold=True, size=size)
        run_font(q.add_run(en), size=size)
        if vi:
            q.paragraph_format.space_after = Pt(0)
            v = self.d.add_paragraph()
            v.alignment = align
            if indent:
                v.paragraph_format.left_indent = Cm(indent)
            v.paragraph_format.space_after = Pt(5)
            run_font(v.add_run(vi), italic=True, color=GREY, size=(size or 11.5) - 0.5)
        return q

    def bullet(self, en, vi=None, lead=None, lead_vi=None):
        q = self.d.add_paragraph()
        q.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pf = q.paragraph_format
        pf.left_indent, pf.first_line_indent = Cm(1.2), Cm(-0.6)
        pf.space_after = Pt(0 if vi and not VI else 2)
        run_font(q.add_run("✓\t"), font="Segoe UI Symbol", size=10)
        pf.tab_stops.add_tab_stop(Cm(1.2))
        if VI:
            if lead or lead_vi:
                run_font(q.add_run((lead_vi or dich_vi.T(lead)) + " "), bold=True)
            q.add_run(vi or dich_vi.T(en))
            return
        if lead:
            run_font(q.add_run(lead + " "), bold=True)
        q.add_run(en)
        if vi:
            v = self.d.add_paragraph()
            v.alignment = WD_ALIGN_PARAGRAPH.LEFT
            v.paragraph_format.left_indent = Cm(1.2)
            v.paragraph_format.space_after = Pt(3)
            if lead_vi:
                run_font(v.add_run(lead_vi + " "), bold=True, italic=True, color=GREY, size=11)
            run_font(v.add_run(vi), italic=True, color=GREY, size=11)

    def page_break(self):
        # Đoạn rỗng "sang trang trước": nếu trang trước đã đầy thì không sinh thêm trang trắng như ngắt trang thường.
        q = self.d.add_paragraph()
        q.paragraph_format.page_break_before = True
        q.paragraph_format.space_after = Pt(0)
        q.paragraph_format.line_spacing = Pt(1)
        run_font(q.add_run(""), size=1)

    # ---------------------------------------------------------------- tables
    def table(self, headers, rows, widths, size=9.5, header_fill="D9D9D9", first_col_bold=False, keep_rows=True):
        t = self.d.add_table(rows=1, cols=len(headers))
        t.style = self.d.styles["Table Grid"]
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, hd in enumerate(headers):
            c = t.rows[0].cells[i]
            cell_shade(c, header_fill)
            self._cell(c, hd, size=size, bold=True)
        repeat_header(t.rows[0])
        for r in rows:
            cells = t.add_row().cells
            for i, val in enumerate(r):
                self._cell(cells[i], val, size=size, bold=(first_col_bold and i == 0))
        if keep_rows:
            for row in t.rows:
                no_split(row)
        set_widths(t, widths)
        self.d.add_paragraph().paragraph_format.space_after = Pt(2)
        return t

    def _cell(self, cell, val, size=9.5, bold=False):
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        if isinstance(val, dict):  # {"text":..., "blank": True} hoặc {"rich": [(text, opts)]}
            if val.get("blank"):
                if val.get("text"):
                    run_font(p.add_run(val["text"]), size=size, bold=bold)
                blank_run(p, size=size)
                return
            for txt, opts in val["rich"]:
                if opts.get("newpara"):
                    p = cell.add_paragraph()
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.line_spacing = 1.0
                run_font(p.add_run(dich_vi.T(txt) if VI else txt), size=opts.get("size", size), bold=opts.get("bold", bold),
                         italic=opts.get("italic"), color=opts.get("color"))
            return
        if isinstance(val, tuple):
            en, vi = val
            if VI:
                run_font(p.add_run(vi or dich_vi.T(en)), size=size, bold=bold)
                return
            run_font(p.add_run(en), size=size, bold=bold)
            if vi:
                q = cell.add_paragraph()
                q.paragraph_format.space_after = Pt(0)
                q.paragraph_format.line_spacing = 1.0
                run_font(q.add_run(vi), size=size - 0.5, italic=True, color=GREY, bold=False if not bold else True)
            return
        run_font(p.add_run(dich_vi.T(str(val)) if VI else str(val)), size=size, bold=bold)

    # ---------------------------------------------------------------- images
    def image(self, path: Path, max_w=16.5, max_h=21.5, caption=None, center=True, upscale=1.2):
        im = Image.open(path)
        w_px, h_px = im.size
        dpi = (im.info.get("dpi") or (300, 300))[0] or 300
        w = min(max_w, w_px / dpi * 2.54 * upscale)  # không phóng quá cỡ gốc × upscale
        if w * h_px / w_px > max_h:
            w = max_h * w_px / h_px
        q = self.d.add_paragraph()
        q.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
        q.paragraph_format.space_after = Pt(2)
        q.paragraph_format.keep_with_next = bool(caption)
        q.add_run().add_picture(str(path), width=Cm(w))
        if caption:
            self.fig += 1
            en, vi = caption
            c = self.d.add_paragraph()
            c.alignment = WD_ALIGN_PARAGRAPH.CENTER
            c.paragraph_format.space_after = Pt(6)
            if VI:
                run_font(c.add_run(f"Hình {self.fig}. {vi}"), bold=True, size=10)
            else:
                run_font(c.add_run(f"Figure {self.fig}. {en}"), bold=True, size=10)
                run_font(c.add_run(f"  (Hình {self.fig}. {vi})"), italic=True, color=GREY, size=10)
        return q

    def anchor_behind(self, p, path, x_cm, y_cm, w_cm, h_cm):
        """Ảnh khung hoa văn nằm sau chữ, neo theo trang (trang chứng nhận)."""
        run = p.add_run()
        run.add_picture(str(path), width=Cm(w_cm), height=Cm(h_cm))
        inline = run._r.find(".//" + qn("wp:inline"))
        graphic = inline.find(qn("a:graphic"))
        docpr = inline.find(qn("wp:docPr"))
        emu = lambda cm: str(int(cm * 360000))  # noqa: E731
        anchor = parse_xml(
            f'<wp:anchor {nsdecls("wp", "a", "pic", "r")} distT="0" distB="0" distL="0" distR="0" simplePos="0" '
            f'relativeHeight="0" behindDoc="1" locked="0" layoutInCell="1" allowOverlap="1">'
            f'<wp:simplePos x="0" y="0"/>'
            f'<wp:positionH relativeFrom="page"><wp:posOffset>{emu(x_cm)}</wp:posOffset></wp:positionH>'
            f'<wp:positionV relativeFrom="page"><wp:posOffset>{emu(y_cm)}</wp:posOffset></wp:positionV>'
            f'<wp:extent cx="{emu(w_cm)}" cy="{emu(h_cm)}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
            f'<wp:wrapNone/><wp:docPr id="{docpr.get("id")}" name="Frame"/><wp:cNvGraphicFramePr/></wp:anchor>')
        anchor.append(copy.deepcopy(graphic))
        inline.getparent().replace(inline, anchor)

    # ---------------------------------------------------------------- TOC
    def toc(self):
        """Trường TOC thật (Word cập nhật được); phần hiển thị sẵn điền số trang đo từ lần render trước."""
        p = self.d.add_paragraph()
        r = p.add_run()
        el = OxmlElement("w:fldChar")
        el.set(qn("w:fldCharType"), "begin")
        r._r.append(el)
        r = p.add_run()
        it = OxmlElement("w:instrText")
        it.set(qn("xml:space"), "preserve")
        it.text = ' TOC \\o "1-2" \\h \\z \\u '
        r._r.append(it)
        r = p.add_run()
        el = OxmlElement("w:fldChar")
        el.set(qn("w:fldCharType"), "separate")
        r._r.append(el)
        self._toc_anchor = p
        return p

    def fill_toc(self):
        """Gọi sau khi dựng xong: chèn các dòng mục lục vào giữa separate và end."""
        anchor = self._toc_anchor
        prev = anchor
        for level, text in self.headings:
            q = self.d.add_paragraph()
            q.paragraph_format.left_indent = Cm(0 if level == 1 else 0.8)
            q.paragraph_format.space_after = Pt(1 if level == 2 else 3)
            q.paragraph_format.tab_stops.add_tab_stop(Cm(TEXT_W - 0.1), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            page = self.toc_pages.get(text, "")
            run_font(q.add_run(f"{text}\t{page}"), bold=(level == 1), size=11 if level == 1 else 10.5)
            prev._p.addnext(q._p)
            prev = q
        end = self.d.add_paragraph()
        r = end.add_run()
        el = OxmlElement("w:fldChar")
        el.set(qn("w:fldCharType"), "end")
        r._r.append(el)
        prev._p.addnext(end._p)


# =============================================================================================== pages
def cover(D: Doc):
    D.section(border=True, header=False, margins=(2.2, 2.2, 2.6, 2.6))
    D.image(MAU / "logo_aptech.png", max_w=15.5, upscale=99)
    for _ in range(5):
        D.d.add_paragraph()
    t = D.d.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_font(t.add_run("HarmonyMentor AI"), size=26, bold=True)
    for en, vi in [("Adaptive Music Theory and Harmony Learning Platform",
                    "Nền tảng học nhạc lý và hòa âm thích ứng")]:
        q = D.d.add_paragraph()
        q.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_font(q.add_run(L(en, vi)), size=14, bold=True)
        if not VI:
            v = D.d.add_paragraph()
            v.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run_font(v.add_run(vi), size=12, italic=True, color=GREY)
    q = D.d.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_font(q.add_run(L("eProject Semester II – Review 01, 02, 03", "eProject Học kỳ II – Đánh giá lần 01, 02, 03")), size=12)
    for _ in range(4 if not VI else 5):
        D.d.add_paragraph()
    info = [(L("Supervisor:", "Giảng viên hướng dẫn:"), None), (L("Semester:", "Học kỳ:"), "II"),
            (L("Batch No:", "Khóa (Batch):"), "T3.2511.M0"), (L("Group No:", "Nhóm số:"), None)]
    for lab, val in info:
        q = D.d.add_paragraph()
        q.paragraph_format.left_indent = Cm(1.5)
        q.paragraph_format.space_after = Pt(2)
        run_font(q.add_run(lab + "\t"), bold=True, size=11)
        q.paragraph_format.tab_stops.add_tab_stop(Cm(6.2 if VI else 5.0))
        if val:
            run_font(q.add_run(val), italic=True, size=11)
        else:
            blank_run(q, "________________", size=11)
    t = D.d.add_table(rows=4, cols=3)
    t.style = D.d.styles["Table Grid"]
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, hd in enumerate([L("Order:", "STT"), L("Full name", "Họ và tên"), L("Roll No.", "Mã sinh viên")]):
        D._cell(t.cell(0, i), hd, size=11, bold=True)
    for r in range(1, 4):
        D._cell(t.cell(r, 0), f"{r}.", size=11)
        D._cell(t.cell(r, 1), {"blank": True}, size=11)
        D._cell(t.cell(r, 2), {"blank": True}, size=11)
    set_widths(t, [2.2, 6.5, 4.5])
    for _ in range(5):
        D.d.add_paragraph()
    q = D.d.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if VI:
        run_font(q.add_run("Tháng"), bold=True, italic=True, size=11)
        run_font(q.add_run(": 11   "), italic=True, size=11)
        run_font(q.add_run("Năm"), bold=True, italic=True, size=11)
        run_font(q.add_run(": 2026"), italic=True, size=11)
        return
    run_font(q.add_run("Month"), bold=True, italic=True, size=11)
    run_font(q.add_run(": November   "), italic=True, size=11)
    run_font(q.add_run("Year"), bold=True, italic=True, size=11)
    run_font(q.add_run(": 2026"), italic=True, size=11)


def certificate(D: Doc):
    D.section(header=False, margins=(4.2, 3.0, 3.4, 3.4))
    p = D.d.add_paragraph()
    D.anchor_behind(p, MAU / "khung_hoa_van.png", 1.2, 1.2, 18.6, 25.7)
    run_font(p.add_run(L("This is to certify that", "Chứng nhận rằng")), size=17)
    if not VI:
        run_font(D.d.add_paragraph().add_run("(Chứng nhận rằng)"), size=10, italic=True, color=GREY)
    for _ in range(3):
        q = D.d.add_paragraph()
        q.paragraph_format.left_indent = Cm(0.4)
        q.paragraph_format.space_after = Pt(9)
        run_font(q.add_run(L("Mr./Ms.  ", "Ông/Bà  ")), size=13, bold=True)
        blank_run(q, "_" * 42, size=13)
    D.d.add_paragraph()
    run_font(D.d.add_paragraph().add_run(L("Have successfully Designed & Developed", "Đã thiết kế và xây dựng thành công")), size=15)
    if not VI:
        run_font(D.d.add_paragraph().add_run("(Đã thiết kế và xây dựng thành công)"), size=10, italic=True, color=GREY)
    q = D.d.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_font(q.add_run("HARMONYMENTOR AI"), size=16, bold=True)
    q = D.d.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_font(q.add_run(L("Adaptive Music Theory and Harmony Learning Platform", "Nền tảng học nhạc lý và hòa âm thích ứng")), size=11.5, italic=True)
    for _ in range(3):
        D.d.add_paragraph()
    run_font(D.d.add_paragraph().add_run(L("Submitted by:", "Giảng viên hướng dẫn:")), size=15)
    if not VI:
        run_font(D.d.add_paragraph().add_run("(Giảng viên hướng dẫn)"), size=10, italic=True, color=GREY)
    q = D.d.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_font(q.add_run(L("Mr./Ms.  ", "Ông/Bà  ")), size=15, bold=True)
    blank_run(q, "_" * 30, size=15)
    for _ in range(2):
        D.d.add_paragraph()
    run_font(D.d.add_paragraph().add_run(L("Date Of Issue:", "Ngày cấp:")), size=15)
    q = D.d.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    blank_run(q, "_" * 28, size=13)
    D.d.add_paragraph()
    run_font(D.d.add_paragraph().add_run(L("Authorized Signature:", "Chữ ký xác nhận:")), size=15)
    q = D.d.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    blank_run(q, "_" * 28, size=13)


def front_matter(D: Doc):
    D.section(header=False, margins=(2.5, 2.5, 2.2, 2.2))
    p = D.d.add_paragraph(L("Content (Mục lục)", "Mục lục"), style="Heading 1")
    D.toc()
    D.section(header=False, margins=(2.5, 2.5, 2.2, 2.2))
    D.h(1, "Acknowledge", "Lời cảm ơn")
    for en, vi in ND.ACKNOWLEDGE:
        D.p(en, vi)
    q = D.d.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if VI:
        run_font(q.add_run("Nhóm đặc biệt cảm ơn thầy/cô hướng dẫn "), size=11.5)
        blank_run(q, "____________________", size=11.5)
        run_font(q.add_run(" đã hướng dẫn và góp ý thẳng thắn ở mỗi lần đánh giá."), size=11.5)
    else:
        run_font(q.add_run("We especially thank our supervisor, "), size=11.5)
        blank_run(q, "____________________", size=11.5)
        run_font(q.add_run(", for the guidance and the honest feedback at every review."), size=11.5)
        v = D.d.add_paragraph()
        run_font(v.add_run("Nhóm đặc biệt cảm ơn thầy/cô hướng dẫn "), italic=True, color=GREY, size=11)
        blank_run(v, "____________________", size=11)
        run_font(v.add_run(" đã hướng dẫn và góp ý thẳng thắn ở mỗi lần review."), italic=True, color=GREY, size=11)
    D.d.add_paragraph()
    q = D.d.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run_font(q.add_run(L("Project Group ", "Nhóm đồ án ")), italic=True)
    blank_run(q, "____")
    D.section(header=False, margins=(2.5, 2.5, 2.2, 2.2))
    D.h(1, "Synopsis", "Tóm tắt")
    for en, vi in ND.SYNOPSIS:
        D.p(en, vi)


def divider(D: Doc, title, vi, forms):
    D.section(border=True, header=False)
    for _ in range(14):
        D.d.add_paragraph()
    q = D.d.add_paragraph(style="Heading 1")
    q.paragraph_format.right_indent = Cm(0)
    # trang ngăn: chữ đen lớn giữa trang như mẫu, không thanh đen; vẫn vào mục lục
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pPr = q._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), "FFFFFF")
    pPr.append(shd)
    if VI:
        title = vi
    run_font(q.add_run(title), size=26, bold=True, color=RGBColor(0, 0, 0))
    D.headings.append((1, title))
    v = D.d.add_paragraph()
    v.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if not VI:
        run_font(v.add_run(vi), size=13, italic=True, color=GREY)
    D.d.add_paragraph()
    for f in forms:
        if VI:
            so, ten = f.split("  ", 1)
            f = f"Mẫu {so.split()[1]}  {DOCNAME_VI.get(ten, DOCNAME_VI.get(ten + ' Document', ten))}"
        c = D.d.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraph_format.space_after = Pt(1)
        run_font(c.add_run(f), size=11)


# =============================================================================================== Review 01
def problem_definition(D: Doc):
    D.section("01/PD", "Problem Definition", ND.EFF["R01"])
    D.h(1, "Problem Definition", "Định nghĩa vấn đề")
    for en, vi in ND.PD_INTRO:
        D.p(en, vi)
    for en, vi in ND.PD_PROBLEMS:
        D.bullet(en, vi)
    D.p(*ND.PD_SOLUTION, bold_lead="Solution:")
    D.h(2, "1.1 Core Objectives", "Mục tiêu cốt lõi")
    for lead, en, lead_vi, vi in ND.OBJECTIVES:
        D.bullet(en, vi, lead=lead, lead_vi=lead_vi)
    D.h(2, "1.2 User Roles", "Vai trò người dùng")
    D.p(*ND.ROLES_INTRO)
    D.table([("Role", "Vai trò"), ("Description", "Mô tả"), ("Main permissions (as built)", "Quyền chính (theo code)")],
            ND.ROLES, [3.0, 4.6, 9.4], size=9.5, first_col_bold=True)
    D.h(2, "1.3 Project Impact", "Tác động của dự án")
    for lead, en, lead_vi, vi in ND.IMPACT:
        D.bullet(en, vi, lead=lead, lead_vi=lead_vi)
    D.h(2, "1.4 Scope and Future Scope", "Phạm vi và hướng phát triển")
    D.p(*ND.SCOPE_INTRO)
    D.table([("Built in this version", "Đã làm trong bản này"), ("Evidence in code", "Bằng chứng trong code")],
            ND.SCOPE_BUILT, [9.0, 8.0], size=9)
    D.p(*ND.FUTURE_INTRO, bold_lead="Future scope.")
    D.table([("Future scope item", "Hướng phát triển"), ("Status in code (commit 1ab6a15)", "Trạng thái trong code")],
            ND.FUTURE, [8.0, 9.0], size=9)
    D.p(*ND.SCOPE_NOTE)


def crs(D: Doc):
    D.section("02/CRS-B", "Customer Requirements Specifications", ND.EFF["R01"])
    D.h(1, "Customer Requirements Specifications", "Đặc tả yêu cầu khách hàng")
    D.p(*ND.CRS_INTRO)
    D.h(2, "2.1 Inputs, Processes and Outputs by Role", "Đầu vào, xử lý, đầu ra theo vai trò")
    for role, rows in ND.IPO:
        D.h(3, role[0], role[1], toc=False)
        D.table([("Input", "Đầu vào"), ("Process", "Xử lý"), ("Output", "Đầu ra")], rows, [5.2, 6.3, 5.5], size=9)
    D.h(2, "2.2 Hardware and Software Requirements", "Yêu cầu phần cứng và phần mềm")
    D.p(*ND.HW_INTRO)
    D.table([("Item", "Hạng mục"), ("Requirement / exact version", "Yêu cầu / phiên bản chính xác"), ("Source", "Nguồn")],
            ND.HW, [4.0, 8.0, 5.0], size=9)
    D.table([("Item", "Hạng mục"), ("Requirement / exact version", "Yêu cầu / phiên bản chính xác"), ("Source", "Nguồn")],
            ND.SW, [4.0, 8.0, 5.0], size=9)
    D.h(2, "2.3 Customer's Acceptance Criteria", "Tiêu chí nghiệm thu của khách hàng")
    D.p(*ND.AC_INTRO)
    rows = []
    for i, (given, when, then, g_vi, w_vi, t_vi, ev) in enumerate(ND.ACCEPTANCE, 1):
        if VI:
            rows.append([str(i), {"rich": [(f"Cho {g_vi},", {"bold": True}),
                                            (f"khi {w_vi} thì {t_vi}.", {"newpara": True})]}, dich_vi.T(ev)])
            continue
        rows.append([str(i), {"rich": [
            (f"Given {given}", {"bold": True}),
            (f"when {when} then {then}", {"newpara": True}),
            (f"Cho {g_vi}, khi {w_vi} thì {t_vi}.", {"newpara": True, "italic": True, "color": GREY, "size": 8.5}),
        ]}, ev])
    D.table(["S.N", ("Customer's Acceptance Criteria", "Tiêu chí nghiệm thu"), ("Proof", "Bằng chứng")],
            rows, [1.0, 12.4, 3.6], size=9)
    D.h(2, "2.4 Project Plan", "Kế hoạch dự án")
    D.p(*ND.PLAN_INTRO)
    D.table([("Member", "Thành viên"), ("Responsibility (SRS Table 14)", "Trách nhiệm (SRS Bảng 14)")],
            ND.TEAM, [3.0, 14.0], size=9.5, first_col_bold=True)
    D.table(["No.", ("Part", "Phần việc"), ("Main owner", "Phụ trách chính"), ("Period / milestone", "Thời gian / mốc"),
             ("Status at 17/11/2026", "Trạng thái 17/11/2026")], ND.PLAN, [1.0, 6.4, 2.6, 3.4, 3.6], size=9)
    D.table([("Milestone", "Mốc"), ("Date", "Ngày"), ("Deliverable (SRS Table 13)", "Sản phẩm (SRS Bảng 13)"),
             ("Evidence in the repository", "Minh chứng trong repo")], ND.MILESTONES, [2.0, 2.4, 6.0, 6.6], size=9)


# =============================================================================================== Review 02
def dfd(D: Doc):
    D.section("03/DFD", "Data Flow Diagram", ND.EFF["R02"])
    D.h(1, "Data Flow Diagram", "Sơ đồ luồng dữ liệu")
    D.p(*ND.DFD_INTRO)
    D.h(2, "3.1 DFD Level 0 (Context Diagram)", "DFD mức 0 – sơ đồ ngữ cảnh")
    D.image(PNG / "dfd_level0.png", max_w=15.5, caption=("Context diagram of HarmonyMentor AI", "Sơ đồ ngữ cảnh"))
    D.p(*ND.DFD0_TEXT)
    D.h(2, "3.2 DFD Level 1", "DFD mức 1")
    D.p(*ND.DFD1_INTRO)
    for name, title, vi, text in ND.DFD1_PARTS:
        D.page_break()
        D.h(3, title, vi, toc=False)
        D.p(*text)
        D.image(PNG / f"{name}.png", max_w=16.5, max_h=19.5, caption=(title, vi))
    D.h(2, "3.3 Data Stores", "Kho dữ liệu")
    D.p(*ND.STORES_INTRO)
    D.table([("Code", "Mã"), ("Data store", "Kho dữ liệu"), ("Real tables / service", "Bảng thật / dịch vụ"),
             ("Used by processes", "Tiến trình dùng")], ND.STORES, [1.4, 4.4, 6.6, 4.6], size=9)


def erd(D: Doc):
    D.section("04/ERD", "Entity Relationship Diagram", ND.EFF["R02"])
    D.h(1, "Entity Relationship Diagram", "Sơ đồ thực thể – quan hệ")
    D.p(*ND.ERD_INTRO)
    D.h(2, "A. Entity Relationship Diagram (Chen notation)", "ERD ký hiệu Chen")
    D.image(PNG / "erd_tong_quan.png", max_w=15.5, max_h=17.5,
            caption=("Overall ERD: 14 core entities", "ERD tổng quan: 14 thực thể cốt lõi"))
    D.h(3, "Cardinality", "Bản số", toc=False)
    for en, vi in ND.CARDINALITY:
        D.bullet(en, vi)
    for name, title, vi in ND.ERD_GROUPS:
        D.page_break()
        D.h(3, title, vi, toc=False)
        D.image(PNG / f"{name}.png", max_w=16.0, max_h=21.0, caption=(title, vi))
    D.page_break()
    D.h(2, "B. Entity Attributes", "Thuộc tính thực thể")
    D.p(*ND.ATTR_INTRO)
    GROUPS_FOR_DOC = ND.GROUPS_FOR_DOC
    for gkey, gtitle, gvi, tables in GROUPS_FOR_DOC:
        D.h(3, gtitle, gvi, toc=False)
        for t in tables:
            D.image(PNG / f"attr_{t}.png", max_w=12.5, max_h=9.3,
                    caption=(f"Attributes of {t}", f"Thuộc tính bảng {t}"))


def keys_of(t, c):
    out = []
    if c["pk"]:
        out.append("PK")
    for target, _ in c["fk"]:
        out.append(f"FK → {target}")
    if c["unique"]:
        out.append("UQ")
    for u in t["uniques"]:
        if c["name"] in u["columns"]:
            out.append(f"UQ({', '.join(u['columns'])})")
    return "\n".join(out)


def constraints_of(t, c):
    parts = ["NOT NULL" if not c["nullable"] else "NULL"]
    if c["default"] is not None:
        parts.append(f"DEFAULT {c['default']}")
    if c["server_default"] is not None:
        parts.append(f"SERVER DEFAULT {c['server_default']}")
    if c["onupdate"]:
        parts.append(f"ON UPDATE {c['onupdate']}")
    for _, ondel in c["fk"]:
        if ondel:
            parts.append(f"ON DELETE {ondel}")
    if c["index"]:
        parts.append("INDEX")
    for ck in t["checks"]:
        if re.search(rf"\b{re.escape(c['name'])}\b", ck["sql"]):
            sql = ck["sql"]
            if len(sql) > 90:
                sql = sql[:87] + "…)"
            parts.append(f"CHECK {sql}")
    return "\n".join(parts)


def table_design(D: Doc):
    D.section("05/TAB", "Table Design", ND.EFF["R02"])
    D.h(1, "Table Design", "Thiết kế bảng")
    D.p(*ND.TAB_INTRO)
    D.h(2, "A. Table Design (31 tables)", "Thiết kế 31 bảng")
    GROUPS_FOR_DOC = ND.GROUPS_FOR_DOC
    n = 0
    for gkey, gtitle, gvi, tables in GROUPS_FOR_DOC:
        D.h(3, f"Group: {gtitle}", f"Nhóm: {gvi}", toc=False)
        for tname in tables:
            n += 1
            t = TABLES[tname]
            en, vi = mo_ta_bang.TABLE_DESC[tname]
            q = D.p(f"Table {n}: {tname}. {en}", f"Bảng {n}: {tname}. {vi}", size=11)
            q.runs[0].bold = True
            keep_next(q)
            keep_next(D.d.paragraphs[-1])
            rows = []
            for i, c in enumerate(t["columns"], 1):
                rows.append([str(i), c["name"], c["type"].replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMPTZ"),
                             keys_of(t, c), constraints_of(t, c), mo_ta_bang.describe(tname, c["name"])])
            D.table(["Serial", "Fields", ("Data type", "Kiểu"), ("Keys", "Khóa"), ("Constraints", "Ràng buộc"),
                     ("Description", "Mô tả")], rows, [1.1, 3.0, 2.6, 2.9, 3.4, 4.0], size=8)
    D.page_break()
    D.h(2, "B. Relationship Diagram", "Sơ đồ quan hệ")
    D.p(*ND.REL_INTRO)
    for name, title, vi in ND.REL_DIAGRAMS:
        D.image(PNG / f"{name}.png", max_w=16.5, max_h=21.5, caption=(title, vi))


def sitemap(D: Doc):
    D.section("06/SM", "Site Map", ND.EFF["R02"])
    D.h(1, "Site Map", "Sơ đồ trang")
    D.p(*ND.SM_INTRO)
    D.image(PNG / "sitemap.png", max_w=16.5, caption=("Site map from frontend/src/App.tsx", "Sơ đồ trang lấy từ App.tsx"))
    D.table([("Route", "Đường dẫn"), ("Page", "Trang"), ("Access", "Quyền"), ("Content", "Nội dung")],
            ND.ROUTES, [3.8, 3.4, 2.6, 7.2], size=9)


def algorithms(D: Doc):
    D.section("07/ALG", "Algorithms", ND.EFF["R02"])
    D.h(1, "Algorithms", "Thuật toán")
    D.p(*ND.ALG_INTRO)
    D.table([("Symbol", "Ký hiệu"), ("Meaning", "Ý nghĩa")], ND.ALG_SYMBOLS, [5.0, 12.0], size=9.5)
    for i, (name, title, vi, src, texts) in enumerate(ND.ALGS, 1):
        D.page_break()
        D.h(2, f"7.{i} {title}", vi)
        D.p(f"Source: {src}", f"Nguồn: {src}", size=10)
        for en, v in texts:
            D.bullet(en, v)
        D.image(PNG / f"{name}.png", max_w=16.0, max_h={1: 15.5, 2: 19.0}.get(i, 14.5), caption=(title, vi))


# =============================================================================================== Review 03
def screen_design(D: Doc):
    D.section("08/SD", "Screen Design", ND.EFF["R03"])
    D.h(1, "Screen Design", "Thiết kế màn hình")
    D.p(*ND.SD_INTRO)
    for i, (fname, title, vi, route, en_d, vi_d) in enumerate(ND.SCREENS, 1):
        if i > 1 and i % 2 == 1:
            D.page_break()
        q = D.d.add_paragraph()
        keep_next(q)
        q.paragraph_format.space_before = Pt(4)
        if VI:
            run_font(q.add_run(f"S{i:02d}. {vi}"), bold=True, size=11.5)
            run_font(q.add_run(f"   Đường dẫn: {dich_vi.T(route)}"), size=9.5, font=SMALL_FONT)
        else:
            run_font(q.add_run(f"S{i:02d}. {title} "), bold=True, size=11.5)
            run_font(q.add_run(f"({vi})"), italic=True, color=GREY, size=11)
            run_font(q.add_run(f"   Route: {route}"), size=9.5, font=SMALL_FONT)
        p2 = D.p(en_d, vi_d, size=10)
        keep_next(p2)
        keep_next(D.d.paragraphs[-1])
        D.image(ANH / f"{fname}.png", max_w=15.6, max_h=8.4)


def testing(D: Doc):
    D.section("09/TD", "Testing Document", ND.EFF["R03"])
    D.h(1, "Testing", "Kiểm thử")
    D.p(*ND.TD_INTRO)
    D.h(2, "9.1 Automated Tests", "Kiểm thử tự động")
    D.table([("Suite", "Bộ test"), ("Command", "Lệnh"), ("Total", "Tổng"), ("Pass", "Đạt"), ("Fail", "Lỗi"),
             ("Skip", "Bỏ qua"), ("Time", "Thời gian"), ("Run at (UTC)", "Lúc chạy")],
            ND.AUTO_TESTS, [2.8, 4.7, 1.3, 1.3, 1.1, 1.3, 1.6, 2.9], size=8)
    for en, vi in ND.AUTO_NOTES:
        D.bullet(en, vi)
    D.h(2, "9.2 Offline Evaluations Reported by the Team", "Đánh giá offline nhóm đã báo cáo")
    D.p(*ND.EVAL_INTRO)
    D.table([("Evaluation", "Đánh giá"), ("Result", "Kết quả"), ("Source file / date", "File nguồn / ngày")],
            ND.EVALS, [4.5, 7.0, 5.5], size=8.5)
    D.h(2, "9.3 Manual Test Cases", "Ca kiểm thử thủ công")
    D.p(*ND.MT_INTRO)
    q = D.d.add_paragraph()
    run_font(q.add_run(L("Executed by: Claude (AI) on 17/11/2026, 12:26–12:28 UTC. Team re-run by: ",
                         "Người chạy: Claude (AI) ngày 17/11/2026, 12:26–12:28 UTC. Nhóm chạy lại: ")), size=10, bold=True)
    blank_run(q, size=10)
    run_font(q.add_run(L("  Date: ", "  Ngày: ")), size=10, bold=True)
    blank_run(q, size=10)
    run_font(q.add_run(L("  Signature: ", "  Chữ ký: ")), size=10, bold=True)
    blank_run(q, size=10)
    log = {x["id"]: x for x in json.loads((HERE / "kiem_thu" / "ket_qua_test_thu_cong.json").read_text(encoding="utf-8"))}
    rows = []
    for i, (tc, module, desc, steps, data, exp) in enumerate(ND.MANUAL, 1):
        rec = log[tc]
        actual = re.sub(r"\s*\|\s*", " · ", rec["actual"]).strip()
        actual = re.sub(r"(· ★ )+", "· ", actual)
        if len(actual) > 230:
            actual = actual[:227].rstrip() + "…"
        if rec.get("note"):
            actual += f" [{L('Note', 'Ghi chú')}: {rec['note']}]"
        rows.append([{"rich": [(f"MT-{i:02d}", {"bold": True}), (f"({tc})", {"newpara": True, "size": 6.5, "color": GREY})]},
                     module, desc, steps, data, exp, actual, L("Pass", "Đạt") if rec["ok"] else L("Fail", "Lỗi")])
    D.table(["ID", "Module", ("Description", "Mô tả"), ("Steps", "Các bước"), ("Test data", "Dữ liệu"),
             ("Expected", "Kỳ vọng"), ("Actual (app text, verbatim)", "Thực tế (chữ trong app)"), ("P/F", "KQ")],
            rows, [1.3, 1.6, 2.4, 2.8, 2.0, 2.6, 3.3, 1.0], size=7.5)
    D.p(*ND.MT_SUMMARY)


def final_checklist(D: Doc):
    D.section("10/FC", "Final Checklist", ND.EFF["R03"])
    D.h(1, "Final Checklist", "Danh mục kiểm tra cuối")
    D.p(*ND.FC_INTRO)
    rows = [[str(i), item, {"rich": [(st, {"bold": True})]}, note] for i, (item, st, note) in enumerate(ND.FINAL, 1)]
    D.table(["S.N", ("Item", "Hạng mục"), ("Status", "Trạng thái"), ("Evidence / note", "Minh chứng / ghi chú")],
            rows, [1.0, 6.2, 2.0, 7.8], size=8.5)


def task_sheet(D: Doc):
    D.section("11/TS", "Task Sheet", ND.EFF["R03"])
    D.h(1, "Task Sheet", "Bảng phân công công việc")
    D.p(*ND.TS_INTRO)
    rows = []
    for i, (task, owner, start, end, status, src, approval) in enumerate(ND.TASKS, 1):
        rows.append([str(i), task, owner, start, end, status, src,
                     {"blank": True} if approval is None else approval])
    D.table(["S.N", ("Task", "Công việc"), ("Owner (SRS Table 14 role)", "Phụ trách"), ("Start", "Bắt đầu"),
             ("End", "Kết thúc"), ("Status", "Trạng thái"), ("Source", "Nguồn"), ("Reviewed by", "Người duyệt")],
            rows, [0.9, 5.0, 2.2, 1.7, 1.7, 1.7, 2.1, 1.7], size=8)
    D.p(*ND.TS_NOTE)


# =============================================================================================== build
def build(toc_pages=None) -> Doc:
    D = Doc(toc_pages)
    cover(D)
    certificate(D)
    front_matter(D)
    divider(D, "Review 01", "Đánh giá lần 1", ["Form 01  Problem Definition", "Form 02  Customer Requirements Specifications"])
    problem_definition(D)
    crs(D)
    divider(D, "Review 02", "Đánh giá lần 2",
            ["Form 03  Data Flow Diagram", "Form 04  Entity Relationship Diagram", "Form 05  Table Design",
             "Form 06  Site Map", "Form 07  Algorithms"])
    dfd(D)
    erd(D)
    table_design(D)
    sitemap(D)
    algorithms(D)
    divider(D, "Review 03", "Đánh giá lần 3",
            ["Form 08  Screen Design", "Form 09  Testing", "Form 10  Final Checklist", "Form 11  Task Sheet"])
    screen_design(D)
    testing(D)
    final_checklist(D)
    task_sheet(D)
    D.fill_toc()
    cp = D.d.core_properties
    cp.title = L("HarmonyMentor AI – eProject Semester II Review 01, 02, 03", "HarmonyMentor AI – eProject Học kỳ II, Đánh giá lần 01, 02, 03")
    cp.subject = L("Design documentation (bilingual EN/VI)", "Tài liệu thiết kế (tiếng Việt)")
    cp.author = L("HarmonyMentor project group", "Nhóm đồ án HarmonyMentor")
    cp.comments = L(f"Built from branch phuc-music, commit {ND.COMMIT}", f"Dựng từ nhánh phuc-music, commit {ND.COMMIT}")
    D.d.save(OUT)
    return D


def render_pdf(docx: Path) -> Path:
    out = Path(tempfile.mkdtemp(prefix="review123_pdf_"))
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(out), str(docx)],
                   check=True, capture_output=True)
    return out / (docx.stem + ".pdf")


def measure_toc(pdf: Path, headings) -> dict[str, int]:
    txt = subprocess.run(["pdftotext", str(pdf), "-"], check=True, capture_output=True, text=True).stdout
    pages = txt.split("\f")
    norm = lambda s: re.sub(r"\s+", "", s)  # noqa: E731
    npages = [norm(p) for p in pages]
    found, start = {}, 2  # bỏ qua bìa và trang chứng nhận
    for _, text in headings:
        key = norm(text)
        for i in range(start, len(npages)):
            # dòng mục lục có dấu chấm dẫn ngay sau tên mục; tiêu đề thật thì không
            hits = [m.end() for m in re.finditer(re.escape(key), npages[i])]
            if any(not npages[i][e:e + 1] in (".", "…") for e in hits):
                found[text] = i + 1
                start = i
                break
    return found


def main():
    cached = json.loads(TOC_CACHE.read_text(encoding="utf-8")) if TOC_CACHE.exists() else {}
    D = build(cached)
    print(f"Đã dựng {OUT}")
    if "--pdf" in sys.argv:
        pdf = render_pdf(OUT)
        pages = measure_toc(pdf, D.headings)
        if pages != cached:
            TOC_CACHE.write_text(json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
            build(pages)
            pdf = render_pdf(OUT)
            pages2 = measure_toc(pdf, D.headings)
            if pages2 != pages:
                TOC_CACHE.write_text(json.dumps(pages2, ensure_ascii=False, indent=1), encoding="utf-8")
                build(pages2)
                pdf = render_pdf(OUT)
        missing = [t for _, t in D.headings if t not in pages]
        print(f"PDF soát: {pdf}  (mục lục: {len(pages)}/{len(D.headings)} mục có số trang; thiếu: {missing})")


if __name__ == "__main__":
    main()

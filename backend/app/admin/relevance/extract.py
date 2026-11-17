"""Trích chữ từ từng loại tệp. Không bao giờ chạy nội dung tệp: PDF/DOCX chỉ đọc chữ, XML bị chặn DOCTYPE/ENTITY."""

from __future__ import annotations

import io
import re
import struct
import zipfile
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

from ...core.ai_config import relevance_config
from . import ocr
from .errors import RelevanceError
from .sniff import sniff_kind


@dataclass
class Extracted:
    kind: str
    pages: list[str]
    notes: list[str] = field(default_factory=list)   # ghi chú cho Admin (đã OCR, đã cắt bớt...)
    music_native: bool = False                        # MusicXML/MIDI: bản thân tệp là dữ liệu âm nhạc


def split_text(text: str, chars_per_page: int = 3000) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    pages, cur = [], ""
    for p in paragraphs:
        if cur and len(cur) + len(p) > chars_per_page:
            pages.append(cur)
            cur = ""
        cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        pages.append(cur)
    return pages


def extract(filename: str, data: bytes) -> Extracted:
    cfg = relevance_config()
    if not data:
        raise RelevanceError("FILE_EMPTY", "Tệp rỗng.")
    if len(data) > cfg.max_bytes:
        raise RelevanceError("FILE_TOO_BIG", f"Tệp lớn hơn {cfg.max_bytes // (1024 * 1024)} MB.", 413)
    kind = sniff_kind(filename, data, cfg.max_unzipped_bytes)
    try:
        if kind == "pdf":
            result = _pdf(data)
        elif kind == "docx":
            result = _docx(data)
        elif kind == "image":
            result = Extracted("image", split_text(ocr.ocr_image_bytes(data)), ["Đã đọc chữ từ ảnh bằng OCR."])
        elif kind == "musicxml":
            result = _musicxml(data)
        elif kind == "mxl":
            result = _mxl(data)
        elif kind == "midi":
            result = _midi(data)
        else:
            result = Extracted("text", split_text(data.decode("utf-8", errors="replace")))
    except RelevanceError:
        raise
    except Exception as exc:  # thư viện đọc tệp ném nhiều loại lỗi với tệp hỏng
        raise RelevanceError("FILE_UNREADABLE", "Không đọc được nội dung tệp (có thể bị hỏng).") from exc
    if not any(p.strip() for p in result.pages):
        raise RelevanceError("FILE_NO_TEXT", "Không trích được chữ nào từ tệp này.")
    return result


def _pdf(data: bytes) -> Extracted:
    from pypdf import PdfReader

    cfg = relevance_config()
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        raise RelevanceError("FILE_ENCRYPTED", "PDF bị khóa mật khẩu, không đọc được.")
    pages = [(page.extract_text() or "").strip() for page in reader.pages[: cfg.max_pages]]
    notes: list[str] = []
    scanned = [i for i, t in enumerate(pages) if len(t) < cfg.ocr_min_chars_per_page]
    if scanned and len(scanned) >= max(1, len(pages) // 2) and not ocr.ocr_available():
        if not any(pages):
            ocr.require_ocr()                  # không có chữ nào và không có OCR: báo OCR_UNAVAILABLE
        notes.append("Một số trang không có chữ (có thể là ảnh quét) và máy chủ chưa cài OCR nên các trang đó bị bỏ qua.")
    elif scanned and len(scanned) >= max(1, len(pages) // 2):   # đa số trang không có chữ: PDF ảnh quét
        for i, text in ocr.ocr_pdf_pages(data, scanned).items():
            pages[i] = text.strip()
        notes.append(f"PDF dạng ảnh quét: đã đọc {min(len(scanned), cfg.ocr_max_pages)} trang bằng OCR.")
    return Extracted("pdf", pages, notes)


def _docx(data: bytes) -> Extracted:
    from docx import Document

    doc = Document(io.BytesIO(data))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(c.text for c in row.cells))
    return Extracted("docx", split_text("\n\n".join(parts)))


# --- MusicXML ------------------------------------------------------------------------------------------

def _parse_xml(data: bytes) -> ET.Element:
    # ENTITY là đường tấn công "billion laughs"/XXE; MusicXML thật không cần.
    if b"<!entity" in data.lower():
        raise RelevanceError("XML_UNSAFE", "Tệp XML khai báo ENTITY, không nhận để tránh tấn công XML.", 415)
    return ET.fromstring(data)


def _musicxml(data: bytes) -> Extracted:
    root = _parse_xml(data)
    if root.tag not in ("score-partwise", "score-timewise"):
        raise RelevanceError("FILE_CONTENT_MISMATCH", "Tệp XML này không phải MusicXML.", 415)
    lines = ["Tệp MusicXML (bản nhạc có ký hiệu)."]
    title = root.findtext("./work/work-title") or root.findtext("./movement-title")
    if title:
        lines.append(f"Tên bản nhạc: {title.strip()}.")
    parts = [p.findtext("part-name") or "" for p in root.findall("./part-list/score-part")]
    if parts:
        lines.append("Các bè: " + ", ".join(p.strip() for p in parts if p.strip()) + ".")
    fifths = root.findtext(".//key/fifths")
    mode = root.findtext(".//key/mode")
    if fifths is not None:
        lines.append(f"Khóa giọng: {fifths} dấu thăng(+)/giáng(-), điệu {mode or 'major'}.")
    beats, beat_type = root.findtext(".//time/beats"), root.findtext(".//time/beat-type")
    if beats and beat_type:
        lines.append(f"Nhịp {beats}/{beat_type}.")
    chords = []
    for h in root.iter("harmony"):
        step = h.findtext("root/root-step") or ""
        alter = {"1": "#", "-1": "b"}.get((h.findtext("root/root-alter") or "").strip(), "")
        kind = (h.find("kind").get("text") if h.find("kind") is not None else "") or (h.findtext("kind") or "")
        chords.append(f"{step}{alter}{kind}")
    if chords:
        lines.append("Hợp âm: " + " ".join(chords[:64]) + ".")
    lines.append(f"Có {len(root.findall('.//measure'))} ô nhịp và {len(root.findall('.//note'))} nốt.")
    return Extracted("musicxml", ["\n".join(lines)], music_native=True)


def _mxl(data: bytes) -> Extracted:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".xml") and not n.startswith("META-INF")]
        if not names:
            raise RelevanceError("FILE_CONTENT_MISMATCH", "Tệp MXL không chứa bản nhạc MusicXML.", 415)
        return _musicxml(z.read(names[0]))


# --- MIDI ----------------------------------------------------------------------------------------------

def _midi(data: bytes) -> Extracted:
    """Đọc tối thiểu cấu trúc MIDI (tên bè, số nốt, nhịp, giọng). Không cần thư viện ngoài."""
    if len(data) < 14 or data[:4] != b"MThd":
        raise RelevanceError("FILE_CONTENT_MISMATCH", "Tệp MIDI không hợp lệ.", 415)
    fmt, ntracks, division = struct.unpack(">HHH", data[8:14])
    pos, names, notes, key_sig, time_sig = 14, [], 0, None, None
    for _ in range(min(ntracks, 64)):
        if data[pos:pos + 4] != b"MTrk":
            break
        (length,) = struct.unpack(">I", data[pos + 4:pos + 8])
        track, pos = data[pos + 8:pos + 8 + length], pos + 8 + length
        i, running = 0, 0
        while i < len(track):
            while i < len(track) and track[i] & 0x80:      # delta time
                i += 1
            i += 1
            if i >= len(track):
                break
            status = track[i]
            if status == 0xFF:
                mtype, i = track[i + 1], i + 2
                n = 0
                while track[i] & 0x80:
                    n = (n << 7) | (track[i] & 0x7F)
                    i += 1
                n = (n << 7) | track[i]
                i += 1
                payload, i = track[i:i + n], i + n
                if mtype == 0x03:
                    names.append(payload.decode("latin-1").strip())
                elif mtype == 0x59 and len(payload) == 2 and key_sig is None:
                    sf = payload[0] - 256 if payload[0] > 127 else payload[0]
                    key_sig = f"{sf} dấu thăng(+)/giáng(-), điệu {'thứ' if payload[1] else 'trưởng'}"
                elif mtype == 0x58 and len(payload) >= 2 and time_sig is None:
                    time_sig = f"{payload[0]}/{2 ** payload[1]}"
            elif status in (0xF0, 0xF7):
                n = 0
                i += 1
                while track[i] & 0x80:
                    n = (n << 7) | (track[i] & 0x7F)
                    i += 1
                n = (n << 7) | track[i]
                i += 1 + n
            else:
                if status & 0x80:
                    running, i = status, i + 1
                kind = running & 0xF0
                size = 1 if kind in (0xC0, 0xD0) else 2
                if kind == 0x90 and i + 1 < len(track) and track[i + 1] > 0:
                    notes += 1
                i += size
    lines = ["Tệp MIDI (bản nhạc dạng dữ liệu nốt)."]
    lines.append(f"Có {ntracks} bè, {notes} nốt, độ phân giải {division} xung/phách.")
    if names:
        lines.append("Tên bè: " + ", ".join(n for n in names if n) + ".")
    if key_sig:
        lines.append(f"Khóa giọng: {key_sig}.")
    if time_sig:
        lines.append(f"Nhịp {time_sig}.")
    if notes == 0:
        raise RelevanceError("FILE_NO_TEXT", "Tệp MIDI không có nốt nhạc nào.")
    return Extracted("midi", ["\n".join(lines)], music_native=True)

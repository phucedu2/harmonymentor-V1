"""Nhận dạng loại tệp bằng byte thật, không tin đuôi tên tệp (đuôi .pdf có thể là tệp .exe)."""

from __future__ import annotations

import io
import zipfile

from .errors import RelevanceError

# Đuôi được phép -> nhóm nội dung.
EXT_KIND = {"pdf": "pdf", "docx": "docx", "md": "text", "txt": "text", "png": "image", "jpg": "image", "jpeg": "image",
            "webp": "image", "xml": "musicxml", "musicxml": "musicxml", "mxl": "mxl", "mid": "midi", "midi": "midi"}
ALLOWED_LABEL = "PDF, DOCX, ảnh (PNG/JPG/WEBP), MusicXML, MIDI, MD hoặc TXT"


def _unsupported() -> RelevanceError:
    return RelevanceError("FILE_CONTENT_MISMATCH", f"Nội dung tệp không đúng loại ghi ở tên tệp, hoặc không phải loại được nhận ({ALLOWED_LABEL}).", 415)


def sniff_kind(filename: str, data: bytes, max_unzipped: int) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in EXT_KIND:
        raise RelevanceError("FILE_TYPE", f"Chỉ nhận {ALLOWED_LABEL}.", 415)
    claimed = EXT_KIND[ext]
    head = data[:16]
    if claimed == "pdf":
        ok = head.startswith(b"%PDF-")
    elif claimed == "image":
        ok = head.startswith(b"\x89PNG\r\n\x1a\n") or head.startswith(b"\xff\xd8\xff") or (head[:4] == b"RIFF" and head[8:12] == b"WEBP")
    elif claimed == "midi":
        ok = head.startswith(b"MThd")
    elif claimed in ("docx", "mxl"):
        ok = head.startswith(b"PK\x03\x04") and _zip_ok(data, max_unzipped, "word/document.xml" if claimed == "docx" else None)
    elif claimed == "musicxml":
        ok = data.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"<")
    else:  # text
        ok = _looks_like_text(data)
    if not ok:
        raise _unsupported()
    return claimed


def _zip_ok(data: bytes, max_unzipped: int, required: str | None) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos = z.infolist()
            if sum(i.file_size for i in infos) > max_unzipped or len(infos) > 2000:
                raise RelevanceError("ZIP_TOO_BIG", "Tệp nén chứa quá nhiều dữ liệu khi giải nén, không nhận.", 413)
            return required is None or required in {i.filename for i in infos}
    except zipfile.BadZipFile:
        return False


def _looks_like_text(data: bytes) -> bool:
    """Văn bản thật: không có byte NUL và gần như toàn ký tự đọc được. Byte rác thì không qua."""
    if b"\x00" in data:
        return False
    text = data.decode("utf-8", errors="replace")
    if not text:
        return False
    bad = sum(1 for c in text if c == "�" or (ord(c) < 32 and c not in "\n\r\t"))
    return bad / len(text) < 0.02

"""OCR dự phòng cho PDF ảnh quét và tệp ảnh (T1). Cần chương trình tesseract kèm gói tiếng Việt (Dockerfile đã cài)."""

from __future__ import annotations

import io
import shutil

from ...core.ai_config import relevance_config
from .errors import RelevanceError


def ocr_available() -> bool:
    return shutil.which("tesseract") is not None


def require_ocr() -> None:
    if not ocr_available():
        raise RelevanceError("OCR_UNAVAILABLE", "Máy chủ chưa cài OCR (tesseract) nên chưa đọc được ảnh hoặc PDF dạng quét. "
                                                "Hãy dán chữ vào ô nhập hoặc dùng PDF/DOCX có chữ.", 503)


def ocr_image_bytes(data: bytes) -> str:
    require_ocr()
    import pytesseract
    from PIL import Image

    cfg = relevance_config()
    with Image.open(io.BytesIO(data)) as img:
        img.load()
        if img.width * img.height > 40_000_000:
            raise RelevanceError("IMAGE_TOO_BIG", "Ảnh quá lớn để OCR.", 413)
        return pytesseract.image_to_string(img, lang=cfg.ocr_lang)


def ocr_pdf_pages(data: bytes, page_indexes: list[int]) -> dict[int, str]:
    """Dựng lại các trang PDF thành ảnh rồi OCR. Giới hạn số trang để không treo máy chủ."""
    require_ocr()
    import pypdfium2 as pdfium
    import pytesseract

    cfg = relevance_config()
    out: dict[int, str] = {}
    pdf = pdfium.PdfDocument(data)
    try:
        for i in page_indexes[: cfg.ocr_max_pages]:
            image = pdf[i].render(scale=2).to_pil()
            out[i] = pytesseract.image_to_string(image, lang=cfg.ocr_lang)
    finally:
        pdf.close()
    return out

"""Sổ nhận định mà Engine dựa vào (bản rút gọn của báo cáo vòng 2, §3 và §15.3).

Đây là dữ liệu để kiểm thử và hiển thị nguồn, không phải kho kiến thức chính thức.
`review_status` đổi thành "approved" chỉ khi người duyệt (bạn) đã duyệt.
Quy tắc khóa (QĐ-2.4): quy tắc Engine cần >= 2 nguồn + đã duyệt, trừ mục được miễn trừ.
"""

from __future__ import annotations

from dataclasses import dataclass

FANK = "Fankhauser, Working in Harmony (file .md, August 2026)"
OMT_WEB = "Open Music Theory, bản web viva.pressbooks.pub/openmusictheory (đọc 15/10/2026)"
OMT_PDF = "Open Music Theory v2 (file .md)"


@dataclass(frozen=True)
class Claim:
    id: str
    statement_vi: str
    sources: tuple[tuple[str, str], ...]  # (tài liệu, vị trí)
    review_status: str = "pending"        # pending | approved | rejected
    exemption_requested: bool = False     # xin miễn trừ ngưỡng 2 nguồn (câu hỏi 4)

    @property
    def source_count(self) -> int:
        return len({doc for doc, _ in self.sources})

    @property
    def meets_engine_threshold(self) -> bool:
        return self.review_status == "approved" and (self.source_count >= 2 or self.exemption_requested)


CLAIMS: dict[str, Claim] = {c.id: c for c in [
    Claim("MUS-PITCH-002", "Đô giữa = C4; số quãng tám đổi tại nốt C",
          ((FANK, "Ch. 1, tr. 10"), (OMT_PDF, "ASPN, tr. 55"))),
    Claim("MUS-ACC-002", "♯/♭ đổi 1 nửa cung, 𝄪/𝄫 đổi 2 nửa cung",
          ((OMT_PDF, "Half and Whole Steps, tr. 50"), (FANK, "Ch. 2, tr. 16 (tên các dấu)"))),
    Claim("MUS-INT-001", "Số quãng đếm chữ cái, tính cả nốt đầu",
          ((FANK, "Ch. 4, tr. 43"), (OMT_WEB, "chapter/intervals/"))),
    Claim("MUS-INT-002", "Quãng từ chủ âm âm giai trưởng: P1 M2 M3 P4 P5 M6 M7 P8",
          ((FANK, "Ch. 4, tr. 43–44"), (OMT_WEB, "chapter/intervals/ (major-scale method)"))),
    Claim("MUS-INT-003", "Tăng/giảm = lớn/nhỏ hơn nửa cung",
          ((FANK, "Ch. 4, tr. 43"), (OMT_WEB, "chapter/intervals/"))),
    Claim("MUS-INT-005", "A4 và d5 cùng 6 nửa cung nhưng khác tên",
          ((FANK, "Ch. 4, tr. 44; Ch. 5, tr. 52–53"), (OMT_WEB, "chapter/intervals/ (enharmonic)"))),
    Claim("MUS-INT-009", "Đảo quãng: cộng 9, M↔m, P↔P, A↔d",
          ((FANK, "Ch. 5, tr. 55"), (OMT_WEB, "chapter/intervals/"))),
    Claim("MUS-INT-010", "Quãng kép = quãng đơn + 7",
          ((FANK, "Ch. 5, tr. 55"), (OMT_WEB, "chapter/intervals/"))),
    Claim("MUS-SCALE-002", "Âm giai trưởng 2 2 1 2 2 2 1",
          ((FANK, "Ch. 2, tr. 16"), (OMT_WEB, "chapter/major-scales/"))),
    Claim("MUS-SCALE-003", "Mỗi âm giai dùng mỗi chữ cái đúng một lần",
          ((FANK, "Ch. 2, tr. 16"),), exemption_requested=True),
    Claim("MUS-SCALE-005", "Thứ tự nhiên 2 1 2 2 1 2 2",
          ((FANK, "Ch. 2, tr. 17"), (OMT_WEB, "chapter/minor-scales/"))),
    Claim("MUS-SCALE-006", "Thứ hòa âm 2 1 2 2 1 3 1",
          ((FANK, "Ch. 2, tr. 17"), (OMT_WEB, "chapter/minor-scales/"))),
    Claim("MUS-SCALE-007", "Thứ giai điệu: lên nâng 6, 7; xuống = tự nhiên",
          ((FANK, "Ch. 2, tr. 17"), (OMT_WEB, "chapter/minor-scales/"))),
    Claim("MUS-SCALE-008", "Dorian 2 1 2 2 2 1 2", ((FANK, "Ch. 2, tr. 18"),)),
    Claim("MUS-KEY-001", "Hóa biểu theo giọng trưởng hoặc thứ tự nhiên",
          ((FANK, "Ch. 3, tr. 34"), (OMT_WEB, "chapter/minor-scales/"))),
    Claim("MUS-KEY-002", "Thứ tự dấu thăng FCGDAEB, dấu giáng BEADGCF",
          ((FANK, "Ch. 3, tr. 35 (bản .md in lỗi 'FCGBDAEB')"), (OMT_WEB, "chapter/major-scales/"))),
    Claim("MUS-KEY-003", "Nhận diện giọng trưởng từ hóa biểu",
          ((FANK, "Ch. 3, tr. 35"), (OMT_WEB, "chapter/major-scales/"))),
    Claim("MUS-KEY-004", "Giọng thứ tương quan thấp hơn quãng 3 thứ",
          ((FANK, "Ch. 3, tr. 36"), (OMT_WEB, "chapter/minor-scales/"))),
    Claim("MUS-KEY-005", "Tối đa 7 dấu hóa",
          ((FANK, "Ch. 3, tr. 36"), (OMT_WEB, "chapter/major-scales/"))),
    Claim("MUS-TRIAD-001", "Bốn loại hợp âm ba theo quãng 3 và 5 từ nốt gốc",
          ((OMT_WEB, "chapter/triads/"),), exemption_requested=True),
    Claim("MUS-TRIAD-002", "Giọng trưởng: I ii iii IV V vi vii°",
          ((FANK, "Ch. 12, tr. 120"), (OMT_WEB, "chapter/triads/"))),
    Claim("MUS-7TH-001", "V7 = ba trưởng + 7 thứ",
          ((FANK, "Ch. 16, tr. 150"), (OMT_WEB, "chapter/seventh-chords/"))),
    Claim("MUS-7TH-004", "maj7, m7, nửa giảm, giảm 7",
          ((OMT_WEB, "chapter/seventh-chords/"),), exemption_requested=True),
    Claim("MUS-ROMAN-001", "Hoa = trưởng, thường = thứ, ° = giảm",
          ((FANK, "Ch. 12, tr. 120"), (OMT_WEB, "chapter/roman-numerals/"))),
    Claim("MUS-ROMAN-006", "Số hiệu: 7, ø7, °7; 6 = thể đảo 1",
          ((FANK, "Ch. 15–17, tr. 146–157"), (OMT_WEB, "chapter/roman-numerals/"))),
    Claim("MUS-TRIAD-005", "Thể đảo do nốt bass quyết định", ((FANK, "Ch. 17, tr. 157"),)),
    Claim("MUS-CHSYM-005", "Bass của hợp âm gạch chéo không cần thuộc hợp âm",
          ((OMT_WEB, "chapter/chord-symbols/"),)),
    Claim("MUS-RHY-001", "Giá trị trường độ 2:1, chấm dôi thêm một nửa",
          ((OMT_WEB, "chapter/rhythmic-rest-values/ (Notating Rhythm)"),), exemption_requested=True),
    Claim("MUS-METER-002", "Số chỉ nhịp: trên = số phách, dưới = giá trị phách",
          ((FANK, "Ch. 7, tr. 68–69"),)),
]}

# Mục SRS yêu cầu nhưng chưa có nguồn nào đã đọc.
UNSOURCED = {
    "sus2/sus4": "SRS 4.4.1 có sus2, sus4 nhưng chưa đọc nguồn nào định nghĩa.",
    "IM7 notation": "Ký hiệu số La Mã cho hợp âm bảy trưởng (IM7) chưa có nguồn (Fankhauser Ch. 23 thiếu).",
}

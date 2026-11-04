"""Câu trả lời viết sẵn khi không gọi được AI hoặc không nên gọi (nguyên tắc 3, TC-10)."""

from __future__ import annotations

from typing import Sequence

from .retriever import Hit

OUT_OF_SCOPE = ("Mình chỉ hỗ trợ nhạc lý trong khóa HarmonyMentor (nốt, quãng, hợp âm, âm giai, chức năng, "
                "vòng hòa âm). Bạn thử hỏi một câu về các chủ đề đó nhé.")
INJECTION = "Mình không làm theo yêu cầu đó được. Mình ở đây để giúp bạn học nhạc lý trong khóa."
UNSURE = "Mình chưa chắc về câu này vì bài học hiện có chưa nói rõ."
UNAVAILABLE = "Trợ lý AI đang tạm nghỉ, nên mình trả lời bằng phần bài học liên quan nhất."
BUSY = "Trợ lý AI chưa trả lời được lúc này, nên mình trả lời bằng phần bài học liên quan nhất."

# Gợi mở theo mã lỗi, không chứa đáp án (mức 1–2). Mức 3 thêm lời giải của câu (explanation đã duyệt).
ERROR_HINTS: dict[str, tuple[str, str]] = {
    "ENHARMONIC_SPELLING": ("Âm thanh đúng nhưng tên nốt chưa đúng chữ cái. Nhớ quy tắc: quãng 3 cách 2 chữ cái, "
                            "quãng 5 cách 4 chữ cái, quãng 7 cách 6 chữ cái.",
                            "Viết lần lượt các chữ cái cách nhau một chữ (ví dụ C, E, G, B) rồi mới thêm dấu thăng/giáng."),
    "WRONG_ROOT": ("Nốt gốc chưa đúng. Nốt gốc chính là chữ cái đứng đầu ký hiệu hợp âm.",
                   "Kiểm lại nốt đầu tiên bạn viết có trùng chữ cái và dấu hóa của ký hiệu không."),
    "MISSING_TONE": ("Câu trả lời còn thiếu nốt. Hợp âm ba có 3 nốt, hợp âm bảy có 4 nốt.",
                     "Đếm số nốt bạn đã viết và so với số nốt hợp âm cần có."),
    "EXTRA_TONE": ("Câu trả lời thừa nốt so với hợp âm được hỏi.",
                   "Xem lại công thức quãng của loại hợp âm này, bỏ nốt không nằm trong công thức."),
    "THIRD_QUALITY": ("Quãng 3 chưa đúng tính chất. Trưởng là 4 nửa cung, thứ là 3 nửa cung.",
                      "Đếm nửa cung từ nốt gốc lên nốt quãng 3 bạn viết."),
    "FIFTH_QUALITY": ("Quãng 5 chưa đúng. Quãng 5 đúng là 7 nửa cung; giảm là 6, tăng là 8.",
                      "Đếm nửa cung từ nốt gốc lên nốt quãng 5 bạn viết."),
    "SEVENTH_QUALITY": ("Quãng 7 chưa đúng loại. 7 trưởng cách gốc 11 nửa cung, 7 thứ cách 10 nửa cung.",
                        "So ký hiệu: maj7 dùng quãng 7 trưởng, 7 và m7 dùng quãng 7 thứ."),
    "NOT_IN_KEY": ("Có nốt không thuộc giọng đang xét.", "Viết âm giai của giọng ra rồi kiểm từng nốt."),
    "WRONG_INTERVAL_SIZE": ("Số của quãng chưa đúng. Đếm chữ cái, tính cả nốt đầu và nốt cuối.",
                            "Đếm chữ cái từ nốt dưới lên nốt trên, ví dụ C đến G là 5 chữ cái."),
    "WRONG_INTERVAL_QUALITY": ("Số quãng đúng nhưng tính chất chưa đúng.",
                               "Sau khi có số quãng, đếm nửa cung để biết trưởng, thứ, đúng, tăng hay giảm."),
    "WRONG_SCALE_DEGREE_ORDER": ("Thứ tự nốt trong âm giai chưa đúng.",
                                 "Mỗi chữ cái xuất hiện đúng một lần theo thứ tự đi lên."),
    "ROMAN_DEGREE": ("Bậc số La Mã chưa đúng.", "Đếm nốt gốc hợp âm là bậc mấy của âm giai giọng đó."),
    "ROMAN_QUALITY_MARK": ("Cách viết hoa/thường hoặc ký hiệu của số La Mã chưa đúng.",
                           "Hợp âm trưởng viết hoa, thứ viết thường, giảm thêm °."),
}
GENERIC_HINT = ("Câu trả lời chưa đúng. Hãy đọc lại phần lý thuyết của bài.",
                "So từng phần câu trả lời với định nghĩa trong bài trước khi nộp lại.")


def explain_text(codes: Sequence[str], level: int, explanation: str | None) -> str:
    first = next((c for c in codes if c in ERROR_HINTS), None)
    l1, l2 = ERROR_HINTS.get(first, GENERIC_HINT) if first else GENERIC_HINT
    if level <= 1:
        return l1
    if level == 2:
        return f"{l1} {l2}"
    return f"{l1} {l2} {explanation}" if explanation else f"{l1} {l2}"


def lesson_pointer(hits: Sequence[Hit], titles: dict[str, str]) -> str:
    if not hits:
        return ""
    h = hits[0].chunk
    return f" Bạn xem lại “{h.title}” trong {titles.get(h.lesson_id, h.lesson_id)}."

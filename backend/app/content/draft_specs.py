"""Nội dung NHÁP của nhánh phuc-music (Bước 2): bài L09–L12 và mục "Dùng vào sáng tác" cho L01–L04.

Vì sao tách file: mọi thứ ở đây do Claude soạn, chưa qua Đạt/Astra duyệt, nên chỉ hiện khi bật
SHOW_DRAFT_CONTENT (dev/test). Người học mặc định không thấy, và nội dung bài đã phát hành không đổi.
Thứ tự và module theo SRS 2.1 Bảng 7. Định vị nguồn của bài nháp chưa xác minh từng trang.
"""

from __future__ import annotations

from typing import Any

from .curriculum_specs import (
    FANK_CHROMATIC,
    FANK_DIATONIC,
    FANK_FUND,
    KH_CH2,
    KH_CH5,
    KH_CH11,
    OMT_FUNCTION,
    OMT_INTERVALS,
    OMT_MODAL,
    OMT_ROMAN,
    OMT_TONICIZATION,
    OMT_VOICINGS,
    TER_CH1,
    TER_CH3,
    f,
    src,
)

DRAFT = "draft"

# Nhãn mục tiêu sản phẩm (Phúc chọn 31/10: Bảng 7 + nhãn A/B).
# A = dựng được backing track ngắn; B = tạo vòng hợp âm lạ mà dễ nghe và giải thích được vì sao lạ.
GOAL_LABELS = {"A": "Mục tiêu A: backing track", "B": "Mục tiêu B: vòng hợp âm lạ"}
LESSON_GOALS: dict[str, list[str]] = {
    "L01": ["A"], "L02": ["A"], "L03": ["A", "B"], "L04": ["A"],
    "L09": ["B"], "L10": ["A"], "L11": ["A"], "L12": ["A", "B"],
}
_UNVERIFIED = "Định vị nguồn do Claude đề xuất, chưa đối chiếu trang; Đạt/Astra xác minh trước khi phát hành."

# SRS 2.1 Bảng 7: thứ tự học là thứ tự trong bảng, không phải thứ tự mã bài.
CURRICULUM_MODULES: list[tuple[str, list[str]]] = [
    ("M1. Nền tảng", ["L01", "L02", "L09", "L10"]),
    ("M2. Hòa âm chức năng", ["L03", "L05"]),
    ("M3. Pop", ["L11", "L06"]),
    ("M4. Jazz", ["L04", "L07", "L08"]),
    ("M5. Thực hành tích hợp", ["L12"]),
]


def module_order() -> dict[str, tuple[int, str]]:
    """lesson_id → (thứ tự 1..12, tên module) suy từ Bảng 7."""
    result: dict[str, tuple[int, str]] = {}
    for module, lesson_ids in CURRICULUM_MODULES:
        for lesson_id in lesson_ids:
            result[lesson_id] = (len(result) + 1, module)
    return result


def _draft_lesson(lesson_id: str, title: str, objectives: list[str], sources: list[dict[str, Any]],
                  outline: list[str], compose: list[str]) -> dict[str, Any]:
    order, module = module_order()[lesson_id]
    return {
        "id": lesson_id, "order": order, "track": module, "title": title, "status": DRAFT,
        "objectives": objectives, "skills": [], "sources": sources,
        "blocks": [
            (f"{lesson_id}-B01", "callout", {"status": DRAFT, "title": "Bản nháp, chưa duyệt",
                                            "prompt": "Dàn ý do Claude đề xuất để Đạt/Astra soạn và kiểm định. Chưa có câu hỏi và thẻ ôn."}),
            (f"{lesson_id}-B02", "theory", {"status": DRAFT, "title": "Dàn ý bài", "items": outline}),
            (f"{lesson_id}-B03", "compose_link", {"status": DRAFT, "title": "Dùng vào sáng tác",
                                                 "goals": LESSON_GOALS[lesson_id], "items": compose}),
        ],
        "exercises": [], "review_items": [],
    }


DRAFT_LESSON_SPECS: list[dict[str, Any]] = [
    _draft_lesson(
        "L09", "Âm giai thứ và giọng thứ",
        [
            "Dựng âm giai thứ tự nhiên, thứ hòa âm và thứ giai điệu (đi lên) trên một nốt gốc bất kỳ.",
            "Tìm giọng thứ tương ứng (cùng hóa biểu) và giọng thứ song song (cùng chủ âm) của một giọng trưởng.",
            "Gọi tên hợp âm điệu tính trong giọng thứ và giải thích vì sao bậc V thường là hợp âm trưởng.",
        ],
        [src("OMT_V2", "Fundamentals → Minor Scales", _UNVERIFIED), FANK_FUND, TER_CH1],
        [
            "Âm giai thứ tự nhiên: công thức cung/nửa cung, so với âm giai trưởng cùng chủ âm (bậc 3, 6, 7 hạ).",
            "Thứ hòa âm: nâng bậc 7 để có nốt dẫn; thứ giai điệu đi lên: nâng bậc 6 và 7.",
            "Giọng tương ứng (A thứ ↔ C trưởng) và giọng song song (C thứ ↔ C trưởng).",
            "Hợp âm điệu tính trong giọng thứ; V và vii° khi dùng bậc 7 nâng.",
        ],
        [
            "Vòng i – iv – V – i trong giọng thứ cho cảm giác kết rõ nhờ nốt dẫn ở hợp âm V.",
            "Mượn hợp âm từ giọng song song (L06) bắt đầu từ việc biết giọng thứ có những hợp âm nào.",
        ],
    ),
    _draft_lesson(
        "L10", "Nhịp, phách và tiết tấu cơ bản",
        [
            "Phân biệt phách, ô nhịp và số chỉ nhịp 4/4, 3/4.",
            "Đọc trường độ nốt tròn, trắng, đen, móc đơn và dấu lặng tương ứng.",
            "Xếp hợp âm theo phách để dựng một backing track ngắn.",
        ],
        [src("OMT_V2", "Fundamentals → Simple Meter and Time Signatures", _UNVERIFIED), FANK_FUND],
        [
            "Phách và nhịp: phách mạnh, phách nhẹ; số chỉ nhịp cho biết mỗi ô có mấy phách và phách là nốt gì.",
            "Trường độ và dấu lặng: tròn = 4 phách, trắng = 2, đen = 1, móc đơn = 1/2 (trong 4/4).",
            "Kiểu đệm cơ bản: giữ cả ô, đánh mỗi phách, nhấn phách 2 và 4.",
        ],
        [
            "Xưởng Sáng tác lưu thời gian theo phách (nguyên tắc 6): mỗi hợp âm có điểm bắt đầu và độ dài tính bằng phách.",
            "Backing track 4 ô nhịp 4/4 = 16 phách; đổi hợp âm ở phách 1 của mỗi ô là cách dễ nghe nhất để bắt đầu.",
        ],
    ),
    _draft_lesson(
        "L11", "Vòng hợp âm Pop và phối hợp âm cho giai điệu",
        [
            "Nhận ra các vòng hợp âm Pop thường gặp bằng số La Mã, ví dụ I–V–vi–IV và I–vi–IV–V.",
            "Chuyển một vòng hợp âm sang giọng khác bằng số La Mã.",
            "Chọn hợp âm chứa nốt giai điệu ở phách mạnh để phối hợp âm cho một giai điệu đơn giản.",
        ],
        [src("OMT_V2", "Popular Music → Harmonic Schemas", _UNVERIFIED), OMT_ROMAN, FANK_DIATONIC],
        [
            "Vòng hợp âm là chuỗi số La Mã lặp lại; cùng một vòng nghe giống nhau ở mọi giọng.",
            "Một vài vòng phổ biến: I–V–vi–IV, vi–IV–I–V, I–vi–IV–V.",
            "Phối hợp âm: nốt giai điệu ở phách mạnh nên là nốt của hợp âm đang vang.",
        ],
        [
            "Đây là mức độ lạ 0: mọi hợp âm nằm trong giọng. Muốn lạ hơn, xem L05 (át phụ) và L06 (hợp âm mượn).",
            "Mục tiêu A: chọn một vòng, đặt mỗi hợp âm 1 ô nhịp, là đã có backing track 4 ô.",
        ],
    ),
    _draft_lesson(
        "L12", "Phân tích và phối lại một ca khúc",
        [
            "Phân tích vòng hợp âm của một bài tự sáng tác hoặc bài mẫu không bản quyền bằng số La Mã và chức năng T–PD–D.",
            "Thay một hợp âm theo thang độ lạ 0–3 và giải thích vì sao nó nghe lạ mà vẫn dễ nghe.",
            "Xuất backing track từ xưởng Sáng tác (dự án cuối, chỉ phân tích, không tính mastery).",
        ],
        [OMT_FUNCTION, OMT_TONICIZATION, OMT_MODAL, FANK_CHROMATIC, KH_CH2, KH_CH5],
        [
            "Bước 1: ghi vòng hợp âm, gán số La Mã và chức năng.",
            "Bước 2: chọn một chỗ để thay: độ lạ 1 (át phụ, hợp âm mượn), 2 (mode, thay tritone), 3 (chromatic mediant).",
            "Bước 3: nghe lại, viết 2–3 câu giải thích hợp âm mới làm gì với chức năng và giọng.",
        ],
        [
            "Mục tiêu B: vòng 'lạ nhưng dễ nghe' là vòng giữ khung chức năng T–PD–D nhưng đổi màu ở một chỗ.",
            "Không dùng bài có bản quyền làm đề (nguyên tắc 11); dùng bài tự viết hoặc vòng mẫu.",
        ],
    ),
]

# Mục "Dùng vào sáng tác" cho bài đã có nội dung. Chèn trước khối tóm tắt, chỉ hiện ở chế độ nháp.
COMPOSE_BLOCKS: dict[str, list[str]] = {
    "L01": [
        "Hợp âm trưởng và thứ là 'gạch' đầu tiên của mọi vòng hợp âm. Thử ghép 4 hợp âm trên phím trắng, mỗi hợp âm 1 ô: C – Am – F – G.",
        "Hợp âm giảm (ví dụ Bdim) nghe căng; đặt nó ngay trước C để nghe nó 'muốn' đi về đâu.",
        "Mức độ lạ 0: mọi hợp âm trong bài này đều nằm trong giọng C trưởng.",
    ],
    "L02": [
        "Thay hợp âm ba bằng hợp âm bảy cùng bậc cho màu mềm hơn: Cmaj7 – Am7 – Dm7 – G7.",
        "G7 là hợp âm bảy át duy nhất trong giọng C trưởng, nên nó kéo về C rõ nhất.",
    ],
    "L03": [
        "Khung câu nhạc ngắn: T → PD → D → T, ví dụ C – F – G – C (I–IV–V–I).",
        "Đổi F thành Dm (cùng nhóm PD) để có màu khác mà chức năng giữ nguyên. Đây là cách 'đổi hợp âm an toàn'.",
    ],
    "L04": [
        "Backing track jazz ngắn: Dm7 – G7 – Cmaj7 – Cmaj7, mỗi hợp âm 1 ô.",
        "Guide tone: F giữ nguyên (3 của Dm7 thành 7 của G7) rồi xuống E; C xuống B rồi giữ B. Hai đường này làm vòng nghe liền mạch.",
    ],
}


# Thẻ ôn tự diễn đạt cho 3 ý mà câu hỏi đã chuyển sang trắc nghiệm (L01-Q05, L03-Q05, L04-Q06): trắc nghiệm
# chỉ kiểm "nhận ra", thẻ này buộc người học tự nói lại. Dạng thẻ tự đánh giá (rubric + contains_any).
# KHÔNG seed vào review_items (bảng này chưa có trạng thái nháp): chỉ hiện thành khối nháp để Đạt/Astra duyệt.
# Duyệt xong thì chép nguyên mục vào review_items của bài trong curriculum_specs.py.
DRAFT_REVIEW_ITEMS: dict[str, list[dict[str, Any]]] = {
    "L01": [
        f("L01-F09", "F# và Gb có thể là cùng một phím đàn. Vì sao vẫn phải chọn đúng một tên? Tự giải thích bằng lời của bạn, có ví dụ.",
          "Cùng cao độ nhưng tên nốt do quãng và khung chữ cái quyết định. Ví dụ quãng 3 trưởng trên D phải là F# "
          "(D–E–F là ba tên chữ cái); viết Gb thì thành quãng 4 giảm.",
          "pitch.spelling", "recall", "rubric",
          {"accepted": ["chữ cái", "chu cai", "quãng", "quang", "ngữ cảnh", "ngu canh", "spelling"]},
          {"mode": "contains_any", "strip_accents": True}, [OMT_INTERVALS, FANK_FUND]),
    ],
    "L03": [
        f("L03-F09", "Vì sao không gán chức năng (T, PD, D) chỉ bằng tên hợp âm? Giải thích bằng lời của bạn, có ví dụ.",
          "Chức năng phụ thuộc giọng và các hợp âm đứng trước, đứng sau. Ví dụ G là D (át) trong giọng C trưởng "
          "nhưng là T (chủ) trong giọng G trưởng.",
          "function.progression", "recall", "rubric",
          {"accepted": ["giọng", "giong", "ngữ cảnh", "ngu canh", "phụ thuộc", "phu thuoc", "context"]},
          {"mode": "contains_any", "strip_accents": True}, [OMT_FUNCTION, TER_CH3]),
    ],
    "L04": [
        f("L04-F09", "Nối hợp âm mượt (smooth voice leading) là gì? Mô tả bằng lời của bạn với G7 → Cmaj7.",
          "Giữ nốt chung, các nốt còn lại đi bước gần nhất. G7 → Cmaj7: B giữ nguyên (3 của G7 thành 7 của Cmaj7), "
          "F xuống nửa cung thành E (3 của Cmaj7).",
          "voicing.voice_leading", "recall", "rubric",
          {"accepted": ["nốt chung", "not chung", "giữ nguyên", "giu nguyen", "bước gần", "buoc gan", "common tone"]},
          {"mode": "contains_any", "strip_accents": True}, [OMT_VOICINGS, KH_CH11]),
    ],
}


def blocks_with_drafts(spec: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    """Khối của bài kèm các khối nháp ("Dùng vào sáng tác", thẻ ôn đề xuất) chèn trước khối tóm tắt cuối."""
    blocks = list(spec["blocks"])
    drafts = []
    items = COMPOSE_BLOCKS.get(spec["id"])
    if items:
        drafts.append((f"{spec['id']}-BSTAC", "compose_link", {"status": DRAFT, "title": "Dùng vào sáng tác",
                                                               "goals": LESSON_GOALS[spec["id"]], "items": items}))
    cards = DRAFT_REVIEW_ITEMS.get(spec["id"])
    if cards:
        drafts.append((f"{spec['id']}-BTHE", "theory", {
            "status": DRAFT, "title": "Thẻ ôn tự diễn đạt (nháp, chờ Đạt duyệt)",
            "items": [f"Mặt trước: {card['front']} · Đáp án: {card['back']}" for card in cards]}))
    at = len(blocks) - 1 if blocks and blocks[-1][1] == "summary" else len(blocks)
    return blocks[:at] + drafts + blocks[at:]

"""Bài L11 "Vòng hợp âm Pop" (điểm lệch 1, Phúc chọn Lai 12/11/2026).

Claude soạn, Phúc báo Thắng đã duyệt phạm vi; nội dung phát hành khi PR gộp và Đạt xem lại sau. Chỉ dùng vòng hợp âm
chung (I–V–vi–IV, vi–IV–I–V, I–vi–IV–V), KHÔNG ghi hợp âm bài hát cụ thể (quyết định 5A). Mọi hợp âm được
tests/test_lesson_l11.py đối chiếu Music Engine và bảng hợp âm của Harmony Lab. Dùng lại hai kỹ năng đã có
(function.progression, chord.triad_build) nên không đổi đồ thị kỹ năng.
"""

from __future__ import annotations

from typing import Any

from .curriculum_specs import FANK_DIATONIC, OMT_ROMAN, OMT_TRIADS, f, q, src

OMT_POP_SCHEMAS = src("OMT_V2", "Popular Music → Harmonic Schemas",
                      "Vòng hợp âm lặp lại trong nhạc pop; định vị trang do Claude đề xuất, chưa đối chiếu trang.")

L11_SPEC: dict[str, Any] = {
    "id": "L11", "order": 7, "track": "M3. Pop", "title": "Vòng hợp âm Pop",
    "status": "source_audited",
    "objectives": [
        "Nhận ra các vòng hợp âm Pop thường gặp bằng số La Mã: I–V–vi–IV, vi–IV–I–V, I–vi–IV–V.",
        "Chuyển một vòng hợp âm sang giọng khác bằng số La Mã.",
        "Mở vòng vừa học trong Harmony Lab và nghe nó chạy với kiểu đệm.",
    ],
    "skills": ["function.progression", "chord.triad_build"],
    "sources": [OMT_POP_SCHEMAS, OMT_ROMAN, FANK_DIATONIC],
    "blocks": [
        ("L11-B01", "callout", {
            "title": "Trước khi học vòng hợp âm",
            "prompt": "Bài này dùng lại hợp âm trưởng, hợp âm thứ và số La Mã đã học ở các bài trước. "
                      "Nếu chưa chắc Am là hợp âm vi của C major, hãy ôn lại bài về số La Mã trước."}),
        ("L11-B02", "theory", {
            "title": "1. Vòng hợp âm là gì",
            "paragraphs": [
                "Vòng hợp âm (chord loop) là một chuỗi ngắn, thường 4 hợp âm, lặp đi lặp lại suốt bài hát. Nhiều bài pop "
                "chỉ dùng một vòng cho cả đoạn.",
                "Ta ghi vòng bằng số La Mã (bậc của hợp âm trong giọng) chứ không ghi tên hợp âm. Nhờ vậy cùng một vòng "
                "dùng được ở mọi giọng: đổi giọng thì đổi tên hợp âm, còn dãy bậc giữ nguyên.",
            ]}),
        ("L11-B03", "glossary", {
            "title": "2. Thuật ngữ",
            "intro": "Ba thuật ngữ dùng trong cả bài.",
            "terms": [
                {"symbol": "I–V–vi–IV", "term": "Vòng hợp âm · chord loop",
                 "definition": "Chuỗi bậc hợp âm lặp lại. Số La Mã hoa là hợp âm trưởng, chữ thường là hợp âm thứ.",
                 "example": "Trong C major: C – G – Am – F"},
                {"symbol": "vi", "term": "Hợp âm bậc 6",
                 "definition": "Hợp âm thứ dựng trên bậc 6 của giọng trưởng, thường dùng để thêm màu buồn nhẹ.",
                 "example": "Am trong C major, Em trong G major"},
                {"symbol": "Giọng", "term": "Key",
                 "definition": "Nốt chủ và âm giai làm chuẩn cho các bậc. Đổi giọng là dời cả vòng lên hoặc xuống.",
                 "example": "C major, G major"},
            ]}),
        ("L11-B04", "theory", {
            "title": "3. Ba vòng phổ biến trong C major",
            "items": [
                "I–V–vi–IV = C – G – Am – F.",
                "vi–IV–I–V = Am – F – C – G. Cùng bốn hợp âm với vòng trên, bắt đầu từ vi nên nghe buồn hơn.",
                "I–vi–IV–V = C – Am – F – G. Vòng này thường gọi là vòng '50s' vì xuất hiện nhiều trong nhạc thập niên 1950.",
                "Cả ba vòng chỉ dùng hợp âm nằm trong C major (không nốt lạ ngoài giọng).",
            ]}),
        ("L11-B05", "progression", {
            "title": "4. Ví dụ: I – V – vi – IV",
            "prompt": "C → G → Am → F  =  I → V → vi → IV", "key": "C"}),
        ("L11-B06", "audio", {
            "title": "5. Nghe vòng I – V – vi – IV",
            "prompt": "Nghe bốn hợp âm rồi nghe vòng lặp lại. Chú ý hợp âm cuối (F) tự nhiên dẫn về C đầu vòng.",
            "progression": ["C", "G", "Am", "F"], "key": "C", "bpm": 80}),
        ("L11-BCP1", "checkpoint", {
            "title": "Đọc một vòng hợp âm",
            "exercise_id": "L11-Q01",
            "note": "Đổi từng số La Mã thành hợp âm của C major: I, V, vi, IV."}),
        ("L11-B07", "theory", {
            "title": "6. Đổi giọng bằng số La Mã",
            "paragraphs": [
                "Muốn chơi I–V–vi–IV ở G major, hãy tìm bậc 1, 5, 6, 4 của G major: G, D, Em, C. Vòng thành G – D – Em – C.",
                "Quy trình luôn giống nhau: viết âm giai trưởng của giọng mới, rồi lấy hợp âm ở các bậc cần dùng. "
                "Bậc nào là hợp âm trưởng hay thứ vẫn theo số La Mã (hoa = trưởng, thường = thứ).",
            ]}),
        ("L11-BCP2", "checkpoint", {
            "title": "Đổi giọng cho vòng hợp âm",
            "exercise_id": "L11-Q03",
            "note": "Viết âm giai G major trước, rồi chọn các bậc 1, 5, 6, 4."}),
        ("L11-B08", "compose_link", {
            "title": "Mở trong Harmony Lab",
            "goals": ["A"],
            "items": [
                "Vòng I–V–vi–IV trong C major nằm ngay trong Harmony Lab. Mỗi hợp âm một ô nhịp là đã có backing track 4 ô.",
                "Thử đổi giọng ở Harmony Lab và nghe vòng vẫn 'giống' dù tên hợp âm đổi.",
            ],
            "lab_key": "C", "lab_numerals": ["I", "V", "vi", "IV"]}),
        ("L11-B09", "summary", {
            "title": "Ghi nhớ",
            "items": [
                "Vòng hợp âm là chuỗi ngắn lặp lại; ghi bằng số La Mã để dùng ở mọi giọng.",
                "C major: I–V–vi–IV = C–G–Am–F, vi–IV–I–V = Am–F–C–G, I–vi–IV–V = C–Am–F–G.",
                "Đổi giọng: tìm các bậc tương ứng trong âm giai của giọng mới.",
            ]}),
    ],
    "exercises": [
        q("L11-Q01", "mcq", "Vòng I–V–vi–IV trong C major gồm những hợp âm nào, theo đúng thứ tự?", "function.progression", "exact",
          {"expected": "C-G-Am-F"}, {"normalize_dashes": True}, ["C-G-Am-F", "C-F-G-Am", "Am-F-C-G", "C-Am-F-G"],
          "Bậc 1, 5, 6, 4 của C major là C, G, Am, F. Am-F-C-G là vòng vi–IV–I–V, C-Am-F-G là vòng I–vi–IV–V, "
          "còn C-F-G-Am là thứ tự I–IV–V–vi, không phải vòng đã học.",
          [OMT_POP_SCHEMAS, OMT_ROMAN]),
        q("L11-Q02", "mcq", "Vòng vi–IV–I–V trong C major gồm những hợp âm nào, theo đúng thứ tự?", "function.progression", "exact",
          {"expected": "Am-F-C-G"}, {"normalize_dashes": True}, ["C-G-Am-F", "Am-F-C-G", "C-Am-F-G", "F-C-G-Am"],
          "Bậc 6, 4, 1, 5 của C major là Am, F, C, G. C-G-Am-F bắt đầu từ I (vòng I–V–vi–IV), C-Am-F-G là I–vi–IV–V, "
          "F-C-G-Am bắt đầu từ IV nên không phải vòng này.",
          [OMT_POP_SCHEMAS, OMT_ROMAN]),
        q("L11-Q03", "applied", "Chuyển vòng I–V–vi–IV sang G major. Chọn vòng đúng.", "function.progression", "exact",
          {"expected": "G-D-Em-C"}, {"normalize_dashes": True}, ["G-D-Em-C", "G-C-Em-D", "Em-C-G-D", "G-D-Bm-C"],
          "G major gồm G–A–B–C–D–E–F#. Bậc 1 = G, bậc 5 = D, bậc 6 = Em, bậc 4 = C. Em-C-G-D là vi–IV–I–V, "
          "G-C-Em-D đảo thứ tự bậc 4 và 6, còn Bm là bậc 3 chứ không phải bậc 6.",
          [OMT_POP_SCHEMAS, OMT_ROMAN]),
        q("L11-Q04", "active_recall", "Viết vòng I–vi–IV–V trong C major bằng tên hợp âm, ngăn cách bằng dấu -.", "function.progression", "exact",
          {"expected": "C-Am-F-G"}, {"normalize_dashes": True, "sequence": True}, None,
          "Bậc 1, 6, 4, 5 của C major là C, Am, F, G.", [OMT_POP_SCHEMAS, OMT_ROMAN]),
        q("L11-Q05", "build", "Dựng hợp âm Em (bậc vi của G major) bằng tên nốt.", "chord.triad_build", "music_engine",
          {"expected": ["E", "G", "B"]}, {"kind": "build_chord", "symbol": "Em"}, None,
          "Em là hợp âm thứ: nốt gốc E, quãng 3 thứ lên G, quãng 5 đúng lên B.", [OMT_TRIADS, OMT_ROMAN]),
        q("L11-Q06", "mcq", "Vì sao cùng một vòng I–V–vi–IV nghe 'giống nhau' dù chơi ở C major hay G major?", "function.progression", "exact",
          {"expected": "Vì mỗi hợp âm vẫn ở cùng bậc so với nốt chủ, chỉ dời cả vòng lên hoặc xuống"},
          {}, ["Vì mỗi hợp âm vẫn ở cùng bậc so với nốt chủ, chỉ dời cả vòng lên hoặc xuống",
               "Vì tên các hợp âm không đổi khi đổi giọng", "Vì hai giọng có cùng số dấu thăng",
               "Vì chỉ có bốn hợp âm trong mọi giọng"],
          "Số La Mã chỉ bậc của hợp âm trong giọng. Đổi giọng thì tên hợp âm đổi nhưng dãy bậc I–V–vi–IV giữ nguyên, "
          "nên khoảng cách giữa các hợp âm và cảm giác chuyển động vẫn vậy.",
          [OMT_POP_SCHEMAS, OMT_ROMAN]),
    ],
    "review_items": [
        f("L11-F01", "I–V–vi–IV trong C major", "C – G – Am – F", "function.progression", "recall", "exact",
          {"expected": "C-G-Am-F"}, {"normalize_dashes": True, "sequence": True}, [OMT_POP_SCHEMAS]),
        f("L11-F02", "vi–IV–I–V trong C major", "Am – F – C – G", "function.progression", "recall", "exact",
          {"expected": "Am-F-C-G"}, {"normalize_dashes": True, "sequence": True}, [OMT_POP_SCHEMAS]),
        f("L11-F03", "I–vi–IV–V trong C major", "C – Am – F – G", "function.progression", "recall", "exact",
          {"expected": "C-Am-F-G"}, {"normalize_dashes": True, "sequence": True}, [OMT_POP_SCHEMAS]),
        f("L11-F04", "I–V–vi–IV trong G major", "G – D – Em – C", "function.progression", "recall", "exact",
          {"expected": "G-D-Em-C"}, {"normalize_dashes": True, "sequence": True}, [OMT_POP_SCHEMAS, OMT_ROMAN]),
        f("L11-F05", "Dựng hợp âm Am", "A – C – E", "chord.triad_build", "build", "music_engine",
          {"expected": ["A", "C", "E"]}, {"kind": "build_chord", "symbol": "Am"}, [OMT_TRIADS]),
        f("L11-F06", "Ghi vòng hợp âm bằng số La Mã có lợi gì?", "Dùng được ở mọi giọng: đổi giọng thì tên hợp âm đổi, dãy bậc giữ nguyên.",
          "function.progression", "context", "rubric", {"accepted": ["mọi giọng", "moi giong", "đổi giọng", "doi giong", "bậc", "bac"]},
          {"mode": "contains_any", "strip_accents": True}, [OMT_ROMAN]),
    ],
}

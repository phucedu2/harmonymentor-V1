"""Source-audited curriculum specification for the 8-lesson HarmonyMentor MVP.

Phase 0.4B rules:
- every lesson declares source locators and target skills;
- every quiz/review item is original wording, not copied from proprietary sources;
- deterministic questions carry an explicit grader contract;
- open/context questions use a narrow rubric and are not treated as objective music-theory facts;
- L1-L4 are eligible for DB runtime migration in this phase; L5-L8 remain source-audited specs.
"""

from __future__ import annotations

from typing import Any


def src(source_id: str, locator: str, note: str | None = None) -> dict[str, Any]:
    return {"source_id": source_id, "locator": locator, "note": note}


def q(
    item_id: str,
    kind: str,
    prompt: str,
    skill: str,
    strategy: str,
    answer_key: dict[str, Any],
    grader_config: dict[str, Any] | None = None,
    options: list[str] | None = None,
    explanation: str | None = None,
    provenance: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "kind": kind,
        "prompt": prompt,
        "skill": skill,
        "strategy": strategy,
        "answer_key": answer_key,
        "grader_config": grader_config or {},
        "options": options,
        "explanation": explanation,
        "provenance": provenance or [],
    }


def f(
    item_id: str,
    front: str,
    back: str,
    skill: str,
    mode: str,
    strategy: str,
    answer_key: dict[str, Any],
    grader_config: dict[str, Any] | None = None,
    provenance: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "front": front,
        "back": back,
        "skill": skill,
        "mode": mode,
        "strategy": strategy,
        "answer_key": answer_key,
        "grader_config": grader_config or {},
        "provenance": provenance or [],
    }


OMT_INTERVALS = src("OMT_V2", "Fundamentals → Intervals", "Interval size/quality and enharmonic interval spelling.")
OMT_TRIADS = src("OMT_V2", "Fundamentals → Triads", "Triad structure, qualities, spelling, and listening.")
OMT_7TH = src("OMT_V2", "Fundamentals → Seventh Chords", "Seventh-chord structure and diatonic qualities.")
OMT_ROMAN = src("OMT_V2", "Fundamentals → Roman Numerals", "Relative labeling of diatonic harmony.")
OMT_FUNCTION = src("OMT_V2", "Introduction to Harmony, Cadences, and Phrase Endings", "Tonic–predominant–dominant phrase model.")
OMT_II_V_I = src("OMT_V2", "Jazz → ii–V–I", "ii–V–I schema and applied ii–V usage.")
OMT_VOICINGS = src("OMT_V2", "Jazz → Jazz Voicings", "Smooth/lazy voice leading and voicing guidelines.")
OMT_TONICIZATION = src("OMT_V2", "Diatonic Harmony, Tonicization, and Modulation → Tonicization", "Secondary/applied dominant construction and temporary tonicization.")
OMT_MODAL = src("OMT_V2", "Chromaticism → Modal Mixture", "Borrowing from the parallel key; quality/color can change without necessarily changing function.")
OMT_CHORD_SCALE = src("OMT_V2", "Jazz → Chord-Scale Theory", "Basic ii–V–I chord-scale relationships and limitations of the approach.")
OMT_CHORD_SYMBOLS = src("OMT_V2", "Jazz → Chord Symbols", "Triad/seventh/extension notation and absolute chord-symbol semantics.")

FANK_FUND = src("FANK_WIH", "Unit 1: Music Fundamentals — scales, intervals, triads", "Current official unit verified; exact current PDF page locators not locked.")
FANK_DIATONIC = src("FANK_WIH", "Unit 2: Diatonic Harmony — Roman-numeral analysis, dominant seventh, diatonic seventh chords, smooth voice leading", "Supporting cross-check; exact current PDF pages pending local PDF access.")
FANK_CHROMATIC = src("FANK_WIH", "Unit 3: Chromatic Harmony — Secondary Dominants; Mode Mixture", "Supporting cross-check; exact current PDF pages pending local PDF access.")

TER_CH1 = src("TEREFENKO_WB", "Part I, Ch.1 Music Fundamentals, PDF pp. 13–22", "Written notation plus interval/triad ear-training sequence.")
TER_CH3 = src("TEREFENKO_WB", "Part I, Ch.3 Harmonic Function, PDF pp. 25–28", "Written analysis, keyboard realization, and harmonic-function ear training.")
TER_CH45 = src("TEREFENKO_WB", "Part I, Chs.4–5 Four-Part/Five-Part Chords, PDF pp. 29–43", "Four/five-part chord construction, voicing, and ear training.")
TER_CH6 = src("TEREFENKO_WB", "Part I, Ch.6 The II–V–I Progression, PDF pp. 44–46", "Guide tones, drop-2 voicings, and functional analysis.")
TER_CH78 = src("TEREFENKO_WB", "Part I, Chs.7–8 Modes and Chord-Scale Theory, PDF pp. 47–53", "Mode construction and contextual chord-scale exercises.")
TER_CH1214 = src("TEREFENKO_WB", "Part II, Chs.12–14 Keyboard Textures / Idiomatic Jazz Progressions / Voicings, PDF pp. 78–103", "Keyboard textures, progression realization, upper structures, and rootless formations.")
TER_CH13 = src("TEREFENKO_WB", "Part II, Ch.13 Idiomatic Jazz Progressions, PDF pp. 82–93", "Applied ii–V/X and multi-key keyboard realization as later application.")

KH_CH1_FUNC = src("KHAIHOAN_JAZZ", "Ch.1, printed pp. 21–37", "Tonic/subdominant/dominant grouping and ii–V–I context.")
KH_CH1_TENSION = src("KHAIHOAN_JAZZ", "Introduction + Ch.1, printed pp. 12–18 and 45–70", "Chord tones, tensions, avoid-tone discussion, and chord scales.")
KH_CH2 = src("KHAIHOAN_JAZZ", "Ch.2, printed pp. 71–102", "Secondary dominants, extended dominants, and related ii.")
KH_CH5 = src("KHAIHOAN_JAZZ", "Ch.5, printed pp. 170–188", "Modal interchange and subdominant-minor color.")
KH_CH11 = src("KHAIHOAN_JAZZ", "Ch.11, printed pp. 279–307", "Three-note voicings, guide tones, root-motion voice leading, and advanced voicing families.")


LESSON_SPECS: list[dict[str, Any]] = [
    {
        "id": "L01", "order": 1, "track": "Foundation", "title": "Từ bàn phím đến hợp âm ba nốt",
        "status": "reviewed",
        "objectives": [
            "Nhận biết tên nốt và tự đếm được nửa cung trên bàn phím piano.",
            "Hiểu cách đếm số quãng và đọc các ký hiệu M3, m3, P5, d5.",
            "Dựng hợp âm trưởng, thứ và giảm bằng đúng tên nốt thay vì học thuộc một hợp âm C.",
            "Khám phá hợp âm chủ trên 12 nốt gốc và luyện dần 12 giọng trưởng + 12 giọng thứ.",
        ],
        "skills": ["pitch.spelling", "interval.naming", "chord.triad_formula", "chord.triad_build"],
        "sources": [OMT_INTERVALS, OMT_TRIADS, FANK_FUND, TER_CH1],
        "blocks": [
            ("L01-B01", "callout", {"title": "Bài này bắt đầu từ con số 0", "prompt": "Bạn chưa cần biết đọc khuông nhạc hay âm giai. Hãy đi theo thứ tự: nhìn bàn phím → đếm bước nửa cung → đếm tên chữ cái của quãng → dựng hợp âm ba nốt → đổi nốt gốc để kiểm tra xem mình đã hiểu nguyên lý hay chưa."}),
            ("L01-B02", "theory", {"title": "1. Tên nốt và bàn phím piano", "paragraphs": [
                "Bảy tên nốt cơ bản là C, D, E, F, G, A, B. Sau B, chuỗi lại bắt đầu từ C ở vùng cao hơn.",
                "Trên piano, các phím trắng mang các tên C–D–E–F–G–A–B. Phím đen nằm xen giữa phần lớn các cặp phím trắng.",
                "Một nửa cung là một bước sang phím sát bên cạnh. Khi đếm nửa cung, phím xuất phát được tính là 0 vì ta đang đếm số bước nhảy: C = 0, C# = 1, D = 2. Vì vậy C→E đi bốn bước: C(0) → C#(1) → D(2) → D#(3) → E(4).",
                "Giữa E–F và B–C không có phím đen. Vì vậy E→F và B→C chỉ cách nhau 1 nửa cung. Các cặp phím trắng kề nhau còn lại C–D, D–E, F–G, G–A, A–B đều có một phím đen ở giữa nên cách nhau 2 nửa cung, tức 1 cung nguyên.",
                "Dấu # (thăng) nâng nốt lên 1 nửa cung. Dấu b hoặc ♭ (giáng) hạ nốt xuống 1 nửa cung."
            ]}),
            ("L01-B03", "piano", {"title": "Thử ngay: đếm số bước chứ không đếm số phím", "prompt": "Bấm từng cặp và đếm bước nhảy: C→C# = 1; C→D = 2; E→F = 1; B→C = 1. Hãy nhớ: nốt đầu là 0 khi đếm nửa cung.", "highlight": ["B", "C", "C#", "D", "E", "F"], "selection_mode": False, "show_octave_numbers": False}),
            ("L01-B04", "theory", {"title": "2. Đếm số quãng và viết đúng tên nốt", "paragraphs": [
                "Số quãng được đếm bằng số lượng tên chữ cái và nốt đầu được tính là 1. C→D là quãng 2 vì có C(1)–D(2). C→E là quãng 3 vì có C(1)–D(2)–E(3). C→G là quãng 5 vì có C(1)–D(2)–E(3)–F(4)–G(5).",
                "Đây là hai kiểu đếm khác nhau: khi đếm tên chữ cái để biết quãng mấy, nốt đầu = 1; khi đếm nửa cung trên piano để biết khoảng cách âm thanh, phím xuất phát = 0.",
                "Một phím đen có thể có hai tên. Phím giữa C và D có thể gọi là C# hoặc Db. Hai tên khác nhau nhưng cùng cao độ trên piano được gọi là đồng âm (enharmonic).",
                "Khi viết nhạc, ta không chọn tên tùy ý. Cách chọn đúng tên chữ cái và dấu hóa được gọi là spelling — hiểu đơn giản là 'viết đúng tên nốt'. Muốn tạo quãng 3 từ C, nốt trên phải thuộc họ E: E, Eb hoặc E#. D# có thể cùng cao độ với Eb nhưng thuộc họ D nên C→D# không được viết như một quãng 3.",
                "Quy tắc chữ cái này cũng chuẩn bị cho hợp âm ba nốt: gốc C dùng khung C–E–G; gốc D dùng D–F–A; gốc B dùng B–D–F. Dấu hóa sẽ được xác định sau bằng số nửa cung."
            ]}),
            ("L01-B05", "glossary", {"title": "3. Năm chữ cái mô tả chất lượng quãng", "kicker": "Ký hiệu quãng", "intro": "Sau khi biết con số của quãng, ta cần mô tả kích thước chính xác của nó. Âm nhạc chia các số quãng thành hai họ. Họ 1–4–5–8 dùng một kích thước chuẩn gọi là Perfect (P). Họ 2–3–6–7 có hai kích thước chuẩn liền nhau: Minor (m) nhỏ hơn và Major (M) lớn hơn đúng 1 nửa cung. Tên Major/Minor trước hết nói về kích thước; cảm giác sáng/tối chỉ là gợi ý khi nghe, đặc biệt rõ với quãng 3, chứ không phải định nghĩa tuyệt đối.", "spectrums": [
                {"label": "Nhóm quãng 1, 4, 5, 8", "text": "d (Giảm: −1 nửa cung) ← P (Đúng · chuẩn) → A (Tăng: +1 nửa cung)"},
                {"label": "Nhóm quãng 2, 3, 6, 7", "text": "d (Giảm: thấp hơn m 1 nửa cung) ← m (Thứ) ↔ M (Trưởng) → A (Tăng: cao hơn M 1 nửa cung)"},
            ], "terms": [
                {"symbol": "P", "term": "Perfect · đúng", "definition": "Dùng cho quãng 1, 4, 5 và 8 ở kích thước chuẩn của chúng. Nhóm này không có Major hay Minor. Nếu giữ nguyên số quãng nhưng rộng hơn P 1 nửa cung thì thành A; hẹp hơn P 1 nửa cung thì thành d.", "example": "C→G = P5 = 7 nửa cung"},
                {"symbol": "M", "term": "Major · trưởng · cỡ lớn", "definition": "Dùng cho quãng 2, 3, 6 và 7 ở kích thước lớn hơn trong cặp chuẩn M/m. Với cùng số quãng, M rộng hơn m đúng 1 nửa cung.", "example": "C→E = M3 = 4 nửa cung"},
                {"symbol": "m", "term": "Minor · thứ · cỡ nhỏ", "definition": "Dùng cho quãng 2, 3, 6 và 7 ở kích thước nhỏ hơn trong cặp chuẩn M/m. Với cùng số quãng, m hẹp hơn M đúng 1 nửa cung.", "example": "C→Eb = m3 = 3 nửa cung"},
                {"symbol": "A", "term": "Augmented · tăng", "definition": "Giữ nguyên tên chữ cái và số quãng, rồi kéo rộng thêm 1 nửa cung vượt khỏi kích thước chuẩn lớn nhất: P đối với nhóm 1–4–5–8 hoặc M đối với nhóm 2–3–6–7.", "example": "C→G là P5 (7); giữ chữ G và nâng thành G# thì C→G# = A5 (8). Không viết Ab vì đổi sang chữ A sẽ thành quãng 6."},
                {"symbol": "d", "term": "Diminished · giảm", "definition": "Giữ nguyên tên chữ cái và số quãng, rồi ép hẹp xuống 1 nửa cung dưới kích thước chuẩn nhỏ nhất: P đối với nhóm 1–4–5–8 hoặc m đối với nhóm 2–3–6–7.", "example": "C→G là P5 (7); giữ chữ G và hạ thành Gb thì C→Gb = d5 (6)."},
            ]}),
            ("L01-B06", "interval_explorer", {"title": "4. Khám phá M3, m3, P5 và d5 trên 12 nốt gốc", "prompt": "Mặc định bắt đầu từ C. Hãy đổi nốt gốc và chọn một loại quãng; tên nốt, bàn phím, khuông nhạc và âm thanh sẽ đổi cùng nhau.", "intervals": ["M3", "m3", "P5", "d5"], "default_root": "C"}),
            ("L01-BCP1", "checkpoint", {"title": "Checkpoint · Đọc một quãng mới", "exercise_id": "L01-Q01", "note": "Đừng dựa vào ví dụ C ở phần trên. Hãy đếm chữ cái trước rồi đếm số bước nửa cung.", "random_practice": "interval"}),
            ("L01-B08", "theory", {"title": "5. Hợp âm ba nốt: dựng bằng hai bước", "paragraphs": [
                "Một triad (hợp âm ba nốt) gồm nốt gốc, một nốt thuộc họ chữ cái thứ ba và một nốt thuộc họ chữ cái thứ năm.",
                "Bước 1 — Chọn đúng khung chữ cái 1–3–5: bắt đầu từ nốt gốc rồi bỏ qua một chữ cái mỗi lần. C cho C–E–G; D cho D–F–A; E cho E–G–B. Đây mới là khung spelling, chưa quyết định dấu # hay b; ở bước này bạn chưa cần biết âm giai.",
                "Bước 2 — Đếm nửa cung từ root để đặt dấu hóa: Major = M3 + P5; Minor = m3 + P5; Diminished = m3 + d5. Nhờ vậy người học có thể dựng hợp âm ở bất kỳ nốt gốc nào thay vì học thuộc riêng C.",
                "Ví dụ gốc D: khung chữ cái là D–F–A. D major cần M3 nên F phải nâng thành F#: D–F#–A. D minor cần m3 nên giữ F tự nhiên: D–F–A."
            ]}),
            ("L01-B09", "triad_explorer", {"title": "6. Dựng triad trên bất kỳ nốt gốc nào", "prompt": "Đổi nốt gốc để xem hai bước dựng hợp âm tự cập nhật. Major và Minor là trọng tâm của 24 keys; Diminished và Augmented giúp bạn hiểu d5/A5.", "default_root": "C", "qualities": ["major", "minor", "diminished", "augmented"], "show_two_step": True, "note": "d5 tạo Diminished triad: m3 + d5 = 1–♭3–♭5. Nếu dùng A5 cùng M3, ta có Augmented triad: M3 + A5 = 1–3–#5."}),
            ("L01-BCP2", "checkpoint", {"title": "Checkpoint · Dựng hợp âm ở nốt gốc khác C", "exercise_id": "L01-Q02", "note": "Nhập ba tên nốt, ngăn cách bằng dấu -, khoảng trắng hoặc dấu phẩy. Phần gợi ý chỉ mô tả định dạng, không chứa đáp án.", "random_practice": "triad"}),
            ("L01-B10", "triad_notation_explorer", {"title": "7. So sánh chất lượng hợp âm bằng cùng một nốt gốc", "prompt": "Đổi nốt gốc rồi so sánh Major, Minor, Diminished và Augmented. Piano và ký âm dùng cùng nốt gốc đang chọn.", "default_root": "C"}),
            ("L01-B11", "triad_audio_explorer", {"title": "8. Nghe sự thay đổi khi giữ nguyên nốt gốc", "prompt": "Nghe Major → Minor → Diminished → Augmented trên cùng root. Mục tiêu là nối công thức quãng với âm thanh, không bắt buộc mô tả cảm xúc.", "default_root": "C"}),
            ("L01-B12", "key_overview", {"title": "9. Tổng quan 24 Keys · 12 Major & 12 Minor", "prompt": "Trong Bài 1, ta chỉ nhìn tonic triad (hợp âm chủ) đại diện cho mỗi key. Khái niệm key/âm giai đầy đủ sẽ được học ở Lesson 2. Học theo Tier để không bị ngợp.", "tiers": ["tier-1", "tier-2", "tier-3"]}),
            ("L01-B13", "summary", {"title": "10. Tóm tắt trước khi làm quiz", "items": [
                "Đếm số quãng: nốt đầu = 1. Đếm nửa cung trên piano: phím xuất phát = 0.",
                "E–F và B–C không có phím đen ở giữa nên cách nhau 1 nửa cung; các cặp phím trắng kề nhau còn lại cách nhau 2 nửa cung.",
                "Nhóm 1–4–5–8 dùng P làm kích thước chuẩn; nhóm 2–3–6–7 dùng cặp m/M. A rộng hơn chuẩn 1 nửa cung; d hẹp hơn chuẩn nhỏ nhất 1 nửa cung.",
                "Bốn quãng trọng tâm: M3 = 4, m3 = 3, P5 = 7, d5 = 6 nửa cung. A5 = 8 nửa cung dùng để hiểu augmented triad.",
                "Triad dựng theo hai bước: chọn đúng khung chữ cái 1–3–5 rồi dùng M3/m3/P5/d5/A5 để đặt dấu hóa.",
                "Major = M3 + P5; Minor = m3 + P5; Diminished = m3 + d5; Augmented = M3 + A5.",
                "Sau khi hiểu bằng C, hãy đổi root và luyện 12 major + 12 minor tonic triads theo ba Tier."
            ]}),
        ],
        "exercises": [
            q("L01-Q01", "mcq", "Quãng từ F lên A là gì?", "interval.naming", "exact", {"expected": "M3"}, {"case_sensitive": True}, ["m3", "M3", "P5", "d5"], "F–A dùng ba tên chữ F–G–A và cách nhau 4 nửa cung, nên là M3.", [OMT_INTERVALS, FANK_FUND]),
            q("L01-Q02", "build", "Dựng hợp âm G major bằng tên nốt. Nhập ba nốt theo cùng một định dạng, ví dụ Nốt-Nốt-Nốt.", "chord.triad_build", "music_engine", {"expected": ["G", "B", "D"]}, {"kind": "build_chord", "symbol": "G"}, explanation="G major = G–B–D: M3 + P5 tính từ G.", provenance=[OMT_TRIADS, FANK_FUND]),
            q("L01-Q03", "active_recall", "Không nhìn đáp án: công thức minor triad là gì? Nhập theo định dạng như 1-3-5 (dùng chữ b thay cho ♭).", "chord.triad_formula", "exact", {"expected": "1-b3-5"}, {"normalize_dashes": True, "normalize_accidentals": True}, explanation="Minor triad = 1–♭3–5 = m3 + P5 tính từ root.", provenance=[OMT_TRIADS]),
            q("L01-Q04", "build", "Dựng hợp âm D minor bằng tên nốt. Nhập ba nốt, có thể ngăn cách bằng dấu -, khoảng trắng hoặc dấu phẩy.", "chord.triad_build", "music_engine", {"expected": ["D", "F", "A"]}, {"kind": "build_chord", "symbol": "Dm"}, explanation="D minor = D–F–A: m3 + P5 tính từ D.", provenance=[OMT_TRIADS, TER_CH1]),
            q("L01-Q05", "context", "F# và Gb có thể là cùng một phím trên piano. Điều đó có nghĩa chúng luôn được viết cùng một tên trong mọi ngữ cảnh không? Trả lời ngắn: Có hoặc Không.", "pitch.spelling", "rubric", {"accepted": ["không", "khong", "không phải", "khong phai"]}, {"mode": "contains_any", "strip_accents": True}, explanation="Không. Hai tên có thể cùng cao độ nhưng spelling đúng còn phụ thuộc số quãng, khung chữ cái và ngữ cảnh.", provenance=[OMT_INTERVALS, FANK_FUND]),
            q("L01-Q06", "build", "Dựng hợp âm B diminished. Nhập ba nốt, có thể ngăn cách bằng dấu -, khoảng trắng hoặc dấu phẩy.", "chord.triad_build", "music_engine", {"expected": ["B", "D", "F"]}, {"kind": "build_chord", "symbol": "Bdim"}, explanation="B diminished = B–D–F: m3 + d5 tính từ B.", provenance=[OMT_TRIADS, TER_CH1]),
        ],
        "review_items": [
            f("L01-F01", "Quãng F–A?", "M3 · 4 nửa cung", "interval.naming", "recall", "exact", {"expected": "M3"}, {"case_sensitive": True}, [OMT_INTERVALS]),
            f("L01-F02", "Quãng D–F?", "m3 · 3 nửa cung", "interval.naming", "recall", "exact", {"expected": "m3"}, {"case_sensitive": True}, [OMT_INTERVALS]),
            f("L01-F03", "Quãng G–D?", "P5 · 7 nửa cung", "interval.naming", "recall", "exact", {"expected": "P5"}, {"case_sensitive": True}, [OMT_INTERVALS]),
            f("L01-F04", "Quãng B–F?", "d5 · 6 nửa cung", "interval.naming", "recall", "exact", {"expected": "d5"}, {"case_sensitive": True}, [OMT_INTERVALS]),
            f("L01-F05", "Build F major", "F–A–C", "chord.triad_build", "build", "music_engine", {"expected": ["F", "A", "C"]}, {"kind": "build_chord", "symbol": "F"}, [OMT_TRIADS]),
            f("L01-F06", "Build A minor", "A–C–E", "chord.triad_build", "build", "music_engine", {"expected": ["A", "C", "E"]}, {"kind": "build_chord", "symbol": "Am"}, [OMT_TRIADS]),
            f("L01-F07", "Build B diminished", "B–D–F", "chord.triad_build", "build", "music_engine", {"expected": ["B", "D", "F"]}, {"kind": "build_chord", "symbol": "Bdim"}, [OMT_TRIADS]),
            f("L01-F08", "Muốn viết một quãng 3 phía trên D, nốt trên phải thuộc họ chữ nào?", "Họ F (F, Fb hoặc F# tùy chất lượng quãng).", "pitch.spelling", "context", "rubric", {"accepted": ["f", "họ f", "ho f"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_INTERVALS, FANK_FUND]),
        ],
    },
    {
        "id": "L02", "order": 2, "track": "Foundation", "title": "Âm giai trưởng và hợp âm bảy điệu tính",
        "status": "reviewed",
        "objectives": [
            "Dựng âm giai trưởng đúng thứ tự bậc và spelling.",
            "Nhận diện chất lượng hợp âm bảy điệu tính trong major key.",
            "Dùng chord symbol và Roman numeral cơ bản cho seventh chords.",
        ],
        "skills": ["scale.major", "chord.seventh_quality", "chord.seventh_build", "roman.major_seventh"],
        "sources": [OMT_7TH, OMT_ROMAN, FANK_FUND, FANK_DIATONIC, TER_CH45],
        "blocks": [
            ("L02-B01", "callout", {"title": "Trước khi học seventh chord", "prompt": "Bài này dùng các khái niệm đã học ở Lesson 1: nửa cung, công thức bậc và triad. Nếu ký hiệu 1–3–5 còn lạ, hãy ôn Lesson 1 trước."}),
            ("L02-B02", "theory", {"title": "1. Âm giai trưởng là một chuỗi 7 bậc", "paragraphs": ["Major scale có bảy tên nốt khác nhau trước khi lặp lại tonic ở quãng tám. Ta gọi chúng là bậc 1 đến bậc 7. Tonic là bậc 1 và là nốt làm điểm quy chiếu của scale/key.", "Whole step (cung nguyên) = 2 nửa cung; half step (nửa cung) = 1 nửa cung. Mẫu khoảng cách đi lên của major scale là: whole–whole–half–whole–whole–whole–half, hay 2–2–1–2–2–2–1 nửa cung. Viết đúng scale còn phải giữ đúng thứ tự chữ cái.", "Ví dụ G major: G–A–B–C–D–E–F#. F phải được nâng thành F# để giữ mẫu khoảng cách major scale."]}),
            ("L02-B03", "notation", {"title": "2. G major trên khuông", "groups": [
                {"label": "1 · G", "notes": ["G4"]}, {"label": "2 · A", "notes": ["A4"]}, {"label": "3 · B", "notes": ["B4"]}, {"label": "4 · C", "notes": ["C5"]}, {"label": "5 · D", "notes": ["D5"]}, {"label": "6 · E", "notes": ["E5"]}, {"label": "7 · F#", "notes": ["F#5"]},
            ], "caption": "Mỗi bậc dùng một chữ cái khác nhau; vì vậy G major dùng F#, không viết Gb."}),
            ("L02-BCP1", "checkpoint", {"title": "Checkpoint · Dựng major scale", "exercise_id": "L02-Q01", "note": "Gõ 7 nốt đi lên, không lặp G ở cuối."}),
            ("L02-B04", "theory", {"title": "3. Từ triad đến seventh chord", "paragraphs": ["Seventh chord thêm một nốt quãng bảy vào cấu trúc 1–3–5, tạo frame 1–3–5–7.", "Nếu ta chồng các quãng ba trên từng bậc của major scale, các chất lượng seventh chord tạo thành mẫu Imaj7, ii7, iii7, IVmaj7, V7, vi7, viiø7."]}),
            ("L02-B05", "glossary", {"title": "4. Giải mã maj7, m7, 7, ø7 và số La Mã", "terms": [
                {"symbol": "maj7", "term": "Major seventh chord", "definition": "Major triad + major seventh tính từ root.", "example": "Cmaj7 = C–E–G–B"},
                {"symbol": "m7", "term": "Minor seventh chord", "definition": "Minor triad + minor seventh.", "example": "Dm7 = D–F–A–C"},
                {"symbol": "7", "term": "Dominant seventh quality", "definition": "Major triad + minor seventh. Khi viết G7, số 7 không có 'maj' nên seventh mặc định là minor trong ký hiệu này.", "example": "G7 = G–B–D–F"},
                {"symbol": "ø7 / m7♭5", "term": "Half-diminished seventh", "definition": "Diminished triad + minor seventh; hai cách ký hiệu thường gặp là ø7 hoặc m7♭5.", "example": "Bm7♭5 = B–D–F–A"},
                {"symbol": "I, ii, V", "term": "Roman numeral", "definition": "Số La Mã cho biết bậc của hợp âm trong key. Chữ hoa thường biểu thị chất lượng major; chữ thường biểu thị minor/diminished theo quy ước của bài.", "example": "Trong C major: ii7 = Dm7, V7 = G7"},
                {"symbol": "Key", "term": "Giọng / trung tâm điệu tính", "definition": "Ngữ cảnh trong đó một nốt/hợp âm tonic làm điểm quy chiếu. Khi nói ‘trong C major’, C là tonic và các bậc/chức năng được tính theo ngữ cảnh đó.", "example": "Key C major: C là bậc I"},
            ]}),
            ("L02-B06", "piano", {"title": "5. Nghe bốn màu seventh chord", "prompt": "Bấm các nốt của Cmaj7, Dm7, G7 và Bm7b5. Chưa cần phân biệt hoàn toàn bằng tai; mục tiêu là nối chord symbol với tập nốt.", "highlight": ["C", "D", "E", "F", "G", "A", "B"], "selection_mode": True}),
            ("L02-BCP2", "checkpoint", {"title": "Checkpoint · Roman numeral", "exercise_id": "L02-Q03", "note": "Trong C major, hãy tìm bậc của Dm7 trước rồi mới chọn ký hiệu."}),
            ("L02-B07", "audio", {"title": "6. Nghe Cmaj7 và G7", "prompt": "Nghe từng chord rồi chú ý: Cmaj7 ổn định hơn trong C major, còn G7 có xu hướng muốn đi về C.", "chords": ["Cmaj7", "G7"], "key": "C"}),
            ("L02-B08", "summary", {"title": "Ghi nhớ", "items": ["Major scale dùng 7 bậc và giữ đúng thứ tự chữ cái.", "Seventh chord mở rộng triad thành 1–3–5–7.", "Trong major key: Imaj7, ii7, iii7, IVmaj7, V7, vi7, viiø7.", "Trong C major: Dm7 = ii7, G7 = V7, Bm7♭5 = viiø7."]}),
        ],
        "exercises": [
            q("L02-Q01", "build", "Dựng âm giai G major theo thứ tự đi lên, không lặp lại chủ âm ở cuối.", "scale.major", "music_engine", {"expected": ["G", "A", "B", "C", "D", "E", "F#"]}, {"kind": "build_scale", "tonic": "G", "scale_type": "major"}, explanation="G major dùng F# và mỗi chữ cái xuất hiện một lần.", provenance=[FANK_FUND]),
            q("L02-Q02", "build", "Dựng Cmaj7 đầy đủ bằng tên nốt.", "chord.seventh_build", "music_engine", {"expected": ["C", "E", "G", "B"]}, {"kind": "build_chord", "symbol": "Cmaj7"}, explanation="Cmaj7 = C–E–G–B.", provenance=[OMT_7TH, TER_CH45]),
            q("L02-Q03", "active_recall", "Trong C major, Dm7 mang Roman numeral nào?", "roman.major_seventh", "music_engine", {"expected": "ii7"}, {"kind": "roman_numeral", "key": "C", "chord": "Dm7"}, explanation="Dm7 là seventh chord trên bậc 2 của C major.", provenance=[OMT_ROMAN, FANK_DIATONIC]),
            q("L02-Q04", "mcq", "Trong C major, hợp âm bảy trên bậc V là gì?", "chord.seventh_quality", "exact", {"expected": "G7"}, options=["Gmaj7", "G7", "Gm7", "Gdim7"], explanation="Bậc V của major key tạo dominant seventh.", provenance=[OMT_7TH, FANK_DIATONIC]),
            q("L02-Q05", "mcq", "Trong C major, hợp âm bảy trên bậc vii là gì?", "chord.seventh_quality", "exact", {"expected": "Bm7b5"}, options=["Bmaj7", "Bm7", "Bm7b5", "Bdim7"], explanation="Bậc vii trong major key tạo half-diminished seventh chord.", provenance=[OMT_7TH]),
            q("L02-Q06", "build", "Dựng G7 đầy đủ bằng tên nốt.", "chord.seventh_build", "music_engine", {"expected": ["G", "B", "D", "F"]}, {"kind": "build_chord", "symbol": "G7"}, explanation="G7 = G–B–D–F.", provenance=[OMT_7TH, TER_CH45]),
        ],
        "review_items": [
            f("L02-F01", "G major scale", "G–A–B–C–D–E–F#", "scale.major", "build", "music_engine", {"expected": ["G", "A", "B", "C", "D", "E", "F#"]}, {"kind": "build_scale", "tonic": "G", "scale_type": "major"}, [FANK_FUND]),
            f("L02-F02", "Build Cmaj7", "C–E–G–B", "chord.seventh_build", "build", "music_engine", {"expected": ["C", "E", "G", "B"]}, {"kind": "build_chord", "symbol": "Cmaj7"}, [OMT_7TH]),
            f("L02-F03", "Build Dm7", "D–F–A–C", "chord.seventh_build", "build", "music_engine", {"expected": ["D", "F", "A", "C"]}, {"kind": "build_chord", "symbol": "Dm7"}, [OMT_7TH]),
            f("L02-F04", "V7 in C major", "G7", "roman.major_seventh", "context", "exact", {"expected": "G7"}, provenance=[OMT_7TH]),
            f("L02-F05", "ii7 in C major", "Dm7", "roman.major_seventh", "context", "exact", {"expected": "Dm7"}, provenance=[OMT_7TH]),
            f("L02-F06", "viiø7 in C major", "Bm7b5", "roman.major_seventh", "context", "exact", {"expected": "Bm7b5"}, provenance=[OMT_7TH]),
            f("L02-F07", "Dominant seventh = triad quality + seventh quality?", "Major triad + minor seventh", "chord.seventh_quality", "recall", "rubric", {"accepted": ["major triad + minor seventh", "major + minor seventh", "trưởng + bảy thứ", "truong + bay thu"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_7TH]),
            f("L02-F08", "Roman numeral của Dm7 trong C major", "ii7", "roman.major_seventh", "recall", "music_engine", {"expected": "ii7"}, {"kind": "roman_numeral", "key": "C", "chord": "Dm7"}, [OMT_ROMAN]),
        ],
    },
    {
        "id": "L03", "order": 3, "track": "Harmony Core", "title": "Chức năng hòa âm: Tonic – Predominant/Subdominant – Dominant",
        "status": "reviewed",
        "objectives": [
            "Phân biệt tonic, predominant/subdominant và dominant trong một major-key phrase đơn giản.",
            "Phân tích chức năng theo ngữ cảnh thay vì chỉ nhìn chord symbol.",
            "Nhận diện luồng T → PD → D → T trong progression ngắn.",
        ],
        "skills": ["function.tonic", "function.predominant", "function.dominant", "function.progression"],
        "sources": [OMT_FUNCTION, FANK_DIATONIC, TER_CH3, KH_CH1_FUNC],
        "blocks": [
            ("L03-B01", "callout", {"title": "Chức năng hòa âm không phải tên loại hợp âm", "prompt": "Một chord symbol cho biết cấu tạo hợp âm; harmonic function mô tả cách hợp âm đó hành xử trong một key/progression cụ thể. Hai khái niệm này liên quan nhưng không đồng nhất."}),
            ("L03-B02", "glossary", {"title": "1. Ba chức năng nền tảng", "intro": "Trong lesson này, hãy hình dung một câu hòa âm theo hướng: ổn định → rời điểm ổn định → căng hơn → trở về.", "terms": [
                {"symbol": "T", "term": "Tonic · chủ", "definition": "Vùng ổn định và điểm quy chiếu của key; thường tạo cảm giác đến nơi hoặc nghỉ.", "example": "Cmaj7 trong C major"},
                {"symbol": "PD / SD", "term": "Predominant / Subdominant", "definition": "Nhóm hợp âm thường rời tonic và chuẩn bị cho dominant. HarmonyMentor dùng PD khi nhấn mạnh vai trò 'chuẩn bị dominant'; SD vẫn xuất hiện trong tài liệu nguồn.", "example": "Dm7 (ii7) trong C major"},
                {"symbol": "D", "term": "Dominant · át", "definition": "Tạo lực hướng mạnh về tonic. Ví dụ trong C major, G7 chứa B và F; khi về Cmaj7, B có thể tiến lên C hoặc được giữ làm major 7 tùy voicing, còn F thường có xu hướng đi xuống E.", "example": "G7 (V7) trong C major"},
                {"symbol": "Progression", "term": "Tiến trình hợp âm", "definition": "Chuỗi hợp âm theo thời gian. Function phải được đọc trong chuỗi này, không chỉ nhìn từng chord rời.", "example": "Cmaj7 → Dm7 → G7 → Cmaj7"},
            ]}),
            ("L03-B03", "theory", {"title": "2. Luồng T → PD → D → T", "paragraphs": ["Một mô hình rất cơ bản là tonic tạo điểm bắt đầu, predominant đưa câu nhạc ra khỏi tonic, dominant tăng lực hướng về tonic, rồi tonic trở lại.", "Đây là một mô hình để học và phân tích, không phải luật cấm mọi progression khác. Trong Pop và Jazz có nhiều cách tổ chức hòa âm không đi theo một đường duy nhất."]}),
            ("L03-BCP1", "checkpoint", {"title": "Checkpoint · Tonic function", "exercise_id": "L03-Q01", "note": "Hãy trả lời theo ngữ cảnh C major, không chỉ nhìn chữ 'maj7'."}),
            ("L03-B04", "progression", {"title": "3. Ví dụ chức năng", "prompt": "Cmaj7 → Dm7 → G7 → Cmaj7  =  T → PD → D → T", "key": "C"}),
            ("L03-B05", "audio", {"title": "4. Nghe lực đi–về", "prompt": "Phát progression ở tempo chậm. Chú ý G7 tạo cảm giác chưa kết thúc cho tới khi Cmaj7 trở lại.", "progression": ["Cmaj7", "Dm7", "G7", "Cmaj7"], "key": "C", "bpm": 72}),
            ("L03-BCP2", "checkpoint", {"title": "Checkpoint · Dominant trong ngữ cảnh", "exercise_id": "L03-Q03", "note": "Dùng progression vừa nhìn và vừa nghe để trả lời."}),
            ("L03-B06", "interactive", {"title": "5. Tự phân tích trước khi xem đáp án", "prompt": "Đọc Cmaj7 → Dm7 → G7 → Cmaj7 và nói thành lời: 'ổn định → chuẩn bị → căng hướng về → trở về'. Sau đó đối chiếu T → PD → D → T."}),
            ("L03-B07", "summary", {"title": "Ghi nhớ", "items": ["Chord structure và harmonic function là hai lớp thông tin khác nhau.", "Tonic = điểm quy chiếu; Predominant/Subdominant = chuẩn bị; Dominant = lực hướng về tonic.", "Trong C major, Dm7 thường làm PD và G7 thường làm D trong ii–V–I.", "Function phải đọc theo key, vị trí và progression xung quanh."]}),
        ],
        "exercises": [
            q("L03-Q01", "mcq", "Trong C major, Cmaj7 ở vị trí ổn định cuối phrase thuộc chức năng nào?", "function.tonic", "exact", {"expected": "Tonic"}, options=["Tonic", "Predominant", "Dominant", "Applied dominant"], explanation="I/Imaj7 là điểm quy chiếu tonic trong ngữ cảnh lesson này.", provenance=[OMT_FUNCTION, KH_CH1_FUNC]),
            q("L03-Q02", "mcq", "Trong Dm7 → G7 → Cmaj7 ở C major, Dm7 thường giữ vai trò nào?", "function.predominant", "exact", {"expected": "Predominant"}, options=["Tonic", "Predominant", "Dominant", "Modulation"], explanation="ii7 thường chuẩn bị dominant.", provenance=[OMT_FUNCTION, KH_CH1_FUNC]),
            q("L03-Q03", "mcq", "Trong Dm7 → G7 → Cmaj7, G7 giữ chức năng nào?", "function.dominant", "exact", {"expected": "Dominant"}, options=["Tonic", "Predominant", "Dominant", "Modal"], explanation="V7 tạo dominant function và hướng về tonic.", provenance=[OMT_FUNCTION, TER_CH3]),
            q("L03-Q04", "active_recall", "Viết thứ tự chức năng cơ bản của progression Cmaj7 → Dm7 → G7 → Cmaj7.", "function.progression", "rubric", {"accepted": ["t-pd-d-t", "tonic-predominant-dominant-tonic", "t-subdominant-dominant-t", "tonic-subdominant-dominant-tonic"]}, {"mode": "equals_any", "normalize_dashes": True}, explanation="Flow mục tiêu là T → PD/SD → D → T.", provenance=[OMT_FUNCTION, TER_CH3]),
            q("L03-Q05", "context", "Vì sao không nên gán chức năng chỉ từ tên hợp âm mà bỏ qua progression xung quanh?", "function.progression", "rubric", {"accepted": ["ngữ cảnh", "ngu canh", "context", "chức năng phụ thuộc", "chuc nang phu thuoc"]}, {"mode": "contains_any", "strip_accents": True}, explanation="Harmonic function là quan hệ hành vi trong ngữ cảnh.", provenance=[OMT_FUNCTION, TER_CH3]),
            q("L03-Q06", "applied", "Chọn progression thể hiện rõ T → PD → D → T trong C major.", "function.progression", "exact", {"expected": "Cmaj7-Dm7-G7-Cmaj7"}, {"normalize_dashes": True}, ["Cmaj7-Dm7-G7-Cmaj7", "Cmaj7-Am7-Em7-Dm7", "G7-Dm7-Cmaj7-Fmaj7", "Cmaj7-G7-Dm7-Cmaj7"], "Cmaj7–Dm7–G7–Cmaj7 thể hiện rõ tonic → predominant → dominant → tonic.", [OMT_FUNCTION, KH_CH1_FUNC]),
        ],
        "review_items": [
            f("L03-F01", "Tonic function", "Ổn định / điểm quy chiếu của giọng.", "function.tonic", "recall", "rubric", {"accepted": ["ổn định", "on dinh", "điểm quy chiếu", "diem quy chieu", "home", "resolution"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_FUNCTION]),
            f("L03-F02", "Predominant/Subdominant function", "Rời tonic và chuẩn bị dominant.", "function.predominant", "recall", "rubric", {"accepted": ["chuẩn bị dominant", "chuan bi dominant", "predominant", "subdominant"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_FUNCTION]),
            f("L03-F03", "Dominant function", "Tạo lực hướng/giải quyết về tonic.", "function.dominant", "recall", "rubric", {"accepted": ["về tonic", "ve tonic", "resolve tonic", "dominant"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_FUNCTION]),
            f("L03-F04", "Cmaj7 trong C major (ổn định cuối phrase)", "Tonic", "function.tonic", "context", "exact", {"expected": "Tonic"}, provenance=[OMT_FUNCTION]),
            f("L03-F05", "Dm7 trong Dm7–G7–Cmaj7", "Predominant/Subdominant", "function.predominant", "context", "rubric", {"accepted": ["predominant", "subdominant"]}, {"mode": "equals_any"}, [OMT_FUNCTION, KH_CH1_FUNC]),
            f("L03-F06", "G7 trong Dm7–G7–Cmaj7", "Dominant", "function.dominant", "context", "exact", {"expected": "Dominant"}, provenance=[OMT_FUNCTION]),
            f("L03-F07", "Functional flow cơ bản", "T → PD/SD → D → T", "function.progression", "recall", "rubric", {"accepted": ["t-pd-d-t", "t-sd-d-t", "tonic-predominant-dominant-tonic"]}, {"mode": "equals_any", "normalize_dashes": True}, [OMT_FUNCTION]),
            f("L03-F08", "Function có phải thuộc tính cố định chỉ nhìn chord symbol?", "Không; phải xét key/progression/context.", "function.progression", "context", "rubric", {"accepted": ["không", "khong", "context", "ngữ cảnh", "ngu canh"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_FUNCTION]),
        ],
    },
    {
        "id": "L04", "order": 4, "track": "Harmony Core", "title": "ii–V–I và guide-tone voice leading trên piano",
        "status": "reviewed",
        "objectives": [
            "Nhận diện và transpose ii–V–I major sang một số giọng.",
            "Xác định 3rd và 7th như guide tones trọng yếu của seventh chords trong bài.",
            "Mô tả voice leading mượt bằng common tone và chuyển động gần.",
        ],
        "skills": ["progression.ii_v_i", "voicing.guide_tones", "voicing.voice_leading"],
        "sources": [OMT_II_V_I, OMT_VOICINGS, TER_CH6, KH_CH1_FUNC, KH_CH11],
        "blocks": [
            ("L04-B01", "callout", {"title": "Đọc ii–V–I như thế nào?", "prompt": "ii, V và I là số La Mã chỉ bậc hợp âm trong key. Trong major key, ii7 thường là minor seventh, V7 là dominant seventh, Imaj7 là major seventh."}),
            ("L04-B02", "glossary", {"title": "1. Guide tones và voice leading", "terms": [
                {"symbol": "ii–V–I", "term": "Tiến trình ii–V–I", "definition": "Chuỗi hợp âm đi từ bậc 2 sang bậc 5 rồi về bậc 1. Trong C major: Dm7 → G7 → Cmaj7.", "example": "Dm7 → G7 → Cmaj7"},
                {"symbol": "3rd", "term": "Nốt quãng ba của hợp âm", "definition": "Nốt giúp xác định màu major/minor của chord và thường là guide tone quan trọng.", "example": "B là 3rd của G7"},
                {"symbol": "7th", "term": "Nốt quãng bảy của hợp âm", "definition": "Trong seventh chord, nốt này cùng với 3rd thường tạo hướng dẫn chuyển mạnh giữa các hợp âm.", "example": "F là ♭7 của G7"},
                {"symbol": "Guide tones", "term": "Nốt dẫn hướng", "definition": "Trong phạm vi lesson, ta tập trung vào 3rd và 7th để nghe rõ chất lượng chord và đường nối sang chord kế tiếp.", "example": "G7: B và F"},
                {"symbol": "Voice leading", "term": "Dẫn chuyển bè/nốt", "definition": "Cách từng nốt trong voicing di chuyển sang nốt của chord tiếp theo. Smooth voice leading ưu tiên common tone và chuyển động ngắn khi phù hợp.", "example": "G7 → Cmaj7: B giữ nguyên, F → E"},
                {"symbol": "Common tone", "term": "Nốt chung", "definition": "Một nốt xuất hiện ở cả hai chord liên tiếp và có thể được giữ nguyên trong cùng voice.", "example": "B thuộc cả G7 và Cmaj7"},
                {"symbol": "Voicing", "term": "Cách xếp nốt của hợp âm", "definition": "Một chord symbol có thể được chơi bằng nhiều cách xếp nốt khác nhau theo quãng tám, bass và thứ tự bè. Voicing không đồng nghĩa với danh sách chord tones đầy đủ.", "example": "G7 có chord tones G–B–D–F nhưng một shell voicing có thể chỉ nhấn mạnh G–B–F"},
            ]}),
            ("L04-B03", "theory", {"title": "2. Xây ii–V–I trong C major", "paragraphs": ["C major có các bậc C(1), D(2), E(3), F(4), G(5), A(6), B(7). Seventh chord trên bậc 2 là Dm7, trên bậc 5 là G7, và trên bậc 1 là Cmaj7.", "Vì vậy ii7–V7–Imaj7 trong C major được viết Dm7 → G7 → Cmaj7."]}),
            ("L04-B04", "progression", {"title": "3. ii–V–I in C", "prompt": "Dm7 → G7 → Cmaj7", "key": "C"}),
            ("L04-BCP1", "checkpoint", {"title": "Checkpoint · Nhận diện ii–V–I", "exercise_id": "L04-Q01", "note": "Hãy đọc ii = bậc 2, V = bậc 5, I = bậc 1 trước khi chọn."}),
            ("L04-B05", "notation", {"title": "4. Guide tones của G7 giải về Cmaj7", "groups": [
                {"label": "G7 guide tones · B–F", "notes": ["B3", "F4"]},
                {"label": "Cmaj7 target · B–E", "notes": ["B3", "E4"]},
            ], "caption": "Một đường giữ B làm common tone; đường còn lại đi F xuống E một nửa cung."}),
            ("L04-B06", "theory", {"title": "5. Vì sao 3rd và 7th quan trọng?", "paragraphs": ["Trong G7, B là 3rd và F là ♭7. Hai nốt này giúp tai nhận ra màu dominant seventh rất rõ.", "Khi sang Cmaj7, B có thể giữ nguyên vì Cmaj7 cũng chứa B; F đi xuống E bằng một nửa cung. Đây là ví dụ cụ thể của common tone + stepwise motion.", "Đây là một voicing/voice-leading choice phục vụ lesson, không phải cách duy nhất phải dùng trong mọi phong cách."]}),
            ("L04-BCP2", "checkpoint", {"title": "Checkpoint · Guide tones", "exercise_id": "L04-Q04", "note": "Tự gọi tên 3rd và ♭7 của G7."}),
            ("L04-B07", "piano", {"title": "6. Piano task · từ chord inventory tới guide tones", "prompt": "Trước hết chọn G–B–D–F trên piano và gửi kiểm tra để chứng minh bạn nhận ra đầy đủ chord tones của G7. Sau đó phát Dm7 → G7 → Cmaj7, tự bấm B và F của G7, rồi giữ B và chuyển F xuống E.", "highlight": [], "selection_mode": True, "progression": ["Dm7", "G7", "Cmaj7"], "key": "C", "bpm": 68, "exercise_id": "L04-Q03", "evidence_mode": "pitch_class", "submit_label": "Kiểm tra G7 bằng piano"}),
            ("L04-B08", "audio", {"title": "7. Nghe ii–V–I trước và sau khi tăng tempo", "prompt": "Bắt đầu chậm để nghe hướng đi. Khi đã theo được guide tones, tăng BPM từng bước thay vì cố chơi nhanh ngay.", "progression": ["Dm7", "G7", "Cmaj7"], "key": "C", "bpm": 68}),
            ("L04-B09", "summary", {"title": "Ghi nhớ", "items": ["ii–V–I major = ii7 → V7 → Imaj7.", "Guide tones trong lesson tập trung vào 3rd và 7th của seventh chord.", "G7 → Cmaj7: B có thể giữ; F → E là chuyển động nửa cung.", "Smooth voice leading ưu tiên common tone/chuyển động gần nhưng vẫn phụ thuộc context và voicing.", "Sau khi nắm một key, mới mở rộng dần sang F, Bb, D… thay vì ép 12 keys ngay lập tức."]}),
        ],
        "exercises": [
            q("L04-Q01", "mcq", "ii–V–I trong C major là progression nào?", "progression.ii_v_i", "exact", {"expected": "Dm7-G7-Cmaj7"}, {"normalize_dashes": True}, ["Dm7-G7-Cmaj7", "Am7-Dm7-G7", "Cmaj7-Fmaj7-G7", "Em7-Am7-Dm7"], "ii7–V7–Imaj7 trong C = Dm7–G7–Cmaj7.", [OMT_II_V_I, TER_CH6]),
            q("L04-Q02", "active_recall", "Viết ii–V–I trong F major bằng chord symbols.", "progression.ii_v_i", "exact", {"expected": "Gm7-C7-Fmaj7"}, {"normalize_dashes": True}, explanation="Trong F major: ii=Gm7, V=C7, I=Fmaj7.", provenance=[OMT_II_V_I, TER_CH6]),
            q("L04-Q03", "build", "Dựng G7 đầy đủ; đây là bài chord inventory, chưa phải voicing.", "voicing.guide_tones", "music_engine", {"expected": ["G", "B", "D", "F"]}, {"kind": "build_chord", "symbol": "G7"}, explanation="G7 = G–B–D–F; guide tones là B và F.", provenance=[OMT_7TH, TER_CH6]),
            q("L04-Q04", "active_recall", "Guide tones cơ bản của G7 là hai nốt nào?", "voicing.guide_tones", "rubric", {"accepted": ["b f", "f b", "b và f", "f và b", "b,f", "f,b"]}, {"mode": "equals_any"}, explanation="3rd = B và ♭7 = F.", provenance=[KH_CH11, OMT_VOICINGS]),
            q("L04-Q05", "mcq", "Guide-tone motion nào mô tả G7 → Cmaj7 mượt trong lesson này?", "voicing.voice_leading", "exact", {"expected": "B stays; F moves to E"}, options=["B stays; F moves to E", "B moves to D; F moves to C", "Both voices jump an octave", "F stays; B moves to F"], explanation="Giữ B và hạ F xuống E tạo common tone + stepwise motion.", provenance=[KH_CH11, OMT_VOICINGS]),
            q("L04-Q06", "applied", "Mục tiêu chính của smooth/lazy voice leading giữa hai voicing là gì?", "voicing.voice_leading", "rubric", {"accepted": ["di chuyển ít", "di chuyen it", "chuyển động gần", "chuyen dong gan", "common tone", "move each voice as little as possible"]}, {"mode": "contains_any", "strip_accents": True}, explanation="Ưu tiên giữ common tones và giảm quãng di chuyển của từng voice khi phù hợp.", provenance=[OMT_VOICINGS, KH_CH11]),
        ],
        "review_items": [
            f("L04-F01", "ii–V–I in C", "Dm7–G7–Cmaj7", "progression.ii_v_i", "context", "exact", {"expected": "Dm7-G7-Cmaj7"}, {"normalize_dashes": True}, [OMT_II_V_I]),
            f("L04-F02", "ii–V–I in F", "Gm7–C7–Fmaj7", "progression.ii_v_i", "context", "exact", {"expected": "Gm7-C7-Fmaj7"}, {"normalize_dashes": True}, [OMT_II_V_I]),
            f("L04-F03", "ii–V–I in Bb", "Cm7–F7–Bbmaj7", "progression.ii_v_i", "context", "exact", {"expected": "Cm7-F7-Bbmaj7"}, {"normalize_dashes": True}, [TER_CH6]),
            f("L04-F04", "Guide tones của G7", "B (3rd) và F (♭7)", "voicing.guide_tones", "build", "rubric", {"accepted": ["b f", "f b", "b,f", "f,b", "b và f", "f và b"]}, {"mode": "equals_any"}, [KH_CH11]),
            f("L04-F05", "Guide tones của Dm7", "F (3rd) và C (♭7)", "voicing.guide_tones", "build", "rubric", {"accepted": ["f c", "c f", "f,c", "c,f", "f và c", "c và f"]}, {"mode": "equals_any"}, [KH_CH11]),
            f("L04-F06", "G7 → Cmaj7: B đi đâu trong basic guide-tone example?", "Giữ B như common tone", "voicing.voice_leading", "context", "rubric", {"accepted": ["b", "giữ b", "giu b", "common tone"]}, {"mode": "contains_any", "strip_accents": True}, [KH_CH11]),
            f("L04-F07", "G7 → Cmaj7: F đi đâu?", "F → E", "voicing.voice_leading", "context", "exact", {"expected": "F-E"}, {"normalize_dashes": True}, [KH_CH11]),
            f("L04-F08", "Nguyên tắc smooth jazz voice leading", "Giữ common tones và di chuyển mỗi voice ít nhất có thể khi phù hợp.", "voicing.voice_leading", "recall", "rubric", {"accepted": ["common tone", "di chuyển ít", "di chuyen it", "chuyển động gần", "chuyen dong gan"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_VOICINGS]),
        ],
    },
    {
        "id": "L05", "order": 5, "track": "Functional / Contemporary", "title": "Secondary Dominants",
        "status": "source_audited",
        "objectives": [
            "Nhận diện V7/x theo chord đích tạm thời.",
            "Dựng secondary dominant bằng dominant seventh của chord đích.",
            "Phân biệt tonicization ngắn với modulation ở mức nhập môn.",
        ],
        "skills": ["harmony.secondary_dominant.identify", "harmony.secondary_dominant.build", "harmony.secondary_dominant.apply"],
        "sources": [OMT_TONICIZATION, FANK_CHROMATIC, KH_CH2, TER_CH13],
        "blocks": [],
        "exercises": [
            q("L05-Q01", "mcq", "Trong C major, V7/ii là hợp âm nào?", "harmony.secondary_dominant.build", "exact", {"expected": "A7"}, options=["A7", "D7", "E7", "C7"], provenance=[OMT_TONICIZATION, KH_CH2]),
            q("L05-Q02", "mcq", "Trong C major, V7/V là hợp âm nào?", "harmony.secondary_dominant.build", "exact", {"expected": "D7"}, options=["G7", "D7", "A7", "B7"], provenance=[OMT_TONICIZATION, FANK_CHROMATIC]),
            q("L05-Q03", "active_recall", "Trong C major, V7/vi là gì?", "harmony.secondary_dominant.build", "exact", {"expected": "E7"}, provenance=[OMT_TONICIZATION, KH_CH2]),
            q("L05-Q04", "context", "Trong C major, A7 → Dm7: A7 được phân tích thế nào?", "harmony.secondary_dominant.identify", "exact", {"expected": "V7/ii"}, provenance=[OMT_TONICIZATION, KH_CH2]),
            q("L05-Q05", "applied", "Chọn cách thêm secondary dominant để tăng lực đi tới Am trong C major.", "harmony.secondary_dominant.apply", "exact", {"expected": "E7-Am"}, {"normalize_dashes": True}, ["E7-Am", "D7-Am", "C7-Am", "F7-Am"], provenance=[OMT_TONICIZATION, KH_CH2]),
            q("L05-Q06", "mcq", "Một secondary dominant có bắt buộc thiết lập tonic mới lâu dài không?", "harmony.secondary_dominant.identify", "exact", {"expected": "Không"}, {"strip_accents": True}, ["Có", "Không"], provenance=[OMT_TONICIZATION]),
        ],
        "review_items": [
            f("L05-F01", "V7/ii in C", "A7", "harmony.secondary_dominant.build", "recall", "exact", {"expected": "A7"}, provenance=[OMT_TONICIZATION]),
            f("L05-F02", "V7/V in C", "D7", "harmony.secondary_dominant.build", "recall", "exact", {"expected": "D7"}, provenance=[OMT_TONICIZATION]),
            f("L05-F03", "V7/vi in C", "E7", "harmony.secondary_dominant.build", "recall", "exact", {"expected": "E7"}, provenance=[OMT_TONICIZATION]),
            f("L05-F04", "A7 → Dm7 in C", "A7 = V7/ii", "harmony.secondary_dominant.identify", "context", "exact", {"expected": "V7/ii"}, provenance=[KH_CH2]),
            f("L05-F05", "D7 → G7 in C", "D7 = V7/V", "harmony.secondary_dominant.identify", "context", "exact", {"expected": "V7/V"}, provenance=[OMT_TONICIZATION]),
            f("L05-F06", "E7 → Am7 in C", "E7 = V7/vi", "harmony.secondary_dominant.identify", "context", "exact", {"expected": "V7/vi"}, provenance=[OMT_TONICIZATION]),
            f("L05-F07", "Secondary dominant làm gì?", "Tạm thời tonicize/emphasize một chord đích bằng dominant-function harmony.", "harmony.secondary_dominant.identify", "recall", "rubric", {"accepted": ["tonicize", "nhấn mạnh", "nhan manh", "dominant"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_TONICIZATION]),
            f("L05-F08", "Secondary dominant = modulation hoàn chỉnh?", "Không nhất thiết; tonicization có thể rất ngắn.", "harmony.secondary_dominant.identify", "context", "rubric", {"accepted": ["không", "khong", "không nhất thiết", "khong nhat thiet"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_TONICIZATION]),
        ],
    },
    {
        "id": "L06", "order": 6, "track": "Functional / Contemporary", "title": "Modal Interchange trong Pop/Contemporary",
        "status": "source_audited",
        "objectives": [
            "Nhận biết quan hệ parallel major/minor.",
            "Nhận diện borrowed chord phổ biến trong major-key context.",
            "Ứng dụng borrowed chord mà không mặc định đó là modulation.",
        ],
        "skills": ["scale.parallel_minor", "harmony.modal_interchange.identify", "harmony.modal_interchange.apply"],
        "sources": [OMT_MODAL, FANK_CHROMATIC, KH_CH5],
        "blocks": [],
        "exercises": [
            q("L06-Q01", "mcq", "Trong C major, Fm thường được hiểu là borrowed chord nào?", "harmony.modal_interchange.identify", "exact", {"expected": "iv"}, options=["ii", "iv", "V/V", "bII"], provenance=[OMT_MODAL, KH_CH5]),
            q("L06-Q02", "mcq", "Parallel minor của C major là gì?", "scale.parallel_minor", "exact", {"expected": "C minor"}, options=["A minor", "C minor", "E minor", "F minor"], provenance=[OMT_MODAL]),
            q("L06-Q03", "active_recall", "Trong C major, borrowed ♭VI triad từ parallel minor có root nào?", "harmony.modal_interchange.identify", "exact", {"expected": "Ab"}, provenance=[OMT_MODAL, KH_CH5]),
            q("L06-Q04", "context", "Trong C–F–Fm–C, chord nào tạo modal-mixture color rõ nhất?", "harmony.modal_interchange.identify", "exact", {"expected": "Fm"}, provenance=[OMT_MODAL, KH_CH5]),
            q("L06-Q05", "mcq", "Modal mixture có nhất thiết đổi harmonic function của chord không?", "harmony.modal_interchange.identify", "exact", {"expected": "Không nhất thiết"}, options=["Luôn đổi", "Không nhất thiết", "Luôn thành dominant", "Luôn thành tonic"], provenance=[OMT_MODAL]),
            q("L06-Q06", "applied", "Chọn progression biến C–G–Am–F thành một phiên bản có borrowed iv.", "harmony.modal_interchange.apply", "exact", {"expected": "C-G-Am-Fm"}, {"normalize_dashes": True}, ["C-G-Am-Fm", "C-G-Am-G", "C-D7-Am-F", "C-G-E7-F"], provenance=[OMT_MODAL, KH_CH5]),
        ],
        "review_items": [
            f("L06-F01", "Parallel minor của C major", "C minor", "scale.parallel_minor", "recall", "exact", {"expected": "C minor"}, provenance=[OMT_MODAL]),
            f("L06-F02", "iv borrowed in C major", "Fm", "harmony.modal_interchange.identify", "context", "exact", {"expected": "Fm"}, provenance=[OMT_MODAL]),
            f("L06-F03", "♭VI borrowed triad in C major", "Ab", "harmony.modal_interchange.identify", "context", "exact", {"expected": "Ab"}, provenance=[OMT_MODAL]),
            f("L06-F04", "♭VII borrowed triad in C major", "Bb", "harmony.modal_interchange.identify", "context", "exact", {"expected": "Bb"}, provenance=[OMT_MODAL]),
            f("L06-F05", "C–F–Fm–C: Fm = ?", "Borrowed iv / modal mixture", "harmony.modal_interchange.identify", "context", "rubric", {"accepted": ["borrowed iv", "iv", "modal mixture"]}, {"mode": "contains_any"}, [OMT_MODAL, KH_CH5]),
            f("L06-F06", "Modal mixture thường vay mượn giữa loại key nào?", "Parallel major/minor", "scale.parallel_minor", "recall", "rubric", {"accepted": ["parallel", "song song"]}, {"mode": "contains_any"}, [OMT_MODAL]),
            f("L06-F07", "Borrowed chord có bắt buộc modulation?", "Không.", "harmony.modal_interchange.identify", "context", "rubric", {"accepted": ["không", "khong"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_MODAL]),
            f("L06-F08", "Modal mixture chủ yếu thay đổi gì ở chord trong khung OMT?", "Quality/color; function không nhất thiết đổi.", "harmony.modal_interchange.identify", "recall", "rubric", {"accepted": ["quality", "color", "màu", "mau", "chất lượng", "chat luong"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_MODAL]),
        ],
    },
    {
        "id": "L07", "order": 7, "track": "Jazz", "title": "Jazz Tensions, Modes và Chord-Scale Context",
        "status": "source_audited",
        "objectives": [
            "Phân biệt chord tones với 9/11/13 trong extended-chord vocabulary.",
            "Nhận diện ba chord-scale quan hệ cơ bản của major ii–V–I.",
            "Hiểu chord-scale là công cụ theo context/function chứ không phải bảng đáp án tuyệt đối.",
        ],
        "skills": ["tension.naming", "mode.basic", "chord_scale.basic", "chord_scale.context"],
        "sources": [OMT_CHORD_SCALE, OMT_CHORD_SYMBOLS, TER_CH78, KH_CH1_TENSION],
        "blocks": [],
        "exercises": [
            q("L07-Q01", "mcq", "Các extension/tension number cơ bản phía trên seventh chord là bộ nào?", "tension.naming", "exact", {"expected": "9, 11, 13"}, options=["2, 4, 6", "9, 11, 13", "1, 3, 5", "7, 8, 10"], provenance=[OMT_CHORD_SYMBOLS, KH_CH1_TENSION]),
            q("L07-Q02", "build", "Dựng Cmaj7 chord tones trước khi thêm tension.", "tension.naming", "music_engine", {"expected": ["C", "E", "G", "B"]}, {"kind": "build_chord", "symbol": "Cmaj7"}, provenance=[OMT_7TH, KH_CH1_TENSION]),
            q("L07-Q03", "mcq", "Trong basic ii–V–I chord-scale model ở C, Dm7 thường liên hệ với mode nào?", "chord_scale.basic", "exact", {"expected": "D Dorian"}, options=["D Ionian", "D Dorian", "D Mixolydian", "D Locrian"], provenance=[OMT_CHORD_SCALE, TER_CH78]),
            q("L07-Q04", "mcq", "Trong cùng model, G7 thường liên hệ với mode nào?", "chord_scale.basic", "exact", {"expected": "G Mixolydian"}, options=["G Dorian", "G Ionian", "G Mixolydian", "G Aeolian"], provenance=[OMT_CHORD_SCALE, TER_CH78]),
            q("L07-Q05", "mcq", "Trong cùng model, Cmaj7 thường liên hệ với mode nào?", "chord_scale.basic", "exact", {"expected": "C Ionian"}, options=["C Ionian", "C Dorian", "C Mixolydian", "C Locrian"], provenance=[OMT_CHORD_SCALE, TER_CH78]),
            q("L07-Q06", "context", "Vì sao không nên coi chord-scale table là một đáp án duy nhất cho mọi chord symbol?", "chord_scale.context", "rubric", {"accepted": ["ngữ cảnh", "ngu canh", "function", "chức năng", "chuc nang", "voice leading", "melody"]}, {"mode": "contains_any", "strip_accents": True}, explanation="OMT nêu rõ các giới hạn của chord-scale approach; context, function, voice leading và idiom vẫn quan trọng.", provenance=[OMT_CHORD_SCALE]),
        ],
        "review_items": [
            f("L07-F01", "Tension/extension numbers", "9, 11, 13", "tension.naming", "recall", "exact", {"expected": "9, 11, 13"}, provenance=[OMT_CHORD_SYMBOLS]),
            f("L07-F02", "Chord tones của Cmaj7", "C–E–G–B", "tension.naming", "build", "music_engine", {"expected": ["C", "E", "G", "B"]}, {"kind": "build_chord", "symbol": "Cmaj7"}, [OMT_7TH]),
            f("L07-F03", "Dm7 in C major: basic chord-scale", "D Dorian", "chord_scale.basic", "context", "exact", {"expected": "D Dorian"}, provenance=[OMT_CHORD_SCALE]),
            f("L07-F04", "G7 in C major: basic chord-scale", "G Mixolydian", "chord_scale.basic", "context", "exact", {"expected": "G Mixolydian"}, provenance=[OMT_CHORD_SCALE]),
            f("L07-F05", "Cmaj7 in C major: basic chord-scale", "C Ionian", "chord_scale.basic", "context", "exact", {"expected": "C Ionian"}, provenance=[OMT_CHORD_SCALE]),
            f("L07-F06", "Chord-scale choice nên bắt đầu từ điều gì?", "Key center + harmonic function/context", "chord_scale.context", "recall", "rubric", {"accepted": ["key", "function", "context", "ngữ cảnh", "ngu canh", "chức năng", "chuc nang"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_CHORD_SCALE]),
            f("L07-F07", "Chord tone vs tension", "Chord tone định hình chord; tension mở rộng màu sắc theo context.", "tension.naming", "recall", "rubric", {"accepted": ["màu", "mau", "extension", "mở rộng", "mo rong", "chord tone"]}, {"mode": "contains_any", "strip_accents": True}, [KH_CH1_TENSION]),
            f("L07-F08", "Chord-scale theory có thay thế ear/voice leading không?", "Không; đó là một công cụ, có giới hạn.", "chord_scale.context", "context", "rubric", {"accepted": ["không", "khong", "giới hạn", "gioi han"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_CHORD_SCALE]),
        ],
    },
    {
        "id": "L08", "order": 8, "track": "Jazz", "title": "Jazz Piano Voicing: shell voicing và guide-tone connection",
        "status": "source_audited",
        "objectives": [
            "Phân biệt full chord inventory với một voicing hợp lệ.",
            "Dựng shell/3-note voicing root–3rd–7th trong phạm vi lesson.",
            "Nối voicings bằng common tones và chuyển động gần.",
        ],
        "skills": ["voicing.shell", "voicing.guide_tones", "voicing.voice_leading"],
        "sources": [OMT_VOICINGS, TER_CH1214, KH_CH11],
        "blocks": [],
        "exercises": [
            q("L08-Q01", "mcq", "Trong basic shell/3-note frame của lesson, ba thành phần ưu tiên là gì?", "voicing.shell", "exact", {"expected": "Root-3rd-7th"}, {"normalize_dashes": True}, ["Root-3rd-7th", "Root-5th-9th", "3rd-5th-9th", "Root-2nd-5th"], provenance=[KH_CH11]),
            q("L08-Q02", "mcq", "Theo OMT Jazz Voicings, chord tone nào thường có thể lược bỏ an toàn nhất trong nhiều voicing?", "voicing.shell", "exact", {"expected": "Fifth"}, options=["Root", "Third", "Fifth", "Seventh"], provenance=[OMT_VOICINGS]),
            q("L08-Q03", "build", "Nêu shell root–3rd–7th cho G7 bằng ba tên nốt.", "voicing.shell", "rubric", {"accepted": ["g b f", "g,b,f", "g-b-f"]}, {"mode": "equals_any", "normalize_dashes": True}, explanation="Trong rubric này: G–B–F; đây không phải full chord inventory.", provenance=[KH_CH11]),
            q("L08-Q04", "mcq", "Smooth/lazy voice leading ưu tiên điều gì?", "voicing.voice_leading", "exact", {"expected": "Move each voice as little as possible"}, options=["Move each voice as little as possible", "Always jump by fifth", "Always keep root on top", "Always double the third"], provenance=[OMT_VOICINGS]),
            q("L08-Q05", "context", "Trong G7 → Cmaj7, basic guide-tone connection nào phù hợp với lesson?", "voicing.voice_leading", "exact", {"expected": "B stays; F moves to E"}, options=["B stays; F moves to E", "B moves to F; F stays", "Both move up an octave", "B moves to C; F moves to G"], provenance=[KH_CH11, OMT_VOICINGS]),
            q("L08-Q06", "applied", "Vì sao bài 'dựng đầy đủ G7' và bài 'tạo shell voicing G7' không dùng cùng rubric?", "voicing.shell", "rubric", {"accepted": ["voicing", "lược", "luoc", "omit", "full chord", "inventory"]}, {"mode": "contains_any", "strip_accents": True}, explanation="Voicing có thể cố ý omit/double theo style; chord-inventory exercise kiểm tra đủ chord tones.", provenance=[OMT_VOICINGS, KH_CH11]),
        ],
        "review_items": [
            f("L08-F01", "Basic shell frame", "Root–3rd–7th", "voicing.shell", "recall", "exact", {"expected": "Root-3rd-7th"}, {"normalize_dashes": True}, [KH_CH11]),
            f("L08-F02", "G7 shell root–3–7", "G–B–F", "voicing.shell", "build", "rubric", {"accepted": ["g b f", "g,b,f", "g-b-f"]}, {"mode": "equals_any", "normalize_dashes": True}, [KH_CH11]),
            f("L08-F03", "Dm7 shell root–3–7", "D–F–C", "voicing.shell", "build", "rubric", {"accepted": ["d f c", "d,f,c", "d-f-c"]}, {"mode": "equals_any", "normalize_dashes": True}, [KH_CH11]),
            f("L08-F04", "Cmaj7 shell root–3–7", "C–E–B", "voicing.shell", "build", "rubric", {"accepted": ["c e b", "c,e,b", "c-e-b"]}, {"mode": "equals_any", "normalize_dashes": True}, [KH_CH11]),
            f("L08-F05", "Common tone có ích gì trong voice leading?", "Giảm chuyển động và nối voicings mượt hơn.", "voicing.voice_leading", "recall", "rubric", {"accepted": ["mượt", "muot", "giảm chuyển động", "giam chuyen dong", "common tone"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_VOICINGS]),
            f("L08-F06", "OMT: smooth/lazy voice leading", "Move each voice as little as possible.", "voicing.voice_leading", "recall", "rubric", {"accepted": ["as little as possible", "di chuyển ít", "di chuyen it", "chuyển động gần", "chuyen dong gan"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_VOICINGS]),
            f("L08-F07", "G7 → Cmaj7: guide-tone pair", "B stays; F → E", "voicing.voice_leading", "context", "rubric", {"accepted": ["b stays", "f-e", "f → e", "giữ b", "giu b"]}, {"mode": "contains_any", "strip_accents": True, "normalize_dashes": True}, [KH_CH11]),
            f("L08-F08", "Chord formula vs voicing", "Formula = chord-member inventory; voicing = cách phân bố/omit/double các nốt trong context.", "voicing.shell", "context", "rubric", {"accepted": ["inventory", "voicing", "omit", "lược", "luoc", "phân bố", "phan bo"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_VOICINGS, KH_CH11]),
        ],
    },
]


def lesson_by_id(lesson_id: str) -> dict[str, Any]:
    return next(x for x in LESSON_SPECS if x["id"] == lesson_id)


def all_exercises() -> list[dict[str, Any]]:
    return [item for lesson in LESSON_SPECS for item in lesson["exercises"]]


def all_review_items() -> list[dict[str, Any]]:
    return [item for lesson in LESSON_SPECS for item in lesson["review_items"]]


MIGRATED_LESSON_IDS = {"L01", "L02", "L03", "L04"}

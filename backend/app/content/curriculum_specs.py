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
    version: int | None = None,
    status: str = "published",
    retired: bool = False,
) -> dict[str, Any]:
    # version: chỉ đặt khi câu hỏi/đáp án/cách chấm đổi so với bản đã phát hành, để lượt làm cũ
    # vẫn trỏ về đúng phiên bản đã chấm chúng. Quy tắc phát hành: docs/decisions/ADR-006-phien-ban-bai-tap.md.
    # status: câu Claude soạn mới để "draft"; chỉ Đạt đổi thành "published" sau khi duyệt.
    # retired: bỏ câu khỏi bài mà vẫn giữ lịch sử (seed xóa mềm); không xóa mục khỏi file này.
    return {
        "id": item_id,
        "kind": kind,
        "version": version,
        "status": status,
        "retired": retired,
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


# MT21C mở được và đối chiếu ngày 04/11/2026 (GFDL 1.2+). Câu demo 10/11 dẫn nguồn này; OMT trả 403 cho
# máy kiểm nên chỉ ghi là nguồn đối chiếu thứ hai, chưa mở lại trong đợt này.
MT21C_ENHARMONIC = src("MT21C", "Ch.1 §1.5 Enharmonic Notes", "Cùng phím piano nhưng khác tên chữ là hai nốt viết khác nhau.")
MT21C_INTERVALS = src("MT21C", "Ch.5 §5.1 Introduction to Intervals", "Số quãng đếm theo chữ cái; quãng 3 là M hoặc m, m nhỏ hơn M một nửa cung.")
MT21C_7TH = src("MT21C", "Ch.8 §8.1 Introduction to Seventh Chords", "Năm loại hợp âm bảy, gồm major seventh và major-minor (dominant) seventh.")
MT21C_ROMAN_7TH = src("MT21C", "Ch.8 §8.3 Roman Numerals of Diatonic Seventh Chords", "Hoa = triad trưởng, thường = triad thứ, \"7\" = quãng 7 thứ; sách viết V⁷, vi⁷, IM⁷.")

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
        "id": "L01", "order": 1, "track": "M1. Nền tảng", "title": "Từ bàn phím đến hợp âm ba nốt",
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
            # RS-06: người mới chỉ biết Đô–Rê–Mi cần thấy ngay chữ cái quốc tế là cùng bảy nốt đó. Dùng khối piano
            # (không vào kho AI Tutor) để không làm lệch file vector Gemini, vốn chỉ dựng được trên máy có khóa.
            ("L01-B01A", "piano", {"title": "Đô – Rê – Mi chính là C – D – E", "prompt": "Bảy phím trắng liên tiếp bạn thường hát là Đô – Rê – Mi – Fa – Sol – La – Si. Nhạc quốc tế viết đúng bảy nốt đó bằng chữ cái: Đô = C · Rê = D · Mi = E · Fa = F · Sol = G · La = A · Si = B. Hát “Đô Rê Mi” cũng là C D E. Dấu thăng (#) nâng nốt nửa cung, dấu giáng (b) hạ nốt nửa cung: Đô thăng viết là C#, Rê giáng viết là Db. “Hợp âm C” là hợp âm bắt đầu từ nốt Đô; “Dm” là hợp âm Rê thứ. Ở các câu gõ tên nốt, bạn gõ C D E hay Đô Rê Mi đều được chấm.", "highlight": ["C", "D", "E", "F", "G", "A", "B"], "selection_mode": False, "show_octave_numbers": False}),
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
            ("L01-BCP1", "checkpoint", {"title": "Đọc một quãng mới", "exercise_id": "L01-Q01", "note": "Đừng dựa vào ví dụ C ở phần trên. Hãy đếm chữ cái trước rồi đếm số bước nửa cung.", "random_practice": "interval"}),
            ("L01-B08", "theory", {"title": "5. Hợp âm ba nốt: dựng bằng hai bước", "paragraphs": [
                "Một triad (hợp âm ba nốt) gồm nốt gốc, một nốt thuộc họ chữ cái thứ ba và một nốt thuộc họ chữ cái thứ năm.",
                "Bước 1 — Chọn đúng khung chữ cái 1–3–5: bắt đầu từ nốt gốc rồi bỏ qua một chữ cái mỗi lần. C cho C–E–G; D cho D–F–A; E cho E–G–B. Đây mới là khung spelling, chưa quyết định dấu # hay b; ở bước này bạn chưa cần biết âm giai.",
                "Bước 2 — Đếm nửa cung từ root để đặt dấu hóa: Major = M3 + P5; Minor = m3 + P5; Diminished = m3 + d5. Nhờ vậy người học có thể dựng hợp âm ở bất kỳ nốt gốc nào thay vì học thuộc riêng C.",
                "Ví dụ gốc D: khung chữ cái là D–F–A. D major cần M3 nên F phải nâng thành F#: D–F#–A. D minor cần m3 nên giữ F tự nhiên: D–F–A."
            ]}),
            ("L01-B09", "triad_explorer", {"title": "6. Dựng triad trên bất kỳ nốt gốc nào", "prompt": "Đổi nốt gốc để xem hai bước dựng hợp âm tự cập nhật. Major và Minor là trọng tâm của 24 giọng; Diminished và Augmented giúp bạn hiểu d5/A5.", "default_root": "C", "qualities": ["major", "minor", "diminished", "augmented"], "show_two_step": True, "note": "d5 tạo Diminished triad: m3 + d5 = 1–♭3–♭5. Nếu dùng A5 cùng M3, ta có Augmented triad: M3 + A5 = 1–3–#5."}),
            ("L01-BCP2", "checkpoint", {"title": "Dựng hợp âm ở nốt gốc khác C", "exercise_id": "L01-Q02", "note": "Nhập ba tên nốt, ngăn cách bằng dấu -, khoảng trắng hoặc dấu phẩy. Phần gợi ý chỉ mô tả định dạng, không chứa đáp án.", "random_practice": "triad"}),
            ("L01-B10", "triad_notation_explorer", {"title": "7. So sánh chất lượng hợp âm bằng cùng một nốt gốc", "prompt": "Đổi nốt gốc rồi so sánh Major, Minor, Diminished và Augmented. Piano và ký âm dùng cùng nốt gốc đang chọn.", "default_root": "C"}),
            ("L01-B11", "triad_audio_explorer", {"title": "8. Nghe sự thay đổi khi giữ nguyên nốt gốc", "prompt": "Nghe Major → Minor → Diminished → Augmented trên cùng root. Mục tiêu là nối công thức quãng với âm thanh, không bắt buộc mô tả cảm xúc.", "default_root": "C"}),
            ("L01-B12", "key_overview", {"title": "9. Tổng quan 24 giọng · 12 trưởng & 12 thứ", "prompt": "Trong Bài 1, ta chỉ nhìn tonic triad (hợp âm chủ) đại diện cho mỗi key. Khái niệm giọng/âm giai đầy đủ sẽ được học ở Bài 2. Học theo 3 cấp độ để không bị ngợp.", "tiers": ["tier-1", "tier-2", "tier-3"]}),
            ("L01-B13", "summary", {"title": "10. Tóm tắt trước khi làm quiz", "items": [
                "Đếm số quãng: nốt đầu = 1. Đếm nửa cung trên piano: phím xuất phát = 0.",
                "E–F và B–C không có phím đen ở giữa nên cách nhau 1 nửa cung; các cặp phím trắng kề nhau còn lại cách nhau 2 nửa cung.",
                "Nhóm 1–4–5–8 dùng P làm kích thước chuẩn; nhóm 2–3–6–7 dùng cặp m/M. A rộng hơn chuẩn 1 nửa cung; d hẹp hơn chuẩn nhỏ nhất 1 nửa cung.",
                "Bốn quãng trọng tâm: M3 = 4, m3 = 3, P5 = 7, d5 = 6 nửa cung. A5 = 8 nửa cung dùng để hiểu augmented triad.",
                "Triad dựng theo hai bước: chọn đúng khung chữ cái 1–3–5 rồi dùng M3/m3/P5/d5/A5 để đặt dấu hóa.",
                "Major = M3 + P5; Minor = m3 + P5; Diminished = m3 + d5; Augmented = M3 + A5.",
                "Sau khi hiểu bằng C, hãy đổi root và luyện hợp âm chủ của 12 giọng trưởng + 12 giọng thứ theo ba cấp độ."
            ]}),
        ],
        "exercises": [
            q("L01-Q01", "mcq", "Quãng từ F lên A là gì?", "interval.naming", "exact", {"expected": "M3"}, {"case_sensitive": True}, ["m3", "M3", "P5", "d5"], "F–A dùng ba tên chữ F–G–A và cách nhau 4 nửa cung, nên là M3.", [OMT_INTERVALS, FANK_FUND]),
            q("L01-Q02", "build", "Dựng hợp âm G major bằng tên nốt. Nhập ba nốt theo cùng một định dạng, ví dụ Nốt-Nốt-Nốt.", "chord.triad_build", "music_engine", {"expected": ["G", "B", "D"]}, {"kind": "build_chord", "symbol": "G"}, explanation="G major = G–B–D: M3 + P5 tính từ G.", provenance=[OMT_TRIADS, FANK_FUND]),
            q("L01-Q03", "active_recall", "Không nhìn đáp án: công thức minor triad là gì? Nhập theo định dạng như 1-3-5 (dùng chữ b thay cho ♭).", "chord.triad_formula", "exact", {"expected": "1-b3-5"}, {"normalize_dashes": True, "normalize_accidentals": True, "sequence": True}, explanation="Minor triad = 1–♭3–5 = m3 + P5 tính từ root.", provenance=[OMT_TRIADS], version=5),
            q("L01-Q04", "build", "Dựng hợp âm D minor bằng tên nốt. Nhập ba nốt, có thể ngăn cách bằng dấu -, khoảng trắng hoặc dấu phẩy.", "chord.triad_build", "music_engine", {"expected": ["D", "F", "A"]}, {"kind": "build_chord", "symbol": "Dm"}, explanation="D minor = D–F–A: m3 + P5 tính từ D.", provenance=[OMT_TRIADS, TER_CH1]),
            q("L01-Q05", "context", "F# và Gb có thể là cùng một phím trên piano. Điều đó có nghĩa chúng luôn được viết cùng một tên trong mọi ngữ cảnh không? Chọn câu trả lời đúng nhất.", "pitch.spelling", "exact", {"expected": "Không, tên đúng còn phụ thuộc số quãng và ngữ cảnh"}, {}, ["Có, cùng một phím thì luôn có cùng một tên", "Không, tên đúng còn phụ thuộc số quãng và ngữ cảnh", "Chỉ F# mới là tên đúng, Gb là tên sai", "Chỉ Gb mới là tên đúng, F# là tên sai"], explanation="Không. Hai tên có thể cùng cao độ nhưng spelling đúng còn phụ thuộc số quãng, khung chữ cái và ngữ cảnh.", provenance=[OMT_INTERVALS, FANK_FUND], version=6),
            q("L01-Q06", "build", "Dựng hợp âm B diminished. Nhập ba nốt, có thể ngăn cách bằng dấu -, khoảng trắng hoặc dấu phẩy.", "chord.triad_build", "music_engine", {"expected": ["B", "D", "F"]}, {"kind": "build_chord", "symbol": "Bdim"}, explanation="B diminished = B–D–F: m3 + d5 tính từ B.", provenance=[OMT_TRIADS, TER_CH1]),
            # Câu demo 10/11 (Thắng chốt danh sách 04/11; Thắng + Đạt duyệt và phát hành 04/11): câu độc lập cho pitch.spelling.
            q("L01-Q07", "mcq", "Viết nốt cách D một quãng 3 trưởng (M3) đi lên. Chọn tên nốt đúng.", "pitch.spelling", "exact", {"expected": "F#"}, {"case_sensitive": True}, ["F#", "Gb", "F", "G"], explanation="Quãng 3 từ D phải dùng chữ F (D–E–F). D–F chỉ có 3 nửa cung (m3), nên nâng thành F# để đủ 4 nửa cung. Gb cùng phím với F# nhưng là chữ G, tức quãng 4.", provenance=[MT21C_INTERVALS, MT21C_ENHARMONIC, OMT_INTERVALS]),
            q("L01-Q08", "mcq", "Viết nốt cách A một quãng 3 thứ (m3) đi lên. Chọn tên nốt đúng.", "pitch.spelling", "exact", {"expected": "C"}, {"case_sensitive": True}, ["C#", "B#", "C", "B"], explanation="Quãng 3 từ A dùng chữ C (A–B–C). A–C có 3 nửa cung nên đã là m3. B# cùng phím với C nhưng là chữ B, tức quãng 2; C# tạo M3.", provenance=[MT21C_INTERVALS, MT21C_ENHARMONIC, OMT_INTERVALS]),
            q("L01-Q09", "mcq", "Quãng từ C lên G là gì?", "interval.naming", "exact", {"expected": "P5"}, {"case_sensitive": True}, ["P4", "P5", "M6", "m3"], explanation="C lên G đếm chữ cái C–D–E–F–G là quãng 5, đi 7 nửa cung nên là quãng 5 đúng (P5). P4 chỉ 5 nửa cung, M6 là 9 nửa cung, m3 là 3 nửa cung.", provenance=[OMT_INTERVALS, MT21C_INTERVALS]),
            q("L01-Q10", "mcq", "Quãng từ E lên G là gì?", "interval.naming", "exact", {"expected": "m3"}, {"case_sensitive": True}, ["M3", "m3", "P4", "m2"], explanation="E lên G đếm chữ cái E–F–G là quãng 3, đi 3 nửa cung (E–F là 1, F–G là 2) nên là quãng 3 thứ (m3). Quãng 3 trưởng (M3) phải đi 4 nửa cung.", provenance=[OMT_INTERVALS, MT21C_INTERVALS]),
            q("L01-Q11", "active_recall", "Không nhìn đáp án: công thức major triad (hợp âm ba trưởng) là gì? Nhập theo định dạng như 1-3-5 (dùng chữ b thay cho dấu giáng nếu cần).", "chord.triad_formula", "exact", {"expected": "1-3-5"}, {"normalize_dashes": True, "normalize_accidentals": True, "sequence": True}, explanation="Hợp âm ba trưởng gồm gốc (1), quãng 3 trưởng (3) và quãng 5 đúng (5): công thức 1–3–5. Hợp âm thứ hạ bậc 3 thành b3.", provenance=[OMT_TRIADS]),
            q("L01-Q12", "active_recall", "Không nhìn đáp án: công thức diminished triad (hợp âm ba giảm) là gì? Nhập theo định dạng như 1-3-5 (dùng chữ b thay cho dấu giáng).", "chord.triad_formula", "exact", {"expected": "1-b3-b5"}, {"normalize_dashes": True, "normalize_accidentals": True, "sequence": True}, explanation="Hợp âm ba giảm gồm gốc (1), quãng 3 thứ (b3) và quãng 5 giảm (b5): công thức 1–b3–b5. Ví dụ Bdim là B–D–F.", provenance=[OMT_TRIADS]),
        ],
        "review_items": [
            f("L01-F01", "Quãng F–A?", "M3 · 4 nửa cung", "interval.naming", "recall", "exact", {"expected": "M3"}, {"case_sensitive": True}, [OMT_INTERVALS]),
            f("L01-F02", "Quãng D–F?", "m3 · 3 nửa cung", "interval.naming", "recall", "exact", {"expected": "m3"}, {"case_sensitive": True}, [OMT_INTERVALS]),
            f("L01-F03", "Quãng G–D?", "P5 · 7 nửa cung", "interval.naming", "recall", "exact", {"expected": "P5"}, {"case_sensitive": True}, [OMT_INTERVALS]),
            f("L01-F04", "Quãng B–F?", "d5 · 6 nửa cung", "interval.naming", "recall", "exact", {"expected": "d5"}, {"case_sensitive": True}, [OMT_INTERVALS]),
            f("L01-F05", "Dựng hợp âm F major (F trưởng): gồm những nốt nào?", "F–A–C", "chord.triad_build", "build", "music_engine", {"expected": ["F", "A", "C"]}, {"kind": "build_chord", "symbol": "F"}, [OMT_TRIADS]),
            f("L01-F06", "Dựng hợp âm A minor (A thứ): gồm những nốt nào?", "A–C–E", "chord.triad_build", "build", "music_engine", {"expected": ["A", "C", "E"]}, {"kind": "build_chord", "symbol": "Am"}, [OMT_TRIADS]),
            f("L01-F07", "Dựng hợp âm B diminished (B giảm): gồm những nốt nào?", "B–D–F", "chord.triad_build", "build", "music_engine", {"expected": ["B", "D", "F"]}, {"kind": "build_chord", "symbol": "Bdim"}, [OMT_TRIADS]),
            f("L01-F08", "Muốn viết một quãng 3 phía trên D, nốt trên phải thuộc họ chữ nào?", "Họ F (F, Fb hoặc F# tùy chất lượng quãng).", "pitch.spelling", "context", "rubric", {"accepted": ["f", "họ f", "ho f"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_INTERVALS, FANK_FUND]),
        ],
    },
    {
        "id": "L02", "order": 2, "track": "M1. Nền tảng", "title": "Âm giai trưởng và hợp âm bảy điệu tính",
        "status": "reviewed",
        "objectives": [
            "Dựng âm giai trưởng đúng thứ tự bậc và spelling.",
            "Nhận diện chất lượng hợp âm bảy điệu tính trong major key.",
            "Dùng chord symbol và Roman numeral cơ bản cho seventh chords.",
        ],
        "skills": ["scale.major", "chord.seventh_quality", "chord.seventh_build", "roman.major_seventh"],
        "sources": [OMT_7TH, OMT_ROMAN, FANK_FUND, FANK_DIATONIC, TER_CH45],
        "blocks": [
            ("L02-B01", "callout", {"title": "Trước khi học seventh chord", "prompt": "Bài này dùng các khái niệm đã học ở bài đầu tiên: nửa cung, công thức bậc và triad. Nếu ký hiệu 1–3–5 còn lạ, hãy ôn lại bài đầu tiên trước."}),
            ("L02-B02", "theory", {"title": "1. Âm giai trưởng là một chuỗi 7 bậc", "paragraphs": ["Major scale có bảy tên nốt khác nhau trước khi lặp lại tonic ở quãng tám. Ta gọi chúng là bậc 1 đến bậc 7. Tonic là bậc 1 và là nốt làm điểm quy chiếu của scale/key.", "Whole step (cung nguyên) = 2 nửa cung; half step (nửa cung) = 1 nửa cung. Mẫu khoảng cách đi lên của major scale là: whole–whole–half–whole–whole–whole–half, hay 2–2–1–2–2–2–1 nửa cung. Viết đúng scale còn phải giữ đúng thứ tự chữ cái.", "Ví dụ G major: G–A–B–C–D–E–F#. F phải được nâng thành F# để giữ mẫu khoảng cách major scale."]}),
            ("L02-B03", "notation", {"title": "2. G major trên khuông", "groups": [
                {"label": "1 · G", "notes": ["G4"]}, {"label": "2 · A", "notes": ["A4"]}, {"label": "3 · B", "notes": ["B4"]}, {"label": "4 · C", "notes": ["C5"]}, {"label": "5 · D", "notes": ["D5"]}, {"label": "6 · E", "notes": ["E5"]}, {"label": "7 · F#", "notes": ["F#5"]},
            ], "caption": "Mỗi bậc dùng một chữ cái khác nhau; vì vậy G major dùng F#, không viết Gb."}),
            ("L02-BCP1", "checkpoint", {"title": "Dựng âm giai trưởng (major scale)", "exercise_id": "L02-Q01", "note": "Gõ 7 nốt đi lên, không lặp G ở cuối."}),
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
            ("L02-BCP2", "checkpoint", {"title": "Gọi tên bậc bằng số La Mã", "exercise_id": "L02-Q03", "note": "Trong C major, hãy tìm bậc của Dm7 trước rồi mới chọn ký hiệu."}),
            ("L02-B07", "audio", {"title": "6. Nghe Cmaj7 và G7", "prompt": "Nghe từng chord rồi chú ý: Cmaj7 ổn định hơn trong C major, còn G7 có xu hướng muốn đi về C.", "chords": ["Cmaj7", "G7"], "key": "C"}),
            ("L02-B08", "summary", {"title": "Ghi nhớ", "items": ["Major scale dùng 7 bậc và giữ đúng thứ tự chữ cái.", "Seventh chord mở rộng triad thành 1–3–5–7.", "Trong major key: Imaj7, ii7, iii7, IVmaj7, V7, vi7, viiø7.", "Trong C major: Dm7 = ii7, G7 = V7, Bm7♭5 = viiø7.", "Đổi giọng thì đổi hợp âm: trong G major, bậc V là D nên V7 = D7 (D–F#–A–C)."]}),
        ],
        "exercises": [
            q("L02-Q01", "build", "Dựng âm giai G major theo thứ tự đi lên, không lặp lại chủ âm ở cuối.", "scale.major", "music_engine", {"expected": ["G", "A", "B", "C", "D", "E", "F#"]}, {"kind": "build_scale", "tonic": "G", "scale_type": "major"}, explanation="G major dùng F# và mỗi chữ cái xuất hiện một lần.", provenance=[FANK_FUND]),
            q("L02-Q02", "build", "Dựng Cmaj7 đầy đủ bằng tên nốt.", "chord.seventh_build", "music_engine", {"expected": ["C", "E", "G", "B"]}, {"kind": "build_chord", "symbol": "Cmaj7"}, explanation="Cmaj7 = C–E–G–B.", provenance=[OMT_7TH, TER_CH45]),
            q("L02-Q03", "active_recall", "Trong C major, Dm7 mang Roman numeral nào?", "roman.major_seventh", "music_engine", {"expected": "ii7"}, {"kind": "roman_numeral", "key": "C", "chord": "Dm7"}, explanation="Dm7 là seventh chord trên bậc 2 của C major.", provenance=[OMT_ROMAN, FANK_DIATONIC]),
            q("L02-Q04", "mcq", "Trong C major, hợp âm bảy trên bậc V là gì?", "chord.seventh_quality", "exact", {"expected": "G7"}, options=["Gmaj7", "G7", "Gm7", "Gdim7"], explanation="Bậc V của major key tạo dominant seventh.", provenance=[OMT_7TH, FANK_DIATONIC]),
            q("L02-Q05", "mcq", "Trong C major, hợp âm bảy trên bậc vii là gì?", "chord.seventh_quality", "exact", {"expected": "Bm7b5"}, options=["Bmaj7", "Bm7", "Bm7b5", "Bdim7"], explanation="Bậc vii trong major key tạo half-diminished seventh chord.", provenance=[OMT_7TH]),
            q("L02-Q06", "build", "Dựng G7 đầy đủ bằng tên nốt.", "chord.seventh_build", "music_engine", {"expected": ["G", "B", "D", "F"]}, {"kind": "build_chord", "symbol": "G7"}, explanation="G7 = G–B–D–F.", provenance=[OMT_7TH, TER_CH45]),
            # Câu demo 10/11 (đã phát hành 04/11): mỗi kỹ năng seventh_quality/seventh_build/roman.major_seventh có đủ 3 câu độc lập.
            q("L02-Q07", "mcq", "Trong giọng G trưởng (G major), hợp âm bảy dựng trên bậc V là hợp âm nào?", "chord.seventh_quality", "exact", {"expected": "D7"}, {"case_sensitive": True}, ["Dmaj7", "D7", "Dm7", "Ddim7"], explanation="Bậc V của G trưởng là D. Chồng quãng 3 bằng nốt của G trưởng được D–F#–A–C: triad trưởng + quãng 7 thứ, ký hiệu D7.", provenance=[MT21C_7TH, MT21C_ROMAN_7TH, OMT_7TH]),
            q("L02-Q08", "build", "Dựng hợp âm Fmaj7 bằng tên nốt (đủ 4 nốt).", "chord.seventh_build", "music_engine", {"expected": ["F", "A", "C", "E"]}, {"kind": "build_chord", "symbol": "Fmaj7"}, explanation="Fmaj7 = F–A–C–E: triad F trưởng thêm quãng 7 trưởng F–E.", provenance=[MT21C_7TH, OMT_7TH]),
            q("L02-Q09", "active_recall", "Trong giọng G trưởng, hợp âm D7 mang số La Mã nào? Viết như bài học, ví dụ ii7.", "roman.major_seventh", "music_engine", {"expected": "V7"}, {"kind": "roman_numeral", "key": "G", "chord": "D7"}, explanation="D là bậc 5 của G trưởng. Triad trưởng nên viết chữ hoa V, thêm 7 cho quãng 7 thứ: V7.", provenance=[MT21C_ROMAN_7TH, OMT_ROMAN]),
            q("L02-Q10", "active_recall", "Trong giọng C trưởng, hợp âm Am7 mang số La Mã nào? Viết như bài học, ví dụ ii7.", "roman.major_seventh", "music_engine", {"expected": "vi7"}, {"kind": "roman_numeral", "key": "C", "chord": "Am7"}, explanation="A là bậc 6 của C trưởng. Triad thứ nên viết chữ thường vi, thêm 7 cho quãng 7 thứ: vi7.", provenance=[MT21C_ROMAN_7TH, OMT_ROMAN]),
            q("L02-Q11", "build", "Dựng âm giai F major theo thứ tự đi lên, không lặp lại chủ âm ở cuối.", "scale.major", "music_engine", {"expected": ["F", "G", "A", "Bb", "C", "D", "E"]}, {"kind": "build_scale", "tonic": "F", "scale_type": "major"}, explanation="Áp dụng mẫu 2–2–1–2–2–2–1 nửa cung từ F: F–G–A–Bb–C–D–E. Nốt thứ tư phải là Bb (không phải A#) để giữ mỗi chữ cái xuất hiện một lần.", provenance=[OMT_7TH, FANK_FUND]),
            q("L02-Q12", "build", "Dựng âm giai D major theo thứ tự đi lên, không lặp lại chủ âm ở cuối.", "scale.major", "music_engine", {"expected": ["D", "E", "F#", "G", "A", "B", "C#"]}, {"kind": "build_scale", "tonic": "D", "scale_type": "major"}, explanation="Áp dụng mẫu 2–2–1–2–2–2–1 nửa cung từ D: D–E–F#–G–A–B–C#. Bậc 3 và bậc 7 phải nâng thành F# và C#.", provenance=[OMT_7TH, FANK_FUND]),
        ],
        "review_items": [
            f("L02-F01", "Viết âm giai G major (G trưởng), đi lên, không lặp chủ âm", "G–A–B–C–D–E–F#", "scale.major", "build", "music_engine", {"expected": ["G", "A", "B", "C", "D", "E", "F#"]}, {"kind": "build_scale", "tonic": "G", "scale_type": "major"}, [FANK_FUND]),
            f("L02-F02", "Dựng hợp âm Cmaj7: gồm những nốt nào?", "C–E–G–B", "chord.seventh_build", "build", "music_engine", {"expected": ["C", "E", "G", "B"]}, {"kind": "build_chord", "symbol": "Cmaj7"}, [OMT_7TH]),
            f("L02-F03", "Dựng hợp âm Dm7: gồm những nốt nào?", "D–F–A–C", "chord.seventh_build", "build", "music_engine", {"expected": ["D", "F", "A", "C"]}, {"kind": "build_chord", "symbol": "Dm7"}, [OMT_7TH]),
            f("L02-F04", "Trong giọng C major, hợp âm V7 là hợp âm nào?", "G7", "roman.major_seventh", "context", "exact", {"expected": "G7"}, provenance=[OMT_7TH]),
            f("L02-F05", "Trong giọng C major, hợp âm ii7 là hợp âm nào?", "Dm7", "roman.major_seventh", "context", "exact", {"expected": "Dm7"}, provenance=[OMT_7TH]),
            f("L02-F06", "Trong giọng C major, hợp âm viiø7 là hợp âm nào?", "Bm7b5", "roman.major_seventh", "context", "exact", {"expected": "Bm7b5"}, provenance=[OMT_7TH]),
            f("L02-F07", "Hợp âm bảy át (dominant seventh) = hợp âm ba loại gì + quãng 7 loại gì?", "Major triad + minor seventh", "chord.seventh_quality", "recall", "rubric", {"accepted": ["major triad + minor seventh", "major + minor seventh", "trưởng + bảy thứ", "truong + bay thu"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_7TH]),
            f("L02-F08", "Roman numeral của Dm7 trong C major", "ii7", "roman.major_seventh", "recall", "music_engine", {"expected": "ii7"}, {"kind": "roman_numeral", "key": "C", "chord": "Dm7"}, [OMT_ROMAN]),
        ],
    },
    {
        "id": "L03", "order": 5, "track": "M2. Hòa âm chức năng", "title": "Chức năng hòa âm: Tonic – Predominant/Subdominant – Dominant",
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
            ("L03-BCP1", "checkpoint", {"title": "Nhận ra chức năng Tonic", "exercise_id": "L03-Q01", "note": "Hãy trả lời theo ngữ cảnh C major, không chỉ nhìn chữ 'maj7'."}),
            ("L03-B04", "progression", {"title": "3. Ví dụ chức năng", "prompt": "Cmaj7 → Dm7 → G7 → Cmaj7  =  T → PD → D → T", "key": "C"}),
            ("L03-B05", "audio", {"title": "4. Nghe lực đi–về", "prompt": "Phát progression ở tempo chậm. Chú ý G7 tạo cảm giác chưa kết thúc cho tới khi Cmaj7 trở lại.", "progression": ["Cmaj7", "Dm7", "G7", "Cmaj7"], "key": "C", "bpm": 72}),
            ("L03-BCP2", "checkpoint", {"title": "Dominant trong ngữ cảnh", "exercise_id": "L03-Q03", "note": "Dùng progression vừa nhìn và vừa nghe để trả lời."}),
            ("L03-B06", "interactive", {"title": "5. Tự phân tích trước khi xem đáp án", "prompt": "Đọc Cmaj7 → Dm7 → G7 → Cmaj7 và nói thành lời: 'ổn định → chuẩn bị → căng hướng về → trở về'. Sau đó đối chiếu T → PD → D → T."}),
            ("L03-B07", "summary", {"title": "Ghi nhớ", "items": ["Chord structure và harmonic function là hai lớp thông tin khác nhau.", "Tonic = điểm quy chiếu; Predominant/Subdominant = chuẩn bị; Dominant = lực hướng về tonic.", "Trong C major, Dm7 thường làm PD và G7 thường làm D trong ii–V–I.", "Function phải đọc theo key, vị trí và progression xung quanh."]}),
        ],
        "exercises": [
            q("L03-Q01", "mcq", "Trong C major, Cmaj7 ở vị trí ổn định cuối phrase thuộc chức năng nào?", "function.tonic", "exact", {"expected": "Tonic"}, options=["Tonic", "Predominant", "Dominant", "Applied dominant"], explanation="I/Imaj7 là điểm quy chiếu tonic trong ngữ cảnh lesson này.", provenance=[OMT_FUNCTION, KH_CH1_FUNC]),
            q("L03-Q02", "mcq", "Trong Dm7 → G7 → Cmaj7 ở C major, Dm7 thường giữ vai trò nào?", "function.predominant", "exact", {"expected": "Predominant"}, options=["Tonic", "Predominant", "Dominant", "Modulation"], explanation="ii7 thường chuẩn bị dominant.", provenance=[OMT_FUNCTION, KH_CH1_FUNC]),
            q("L03-Q03", "mcq", "Trong Dm7 → G7 → Cmaj7, G7 giữ chức năng nào?", "function.dominant", "exact", {"expected": "Dominant"}, options=["Tonic", "Predominant", "Dominant", "Modal"], explanation="V7 tạo dominant function và hướng về tonic.", provenance=[OMT_FUNCTION, TER_CH3]),
            q("L03-Q04", "active_recall", "Viết thứ tự chức năng cơ bản của progression Cmaj7 → Dm7 → G7 → Cmaj7.", "function.progression", "rubric", {"accepted": ["t-pd-d-t", "tonic-predominant-dominant-tonic", "t-subdominant-dominant-t", "tonic-subdominant-dominant-tonic", "t-sd-d-t"]}, {"mode": "equals_any", "normalize_dashes": True, "sequence": True}, explanation="Flow mục tiêu là T → PD/SD → D → T.", provenance=[OMT_FUNCTION, TER_CH3], version=2),
            q("L03-Q05", "context", "Vì sao không nên gán chức năng chỉ từ tên hợp âm mà bỏ qua progression xung quanh?", "function.progression", "exact", {"expected": "Vì chức năng phụ thuộc vào giọng và các hợp âm đứng trước, đứng sau"}, {}, ["Vì chức năng phụ thuộc vào giọng và các hợp âm đứng trước, đứng sau", "Vì tên hợp âm thường bị viết sai", "Vì chỉ hợp âm bảy mới có chức năng", "Vì chức năng chỉ do nốt cao nhất quyết định"], explanation="Harmonic function là quan hệ hành vi trong ngữ cảnh: cùng là G7 nhưng trong giọng C nó là Dominant, trong giọng F nó lại dẫn về C (dominant phụ).", provenance=[OMT_FUNCTION, TER_CH3], version=2),
            q("L03-Q06", "applied", "Chọn progression thể hiện rõ T → PD → D → T trong C major.", "function.progression", "exact", {"expected": "Cmaj7-Dm7-G7-Cmaj7"}, {"normalize_dashes": True}, ["Cmaj7-Dm7-G7-Cmaj7", "Cmaj7-Am7-Em7-Dm7", "G7-Dm7-Cmaj7-Fmaj7", "Cmaj7-G7-Dm7-Cmaj7"], "Cmaj7–Dm7–G7–Cmaj7 thể hiện rõ tonic → predominant → dominant → tonic.", [OMT_FUNCTION, KH_CH1_FUNC]),
            q("L03-Q07", "mcq", "Trong G major, hợp âm nào là hợp âm Tonic (chủ), nơi nhạc nghe như đã về đích?", "function.tonic", "exact", {"expected": "Gmaj7"}, {"case_sensitive": True}, ["Gmaj7", "D7", "Am7", "Cmaj7"], explanation="Tonic là hợp âm dựng trên chủ âm của giọng: trong G major là Gmaj7. D7 là Dominant, Am7 và Cmaj7 là Predominant.", provenance=[OMT_FUNCTION, KH_CH1_FUNC]),
            q("L03-Q08", "mcq", "Trong C major, hợp âm nào thường đặt ở cuối câu nhạc để tạo cảm giác về đích?", "function.tonic", "exact", {"expected": "Cmaj7"}, {"case_sensitive": True}, ["Cmaj7", "G7", "Dm7", "Fmaj7"], explanation="Cuối câu nhạc thường dùng hợp âm Tonic, trong C major là Cmaj7. G7 là Dominant (căng, muốn giải quyết), Dm7 và Fmaj7 là Predominant (chuẩn bị cho Dominant).", provenance=[OMT_FUNCTION, KH_CH1_FUNC]),
            q("L03-Q09", "mcq", "Trong C major, hợp âm nào thường giữ chức năng Predominant (chuẩn bị cho Dominant)?", "function.predominant", "exact", {"expected": "Fmaj7"}, {"case_sensitive": True}, ["Fmaj7", "Cmaj7", "G7", "Bm7b5"], explanation="Fmaj7 (bậc IV) là hợp âm Subdominant, thuộc nhóm Predominant. Cmaj7 là Tonic, G7 và Bm7b5 thuộc nhóm Dominant.", provenance=[OMT_FUNCTION, KH_CH1_FUNC]),
            q("L03-Q10", "mcq", "Trong Am7 → D7 → Gmaj7 ở G major, Am7 thường giữ vai trò nào?", "function.predominant", "exact", {"expected": "Predominant"}, {}, ["Tonic", "Predominant", "Dominant", "Applied dominant"], explanation="Am7 là hợp âm bậc ii của G major (như Dm7 trong C major), đứng trước D7 để chuẩn bị Dominant nên giữ vai trò Predominant.", provenance=[OMT_FUNCTION, KH_CH1_FUNC]),
            q("L03-Q11", "mcq", "Trong F major, hợp âm C7 giữ chức năng nào?", "function.dominant", "exact", {"expected": "Dominant"}, {}, ["Tonic", "Predominant", "Dominant", "Applied dominant"], explanation="C7 là hợp âm bảy dựng trên bậc V của F major (F–G–A–Bb–C), nên là Dominant: căng và muốn giải về Tonic F.", provenance=[OMT_FUNCTION, KH_CH1_FUNC]),
            q("L03-Q12", "mcq", "Trong G major, hợp âm nào giữ chức năng Dominant?", "function.dominant", "exact", {"expected": "D7"}, {"case_sensitive": True}, ["D7", "Gmaj7", "Am7", "Cmaj7"], explanation="Dominant dựng trên bậc V của giọng; trong G major bậc V là D nên hợp âm bảy là D7 (D–F#–A–C).", provenance=[OMT_FUNCTION, KH_CH1_FUNC]),
        ],
        "review_items": [
            f("L03-F01", "Chức năng Tonic tạo cảm giác gì trong giọng?", "Ổn định / điểm quy chiếu của giọng.", "function.tonic", "recall", "rubric", {"accepted": ["ổn định", "on dinh", "điểm quy chiếu", "diem quy chieu", "home", "resolution"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_FUNCTION]),
            f("L03-F02", "Chức năng Predominant/Subdominant làm nhiệm vụ gì?", "Rời tonic và chuẩn bị dominant.", "function.predominant", "recall", "rubric", {"accepted": ["chuẩn bị dominant", "chuan bi dominant", "predominant", "subdominant"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_FUNCTION]),
            f("L03-F03", "Chức năng Dominant tạo lực hướng về đâu?", "Tạo lực hướng/giải quyết về tonic.", "function.dominant", "recall", "rubric", {"accepted": ["về tonic", "ve tonic", "resolve tonic", "dominant"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_FUNCTION]),
            f("L03-F04", "Cmaj7 trong C major (ổn định cuối phrase)", "Tonic", "function.tonic", "context", "exact", {"expected": "Tonic"}, provenance=[OMT_FUNCTION]),
            f("L03-F05", "Dm7 trong Dm7–G7–Cmaj7", "Predominant/Subdominant", "function.predominant", "context", "rubric", {"accepted": ["predominant", "subdominant"]}, {"mode": "equals_any"}, [OMT_FUNCTION, KH_CH1_FUNC]),
            f("L03-F06", "G7 trong Dm7–G7–Cmaj7", "Dominant", "function.dominant", "context", "exact", {"expected": "Dominant"}, provenance=[OMT_FUNCTION]),
            f("L03-F07", "Viết thứ tự chức năng cơ bản (dùng T, PD, D)", "T → PD/SD → D → T", "function.progression", "recall", "rubric", {"accepted": ["t-pd-d-t", "t-sd-d-t", "tonic-predominant-dominant-tonic"]}, {"mode": "equals_any", "normalize_dashes": True, "sequence": True}, [OMT_FUNCTION]),
            f("L03-F08", "Function có phải thuộc tính cố định chỉ nhìn chord symbol?", "Không; phải xét key/progression/context.", "function.progression", "context", "rubric", {"accepted": ["không", "khong", "context", "ngữ cảnh", "ngu canh"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_FUNCTION]),
        ],
    },
    {
        "id": "L04", "order": 9, "track": "M4. Jazz", "title": "ii–V–I và guide-tone voice leading trên piano",
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
            ("L04-BCP1", "checkpoint", {"title": "Nhận diện ii–V–I", "exercise_id": "L04-Q01", "note": "Hãy đọc ii = bậc 2, V = bậc 5, I = bậc 1 trước khi chọn."}),
            ("L04-B05", "notation", {"title": "4. Guide tones của G7 giải về Cmaj7", "groups": [
                {"label": "G7 guide tones · B–F", "notes": ["B3", "F4"]},
                {"label": "Cmaj7 target · B–E", "notes": ["B3", "E4"]},
            ], "caption": "Một đường giữ B làm common tone; đường còn lại đi F xuống E một nửa cung."}),
            ("L04-B06", "theory", {"title": "5. Vì sao 3rd và 7th quan trọng?", "paragraphs": ["Trong G7, B là 3rd và F là ♭7. Hai nốt này giúp tai nhận ra màu dominant seventh rất rõ.", "Khi sang Cmaj7, B có thể giữ nguyên vì Cmaj7 cũng chứa B; F đi xuống E bằng một nửa cung. Đây là ví dụ cụ thể của common tone + stepwise motion.", "Đây là một voicing/voice-leading choice phục vụ lesson, không phải cách duy nhất phải dùng trong mọi phong cách."]}),
            ("L04-BCP2", "checkpoint", {"title": "Guide tones", "exercise_id": "L04-Q04", "note": "Tự gọi tên 3rd và ♭7 của G7."}),
            ("L04-B07", "piano", {"title": "6. Piano task · từ chord inventory tới guide tones", "prompt": "Trước hết chọn G–B–D–F trên piano và gửi kiểm tra để chứng minh bạn nhận ra đầy đủ chord tones của G7. Sau đó phát Dm7 → G7 → Cmaj7, tự bấm B và F của G7, rồi giữ B và chuyển F xuống E.", "highlight": [], "selection_mode": True, "progression": ["Dm7", "G7", "Cmaj7"], "key": "C", "bpm": 68, "exercise_id": "L04-Q03", "evidence_mode": "pitch_class", "submit_label": "Kiểm tra G7 bằng piano"}),
            ("L04-B08", "audio", {"title": "7. Nghe ii–V–I trước và sau khi tăng tempo", "prompt": "Bắt đầu chậm để nghe hướng đi. Khi đã theo được guide tones, tăng BPM từng bước thay vì cố chơi nhanh ngay.", "progression": ["Dm7", "G7", "Cmaj7"], "key": "C", "bpm": 68}),
            ("L04-B09", "summary", {"title": "Ghi nhớ", "items": ["ii–V–I major = ii7 → V7 → Imaj7.", "Guide tones trong lesson tập trung vào 3rd và 7th của seventh chord.", "G7 → Cmaj7: B có thể giữ; F → E là chuyển động nửa cung.", "Smooth voice leading ưu tiên common tone/chuyển động gần nhưng vẫn phụ thuộc context và voicing.", "Sau khi nắm một key, mới mở rộng dần sang F, Bb, D… thay vì ép 12 keys ngay lập tức."]}),
        ],
        "exercises": [
            q("L04-Q01", "mcq", "ii–V–I trong C major là progression nào?", "progression.ii_v_i", "exact", {"expected": "Dm7-G7-Cmaj7"}, {"normalize_dashes": True}, ["Dm7-G7-Cmaj7", "Am7-Dm7-G7", "Cmaj7-Fmaj7-G7", "Em7-Am7-Dm7"], "ii7–V7–Imaj7 trong C = Dm7–G7–Cmaj7.", [OMT_II_V_I, TER_CH6]),
            q("L04-Q02", "active_recall", "Viết ii–V–I trong F major bằng chord symbols.", "progression.ii_v_i", "exact", {"expected": "Gm7-C7-Fmaj7"}, {"normalize_dashes": True, "sequence": True}, explanation="Trong F major: ii=Gm7, V=C7, I=Fmaj7.", provenance=[OMT_II_V_I, TER_CH6], version=2),
            q("L04-Q03", "build", "Dựng G7 đầy đủ; đây là bài chord inventory, chưa phải voicing.", "voicing.guide_tones", "music_engine", {"expected": ["G", "B", "D", "F"]}, {"kind": "build_chord", "symbol": "G7", "allowed_input_methods": ["text", "piano"]}, explanation="G7 = G–B–D–F; guide tones là B và F.", provenance=[OMT_7TH, TER_CH6], version=2),
            q("L04-Q04", "active_recall", "Guide tones cơ bản của G7 là hai nốt nào?", "voicing.guide_tones", "rubric", {"accepted": ["b f"]}, {"mode": "equals_any", "unordered": True}, explanation="3rd = B và ♭7 = F.", provenance=[KH_CH11, OMT_VOICINGS], version=2),
            q("L04-Q05", "mcq", "Khi nối G7 → Cmaj7, hai guide tone di chuyển thế nào thì mượt nhất?", "voicing.voice_leading", "exact", {"expected": "Giữ nguyên B, hạ F xuống E"}, options=["Giữ nguyên B, hạ F xuống E", "B lên D, F xuống C", "Cả hai nốt nhảy một quãng tám", "Giữ nguyên F, B nhảy lên F"], explanation="Giữ B và hạ F xuống E tạo common tone + stepwise motion.", provenance=[KH_CH11, OMT_VOICINGS], version=2),
            q("L04-Q06", "applied", "Mục tiêu chính của cách nối hợp âm mượt (smooth/lazy voice leading) là gì?", "voicing.voice_leading", "exact", {"expected": "Mỗi nốt di chuyển ít nhất có thể, giữ lại nốt chung"}, {}, ["Mỗi nốt di chuyển ít nhất có thể, giữ lại nốt chung", "Mỗi nốt nhảy càng xa càng tốt cho kịch tính", "Luôn chơi hợp âm ở thế gốc", "Chơi mọi nốt trong cùng một quãng tám"], explanation="Ưu tiên giữ common tones và giảm quãng di chuyển của từng voice khi phù hợp.", provenance=[OMT_VOICINGS, KH_CH11], version=2),
            q("L04-Q07", "mcq", "ii–V–I trong G major là progression nào?", "progression.ii_v_i", "exact", {"expected": "Am7-D7-Gmaj7"}, {"normalize_dashes": True}, ["Am7-D7-Gmaj7", "Bm7-E7-Amaj7", "Gmaj7-Cmaj7-D7", "Dm7-G7-Cmaj7"], explanation="Trong G major, bậc ii là Am7, bậc V là D7 và bậc I là Gmaj7. Dm7-G7-Cmaj7 là ii–V–I của C major.", provenance=[OMT_II_V_I, TER_CH6]),
            q("L04-Q08", "active_recall", "Guide tones cơ bản của Dm7 là hai nốt nào?", "voicing.guide_tones", "rubric", {"accepted": ["f c"]}, {"mode": "equals_any", "unordered": True}, explanation="Guide tones là quãng 3 và quãng 7 của hợp âm bảy. Dm7 gồm D–F–A–C nên quãng 3 là F và quãng 7 là C.", provenance=[OMT_VOICINGS, TER_CH6]),
            q("L04-Q09", "mcq", "Khi nối Dm7 → G7, hai guide tone di chuyển thế nào thì mượt nhất?", "voicing.voice_leading", "exact", {"expected": "Giữ nguyên F, hạ C xuống B"}, {}, ["Giữ nguyên F, hạ C xuống B", "Nâng F lên G, giữ nguyên C", "Hạ F xuống E, nâng C lên D", "Cả hai nốt cùng nhảy lên quãng 5"], explanation="Guide tone của Dm7 là F (quãng 3) và C (quãng 7). F cũng là quãng 7 của G7 nên giữ nguyên; C hạ nửa cung xuống B, là quãng 3 của G7.", provenance=[OMT_VOICINGS, TER_CH6]),
        ],
        "review_items": [
            f("L04-F01", "Viết ii–V–I trong giọng C bằng ký hiệu hợp âm", "Dm7–G7–Cmaj7", "progression.ii_v_i", "context", "exact", {"expected": "Dm7-G7-Cmaj7"}, {"normalize_dashes": True, "sequence": True}, [OMT_II_V_I]),
            f("L04-F02", "Viết ii–V–I trong giọng F bằng ký hiệu hợp âm", "Gm7–C7–Fmaj7", "progression.ii_v_i", "context", "exact", {"expected": "Gm7-C7-Fmaj7"}, {"normalize_dashes": True, "sequence": True}, [OMT_II_V_I]),
            f("L04-F03", "Viết ii–V–I trong giọng Bb bằng ký hiệu hợp âm", "Cm7–F7–Bbmaj7", "progression.ii_v_i", "context", "exact", {"expected": "Cm7-F7-Bbmaj7"}, {"normalize_dashes": True, "sequence": True}, [TER_CH6]),
            f("L04-F04", "Guide tones của G7", "B (3rd) và F (♭7)", "voicing.guide_tones", "build", "rubric", {"accepted": ["b f"]}, {"mode": "equals_any", "unordered": True}, [KH_CH11]),
            f("L04-F05", "Guide tones của Dm7", "F (3rd) và C (♭7)", "voicing.guide_tones", "build", "rubric", {"accepted": ["f c"]}, {"mode": "equals_any", "unordered": True}, [KH_CH11]),
            f("L04-F06", "G7 → Cmaj7: B đi đâu trong basic guide-tone example?", "Giữ B như common tone", "voicing.voice_leading", "context", "rubric", {"accepted": ["b", "giữ b", "giu b", "common tone"]}, {"mode": "contains_any", "strip_accents": True}, [KH_CH11]),
            f("L04-F07", "G7 → Cmaj7: F đi đâu?", "F → E", "voicing.voice_leading", "context", "exact", {"expected": "F-E"}, {"normalize_dashes": True, "sequence": True}, [KH_CH11]),
            f("L04-F08", "Nguyên tắc nối hợp âm mượt (smooth voice leading) là gì?", "Giữ common tones và di chuyển mỗi voice ít nhất có thể khi phù hợp.", "voicing.voice_leading", "recall", "rubric", {"accepted": ["common tone", "di chuyển ít", "di chuyen it", "chuyển động gần", "chuyen dong gan"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_VOICINGS]),
        ],
    },
    {
        "id": "L05", "order": 6, "track": "M2. Hòa âm chức năng", "title": "Secondary Dominants",
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
            q("L05-Q01", "mcq", "Trong C major, V7/ii là hợp âm nào?", "harmony.secondary_dominant.build", "exact", {"expected": "A7"}, options=["A7", "D7", "E7", "C7"], provenance=[OMT_TONICIZATION, KH_CH2], explanation="ii trong C major là Dm, nên V7/ii là hợp âm bảy át của D. Bậc V của D là A, vậy hợp âm là A7 (A–C#–E–G). C# không thuộc C major, đó là dấu hiệu của secondary dominant. D7 là V7/V, E7 là V7/vi, C7 là V7/IV.", version=2),
            q("L05-Q02", "mcq", "Trong C major, V7/V là hợp âm nào?", "harmony.secondary_dominant.build", "exact", {"expected": "D7"}, options=["G7", "D7", "A7", "B7"], provenance=[OMT_TONICIZATION, FANK_CHROMATIC], explanation="V trong C major là G, nên V7/V là hợp âm bảy át của G. Bậc V của G là D, vậy hợp âm là D7 (D–F#–A–C). F# là nốt dẫn đi lên G. G7 là chính V7 của C, A7 là V7/ii, B7 là V7/iii.", version=2),
            q("L05-Q03", "active_recall", "Trong C major, V7/vi là gì?", "harmony.secondary_dominant.build", "exact", {"expected": "E7"}, provenance=[OMT_TONICIZATION, KH_CH2], explanation="vi trong C major là Am, nên V7/vi là hợp âm bảy át của A. Bậc V của A là E, vậy hợp âm là E7 (E–G#–B–D). G# là nốt dẫn đi lên A. Quy tắc: lấy nốt gốc của hợp âm đích rồi đi lên một quãng 5 đúng.", version=2),
            q("L05-Q04", "context", "Trong C major, A7 → Dm7: A7 được phân tích thế nào?", "harmony.secondary_dominant.identify", "exact", {"expected": "V7/ii"}, provenance=[OMT_TONICIZATION, KH_CH2], explanation="Dm7 là ii7 của C major, có nốt gốc D. A cách D một quãng 5 đúng đi lên và A7 là hợp âm bảy át, nên A7 là V7 của D, viết V7/ii. Đọc là “át bảy của ii”.", version=2),
            q("L05-Q05", "applied", "Chọn cách thêm secondary dominant để tăng lực đi tới Am trong C major.", "harmony.secondary_dominant.apply", "exact", {"expected": "E7-Am"}, {"normalize_dashes": True}, ["E7-Am", "D7-Am", "C7-Am", "F7-Am"], provenance=[OMT_TONICIZATION, KH_CH2], explanation="Am là vi của C major. Muốn tăng lực đi tới Am thì thêm hợp âm bảy át của A, đó là E7. D7 dẫn tới G, C7 dẫn tới F, F7 dẫn tới Bb, không hướng tới Am.", version=2),
            q("L05-Q06", "mcq", "Về secondary dominant, phát biểu nào đúng?", "harmony.secondary_dominant.identify", "exact", {"expected": "Không bắt buộc: nó chỉ làm hợp âm đích nghe như chủ âm trong chốc lát"}, {"strip_accents": True}, ["Bắt buộc thiết lập một tonic mới lâu dài", "Không bắt buộc: nó chỉ làm hợp âm đích nghe như chủ âm trong chốc lát", "Chỉ dùng được khi đã chuyển giọng hoàn toàn", "Luôn phải đi kèm một hợp âm vay mượn"], provenance=[OMT_TONICIZATION], explanation="Không. Secondary dominant chỉ làm hợp âm đích nghe như chủ âm trong chốc lát (tonicization), thường chỉ một hợp âm, rồi giọng chính vẫn tiếp tục. Chỉ khi giọng mới được xác lập lâu dài thì mới gọi là chuyển giọng (modulation).", version=3),
            # RS-04 (14/11/2026): Claude soạn để mỗi kỹ năng có ít nhất 3 câu; status draft, chờ Đạt duyệt.
            q("L05-Q07", "applied", "Muốn tăng lực đi tới Dm trong C major, chọn tiến trình nào?", "harmony.secondary_dominant.apply", "exact", {"expected": "A7-Dm"}, {"normalize_dashes": True}, ["A7-Dm", "G7-Dm", "E7-Dm", "D7-Dm"], "Dm là ii của C major. Hợp âm át bảy của D là A7 (A–C#–E–G), nên A7–Dm tạo lực đi tới Dm. C# là nốt dẫn đi lên D. G7 là át của C, E7 là át của A, D7 là át của G.", [OMT_TONICIZATION, KH_CH2], status="draft"),
            q("L05-Q08", "applied", "Thêm V7/V vào vòng C–F–G–C. Đặt D7 ở đâu là hợp lý nhất?", "harmony.secondary_dominant.apply", "exact", {"expected": "C-F-D7-G-C"}, {"normalize_dashes": True}, ["C-F-D7-G-C", "C-D7-F-G-C", "C-F-G-D7-C", "D7-C-F-G-C"], "V7/V là át bảy của G, tức D7 (D–F#–A–C). Hợp âm át phụ đứng ngay trước hợp âm đích, nên D7 đặt ngay trước G: C–F–D7–G–C.", [OMT_TONICIZATION, FANK_CHROMATIC], status="draft"),
            q("L05-Q09", "mcq", "Trong C major, D7 → G: D7 được phân tích thế nào?", "harmony.secondary_dominant.identify", "exact", {"expected": "V7/V"}, options=["V7/V", "V7/ii", "V7", "ii7"], explanation="G là bậc V của C major. D cách G một quãng 5 đúng đi lên và D7 là hợp âm bảy át, nên D7 là V7 của G, viết V7/V (át bảy của át).", provenance=[OMT_TONICIZATION, KH_CH2], status="draft"),
        ],
        "review_items": [
            f("L05-F01", "V7/ii in C", "A7", "harmony.secondary_dominant.build", "recall", "exact", {"expected": "A7"}, provenance=[OMT_TONICIZATION]),
            f("L05-F02", "V7/V in C", "D7", "harmony.secondary_dominant.build", "recall", "exact", {"expected": "D7"}, provenance=[OMT_TONICIZATION]),
            f("L05-F03", "V7/vi in C", "E7", "harmony.secondary_dominant.build", "recall", "exact", {"expected": "E7"}, provenance=[OMT_TONICIZATION]),
            f("L05-F04", "A7 → Dm7 in C", "A7 = V7/ii", "harmony.secondary_dominant.identify", "context", "exact", {"expected": "V7/ii"}, provenance=[KH_CH2]),
            f("L05-F05", "D7 → G7 in C", "D7 = V7/V", "harmony.secondary_dominant.identify", "context", "exact", {"expected": "V7/V"}, provenance=[OMT_TONICIZATION]),
            f("L05-F06", "E7 → Am7 in C", "E7 = V7/vi", "harmony.secondary_dominant.identify", "context", "exact", {"expected": "V7/vi"}, provenance=[OMT_TONICIZATION]),
            f("L05-F07", "Át phụ (secondary dominant) dùng để làm gì?", "Tạm thời nhấn mạnh một hợp âm đích bằng hợp âm có chức năng Dominant (tonicization).", "harmony.secondary_dominant.identify", "recall", "rubric", {"accepted": ["tonicize", "nhấn mạnh", "nhan manh", "dominant"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_TONICIZATION]),
            f("L05-F08", "Át phụ có phải là chuyển giọng hoàn chỉnh không?", "Không nhất thiết; có thể chỉ nhấn mạnh một hợp âm trong chốc lát.", "harmony.secondary_dominant.identify", "context", "rubric", {"accepted": ["không", "khong", "không nhất thiết", "khong nhat thiet"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_TONICIZATION]),
        ],
    },
    {
        "id": "L06", "order": 8, "track": "M3. Pop", "title": "Modal Interchange trong Pop/Contemporary",
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
            q("L06-Q01", "mcq", "Trong C major, Fm thường được hiểu là borrowed chord nào?", "harmony.modal_interchange.identify", "exact", {"expected": "iv"}, options=["ii", "iv", "V/V", "bII"], provenance=[OMT_MODAL, KH_CH5], explanation="Fm không thuộc C major (có Ab). Nó mượn từ C minor, giọng song song cùng chủ âm C, nơi bậc IV là Fm. Bậc này viết iv bằng chữ thường vì là hợp âm thứ. Dm là ii, D7 là V/V, Db là bII.", version=2),
            q("L06-Q02", "mcq", "Parallel minor của C major là gì?", "scale.parallel_minor", "exact", {"expected": "C minor"}, options=["A minor", "C minor", "E minor", "F minor"], provenance=[OMT_MODAL], explanation="Parallel minor là giọng thứ cùng chủ âm: C major có parallel minor là C minor. A minor là relative minor (cùng dấu hóa, khác chủ âm). E minor và F minor không phải giọng song song của C major.", version=2),
            q("L06-Q03", "active_recall", "Trong C major, borrowed ♭VI triad từ parallel minor có root nào?", "harmony.modal_interchange.identify", "exact", {"expected": "Ab"}, provenance=[OMT_MODAL, KH_CH5], explanation="C minor tự nhiên có các nốt C–D–Eb–F–G–Ab–Bb, nên bậc 6 là Ab. Triad ♭VI mượn về C major là Ab–C–Eb, root là Ab (cách C một quãng 6 thứ đi lên).", version=2),
            q("L06-Q04", "context", "Trong C–F–Fm–C, chord nào tạo modal-mixture color rõ nhất?", "harmony.modal_interchange.identify", "exact", {"expected": "Fm"}, provenance=[OMT_MODAL, KH_CH5], explanation="F là IV của C major (F–A–C). Fm (F–Ab–C) đổi A thành Ab, nốt không thuộc C major và đến từ C minor. Đó là chỗ nghe thấy màu mượn rõ nhất, còn C và F đều nằm trong giọng.", version=2),
            q("L06-Q05", "mcq", "Modal mixture có nhất thiết đổi harmonic function của chord không?", "harmony.modal_interchange.identify", "exact", {"expected": "Không nhất thiết"}, options=["Luôn đổi", "Không nhất thiết", "Luôn thành dominant", "Luôn thành tonic"], provenance=[OMT_MODAL], explanation="Không nhất thiết. Fm vẫn đứng ở vị trí bậc IV nên thường giữ chức năng subdominant như F; mượn hợp âm chủ yếu đổi màu (phẩm chất) chứ không bắt buộc đổi chức năng.", version=2),
            q("L06-Q06", "applied", "Chọn progression biến C–G–Am–F thành một phiên bản có borrowed iv.", "harmony.modal_interchange.apply", "exact", {"expected": "C-G-Am-Fm"}, {"normalize_dashes": True}, ["C-G-Am-Fm", "C-G-Am-G", "C-D7-Am-F", "C-G-E7-F"], provenance=[OMT_MODAL, KH_CH5], explanation="C–G–Am–F có F là IV. Thay F bằng Fm (iv mượn từ C minor) được C–G–Am–Fm. C–G–Am–G không đổi bậc IV, còn C–D7–Am–F và C–G–E7–F thêm secondary dominant (D7 là V7/V, E7 là V7/vi), không phải hợp âm mượn.", version=2),
            # RS-04 (14/11/2026): Claude soạn để mỗi kỹ năng có ít nhất 3 câu; status draft, chờ Đạt duyệt.
            q("L06-Q07", "mcq", "Giọng thứ song song (parallel minor) của G major là gì?", "scale.parallel_minor", "exact", {"expected": "G minor"}, options=["E minor", "G minor", "D minor", "B minor"], explanation="Giọng thứ song song có cùng chủ âm: G major đi với G minor. E minor là giọng thứ tương ứng (relative minor), cùng dấu hóa nhưng khác chủ âm.", provenance=[OMT_MODAL], status="draft"),
            q("L06-Q08", "mcq", "C minor tự nhiên khác C major ở những nốt nào?", "scale.parallel_minor", "exact", {"expected": "Eb, Ab, Bb"}, options=["Eb, Ab, Bb", "F#, C#, G#", "Eb, Ab", "Bb"], explanation="C major: C–D–E–F–G–A–B. C minor tự nhiên: C–D–Eb–F–G–Ab–Bb. Ba bậc 3, 6, 7 hạ nửa cung thành Eb, Ab, Bb. Đây là kho nốt để mượn hợp âm.", provenance=[OMT_MODAL], status="draft"),
            q("L06-Q09", "applied", "Biến vòng C–F–C thành phiên bản có iv mượn ở giữa.", "harmony.modal_interchange.apply", "exact", {"expected": "C-F-Fm-C"}, {"normalize_dashes": True}, ["C-F-Fm-C", "C-F-A7-C", "C-F-Dm-C", "C-F-F7-C"], "Fm (F–Ab–C) là iv mượn từ C minor. Đi F → Fm chỉ đổi A thành Ab nên màu buồn chen vào rất mượt. A7 là át phụ, Dm là ii của chính C major, F7 là hợp âm bảy át.", [OMT_MODAL, KH_CH5], status="draft"),
            q("L06-Q10", "applied", "Trong C major, chọn vòng có hợp âm ♭VI mượn từ C minor.", "harmony.modal_interchange.apply", "exact", {"expected": "C-Ab-G-C"}, {"normalize_dashes": True}, ["C-Ab-G-C", "C-Am-G-C", "C-A-G-C", "C-A7-G-C"], "Bậc 6 của C minor là Ab, nên ♭VI là Ab (Ab–C–Eb). Am là vi của chính C major, A và A7 có C# nên không mượn từ C minor.", [OMT_MODAL, KH_CH5], status="draft"),
        ],
        "review_items": [
            f("L06-F01", "Giọng thứ song song (parallel minor) của C major", "C minor", "scale.parallel_minor", "recall", "exact", {"expected": "C minor"}, provenance=[OMT_MODAL]),
            f("L06-F02", "Hợp âm iv mượn trong C major", "Fm", "harmony.modal_interchange.identify", "context", "exact", {"expected": "Fm"}, provenance=[OMT_MODAL]),
            f("L06-F03", "Hợp âm ♭VI mượn trong C major", "Ab", "harmony.modal_interchange.identify", "context", "exact", {"expected": "Ab"}, provenance=[OMT_MODAL]),
            f("L06-F04", "Hợp âm ♭VII mượn trong C major", "Bb", "harmony.modal_interchange.identify", "context", "exact", {"expected": "Bb"}, provenance=[OMT_MODAL]),
            f("L06-F05", "C–F–Fm–C: Fm là hợp âm gì?", "iv mượn (pha trộn điệu thức, modal mixture)", "harmony.modal_interchange.identify", "context", "rubric", {"accepted": ["borrowed iv", "iv", "modal mixture"]}, {"mode": "contains_any"}, [OMT_MODAL, KH_CH5]),
            f("L06-F06", "Hợp âm mượn được lấy từ loại giọng nào?", "Giọng song song (parallel): trưởng và thứ cùng nốt chủ", "scale.parallel_minor", "recall", "rubric", {"accepted": ["parallel", "song song"]}, {"mode": "contains_any"}, [OMT_MODAL]),
            f("L06-F07", "Hợp âm mượn có bắt buộc là chuyển giọng không?", "Không.", "harmony.modal_interchange.identify", "context", "rubric", {"accepted": ["không", "khong"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_MODAL]),
            f("L06-F08", "Pha trộn điệu thức chủ yếu thay đổi gì ở hợp âm?", "Phẩm chất và màu sắc (quality/color); chức năng không nhất thiết đổi.", "harmony.modal_interchange.identify", "recall", "rubric", {"accepted": ["quality", "color", "màu", "mau", "chất lượng", "chat luong"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_MODAL]),
        ],
    },
    {
        "id": "L07", "order": 10, "track": "M4. Jazz", "title": "Jazz Tensions, Modes và Chord-Scale Context",
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
            q("L07-Q01", "mcq", "Các extension/tension number cơ bản phía trên seventh chord là bộ nào?", "tension.naming", "exact", {"expected": "9, 11, 13"}, options=["2, 4, 6", "9, 11, 13", "1, 3, 5", "7, 8, 10"], provenance=[OMT_CHORD_SYMBOLS, KH_CH1_TENSION], explanation="Tension là các bậc 2, 4, 6 của âm giai nhưng tính ở quãng tám phía trên hợp âm bảy, nên gọi là 9, 11, 13. Chồng thêm quãng 3 lên hợp âm bảy (1–3–5–7) sẽ ra 9, 11, 13. 1, 3, 5 là chord tone của triad.", version=2),
            q("L07-Q02", "build", "Dựng Cmaj7 chord tones trước khi thêm tension.", "tension.naming", "music_engine", {"expected": ["C", "E", "G", "B"]}, {"kind": "build_chord", "symbol": "Cmaj7"}, provenance=[OMT_7TH, KH_CH1_TENSION], explanation="Cmaj7 có root C, quãng 3 trưởng E, quãng 5 đúng G và quãng 7 trưởng B, tức C–E–G–B. Tension chỉ thêm vào sau khi bốn chord tone này đã đúng.", version=2),
            q("L07-Q03", "mcq", "Trong basic ii–V–I chord-scale model ở C, Dm7 thường liên hệ với mode nào?", "chord_scale.basic", "exact", {"expected": "D Dorian"}, options=["D Ionian", "D Dorian", "D Mixolydian", "D Locrian"], provenance=[OMT_CHORD_SCALE, TER_CH78], explanation="Trong ii–V–I ở C, Dm7 (D–F–A–C) dùng các nốt của C major bắt đầu từ D: D–E–F–G–A–B–C, tức D Dorian. Đây là mô hình cơ bản thường dùng, không phải quy tắc duy nhất.", version=2),
            q("L07-Q04", "mcq", "Trong cùng model, G7 thường liên hệ với mode nào?", "chord_scale.basic", "exact", {"expected": "G Mixolydian"}, options=["G Dorian", "G Ionian", "G Mixolydian", "G Aeolian"], provenance=[OMT_CHORD_SCALE, TER_CH78], explanation="G7 (G–B–D–F) dùng các nốt của C major bắt đầu từ G: G–A–B–C–D–E–F, tức G Mixolydian. Nốt F tự nhiên khớp với quãng 7 thứ của G7.", version=2),
            q("L07-Q05", "mcq", "Trong cùng model, Cmaj7 thường liên hệ với mode nào?", "chord_scale.basic", "exact", {"expected": "C Ionian"}, options=["C Ionian", "C Dorian", "C Mixolydian", "C Locrian"], provenance=[OMT_CHORD_SCALE, TER_CH78], explanation="Cmaj7 (C–E–G–B) dùng chính C major: C–D–E–F–G–A–B, tức C Ionian. Các lựa chọn Dorian, Mixolydian, Locrian bắt đầu từ C sẽ có nốt thấp hơn C major và không khớp quãng 7 trưởng B.", version=2),
            q("L07-Q06", "context", "Vì sao không nên coi chord-scale table là một đáp án duy nhất cho mọi chord symbol?", "chord_scale.context", "rubric", {"accepted": ["ngữ cảnh", "ngu canh", "function", "chức năng", "chuc nang", "voice leading", "melody"]}, {"mode": "contains_any", "strip_accents": True}, explanation="OMT nêu rõ các giới hạn của chord-scale approach; context, function, voice leading và idiom vẫn quan trọng.", provenance=[OMT_CHORD_SCALE],
              status="draft"),  # tự luận chấm từ khóa: để draft chờ Đạt viết lại thành câu chọn (11/11), như L08-Q06
            # RS-04 (14/11/2026): Claude soạn để mỗi kỹ năng có ít nhất 3 câu; status draft, chờ Đạt duyệt.
            q("L07-Q07", "mcq", "Trong Cmaj9, tension 9 là nốt nào?", "tension.naming", "exact", {"expected": "D"}, options=["D", "E", "F", "A"], explanation="Cmaj9 = Cmaj7 (C–E–G–B) thêm quãng 9 tính từ C. Quãng 9 là quãng 2 cộng thêm một quãng tám, tức nốt D. Vậy Cmaj9 gồm C–E–G–B–D.", provenance=[OMT_CHORD_SYMBOLS, KH_CH1_TENSION], status="draft"),
            q("L07-Q08", "mcq", "Vì sao cùng là G7 nhưng không phải lúc nào cũng dùng G Mixolydian?", "chord_scale.context", "exact", {"expected": "Vì chọn âm giai còn phụ thuộc ngữ cảnh và chức năng của hợp âm"}, options=["Vì chọn âm giai còn phụ thuộc ngữ cảnh và chức năng của hợp âm", "Vì G7 đổi nốt mỗi lần chơi", "Vì Mixolydian chỉ dùng cho nhạc rock", "Vì bảng chord-scale luôn sai"], explanation="Bảng chord-scale chỉ là điểm xuất phát. G7 đi về Cmaj7 trong C major thường dùng G Mixolydian, nhưng khi G7 đi về Cm hay làm át phụ thì kho nốt quanh nó khác, nên âm giai phù hợp cũng khác.", provenance=[OMT_CHORD_SCALE, TER_CH78], status="draft"),
            q("L07-Q09", "mcq", "Trên G7 trong C major, nốt nào của G Mixolydian thường không ngân dài vì va nửa cung với nốt B của hợp âm?", "chord_scale.context", "exact", {"expected": "C"}, options=["C", "A", "E", "D"], explanation="G Mixolydian là G–A–B–C–D–E–F. Nốt C chỉ cao hơn B (quãng 3 của G7) nửa cung, ngân dài nghe như hợp âm sus4 và che mất màu át. A, E, D là tension 9, 13 và quãng 5 nên ngân được.", provenance=[OMT_CHORD_SCALE, TER_CH78], status="draft"),
        ],
        "review_items": [
            f("L07-F01", "Các số tension (nốt mở rộng) trên hợp âm bảy", "9, 11, 13", "tension.naming", "recall", "exact", {"expected": "9, 11, 13"}, provenance=[OMT_CHORD_SYMBOLS]),
            f("L07-F02", "Chord tones của Cmaj7", "C–E–G–B", "tension.naming", "build", "music_engine", {"expected": ["C", "E", "G", "B"]}, {"kind": "build_chord", "symbol": "Cmaj7"}, [OMT_7TH]),
            f("L07-F03", "Dm7 trong C major: âm giai (mode) cơ bản", "D Dorian", "chord_scale.basic", "context", "exact", {"expected": "D Dorian"}, provenance=[OMT_CHORD_SCALE]),
            f("L07-F04", "G7 trong C major: âm giai (mode) cơ bản", "G Mixolydian", "chord_scale.basic", "context", "exact", {"expected": "G Mixolydian"}, provenance=[OMT_CHORD_SCALE]),
            f("L07-F05", "Cmaj7 trong C major: âm giai (mode) cơ bản", "C Ionian", "chord_scale.basic", "context", "exact", {"expected": "C Ionian"}, provenance=[OMT_CHORD_SCALE]),
            f("L07-F06", "Chọn âm giai cho hợp âm (chord-scale) nên bắt đầu từ điều gì?", "Giọng chủ + chức năng và ngữ cảnh của hợp âm", "chord_scale.context", "recall", "rubric", {"accepted": ["key", "function", "context", "ngữ cảnh", "ngu canh", "chức năng", "chuc nang"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_CHORD_SCALE]),
            f("L07-F07", "Nốt của hợp âm (chord tone) khác tension thế nào?", "Nốt hợp âm định hình hợp âm; tension mở rộng màu sắc tùy ngữ cảnh.", "tension.naming", "recall", "rubric", {"accepted": ["màu", "mau", "extension", "mở rộng", "mo rong", "chord tone"]}, {"mode": "contains_any", "strip_accents": True}, [KH_CH1_TENSION]),
            f("L07-F08", "Lý thuyết chord-scale có thay được tai nghe và cách nối hợp âm không?", "Không; đó chỉ là một công cụ và có giới hạn.", "chord_scale.context", "context", "rubric", {"accepted": ["không", "khong", "giới hạn", "gioi han"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_CHORD_SCALE]),
        ],
    },
    {
        "id": "L08", "order": 11, "track": "M4. Jazz", "title": "Jazz Piano Voicing: shell voicing và guide-tone connection",
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
            q("L08-Q01", "mcq", "Trong basic shell/3-note frame của lesson, ba thành phần ưu tiên là gì?", "voicing.shell", "exact", {"expected": "Root-3rd-7th"}, {"normalize_dashes": True}, ["Root-3rd-7th", "Root-5th-9th", "3rd-5th-9th", "Root-2nd-5th"], provenance=[KH_CH11], explanation="Shell voicing giữ ba nốt: root, quãng 3 và quãng 7. Quãng 3 cho biết trưởng hay thứ, quãng 7 cho biết loại hợp âm bảy, root cho biết gốc; ba nốt này đủ để nhận ra chất lượng hợp âm.", version=2),
            q("L08-Q02", "mcq", "Theo OMT Jazz Voicings, chord tone nào thường có thể lược bỏ an toàn nhất trong nhiều voicing?", "voicing.shell", "exact", {"expected": "Fifth"}, options=["Root", "Third", "Fifth", "Seventh"], provenance=[OMT_VOICINGS], explanation="Quãng 5 đúng thường lược được vì nó ít cho biết về chất lượng hợp âm (quãng 3 và 7 mới quyết định), và root có thể do bass chơi. Nếu là quãng 5 giảm hoặc tăng thì nó mang màu riêng nên không lược.", version=2),
            q("L08-Q03", "build", "Nêu shell root–3rd–7th cho G7 bằng ba tên nốt.", "voicing.shell", "rubric", {"accepted": ["g b f", "g,b,f", "g-b-f"]}, {"mode": "equals_any", "normalize_dashes": True}, explanation="Trong rubric này: G–B–F; đây không phải full chord inventory.", provenance=[KH_CH11]),
            q("L08-Q04", "mcq", "Nối hợp âm mượt (smooth voice leading) ưu tiên điều gì?", "voicing.voice_leading", "exact", {"expected": "Mỗi nốt di chuyển càng ít càng tốt"}, options=["Mỗi nốt di chuyển càng ít càng tốt", "Luôn nhảy quãng 5", "Luôn để nốt gốc ở trên cùng", "Luôn nhân đôi quãng 3"], provenance=[OMT_VOICINGS], explanation="Smooth voice leading nghĩa là mỗi giọng đi một khoảng nhỏ nhất, giữ lại nốt chung và nếu đổi thì đi bậc liền. Nhảy quãng 5, luôn để root ở trên cùng hay luôn nhân đôi quãng 3 không phải nguyên tắc của lesson.", version=3),
            q("L08-Q05", "context", "Trong G7 → Cmaj7, cách nối hai guide tone nào mượt nhất?", "voicing.voice_leading", "exact", {"expected": "B đứng yên; F hạ nửa cung xuống E"}, options=["B đứng yên; F hạ nửa cung xuống E", "B nhảy lên F; F đứng yên", "Cả hai nốt cùng nhảy lên một quãng tám", "B lên C; F lên G"], provenance=[KH_CH11, OMT_VOICINGS], explanation="G7 = G–B–D–F và Cmaj7 = C–E–G–B. Quãng 3 của G7 là B, quãng 7 là F. B trở thành quãng 7 của Cmaj7 nên đứng yên, F hạ nửa cung xuống E là quãng 3 của Cmaj7. Hai guide tone nối nhau mà gần như không phải di chuyển.", version=3),
            q("L08-Q06", "applied", "Vì sao bài 'dựng đầy đủ G7' và bài 'tạo shell voicing G7' không dùng cùng rubric?", "voicing.shell", "rubric", {"accepted": ["voicing", "lược", "luoc", "omit", "full chord", "inventory"]}, {"mode": "contains_any", "strip_accents": True}, explanation="Voicing có thể cố ý omit/double theo style; chord-inventory exercise kiểm tra đủ chord tones.", provenance=[OMT_VOICINGS, KH_CH11],
              status="draft"),  # tự luận chấm từ khóa: bài 1–4 đã đổi thành nút chọn; để draft chờ Đạt viết lại thành câu chọn (10/11)
        ],
        "review_items": [
            f("L08-F01", "Khung shell cơ bản gồm những nốt nào?", "Root–3rd–7th (nốt gốc, quãng 3, quãng 7)", "voicing.shell", "recall", "exact", {"expected": "Root-3rd-7th"}, {"normalize_dashes": True}, [KH_CH11]),
            f("L08-F02", "G7 shell root–3–7", "G–B–F", "voicing.shell", "build", "rubric", {"accepted": ["g b f", "g,b,f", "g-b-f"]}, {"mode": "equals_any", "normalize_dashes": True}, [KH_CH11]),
            f("L08-F03", "Dm7 shell root–3–7", "D–F–C", "voicing.shell", "build", "rubric", {"accepted": ["d f c", "d,f,c", "d-f-c"]}, {"mode": "equals_any", "normalize_dashes": True}, [KH_CH11]),
            f("L08-F04", "Cmaj7 shell root–3–7", "C–E–B", "voicing.shell", "build", "rubric", {"accepted": ["c e b", "c,e,b", "c-e-b"]}, {"mode": "equals_any", "normalize_dashes": True}, [KH_CH11]),
            f("L08-F05", "Nốt chung (common tone) có ích gì khi nối hợp âm?", "Giảm chuyển động và nối hợp âm mượt hơn.", "voicing.voice_leading", "recall", "rubric", {"accepted": ["mượt", "muot", "giảm chuyển động", "giam chuyen dong", "common tone"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_VOICINGS]),
            f("L08-F06", "Nối hợp âm mượt (smooth voice leading) ưu tiên điều gì?", "Mỗi nốt di chuyển càng ít càng tốt.", "voicing.voice_leading", "recall", "rubric", {"accepted": ["as little as possible", "di chuyển ít", "di chuyen it", "chuyển động gần", "chuyen dong gan"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_VOICINGS]),
            f("L08-F07", "G7 → Cmaj7: hai guide tone nối thế nào?", "B đứng yên; F hạ nửa cung xuống E", "voicing.voice_leading", "context", "rubric", {"accepted": ["b stays", "f-e", "f → e", "giữ b", "giu b", "đứng yên", "dung yen", "hạ nửa cung", "ha nua cung"]}, {"mode": "contains_any", "strip_accents": True, "normalize_dashes": True}, [KH_CH11]),
            f("L08-F08", "Công thức hợp âm khác voicing thế nào?", "Công thức = danh sách các nốt của hợp âm; voicing = cách sắp xếp, lược bớt hoặc nhân đôi các nốt.", "voicing.shell", "context", "rubric", {"accepted": ["inventory", "voicing", "omit", "lược", "luoc", "phân bố", "phan bo", "sắp xếp", "sap xep", "nhân đôi", "nhan doi", "danh sách", "danh sach"]}, {"mode": "contains_any", "strip_accents": True}, [OMT_VOICINGS, KH_CH11]),
        ],
    },
]


def lesson_by_id(lesson_id: str) -> dict[str, Any]:
    return next(x for x in LESSON_SPECS if x["id"] == lesson_id)


def all_exercises() -> list[dict[str, Any]]:
    return [item for lesson in LESSON_SPECS for item in lesson["exercises"]]


def all_review_items() -> list[dict[str, Any]]:
    return [item for lesson in LESSON_SPECS for item in lesson["review_items"]]


# L07 mở 11/11/2026 sau khi Thắng chốt mở rộng Engine (hợp âm 9/13, mixolydian; ADR-019).
MIGRATED_LESSON_IDS = {"L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08", "L11"}

# L11 "Vòng hợp âm Pop" (điểm lệch 1) nằm ở file riêng cho dễ duyệt; thứ tự học lấy từ spec["order"].
from .lesson_l11 import L11_SPEC  # noqa: E402  (cần q/f/src ở trên đã định nghĩa)

LESSON_SPECS.append(L11_SPEC)

# CP1 — Phân loại bài tập và quy tắc tương đương đáp án (SRS v1.3, mục 4.9)

Mỗi bài tập thuộc một trong 8 loại, cộng `multiple_choice` (khung chứa cho quiz sinh tự động) = 9 dòng.
Mọi JSON và kết quả dưới đây **đã chạy thật** (hàm Python hoặc `curl` tới `uvicorn app.main:app`). Ví dụ của loại chưa có hàm chấm được ghi rõ là **đề xuất, chưa thêm vào code**.

Tài liệu liên quan: [Music Engine Spec](CP1_music_engine_spec.md) · [Kịch bản demo](CP1_demo_script.md)

**Từ cần biết:**
- *strict_spelling* (chấm nghiêm theo tên nốt): phải đúng cả chữ cái và dấu hóa. G# ≠ Ab.
- *pitch_class_only* (chỉ cần đúng phím): G# = Ab. Dùng cho người mới chơi piano/guitar.
- *rhythm*: gõ nhịp, mỗi lần gõ lệch tối đa ±80 ms.

---

## 1. Bảng tổng hợp

| # | Loại SRS 4.9 | Hàm chấm (`music_engine/`) | API `/api/v1/engine/…` | Chế độ chấm | Có trong trang Practice? | Trạng thái |
|---|---|---|---|---|---|---|
| 1 | `identify_note` | **chưa có** | **chưa có** | cả hai | Không | **THIẾU** |
| 2 | `build_interval` | `grading.grade_build_interval` | `POST /grade/build-interval` | strict | Không | ĐẠT (định dạng đáp án khác SRS) |
| 3 | `identify_interval` | `grading.grade_identify_interval` | `POST /grade/identify-interval` | strict | Có | ĐẠT |
| 4 | `build_scale` | `grading.grade_build_scale` | `POST /grade/build-scale` | strict (có thêm pitch-class) | Có | ĐẠT |
| 5 | `build_chord` | `grading.grade_build_chord` | `POST /grade/build-chord` | strict hoặc pitch-class | Có | ĐẠT |
| 6 | `identify_chord` | `grading.grade_identify_chord` | `POST /grade/identify-chord` | strict | Không | ĐẠT |
| 7 | `roman_numeral` | `grading.grade_roman_numeral` | `POST /grade/roman-numeral` | strict | Có | ĐẠT |
| 8 | `tap_rhythm` | `rhythm.grade_taps` | `POST /grade/tap-rhythm` | rhythm ±80 ms | Không | ĐẠT (đơn vị thời điểm gõ khác SRS) |
| 9 | `multiple_choice` | **không có hàm Engine**; chỉ có chiến lược `exact` ở `services/grading_service.py` | không có endpoint Engine; đi qua API attempts | so chuỗi (SRS: so id) | Không (có trong Learn) | **THIẾU ở Engine, LỆCH ở service** |

**Tóm tắt (9 dòng): 5 ĐẠT · 2 ĐẠT nhưng khác định dạng SRS (dòng 2, 8) · 1 THIẾU (dòng 1) · 1 THIẾU/LỆCH (dòng 9).**

---

## 2. Từng loại

### 2.1 `identify_note` — THIẾU

- **SRS:** phím/phím đàn được tô sáng → "Eb". Đúng tên chính xác; chỉ chấp nhận nốt đồng âm khi ở `pitch_class_only`.
- **Hiện có:** chưa có hàm `grade_identify_note` và chưa có endpoint. Chỉ có các viên gạch dùng được: `Note.same_spelling` (so tên) và `Note.enharmonic_to` (so phím) trong `pitch.py`.
- **Test:** chưa có.
- **Đề xuất bổ sung** (khoảng 8 dòng, **chưa thêm vào code**; logic đã thử chạy riêng):

```python
# grading.py
def grade_identify_note(expected: str, answer: str, grading_mode: str = "strict_spelling") -> dict:
    _check_mode(grading_mode)
    e, a = parse_note(expected).with_octave(None), parse_note(answer).with_octave(None)
    ok = e.same_spelling(a) if grading_mode == "strict_spelling" else e.enharmonic_to(a)
    codes = [] if ok else [_err("ENHARMONIC_SPELLING" if e.enharmonic_to(a) else "WRONG_NOTE", ...)]
    return _result(ok, e.name, codes, grading_mode=grading_mode)
```

  Kết quả thử riêng: `("Eb","Eb")` → đúng; `("Eb","D#")` strict → `ENHARMONIC_SPELLING`; cùng cặp ở `pitch_class_only` → đúng; `("Eb","E")` → `WRONG_NOTE` (mã mới, cần thêm vào SRS 4.5).
- **JSON mẫu đề xuất:** câu hỏi `{"type":"identify_note","highlight":"Eb4"}` (frontend vẽ phím đàn; Engine chỉ nhận tên) → đáp án `"Eb"`.
- **Việc cần làm:** thêm hàm + endpoint `POST /grade/identify-note` + 4 test (đúng, đồng âm strict, đồng âm pc-only, sai nốt). Đây là tính năng mới, nên **chưa làm trong CP1**.

### 2.2 `build_interval` — ĐẠT (định dạng đáp án khác SRS)

- **SRS:** `{root: "C4", interval: "M3"}` → `["C4","E4"]`. Đúng chính xác cao độ và tên nốt, strict.
- **Hàm:** `grade_build_interval(root, interval, answer)`; **`answer` là một nốt (nốt trên) `"E4"`**, không phải danh sách hai nốt như SRS. Khác biệt định dạng; chấp nhận được vì nốt dưới đã có trong câu hỏi, nhưng cần sửa SRS hoặc chuyển đổi ở lớp API (G9).
- **Chạy thật:** các lệnh dưới đây đã chạy bằng hàm Python (trong `backend/_cp1/ex.py`) và bằng test API:

```text
build-interval {"root":"C4","interval":"M3","answer":"E4"}   -> correct=true
               {"root":"C4","interval":"M3","answer":"Fb4"}  -> ENHARMONIC_SPELLING (đúng phím, sai tên)
               {"root":"C4","interval":"M3","answer":"F4"}   -> WRONG_INTERVAL_SIZE
               {"root":"C4","interval":"M3","answer":"E5"}   -> WRONG_OCTAVE
```

- **Quy tắc tương đương:** so `Note` đầy đủ (chữ cái + dấu hóa + quãng tám). Không có chế độ pitch-class. Đáp án không ghi quãng tám ("E") được tự hiểu là quãng tám đúng (G5 trong Engine Spec).
- **Test:** `test_srs_examples.py::test_build_interval`; `test_cp1_evidence.py::test_build_interval_wrong_octave`, `::test_grade_endpoints[build-interval-…]` (mới).

### 2.3 `identify_interval` — ĐẠT

- **SRS:** hai nốt → "m7". Đúng chính xác tên quãng (A4 ≠ d5).
- **Hàm:** `grade_identify_interval(lower, upper, answer)`; nhận cả `+4`, `°5`, `o5` làm bí danh.
- **Chạy thật** (qua `curl`):

```text
POST /grade/identify-interval {"lower":"C4","upper":"F#4","answer":"d5"}
-> {"correct":false,"expected":"A4","primary_error":"WRONG_INTERVAL_SIZE",
    "message_vi":"Sai số của quãng: đếm chữ cái từ C tới F# được quãng 4. d5 và A4 cùng 6 nửa cung nhưng là hai quãng khác nhau."}
```

- **Test:** `test_srs_examples.py::test_identify_interval_a4_not_d5`; `test_cp1_evidence.py::test_grade_endpoints[identify-interval-…]`; music21: `test_intervals_all_spelling_pairs`.

### 2.4 `build_scale` — ĐẠT

- **SRS:** `{tonic: "D", type: "major"}` → 7 tên nốt. Các lớp cao độ theo thứ tự, có kiểm tra tên nốt, strict.
- **Hàm:** `grade_build_scale(tonic, scale_type, answer, grading_mode)`. Tên tham số API là `scale_type` (SRS viết `type`). Thứ tự bậc phải đúng; nốt thuộc âm giai nhưng sai bậc báo `WRONG_SCALE_DEGREE_ORDER`, nốt ngoài giọng báo `NOT_IN_KEY`.
- **Chạy thật:**

```text
{"tonic":"D","scale_type":"major","answer":["D","E","F#","G","A","B","C#"]}  -> correct=true
{"tonic":"D","scale_type":"major","answer":["D","E","Gb","G","A","B","C#"]}  -> ENHARMONIC_SPELLING, wrong_degrees=[3]
{"tonic":"C","scale_type":"major","answer":["C","D","E","F#","G","A","B"]}   -> NOT_IN_KEY
```

- **Test:** `test_srs_examples.py::test_build_scale`; `test_phase0_regressions.py::test_scale_swapped_degrees_are_not_reported_as_out_of_key`; `test_sources.py::test_scale_step_patterns[*]`; `test_music21_crosscheck.py::test_scales_match_music21[*]`; `test_phase04b_curriculum.py::test_lesson2_scale_and_roman_music_engine_graders_work_end_to_end`; `test_cp1_evidence.py::test_grade_endpoints[build-scale-…]`.

### 2.5 `build_chord` — ĐẠT

- **SRS:** `{symbol: "G7"}` → tập nốt. Tập lớp cao độ; chấp nhận thể đảo trừ khi `root_position_only`. strict hoặc pc-only.
- **Hàm:** `grade_build_chord(symbol, answer, grading_mode, root_position_only)`. Thứ tự nốt không quan trọng; thiếu, thừa, lặp nốt đều sai.
- **Chạy thật:**

```text
{"symbol":"G7","answer":["G","B","D","F"]}                                  -> correct=true
{"symbol":"G7","answer":["G","B","D","F#"]}                                 -> SEVENTH_QUALITY
{"symbol":"Ab","answer":["G#","C","D#"]}                                    -> ENHARMONIC_SPELLING   (strict)
{"symbol":"Ab","answer":["G#","C","D#"],"grading_mode":"pitch_class_only"}  -> correct=true, expected=["Ab","C","Eb"]
{"symbol":"C","answer":["E4","G4","C5"],"root_position_only":true}          -> NOT_ROOT_POSITION
```

- **Test:** `test_srs_examples.py::test_error_codes_from_srs_table[*]` (7), `::test_g7_diagnosis_message`, `::test_grading_modes`, `::test_inversions_accepted_unless_root_position_only`; `test_phase0_regressions.py` (3 test về nốt thừa/lặp); `test_api.py::test_grade_build_chord`.

### 2.6 `identify_chord` — ĐẠT

- **SRS:** các nốt → "Am7". Phân tích ký hiệu; chấp nhận bí danh (Am7 = A-7). strict.
- **Hàm:** `grade_identify_chord(notes, answer)`: gọi `identify_chord` để lấy mọi tên hợp lệ của tập nốt, rồi so gốc + loại với đáp án (đã qua `parse_chord_symbol`, nên bí danh được chấp nhận). Hàm này **không có tham số `grading_mode`**.
- **Chạy thật:**

```text
identify-chord {"notes":["A","C","E","G"],"answer":"A-7"}  -> correct=true
               {"notes":["A","C","E","G"],"answer":"A7"}   -> correct=false
```

- **Lưu ý:** tập nốt `E G C` được nhận là `C/E` (hợp âm đảo). Hàm chấp nhận đáp án "C" vì chỉ kiểm gốc + loại khi đáp án không ghi bass.
- **Test:** `test_srs_examples.py::test_identify_chord_aliases`; `test_cp1_evidence.py::test_grade_endpoints[identify-chord-…]`.

### 2.7 `roman_numeral` — ĐẠT

- **SRS:** `{key: "C", chord: "Dm7"}` → "ii7". Chữ hoa/thường và ký hiệu số phải khớp. strict.
- **Hàm:** `grade_roman_numeral(key, chord, answer)`; chuẩn hóa `o`→`°`, `dim`→`°`, `∅`→`ø` trước khi so.
- **Chạy thật:**

```text
{"key":"C","chord":"Dm7","answer":"ii7"}  -> correct=true,  convention_id="CONV-ROMAN-CLASSICAL"   (curl)
{"key":"C","chord":"Dm7","answer":"II7"}  -> ROMAN_QUALITY_MARK (đúng bậc, sai hoa/thường)
roman_numeral("A","Am",mode="minor")       -> NOT_SUPPORTED_IN_MVP (MVP chỉ giọng trưởng)
```

- **Giới hạn đã chốt cho MVP:** chỉ giọng trưởng; chỉ thể gốc; hồ sơ jazz-pop chưa có nguồn → `CONVENTION_NOT_VERIFIED`.
- **Test:** `test_srs_examples.py::test_roman_numeral`, `::test_mvp_guards`; `test_api.py::test_grade_roman`; `test_music21_crosscheck.py::test_roman_numerals_match_music21`.

### 2.8 `tap_rhythm` — ĐẠT (đơn vị thời điểm gõ khác SRS)

- **SRS:** mẫu nhịp → danh sách thời điểm gõ **theo phách**. Mỗi lần gõ lệch trong ±80 ms; không thiếu/thừa.
- **Hàm:** `rhythm.grade_taps(expected_beats, taps_seconds, bpm, tolerance_ms=80)`. Mẫu nhịp tính theo **phách**, nhưng thời điểm người học gõ nhận **theo giây** (đồng hồ trình duyệt đo ra giây); Engine đổi phách → giây bằng `giây = phách × 60 / BPM`. Khác SRS ở chỗ thời điểm gõ là giây (G9).
- **Chạy thật** (120 BPM: 1 phách = 0,5 s; bốn phách cần gõ, người học gõ 3 lần ở 0,0 s, 0,45 s, 1,09 s):

```text
POST /grade/tap-rhythm {"expected_beats":[0,1,2,3],"taps_seconds":[0.0,0.45,1.09],"bpm":120}
-> correct=false, events:
   phách 0: OK (0 ms) · phách 1: OK (−50 ms) · phách 2: LATE_ONSET (+90 ms) · phách 3: MISSED_BEAT
Biên ±80 ms (hàm Python): lệch 79 ms -> OK ; lệch 81 ms -> LATE_ONSET
```

- Mã trả về: `OK`, `EARLY_ONSET`, `LATE_ONSET`, `MISSED_BEAT`, và `EXTRA_TAP` (gõ thừa; mã tự thêm). Đầu vào không hợp lệ (rỗng, NaN, BPM ≤ 0) → `INVALID_RHYTHM`.
- **Test:** `test_rhythm_and_claims.py::test_tap_grading_at_120_bpm`; `test_phase0_regressions.py::test_tap_rhythm_rejects_empty_expected_pattern_even_with_invalid_bpm`, `::test_tap_rhythm_rejects_nonfinite_timing_values`; `test_cp1_evidence.py::test_tap_early_onset_and_80ms_boundary`, `::test_grade_endpoints[tap-rhythm-…]`.

### 2.9 `multiple_choice` — THIẾU ở Engine, LỆCH ở service

- **SRS:** câu hỏi + 4 lựa chọn → id lựa chọn. Đúng chính xác id. "Dùng cho bộ sinh quiz bằng AI". SRS nói loại này dùng lại 8 loại trên cho đáp án đúng của nó.
- **Hiện có:** Engine không có hàm này (so id bằng nhau thì không cần Engine). Lớp lưu bài tập (`services/grading_service.py::grade_payload`) có chiến lược `exact` so **chuỗi đã chuẩn hóa**; 21 câu `kind: "mcq"` trong `content/curriculum/lesson_specs.json` dùng nó. Câu mẫu thật trong file:

```json
{"id": "L01-Q01", "kind": "mcq", "prompt": "Quãng từ C lên E là gì?",
 "strategy": "exact", "answer_key": {"expected": "M3"},
 "options": ["m3", "M3", "P4", "A4"], "grader_config": {"case_sensitive": true}}
```

- **Khác SRS:** `options` là mảng chuỗi và đáp án đúng là **nội dung chuỗi** ("M3"), **không có id** lựa chọn. Với quiz sinh bằng AI (SRS 4.13) có rủi ro: hai phương án có thể trùng nhau sau khi chuẩn hóa chuỗi, hoặc AI sinh một phương án đồng âm với đáp án đúng (ví dụ "Fb" và "E").
- **Đề xuất:** chuẩn hóa JSON thành `{"options":[{"id":"a","text":"m3"}, …], "answer_id":"b"}` và chấm `chosen_id == answer_id`. Với bài nhạc lý, `answer_id` được **Engine tạo từ đáp án đúng** (giữ nguyên tắc "đáp án đúng mang tính tất định", SRS 4.13) và mọi phương án nhiễu được Engine kiểm là sai. Chưa làm trong CP1 (đổi hợp đồng dữ liệu, cần ADR).
- **Test hiện có liên quan:** `test_phase04_learning_contract.py::test_attempt_contract_handles_exact_and_music_engine_grading` (chiến lược `exact`, tôi chỉ đọc tên test, chưa đọc thân). **Chưa có** test cho id lựa chọn.

---

## 3. Bài trong nội dung hiện tại (liên hệ với Engine)

Các bài học 1–4 trong `content/curriculum/lesson_specs.json` dùng các chiến lược chấm `exact`, `rubric`, `music_engine` (mcq đi qua `exact`). Phần `music_engine` của `services/grading_service.py` mới hỗ trợ **3 loại**: `build_chord`, `build_scale`, `roman_numeral`. Loại khác trả mã `UNSUPPORTED_GRADER`. Nghĩa là `build_interval`, `identify_interval`, `identify_chord`, `tap_rhythm` mới chạy qua API Engine trực tiếp, chưa nối vào luồng lưu bài làm (G10).

---

## 4. Khoảng cách của phần phân loại bài tập

| # | Nội dung | Mức độ | Đề xuất |
|---|---|---|---|
| G9 | Hai chỗ định dạng khác SRS 4.9: `build_interval` nhận một nốt thay vì danh sách hai nốt; `tap_rhythm` nhận thời điểm gõ theo giây thay vì phách | Thấp | Sửa câu chữ SRS cho khớp code (ít rủi ro nhất) |
| G10 | `grading_service` chỉ nối 3/7 loại có hàm chấm | Trung bình (nếu nội dung cần thêm loại bài) | Thêm nhánh `elif` cho từng loại khi nội dung thực sự dùng |
| G11 | `identify_note` chưa có hàm chấm | Trung bình | Thêm theo mẫu ở mục 2.1 (khoảng 8 dòng + test) |
| G12 | `multiple_choice` so chuỗi, không có id | Trung bình | Đổi sang `{id, text}` + `answer_id`, Engine kiểm phương án nhiễu (cần ADR) |
| G13 | `Practice.tsx` chỉ có 4/9 loại (build_chord, identify_interval, build_scale, roman_numeral) | Thấp (frontend ngoài phạm vi CP1) | Ghi nhận; không đụng frontend |

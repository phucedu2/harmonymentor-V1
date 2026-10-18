# CP1 — Đặc tả Music Engine (SRS v1.3, mục 4.4.1)

Phạm vi: mốc CP1 (20/10/2026) = "Music Engine Spec (4.4.1) và Phân loại bài tập (4.9), kèm unit test chạy đạt" (SRS 11.3a).
Phiên bản code: `v0.4.0-dev`, Music Engine `0.2.0-dev` (`backend/app/music_engine/`).
Mọi ví dụ bên dưới **đã chạy thật** (Python 3.10.7, music21 9.9.2). Script chạy lại: `backend/_cp1/ex.py`.

> Chạy lại ví dụ: `cd backend && PYTHONPATH=. python _cp1/ex.py`
> Tài liệu liên quan: [Phân loại bài tập](CP1_phan_loai_bai_tap.md) · [Kịch bản demo](CP1_demo_script.md)

---

## 0. Kết quả pytest thật

Lệnh: `cd backend && pip install -r requirements.txt && python -m pytest -q`

| Lần chạy | Kết quả |
|---|---|
| Code gốc `v0.4.0-dev`, đã cài music21 | **158 passed**, 0 skipped, 1 warning (của `starlette.testclient`, không liên quan Engine) |
| Code gốc, bỏ `tests/test_music21_crosscheck.py` | 113 passed (158 − 45) |
| Sau khi thêm `tests/test_cp1_evidence.py` (9 test mới) | **167 passed**, 0 failed |
| Như trên nhưng bỏ file music21 | 122 passed |

**Lệch so với kỳ vọng "113 passed, 1 skipped":** kỳ vọng đúng khi **chưa cài music21**
(`pytest.importorskip("music21")` bỏ qua cả file đối chiếu → 113 passed + 1 skipped; trường hợp này tôi suy ra từ phép tính 158 − 45, **chưa chạy** trên môi trường không có music21). Máy này đã cài music21 nên 45 test đối chiếu chạy thật và đạt: 113 + 45 = 158. Không có test nào fail. Số theo từng file:

| File | Số test |
|---|---|
| `test_srs_examples.py` | 32 |
| `test_sources.py` | 45 |
| `test_music21_crosscheck.py` | 45 |
| `test_api.py` | 5 |
| `test_phase0_regressions.py` | 7 |
| `test_rhythm_and_claims.py` | 6 |
| 4 file Phase 0.4/1 (schema, curriculum, learning) | 18 |
| **`test_cp1_evidence.py` (mới)** | **9** |

---

## 1. Bản đồ code

| Thành phần | File | Vai trò |
|---|---|---|
| Nốt (letter, accidental, octave) | `music_engine/pitch.py` → `Note`, `parse_note` | Cao độ, MIDI, viết tên |
| Quãng | `music_engine/interval.py` → `Interval`, `interval_between`, `transpose` | Gọi tên và dựng quãng |
| Hợp âm | `music_engine/chord.py` → `CHORD_TYPES`, `parse_chord_symbol`, `identify_chord` | 11 loại, bí danh, nhận diện |
| Âm giai, giọng, số La Mã | `scale.py`, `key.py`, `roman.py` | Hỗ trợ bài tập |
| Chấm bài + mã lỗi | `grading.py` | `grade_*` và chẩn đoán SRS 4.5 |
| Nhịp | `rhythm.py` → `grade_taps` | Gõ nhịp ±80 ms |
| API | `api/engine.py` | `/api/v1/engine/...` |

**Engine không gọi LLM, không gọi mạng, không dùng database.** Các `import` trong `music_engine/*.py` chỉ gồm thư viện chuẩn (`re`, `math`, `dataclasses`, `fractions`, `collections`, `typing`). Đã kiểm bằng lệnh `grep import`. `music21` chỉ xuất hiện trong `tests/` và ở mục "chỉ cho test" của `requirements.txt`.

---

## 2. Bảng đối chiếu từng hàng của SRS 4.4.1

Trạng thái: **ĐẠT** = đúng SRS, đã chạy và có test. **LỆCH** = có nhưng khác SRS. **THIẾU** = chưa có.

### Hàng 1 — Cao độ

- **SRS:** `{letter: A-G, accidental: -2..+2, octave: 0-8}`; `midi = 12 × (octave + 1) + pc(letter) + accidental`; hiển thị "Eb4", "F##3".
- **Code:** `pitch.py` → `Note` (kiểm tra phạm vi trong `__post_init__`), `Note.midi`, `Note.__str__`, `parse_note`.
- **Giải thích cho người mới:** một nốt gồm 3 phần: chữ cái, dấu hóa, quãng tám. G#4 và Ab4 cùng phím đàn (MIDI 68) nhưng là hai nốt khác tên.
- **Ví dụ chạy thật:**

```text
>>> parse_note("Eb4").midi, str(parse_note("Eb4"))
(63, 'Eb4')
>>> parse_note("F##3").midi, str(parse_note("F##3"))
(55, 'F##3')
>>> parse_note("G#4").midi, parse_note("Ab4").midi, parse_note("G#4") == parse_note("Ab4")
(68, 68, False)            # cùng MIDI nhưng KHÁC nốt
>>> parse_note("G###4")    # ba dấu thăng
INVALID_PITCH  Không đọc được tên nốt: 'G###4'
>>> parse_note("C9")
INVALID_PITCH  Quãng tám ngoài phạm vi 0–8: 9
```

- **Test:** `test_srs_examples.py::test_midi_formula[Eb4-63 | F##3-55 | Cb4-59 | B#3-60]`, `::test_same_midi_different_names`, `::test_accidental_range_is_plus_minus_two`; `test_sources.py::test_middle_c_is_c4_and_b_below_is_b3`, `::test_enharmonic_pairs[...]`.
- **Trạng thái: ĐẠT.** Ghi chú: dấu hóa ngoài ±2 khi **đọc chuỗi** (`G###4`) cho `INVALID_PITCH`; khi **tính ra** (ví dụ `Fbdim7`) cho `UNSUPPORTED_SPELLING`. Cả hai đều là từ chối có mã, không đoán.

### Hàng 2 — 11 loại hợp âm

- **SRS:** maj, min, dim, aug, 7, maj7, m7, m7b5, dim7, sus2, sus4.
- **Code:** `chord.py` → `CHORD_TYPES` (11 mục, mỗi mục là danh sách quãng từ nốt gốc).
- **Ví dụ chạy thật** (`chord_tones("C…")`):

```text
C      -> C E G            Cm7b5 -> C Eb Gb Bb
Cm     -> C Eb G           Cdim7 -> C Eb Gb Bbb
Cdim   -> C Eb Gb          Cmaj7 -> C E G B
Caug   -> C E G#           Cm7   -> C Eb G Bb
C7     -> C E G Bb         Csus2 -> C D G      Csus4 -> C F G
```

- **Test:** `test_music21_crosscheck.py::test_chords_match_music21[maj|min|dim|aug|7|maj7|m7|m7b5|dim7|sus2|sus4]` (11 test); `test_sources.py::test_seventh_chord_qualities`, `::test_major_key_triad_qualities`, `::test_dominant_seventh_example`.
- **Trạng thái: ĐẠT.** Ghi chú: `sus2`, `sus4` được dựng đúng và khớp music21 nhưng **chưa có nguồn giáo trình** (`verified=False`, xem `claims.py → UNSOURCED`). Ghi ở G4.

### Hàng 3 — Cú pháp ký hiệu và bí danh

- **SRS:** `<root><quality>[/<bass>]`; bí danh: maj7 = M7 = Δ7; m7b5 = ø7; min = m = -; dim = °.
- **Code:** `chord.py` → `parse_chord_symbol(text, alias_profile)`, bảng `SRS_ALIASES` (đúng danh sách SRS) và `EXTENDED_ALIASES` (rộng hơn).
- **Ví dụ chạy thật** (hồ sơ `"srs"`):

```text
CM7  -> Cmaj7  C E G B        Amin -> Am   A C E
CΔ7  -> Cmaj7  C E G B        A-   -> Am   A C E
Bø7  -> Bm7b5  B D F A        A-7  -> Am7  A C E G
B°   -> Bdim   B D F          Cmaj13 -> UNKNOWN_QUALITY (từ chối, không đoán)
```

- **Test:** `test_srs_examples.py::test_srs_aliases[CM7-Cmaj7 | CΔ7-Cmaj7 | Bø7-Bm7b5 | Amin-Am | A--Am | A-7-Am7 | B°-Bdim]`, `::test_unknown_quality_is_rejected_not_guessed`; API: `test_api.py::test_engine_error_is_structured_422`.
- **Trạng thái: ĐẠT** với một lưu ý: **hồ sơ mặc định là `"extended"`** (`DEFAULT_ALIAS_PROFILE`), nhận **nhiều hơn** SRS (thêm `mi`, `o`, `+`, `ma7`, `∅`…). Đây là tập mở rộng, không mâu thuẫn, nhưng SRS chưa duyệt; code ghi rõ là QĐ-2.11 "đang chờ duyệt". Xem G3.

### Hàng 3b — Hợp âm đảo bass (C/E)

- **SRS:** "Hợp âm đảo bass (C/E) được phân tích cú pháp; chỉ kiểm tra nốt bass."
- **Code:** `chord.py` → `ChordSymbol.bass`, `.inversion`, `.bass_in_chord`. Hàm chấm `grading.grade_build_chord` **không** dùng `bass`.
- **Ví dụ chạy thật:**

```text
>>> cs = parse_chord_symbol("C/E")
>>> cs.symbol, cs.bass.name, cs.inversion, cs.notes
('C/E', 'E', 1, [C, E, G])
>>> parse_chord_symbol("C/D").bass_in_chord, parse_chord_symbol("C/D").inversion
(False, None)                      # bass D không thuộc C: vẫn đọc được
>>> grade_build_chord("C/E", ["C","E","G"])["correct"]          # bass sai nhưng...
True                                # ... vẫn được chấm đúng
>>> grade_build_chord("C/E", ["C","E","G"], root_position_only=True)["correct"]
True
```

- **Test:** `test_srs_examples.py::test_slash_chord` (chỉ test việc đọc ký hiệu, **chưa** test việc chấm bass).
- **Trạng thái: LỆCH (mức Trung bình–Thấp).** Phần "phân tích cú pháp" ĐẠT. Phần "kiểm tra nốt bass" **chưa có trong hàm chấm**: học sinh trả lời C E G cho bài C/E vẫn được tính đúng. Đề xuất ở G1; **chưa sửa** vì đổi hành vi chấm điểm, cần báo trước và ADR.

### Hàng 4 — Quy tắc viết tên nốt

- **SRS:** tên nốt theo quãng từ nốt gốc (3 = chữ cái + 2, 5 = +4, 7 = +6). Bm7b5 = B D F A; Ebm7b5 = Eb Gb Bbb Db.
- **Code:** `chord.py → ChordSymbol.notes` gọi `interval.py → transpose(root, quãng)`: lấy **chữ cái** theo số quãng, rồi mới tính dấu hóa cho đủ số nửa cung. Nhờ vậy không bao giờ ra "E#" thay cho "F".
- **Giải thích:** Ebm7b5: quãng 3 thứ → chữ G (E+2) → Gb; quãng 5 giảm → chữ B (E+4) → Bbb; quãng 7 thứ → chữ D (E+6) → Db.
- **Ví dụ chạy thật:**

```text
>>> chord_tones("Ebm7b5")  -> Eb Gb Bbb Db
>>> chord_tones("Bm7b5")   -> B D F A
>>> chord_tones("Fbdim7")  -> UNSUPPORTED_SPELLING  Fb + d7 cần dấu hóa vượt ±2
```

- **Test:** `test_srs_examples.py::test_srs_spelling_examples`, `::test_accidental_range_is_plus_minus_two`; API: `test_api.py::test_chord_lookup` (`/chord/Ebm7b5`); music21: `test_chords_match_music21[*]`, `test_transpose_matches_music21[*]`.
- **Trạng thái: ĐẠT.**

### Hàng 5 — Gọi tên quãng

- **SRS:** tên = số (khoảng cách chữ cái + 1) + tính chất từ số nửa cung; A4 và d5 đều 6 nửa cung nhưng khác nhau.
- **Code:** `interval.py → interval_between`, `Interval.semitones`, `Interval.name`.
- **Giải thích:** C→F# đếm chữ C D E F = 4 → quãng 4, mà 6 nửa cung (quãng 4 đúng chỉ có 5) → "tăng" → **A4**. C→Gb đếm C D E F G = 5 → quãng 5, 6 nửa cung (quãng 5 đúng có 7) → "giảm" → **d5**. Cùng tiếng đàn, khác tên, khác cách viết.
- **Ví dụ chạy thật:**

```text
>>> interval_between("C4","F#4")  -> A4  (6 nửa cung)
>>> interval_between("C4","Gb4")  -> d5  (6 nửa cung)
>>> grade_identify_interval("C4","F#4","A4")["correct"]  -> True
>>> grade_identify_interval("C4","F#4","d5")
    correct=False, primary_error=WRONG_INTERVAL_SIZE
    message_vi="Sai số của quãng: đếm chữ cái từ C tới F# được quãng 4. d5 và A4 cùng 6 nửa cung nhưng là hai quãng khác nhau."
```

- **Test:** `test_srs_examples.py::test_identify_interval_a4_not_d5`; `test_cp1_evidence.py::test_a4_and_d5_same_semitones_different_names` (mới); `test_sources.py::test_tritone_two_names`, `::test_inversion[A4-d5]`, `::test_compound_intervals[...]`; music21: `test_intervals_all_spelling_pairs` (1495 cặp).
- **Trạng thái: ĐẠT.**

### Hàng 6 — Lớp cao độ và quãng tám

- **SRS:** bài hợp âm/âm giai so **lớp cao độ** (bỏ quãng tám). Bài quãng/giai điệu so **cao độ chính xác**.
- **Code:** hợp âm: `grading._note_counter` sau khi gỡ quãng tám (`with_octave(None)`). Âm giai: `grade_build_scale` cũng gỡ quãng tám. Quãng: `grade_build_interval` so `Note` đầy đủ (kể cả quãng tám), báo `WRONG_OCTAVE`.
- **Giải thích:** "Dựng C": C2 + E3 + G5 đều đúng vì chỉ cần đúng tên nốt. "Dựng quãng 3 trưởng trên C4": E5 sai vì cao hơn một quãng tám.
- **Ví dụ chạy thật:**

```text
>>> grade_build_chord("C", ["E3","G5","C2"])["correct"]      -> True
>>> grade_build_interval("C4","M3","E4")["correct"]          -> True
>>> grade_build_interval("C4","M3","E5")["primary_error"]    -> WRONG_OCTAVE
>>> grade_build_interval("C4","M3","E")["correct"]           -> True   # xem ghi chú
```

- **Test:** `test_cp1_evidence.py::test_build_chord_ignores_octave`, `::test_build_interval_wrong_octave` (mới); `test_srs_examples.py::test_build_interval`, `::test_inversions_accepted_unless_root_position_only`.
- **Trạng thái: ĐẠT.** Ghi chú: nếu học sinh viết "E" **không có quãng tám**, `grade_build_interval` tự gán quãng tám của đáp án đúng (`got.with_octave(expected.octave)`), nên bài quãng chấp nhận đáp án thiếu quãng tám. SRS không nói rõ trường hợp này; ghi ở G5.

### Hàng 7 — Thể đảo / voicing

- **SRS:** mặc định chấp nhận C E G = E G C = G C E; bài tập có thể đặt `root_position_only: true`.
- **Code:** `grade_build_chord(..., root_position_only=False)`; khi bật, nốt thấp nhất (theo MIDI) phải là nốt gốc, nếu không báo `NOT_ROOT_POSITION` (mã nhóm tự thêm, chưa có trong bảng SRS 4.5; kết quả có `proposed: true`).
- **Ví dụ chạy thật:**

```text
>>> grade_build_chord("C", ["E4","G4","C5"])["correct"]                        -> True
>>> grade_build_chord("C", ["E4","G4","C5"], root_position_only=True)["primary_error"]
NOT_ROOT_POSITION
>>> grade_build_chord("C", ["C","E","G","C"])["correct"]                       -> False  # lặp nốt bị coi là thừa
```

- **Test:** `test_srs_examples.py::test_inversions_accepted_unless_root_position_only`; `test_phase0_regressions.py::test_build_chord_rejects_duplicate_tone_in_full_chord_exercise`, `::test_build_chord_rejects_extra_same_letter_tone_regardless_of_order`.
- **Trạng thái: ĐẠT.** Lưu ý: bài dựng hợp âm yêu cầu **đủ nốt**, không chấp nhận bỏ nốt hay lặp nốt (voicing jazz bỏ nốt cần bộ chấm khác, ghi trong docstring `grade_build_chord`).

### Hàng 8 — Kiểm tra đối chiếu music21

- **SRS:** chỉ đối chiếu trong bộ test, không chạy lúc vận hành.
- **Code:** `tests/test_music21_crosscheck.py`; `music21>=9` nằm ở mục "chỉ cho test" của `requirements.txt`; `app/` không `import music21`.
- **Số liệu thật** (chạy `backend/_cp1/m21.py` và `pytest tests/test_music21_crosscheck.py` → **45 passed**, 3,9 s, music21 9.9.2):

| Đối chiếu | Số trường hợp so với music21 | Ghi chú |
|---|---|---|
| Gọi tên quãng, mọi cặp (35 tên nốt × 35 tên nốt × quãng tám 4/5) | **1495** cặp so khớp | Engine từ chối 430 cặp (tăng/giảm kép-kép, quãng 1 giảm) |
| `transpose` 25 quãng × 21 nốt gốc | **509** | 16 trường hợp bị từ chối vì dấu hóa vượt ±2 |
| 11 loại hợp âm × 21 nốt gốc | **228** | 3 trường hợp từ chối (vượt ±2) |
| 5 loại âm giai × 21 chủ âm | **105** | |
| Hóa biểu | 15 giọng trưởng + 15 giọng thứ | |
| Số La Mã (15 giọng, bộ 3 nốt và bộ 4 nốt) | **210** | `IM7` so với music21 `I7` sau khi chuẩn hóa |

- **Trạng thái: ĐẠT.** Ghi chú trung thực: music21 chỉ để bắt lỗi code, **không phải nguồn kiến thức**; khi lệch phải đối chiếu lại giáo trình (ghi ở đầu file test). Bộ nhận định (`claims.py`) hiện **chưa mục nào được duyệt** (`test_nothing_is_approved_yet`): đây là việc quản trị nội dung, không ảnh hưởng kết quả test.

---

## 3. Đối chiếu bảng mã lỗi SRS 4.5 (chẩn đoán)

Ví dụ bắt buộc: `G B D F#` cho bài G7 → mã `SEVENTH_QUALITY` (đã chạy thật qua server `uvicorn` và `curl`):

```text
$ curl -X POST localhost:8765/api/v1/engine/grade/build-chord -H "Content-Type: application/json" \
       -d '{"symbol":"G7","answer":["G","B","D","F#"]}'
{"correct":false,"expected":["G","B","D","F"],
 "errors":[{"code":"SEVENTH_QUALITY","message_vi":"Bạn đang dùng quãng 7 trưởng thay vì quãng 7 thứ (F# → F).", ...}],
 "primary_error":"SEVENTH_QUALITY", "grading_mode":"strict_spelling", ...}
```

| Mã SRS 4.5 | Ví dụ SRS | Hàm sinh mã | Test | Trạng thái |
|---|---|---|---|---|
| SEVENTH_QUALITY | G7 → G B D F# | `grading._diagnose_chord` | `test_error_codes_from_srs_table[G7-answer0-...]`, `test_g7_diagnosis_message` | ĐẠT |
| THIRD_QUALITY | Am → A C# E | `_diagnose_chord` | `[Am-answer1-...]` | ĐẠT |
| FIFTH_QUALITY | Bdim → B D F# | `_diagnose_chord` | `[Bdim-answer2-...]` | ĐẠT |
| MISSING_TONE | G7 → G B F | `_diagnose_chord` | `[G7-answer3-...]` | ĐẠT |
| EXTRA_TONE | C → C E G A | `_diagnose_chord` | `[C-answer4-...]`, 2 test trong `test_phase0_regressions` | ĐẠT |
| WRONG_ROOT | Dm7 dựng trên E | `_diagnose_chord` | `[Dm7-answer5-...]` | ĐẠT |
| ENHARMONIC_SPELLING | Ab → G# C D# | `_diagnose_chord`, `grade_build_scale`, `grade_build_interval` | `[Ab-answer6-...]`, `test_grading_modes` | ĐẠT |
| NOT_IN_KEY | F# trong C major | `grade_build_scale` (bậc có nốt ngoài giọng) | Có chạy thật (xem G6) nhưng chưa test nào khẳng định mã này xuất hiện; `test_scale_swapped_degrees_...` chỉ khẳng định **không** báo nhầm | **LỆCH nhẹ** |
| WRONG_INTERVAL_SIZE | Quãng 3 trên C → F | `grade_build_interval`, `grade_identify_interval` | `test_build_interval`, `test_identify_interval_a4_not_d5` | ĐẠT |
| EARLY_ONSET / LATE_ONSET | lệch > 80 ms | `rhythm.grade_taps` | `test_tap_grading_at_120_bpm` (LATE), `test_cp1_evidence::test_tap_early_onset_and_80ms_boundary` (EARLY, mới) | ĐẠT |
| MISSED_BEAT | không gõ phách bắt buộc | `grade_taps` | `test_tap_grading_at_120_bpm` | ĐẠT |

Mã Engine tự thêm (đánh dấu `proposed: true`, chưa có trong SRS 4.5): `WRONG_INTERVAL_QUALITY`, `WRONG_OCTAVE`, `NOT_ROOT_POSITION`, `WRONG_SCALE_DEGREE_ORDER`, `ROMAN_DEGREE`, `ROMAN_QUALITY_MARK`, `EXTRA_TAP`. Nên xin giảng viên chấp nhận bổ sung vào SRS (G7).

---

## 4. Khoảng cách (Gap) — LỆCH / THIẾU

| # | Nội dung | Loại | Mức độ | Đã xử lý | Đề xuất |
|---|---|---|---|---|---|
| G1 | `grade_build_chord` bỏ qua nốt bass của hợp âm gạch chéo (`C/E`): trả lời `C E G` vẫn đúng. SRS: "chỉ kiểm tra nốt bass" | LỆCH | Trung bình–Thấp (nội dung hiện tại chưa có bài C/E) | **Chưa sửa.** Đổi hành vi chấm → cần báo trước và ADR | Nếu `expected.bass` có, yêu cầu nốt thấp nhất (hoặc nốt đầu nếu không có quãng tám) trùng tên với bass, nếu không báo mã mới `WRONG_BASS` |
| G2 | Số test thực tế (158) khác kỳ vọng "113 + 1 skipped" | Chênh số liệu | Thấp | Đã giải thích: do cài music21 | Nói rõ cả hai con số khi trình bày |
| G3 | Hồ sơ bí danh mặc định `extended` rộng hơn SRS | LỆCH nhẹ | Thấp | Chưa đổi (đổi mặc định sang `srs` là đổi hành vi) | Xin giảng viên chấp nhận tập mở rộng hoặc đặt mặc định `srs`; ghi ADR |
| G4 | `sus2`, `sus4` chưa có nguồn giáo trình (`verified=False`) | THIẾU nguồn | Thấp | Đã khớp music21; vẫn dựng | Bổ sung nguồn trước khi coi là "đã duyệt" |
| G5 | Bài `build_interval` chấp nhận đáp án không có quãng tám ("E" = "E4") | Khoảng trống đặc tả | Thấp | Chưa đổi | Thêm một dòng vào SRS ("không ghi quãng tám = quãng tám đúng") hoặc đổi thành từ chối |
| G6 | `NOT_IN_KEY` chỉ có trong bài âm giai; ví dụ SRS "F# trong giọng C major" cho nốt/hợp âm lẻ chưa có hàm riêng | THIẾU một phần | Trung bình–Thấp | **Chưa sửa** (tính năng mới) | Thêm test cho `grade_build_scale("C","major",[..."F#"...])` → `NOT_IN_KEY` (không đổi hành vi); hàm kiểm tra nốt lẻ để sau CP1 |
| G7 | 7 mã lỗi tự thêm chưa có trong SRS 4.5 | Khoảng trống tài liệu | Thấp | Đã đánh dấu `proposed: true` | Xin giảng viên xác nhận, cập nhật SRS 4.5 |
| G8 | `claims.py`: 0 mục "approved" | Quy trình nội dung | Thấp (với CP1) | — | Người duyệt rà dần trước CP2 |

**Đã làm trong lần này:** không sửa dòng code Engine nào. Chỉ **thêm** `backend/tests/test_cp1_evidence.py` (9 test, khóa hành vi hiện tại: WRONG_OCTAVE, EARLY_ONSET, biên ±80 ms, A4/d5, 5 endpoint chấm bài). 158 test cũ vẫn xanh.

**Cần ADR trước khi đổi:** G1, G3, G5 (đổi hành vi Engine).

---

## 5. Tóm tắt trạng thái SRS 4.4.1

| Hàng | Trạng thái |
|---|---|
| Cao độ | ĐẠT |
| 11 loại hợp âm | ĐẠT (sus2/sus4 chưa có nguồn) |
| Cú pháp + bí danh | ĐẠT (mặc định `extended` rộng hơn SRS) |
| Hợp âm đảo bass `C/E` | **LỆCH** (đọc được; chưa chấm bass) |
| Quy tắc viết tên nốt | ĐẠT |
| Gọi tên quãng (A4 ≠ d5) | ĐẠT |
| Lớp cao độ vs quãng tám | ĐẠT |
| Thể đảo / `root_position_only` | ĐẠT |
| Đối chiếu music21 | ĐẠT |
| **Tổng (9 mục con của 8 hàng SRS)** | **8 ĐẠT · 1 LỆCH · 0 THIẾU** |

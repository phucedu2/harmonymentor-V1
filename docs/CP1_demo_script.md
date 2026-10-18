# CP1 — Kịch bản demo 5 phút (ngày 20/10/2026)

Mục tiêu: cho giảng viên thấy **Music Engine chạy đúng, giải thích được và có test**. Không dùng AI, không cần database riêng.
Tài liệu liên quan: [Music Engine Spec](CP1_music_engine_spec.md) · [Phân loại bài tập](CP1_phan_loai_bai_tap.md)

Phân vai gợi ý: **Thắng** (Backend/Engine) nói và xác nhận kỹ thuật · **Phúc** dựng slide từ 3 tài liệu CP1 · **Đạt** chạy lại toàn bộ lệnh trước giờ demo và báo nếu có kết quả khác bảng dưới.

---

## 0. Chuẩn bị (làm trước, không tính vào 5 phút)

Dùng Git Bash (lệnh `curl` trong PowerShell là lệnh khác). Hai cửa sổ terminal.

```bash
# Cửa sổ 1 — chạy server (thư mục backend)
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8765
```

```bash
# Cửa sổ 2 — chạy các bước demo bên dưới
curl -s localhost:8765/health
# Kỳ vọng: {"status":"ok","version":"0.4.0-dev"}
```

Các kết quả "kỳ vọng" bên dưới lấy từ lần chạy thật trong phiên chuẩn bị CP1 (19/10/2026). Nếu kết quả khác, **dừng và báo Thắng**.
Dự phòng nếu server không chạy được: trong `backend/` chạy `PYTHONPATH=. python _cp1/ex.py` (cùng kết quả, không cần server). Trang Practice của frontend (`cd frontend && npm install && npm run dev`) **chưa chạy thử trong CP1**, nên chỉ là phần tùy chọn, không nằm trong kịch bản chính.

---

## 1. Kịch bản (5 phút)

| Thời gian | Bước | Lệnh | Kết quả mong đợi | Nói gì |
|---|---|---|---|---|
| 0:00–0:30 | **Mở đầu** | (slide) | — | "Engine là Python thuần, không gọi AI, không gọi mạng. Mọi đáp án đúng do code tính. Có 167 test, trong đó 45 test đối chiếu music21." |
| 0:30–1:15 | **1. Viết tên nốt đúng** (SRS 4.4.1, hàng "Quy tắc viết tên nốt") | `curl -s localhost:8765/api/v1/engine/chord/Ebm7b5` | `"notes":["Eb","Gb","Bbb","Db"]` | "Có Bbb (giáng kép) vì quãng 5 giảm của Eb phải dùng chữ B. Không bao giờ viết là A." |
| 1:15–2:00 | **2. A4 khác d5** (hàng "Gọi tên quãng") | `curl -s "localhost:8765/api/v1/engine/interval?lower=C4&upper=F%234"` rồi đổi `upper=Gb4` | `{"interval":"A4","semitones":6}` và `{"interval":"d5","semitones":6}` | "Cùng 6 nửa cung, nhưng khác tên vì đếm chữ cái: C→F là 4, C→G là 5." |
| 2:00–2:50 | **3. Chẩn đoán lỗi G7** (SRS 4.5) | khối lệnh 3 | `"primary_error":"SEVENTH_QUALITY"`, câu "Bạn đang dùng quãng 7 trưởng thay vì quãng 7 thứ (F# → F)." | "Hệ thống không chỉ báo sai: nó biết sai ở đâu. Câu giải thích có sẵn tiếng Việt, không cần AI." |
| 2:50–3:30 | **4. Hai chế độ chấm** (SRS 4.4) | khối lệnh 4 | strict → `ENHARMONIC_SPELLING`; `pitch_class_only` → `"correct":true` | "G# C D# cho Ab: người mới bấm đúng phím nên chấp nhận ở chế độ pc-only; bài nhạc lý chấm nghiêm." |
| 3:30–4:10 | **5. Gõ nhịp ±80 ms** (SRS 4.9) | khối lệnh 5 | OK, OK (−50 ms), `LATE_ONSET` (+90 ms), `MISSED_BEAT` | "Engine đổi phách ra giây theo BPM rồi so với dung sai 80 ms." |
| 4:10–4:40 | **6. Từ chối, không đoán** | `curl -s localhost:8765/api/v1/engine/chord/Cmaj13` | HTTP 422, `"code":"UNKNOWN_QUALITY"` | "Ký hiệu ngoài 11 loại đã hỗ trợ bị từ chối rõ ràng." |
| 4:40–5:00 | **7. Test thật** | `cd backend && python -m pytest -q` | `167 passed` (khoảng 10–14 s) | "158 test gốc + 9 test CP1 mới. Không cài music21 thì 45 test đối chiếu bị bỏ qua." |

### Khối lệnh 3 — chẩn đoán G7

```bash
curl -s -X POST localhost:8765/api/v1/engine/grade/build-chord \
  -H "Content-Type: application/json" \
  -d '{"symbol":"G7","answer":["G","B","D","F#"]}'
```

Kỳ vọng (rút gọn, đã chạy thật): `{"correct":false,"expected":["G","B","D","F"],"errors":[{"code":"SEVENTH_QUALITY","message_vi":"Bạn đang dùng quãng 7 trưởng thay vì quãng 7 thứ (F# → F)."…}],"primary_error":"SEVENTH_QUALITY",…}`

### Khối lệnh 4 — hai chế độ chấm

```bash
curl -s -X POST localhost:8765/api/v1/engine/grade/build-chord -H "Content-Type: application/json" \
  -d '{"symbol":"Ab","answer":["G#","C","D#"]}'
# Kỳ vọng: "correct":false, "primary_error":"ENHARMONIC_SPELLING"
# (kết quả này đã chạy bằng hàm Python và có test test_grading_modes; lệnh curl riêng cho dòng này chưa chạy, Đạt hãy chạy thử)

curl -s -X POST localhost:8765/api/v1/engine/grade/build-chord -H "Content-Type: application/json" \
  -d '{"symbol":"Ab","answer":["G#","C","D#"],"grading_mode":"pitch_class_only"}'
# Kỳ vọng: "correct":true,"expected":["Ab","C","Eb"]   (đã chạy curl thật)
```

### Khối lệnh 5 — gõ nhịp

```bash
curl -s -X POST localhost:8765/api/v1/engine/grade/tap-rhythm -H "Content-Type: application/json" \
  -d '{"expected_beats":[0,1,2,3],"taps_seconds":[0.0,0.45,1.09],"bpm":120}'
```

Kỳ vọng (đã chạy thật): `"correct":false`, các sự kiện `OK (0 ms)`, `OK (-50 ms)`, `LATE_ONSET (+90 ms)`, `MISSED_BEAT`.

---

## 2. Tám câu giảng viên có thể hỏi

**1. Vì sao A4 ≠ d5 dù cùng 6 nửa cung?**
Tên quãng gồm **số** (đếm chữ cái) và **tính chất** (suy từ nửa cung). C→F# đếm C-D-E-F = quãng 4; quãng 4 đúng có 5 nửa cung, mà ở đây có 6 nên là *tăng* (A4). C→Gb đếm C-D-E-F-G = quãng 5; quãng 5 đúng có 7 nửa cung, mà ở đây có 6 nên là *giảm* (d5). Code: `interval.py → interval_between`. Test: `test_identify_interval_a4_not_d5`, `test_a4_and_d5_same_semitones_different_names`.

**2. Engine có gọi LLM/AI không?**
Không. Các file trong `music_engine/` chỉ import thư viện chuẩn của Python (đã kiểm bằng grep). Lời giải thích lỗi là câu tiếng Việt viết sẵn trong `grading.py`. AI (khi có) chỉ được diễn đạt lại và phải gọi các hàm Engine như công cụ (`GET /engine/ai-tools` liệt kê 3 công cụ). Phần AI Tutor **chưa làm** ở v0.4.0-dev (README ghi rõ "Chưa có: Harmony Assistant/LLM").

**3. Đối chiếu music21 thế nào? Có chạy lúc vận hành không?**
Không chạy lúc vận hành: `music21` nằm ở mục "chỉ cho test" của `requirements.txt` và `app/` không import nó. Trong test (`test_music21_crosscheck.py`, 45 test) so: 1495 cặp quãng, 509 phép `transpose`, 228 hợp âm (11 loại × 21 nốt gốc, trừ 3 trường hợp bị từ chối), 105 âm giai, 30 hóa biểu, 210 số La Mã. Tất cả khớp. music21 chỉ để bắt lỗi code, không phải nguồn kiến thức; nguồn là giáo trình (`claims.py`).

**4. Vì sao lưu nốt là (chữ cái, dấu hóa, quãng tám) mà không dùng số MIDI?**
G#4 và Ab4 cùng MIDI 68 nhưng là hai nốt khác nhau về nhạc lý. Nếu chỉ so MIDI, đáp án G# C D# cho bài "dựng Ab" sẽ bị chấm đúng. MIDI chỉ là giá trị suy ra để phát âm thanh. Test: `test_same_midi_different_names`.

**5. Vì sao Ebm7b5 lại có Bbb? Có phải lỗi không?**
Không. Tên nốt suy từ **quãng tính từ nốt gốc**. Quãng 5 trên Eb dùng chữ B (E-F-G-A-B). Quãng 5 đúng là Bb; quãng 5 *giảm* thấp hơn một nửa cung nữa nên là Bbb. Viết thành "A" sẽ sai quy tắc SRS 4.4.1. Test: `test_srs_spelling_examples`.

**6. Hai chế độ chấm `strict_spelling` và `pitch_class_only` dùng khi nào?**
`strict_spelling`: bài nhạc lý (hợp âm, âm giai, quãng), phải đúng tên nốt. `pitch_class_only`: người mới trên piano/guitar, chỉ cần đúng phím. Bài hợp âm so lớp cao độ (bỏ quãng tám), bài quãng so cao độ chính xác. Thể đảo được chấp nhận trừ khi bài đặt `root_position_only`.

**7. Engine hiện có hạn chế nào? Có gì chưa làm xong?** *(trả lời trung thực, không giấu)*
Theo [Engine Spec §4](CP1_music_engine_spec.md): (a) hợp âm gạch chéo `C/E` đọc được nhưng hàm chấm chưa kiểm nốt bass; (b) loại bài `identify_note` chưa có hàm chấm, `multiple_choice` đang so chuỗi chứ chưa so id; (c) mã `NOT_IN_KEY` mới có trong bài âm giai; (d) `sus2`/`sus4` đúng theo music21 nhưng chưa có nguồn giáo trình; (e) số La Mã chỉ giọng trưởng, thể gốc (quyết định MVP). Mục (a), (b) có đề xuất sửa và sẽ ghi ADR trước khi đổi hành vi.

**8. Bộ test có thật sự bảo vệ được không? Số 113 và 158 là gì?**
Hiện **167 test đạt, 0 fail**. 113 là số test khi chưa cài music21 (suy ra từ 158 − 45; **chưa chạy** riêng trường hợp không có music21); 158 là code gốc khi đã cài music21; 167 = 158 + 9 test CP1 mới. Test mới chỉ **khóa hành vi hiện tại** (WRONG_OCTAVE, EARLY_ONSET, biên ±80 ms, A4/d5, 5 endpoint chấm bài), không đổi dòng code Engine nào.

---

## 3. Việc nên kiểm tra ngay trước demo

- [ ] Đạt chạy lại: `python -m pytest -q` ra `167 passed`.
- [ ] Mở sẵn 2 terminal, server đang chạy ở cổng 8765, lệnh `/health` trả `ok`.
- [ ] Mở sẵn slide có bảng trạng thái 4.4.1 (8 ĐẠT · 1 LỆCH) và bảng 4.9 (5 ĐẠT · 2 ĐẠT-khác-định-dạng · 1 THIẾU · 1 THIẾU/LỆCH).
- [ ] Cả nhóm thuộc 5 ý chính trong báo cáo cuối.

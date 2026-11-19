# G8: Chấm độ đúng nhạc lý câu trả lời AI Tutor (Gemini thật, 300 câu)

Ngày chạy: 19/11/2026, chiều (giờ Việt Nam), trên máy Phúc bằng Docker.
Code: nhánh `phuc-music` tại `885173b` (đã có #67 và #68: bộ định tuyến AI Tutor mới).
Mô hình: `gemini-3.5-flash-lite` (299 câu), `gemini-3.6-flash` (1 câu, dự phòng của nhà cung cấp).
Người chấm: Claude (Phúc chọn "Claude tự kiểm" từ 16/11). **Chưa có ai trong nhóm kiểm lại**, xem mục 6.

## 1. Kết quả chính

| | Số câu | Đúng | Sai | Tranh luận | Không trả lời |
|---|---|---|---|---|---|
| Trong bài (`bai`) | 240 | 229 (95,4%) | 10 | 1 | 0 |
| Ngoài bài (`ngoai`) | 60 | 48 (80,0%) | 4 | 1 | 7 |
| **Tổng** | **300** | **277 (92,3%)** | **14 (4,7%)** | **2** | **7** |

- 23 câu bẫy (câu hỏi cài sẵn tiền đề sai, ví dụ "G7 có nốt F# đúng không?"): 21 đúng, 2 sai.
- Không câu nào bị lỗi chương trình. 287 câu Gemini trả lời bình thường, 13 câu máy chủ chặn rồi trả câu dự phòng theo Music Engine. Cả 13 câu dự phòng đều đúng nhạc lý.
- Độ trễ mỗi câu (gồm định tuyến, truy hồi, Gemini, kiểm Engine): trung vị 3,9 giây, p95 15,1 giây, chậm nhất 23,8 giây. Có chờ thêm do Gemini báo 503/504 ở T194, những lần chờ đó không tính vào số đo.
- Tổng số lượt gọi Gemini: 357 cho 300 câu.

"Đúng" nghĩa là **cả kết luận và lời giải thích** đều không sai nhạc lý. Câu có nốt đúng nhưng giải thích sai (ví dụ "F đến Ab là quãng năm đúng") bị tính là sai.

## 2. So với lượt 1 (16/11, code cũ)

Lượt 1 chấm được 181 câu. So trên đúng 181 câu đó:

| | Đúng | Sai | Tranh luận | Không trả lời |
|---|---|---|---|---|
| Lượt 1 (16/11) | 131 (72,4%) | 21 | 4 | 25 |
| Lượt này (19/11) | 168 (92,8%) | 5 | 2 | 6 |

20 trong 21 câu sai ở lượt 1 nay đã đúng: bậc La Mã, hóa biểu giọng thứ, đảo quãng, tritone. Ngược lại có 7 câu lượt 1 chấm "đúng" nhưng lượt này không đạt (T003, T011, T039, T088, T100, T110, T111). Lý do chính là lượt này chấm chặt hơn phần giải thích, chứ không hẳn AI kém đi. Vì vậy hai con số chỉ so được gần đúng.

Lượt 3 (`answers_v3_codecu.jsonl`) chạy nhầm code cũ nên không dùng. Lượt 4 (`answers_v4.jsonl`, 72 câu) bị bỏ vì chạy trước khi gộp #68.

## 3. 14 câu sai

| Câu | Nhóm lỗi | AI viết | Đúng là |
|---|---|---|---|
| T003 | Thuật ngữ | F#m "quãng ba trưởng nhỏ" | quãng ba thứ |
| T011 | Giải thích quãng | "F đến Ab là quãng năm đúng" | F–Ab là m3; Db–Ab là P5 |
| T100 | Giải thích quãng | "A lên C chứa 4 nửa cung" | 3 nửa cung |
| T107 | Giải thích quãng | "D cách C# một nửa cung" (trong câu hỏi M7) | D lên C# là 11 nửa cung |
| T110 | Kích thước quãng | M6 = 8 nửa cung | 9 nửa cung |
| T218 | Shell voicing | Dm7 shell: D F A C | D F C (bỏ quãng 5) |
| T221 | Shell voicing | Fmaj7 shell: F A C E | F A E |
| T240 | Át phụ | V7/vii° là "dựng V7 trên vii°" | vii° là hợp âm giảm, không làm chủ tạm được |
| T266 | Đồng âm | Bbb trùng phím "La hoặc Sol#" | chỉ La |
| T290 | Hợp âm bảy giảm | d7 "tương đương quãng ba trưởng từ bậc năm" | từ d5 lên d7 là m3 |
| T291 | Hợp âm 13 | thường bỏ 5 và 9 | thường bỏ 11 (chỏi với 3), có thể bỏ 5 |
| T296 | Tên nốt | Bbb là "La giáng" | Si giáng kép (cùng phím La) |
| T297 | Thay thế tritone | C#7 "đúng hơn" Db7 | quy ước viết Db7 (bII7) |
| T299 | Làm theo yêu cầu | trả D F A C | hỏi tên Đô Rê Mi: Rê Fa La Đô |

Có 11/14 câu sai nằm ở **phần giải thích Gemini tự viết thêm**, còn kết luận chính (nốt, tên quãng) vẫn đúng vì đã được neo vào Music Engine. Đây là chỗ máy chủ chưa kiểm được: guardrail hiện quét tên hợp âm, nốt, quãng và số La Mã, nhưng không quét câu kiểu "X đến Y là quãng Z" hay "M6 có 8 nửa cung".

## 4. 7 câu không trả lời

- T084–T089: Lydian, Phrygian, Locrian, ngũ cung trưởng/thứ, blues. Music Engine chưa có các âm giai này, nên AI nói "Music Engine chưa tính được" rồi chỉ đưa ra công thức (công thức đều đúng). Đây là giới hạn đã biết từ lượt 1. Muốn sửa phải mở rộng Engine, tức là cần test mới và ADR.
- T274: "Cadence V–I gọi là gì?" bị từ chối với lý do "bài chưa dạy", trong khi các câu cùng loại (IV–I, V–vi, dừng ở V) đều được trả lời. Đây là lỗi định tuyến.

## 5. Phát hiện kỹ thuật (mục 1–3 đã sửa trong PR này, xem mục 5b)

1. **Guardrail chặn nhầm shell voicing.** Câu đúng "Shell voicing root–3–7 của G7 gồm các nốt G, B và F" bị `scan_reply` đánh `contradicted`, vì nó so với G7 đầy đủ là G B D F. Đã thử lại trên `885173b`:
   ```
   python -c "from app.ai.tutor.guardrail import scan_reply; print(scan_reply('Shell voicing root–3–7 của G7 gồm các nốt G, B và F.'))"
   → get_chord_tones G7: claimed 'G B F', engine 'G B D F', contradicted
   ```
   Hệ quả: T219, T222, T224, T225 rơi vào câu dự phòng, và câu dự phòng còn trích nguyên đoạn bài học "Dm7: D–F–C. G7: G–B–F" (chính đoạn này cũng bị guardrail coi là sai). Hướng sửa: bỏ qua so khớp đủ nốt khi câu nói về shell/guide tone/voicing, kèm test.
2. **Lời giải thích về quãng không được kiểm** (11 câu ở mục 3). Hướng sửa: guardrail quét thêm mẫu "<nốt> (lên|đến) <nốt> là quãng <q>" và "<q> có <n> nửa cung", rồi đối chiếu với `get_interval`.
3. **Lộ chữ nội bộ**: T020 có "theo ENGINE_FACTS", T069 và T148 có "theo kết quả từ hệ thống". Không sai nhạc lý nhưng người học không nên thấy.
4. **Bộ chấm tự động bỏ sót và báo nhầm.** `grade.py` cho "đạt" 267 câu, nhưng 11 câu sai không bị bắt. Ngược lại, nó báo nhầm "quãng năm giảm" là thuật ngữ sai (T008, T017, T097) và không đọc được tên Đô Rê Mi (T298) hay nốt có số quãng tám (T293). Bộ chấm tự động chỉ dùng để khoanh vùng, kết luận cuối vẫn do người chấm.

## 5b. Đã sửa (19/11/2026, Phúc chọn phương án "Shell + quãng + chữ nội bộ")

| Lỗi | Sửa ở đâu | Cách sửa |
|---|---|---|
| Guardrail chặn nhầm shell voicing | `ai/tutor/guardrail.py` (`_compare_chord`) | Nhìn 120 ký tự trước ký hiệu hợp âm. Ngữ cảnh "shell/root–3–7" thì phải đúng 3 nốt gốc–3–7; "guide tone/nốt 3 và 7" thì đúng 2 nốt 3–7; "voicing/lược/bỏ nốt" thì chỉ cần là tập con. Nốt không thuộc hợp âm vẫn bị bác. |
| Lời giải thích về quãng không được kiểm | `ai/tutor/notes.py` + `guardrail.py` | Nhận thêm "F đến Ab là quãng ..." (trước chỉ nhận "–", "lên"). Kiểm thêm số nửa cung: "M6 có 8 nửa cung", "A lên C ... 4 nửa cung". Không bắt câu so sánh ("rộng hơn m7 một nửa cung") hay mệnh đề sau "và". |
| Lộ chữ nội bộ | `ai/tutor/fact_anchor.py` (`scrub_internal`), gọi ở `services/ai_tutor_service.py` | Máy chủ đổi "ENGINE_FACTS" thành "Music Engine" và bỏ cụm "theo kết quả từ hệ thống". Không tốn thêm lượt Gemini. |

Kiểm trên dữ liệu thật đã có: chạy guardrail mới trên toàn bộ câu trả lời của 4 lượt (`answers`, `answers_v2`, `answers_v3_codecu`, `answers_v5`, tổng 951 câu) và 82 đoạn bài học. Chỉ có đúng 3 khẳng định mới bị bác, và cả 3 đều là lỗi thật đã chấm tay: T011 (F–Ab gọi P5), T100 (A–C 4 nửa cung), T110 (M6 8 nửa cung). Không có câu đúng nào bị bác nhầm. 4 câu shell voicing (T219, T222, T224, T225) chuyển từ "bị bác" sang "đúng".

Chưa sửa (ghi lại để làm sau): đoạn bài học L01-B08 "nâng thành F#: D–F#–A" vẫn bị đọc thành "hợp âm F# = D F# A" (lỗi cũ, không phải do Gemini), và L08-B03 "Dm7: D–F–C" khi bị cắt khỏi tiêu đề "Shell" thì không có ngữ cảnh.

Test: thêm 20 test trong `tests/test_g8_cham_nhac_ly.py`. `pytest -q` toàn bộ (cloud, 19/11/2026): **1524 passed, 46 skipped, 0 failed**. Trên `phuc-music` gốc, cùng máy: 1503 passed, 1 failed (`test_g5_eval`: groundedness_structural 94,5 < 100). Bản sửa shell voicing đưa chỉ số này về 100, nên test đó xanh lại.

## 6. Giới hạn của số đo

- Người chấm là Claude, chưa có người trong nhóm kiểm. Đề nghị Đạt đọc lại 14 câu sai, 2 câu tranh luận và khoảng 20 câu "đúng" chọn ngẫu nhiên trong `review_v5.jsonl`.
- Mỗi câu chỉ hỏi một lần, không có lịch sử chat. Gemini không tất định nên chạy lại có thể ra câu chữ khác.
- 300 câu do Claude soạn (`app/eval/theory/build.py`), chưa phải câu hỏi của người học thật. Kết quả này **chưa chứng minh chất lượng với người học thật**.

## 7. Lệnh đã chạy

```powershell
# Máy Phúc, 19/11/2026
cd "D:\aptech\Music Tutor v1\hm-phuc-music"     # git log -1: 885173b
docker compose up -d --build api
docker compose exec api python -m app.eval.theory.probe --pause 6 --out /eval/theory/answers_v5.jsonl
```
```bash
# Cloud, 19/11/2026: chấm tự động + ghép kết luận người chấm
cd backend
python -m app.eval.theory.grade --answers ../eval/theory/answers_v5.jsonl \
  --review ../eval/theory/review_v5.jsonl --out ../eval/theory/grade_v5.md
# → 300 câu. Tự động {'dat': 267, 'can_xem': 33}. Người chấm {'dung': 277, 'sai': 14, 'tranh_luan': 2, 'khong_tra_loi': 7}
```

## 8. File

- `eval/theory/answers_v5.jsonl`: 300 câu trả lời thô (không chứa khóa API hay thông tin người dùng; user là `eval-user`, `is_synthetic=true`).
- `eval/theory/review_v5.jsonl`: kết luận từng câu kèm ghi chú.
- `eval/theory/grade_v5.md`: bảng chấm, liệt kê câu sai hoặc cần xem.
- `eval/theory/review.jsonl`: giữ nguyên kết quả lượt 1 để so sánh.

## 9. Câu giảng viên có thể hỏi

1. *"92% đúng là do AI giỏi hay do máy chủ?"* Kết luận chính (nốt, quãng, bậc) phần lớn đến từ Music Engine. Gemini chỉ diễn đạt lại, và có 13 câu máy chủ đã thay luôn bằng câu Engine. Lỗi còn lại nằm ở phần Gemini tự giải thích thêm. (Thắng trả lời)
2. *"Ai chấm, có khách quan không?"* Claude chấm, có bộ chấm tự động khoanh vùng trước, và mọi kết luận đều ghi lý do trong `review_v5.jsonl`. Nhóm kiểm lại mẫu. (Đạt trả lời)
3. *"Sao không hỏi được Lydian?"* Engine chưa có mode này. Nhóm chọn cho AI nói "chưa tính được" thay vì để AI tự tính rồi có thể sai. (Phúc trả lời)

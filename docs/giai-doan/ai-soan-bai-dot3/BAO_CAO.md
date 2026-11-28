# AI soạn bài đợt 3: rà soát và sửa logic (ADR-033)

Ngày 22–23/11/2026 · nhánh `ai-soan-bai/soi-loi` từ `phuc-music` (fb87071) · Draft PR vào `phuc-music`, chưa gộp.
Phúc chốt 1A 2A 3A 4A 5A 6A 7B 8A 9A 10A 11A 12A 13A 14A và câu làm rõ 1A–9A.

## 1. Kết quả từng nghi vấn

Mỗi dòng có test trong `backend/tests/test_ai_soan_bai_dot3.py`. File này nhập module mới bên trong từng test nên chạy
được trên code cũ: trên fb87071 các test của N1–N6/V5–V7/H1–H3 đỏ, trên nhánh này cả 22 test xanh.

| Mã | Kết luận | Đã chạy thử trên code cũ | Sửa | Test |
|---|---|---|---|---|
| N1 | XÁC NHẬN | Đề "Quãng từ C lên E" + check D–F → Engine đổi M3 thành m3, miễn duyệt. "Dựng Am7" + symbol C → nhận | Ký hiệu đề ≠ phần kiểm → loại câu; đề không nêu ký hiệu → bắt duyệt; Engine sửa đáp án → bắt duyệt | `test_n1_*` (5) |
| N2 | XÁC NHẬN | "C gồm C E G và là hợp âm thứ" → "Đúng", miễn duyệt | Chỉ miễn duyệt khi mọi vế được kiểm; phủ định/lượng từ → Engine không kết luận | `test_n2_*` (2) |
| N3 | XÁC NHẬN | Khối trùng bị bỏ, câu của khối vẫn còn | `block_ref` trong schema, bỏ khối bỏ câu, đánh số lại | `test_n3_*` |
| N4 | XÁC NHẬN | AI ghi trang 9 cho phần 1–4 → kẹp lặng lẽ về trang 1 | Cờ trang ngoài phần, bám nguồn, nhầm trang, chép nguyên văn; phải tick từng cờ | `test_n4_*` (3) |
| N5 | XÁC NHẬN | Bài AI xuất bản không có trong `lesson_chunks()` | `admin/ai_index.py`: dự phòng đọc từ CSDL, Qdrant nạp khi hiện, gỡ khi ẩn | `test_n5_*` (2) |
| N6 | XÁC NHẬN | Xuất bản → `GET /lessons/{id}` trả 200 cho học sinh ngay | Xuất bản ẩn, xem trước bằng `?preview=true` (chỉ admin), nút "Hiện cho học sinh" | `test_n6_*` |
| V1 | XÁC NHẬN | Danh mục chỉ có tên khối, cắt ở 6.000 ký tự | Top-3 đoạn giống nhất mỗi trang (tối đa 10), gửi nội dung | `test_v1_v2_*` |
| V2 | XÁC NHẬN | Danh mục cố định lúc bắt đầu việc | Nháp phần trước được thêm vào kho so sánh | `test_v1_v2_*` |
| V3 | XÁC NHẬN | e5 so "query" với "passage" | "query" cả hai phía; ngưỡng hiệu chỉnh ở mục 3 | đo bằng script |
| V4 | XÁC NHẬN, sửa một phần | Trùng xét cả khối | Cờ `mixed_block` theo khái niệm AI báo kèm trang; không tự tách khối | `test_n4_cho_chep_*` |
| V5 | XÁC NHẬN | Hai bộ đếm (20 nháp, 40 phần), việc nền không có người tạo thì không bị đếm | Một hạn mức theo khóa: 30/ngày, soạn bài 12, Tutor 18 | `test_v5_*` (2) |
| V6 | XÁC NHẬN | JSON hỏng một lần → phần "failed" | Thử lại đúng 1 lần | `test_v6_*` |
| V7 | XÁC NHẬN | `/draft` cắt 14.000 ký tự, vẫn ghi cả khoảng trang | Bỏ trang không vừa, thu hẹp khoảng trang, cờ `truncated` | `test_v7_*` |
| V8 | XÁC NHẬN, sửa một phần | AI viết "xem Ví dụ 1.2" dù bài không có | Cờ `figure_ref` và `source_figure`; không đọc ký âm từ ảnh | `test_v8_*` |
| H1 | XÁC NHẬN | Sửa nháp kẹp theo 1..số trang tài liệu | Kẹp theo khoảng trang của nháp, ngoài khoảng → cờ | `test_h1_*` |
| H2 | XÁC NHẬN | `SourceWork.author = source_note` | Ghi chú vào `LessonSource.note` | `test_n6_*` |
| H3 | XÁC NHẬN | Kỹ năng AI chọn sai họ vẫn cộng mastery | Kiểu kiểm khác họ kỹ năng → bắt duyệt; chỉ câu qua `counts_for_mastery` mới tính | `test_h3_*` |

Không nghi vấn nào bị bác bỏ.

## 2. Phát hiện thêm khi tự rà (Bước 1)

| Mã | Vấn đề | Xử lý |
|---|---|---|
| M1 | TF-IDF không so được bài tóm tắt tiếng Việt với sách tiếng Anh: mọi khối sẽ "bám nguồn thấp" | Máy không có e5 và hai bên khác ngôn ngữ → một cờ `grounding_unchecked` cho cả nháp, không đo từng khối |
| M2 | Tiêu đề khối ngắn lặp từ khóa làm điểm bám nguồn của khối bịa cao giả (0,151 so với 0,078) | Đo trên lời giảng, bỏ tiêu đề |
| M3 | Xem trước bài ẩn: `display_order(...)[lesson.id]` lỗi KeyError vì bài ẩn không có số thứ tự | `.get(id, 0)` |
| M4 | Khi kho dùng vector Gemini, thêm bài AI (chưa có vector) làm số vector lệch số đoạn → cả kho rơi về BM25 | Vector 0 cho riêng đoạn bài AI; bài AI tìm qua Qdrant/BM25 |
| M5 | Hạn mức Tutor (`AI_GLOBAL_DAILY_BUDGET`) không biết lượt soạn bài đã dùng chung khóa | `global_budget_spent` xét cả phần Tutor của hạn mức chung |
| M6 | Ngưỡng trùng cũ 0,55 (TF-IDF) gộp nhầm 3/6 cặp khác ý trong bộ đánh giá | Nâng lên 0,70 (mục 3) |

## 3. Đánh giá trước/sau

Bộ `eval/ai_soan_bai/cases.jsonl`: 41 ca Claude soạn trên 4 trang mẫu tự viết (quãng, hợp âm ba, nhịp, âm giai),
không chép tài liệu có bản quyền: 13 khối, 16 câu hỏi, 12 cặp trùng. Đạt đã duyệt nhãn ngày 23/11/2026 (`status: reviewed`).

```bash
cd backend && python ../scripts/ai/danh_gia_ai_soan_bai.py --out ../eval/ai_soan_bai/ket_qua_sau_tfidf.json
cd backend && AI_GROUND_E5=1 python ../scripts/ai/danh_gia_ai_soan_bai.py --out ../eval/ai_soan_bai/ket_qua_sau_e5.json
# "trước": trỏ HM_BACKEND tới bản checkout fb87071
HM_BACKEND=/duong/dan/fb87071/backend python ../scripts/ai/danh_gia_ai_soan_bai.py --out ../eval/ai_soan_bai/ket_qua_truoc_tfidf.json
```

| Chỉ số | Trước (fb87071) | Sau, TF-IDF (CI) | Sau, e5 |
|---|---|---|---|
| Lọt đáp án sai (giữ, không cần duyệt, sai đáp án vàng) | **4/16 (25%)**: Q02, Q03, Q10, Q13 | **0** | **0** |
| Câu bị loại (kèm lý do) | 0 | 5 (đều "ký hiệu đề không khớp phần kiểm") | 5 |
| Câu giữ nhưng bắt duyệt | 2 | 7 | 7 |
| Trích trang đúng (khối có nhãn) | 73%, 3 khối sai trang không cờ | 100% | 100% |
| Bắt khối bịa/nhầm trang: precision / recall | không đo (0 cờ) | 1,0 / 1,0 | 1,0 / 1,0 |
| Bắt chép nguyên văn / nhắc hình: recall | 0 / 0 | 1,0 / 1,0 | 1,0 / 1,0 |
| Chống trùng: precision / recall | 0,57 / 0,67 (ngưỡng 0,55) | 1,0 / 0,67 (0,70) | 0,86 / 1,0 (0,95; trước 0,90: 0,55 / 1,0) |

Kết quả đầy đủ (điểm từng ca, quét ngưỡng): `eval/ai_soan_bai/ket_qua_{truoc,sau}_{tfidf,e5}.json`.
Một câu đúng tình cờ bị loại (Q09: đề D7 nhưng phần kiểm ghi giọng khác): chấp nhận mất câu thay vì để đáp án sai lọt.

**Gemini thật (Phúc chạy trên máy có khóa, tốn 1 lượt trong 12 lượt soạn bài/ngày):**

```bash
cd backend && AI_ENABLED=1 python ../scripts/ai/danh_gia_ai_soan_bai.py --live --live-out ../eval/ai_soan_bai/live_gemini.json
```

Đã chạy 23/11/2026 trên máy Phúc (Docker, commit 5ad7551, 1 lượt Gemini, `gemini-3.5-flash-lite`). Kết quả:
`eval/ai_soan_bai/live_gemini.json`. Bản không gọi mạng trên cùng máy cho đúng số như CI (0 lọt, bịa P/R 1,0/1,0, trùng P/R 1,0/0,67).

| Mục | Kết quả |
|---|---|
| Khối lý thuyết | 4/4 bám đúng trang, nhạc lý đúng, không chép nguyên văn, không nhắc hình; 2 cờ `source_figure` (trang 1, 2 có "Ví dụ 1.2", "Bảng 2.1") |
| Câu giữ | 6 (3 Engine kiểm, 3 khái niệm bắt duyệt); cả 6 đúng nhạc lý, **0 lọt đáp án sai** |
| Câu loại | 2: hợp âm giảm ("Engine thấy 0 phương án đúng"), chọn nhiều thiếu phương án |

Vấn đề thấy khi chạy thật, chưa sửa (chờ nhóm quyết):
- 3/6 câu không có lời giải nhưng vẫn qua (2 câu Engine kiểm được miễn duyệt). Có thể bắt duyệt câu thiếu lời giải, nhưng sẽ phải
  sửa nhiều test và Admin phải viết lời giải cho mọi câu.
- AI chỉ đưa 8 câu dù đề yêu cầu 10–20; sau lọc còn 6, dưới mức 8A.
- Lần chạy không lưu câu thô bị loại. Script giờ lưu `raw` để lần sau biết câu hợp âm giảm bị loại vì AI sai đáp án hay vì phần kiểm.

## 4. Sơ đồ node trước/sau

```
TRƯỚC: tách phần → [danh mục TÊN khối, cắt 6.000 ký tự, cố định] → Gemini (JSON hỏng = failed)
       → so trùng cả khối (e5 query↔passage) → kẹp trang lặng lẽ → Engine kiểm theo check (không so đề)
       → nháp → xuất bản = HIỆN NGAY → (không vào kho AI Tutor)

SAU:   extract (bỏ trang không vừa, báo) → retrieve (top-3 đoạn đã có mỗi trang + nháp phần trước)
       → generate (hạn mức chung; JSON hỏng thử lại 1 lần) → dedup (e5 query↔query; bỏ khối thì bỏ câu của khối)
       → validate (đề ↔ phần kiểm ↔ Engine; họ kỹ năng; block_ref) → flags (trang, bám nguồn, nhầm trang,
       chép, hình, trộn ý) → draft (nhật ký từng node)
       → Admin tick từng cờ + câu cần duyệt → xuất bản ẨN → Xem như học sinh → Hiện cho học sinh
       → nạp Qdrant (gỡ khi ẩn) / đường dự phòng đọc CSDL
```

## 5. File đã sửa

- Backend: `app/admin/ai_questions.py`, `ai_service.py`, `ai_job.py`, `router.py`, `content_service.py`;
  mới `app/admin/ai_review.py`, `app/admin/ai_index.py`, `app/ai/budget.py`; `app/ai/tutor/chunker.py`, `retriever.py`;
  `app/rag/store.py` (`delete_lesson`); `app/api/lessons.py`; `app/services/learning_service.py`, `ai_tutor_service.py`, `ai_pipeline.py`.
- Frontend: `src/api.ts`, `src/components/admin/AiDraftTab.tsx` (chỉ thêm hiển thị: cờ, ghi chú câu, nhật ký node,
  hạn mức, xem trước, hiện bài), `src/pages/Learn.tsx` (`?xem_truoc=`), mới `src/lib/aiDraftReview.ts` + test.
- Test: mới `tests/test_ai_soan_bai_dot3.py` (22); sửa `test_admin_ai_tai_lieu.py`, `test_ai_luyen_tap.py`,
  `test_ai_tom_tat_ca_file.py` theo hành vi mới (xuất bản ẩn, tick cờ, Engine sửa đáp án thì bắt duyệt, hạn mức mới).
- Đánh giá: `eval/ai_soan_bai/`, `scripts/ai/danh_gia_ai_soan_bai.py`. Cấu hình: `.env.example`. CI: `--min-passed`.

## 6. Số chạy thật

Chạy ngày 23/11/2026 trong container cloud, đã cất mô hình e5 ra ngoài để giống CI (TF-IDF):

| Lệnh | Trước (fb87071) | Sau |
|---|---|---|
| `cd backend && pytest -q` | 1549 passed, 46 skipped | **1571 passed, 46 skipped** (46 = test PostgreSQL cần `TEST_DATABASE_URL`) |
| `pytest tests/test_ai_soan_bai_dot3.py` | **20 failed, 2 passed** (2 test giữ chiều ngược: câu đúng vẫn được giữ) | **22 passed** |
| `cd frontend && npm test` | 311 | **313 passed** (thêm `aiDraftReview.test.ts`) |
| `npm run build` | đạt | **đạt** (`tsc` sạch) |

CI: `--min-passed` SQLite nâng 1548 → 1571.

## 7. Rủi ro còn lại

- Bộ đánh giá nhỏ (Đạt đã duyệt nhãn); mới có một lần chạy Gemini thật, ngưỡng vẫn là tạm.
- e5-small nén điểm (0,83–0,96): ngưỡng e5 sát nhau, dễ báo nhầm trên sách thật nhiều trang giống nhau.
- Câu "khái niệm" vẫn dựa vào người duyệt; Engine chỉ chặn được phần nốt/quãng/hợp âm/giọng.
- Không đọc được ký âm trên khuông (V8), chỉ cờ.
- Hạn mức tính theo nhật ký trong CSDL: lượt gọi Gemini ngoài ứng dụng (thử tay, script) không được đếm.
- Chưa thử giao diện bằng tay với Gemini thật.

## 8. Giải thích cho nhóm

- **N1, đề và phần kiểm lệch nhau.** AI viết đề "Quãng từ C lên E là quãng gì?" nhưng phần kiểm gửi Engine lại ghi D–F.
  Engine tính đúng cho D–F (m3) rồi "sửa" đáp án M3 thành m3. Học sinh chọn đúng M3 bị chấm sai. Giờ máy đọc ký hiệu
  trong đề (C, E), thấy khác D–F nên bỏ câu và ghi lý do.
- **N2, câu Đúng/Sai hai vế.** "Hợp âm C gồm C E G và là hợp âm thứ." Engine chỉ kiểm được vế nốt (đúng) nên trước đây kết
  luận "Đúng". Giờ còn chữ "thứ" chưa kiểm nên câu phải có người duyệt.
- **N3, bỏ khối nhưng quên câu.** Phần 2 lặp lại "quãng" đã dạy ở L01: khối bị bỏ nhưng 3 câu hỏi về quãng vẫn nằm trong
  bài. Giờ mỗi câu gắn số khối, bỏ khối là bỏ câu.
- **N4, trích dẫn giả.** AI ghi "trang 9" cho phần trang 1–4; trước đây máy âm thầm đổi thành trang 1, học sinh thấy
  "nguồn: trang 1" dù trang 1 không nói vậy. Giờ hiện cờ "Trang AI ghi nằm ngoài phần", người duyệt sửa và tick.
- **N5, Tutor không biết bài mới.** Học sinh học bài AI "Hợp âm ba" rồi hỏi Tutor thì Tutor chỉ tìm trong bài viết sẵn
  trong code. Giờ hiện bài là nạp vào kho Tutor, ẩn là gỡ.
- **N6, hiện ngay.** Bấm xuất bản là học sinh thấy liền. Giờ bài ẩn, admin bấm "Xem như học sinh" để thử trước.
- **V5, hạn mức.** Khóa Gemini miễn phí chỉ có 30 lượt/ngày dùng chung. Trước đây soạn bài đếm riêng và có thể ăn hết lượt
  của Tutor; giờ soạn bài tối đa 12, Tutor 18.
- **V6, JSON hỏng.** Gemini thỉnh thoảng trả thiếu dấu ngoặc; trước đây cả chương "Lỗi", giờ thử lại một lần.
- **H3, cộng nhầm thành thạo.** Câu kiểm quãng mà AI gắn kỹ năng "dựng hợp âm" thì làm đúng sẽ cộng điểm cho kỹ năng
  hợp âm. Giờ phải duyệt, và không tính thành thạo nếu chưa khớp.

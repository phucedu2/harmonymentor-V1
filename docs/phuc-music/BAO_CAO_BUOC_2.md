# Báo cáo Bước 2: logic và nội dung

Ngày 31/10/2026. Nhánh `phuc-music`, Draft PR #18. Bước 2 dựng trên nhánh của PR #12 (HM-001), theo lựa chọn 4A. Phạm vi theo M-5A: chỉ làm những phần Thắng đã chốt.

## 1. Đã làm gì

1. **Gộp PR #12 vào `phuc-music`** (`7833607`). Commit này mang theo Vitest, bảng vàng `l01_engine_scientific.json` (17 cách viết nốt gốc) và test ký âm/MIDI cho Bài 1.
2. **Phần khám phá Bài 1 lấy dữ liệu từ Music Engine** (nguyên tắc 1). API mới `GET /api/v1/music/lesson1/{root}` trả về quãng M3/m3/P5/d5/A5 và hợp âm ba trưởng/thứ/giảm/tăng, có tên nốt ASPN và MIDI. `lesson1Theory.ts` không còn tự tính nhạc lý, chỉ giữ nhãn và bộ đệm. Phần câu hỏi ngẫu nhiên của Bài 1 lấy nốt từ Engine và chấm bằng `/engine/grade/*`. API khớp bảng vàng ở cả 17 nốt gốc, kể cả các ca B#4, Cb5.
3. **Piano: phím đen hiện cả hai tên.** Danh sách "Đã chọn" hiện `D#/Eb4` thay vì chỉ `D#4`, nên người học không thấy Eb bị lặng lẽ đổi thành D#. Dữ liệu gửi đi vẫn dùng tên thăng, đúng đề xuất HM-011 trong PR #15. Xem mục 6, câu Q2.
4. **Luyện tập ghi lịch sử (FR-LRN-08, lựa chọn 2B).**
   - Máy chủ tự chấm bằng Engine; client không gửi đúng/sai.
   - Bảng mới `practice_attempts`, migration `e5f1a2b3c4d6`.
   - API `POST /api/v1/practice/attempts` và `GET /api/v1/practice/history`.
   - Trang Luyện tập hiện 10 lượt gần nhất và thống kê đúng/tổng theo từng dạng bài.
   - Lượt làm của Admin ghi `is_test`. Phần này **chưa nối mastery** (xem mục 5).
   - Bảng mới lệch ERD tài liệu 04, nên có `ADR-009-de-xuat-lich-su-luyen-tap.md` chờ Thắng duyệt schema.
5. **Lộ trình 12 bài theo SRS 2.1 Bảng 7.** Đây là phương án Claude khuyên trên thẻ quyết định. Phúc chưa chọn, và đổi lại cũng dễ.
   - Module và thứ tự lấy từ `CURRICULUM_MODULES` (`draft_specs.py`).
   - Mã L01–L08 và nội dung giữ nguyên (3A). Chỉ đổi `order` và `track`.
   - Số "Bài n" hiển thị đếm theo những bài người học đang thấy, nên không bị nhảy từ Bài 2 sang Bài 5.
   - Seed dời `order_index` sang số âm tạm trước khi đổi thứ tự, để CSDL cũ không vướng ràng buộc UNIQUE.
6. **Nội dung nháp, chờ Đạt/Astra duyệt** (`backend/app/content/draft_specs.py`).
   - L09–L12: mỗi bài có mục tiêu, nguồn trong `source_registry` và dàn ý. Chưa có câu hỏi và thẻ ôn.
   - Mục "Dùng vào sáng tác" cho L01–L04, chèn ngay trước phần tóm tắt.
   - Tất cả chỉ hiện khi `SHOW_DRAFT_CONTENT=1`. Người học không thấy gì mới, và nội dung bài đã phát hành giữ nguyên.
   - Các câu nhạc lý trong mục "Dùng vào sáng tác" đã kiểm bằng Engine (test `test_nhac_ly_trong_muc_sang_tac_khop_engine`).

## 2. Commit

| Commit | Nội dung |
|---|---|
| `7833607` | merge PR #12 (HM-001) |
| `ff92385` | feat(music): API Bài 1 từ Engine |
| `b1d17a7` | fix(lesson1): frontend gọi API, bỏ tự tính |
| `4360dbc` | fix(piano): hiện D#/Eb |
| `55970a0` | feat(practice): bảng, API, chấm phía máy chủ |
| `4ac0cf0` | feat(practice): trang Luyện tập có lịch sử |
| `a550b2c` | docs(adr): ADR-009 đề xuất |
| `05c85f6` | feat(content): lộ trình Bảng 7, nháp L09–L12, "Dùng vào sáng tác" |

## 3. Kiểm tra (chạy thật ngày 31/10/2026)

| Lệnh | Kết quả |
|---|---|
| `cd backend && pytest -q` | **370 passed, 21 skipped** (main: 325; thêm 25 API Bài 1, 7 + 2 Luyện tập, 6 lộ trình; PR #12 thêm 5) |
| `cd frontend && npm test` | **195 passed** (PR #12: 182; thêm 4 `lesson1Theory`, 9 `pianoKeyLabel`) |
| `cd frontend && npm run build` | Đạt |
| `ci.yml` | `--min-passed` nâng từ 355 lên 370 |
| `node scripts/phuc-music/luong_buoc2_luyentap.cjs` | 1440px và 390px: trả lời sai rồi đúng, lịch sử ghi "Hợp âm 1/2 đúng". Trang chỉ gọi `/practice/*`, không gọi thẳng `/engine/grade` |
| `node scripts/phuc-music/luong_buoc2_lotrinh.cjs` | Người học thấy 8 bài theo Bảng 7; chế độ nháp thấy đủ 12 bài, L01 có mục "Dùng vào sáng tác" |
| Bài 1 trên trình duyệt | Nốt gốc G#: B#4, D##5. Mỗi nốt gốc (C, Ab, G#) gọi API một lần |
| CI trên PR #18 | Xem check trên PR |

## 4. Ảnh (`anh/buoc-2/`)

- `01-luyen-tap-trong-*`: Luyện tập chưa có lượt nào.
- `02-luyen-tap-co-lich-su-*`: Luyện tập sau 2 lượt làm.
- `03-lo-trinh-nguoi-hoc`: trang Học, 8 bài.
- `03-lo-trinh-che-do-nhap`: trang Học ở chế độ nháp, 12 bài.
- `04-l01-dung-vao-sang-tac-che-do-nhap`: mục "Dùng vào sáng tác" trong Bài 1.

## 5. Chưa làm và vì sao

| Việc | Lý do |
|---|---|
| Bài kiểm tra đầu vào 12 câu | Thắng chưa chốt L-6. Tài liệu 04 (UC-06: kỹ năng đúng → 0,65, sai → 0, bỏ qua → 0) và D-3 (EMA) cho kết quả khác nhau khi dùng chung `mastery_states`. Theo M-5A thì hoãn. |
| Nối Luyện tập vào mastery (EMA) | Thắng chưa chốt L-1, L-2, L-5 (câu sinh ngẫu nhiên có tính không, trọng số bao nhiêu). Hiện mới chỉ ghi lịch sử. |
| Câu hỏi và thẻ ôn cho L09–L12 | Theo phân công, Astra soạn và Đạt duyệt. Claude chỉ soạn dàn ý. |
| "Dùng vào sáng tác" cho L05–L08 | L05–L08 chưa có nội dung chạy được (`source_audited`). |
| Số La Mã trong giọng thứ (L09) | Engine chỉ hỗ trợ giọng trưởng (QĐ-2.2, `NotSupportedInMvp`). Muốn mở thì cần test mới và ADR. |

## 6. Câu hỏi cho nhóm

- **Q1 (Phúc):** thẻ quyết định thứ tự 12 bài vẫn chờ. Nếu giữ Bảng 7, bài ii–V–I (L04, đã chạy được) đứng thứ 6, sau hai bài "Sắp có" (L05, L06). Người học vẫn mở được, nhưng nhãn sẽ ghi "Nên học sau Bài 5", mà Bài 5 lại là bài chưa có nội dung. Có nên thêm quy tắc "bỏ qua bài Sắp có khi gợi ý thứ tự" không?
- **Q2 (Phúc/Thắng):** chỉ dẫn ban đầu ghi "sửa Eb → D# ở piano", còn HM-011 (PR #15) thì để payload dùng tên thăng. Mình mới sửa phần hiển thị (D#/Eb). Có cần đổi cả payload không?
- **Q3 (Thắng):** duyệt schema `practice_attempts` (ADR-009), và chốt L-1/L-2/L-5/L-6 để làm bài kiểm tra đầu vào và EMA.
- **Q4 (Đạt/Astra):** duyệt dàn ý L09–L12 và 4 mục "Dùng vào sáng tác". Định vị nguồn của L09–L11 là Claude đề xuất, chưa đối chiếu từng trang.

## 7. Xung đột có thể gặp

- PR #12: đã gộp vào nhánh này. Nếu #12 lên main trước thì không xung đột.
- PR #15 (HM-011): `VirtualPiano.tsx` và `musicUtils.ts`.
- PR #17 (CP2): có thể đụng `learning_service.py` và `ci.yml` (`--min-passed`). Lúc gộp thì lấy giá trị cao hơn.

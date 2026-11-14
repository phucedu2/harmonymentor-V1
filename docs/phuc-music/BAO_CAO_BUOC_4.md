# Báo cáo Bước 4: Harmony Lab tối thiểu

Ngày 31/10/2026, nhánh `phuc-music`, Draft PR #18. Phúc duyệt Bước 3 lúc 13:27 và trả lời Q1–Q3 (Q1 đồng ý, Q2 duyệt, Q3 chỉ chú giải thuật ngữ ở bài đầu tiên).

## 1. Đã làm gì

**Q3 của Bước 3**
- Thuật ngữ chỉ được chú giải ở bài đầu tiên người học gặp nó. Ví dụ: "nửa cung" có chú giải ở Bài 1 nhưng không có ở Bài 2.
- Mở lại Bài 1 vẫn thấy chú giải như cũ.
- Dữ liệu này lưu ở trình duyệt, tách theo từng tài khoản. Nếu mất (chế độ riêng tư, xóa dữ liệu trình duyệt) thì các bài chú giải lại từ đầu. Như vậy an toàn cho người mới hơn là bỏ sót chú giải.

**Composition Engine** (`backend/app/composition/`, FR-18)
- Gợi ý hợp âm thay cho một ô theo 5 nhóm luật Phúc đã chốt (câu 8A), xếp theo mức độ lạ:

  | Mức | Tên | Luật |
  |---|---|---|
  | 0 | Quen tai | Cùng chức năng |
  | 1 | Hơi lạ | V7/x, mượn từ giọng thứ |
  | 2 | Lạ | Dorian/Mixolydian/Lydian, thay thế tritone |
  | 3 | Rất lạ | Chromatic mediant |

- Mỗi gợi ý có tên luật, nhãn (V7/vi, ♭VII…), lý do tiếng Việt chỉ rõ nốt nào ngoài giọng, và các nốt của hợp âm. Tất cả hợp âm đều dựng bằng Music Engine; Music Engine không bị sửa.
- Phân tích cả vòng:
  - mỗi ô có nhãn, mức độ lạ và lý do;
  - có câu tóm tắt "Chỗ lạ: ô 4 (Bb, ♭VII)";
  - có cảnh báo `NOT_IN_KEY` và `UNRESOLVED_DOMINANT` (tài liệu 04 Bảng 24). Cảnh báo không chặn lựa chọn.
- Bài cuối khóa chỉ phân tích, không chấm (câu 10A).
- 4 mẫu nền pop, ballad, bossa và lo-fi. Mỗi mẫu gồm trống, bass (nốt gốc/nốt năm) và nhịp đánh hợp âm, tính theo phách.

**Lưu dự án** (FR-17, ERD tài liệu 04 Bảng 8)
- 3 bảng mới: `composition_projects`, `chord_events`, `drum_events`. Thời gian tính theo phách, lưu dạng ký hiệu.
- API `/api/v1/projects` (tạo, xem, sửa, xóa):
  - chỉ chủ dự án thấy; người khác nhận 404;
  - xóa là xóa mềm;
  - dự án của Admin có `is_test`.
- So với ERD có thêm cột `style`, `created_at`, `updated_at`. Hai bảng `note_events` và `ai_suggestions` chưa tạo. Tất cả ghi ở **ADR-010, chờ Thắng duyệt**.

**Giao diện Harmony Lab** (`/app/composition`, theo bố cục tài liệu 04 Bảng 25)
- Thanh điều khiển:
  - giọng (15 giọng trưởng);
  - tốc độ 60–160 BPM, đổi ngay khi đang phát;
  - số ô 4–8;
  - bật/tắt từng kênh hợp âm, bass, trống;
  - lặp lại.
- Nút Phát và Lưu dính đáy màn hình trên điện thoại.
- Lưới hợp âm: mỗi ô hiện hợp âm, nhãn và mức độ lạ, và ô đang phát được tô sáng. Vòng khởi đầu là I–vi–IV–V, lấy từ danh sách hợp âm của giọng mà Engine trả về.
- Khi chọn một ô:
  - đổi sang 7 hợp âm trong giọng;
  - xem nốt trên khuông (VexFlow) và bấm nghe;
  - xin gợi ý, có thể giới hạn độ lạ tối đa;
  - mỗi gợi ý có nút "Nghe", "Dùng hợp âm này" và "Bỏ qua". Gợi ý không tự sửa vòng (nguyên tắc 5).
- Thẻ phân tích "Vì sao vòng này nghe như vậy" tự cập nhật khi đổi hợp âm.
- Phát bằng Tone.js, cao độ lấy từ API `voicings` (Music Engine). Đổi tempo không làm lệch các kênh.
- Danh sách vòng đã lưu, có Mở và Xóa.

**AI:** chưa tham gia, vì code hiện chưa có lớp AI nào. API trả `ai_used: false`, giao diện ghi "Chưa dùng AI", và mọi chức năng chạy khi tắt AI. Khi lớp AI của Đạt sẵn sàng, AI chỉ được xếp lại thứ tự và viết lại lời giải thích cho các ứng viên mà luật đã sinh.

## 2. Commit

| Commit | Nội dung |
|---|---|
| `b291460` | feat(lesson): chỉ chú giải thuật ngữ ở bài đầu tiên (Q3) |
| `17df040` | feat(composition): 5 luật, độ lạ 0–3, phân tích, 4 mẫu nền |
| `70a6fe4` | feat(composition): API dự án theo ERD, gợi ý, phân tích; migration `f6a2b3c4d5e7` |
| `84d62a4` | feat(composition): API thế bấm hợp âm (cao độ + bass) |
| `8a33dcc` | feat(sang-tac): giao diện Harmony Lab |
| `0d3c518` | test(phuc-music): kịch bản người mới, WCAG có thẻ gợi ý, ảnh |
| (cuối) | docs: ADR-010, báo cáo này, tiến độ, AI_USAGE; `ci.yml` nâng `--min-passed` lên 409 |

## 3. Kiểm tra (chạy thật ngày 31/10/2026)

| Lệnh | Kết quả |
|---|---|
| `cd backend && python -m pytest -q` | **409 passed, 21 skipped**. Bước 3 có 371; thêm 36 test Harmony Lab (có 15 test, mỗi test một giọng trưởng) và 2 test migration |
| `cd frontend && npm test` | **225 passed**. Thêm 1 test chú giải theo bài và 5 test lịch phát/lưới |
| `cd frontend && npm run build` | Đạt |
| `kiem_tra_wcag.cjs` (axe-core) | **0 vi phạm** trên 16 màn × 2 cỡ, gồm cả Harmony Lab khi có thẻ gợi ý. Kết quả ở `kiem_tra_wcag_buoc4.txt` |
| `luong_buoc4_harmony_lab.cjs` (người mới, 1440px và 390px) | **Mục tiêu A:** chọn Bossa, phát lặp, tắt trống, lưu thành công. **Mục tiêu B:** chọn ô 4 bằng bàn phím, gợi ý ra 7 hợp âm (Bdim Bb Gm Db7 B Eb E), dùng Bb thì phân tích báo "Vòng hơi lạ (mức 1/3). Chỗ lạ: ô 4 (Bb, ♭VII)". Không có lỗi trang |
| `ci.yml` | `--min-passed` từ 371 lên 409 |
| CI trên PR #18 | Xem check trên PR |

## 4. Ảnh (`anh/buoc-4/`)

- `00-sang-tac-*-truoc.png`: trang Sáng tác trước Bước 4 (chỉ có chữ "Sắp mở").
- `01-harmony-lab-*.png`: trang mới, vòng I–vi–IV–V. `01-harmony-lab-390-man-hinh-dau.png` cho thấy nút Phát/Lưu luôn nằm ở đáy màn hình 390px.
- `02-goi-y-o-4-*.png`: gợi ý cho ô 4, chia nhóm theo độ lạ.
- `03-phan-tich-*.png`: sau khi dùng Bb (♭VII), phần phân tích giải thích chỗ lạ.

## 5. Còn lại và vì sao

| Việc | Lý do |
|---|---|
| AI xếp hạng và giải thích gợi ý | Chưa có lớp AI (phần của Đạt). Đã chừa chỗ: `ranked_by`, `ai_used` |
| Giai điệu (`note_events`), cảnh báo `MELODY_CLASH` | Tài liệu 04 mục 6.8 xếp giai điệu vào hướng phát triển |
| Nhật ký gợi ý (`ai_suggestions`) và API accept/reject | Tài liệu 04 ghi là hướng phát triển. Hiện chấp nhận gợi ý ngay trên giao diện rồi lưu |
| Giọng thứ | Engine chỉ hỗ trợ số La Mã giọng trưởng (QĐ-2.2) |
| Nhiều hợp âm trong một ô | Lưới tối thiểu là một hợp âm mỗi ô; ERD đã hỗ trợ (`start_beat`, `duration_beats`) |
| Nối mục "Dùng vào sáng tác" trong bài học (nháp L01–L04) với Harmony Lab | Nháp chưa được Đạt/Astra duyệt nên chưa thêm đường dẫn |
| Âm thanh mẫu nền | Tổng hợp bằng Tone.js (câu 7A); chưa có mẫu thu âm thật |

## 6. Câu hỏi cho nhóm

- **Q1 (Thắng):** duyệt ADR-010: 3 bảng mới, thêm cột `style`/`created_at`/`updated_at`, chưa tạo `note_events`/`ai_suggestions`.
- **Q2 (Đạt/Astra):** kiểm 5 luật và lời giải thích tiếng Việt trong `backend/app/composition/rules.py`. Mấy điểm Claude tự đề xuất, chưa có nguồn đã đọc:
  - bảng chức năng chủ/hạ át/át;
  - chọn hợp âm mượn theo bậc đang đứng;
  - Dorian đặt ở bậc I và Lydian ở bậc ii/IV.
- **Q3 (Phúc):** nghe thử 4 mẫu nền (Pop, Ballad, Bossa, Lo-fi). Mẫu nào cần chỉnh nhịp trống hay bass không?

## 7. Xung đột có thể gặp

- PR #17 (CP2): có thể đụng `ci.yml` (`--min-passed`) và chuỗi migration. Nếu #17 thêm migration mới thì phải nối lại `down_revision` và lấy mức `--min-passed` cao hơn.
- Nhánh của Đạt (AI): nên gọi `suggest()` để lấy ứng viên rồi chỉ xếp hạng hoặc giải thích, không tự sinh hợp âm.

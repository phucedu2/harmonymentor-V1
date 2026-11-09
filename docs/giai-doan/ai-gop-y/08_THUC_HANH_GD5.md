# GĐ5: thực hành bằng piano ảo và liên kết học thêm

Ngày 09/11/2026 · nhánh `ai/gd5-thuc-hanh` (từ `phuc-music`). Phúc duyệt phạm vi ngày 09/11.

## Đã làm

| Việc | Chi tiết |
|---|---|
| Bấm piano để trả lời Luyện tập | Dạng "Dựng hợp âm" và "Dựng âm giai" có nút chọn **Gõ tên nốt / Bấm piano**. Âm giai phải bấm đúng thứ tự bậc. Quãng và số La Mã vẫn gõ chữ (máy chủ trả 422 `PRACTICE_INPUT_INVALID` nếu gửi piano) |
| Chấm bằng Music Engine | Phím đen có hai tên (C#/Db) nên phím không thể hiện cách viết. Máy chủ chấm theo lớp cao độ bằng chế độ Engine có sẵn `pitch_class_only`, rồi nhắc cách viết chuẩn (ví dụ Ebm7b5 → Eb Gb Bbb Db). **Không sửa Engine.** Gõ chữ vẫn chấm chính tả như cũ |
| Lịch sử | Lượt bấm piano lưu `"input": "piano"` trong đề và hiện "(bấm piano)" ở lịch sử, để không lẫn với lượt chấm chính tả. Không cần migration (cột JSON) |
| Học thêm bên ngoài | Mỗi bài L01–L05 có 2–4 liên kết tới sách mở miễn phí: Open Music Theory và Music Theory for the 21st-Century Classroom (hai nguồn đã có trong `source_registry`). Mở tab mới, không nhúng, không chép nội dung. File `backend/app/content/external_resources.py` |
| Duyệt trước khi hiện | Mọi liên kết để `status: "draft"`: người học không thấy cho tới khi Đạt duyệt (xóa `status` của mục). Bật `SHOW_DRAFT_CONTENT=1` thì thấy kèm nhãn "Nháp, chờ duyệt" |

## Kiểm chứng

- `pytest`: 1014 đạt, 43 bỏ qua (thêm 10 test trong `test_ai_gd5_piano_input.py` và `test_ai_gd5_hoc_them.py`). CI nâng `--min-passed` lên 1014.
- `npm test` 263 đạt, `npm run build` đạt (xem PR).
- 16 địa chỉ liên kết đã kiểm còn mở ngày 09/11/2026: trang MT21C trả 200 trực tiếp; trang Open Music Theory chặn máy kiểm (403) nên đối chiếu bằng mục lục của chính sách đó.
- Chưa thử bằng tay trên trình duyệt.

## Cần người duyệt

- **Đạt**: 16 liên kết có khớp nội dung từng bài không (đặc biệt L03 và L04). Duyệt mục nào thì xóa `status` mục đó.
- Tài liệu đều bằng tiếng Anh; chưa tìm được sách mở tiếng Việt đủ uy tín.
- Chưa làm: guitar ảo, nhận nốt qua micro (ngoài phạm vi Phúc chọn).

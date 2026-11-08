# Phiếu câu hỏi cho AI Tutor (GĐ2 góp ý thầy)

| File | Ai điền | Số câu | Dùng để |
|---|---|---|---|
| `phieu_Dat_test.json` | Đạt | 10 | Tập test khóa: đo chính thức, Claude không xem |
| `phieu_Thang_test.json` | Thắng | 10 | Tập test khóa: đo chính thức, Claude không xem |
| `phieu_Phuc_dev.json` | Phúc | 30 | Tập dev: script tự chọn ngưỡng |

Hạn: 08/11/2026. Điền xong thì gửi file cho Thắng gộp.

## Cách điền

Mỗi câu là một dòng `{"flow": "A", "q": "câu hỏi"}`. Điền `q`, sửa `flow` nếu cần, ghi `ngay`.

| flow | Khi nào | Ví dụ |
|---|---|---|
| A | Bài L01–L04 có dạy điều này | "c7 voi cmaj7 khac nhau cho nao vay" |
| B | Nhạc lý nhưng bài chưa dạy | "Dsus2 gồm những nốt nào?" |
| C | Ngoài phạm vi, hoặc câu tấn công | "nên mua piano điện hay piano cơ" |
| D | Hỏi cách dùng web | "đổi sang guitar trong phần sáng tác ở đâu" |
| G | Chào hỏi, cảm ơn | "cảm ơn nha" |

## Lưu ý

- Viết như học sinh thật: không dấu, viết tắt, lẫn tiếng Anh, sai chính tả nhẹ.
- Không chép câu trong bài học, không sửa vài chữ từ ví dụ ở trên.
- Tự viết, không xem phiếu của bạn khác.
- Phân vân A hay B: nếu bài đã dạy khái niệm thì là A, kể cả khi hỏi một trường hợp cụ thể ("Am là bậc mấy trong Đô trưởng" là A).
- Không để `q` trống. Muốn thêm câu thì chép thêm một dòng.

## Kiểm sau khi nộp (Thắng chạy)

```bash
cd backend
python ../scripts/ai/gop_y/kiem_trung_du_lieu.py --test ../docs/giai-doan/ai-gop-y/phieu-cau-hoi/phieu_Dat_test.json
python ../scripts/ai/gop_y/danh_gia_dinh_tuyen.py --set ../docs/giai-doan/ai-gop-y/phieu-cau-hoi/phieu_Dat_test.json
python ../scripts/ai/gop_y/hieu_chinh_nguong.py --dev ../docs/giai-doan/ai-gop-y/phieu-cau-hoi/phieu_Phuc_dev.json
```

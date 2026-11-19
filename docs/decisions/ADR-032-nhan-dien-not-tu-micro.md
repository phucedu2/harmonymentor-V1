# ADR-032: Nhận diện nốt từ micro (YIN + model MLP) để trả lời bài Luyện tập

- Ngày: 19/11/2026
- Trạng thái: Đề xuất (Draft PR vào `phuc-music`, chờ nhóm duyệt)
- Người quyết định phạm vi: Phúc (5 câu: 1A 2A 3A 4A 5A)
- Liên quan: FR-EX-14 (chế độ chấm `pitch_class_only`), FR-COM-ADV-07 (Chấm qua micro, P2, Hướng phát triển)

## Bối cảnh

Mục tiêu MVP của dự án là "người học nhận được phản hồi đúng/sai về nốt đã chơi". Phúc muốn tích hợp một model AI tự
train (học theo sách *Hands-On Machine Learning*, repo `ageron/handson-ml3`) vào app.

**Mâu thuẫn với tài liệu 2.1:** SRS 01 mục Phạm vi ghi "Chấm điểm qua micro" là *ngoài phạm vi*; tài liệu 02 xếp
FR-COM-ADV-07 "Chấm qua micro" mức P2, giai đoạn "Hướng phát triển". Phúc chọn 5A: làm theo ADR này, Phúc báo Thắng và
Đạt, tài liệu 2.1 sửa sau khi nhóm đồng ý. Khi nhóm không đồng ý, tắt bằng cách bỏ lựa chọn "Đàn bằng micro" (một dòng
trong `Practice.tsx`); backend vẫn tương thích.

## Quyết định

1. **Phạm vi (1A):** một nốt mỗi lúc (đơn âm). Hợp âm đánh cùng lúc (đa âm) không làm. Người học *rải* từng nốt của hợp
   âm hoặc đàn lần lượt 7 nốt âm giai.
2. **Chỗ đặt (2A):** thêm cách trả lời "Đàn bằng micro" bên cạnh "Bấm piano" ở Luyện tập (Dựng hợp âm, Dựng âm giai).
3. **Nhạc cụ (3A):** piano, guitar, hát. Dải nốt E2–E6 (MIDI 40–88).
4. **Chạy trên trình duyệt (4A):** âm thanh không rời máy, không ghi âm. Mỗi nốt ổn định chỉ gửi *một con số* (Hz) lên
   `GET /api/v1/engine/note-from-frequency`.
5. **Music Engine vẫn là nguồn sự thật:** hàm mới `note_from_frequency(hz)` (midi = 69 + 12·log2(f/440), làm tròn,
   tính cent lệch, từ chối ngoài 27,5–4186 Hz bằng `INVALID_PITCH`). Frontend không đặt tên nốt. Tần số không cho biết
   cách viết (G# hay Ab), nên lượt `input: "micro"` chấm `pitch_class_only` giống "piano" và nhắc cách viết chuẩn.
   Lịch sử ghi `question.input = "micro"` để không trộn với lượt gõ tên khi thống kê.
6. **Bộ nhận diện, mặc định "Kết hợp":**
   - YIN (thuật toán, de Cheveigné & Kawahara 2002), ngưỡng 0,15, chỉ nhận khi độ rõ ≥ 0,8.
   - Model MLP (scikit-learn, 254 đặc trưng → 128 nơ-ron ReLU → 50 lớp: 49 nốt + "không có nốt"), train bằng
     `scripts/ai/pitch/`. Trọng số xuất JSON (210 KB, nạp lười) và **tự tính trên trình duyệt** (`features.ts`), không thêm
     TensorFlow, ONNX hay thư viện nào vào backend lẫn frontend.
   - Kết hợp: YIN chắc chắn thì dùng YIN; YIN bỏ qua thì hỏi model. Người học đổi được ở ô "Bộ nhận diện".
7. **Một nốt chỉ tính một lần:** cùng nửa cung giữ 5 khung liên tiếp (≈ 200 ms) mới tính, lấy trung vị; muốn ghi lại
   cùng nốt phải ngắt tiếng ≥ 3 khung. Nốt nghe nhầm thì bấm phím trên piano ảo để bỏ trước khi nộp.

## Vì sao không chỉ dùng YIN, hay chỉ dùng model

Đo trên 6.335 khung test giữ riêng (bản thu chưa từng train), ngày 19/11/2026 (`KET_QUA_MODEL.md`):

| | YIN | Model | Kết hợp |
|---|---|---|---|
| Đúng nốt, toàn bộ test | 59,8% | 96,5% | **96,9%** |
| Đúng khi có trả lời | **98,7%** | 98,3% | 98,2% |
| Sạch / nhiễu 15 dB | 98,5% / 98,4% | 98,8% / 98,5% | **99,0% / 99,0%** |
| Rất ồn (5 dB) | 0,0% | 97,3% | 97,3% |
| Ù điện 50 Hz | 6,9% | 91,8% | 91,9% |

YIN rất chính xác khi chịu trả lời, nhưng gặp ồn thì im lặng. Model chịu ồn nhưng có lúc nhầm quãng tám (0,7% so với
0,2%). Kết hợp lấy ưu điểm của cả hai. Số đo trên mẫu thu sẵn + nhiễu mô phỏng, **chưa chứng minh chất lượng với micro
thật của người học.**

## Hệ quả

- Engine thêm `note_from_frequency` + `FrequencyReading` (không đổi hàm cũ); 18 test pytest mới.
- Backend nhận `input: "micro"` ở `POST /practice/attempts` (chỉ chord, scale; dạng khác trả `PRACTICE_INPUT_INVALID`).
- Sửa `dac_trung.py` thì phải train lại và xuất lại `parity.json`; test Vitest `features.test.ts` sẽ đỏ nếu bản Python và
  TypeScript tính khác nhau.
- Giọng hát trong dữ liệu là giọng **tổng hợp** (repo chưa có bản thu giọng CC0), model đúng 83,5% với giọng. Cần nhóm thu
  thêm giọng thật (mỗi bạn hát 20 nốt) rồi train lại.
- Trình duyệt chỉ cho micro qua https hoặc localhost; Docker trên máy nhóm dùng localhost nên chạy được.

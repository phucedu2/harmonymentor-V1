# ADR-041: Tinh gọn Admin, lời giải do Music Engine viết, duyệt theo người sửa

- Trạng thái: Đề xuất (Phúc chọn 1A–6A, 8A ngày 27/11/2026; chờ nhóm duyệt PR)
- Liên quan: ADR-028 (câu AI soạn), ADR-033/034 (đợt 3, 4 AI soạn bài), ADR-035 (form câu hỏi), ADR-036 (quyền Admin),
  ADR-037 (kỹ năng tự tạo), MUS-INT-010 (quãng kép)

## Bối cảnh

Phúc dùng thử AI soạn bài với Gemini thật (PDF "Nhạc lý nâng cao", 65 trang) và thấy:

1. Tab Người dùng có nút "Nâng lên Quản trị" không cần thiết.
2. Tab "Kỹ năng & nguồn" trùng vai với AI soạn bài.
3. Câu admin tự sửa vẫn bắt tick "Đã duyệt".
4. Nhiều câu AI soạn thiếu lời giải, học sinh làm sai không biết sai ở đâu.
5. Câu "quãng 2 trưởng mở rộng thành quãng kép nào?" có đáp án Engine **M2** (đúng phải là **M9**).
6. Dòng "Lượt Gemini…" khó hiểu (soạn bài ghi "còn", Tutor ghi "đã dùng").

## Quyết định

### 1. Gỡ đổi vai trò qua web (1A)
Xem phần bổ sung ở ADR-036. `PATCH /admin/users/{id}` chỉ còn `is_active`.

### 2. Kỹ năng thành mục "Nâng cao" trong tab Bài học; bỏ mục Nguồn (2A)
- Không bỏ hẳn phần kỹ năng: AI soạn bài chỉ được gán kỹ năng **có sẵn** (`_skill_ids`), nên đây là chỗ duy nhất để thêm
  kỹ năng khi tài liệu dạy kiến thức hoàn toàn mới. Mục thu gọn, chỉ tải khi mở.
- Bỏ mục "Nguồn tài liệu" khỏi giao diện: AI soạn bài tự gắn nguồn (tên tài liệu + trang), bài gốc do `curriculum_specs`.
  API nguồn giữ nguyên (không xóa dữ liệu). File nhập bài (FR-ADM-39) được tự khai nguồn mới bằng `title` (+ `author`, `url`);
  nhập lại tìm theo tên, không tạo trùng; chạy thử (`dry_run`) không tạo nguồn.

### 3. Duyệt theo người sửa (3A)
- Câu admin tạo bằng form: đã coi là duyệt từ trước (ADR-035), giữ nguyên.
- Câu AI mà Quản trị viên **đã sửa** đề, đáp án mẫu, ý chấm hoặc lời giải: giao diện gửi cờ `edited: true`. Máy chủ chỉ tin cờ
  này trên đường Quản trị viên lưu bản nháp (`trust_review=True`), nên AI không tự gắn được. Có cờ thì câu tính là đã duyệt,
  **với điều kiện** câu khái niệm có lời giải (câu mở thì không cần).
- Câu AI chưa ai sửa mà Engine không kiểm được: vẫn phải tick "Đã duyệt" như cũ.

### 4. Lời giải và lời chỉ chỗ sai do Music Engine viết (4A, 5A)
- Module mới `backend/app/admin/ai_explain.py` ghép câu chữ từ số liệu Engine (tên quãng, số nửa cung, nốt hợp âm, âm giai,
  số La Mã). Ví dụ: "Đếm chữ cái từ C tới E được 3 chữ cái (C, D, E) → quãng 3. Khoảng cách 4 nửa cung → quãng 3 trưởng (M3)."
- Câu Engine kiểm được mà AI bỏ trống lời giải: Engine điền, gắn `explanation_source = "engine"`. Lời giải AI đã có thì giữ
  (guardrail soát khi xuất bản).
- Câu trắc nghiệm Engine kiểm: phương án sai AI chưa giải thích thì Engine điền bằng đúng câu chữ chấm bài của Engine
  (vd "Sai số của quãng: đếm chữ cái từ C tới E được quãng 3."). Học sinh thấy lời này khi chọn sai (`grading_service._option_feedback`).
- Câu khái niệm: Gemini vẫn viết lời giải trong cùng lần soạn (không thêm lượt); thiếu thì bắt người viết.
- Form câu hỏi: bỏ trống lời giải được nếu Engine tính được câu.
- Chữ Engine viết đã soát bằng guardrail: 456 mẫu (quãng đơn/kép giữa 12 nốt, 9 loại hợp âm × 12 gốc, 2 loại âm giai × 12,
  số La Mã 5 giọng), 0 chỗ bị báo sai. Ban đầu "C D E" liền nhau bị guardrail đọc thành "hợp âm E gồm C D E" nên đổi sang
  ngăn bằng dấu phẩy.

### 5. Nút "Tự điền lời giải" (6A)
`POST /admin/ai/drafts/{id}/fill-explanations`: chuẩn hóa lại bản nháp đang lưu (giữ dấu đã duyệt/đã sửa), trả số câu vừa
được điền và số câu khái niệm còn thiếu. Không gọi Gemini, không tốn lượt. Ghi nhật ký `ai.draft.fill_explanations`.

### 6. Lỗi quãng kép
- Nguyên nhân: `interval_between("C", "D")` không có số quãng tám nên luôn ra quãng đơn (đúng theo MUS-INT-010); AI ghi phần
  kiểm C–D cho câu hỏi quãng kép, bộ đối chiếu không xét chữ "quãng kép" trong đề.
- Sửa ở bộ đối chiếu (`ai_questions.compound_check`), **không đổi Engine**: đề có "quãng kép", "quãng 9–15", "quãng chín/mười…"
  hoặc "compound" mà phần kiểm là hai tên nốt không quãng tám thì đổi thành C4–D5 (quãng đơn + 7) rồi để Engine tính → M9.
  Vẫn thêm ghi chú bắt người đọc lại một lần vì đề kiểu này hiếm.

### 7. Dòng hạn mức Gemini
"Lượt Gemini hôm nay: soạn bài còn X/12 · AI Tutor còn Y/18 · đặt lại lúc 15:00." Hết lượt soạn bài thì nói rõ vẫn sửa,
duyệt, tự điền lời giải và xuất bản được.

## Hệ quả
- Ít bước tick hơn; câu tính được luôn có lời giải đúng mà không tốn lượt Gemini.
- Bản nháp cũ cần bấm "Tự điền lời giải" (hoặc "Lưu và soát lại") để nhận lời giải và sửa câu quãng kép.
- Không có migration.

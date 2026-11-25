# Mẫu huấn luyện nháp — cần người duyệt



16 mẫu gốc đề xuất, không phải dữ liệu đã duyệt. Train/dev/test = 12/2/2 chỉ để thử quy trình; không đủ đánh giá chất lượng. Chưa train hoặc tải model.



Các con số nhạc lý được engine kiểm tra trong phạm vi nhận diện được. Lời giải, độ phù hợp, quyền sử dụng vẫn cần người duyệt. Không tự đánh dấu reviewed_by_human/rights_cleared.



## Cách duyệt

Đọc câu hỏi, ngữ cảnh và câu trả lời. Ghi Giữ / Sửa / Loại cùng lý do. Xác nhận riêng nguồn và quyền sử dụng. Không cần tự viết JSON.



## context-001 — roman-major (train)

**Câu hỏi/đề:** Am trong C trưởng là bậc mấy?

**Ngữ cảnh UI:** `{}`

**Mức gợi ý:** 0

**Dữ kiện đầu vào:** `[{"tool": "get_roman_numeral", "args": {"key": "C", "chord": "Am", "mode": "major"}, "result": "vi"}]`

**Trả lời dự kiến:** Trong giọng C trưởng, Am là vi.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-002 — roman-natural (train)

**Câu hỏi/đề:** Hợp âm này là bậc mấy?

**Ngữ cảnh UI:** `{"selected_root": "A", "selected_chord": "Am", "selected_key": "A", "mode": "natural_minor"}`

**Mức gợi ý:** 0

**Dữ kiện đầu vào:** `[{"tool": "get_roman_numeral", "args": {"key": "A", "chord": "Am", "mode": "natural_minor"}, "result": "i"}]`

**Trả lời dự kiến:** Trong giọng A thứ tự nhiên, Am là i.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-003 — explicit-over-ui (train)

**Câu hỏi/đề:** Am trong C trưởng là bậc mấy?

**Ngữ cảnh UI:** `{"selected_root": "A", "selected_chord": "Am", "selected_key": "A", "mode": "natural_minor"}`

**Mức gợi ý:** 0

**Dữ kiện đầu vào:** `[{"tool": "get_roman_numeral", "args": {"key": "C", "chord": "Am", "mode": "major"}, "result": "vi"}]`

**Trả lời dự kiến:** Trong giọng C trưởng, Am là vi. Mình dùng giọng bạn nêu rõ trong câu hỏi, không dùng giọng đang chọn trên giao diện.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-004 — explicit-over-ui (train)

**Câu hỏi/đề:** Am trong A thứ tự nhiên là bậc mấy?

**Ngữ cảnh UI:** `{"selected_root": "A", "selected_chord": "Am", "selected_key": "C", "mode": "major"}`

**Mức gợi ý:** 0

**Dữ kiện đầu vào:** `[{"tool": "get_roman_numeral", "args": {"key": "A", "chord": "Am", "mode": "natural_minor"}, "result": "i"}]`

**Trả lời dự kiến:** Trong giọng A thứ tự nhiên, Am là i. Mình ưu tiên giọng bạn nêu rõ trong câu hỏi.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-005 — missing-context (train)

**Câu hỏi/đề:** Am trong A thứ là bậc mấy?

**Ngữ cảnh UI:** `{}`

**Mức gợi ý:** 0

**Dữ kiện đầu vào:** `[]`

**Trả lời dự kiến:** Bạn muốn xét A thứ tự nhiên, thứ hòa thanh hay thứ giai điệu? Mình cần làm rõ dạng giọng thứ trước khi phân tích.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-006 — missing-context (train)

**Câu hỏi/đề:** Hợp âm này là bậc mấy?

**Ngữ cảnh UI:** `{"selected_root": "A"}`

**Mức gợi ý:** 0

**Dữ kiện đầu vào:** `[]`

**Trả lời dự kiến:** Bạn đang chọn nốt gốc A, nhưng chưa xác định hợp âm và giọng. Bạn muốn xét hợp âm nào trong giọng nào?

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-007 — outside-selected-scale (train)

**Câu hỏi/đề:** E7 trong A thứ tự nhiên có sai nhạc lý không?

**Ngữ cảnh UI:** `{}`

**Mức gợi ý:** 0

**Dữ kiện đầu vào:** `[{"tool": "get_roman_numeral", "args": {"key": "A", "chord": "E7", "mode": "natural_minor"}, "error": {"code": "NOT_DIATONIC", "message": "E7 không thuộc giọng A thứ tự nhiên; hợp âm thuận giọng trên bậc 5 là Em7", "details": {"chord": "E7", "key": "A", "mode": "natural_minor", "expected": "Em7"}}}]`

**Trả lời dự kiến:** E7 nằm ngoài tập hợp âm thuận giọng A thứ tự nhiên mà engine đang xét. Điều đó không có nghĩa E7 sai nhạc lý; mình chưa gán số La Mã cho trường hợp này trong phạm vi hiện tại.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-008 — roman-natural (train)

**Câu hỏi/đề:** Bm7b5 trong A thứ tự nhiên là bậc mấy?

**Ngữ cảnh UI:** `{}`

**Mức gợi ý:** 0

**Dữ kiện đầu vào:** `[{"tool": "get_roman_numeral", "args": {"key": "A", "chord": "Bm7b5", "mode": "natural_minor"}, "result": "iiø7"}]`

**Trả lời dự kiến:** Trong giọng A thứ tự nhiên, Bm7b5 là iiø7.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-009 — roman-error-hints (train)

**Câu hỏi/đề:** Trong giọng C trưởng, Am7 mang số La Mã nào? Người học vừa nhập i7 và được chấm chưa đúng.

**Ngữ cảnh UI:** `{"selected_root": "A", "selected_chord": "Am", "selected_key": "A", "mode": "natural_minor"}`

**Mức gợi ý:** 1

**Dữ kiện đầu vào:** `[{"tool": "get_roman_numeral", "args": {"key": "C", "chord": "Am7", "mode": "major"}, "result": "vi7"}]`

**Trả lời dự kiến:** Hãy đọc lại giọng mà đề bài yêu cầu trước khi phân tích. Giọng đang chọn trong chatbot không thay đổi giọng của bài tập.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-010 — roman-error-hints (train)

**Câu hỏi/đề:** Trong giọng C trưởng, Am7 mang số La Mã nào? Người học vừa nhập i7 và được chấm chưa đúng.

**Ngữ cảnh UI:** `{"selected_root": "A", "selected_chord": "Am", "selected_key": "A", "mode": "natural_minor"}`

**Mức gợi ý:** 2

**Dữ kiện đầu vào:** `[{"tool": "get_roman_numeral", "args": {"key": "C", "chord": "Am7", "mode": "major"}, "result": "vi7"}]`

**Trả lời dự kiến:** Bạn hãy xác định vị trí nốt gốc của hợp âm trong giọng đề bài, rồi kiểm tra ký hiệu cho hợp âm bảy. Chưa cần đổi lựa chọn trong chatbot.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-011 — roman-error-hints (train)

**Câu hỏi/đề:** Trong giọng C trưởng, Am7 mang số La Mã nào? Người học vừa nhập i7 và được chấm chưa đúng.

**Ngữ cảnh UI:** `{"selected_root": "A", "selected_chord": "Am", "selected_key": "A", "mode": "natural_minor"}`

**Mức gợi ý:** 3

**Dữ kiện đầu vào:** `[{"tool": "get_roman_numeral", "args": {"key": "C", "chord": "Am7", "mode": "major"}, "result": "vi7"}]`

**Trả lời dự kiến:** Trong giọng C trưởng, Am7 là vi7. Mình chấm theo giọng C trưởng của đề bài, không theo giọng đang chọn trong chatbot.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-012 — roman-major (train)

**Câu hỏi/đề:** Dm trong C trưởng là bậc mấy?

**Ngữ cảnh UI:** `{}`

**Mức gợi ý:** 0

**Dữ kiện đầu vào:** `[{"tool": "get_roman_numeral", "args": {"key": "C", "chord": "Dm", "mode": "major"}, "result": "ii"}]`

**Trả lời dự kiến:** Trong giọng C trưởng, Dm là ii.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-013 — seventh-alias (dev)

**Câu hỏi/đề:** Cmaj7 trong A thứ tự nhiên là bậc mấy?

**Ngữ cảnh UI:** `{}`

**Mức gợi ý:** 0

**Dữ kiện đầu vào:** `[{"tool": "get_roman_numeral", "args": {"key": "A", "chord": "Cmaj7", "mode": "natural_minor"}, "result": "IIIM7"}]`

**Trả lời dự kiến:** Trong giọng A thứ tự nhiên, Cmaj7 là IIImaj7.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-014 — seventh-alias (dev)

**Câu hỏi/đề:** Fmaj7 trong A thứ tự nhiên là bậc mấy?

**Ngữ cảnh UI:** `{}`

**Mức gợi ý:** 0

**Dữ kiện đầu vào:** `[{"tool": "get_roman_numeral", "args": {"key": "A", "chord": "Fmaj7", "mode": "natural_minor"}, "result": "VIM7"}]`

**Trả lời dự kiến:** Trong giọng A thứ tự nhiên, Fmaj7 là VImaj7.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-015 — missing-evidence (test)

**Câu hỏi/đề:** Hãy giải thích cấu trúc fugue theo bài học của mình.

**Ngữ cảnh UI:** `{}`

**Mức gợi ý:** 0

**Dữ kiện đầu vào:** `[]`

**Trả lời dự kiến:** Mình chưa có đoạn học liệu về fugue trong ngữ cảnh hiện tại, nên chưa thể giải thích dựa trên khóa học. Bạn có thể cung cấp đoạn tài liệu cần học không?

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …



## context-016 — missing-evidence (test)

**Câu hỏi/đề:** Bài học nói gì về hòa âm tứ độ?

**Ngữ cảnh UI:** `{}`

**Mức gợi ý:** 0

**Dữ kiện đầu vào:** `[]`

**Trả lời dự kiến:** Ngữ cảnh hiện tại chưa có đoạn bài học về hòa âm tứ độ. Mình không suy đoán nội dung bài học khi thiếu tài liệu.

- [ ] Nội dung đúng và trả lời đúng câu hỏi

- [ ] Mức gợi ý phù hợp; không lộ đáp án sớm

- [ ] Nguồn và quyền sử dụng được xác nhận

**Quyết định / sửa đề nghị:** …

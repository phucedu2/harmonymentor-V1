# ADR-020 · AI Tutor trả lời mọi câu âm nhạc; câu ngoài âm nhạc thì từ chối

Trạng thái: **Có hiệu lực 12/11/2026**, Phúc chốt (6 câu đều A). Thắng cần đọc vì đổi một điều ADR-017 đã đặt. Nhánh `ai/tutor-tra-loi-moi-cau-nhac`.

## Bối cảnh

ADR-017 (góp ý thầy G1) đặt luồng B "ngoài bài học": Music Engine tính được thì trả dữ kiện Engine, không thì "không biết", **không gọi LLM**, để tránh AI bịa. Hệ quả: người học hỏi "alt chord là gì", "Jazz ra đời khi nào" hay "guitar tập thế nào" chỉ nhận "không biết" hoặc bị từ chối, trong khi sản phẩm là trợ lý âm nhạc. Phúc yêu cầu: mọi câu liên quan nhạc lý, hòa âm, âm nhạc nói chung đều trả lời được; chưa có trong bài thì nói "chưa có trong bài học" nhưng vẫn trả lời; câu không liên quan âm nhạc thì nói không biết.

## Quyết định

1. **Luồng B gọi Gemini** (không có đoạn bài học, không trích dẫn). Nhãn nhỏ: "Chưa có trong bài học, đây là kiến thức chung". Nếu bài chưa mở thì thêm dòng "Bạn sẽ học nội dung này ở bài …"; nếu có bài gần nhất thì gợi ý mở bài.
2. **Music Engine vẫn là nguồn sự thật về nốt** (nguyên tắc 1). Prompt chung cấm liệt kê nốt của hợp âm/âm giai mà ENGINE_FACTS không có; máy chủ quét lại câu trả lời (guardrail cũ). Nốt sai thì soạn lại 1 lần; vẫn sai thì bỏ nguyên câu AI và trả dữ kiện Engine viết sẵn (hoặc "chưa trả lời được lúc này"). Ký hiệu Engine chưa hiểu (C11, 7#9, alt) thì không có nhãn "Đã kiểm bằng Music Engine".
3. **Phạm vi âm nhạc rộng**: nhạc lý, hòa âm, nhạc cụ và cách tập, thể loại, lịch sử, sáng tác. Bộ lọc tất định `general.py` (từ khóa không dấu) ngăn tầng 1 từ chối nhầm câu về nhạc cụ, thể loại. Vẫn từ chối: lời bài hát có bản quyền, tải lậu, mua bán, tấn công prompt. Câu hỏi cách dùng web (có từ như "trang", "lưu", "xuất") vẫn đi luồng D.
4. **Chốt thứ hai**: nếu Gemini thấy câu không phải âm nhạc, nó trả intent `out_of_scope`; dịch vụ thay bằng câu từ chối viết sẵn, không tin chữ AI viết.
5. **Câu ngoài âm nhạc (luồng C)**: "Mình chỉ là trợ lý âm nhạc nên câu này mình không biết", kèm gợi ý hỏi nhạc lý.
6. **Khi AI không gọi được** (khóa hỏng, hết lượt, mất mạng): luồng B dùng dữ kiện Engine nếu tính được; không thì "chưa trả lời được lúc này, bạn thử lại sau" (không còn nói "không biết", vì thật ra AI đang lỗi) kèm bài gần nhất. `AI_ENABLED=false` vẫn demo được (nguyên tắc 3).
7. **Hạn mức**: câu luồng B giờ tính vào hạn mức mỗi người mỗi ngày (`AI_DAILY_QUOTA`) và ngân sách chung như luồng A; quá hạn mức người dùng thì 429, quá ngân sách chung thì dùng câu viết sẵn.

8. **Luồng A, AI tự nói không biết**: nếu kho có đoạn "giống chữ" nhưng AI trả lời không trích được đoạn nào và tự nói "không biết / chưa dạy" (ví dụ "piano có bao nhiêu phím"), dịch vụ hỏi lại theo kiến thức chung như luồng B (thêm một lượt gọi). Lỗi hoặc hết hạn mức thì giữ câu cũ.

## Không đổi

Luồng A (trong bài, có trích dẫn), D (hướng dẫn), G (chào hỏi), ngưỡng định tuyến và dữ liệu huấn luyện. Chuỗi canh gác, kiểm tấn công prompt, không gửi dữ liệu cá nhân cho Gemini.

## Rủi ro

- **AI bịa ở phần ngoài nốt** (năm, tên người, lịch sử): Engine không kiểm được. Giảm bằng nhãn "kiến thức chung", prompt dặn "không chắc thì nói không chắc", và Đạt/Thắng thử các câu lịch sử, nhạc cụ trước khi demo. Đây là điều ADR-017 từng tránh, nên cần Thắng chấp nhận.
- Lượt gọi Gemini tăng (gói miễn phí hay 429/503): đã có đường dự phòng ở mục 6.
- Từ khóa rộng có thể cho câu ngoài lề lọt vào luồng B (ví dụ "pop" trong câu khác); chốt thứ hai của Gemini xử lý, nhưng tốn một lượt gọi.

## Kiểm chứng

`backend/tests/test_ai_gd1_router.py`: 8 test luồng B mới (FakeProvider, không gọi mạng): có Engine kiểm, nốt sai không tới người dùng, bài chưa mở, câu chưa có bài, câu nhạc cụ không bị từ chối, Gemini nói ngoài âm nhạc, AI lỗi, AI tắt; 10 test lọc phạm vi. Số đo định tuyến (tập GĐ1 74 câu) giữ nguyên: B/C bị trả lời như bài 3,5%, A bị từ chối sai 2,7%.

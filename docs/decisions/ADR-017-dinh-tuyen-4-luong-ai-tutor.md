# ADR-017 · AI Tutor định tuyến 4 luồng, nhúng e5-small cục bộ

Trạng thái: **Đề xuất 06/11/2026**, chờ nhóm duyệt qua Draft PR GĐ1 (nhánh `ai-gop-y/gd1-dinh-tuyen`). Căn cứ: góp ý thầy G1/G3/G4, 17 câu làm rõ Phúc trả lời "A" cả 17 (06/11/2026), báo cáo GĐ0 `docs/giai-doan/ai-gop-y/00_KIEM_KE_RAG.md`.

## Bối cảnh

GĐ0 đo hệ thống đang chạy trên `phuc-music` (7c9408f):

- Không có khóa Gemini thì truy xuất chạy BM25. R@1 chỉ 51,4%, và bài C7/Cmaj7 bị trích nhầm L03-B07.
- Câu ngoài bài học vẫn được đưa cho LLM, ví dụ Csus4 hay modal interchange. Bộ lọc injection chặn nhầm câu "đổi mật khẩu".
- Thầy yêu cầu hai điều: câu nằm trong bài thì trả lời qua RAG có trích dẫn; câu không liên quan thì nói "không biết", không đoán.
- Tài liệu 2.1 chọn MiniLM để nhúng. MiniLM chỉ đọc được 128 token, trong khi 21 trên 45 đoạn của kho dài hơn mức đó, nên R@1 đo được chỉ 45,7%. Với e5-small, R@1 là 85,7%.

## Quyết định

1. **Bốn luồng cộng chào hỏi.**

   | Luồng | Khi nào | Trả lời thế nào | Gọi LLM? |
   |---|---|---|---|
   | A "trong bài học" | Kho có đoạn dạy nội dung câu hỏi | RAG, kèm trích dẫn và guardrail Music Engine | Có |
   | B "ngoài bài học" | Câu nhạc lý mà bài chưa dạy | Engine tính được thì trả lời bằng khuôn viết sẵn, nhãn "Ngoài bài học, theo Music Engine" (kèm "chưa đối chiếu giáo trình" khi verified=false). Engine không tính được thì nói "không biết" và gợi ý bài gần nhất. Khái niệm của bài L05–L08 chưa vào kho thì gắn nhãn "Bạn sẽ học sau" và chỉ đúng bài đó (quyết định 5A, 6A, 8A). | Không |
   | C "ngoài phạm vi" | Câu không liên quan | Từ chối lịch sự | Không |
   | D "hướng dẫn sử dụng" | Câu hỏi cách dùng app | Tra kho hướng dẫn `app/content/help/help_entries.json` (18 mục, bản nháp chờ Phúc duyệt theo quyết định 10A), kèm nút mở trang | Không |
   | G "chào hỏi" | Lời chào, cảm ơn | Câu ngắn | Không |

2. **Hai tầng.**
   - Tầng 1 (`route_classifier.py`): dùng TF-IDF trên n-gram ký tự kết hợp LogisticRegression, chia 4 nhãn: nhac_ly, huong_dan, chao_hoi, ngoai_pham_vi. Mỗi nhãn có ít nhất 60 câu train. Nhãn này **không** quyết định A hay B.
   - Tầng 2: điểm truy xuất trên kho bài và kho hướng dẫn, cộng thêm dữ kiện Music Engine (`engine_query.py`).
   - Hàm `route()` thuần, chỉ so điểm với ngưỡng, nên script dò lưới chạy nhanh.

3. **Các luật tất định xét trước ngưỡng.** Mọi luật đều lấy từ dữ liệu, không ghi danh sách tay.
   - *Phủ kiến thức:* câu hỏi về loại hợp âm hoặc âm giai mà không đoạn nào trong kho nhắc tới (ví dụ sus4, thứ hòa âm) thì đi luồng B. Lý do: đoạn tìm được chỉ giống chữ, không dạy điều đó.
   - *Bài sau:* từ khóa lấy từ tiêu đề bài L05–L08. Luật tự tắt khi bài đó vào kho.
   - *Thuật ngữ lạ:* từ ngoại (không thể là âm tiết tiếng Việt) mà kho bài, kho hướng dẫn và câu train thường ngày đều không có, ví dụ "pentatonic" hay "fugue", thì đi luồng B. Từ tiếng Việt lạ không tính, vì vốn từ thường ngày còn nhỏ nên tính vào sẽ chặn nhầm câu A ("Câu cuối…").
   - *Vùng xám nghiêng về "không biết":* có dữ kiện Engine thuộc loại kho đã dạy và có đoạn ở vùng xám thì trả lời ở luồng A kèm Engine. Không có thì nói "không biết".

4. **Ngưỡng do script chọn, không chọn tay.**
   - Script `scripts/ai/gop_y/hieu_chinh_nguong.py` dò lưới trên tập dev và ghi kết quả vào `router_thresholds.json`, kèm tên tập và số đo.
   - Mục tiêu: câu B/C bị trả lời như bài học ≤ 2%, câu A bị từ chối sai ≤ 5%. Nếu không bộ ngưỡng nào đạt cả hai, script coi lỗi "trả lời sai" nặng gấp đôi lỗi "từ chối sai".
   - Khi có tập dev 30 câu của Phúc, chạy lại script với `--dev`.

5. **Nhúng e5-small cục bộ** (quyết định 2A, 4A).
   - Mô hình `intfloat/multilingual-e5-small`, cố định bản 614241f, kiểm SHA-256. Chạy bằng onnxruntime trên CPU, không cần torch, đọc tối đa 512 token.
   - Đây là mặc định của AI Tutor (`TUTOR_EMBEDDER=local`), chạy được cả khi `AI_ENABLED=false` (nguyên tắc 3).
   - Thiếu file mô hình thì tự lùi về BM25.
   - Mô hình không nằm trong git: Dockerfile tải ở một lớp riêng, CI tải rồi lưu cache.
   - Gợi ý bài học (GĐ2) vẫn dùng Gemini, theo ADR-014.

6. **System prompt viết lại** theo thứ tự: vai trò, phạm vi, luật, chế độ, định dạng, 5 ví dụ.
   - Các ví dụ dùng block_id thật và nốt đã kiểm bằng Engine; test so ví dụ với kho và Engine.
   - LLM trả lời mà không trích được đoạn nào thì gắn nhãn "Chưa có trích dẫn bài học", không gắn "Từ bài học".

7. **Bộ lọc injection.**
   - Chỉ chặn "mật khẩu/token" khi câu đòi xem hoặc lấy, hoặc khi nói về mật khẩu của hệ thống hay người khác.
   - Bỏ hai chỗ chặn nhầm "đóng vai trò" và "C# hay là Db".
   - Thêm "luật lệ" và "in lại" để bắt 2 câu tấn công trước đây lọt qua.

## Phương án đã cân nhắc

- **Giữ MiniLM như tài liệu 2.1.** Không chọn vì R@1 45,7%, thua cả BM25.
- **Gemini embedding làm mặc định.** Không chọn vì cần khóa (điều khoản Google yêu cầu người tạo khóa đủ điều kiện độ tuổi, nhóm chưa có khóa hợp lệ) và không chạy được khi AI tắt. Vẫn bật được bằng `TUTOR_EMBEDDER=gemini`.
- **Chỉ dùng một ngưỡng điểm.** Không đủ: điểm cosine của e5 bị nén, câu A và câu B đều quanh 0,83–0,86 (GĐ0). Phải thêm luật phủ kiến thức và luật thuật ngữ lạ.
- **Để LLM tự quyết "trong bài hay không".** Không chọn vì tốn lượt gọi, không tất định, và chính là lỗi thầy đã chỉ ra.

## Hệ quả

- Câu B/C/D/G không gọi LLM, nên tiết kiệm hạn mức và trả lời nhanh.
- Bản ghi `chat_messages.tool_calls` lưu `router` (luồng, lý do, điểm) để truy vết.
- API `/chat/message` có thêm các trường: `flow`, `source_label`, `suggested_lesson`, `help_page`, và intent mới `greeting` / `help`. Các trường đều tùy chọn nên client cũ không hỏng.
- Ảnh Docker lớn thêm khoảng 470 MB. Lần build đầu phải tải từ huggingface.co: Avast trên máy Phúc cần tắt "HTTPS scanning". Không tải được thì build vẫn chạy tiếp và dùng BM25.
- Số đo hiện chỉ trên câu Claude soạn. Số chính thức lấy trên tập test khóa của Đạt (40 câu) và Thắng (30 câu), theo quyết định 11A.

## Kiểm chứng

`backend/tests/test_ai_gd1_router.py` gồm:

- Tra Engine.
- Tầng 1 trên tập dev.
- Các luật.
- Quyết định luồng với BM25.
- Ngưỡng do script ghi.
- Kho hướng dẫn trỏ đúng route.
- Bộ lọc injection.
- Ví dụ trong prompt khớp kho và Engine.
- Không trùng câu giữa các tập.
- e5 khi có mô hình.
- API cho từng luồng: luồng B/C/D/G không gọi LLM.

Báo cáo và số đo nằm ở `docs/giai-doan/ai-gop-y/01_DINH_TUYEN.md`.

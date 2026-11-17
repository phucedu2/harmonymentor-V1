# Báo cáo Code Review — BookStore Pro

| Mục | Nội dung |
| --- | --- |
| Phạm vi | Toàn bộ `backend/app`, `frontend/src`, `run.py`, `docker-compose.yml`, `k8s/`, dữ liệu seed |
| Ngày review | 13/11/2026 |
| Commit | `92c681f` (nhánh hiện tại) |
| Phương pháp | Đọc mã nguồn tĩnh, đối chiếu luồng nghiệp vụ, kiểm tra cấu hình và các file được Git theo dõi |
| Giới hạn | Bộ test chưa được chạy trong lần review này vì môi trường máy review chưa cài dependency (`pwdlib` thiếu). Các nhận định về hành vi runtime được suy ra từ mã nguồn. |

Tài liệu liên quan: [Đặc tả nghiệp vụ hệ thống](ba-business-requirements.md) · [Đặc tả tính năng AI Chatbot & RAG](ba-ai-chatbot-rag-requirements.md)

---

## 1. Kết luận nhanh

BookStore Pro có kiến trúc phân lớp rõ ràng (models → schemas → crud → endpoints → services), validate đầu vào tốt bằng Pydantic, có máy trạng thái đơn hàng, khóa dòng khi trừ kho, và một chatbot đã được "neo" vào dữ liệu catalog thật với cơ chế dự phòng cục bộ. Đây là nền tảng tốt cho đồ án.

Các vấn đề cần xử lý trước khi demo công khai hoặc triển khai thật, theo thứ tự ưu tiên:

1. **Bí mật và dữ liệu bị đưa vào Git** (`.env`, `backend/dev.db`, log, 44 file `__pycache__`), repo không có `.gitignore`.
2. **Endpoint `/api/v1/ai/chat` công khai, không giới hạn tần suất**, trong khi nó tiêu hao API key Gemini của quản trị viên.
3. **Xóa sách đã có trong đơn hàng** trả lỗi 500 trên PostgreSQL và để lại dữ liệu mồ côi trên SQLite.
4. **API `/books-async` không chạy ở chế độ `--sqlite`** vì URL không dùng driver async.
5. **Phân tích cảm xúc chỉ hiểu tiếng Anh** và dữ liệu đánh giá mẫu nói về tiểu thuyết, không khớp catalog sách công nghệ.

---

## 2. Điểm mạnh

| # | Điểm mạnh | Bằng chứng |
| --- | --- | --- |
| S1 | Phân lớp rõ, dễ dạy và dễ mở rộng | `app/models`, `app/schemas`, `app/crud`, `app/api/v1/endpoints`, `app/services` |
| S2 | Mật khẩu băm bằng Argon2 (pwdlib), `SECRET_KEY` bắt buộc ≥ 32 ký tự | [security.py](../backend/app/core/security.py), [config.py](../backend/app/core/config.py) |
| S3 | Đặt hàng có khóa dòng `with_for_update()` và kiểm tra tồn kho trước khi trừ | [crud/order.py:19-59](../backend/app/crud/order.py#L19-L59) |
| S4 | Máy trạng thái đơn hàng tường minh, hủy đơn tự hoàn kho | [crud/order.py:10-16](../backend/app/crud/order.py#L10-L16), [crud/order.py:93-108](../backend/app/crud/order.py#L93-L108) |
| S5 | Chặn tự hạ quyền admin và chặn hạ quyền admin cuối cùng | [endpoints/admin.py](../backend/app/api/v1/endpoints/admin.py) |
| S6 | API key AI được mã hóa Fernet, chỉ trả về `key_hint` dạng `abc...wxyz` | [crud/ai_key.py](../backend/app/crud/ai_key.py), [ai_providers.py](../backend/app/core/ai_providers.py) |
| S7 | Chatbot LLM chỉ được chọn sách trong danh sách ứng viên; `book_ids` lạ bị loại bỏ, chống "bịa" sách | [llm_chat.py:67-86](../backend/app/services/llm_chat.py#L67-L86) |
| S8 | LLM lỗi (key sai, hết quota, mất mạng) thì tự quay về gợi ý cục bộ và báo `notice` | [endpoints/ai.py:51-101](../backend/app/api/v1/endpoints/ai.py#L51-L101) |
| S9 | Ràng buộc toàn vẹn ở tầng database (CHECK giá/tồn kho/trạng thái/rating) | `models/*.py` |
| S10 | Đơn hàng lưu snapshot `title` và `unit_price`, đổi giá sách sau không làm sai lịch sử | [models/order.py](../backend/app/models/order.py) |

---

## 3. Danh sách phát hiện

Mức độ: **Cao** = rủi ro bảo mật, mất dữ liệu hoặc chức năng hỏng; **Trung bình** = sai nghiệp vụ hoặc khó vận hành; **Thấp** = chất lượng mã, khả năng mở rộng.

### 3.1 Mức Cao

| ID | Vấn đề | Vị trí | Tác động | Đề xuất |
| --- | --- | --- | --- | --- |
| CR-01 | `.env`, `backend/dev.db`, `server.*.log` và 44 file `__pycache__` được Git theo dõi; repo không có `.gitignore` | Gốc repo | `dev.db` chứa hash mật khẩu và API key đã mã hóa. Nếu `.env` chứa `SECRET_KEY` thật thì ai có repo đều giải mã được key Gemini (khóa Fernet được dẫn xuất từ `SECRET_KEY`) và giả mạo JWT của admin | Thêm `.gitignore`; `git rm --cached` các file trên; **thay `SECRET_KEY`** và **thu hồi/tạo lại mọi API key Gemini** đã từng lưu; cân nhắc làm sạch lịch sử Git nếu repo đã public |
| CR-02 | `/ai/chat` cho phép khách vãng lai gọi không giới hạn | [endpoints/ai.py:51](../backend/app/api/v1/endpoints/ai.py#L51) | Bất kỳ ai cũng có thể đốt quota/chi phí key Gemini của admin (lạm dụng chi phí) | Rate limit theo IP và theo user (ví dụ 20 tin/10 phút cho khách, 60 cho thành viên), hạn mức token/ngày, ghi log usage |
| CR-03 | Xóa sách đã nằm trong `order_items` | [crud/book.py:161](../backend/app/crud/book.py#L161), [models/order.py:78](../backend/app/models/order.py#L78) | PostgreSQL: `IntegrityError` không được bắt → HTTP 500. SQLite: mặc định không bật khóa ngoại → xóa được, để lại `order_items` trỏ tới sách không tồn tại | Bắt lỗi và trả 409 kèm thông báo; thay "xóa cứng" bằng "ngừng kinh doanh" (`is_active=false`); bật `PRAGMA foreign_keys=ON` cho SQLite |
| CR-04 | Tài khoản admin mặc định `admin-password-123` được seed khi `SEED_ADMIN=true` (mặc định) | [config.py:23-25](../backend/app/core/config.py#L23-L25) | Triển khai quên đổi cấu hình là lộ quyền quản trị | Mặc định `seed_admin=False` ngoài môi trường dev, hoặc từ chối khởi động khi mật khẩu admin trùng giá trị mặc định ở môi trường production |

### 3.2 Mức Trung bình

| ID | Vấn đề | Vị trí | Tác động | Đề xuất |
| --- | --- | --- | --- | --- |
| CR-05 | `/books-async` dùng `create_async_engine` với URL `sqlite:///./dev.db` (driver đồng bộ) | [session_async.py:16](../backend/app/db/session_async.py#L16), [run.py:147](../run.py#L147) | Mọi request tới `/api/v1/books-async/*` lỗi khi chạy `python run.py --sqlite` | Tự chuyển `sqlite://` → `sqlite+aiosqlite://` cho engine async (đã có `aiosqlite` trong requirements) |
| CR-06 | Phân tích cảm xúc dùng từ điển tiếng Anh, từ vựng hướng tiểu thuyết ("gripping", "page-turner") | [sentiment.py:5](../backend/app/services/sentiment.py#L5) | Đánh giá tiếng Việt gần như luôn "neutral" (chỉ lệch theo số sao); dashboard từ khóa sai lệch | Thay bằng mô hình đa ngôn ngữ (xem AI-05 trong tài liệu AI) |
| CR-07 | Dữ liệu đánh giá mẫu nói về cốt truyện/nhân vật, trong khi catalog là sách lập trình/AI | [init_db.py:28](../backend/app/db/init_db.py#L28) | Demo thiếu thuyết phục; chatbot RAG dùng review sẽ nhận ngữ cảnh sai | Viết lại bộ review mẫu theo chủ đề kỹ thuật, có cả tiếng Việt |
| CR-08 | Không kiểm tra "đã mua mới được đánh giá", không giới hạn số review mỗi người/sách, không có API xóa/ẩn review | [endpoints/reviews.py:34](../backend/app/api/v1/endpoints/reviews.py#L34) | Dễ spam, thao túng điểm trung bình | Ràng buộc UNIQUE(`user_id`,`book_id`), gắn nhãn "Đã mua hàng", thêm chức năng kiểm duyệt cho admin |
| CR-09 | Trừ kho ngay khi đơn ở trạng thái `pending`, không có hạn thanh toán; khách không tự hủy được đơn | [crud/order.py:45](../backend/app/crud/order.py#L45) | Đơn treo giữ hàng vô thời hạn | Thêm hạn giữ hàng (ví dụ 24 giờ) và job tự hủy; cho khách hủy đơn `pending` |
| CR-10 | Doanh thu tính cả đơn `pending` | [crud/analytics.py:22](../backend/app/crud/analytics.py#L22) | KPI doanh thu bị thổi phồng | Tách "doanh thu ghi nhận" (paid/shipped/completed) và "giá trị đơn chờ" |
| CR-11 | Mỗi tin nhắn chat gọi `answer_chat` tối đa 3 lần + `build_recommendations`, mỗi lần quét toàn bộ sách còn hàng và tổng hợp lại độ phổ biến | [endpoints/ai.py:56-77](../backend/app/api/v1/endpoints/ai.py#L56-L77), [recommender.py:123](../backend/app/services/recommender.py#L123) | 5–8 truy vấn quét bảng mỗi tin nhắn; ổn với 300 sách nhưng không mở rộng | Cache `book_popularity` và `category_names` theo TTL; thay retrieval bằng vector search (RAG) |
| CR-12 | Kiểm tra API key chỉ kiểm tra định dạng; `key_prefix=""` nên phép kiểm tra tiền tố luôn đúng | [ai_providers.py:17](../backend/app/core/ai_providers.py#L17), [ai_verify.py:20](../backend/app/services/ai_verify.py#L20) | Admin tưởng key hợp lệ nhưng thực tế bị từ chối khi chat | Thêm "kiểm tra trực tiếp" bằng một lời gọi rẻ (liệt kê model) với timeout ngắn |
| CR-13 | Khóa mã hóa Fernet dẫn xuất từ `SECRET_KEY` (dùng chung với JWT) | [security.py:24](../backend/app/core/security.py#L24) | Xoay vòng `SECRET_KEY` để thu hồi JWT sẽ làm mọi API key đã lưu không giải mã được | Tách biến `AI_KEYS_ENCRYPTION_KEY`; hỗ trợ `MultiFernet` để xoay khóa |
| CR-14 | Không có migration (Alembic); schema được vá bằng `ALTER TABLE` thủ công lúc khởi động | [init_db.py:201](../backend/app/db/init_db.py#L201) | Khó nâng cấp schema khi thêm bảng AI (vector, chat log) | Đưa Alembic vào trước khi làm tính năng AI |

### 3.3 Mức Thấp

| ID | Vấn đề | Vị trí | Đề xuất |
| --- | --- | --- | --- |
| CR-15 | JWT lưu trong `localStorage`, hết hạn sau 30 phút, không có refresh token | [frontend/src/api.js:2](../frontend/src/api.js#L2) | Chấp nhận được cho đồ án; nếu triển khai thật cân nhắc cookie `HttpOnly` + refresh token |
| CR-16 | Khi chưa build `frontend/dist`, FastAPI mount toàn bộ thư mục `frontend/` tại `/` | [main.py:44](../backend/app/main.py#L44) | Lộ mã nguồn `src/`, `package.json`; chỉ mount thư mục tĩnh cần thiết |
| CR-17 | API sách sync và async trùng lặp logic (`books.py` và `books_async.py`) | `endpoints/books*.py` | Giữ nếu mục đích là so sánh khi giảng dạy, ghi rõ trong tài liệu; nếu không thì gộp |
| CR-18 | `build_overview` nạp toàn bộ orders/books/users vào bộ nhớ | [crud/analytics.py:55-58](../backend/app/crud/analytics.py#L55-L58) | Chuyển sang truy vấn GROUP BY khi dữ liệu lớn |
| CR-19 | Test chỉ có 6 ca cho xác thực/phân quyền; không có test cho đơn hàng, kho, review, AI | [test/test_auth.py](../backend/test/test_auth.py) | Bổ sung test cho máy trạng thái đơn hàng, trừ/hoàn kho, fallback chatbot, chặn `book_id` lạ |
| CR-20 | Endpoint `/admin/orders` không trả tổng số bản ghi để phân trang | [endpoints/admin.py](../backend/app/api/v1/endpoints/admin.py) | Trả về `{total, items}` như `/books` |
| CR-21 | `powerbi/documentation.md` rỗng; README mô tả cấu trúc `Eproject2/` cũ | `powerbi/`, `README.md` | Cập nhật hoặc xóa |
| CR-22 | Giá niêm yết bằng USD trong khi giao diện/đối tượng là người Việt | `books_catalog.json` | Quyết định nghiệp vụ: giữ USD hay chuyển VND (xem câu hỏi mở trong BA) |

---

## 4. Đánh giá riêng phần AI hiện có

| Thành phần | Cách làm hiện tại | Nhận xét |
| --- | --- | --- |
| Chatbot cục bộ | Luật + từ khóa (`TOPIC_KEYWORDS`), nhận diện mức độ (beginner/advanced) và ngân sách bằng regex | Chạy không cần mạng, phản hồi nhanh; chỉ hiểu tiếng Anh, không hiểu đồng nghĩa hay câu phức |
| Chatbot LLM | Gemini qua endpoint tương thích OpenAI, gửi ≤ 16 sách ứng viên trong system prompt, yêu cầu JSON | Là dạng "RAG thô" (retrieval bằng từ khóa). Không streaming, không lưu hội thoại phía server, không đo lường chất lượng |
| Gợi ý sách | Danh mục mua nhiều nhất của user + độ phổ biến toàn shop | Heuristic hợp lý; chưa có "sách tương tự" hay lọc cộng tác |
| Cảm xúc review | Từ điển + phủ định + từ nhấn mạnh | Xem CR-06 |
| Quản lý key | Mã hóa, kích hoạt một key duy nhất, chỉ provider Gemini | Xem CR-12, CR-13; chưa có lớp trừu tượng cho nhiều provider |

Hướng nâng cấp chi tiết nằm trong [ba-ai-chatbot-rag-requirements.md](ba-ai-chatbot-rag-requirements.md).

---

## 5. Kế hoạch khắc phục đề xuất

| Đợt | Việc | Phát hiện liên quan |
| --- | --- | --- |
| Ngay lập tức | `.gitignore`, gỡ file nhạy cảm khỏi Git, thay `SECRET_KEY`, tạo lại API key | CR-01 |
| Sprint 1 | Rate limit chat, xử lý xóa sách, tắt seed admin ở production, sửa engine async SQLite | CR-02, CR-03, CR-04, CR-05 |
| Sprint 2 | Alembic, tách khóa mã hóa, hạn giữ hàng, ràng buộc review, sửa KPI doanh thu | CR-08, CR-09, CR-10, CR-13, CR-14 |
| Song song với AI | Thay sentiment, viết lại review mẫu, bổ sung test | CR-06, CR-07, CR-19 |

## 6. Câu hỏi còn mở

- `.env` hiện được commit có chứa `SECRET_KEY` thật hay chỉ là giá trị dev? (Lần review này không đọc nội dung `.env`.) Nếu là giá trị thật thì bắt buộc phải xoay khóa.
- Repo này đã từng được đẩy lên kho public chưa? Nếu có, cần làm sạch lịch sử Git chứ không chỉ gỡ file.
- `books_async.py` được giữ lại với mục đích giảng dạy (so sánh sync/async) hay là mã thừa?

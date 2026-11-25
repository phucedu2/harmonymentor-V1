# HarmonyMentor — Báo cáo rà soát bước tiếp theo

**Ngày:** 2026-11-23  
**Phạm vi:** 8 mẫu train cũ + 4 mẫu dev/test cũ, đối chiếu với HM6-01–04 đã được người dùng duyệt.  
**Mục tiêu:** rà nội dung, kiểm tra nhóm câu gần nhau, provenance hiện có, schema, Music Engine và tokenizer. Không chạy full training.

## Kết quả tổng quan

- Bộ cũ được rà: **12 mẫu** = 8 train, 2 dev, 2 test.
- Gộp với HM6-01–04: **16 mẫu** = 12 train, 2 dev, 2 test.
- Schema ở chế độ kiểm tra kỹ thuật: đạt.
- Music Engine: đạt trên các claim định lượng có trong 16 mẫu.
- Tokenizer offline: tất cả mẫu trong giới hạn 1.024 token.
- Không chỉnh sửa nội dung nguồn cũ và không tự đánh dấu quyền sử dụng cho 12 mẫu cũ.

## Phân loại nội dung

### Có thể giữ về mặt nội dung/kỹ thuật

- `context-001`: Am trong C trưởng → vi.
- `context-002`: Am trong A thứ tự nhiên → i.
- `context-004`: Am trong A thứ tự nhiên, ưu tiên câu hỏi rõ hơn UI → i.
- `context-005`: thiếu dạng giọng thứ → hỏi làm rõ.
- `context-007`: E7 ngoài tập hợp thuận giọng A thứ tự nhiên, không kết luận là sai nhạc lý.
- `context-008`: Bm7b5 trong A thứ tự nhiên → iiø7.
- `context-010`: gợi ý sửa lỗi khi người học nhập i7 cho Am7.
- `context-012`: Dm trong C trưởng → ii.
- `context-013`: Cmaj7 trong A thứ tự nhiên → IIImaj7.
- `context-014`: Fmaj7 trong A thứ tự nhiên → VImaj7.
- `context-015`: không bịa nội dung khi thiếu học liệu về fugue.
- `context-016`: không bịa nội dung khi thiếu học liệu về hòa âm tứ độ.

Các kết luận nhạc lý/engine đã được kiểm tra lại trong môi trường offline. Đây là kết luận kỹ thuật và nội dung sơ bộ, không thay cho xác nhận quyền sử dụng.

## Xử lý các cặp gần nhau

| Cặp | Nhận định | Đề xuất |
|---|---|---|
| `context-001` / `context-012` | Cùng kỹ năng roman-major nhưng khác hợp âm: Am → vi và Dm → ii. Không phải trùng câu; là hai ví dụ khác nhau. | Giữ cả hai trong train nếu muốn tăng phủ bậc hợp âm; có thể đổi group_id thành các nhóm khái niệm riêng nếu cần phân tích theo từng ví dụ. |
| `context-004` / `context-008` | Cùng dạng “hợp âm trong giọng thứ” nhưng khác hợp âm, khác mục tiêu: explicit UI vs roman-natural. | Giữ; không phải trùng mục tiêu. |
| `context-004` / `context-013` và `context-014` | Dev dùng cùng dạng truy vấn “hợp âm trong A thứ tự nhiên”, nhưng Cmaj7 và Fmaj7 khác bậc. | Giữ để kiểm tra generalization, nhưng ghi nhận dev có hai mẫu cùng template; không dùng chúng như hai phép đo độc lập hoàn toàn. |
| `context-013` / `context-014` | Cùng group `seventh-alias`, cùng câu khung và cùng giọng; chỉ khác hợp âm/bậc. | Giữ tối đa một mẫu nếu muốn dev đa dạng hơn; mẫu còn lại nên chuyển sang một dev case khác hoặc thay bằng câu khác trước khi báo cáo accuracy. |
| `context-005` với các mẫu Am khác | Cùng từ khóa Am nhưng mục tiêu là thiếu thông tin, không phải trả bậc. | Giữ; đây là mẫu routing/missing-context, không phải mẫu roman numeral thuần. |

## Provenance và cổng duyệt

Rà soát này xác nhận nội dung và pipeline, nhưng chưa có bằng chứng đủ để tự chuyển 12 mẫu cũ sang `rights_cleared=true`. Vì vậy:

- 4 mẫu HM6-01–04: đã có bạn xác nhận dùng nội bộ.
- 12 mẫu cũ: đã rà kỹ thuật/nội dung, nhưng vẫn chờ xác nhận phạm vi quyền dùng ở cấp artifact.
- 34 mẫu A/C còn lại: chưa đưa vào bộ chính thức trong bước này.
- Không tạo manifest production-ready.
- Không chạy full training.

## Tokenizer và Engine

- 16 mẫu được encode bằng snapshot offline đã xác minh.
- Độ dài toàn bộ nằm trong giới hạn 1.024 token.
- Assistant mask hợp lệ.
- Music Engine đạt cho các claim định lượng.

## Kết luận và bước cần quyết định

Về mặt nội dung, **không phát hiện lỗi nhạc lý rõ ràng trong 12 mẫu cũ**. Vấn đề còn lại là quản trị bộ đánh giá và quyền sử dụng:

1. Có giữ cả `context-013` và `context-014` trong dev không, hay thay một mẫu để tránh dev quá đồng dạng?
2. Có xác nhận 12 mẫu cũ được phép dùng cho internal training không?
3. Sau hai xác nhận trên, mới gắn cờ approval/rights cho đúng phạm vi, tạo manifest strict và chạy preflight production.

Full training vẫn cần một xác nhận riêng sau khi manifest production-ready đạt.
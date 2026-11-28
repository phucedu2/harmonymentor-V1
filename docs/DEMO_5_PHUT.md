# Kịch bản demo 5 phút (góp ý thầy T1–T6)

Chuẩn bị (PowerShell, trước giờ demo): `docker compose up --build`, rồi `docker compose exec api python -m app.rag.ingest --source lessons`. Đăng nhập một tài khoản Admin và một tài khoản học viên. Có `.env` với khóa Gemini; nếu mạng lỗi, chatbot tự dùng câu dự phòng.

| Phút | Việc làm | Nói gì | Chỉ ra |
|---|---|---|---|
| 0:00–1:00 | Học viên mở bài L03, đổi giọng C → Eb | "Trước đây ví dụ chỉ thấy C/Cmaj7; giờ ký hiệu tính bằng Music Engine theo giọng." (T4) | Ebmaj7 Fm7 Bb7 Ebmaj7, nghe được |
| 1:00–2:15 | Admin: dán công thức nấu ăn → bị từ chối; dán đoạn về ii–V–I → nhận; dán đoạn lẫn → "chờ duyệt" | "Tài liệu phải qua cổng liên quan nhạc lý trước khi AI soạn bài." (T1) | Lý do tiếng Việt, điểm, nút Duyệt/Từ chối |
| 2:15–3:30 | Chatbot: hỏi "Cmaj7 gồm những nốt nào?" rồi "Hôm nay đá bóng ở đâu?" | "Có trích dẫn khối bài; lạc đề chỉ trả lời tối đa 2 câu rồi dẫn về." (T3) | Nhãn nguồn, sơ đồ `docs/AI_PIPELINE.md`, `docker compose exec api python -m app.rag.query "..."` (Qdrant không mở cổng ra máy) |
| 3:30–4:30 | Terminal: `cd backend; python -m app.eval.run` | "115 ca, đo HitRate@5, MRR, định tuyến; tụt là CI đỏ." (T2) | `eval/report.md`: HitRate 93,0%, MRR 0,848 |
| 4:30–5:00 | Mở `docs/MODEL_CARD.md`; `$env:RELEVANCE_SCORER="classifier"` | "Bộ phân loại tự train bằng CPU, có phiên bản và SHA-256; nói thật là chưa hơn hybrid." (T6) | Bảng AUC, mục Hạn chế |

Câu hỏi thầy dễ hỏi: vì sao Qdrant không tăng điểm (cùng e5; giá trị là lọc payload và mở rộng); nhãn do ai soạn (Claude, chưa kiểm độc lập); Gemini có bị gọi cho câu lạc đề không (có, 1 lượt ngắn; `OFFTOPIC_MODE=refuse` để tắt).

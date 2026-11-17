# G4 (T3, phần 2): pipeline chatbot kiểu n8n

Ngày làm: 15/11/2026. Nhánh `gop-y-thay/g4-pipeline` (xếp trên G3). Sơ đồ mermaid và bảng từng bước: [`docs/AI_PIPELINE.md`](../../AI_PIPELINE.md). Quyết định: [ADR-027](../../decisions/ADR-027-chatbot-pipeline-va-lac-de-tra-loi-ngan.md).

## Đã làm
- Khung pipeline `backend/app/ai/pipeline/core.py` (Node, điều kiện chạy, kết thúc sớm, nhảy lùi một lần cho vòng soạn lại, chặn vòng lặp vô hạn, ghi vết từng bước).
- 22 Node trong `backend/app/services/ai_pipeline.py`: trigger → rate_limit → guard → study_advice → intent → rewrite → retrieve → rerank → route → (greeting | help | off_topic | low_confidence → general | answer_gate → prompt → llm → parse → citation_check → safety → unknown_fallback) → log.
- Retrieve qua Qdrant khi `RAG_ENABLED=1` và đã nạp; lỗi hoặc rỗng thì tự lùi về e5 + BM25 và ghi lý do vào nhật ký. Rerank giữ nguyên điểm vector nên ngưỡng định tuyến không phải hiệu chỉnh lại.
- Máy chủ tự đối chiếu từng trích dẫn với đoạn đã truy xuất; Music Engine kiểm khẳng định nhạc lý; vòng soạn lại tối đa 1 lần.
- Lạc đề: tối đa 2 câu rồi dẫn về (ADR-027). Giới hạn tốc độ 20 lượt/phút/người (429 `AI_RATE_LIMITED`, kèm `Retry-After`, tin bị chặn không lưu). Nhật ký mỗi tin: các bước + mili giây, token, chi phí ước tính (nếu đặt giá).
- Giao diện chat giữ nguyên; chỉ thêm thông báo cho mã 429 mới.

## Kiểm chứng
- 19 test mới `tests/test_g4_pipeline.py`: khung pipeline, rewrite, rerank, cắt câu, Qdrant (nhúng) kể cả khi sập, rate limit, lạc đề, strict, nhật ký, và `docs/AI_PIPELINE.md` phải liệt kê đủ mọi node.
- Toàn bộ test cũ vẫn đạt sau khi thay `answer_question` bằng pipeline (đó là bằng chứng giữ nguyên hành vi). Hai test cũ phải sửa theo ý Phúc: câu lạc đề nay gọi AI và trả lời ngắn (`test_api_flow_g_and_c`, `test_out_of_scope_refused_without_llm` giữ chế độ `refuse`). Script đo `evaluate_rag.py` được chỉnh theo cùng định nghĩa "bị chặn".
- pytest 1368 passed, 1 skipped (test Qdrant thật chỉ chạy ở CI); `--min-passed` nâng lên 1369. Vitest 277 đạt; `npm run build` đạt.

## Chưa chạy / giới hạn
- Chưa thử với Gemini thật (khóa nằm ở máy Phúc); toàn bộ dùng FakeProvider.
- Chưa chạy stack Docker đầy đủ với Qdrant thật.
- Rerank hiện là luật từ khóa nhẹ, chưa phải mô hình; G5 sẽ đo xem có cải thiện HitRate/MRR không, nếu không thì tắt.
- `rate_limit` đếm trong bộ nhớ từng tiến trình.

## Cần Phúc quyết
1. Đồng ý ADR-027 (nhất là: câu lạc đề giờ tốn một lượt Gemini)? Nếu không muốn tốn lượt thì đặt `OFFTOPIC_MODE=refuse`.
2. `RAG_STRICT_GROUNDING`: giữ mặc định tắt (ADR-020 trả lời bằng kiến thức chung) hay bật cho bản nộp thầy?

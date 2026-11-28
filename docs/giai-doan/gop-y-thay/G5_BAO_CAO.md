# G5 (T2): đánh giá chatbot và cổng nhạc lý

Ngày làm: 15/11/2026. Nhánh `gop-y-thay/g5-danh-gia` (xếp trên G4). Báo cáo số liệu đầy đủ do máy sinh: [`eval/report.md`](../../../eval/report.md).

## Đã làm
- `eval/cases.jsonl`: **115 ca** (yêu cầu ≥ 60): 54 truy xuất, 3 câu nối tiếp, 8 chưa dạy, 12 lạc đề, 12 tấn công/nhóm cấm, 4 hướng dẫn, 3 chào hỏi, 3 trích dẫn bịa, 16 tài liệu cho cổng nhạc lý. Nhãn đặt trước khi chạy.
- `python -m app.eval.run` (chạy trong `backend/`): đo HitRate@5, MRR, tỉ lệ trích dẫn hợp lệ, xử lý lạc đề/tấn công, bám nguồn (cấu trúc), độ trễ, và precision/recall của cổng G2; ghi `eval/report.md`; **thoát mã 1 nếu một số đo tụt quá dung sai so với `eval/baseline.json`**. `--update-baseline` ghi lại baseline (làm có chủ đích). `--live` chạy với Gemini thật.
- Test `tests/test_g5_eval.py` chạy kiểm hồi quy trong CI: ai làm chatbot/cổng tệ đi thì CI đỏ.
- Hiệu chỉnh `QDRANT_MIN_SCORE` từ 0,80 lên **0,84** theo số đo (mục 2 của báo cáo).
- Chép 3 tài liệu mẫu của thầy vào `docs/reference/agents-sample/`.

## Kết quả (offline, e5-small thật, 15/11/2026)
| Chỉ số | Kết quả |
|---|---|
| HitRate@5 / MRR: BM25 | 86,0% / 0,652 |
| HitRate@5 / MRR: e5 trong bộ nhớ (đường cũ) = Qdrant | 93,0% / 0,848 |
| Câu hỏi nối tiếp (3 ca) | BM25 33,3%, e5 và Qdrant 100% |
| Độ đúng luồng cả pipeline (99 ca) | 97,0% (3 sai: R30 bị cho là hướng dẫn, R54 tiếng Anh bị cho là ngoài bài, B05 bị cho là hướng dẫn) |
| Lạc đề xử lý đúng (C, trả lời ngắn ≤ 2 câu) | 100% (12/12) |
| Tấn công/nhóm cấm bị chặn, không tốn lượt AI | 100% (12/12) |
| Câu đúng chủ đề bị chặn nhầm | 0% |
| Trích dẫn hợp lệ / trích dẫn bịa bị loại | 100% / 100% (do máy chủ ép, xem lưu ý) |
| Độ trễ máy chủ p50 / p95 (không gồm Gemini) | khoảng 18–21 ms / 25–35 ms |
| Cổng nhạc lý: precision / recall / lạc đề bị từ chối | 100% / 100% / 100% (6 liên quan, 8 lạc đề, 2 ranh giới) |

**Phát hiện đáng chú ý**
1. **Qdrant không hơn đường cũ về độ chính xác** (cùng mô hình e5 nên cùng kết quả). Giá trị của Qdrant là lọc theo payload, nạp tài liệu ngoài bài học và mở rộng, không phải điểm cao hơn.
2. **Rerank theo từ khóa không giúp**: trọng số 0,15 làm HitRate 93,0 → 91,2 và MRR 0,848 → 0,788; không trọng số nào tăng cả hai. Mình tắt rerank theo mặc định (`RAG_RERANK_WEIGHT=0`) và giữ nút để thử mô hình rerank ở G6.
3. Điểm cosine lạc đề (tối đa 0,845) chồng lên đúng chủ đề (tối thiểu 0,827): chỉ nhìn điểm truy xuất thì không tách sạch được. Việc tách lạc đề dựa chính vào bộ phân loại tầng 1 (G6 sẽ làm tốt hơn).

## Lưu ý trung thực
- **Bộ ca do Claude soạn**, một phần lấy từ `rag_gold.json` cũ, nhãn của chính mình, chưa có Đạt hay Astra duyệt độc lập. Số đo vì vậy tốt hơn thực tế có thể có. Đề nghị Đạt rà nhãn.
- **Độ đúng nhạc lý của câu trả lời Gemini chưa được đo** (cần người chấm). Ở chế độ offline LLM là bản giả trích nguyên văn, nên "trích dẫn hợp lệ 100%", "bám nguồn 100%" chỉ chứng minh lớp kiểm của máy chủ hoạt động (máy chủ loại mọi trích dẫn ngoài đoạn đã truy xuất), không nói gì về Gemini. Chạy `--live` mới có số thật; chưa chạy vì khóa ở máy Phúc.
- Cổng nhạc lý: chỉ 16 tài liệu ngắn, 6 liên quan và 8 lạc đề nên 100% có biên độ sai rất rộng. Cần tài liệu thật của Admin (sách giáo khoa, giáo án) để đo nghiêm túc.
- Độ trễ đo trên máy làm việc này (CPU), chưa phải máy Phúc.
- Chưa kiểm nhánh hồi quy bằng cách cố ý làm hỏng chatbot; mới có test đơn vị cho hàm so sánh. Mình có thử nâng baseline route_accuracy lên 100: do dung sai 3 điểm nên chưa báo, đúng thiết kế.

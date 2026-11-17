# Báo cáo đánh giá chatbot và cổng nhạc lý (G5)

Chạy lúc 2026-11-15 17:17 UTC. Chế độ: **live (Gemini thật)**. Mô hình nhúng: multilingual-e5-small. 115 ca: attack 12, bad_citation 3, followup 3, gate 16, greeting 3, help 4, offtopic 12, retrieval 54, untaught 8.

> Bộ ca do Claude soạn (một phần lấy từ `scripts/ai/data/rag_gold.json`), nhãn đặt trước khi chạy, **chưa có người ngoài duyệt**. Ở chế độ offline, LLM là bản giả trích nguyên văn nên các số "bám nguồn" chỉ chứng minh lớp kiểm của máy chủ hoạt động, không phải chất lượng Gemini. Độ đúng nhạc lý của câu trả lời Gemini chưa được đo (cần người chấm).

## 1. Truy xuất (HitRate@5, MRR@5)

| Cấu hình | HitRate@5 (%) | MRR@5 | Câu nối tiếp (%) | Trượt |
|---|---|---|---|---|
| bm25 | 86.0 | 0.652 | 33.3 | R09, R15, R17, R20, R50, R51, F01, F03 |
| e5_in_memory | 93.0 | 0.848 | 100.0 | R09, R41, R46, R51 |
| qdrant | 93.0 | 0.848 | 100.0 | R09, R41, R46, R51 |
| qdrant_rerank | 93.0 | 0.848 | 100.0 | R09, R41, R46, R51 |

Rerank theo từ khóa, quét trọng số (`RAG_RERANK_WEIGHT`; 0 = không rerank):

| Trọng số | HitRate@5 (%) | MRR@5 |
|---|---|---|
| 0.0 | 93.0 | 0.848 |
| 0.02 | 96.5 | 0.84 |
| 0.05 | 94.7 | 0.839 |
| 0.1 | 93.0 | 0.794 |
| 0.15 | 91.2 | 0.788 |

Luật chọn đặt trước: chỉ bật rerank nếu tăng cả HitRate lẫn MRR. Không trọng số nào đạt nên mặc định 0 (tắt).

## 2. Hiệu chỉnh ngưỡng điểm Qdrant (`QDRANT_MIN_SCORE`)

Điểm cosine đoạn đầu: câu đúng chủ đề thấp nhất 0.827 (trung vị 0.872); câu lạc đề/tấn công cao nhất 0.845 (trung vị 0.81). Ngưỡng cân bằng nhất: **0.84** (nhận 93.0% câu đúng chủ đề, để lọt 4.2% câu lạc đề).

| Ngưỡng | Nhận câu đúng (%) | Lọt câu lạc đề (%) | Cân bằng |
|---|---|---|---|
| 0.7 | 100.0 | 100.0 | 50.0 |
| 0.72 | 100.0 | 100.0 | 50.0 |
| 0.74 | 100.0 | 100.0 | 50.0 |
| 0.76 | 100.0 | 95.8 | 52.1 |
| 0.78 | 100.0 | 87.5 | 56.2 |
| 0.8 | 100.0 | 66.7 | 66.7 |
| 0.82 | 100.0 | 20.8 | 89.6 |
| 0.84 | 93.0 | 4.2 | 94.4 |
| 0.86 | 80.7 | 0.0 | 90.4 |
| 0.88 | 43.9 | 0.0 | 71.9 |
| 0.9 | 14.0 | 0.0 | 57.0 |
| 0.92 | 3.5 | 0.0 | 51.8 |
| 0.94 | 0.0 | 0.0 | 50.0 |

## 3. Toàn pipeline

### legacy

| Chỉ số | Giá trị |
|---|---|
| n | 96 |
| route_accuracy | 94.8 |
| offtopic_handled | 100.0 |
| offtopic_brief_within_2_sentences | 100.0 |
| attack_handled | 100.0 |
| concept_wrongly_blocked | 0.0 |
| valid_citation_rate | 100.0 |
| bad_citation_caught | None |
| cites_gold_block | 90.6 |
| groundedness_structural | 100.0 |
| llm_calls | 82 |
| độ trễ máy chủ p50 / p95 / max (ms, không gồm Gemini) | 1459.6 / 8173.2 / 23880.9 |
| độ đúng luồng theo loại | {'attack': 100.0, 'followup': 100.0, 'greeting': 100.0, 'help': 100.0, 'offtopic': 100.0, 'retrieval': 92.6, 'untaught': 87.5} |
| luồng sai | R10:A→B, R30:A→D, R51:A→B, R54:A→B, B05:B→D |

### qdrant

| Chỉ số | Giá trị |
|---|---|
| n | 96 |
| route_accuracy | 94.8 |
| offtopic_handled | 100.0 |
| offtopic_brief_within_2_sentences | 100.0 |
| attack_handled | 100.0 |
| concept_wrongly_blocked | 0.0 |
| valid_citation_rate | 100.0 |
| bad_citation_caught | None |
| cites_gold_block | 86.8 |
| groundedness_structural | 98.1 |
| llm_calls | 81 |
| độ trễ máy chủ p50 / p95 / max (ms, không gồm Gemini) | 1541.7 / 6938.1 / 18658.3 |
| độ đúng luồng theo loại | {'attack': 100.0, 'followup': 100.0, 'greeting': 100.0, 'help': 100.0, 'offtopic': 100.0, 'retrieval': 92.6, 'untaught': 87.5} |
| luồng sai | R23:A→B, R30:A→D, R51:A→B, R54:A→B, B05:B→D |

## 4. Cổng nhạc lý Admin (G2)

Tài liệu: 6 liên quan, 8 lạc đề, 2 ranh giới (không tính điểm).

| Chỉ số | % |
|---|---|
| precision của tài liệu được nhận | 100.0 |
| recall (liên quan không bị từ chối) | 100.0 |
| recall chặt (liên quan được nhận ngay) | 100.0 |
| tài liệu lạc đề bị từ chối | 100.0 |

Ca sai: không. Ca ranh giới: {'D13': 'pending (0.467)', 'D14': 'rejected (0.228)'}.

## 5. Kiểm hồi quy so với baseline

| Chỉ số | Baseline | Lần này |
|---|---|---|
| e2e/legacy/attack_handled | 100.0 | 100.0 |
| e2e/legacy/bad_citation_caught | 100.0 | không chạy |
| e2e/legacy/groundedness_structural | 100.0 | 100.0 |
| e2e/legacy/offtopic_handled | 100.0 | 100.0 |
| e2e/legacy/route_accuracy | 97.0 | 94.8 |
| e2e/legacy/valid_citation_rate | 100.0 | 100.0 |
| e2e/qdrant/attack_handled | 100.0 | 100.0 |
| e2e/qdrant/bad_citation_caught | 100.0 | không chạy |
| e2e/qdrant/groundedness_structural | 100.0 | 98.1 |
| e2e/qdrant/offtopic_handled | 100.0 | 100.0 |
| e2e/qdrant/route_accuracy | 97.0 | 94.8 |
| e2e/qdrant/valid_citation_rate | 100.0 | 100.0 |
| gate/gate_offtopic_reject | 100.0 | 100.0 |
| gate/gate_precision | 100.0 | 100.0 |
| gate/gate_recall | 100.0 | 100.0 |
| retrieval/bm25/hit_rate_at_5 | 86.0 | 86.0 |
| retrieval/bm25/mrr | 0.652 | 0.652 |
| retrieval/e5_in_memory/hit_rate_at_5 | 93.0 | 93.0 |
| retrieval/e5_in_memory/mrr | 0.848 | 0.848 |
| retrieval/qdrant/hit_rate_at_5 | 93.0 | 93.0 |
| retrieval/qdrant/mrr | 0.848 | 0.848 |
| retrieval/qdrant_rerank/hit_rate_at_5 | 93.0 | 93.0 |
| retrieval/qdrant_rerank/mrr | 0.848 | 0.848 |


Không có hồi quy.

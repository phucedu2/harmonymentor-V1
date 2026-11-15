# Bản đồ góp ý của thầy (T1–T6) → việc đã làm

Cập nhật 15/11/2026. Mỗi cổng G là một Draft PR nhỏ, xếp chồng theo thứ tự G1 → G2 → … → G7, chưa gộp vào `phuc-music` (chờ nhóm duyệt).

| Góp ý | Nội dung | Cổng | PR | Cách kiểm lại | Còn thiếu / nói thẳng |
|---|---|---|---|---|---|
| T1 | Admin upload tài liệu lạc đề vẫn được dùng để AI soạn bài | G2 | #55 | Dán công thức nấu ăn ở trang Admin → bị từ chối kèm lý do; `pytest tests/test_g2_cong_nhac_ly.py` | Điểm liên quan mới là heuristic + e5; ngưỡng LOW 0,35 / HIGH 0,60 do Phúc chọn, chưa hiệu chỉnh bằng tài liệu thật của nhóm |
| T2 | Đánh giá chatbot và cổng một cách đo được | G5 | #58 | `cd backend && python -m app.eval.run` → `eval/report.md`, thoát mã 1 nếu tụt so với `eval/baseline.json` | 115 ca và nhãn do Claude soạn, chưa ai độc lập kiểm; chạy offline với Gemini giả, chưa đo Gemini thật |
| T3 | Kho vector Qdrant và chatbot dạng pipeline (kiểu n8n) | G3, G4 | #56, #57 | `docker compose up` (có Qdrant), `python -m app.rag.ingest --source all`, sơ đồ ở `docs/AI_PIPELINE.md`; lạc đề trả lời tối đa 2 câu rồi dẫn về | Chưa chạy Qdrant server thật trong phiên cloud (chỉ chế độ nhúng + CI service container); Qdrant không làm HitRate cao hơn đường cũ (cùng e5) |
| T4 | Bài 2–9 chỉ thấy hợp âm C / Cmaj7 | G1 | #54 | Chọn giọng Eb ở bài L03 → Ebmaj7 Fm7 Bb7; `tests/test_g1_doi_giong.py` | Giọng mặc định vẫn C, lời văn quanh ví dụ vẫn nhắc giọng C (cần Đạt duyệt nếu đổi) |
| T5 | Làm từng cổng, dừng chờ duyệt, không gộp bừa | G1–G7 | #54–#59 + PR G7 | Mỗi cổng có báo cáo `docs/giai-doan/gop-y-thay/G*_BAO_CAO.md` | Các PR xếp chồng, `ci.yml --min-passed` sẽ xung đột khi gộp: giữ số lớn nhất |
| T6 | Tự train mô hình (CPU, không fine-tune LLM) | G6 | #59 | `cd backend && python -m app.ml.relevance_train`; `docs/MODEL_CARD.md` | Chưa vượt rõ bộ chấm hybrid; nhãn do Claude soạn; adapter/reranker và notebook Colab chưa chạy |

Quyết định đã chốt (Phúc): ngưỡng 0,35/0,60 · PDF+OCR, DOCX, ảnh OCR, MusicXML/MIDI, dán chữ · Qdrant Docker cục bộ, giữ đường cũ làm dự phòng · e5-small (máy 8 GB RAM) · Gemini chỉ qua `.env`, có FakeProvider · kho tài liệu thô ở `data/corpus/raw/` (gitignore) · không fine-tune LLM.

# G3 (T3, phần 1): Qdrant, nạp dữ liệu và truy vấn

Ngày làm: 15/11/2026. Nhánh `gop-y-thay/g3-qdrant` (xếp trên nhánh G2, đích `phuc-music`). Quyết định: [ADR-026](../../decisions/ADR-026-qdrant-kho-vector-mac-dinh.md).

## Đã làm
- `docker-compose.yml`: dịch vụ `qdrant` (v1.12.4, volume `qdrantdata`, healthcheck); `api` nhận `QDRANT_URL=http://qdrant:6333`.
- `backend/app/rag/`: `chunker.py` (chia theo TOKEN của e5, có chồng lấn, không cắt giữa câu), `store.py` (collection cosine, chỉ mục payload, upsert idempotent, xóa đoạn cũ, lọc + ngưỡng điểm), `sources.py` (bài học đã phát hành; `data/corpus/raw` qua bộ trích chữ của cổng G2, sidecar `*.meta.json`), `ingest.py`, `query.py`, `embedding.py`.
- CLI: `python -m app.rag.ingest --source lessons|corpus|all [--dry-run] [--recreate] [--stats]`, `python -m app.rag.query "câu hỏi" [--source] [--lesson] [--top-k] [--min-score]`.
- `data/corpus/raw/` nằm trong `.gitignore` (không commit sách có bản quyền); hướng dẫn ở `data/corpus/README.md`.
- Cấu hình tập trung `RagConfig`, ghi đè bằng biến môi trường (đã thêm vào `.env.example`).

## Kiểm chứng
- `tests/test_g3_qdrant.py`: 12 test chạy với FakeEmbedder + Qdrant nhúng (`:memory:`): chia đoạn, idempotent, xóa đoạn cũ, lọc nguồn/bài, ngưỡng điểm, tài liệu hỏng bị cảnh báo chứ không sập, CLI `--dry-run`, thiếu `QDRANT_URL` báo lỗi mã 2.
- 1 test tích hợp với MÁY CHỦ Qdrant thật (`QDRANT_TEST_URL`). CI có service container nên chạy thật ở đó; **trong phiên làm việc này tôi không chạy được máy chủ Qdrant** (không có Docker; việc chạy tệp nhị phân tải về bị chặn và tôi không vòng qua), nên test đó bị skip ở máy tôi. Kết quả thật nằm ở CI của PR.
- pytest cục bộ: 1349 passed, 1 skipped (test tích hợp nói trên). `--min-passed` nâng lên 1350 (tính cả test tích hợp trong CI).
- Thử với e5 thật (Qdrant nhúng): nạp 82 đoạn bài học trong 4,6 giây. Điểm top-1: "Cmaj7 gồm những nốt nào" 0,880 (L04); "vòng I-V-vi-IV" 0,890; câu lạc đề "cách nấu phở bò" vẫn được 0,813.

## Cần Phúc biết
1. Ngưỡng `QDRANT_MIN_SCORE=0.80` chỉ là giá trị ban đầu: câu lạc đề đã đạt 0,813, tức chưa tách được. Ngưỡng sẽ hiệu chỉnh ở G5 (dự kiến quanh 0,84–0,86), và G4 còn có bước Guard chặn lạc đề trước khi tới Qdrant.
2. Chạy thử trên máy bạn (PowerShell):
   ```powershell
   docker compose up -d --build
   docker compose exec api python -m app.rag.ingest --source lessons
   docker compose exec api python -m app.rag.query "Cmaj7 gồm những nốt nào"
   docker compose exec api python -m app.rag.ingest --stats
   ```
3. Chưa nối chatbot vào Qdrant: đó là G4. Hiện đường cũ (e5 + BM25) vẫn chạy nguyên.
4. `ci.yml` giờ bị sửa ở cả PR G1, G2 và G3 (dòng `--min-passed`); gộp theo thứ tự G1 → G2 → G3 và giữ số lớn nhất.

# Kho tài liệu RAG

Đặt tài liệu nhạc lý (PDF, DOCX, ảnh, MusicXML/MIDI, .md, .txt) vào `data/corpus/raw/` (thư mục này nằm trong `.gitignore`, **không** commit sách có bản quyền).
Có thể thêm tệp cạnh bên `<tên tệp>.meta.json`: `{"title": "...", "lang": "vi", "license": "CC-BY / tự soạn / ...", "lesson_id": "L03"}`.

```powershell
docker compose up -d qdrant
docker compose exec api python -m app.rag.ingest --source all
docker compose exec api python -m app.rag.query "Cmaj7 gồm những nốt nào"
```
Chạy lại an toàn (id điểm tất định). Đổi mô hình nhúng thì thêm `--recreate`.

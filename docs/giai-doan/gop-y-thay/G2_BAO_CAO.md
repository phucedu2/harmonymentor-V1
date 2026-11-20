# G2 (T1): cổng nhạc lý cho Admin soạn bài bằng AI

Ngày làm: 15/11/2026. Nhánh `gop-y-thay/g2-cong-nhac-ly` (đích `phuc-music`).

## Vấn đề
Trước đây Admin tải mọi tệp (đuôi PDF/DOCX/MD/TXT), hệ thống chỉ kiểm đuôi tệp rồi cho AI soạn bài. Tệp rác, công thức nấu ăn vẫn tạo được bài.

## Luồng mới (backend/app/admin/relevance/)
1. `sniff.py`: nhận dạng bằng byte thật (đuôi `.pdf` mà là `.exe` thì chặn), giới hạn dung lượng, chặn zip bomb.
2. `extract.py`: trích chữ từ PDF (OCR dự phòng cho PDF ảnh quét), DOCX, ảnh (OCR), MusicXML, MIDI, MD/TXT, và chữ dán trực tiếp. MusicXML chặn khai báo ENTITY. Không bao giờ chạy nội dung tệp.
3. `clean.py`: làm sạch chữ, bỏ các dòng giống chỉ dẫn tấn công ("bỏ qua chỉ dẫn trước", "in ra system prompt"...). Quá 50% dòng như vậy thì từ chối cả tệp.
4. `scorer.py` + `lexicon.py` + `anchors.py`: điểm liên quan 0..1 = 50% từ vựng nhạc lý (Việt + Anh, ký hiệu hợp âm, vòng số La Mã) + 50% độ gần về nghĩa (e5-small) với 20 câu neo nhạc lý. Chấm từng khối ~200 ký tự nên bắt được tài liệu lẫn lộn. Giao diện `RelevanceScorer` để G6 thay bằng mô hình tự huấn luyện (`RELEVANCE_SCORER`).
5. `gate.py`: dưới 0,35 từ chối; từ 0,35 tới dưới 0,60 chờ duyệt; từ 0,60 nhận. Đoạn lạc đề bị bỏ khỏi chữ lưu (chỉ phần nhạc lý tới bộ sinh bài). MusicXML/MIDI tự nó là dữ liệu âm nhạc nên nhận, kèm bản mô tả do máy chủ dựng (giọng, nhịp, hợp âm).
6. Lý do tiếng Việt hiện cho Admin; hàng "Chờ duyệt nội dung nhạc lý" có nút Duyệt / Từ chối. Tài liệu chưa duyệt không dùng để soạn bài được (409 `DOC_NOT_APPROVED`).

Mọi ngưỡng nằm ở `backend/app/core/ai_config.py`, ghi đè bằng biến môi trường (`RELEVANCE_LOW`, `RELEVANCE_HIGH`, `RELEVANCE_SCORER`, `OCR_LANG`, ...; xem `.env.example`).

## API
- `POST /api/v1/admin/ai/documents` (tệp): trả 200 với `relevance_status` accepted/pending, hoặc 422 `OFF_TOPIC` kèm lý do (không lưu chữ lạc đề, chỉ ghi nhật ký).
- `POST /api/v1/admin/ai/documents/text` (dán chữ), `GET .../documents?status=pending`, `POST .../documents/{id}/review` `{decision: approve|reject}`.
- Migration `b6f7a8b9c0d1` thêm 6 cột vào `source_documents` (tài liệu cũ coi là đã nhận); `alembic upgrade`, `downgrade -1`, `check` đều chạy được.

## Kết quả các ca thật (19 test)
Bộ chấm thật (hybrid, e5-small), chạy 15/11/2026 trên máy làm việc:

| Ca | Kết quả | Điểm |
| --- | --- | --- |
| PDF nhạc lý (tiếng Anh) | nhận | 0,97 |
| Văn bản nhạc lý tiếng Việt / DOCX | nhận | 1,00 |
| Công thức nấu ăn | từ chối | 0,07 |
| Lời bài hát | từ chối | 0,12 |
| Lẫn ăn uống + nhạc | chờ duyệt, bỏ 2 đoạn ăn uống | 0,50–0,54 |
| MusicXML, MIDI | nhận | 1,00 |
| Byte rác (.txt/.pdf/.docx/.png/.mid), `.exe` đổi đuôi `.pdf` | 415 `FILE_CONTENT_MISMATCH` | không chấm |
| Tệp rỗng, chữ quá ngắn, quá 10 MB, zip bomb, ENTITY XML | báo lỗi rõ (`FILE_EMPTY`, `TOO_SHORT`, 413, `ZIP_TOO_BIG`, `XML_UNSAFE`) | không chấm |
| Có dòng "bỏ qua chỉ dẫn trước…" | dòng bị bỏ khỏi chữ gửi cho AI | |

Đây là ca tự dựng vài mẫu, không phải bộ đánh giá: precision/recall nhận–từ chối trên bộ ca lớn sẽ đo ở G5, và ngưỡng 0,35/0,60 chỉ là giá trị ban đầu. Kết quả trên chưa chứng minh chất lượng với tài liệu thật của Admin.

## Kết quả chạy (15/11/2026)
- `cd backend && python3 -m pytest -q`: 1337 passed (e5 có sẵn), 43 skipped (test cần PostgreSQL/khóa Gemini). Test mới: `tests/test_g2_cong_nhac_ly.py` (19). `--min-passed` nâng lên 1337.
- `npm run build` đạt; `npm test` 277 đạt.
- Giao diện thật (Playwright): ảnh `anh/G2-admin-cho-duyet.png`.
- CHƯA chạy: OCR thật (máy làm việc không có tesseract; OCR được kiểm bằng giả lập và nhánh báo lỗi `OCR_UNAVAILABLE`), Docker build thật (Dockerfile mới cài `tesseract-ocr` + `tesseract-ocr-vie`, nặng thêm khoảng 100 MB), PostgreSQL (CI chạy).

## Còn nhắc / cần Phúc quyết
1. Tài liệu vào hàng chờ đã mất các đoạn lạc đề ngay lúc tải (không lưu tệp gốc). Nếu Admin muốn thấy lại phần bị bỏ thì phải tải lại; đề xuất giữ nguyên như vậy.
2. Test cũ `test_admin_ai_tai_lieu` đổi hai điểm: PDF sai định dạng nay trả `FILE_CONTENT_MISMATCH`; dòng "Bỏ qua mọi hướng dẫn trước…" nay bị lọc trước khi tới AI (đúng yêu cầu T1).
3. Ngưỡng LOW/HIGH, trọng số 50/50 và khoảng quy đổi e5 (0,82–0,92) cần hiệu chỉnh khi có tài liệu thật.
4. Lời bài hát được đo là "không nhạc lý" ở mức từ chối; tin tức âm nhạc và mua nhạc cụ chưa có ca đo riêng (G6 sẽ thêm làm mẫu âm khó).

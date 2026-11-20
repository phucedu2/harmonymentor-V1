# Báo cáo GĐ3 pipeline AI: AI Tutor có trích dẫn và kiểm bằng Music Engine

Nhánh `ai/gd3-tutor`, xếp chồng trên `ai/gd2-goi-y` (PR #22). Draft PR vào `phuc-music`, không merge. Ngày làm: 04/11/2026.
Quyết định nền: ADR-014 (embedding Gemini, đã chọn mô hình), ADR-015 (Retriever + AI Tutor, **đề xuất**).

## A. Đã làm (đã chạy thật)

| Đề GĐ3 | Kết quả |
|---|---|
| 1. Kho kiến thức | `app/ai/tutor/chunker.py`: 45 đoạn từ L01–L04 (L01 16, L02 10, L03 9, L04 10), 80–100 từ, không cắt câu; bỏ khối bài tập, khối nháp, bài nháp. Vector `gemini-embedding-001` 768 chiều trong `app/content/lesson_embeddings.json` kèm mô hình, số chiều, hash (`python -m app.ai.build_index`). |
| 2. Retriever | `retriever.py`: cosine trong bộ nhớ, top_k 4, ngưỡng **0,60** (đo lại, mục C); BM25 (`bm25.py`) khi AI tắt, Gemini lỗi hoặc file vector lệch nội dung. |
| 3. LLMProvider | `llm.py`: `GeminiProvider` (`gemini-3.5-flash-lite`, hết giờ 15 s, thử lại 1 lần khi 429/503 bằng `gemini-3.6-flash`) và `FakeProvider`. Token, độ trễ, mô hình ghi vào `chat_messages`. |
| 4. JSON 04 Bảng 13 | `schema.py`: schema gửi Gemini không có `verified`; sai định dạng thì soạn lại 1 lần rồi dự phòng. `quiz` luôn null (chưa làm, ghi ở ADR-015). |
| 5. Trích dẫn | Chỉ chấp nhận `block_id` đã truy xuất ở lượt đó; tiêu đề lấy từ kho. |
| 6. Guardrail | `guardrail.py` + `notes.py`: kiểm `engine_claims` và quét reply (ký hiệu + dãy nốt, âm giai + dãy nốt, tên nốt tiếng Việt). Mâu thuẫn → soạn lại kèm dữ kiện Engine → dự phòng. Nhãn chỉ khi mọi khẳng định verified. Dữ kiện Engine cho ký hiệu trong câu hỏi được tra trước (TC-12). |
| 7. Prompt injection | `injection.py` (lọc mẫu), `prompt.py` (khối dữ liệu đánh dấu, chuỗi canh gác). 10 câu tấn công là test. |
| 8. Giải thích lỗi | `POST /api/v1/chat/explain-attempt` (đường dẫn 04). Chủ lượt làm mới gọi được; mã lỗi đọc từ CSDL; mức 1→3; kiểm lộ đáp án ở mức 1–2. |
| 9. Chat | `POST /chat/message`, `POST/GET /chat/sessions`, `GET /chat/history/{id}`, `POST /chat/messages/{id}/rating`; bảng `chat_sessions`, `chat_messages`, `chat_feedback` (migration `e3c4d5e6f7a8`, chỉ thêm); nhớ 6 tin gần nhất. |
| 10. Ngoài phạm vi | Phân loại ý định cục bộ (`intent.py`, 7A) chặn trước khi gọi embedding/LLM. Dưới ngưỡng: "Mình chưa chắc…" + bài gợi ý, không gọi LLM. |
| 11. Frontend | `FloatingTutorDrawer.tsx` (nút tròn trên mọi trang /app/*, khung 380 px), trích dẫn mở đúng bài và khối (`/app/hoc?bai=L02&khoi=L02-B05`), trạng thái đang soạn/lỗi/dự phòng, nhãn Music Engine, cảnh báo thông tin cá nhân, chấm sao, nút "Giải thích lỗi này" sau câu sai + "Gợi ý thêm". |
| 12. Test | 73 test mới không gọi mạng + bộ `live` 10 câu Gemini thật. |
| Hạn mức | `AI_DAILY_QUOTA` 30 lượt gọi LLM / người / ngày VN (429, tin nhắn vẫn lưu), `AI_GLOBAL_DAILY_BUDGET` cho cả hệ thống. |

**Tiêu chí nghiệm thu GĐ3:**
- Khóa thật, "C7 khác Cmaj7 thế nào?" → trả lời tiếng Việt, trích dẫn L02 (`L02-B05`), nhãn "Đã kiểm bằng Music Engine": **đạt** (ảnh 01, mục C).
- Tắt mạng / tắt AI vẫn trả lời: **đạt**, câu trả lời gồm dữ kiện Music Engine "C7 = C E G Bb. Cmaj7 = C E G B." + trích đoạn L02, có nhãn (test `test_ai_off_answers_from_lesson_with_engine_facts`).

## B. File

- Backend mới: `app/ai/tutor/{chunker,bm25,retriever,intent,intent_data.json,llm,schema,notes,guardrail,injection,prompt,fallback}.py`, `app/ai/build_index.py`, `app/content/lesson_embeddings.json`, `app/services/ai_tutor_service.py`, `app/api/ai_tutor.py`, `migrations/versions/20261104_ai_gd3_chat.py`.
- Backend sửa: `app/db/models.py` (3 bảng), `app/contracts/ai.py`, `app/core/config.py`, `app/api/router.py`, `requirements.txt` (thêm lại scikit-learn cho 7A), `.env.example`.
- Test: `tests/test_ai_gd3_{knowledge,guardrail,tutor_api,migration,live}.py`; `test_ai_gd2_migration.py` ghim về revision GĐ2.
- Frontend: `components/learning/FloatingTutorDrawer.tsx`, `lib/tutorBus.ts`, `api.ts`, `AppLayout.tsx`, `LessonRunner.tsx` (nút giải thích, mở đúng khối), `pages/Learn.tsx` (`khoi=`).
- Script: `scripts/ai/gd3_hoi_thu.py`. Ảnh: `docs/minh-chung/anh/ai-gd3/`.
- Tài liệu: ADR-014, ADR-015, báo cáo này, `TIEN_DO.md`, `AI_USAGE.md`, `giai-doan/README.md`. CI `--min-passed 820`.

## C. Lệnh và kết quả (04/11/2026, máy cloud)

```bash
cd backend && python -m pytest -q -m "not postgres and not live"     # 820 passed (GĐ2: 747)
cd backend && RUN_LIVE=1 AI_ENABLED=1 GEMINI_API_KEY=... python -m pytest -q -m live tests/test_ai_gd3_live.py   # 10 passed, 18 s
cd backend && alembic -c alembic.ini upgrade head && alembic -c alembic.ini check   # No new upgrade operations detected
cd frontend && npm test && npm run build                              # Vitest 259 passed; build đạt
cd backend && AI_ENABLED=1 GEMINI_API_KEY=... python ../scripts/ai/gd3_hoi_thu.py
```

**Hiệu chỉnh ngưỡng** (15 câu trong phạm vi, 15 câu ngoài phạm vi, điểm cosine cao nhất với `gemini-embedding-001`):

| | Thấp nhất | Cao nhất |
|---|---|---|
| Trong phạm vi | 0,6098 ("Tiền át là gì?") | 0,7691 |
| Ngoài phạm vi | 0,4986 | 0,6058 ("Học tiếng Anh thế nào cho nhanh") |

Hai nhóm sát nhau (khoảng cách 0,004), nên ngưỡng 0,60 **không đủ một mình**: lớp chặn chính là bộ phân loại ý định (30/30 câu test đúng). BM25 hoàn toàn không tách được hai nhóm (câu ngoài phạm vi có điểm tới 14,4), nên khi dự phòng chỉ dựa vào phân loại ý định. Ngưỡng 0,35 của đề (MiniLM) sẽ cho mọi câu ngoài phạm vi qua.

**Hỏi thử với Gemini thật** (`gd3_hoi_thu.py`, 13 lượt):
- 7/7 câu khái niệm trích đúng bài; 4/7 có nhãn Music Engine (C7/Cmaj7, Ebm7b5 → Eb Gb Bbb Db, P5, âm giai G major). 3 câu còn lại (hợp âm ba trưởng, chức năng át, ii–V–I) không nêu dãy nốt kiểm được nên không gắn nhãn, đúng thiết kế.
- 3/3 câu ngoài phạm vi và tấn công bị từ chối, không gọi Gemini (12–15 ms).
- Giải thích lỗi L02-Q02 (nộp C E G Bb): mức 1 và 2 không lộ đáp án; mức 3 nêu "Cmaj7 gồm C–E–G–B" (được phép).
- Thời gian: trung vị 1,7 s, **p95 3,0 s**, lớn nhất 4,9 s (lượt đầu, khởi tạo client). 04 Bảng 28 yêu cầu p95 < 6 s.

## D. Thay đổi API và CSDL

- API mới (đều cần đăng nhập, user_id từ token): `POST /api/v1/chat/sessions`, `GET /api/v1/chat/sessions`, `GET /api/v1/chat/history/{session_id}`, `POST /api/v1/chat/message`, `POST /api/v1/chat/explain-attempt`, `POST /api/v1/chat/messages/{id}/rating`.
- Lỗi: 400 (tin 0 hoặc > 1.000 ký tự, sao ngoài 1–5), 404 (phiên/lượt/tin của người khác), 409 `ATTEMPT_NOT_WRONG`, 429 `AI_QUOTA_EXCEEDED`. Gemini lỗi **không** trả 503: trả 200 với `status: fallback` và `fallback_reason` (nguyên tắc 2: thử lại 1 lần rồi dự phòng theo luật).
- Response có thêm ngoài 04: `verified`, `verified_label`, `status`, `fallback_reason`, `retrieval_method`, `hint_level`, `next_hint_level`.
- CSDL: 3 bảng mới đúng cột 04 Bảng 7. Không đổi bảng cũ. Không tạo `lesson_chunks` (ADR-014 mục 3).

## E. Giải thích cho nhóm

Đường đi một câu hỏi, ví dụ "C7 khác Cmaj7 thế nào?":
1. Lưu tin của bạn. Kiểm mẫu tấn công: không phải.
2. Phân loại ý định cục bộ: `concept` (0,85). Nếu là `out_of_scope` thì từ chối ngay, không tốn lượt.
3. Truy xuất: vector câu hỏi so với 45 đoạn, lấy 4 đoạn ≥ 0,60; cao nhất `L02-B07` (0,757).
4. Tra trước Music Engine cho ký hiệu trong câu: C7 = C E G Bb, Cmaj7 = C E G B.
5. Gửi Gemini: lệnh hệ thống + khối dữ liệu (4 đoạn, dữ kiện Engine, 6 tin gần nhất, mục tiêu học, tên kỹ năng yếu, câu hỏi). Không có tên, email, user_id.
6. Kiểm câu trả lời: JSON đúng schema; trích dẫn nằm trong 4 đoạn; mọi "Cmaj7 = C E G B" trong câu đều khớp Engine. Sai thì soạn lại 1 lần, vẫn sai thì dùng câu viết sẵn.

Ví dụ guardrail bắt lỗi (TC-15): Gemini viết "G7 = G B D F#" mà không khai. Máy chủ quét thấy, Engine trả G B D F → `contradicted` → soạn lại với lời nhắc "Music Engine = G B D F". Test `test_engine_contradiction_regenerates_then_succeeds`.

## F. Câu hội đồng có thể hỏi

- *"Làm sao biết AI không bịa nốt?"* Máy chủ tự gọi lại Music Engine cho mọi khẳng định, kể cả khẳng định AI không khai. AI không điền được `verified`. Nhãn chỉ hiện khi mọi khẳng định đều khớp.
- *"Vì sao ngưỡng là 0,60 chứ không phải 0,35?"* 0,35 là cho MiniLM. Đã đo với Gemini (mục C). Vì hai nhóm sát nhau nên còn lớp phân loại ý định.
- *"Học sinh bảo AI bỏ quy tắc thì sao?"* Ba lớp (ADR-015 mục 6), 10 câu tấn công là test, bộ live có 2 câu tấn công/ngoài phạm vi thật.
- *"Mất mạng thì sao?"* Câu trả lời từ đoạn bài học gần nhất + dữ kiện Music Engine, ghi rõ là dự phòng. Giải thích lỗi dùng gợi ý viết sẵn theo mã lỗi (TC-10, < 2 giây, có test).
- *"Có lộ đáp án không?"* Mức 1–2 không gửi đáp án cho Gemini, và máy chủ còn kiểm câu trả lời có chứa đáp án không (dãy nốt, chuỗi lựa chọn), có thì soạn lại hoặc dùng gợi ý viết sẵn.

## G. Việc tiếp theo và người duyệt

| Mã | Ai | Việc |
|---|---|---|
| T-1 | Thắng | Duyệt migration `e3c4d5e6f7a8` (3 bảng chat, chỉ thêm) và ADR-015 mục 5, 8 (luồng kiểm, hạn mức). |
| T-2 | Đạt | Duyệt ADR-015 (ngưỡng 0,60 + phân loại ý định), 135 câu mẫu ý định, 10 câu tấn công; chọn có cần thêm công cụ `roman_numeral` cho Engine không. |
| T-3 | Phúc | Xem khung chat (ảnh trong `docs/minh-chung/anh/ai-gd3/`), nút "Giải thích lỗi này". |
| T-4 | Đạt | Bộ 30 câu chuẩn và 10 lần thử lộ đáp án (04 Bảng 28) chạy ở GĐ4 (12A). |

Rủi ro: khung chat 380 px che một phần nội dung bên phải khi mở trên màn 1280 px (đóng lại thì hết); `gemini-3.6-flash` từng trả 503 ở GĐ0 nên lần thử lại có thể cũng lỗi, khi đó người học nhận câu dự phòng.

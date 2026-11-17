# Bàn giao: tài liệu eProject Review 01–03 (bản song ngữ Anh–Việt và bản thuần tiếng Việt)

Ngày 17/11/2026. Nhánh `docs-review123` tách từ `phuc-music` commit **1ab6a15** (merge PR #62).

## 1. Kết quả

| File | Nội dung |
|---|---|
| `eProject_Sem-II_HarmonyMentor_Review01_02_03_TiengViet.docx` | **Bản thuần tiếng Việt** (thêm 17/11/2026 theo yêu cầu của Phúc), 89 trang A4, cùng nội dung và bố cục với bản song ngữ. Mọi tiêu đề, tên mục theo mẫu Aptech, header/footer, bìa, chứng nhận, bảng và nhãn sơ đồ đều bằng tiếng Việt. Giữ nguyên như trong code: tên bảng, tên cột, endpoint, mã lỗi, đường dẫn file, thuật ngữ kỹ thuật (DFD, ERD, API, JWT, mastery, embedding…) |
| `eProject_Sem-II_HarmonyMentor_Review01_02_03.docx` | Bản song ngữ, 109 trang A4 khi render bằng LibreOffice 24.2: bìa, chứng nhận, mục lục (trường TOC thật, đã điền số trang), lời cảm ơn, tóm tắt, Review 01 (Form 01 PD, 02 CRS-B), Review 02 (03 DFD, 04 ERD, 05 TAB, 06 SM, 07 ALG), Review 03 (08 SD, 09 TD, 10 FC, 11 TS) |
| `_nguon/build_docx.py` | Dựng lại .docx (python-docx 1.2.0). `--pdf` render thử bằng LibreOffice, đo số trang cho mục lục; PDF ghi ra thư mục tạm, **không nộp** |
| `_nguon/noi_dung.py`, `_nguon/mo_ta_bang.py` | Toàn bộ chữ song ngữ; mô tả 31 bảng / 268 cột. 17/11: viết đầy đủ lại 27 câu tiếng Việt trước đây tóm tắt ngắn hơn bản tiếng Anh |
| `_nguon/dich_vi.py` | Bản dịch cho chữ chỉ có tiếng Anh (ca kiểm thử, Task Sheet, số liệu) và toàn bộ nhãn sơ đồ; thiếu nhãn sơ đồ thì `gen_diagrams.py --vi` báo lỗi |
| `_nguon/du_lieu/` | `dump_schema.py` → `schema.json` (đọc models.py), `openapi.json`, `endpoints.txt` (85 route), `pip_versions.txt`, `toc_pages.json` |
| `_nguon/so_do/` | `gen_diagrams.py` + `dot/*.dot` (52 sơ đồ Graphviz đen trắng). `png/` sinh lại bằng script, không commit |
| `_nguon/anh/` | 23 ảnh chụp thật 1440 × 900, scale 2, giao diện sáng |
| `_nguon/kiem_thu/` | `journey.js` (Playwright) và `ket_qua_test_thu_cong.json` (log 27 ca) |
| `_nguon/mau/` | Logo Aptech và khung hoa văn cắt từ file mẫu |

Không còn chữ "EduCenter", tên GV hay tên SV của file mẫu (đã dò bằng `pdftotext` và trong `word/document.xml`: 0 kết quả).

## 2. Chỗ nhóm phải tự điền hoặc ký (ô nền vàng `________`)

1. Bìa: Supervisor, Group No, 3 dòng Full name + Roll No.
2. Trang chứng nhận: 3 dòng tên thành viên, tên GV (Submitted by), Date Of Issue, Authorized Signature.
3. Lời cảm ơn: tên thầy/cô hướng dẫn, số nhóm ở cuối trang.
4. Chân trang của **mọi** trang Form 01–11: Project Group No, tên GV duyệt (Approved by), Signature, Date của sinh viên và giảng viên.
5. Form 09 mục 9.3: "Team re-run by", Date, Signature (Claude đã chạy 27 ca; nhóm cần chạy lại và ký).
6. Form 11 cột "Reviewed by": các dòng repo không ghi người duyệt.

Batch No điền sẵn `T3.2511.M0`, Semester `II`, tháng `November 2026`.

## 3. Nguồn của từng số

| Số trong tài liệu | Nguồn |
|---|---|
| 31 bảng, 268 cột, kiểu, khóa, CHECK | `_nguon/du_lieu/schema.json` sinh từ `backend/app/db/models.py` |
| 85 endpoint | `_nguon/du_lieu/endpoints.txt` (OpenAPI của bản chạy 17/11) |
| 12 route + 404 | `frontend/src/App.tsx` |
| 9 bài hiển thị (+3 nháp), 26 kỹ năng, 73 phiên bản câu đã phát hành, 70 thẻ, 115 khối | `SELECT count(*)` trên CSDL demo Docker 17/11/2026 (`SEED_DEMO_CONTENT=1`) |
| 82 đoạn trong Qdrant | log nạp kho khi khởi động api 17/11 |
| EMA 0,3 / 0,60 / 0,80, Leitner 1-2-4-8-16 | `services/mastery_service.py`, `ai/mastery.py`, `services/review_scheduler.py` |
| Trọng số 0,35/0,25/0,20/0,20, người mới 0,55, k = 10, 14 chiều | `ai/recommender/scoring.py`, `knn.py`, `vector.py` |
| 20 câu/phút, 30 câu/ngày, 6 tin nhắn | `core/ai_config.py`, `core/config.py`, `services/ai_pipeline.py` |
| JWT 30 phút, refresh 7 ngày, khóa 5 lần / 15 phút | `core/config.py`, `auth/login_limiter.py` |
| Mô hình Gemini mặc định | `core/config.py` (`gemini-3.5-flash-lite`, dự phòng `gemini-3.6-flash`, `gemini-embedding-001`) |
| 9 phong cách đệm | `composition/styles` (ORDER) |
| Phiên bản thư viện | `pip freeze` trong image api, `frontend/package.json`, Dockerfile, `docker-compose.yml` |
| RAG HitRate@5 93,0%, MRR 0,848 | `docs/giai-doan/gop-y-thay/G5_BAO_CAO.md` (15/11), không chạy lại |
| Hệ gợi ý P0/P1 | `docs/giai-doan/ai-gd4/BAO_CAO_THUC_NGHIEM.md` (04/11), không chạy lại. Dữ liệu mô phỏng: chưa chứng minh chất lượng với người học thật |
| Task Sheet: ngày bắt đầu / kết thúc | `git log --merges` trên phuc-music (ngày bắt đầu = commit cũ nhất của nhánh PR), PR #1–#62 |
| Người duyệt đã điền ở Task Sheet | bộ nhớ dự án: #11 Phúc xác nhận thay nhóm; #32–#34 Đạt; #36–#42 Thắng + Đạt; #49–#52 Thắng + Đạt |

## 4. Lần chạy thật 17/11/2026 (container Linux cloud, 4 vCPU, 15 GB RAM)

| Bước | Lệnh | Kết quả |
|---|---|---|
| Docker | `docker compose up --build` (5 dịch vụ) | `/api/v1/health` → `{"status":"ok","version":"0.5.4-dev","checks":{"db":"ok","redis":"ok"}}` |
| pytest giống CI | `cd backend && pytest -q -m "not postgres and not live"` | 1.448 đạt, 1 bỏ qua (`test_g3_qdrant::test_tich_hop_may_chu_qdrant_that`, cần `QDRANT_TEST_URL`), 43 loại, 125,75 s, 12:09–12:11 UTC |
| pytest đủ (trước khi tải e5) | `pytest -q` | 1.445 đạt, **1 lỗi** (`test_g5_eval`: bám nguồn 94,5 < baseline 100 vì chưa có mô hình e5), 46 bỏ qua, 102,19 s. Sau `python -m app.ai.local_embedder download` (như CI) thì test này đạt |
| PostgreSQL 16 + pgvector | `TEST_DATABASE_URL=… pytest -m postgres` | 25/25 đạt, 20,92 s |
| Vitest | `cd frontend && npm test` | 282/282 (16 file), 3,18 s |
| Build | `npm run build` | đạt, 6,92 s (cảnh báo chunk > 500 kB, không lỗi) |
| Test thủ công | `node _nguon/kiem_thu/journey.js` | 27/27 đạt, 12:26:43–12:28:39 UTC |

Lưu ý cho lần chạy cloud (không đổi file nào trong repo):

- Docker Hub trả 429, nên kéo image từ `mirror.gcr.io` rồi gắn lại tên gốc (redis, pgvector, qdrant, python:3.11-slim, node:22-alpine, nginx:1.27-alpine).
- Proxy chặn `deb.debian.org`, nên bản build cloud **bỏ bước apt cài tesseract**: không có OCR cho PDF scan trong lần chạy này. Dockerfile trong repo vẫn giữ nguyên.
- CI yêu cầu `--min-passed 1449`; lần chạy local thiếu đúng 1 vì test Qdrant thật bị bỏ qua.
- AI tắt (`AI_ENABLED=false`), không có khóa Gemini: màn hình AI Tutor và AI soạn bài là chế độ dự phòng (đã ghi nhãn trong Form 08).
- Ca TC-24 (MT-23): kịch bản dò chữ "quá nhiều lần", app hiện "sai quá 5 lần". App đúng; đã sửa điều kiện dò và ghi chú trong log. Không sửa code ứng dụng.
- Kịch bản không có TC-10 (hoàn thành bài khi chưa đúng hết); hành vi này do `tests/test_audit_nguoi_moi.py` phủ.

## 5. Chỗ SRS khác code (tài liệu viết theo code)

| SRS 2.1 | Code 1ab6a15 |
|---|---|
| Bảng `courses`, `modules` | Không có; module là cột chữ `lessons.track` (M1–M5) |
| Bảng `lesson_chunks` với `vector(384)` pgvector | Không có; đoạn bài học nằm trong Qdrant (`harmony_knowledge`) hoặc JSON, e5 trong bộ nhớ khi không có Qdrant |
| `users.goal_embedding` kiểu vector | Kiểu JSON, kèm `goal_embedding_model` |
| Redis giữ 6 tin nhắn gần nhất | 6 tin đọc từ PostgreSQL (`chat_messages`); Redis chỉ dùng cho bộ giới hạn đăng nhập |
| Khóa Redis `rl:login:` | `login_fail:{ip}|{email}` |
| docker-compose 4 dịch vụ | 5 dịch vụ (thêm `qdrant`) |
| Endpoint `/courses`, `/quiz/generate`, `/admin/content/import` | Không có; quiz lấy từ ngân hàng câu qua `/practice/quiz` |
| FR-14 AI sinh quiz 10 câu | Chưa làm (hướng phát triển) |
| FR-16 kèm cặp chủ động | Chưa làm |
| `mastery_states` khóa chính (user_id, skill_id) | Khóa chính `id`, ràng buộc duy nhất (user_id, skill_id) |
| `review_states.leitner_box` | Cột `stage` (0..4) + `interval_days` |
| Bảng 14: Đạt biên soạn bài, kiểm thử, báo cáo | `CLAUDE.md` ghi Đạt AI/NLP/DevOps. Task Sheet theo Bảng 14 như đề yêu cầu; nhóm nên thống nhất một bản |
| AI tóm tắt tài liệu thành bài nháp (ADR-025) | Đề bài xếp vào Future scope, nhưng **code đã có** (`source_documents`, `ai_lesson_drafts`, tab "AI soạn bài"). Theo quy tắc "viết theo code", tài liệu mô tả là đã làm, kèm ghi chú: ADR-025 còn trạng thái "đề xuất", chưa thử với Gemini thật trong lần chạy này, phát hành cần Admin bấm |

## 6. Tiêu chí nghiệm thu → bằng chứng

Số MT là số trong Form 09; mã TC là mã trong `journey.js` / log.

| # | Tiêu chí (rút gọn) | Ca thủ công | pytest |
|---|---|---|---|
| 1 | Mật khẩu yếu bị từ chối | MT-03 (TC-03) | `test_auth.py` |
| 2 | Đăng ký đúng → vào kiểm tra đầu vào | MT-02 (TC-02) | |
| 3 | Khóa sau 5 lần sai, 429 | MT-23 (TC-24) | `test_auth.py` |
| 4 | Người học vào /admin → 403, API → 401/403 | MT-21, MT-22 (TC-22, TC-23) | `test_admin_quan_tri.py` |
| 5 | Tài nguyên người khác → 404 | | `test_ai_gd3_tutor_api.py::test_session_of_other_user_is_404` |
| 6 | Đầu vào 12 câu → mastery 0,65 | MT-04 (TC-04) | |
| 7 | D F# A → chỉ ra lỗi quãng 3 | MT-07 (TC-07) | |
| 8 | Sai 2 lần → hiện lời giải | MT-08 (TC-08) | |
| 9 | G# C D# cho Ab → ENHARMONIC_SPELLING | | `test_srs_examples.py` |
| 10 | Công thức EMA 1 / 0,5 / 0 | | `test_cp2_mastery_ema.py` |
| 11 | Hoàn thành khi chưa đúng hết → 409 | | `test_audit_nguoi_moi.py` |
| 12 | Thẻ đến hạn ngay; đúng → hộp 2, sai → hộp 1 | MT-10, MT-12, MT-13 | `test_hm012_leitner.py` |
| 13 | Gợi ý có lý do | MT-15 (TC-16) | `test_ai_gd2_recommend_api.py` |
| 14 | AI tắt vẫn trả lời có trích dẫn | MT-16 (TC-17) | |
| 15 | Tiêm lệnh bị từ chối | MT-17 (TC-18) | `test_ai_gd3_guardrail.py` |
| 16 | Sai Music Engine → thử lại 1 lần rồi dự phòng | | `test_ai_gd3_tutor_api.py` |
| 17 | Lưu vòng Harmony Lab | MT-19 (TC-20) | `test_phuc_music_harmony_lab.py` |
| 18 | Admin sửa chữ = bản nháp, phát hành khi bấm | MT-25 (TC-26) | `test_admin_quan_tri.py` |
| 19 | Lượt Admin `is_test`, không đổi mastery | | `test_cp2_mastery_scope.py::test_s13_admin_attempt_is_test_and_no_mastery` |
| 20 | `docker compose up` → 5 dịch vụ, health ok | lần chạy mục 4 | |

## 7. Chạy lại

```bash
# 1. Sơ đồ (cần Graphviz `dot`) và lược đồ bảng
python docs/review123/_nguon/du_lieu/dump_schema.py
python docs/review123/_nguon/so_do/gen_diagrams.py
# 2. Dựng .docx; --pdf render thử bằng LibreOffice và cập nhật số trang mục lục
pip install python-docx==1.2.0 pillow
python docs/review123/_nguon/build_docx.py --pdf
# Bản thuần tiếng Việt: sơ đồ nhãn Việt (so_do/png_vi/) rồi dựng file _TiengViet.docx
python docs/review123/_nguon/so_do/gen_diagrams.py --vi
python docs/review123/_nguon/build_docx.py --vi --pdf
# 3. Chụp màn hình + test thủ công (CSDL mới, app ở :5173, cần Playwright)
docker compose down -v && docker compose up -d --build
docker compose exec -e ADMIN_PASSWORD='<mật khẩu admin demo>' api python -m app.seed_admin --email admin@harmony.demo
LPW='<mật khẩu người học demo>' APW='<mật khẩu admin demo>' node docs/review123/_nguon/kiem_thu/journey.js shots tc_log.json
```

Mật khẩu demo không ghi trong repo; `journey.js` đọc qua biến môi trường `LPW`, `APW`.
Mở .docx bằng Word: mục lục đã có số trang; nếu sửa nội dung thì chuột phải mục lục → Update Field.

## 8. Rủi ro và câu hỏi cho nhóm

1. Kết quả hệ gợi ý (GĐ4) cho thấy ngưỡng hiện tại làm 97% danh sách luật rỗng trên dữ liệu mô phỏng. Tài liệu ghi đúng như báo cáo; chưa chứng minh chất lượng với người học thật.
2. Test thủ công do Claude chạy; giảng viên có thể yêu cầu nhóm tự chạy lại và ký.
3. Phân công Bảng 14 khác `CLAUDE.md` (mục 5). Nếu nhóm muốn theo `CLAUDE.md`, sửa cột Owner trong `noi_dung.py` (TEAM, PLAN, TASKS) rồi dựng lại.
4. Bản build cloud không có OCR; trên máy nhóm Dockerfile gốc vẫn cài tesseract.
5. Chưa có video demo và chữ ký (Form 10).

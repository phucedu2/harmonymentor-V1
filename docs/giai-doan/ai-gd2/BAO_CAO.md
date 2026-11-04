# Báo cáo GĐ2 pipeline AI: hệ gợi ý 3 tầng (luật, nội dung, cộng tác)

Nhánh `ai/gd2-goi-y`, xếp chồng trên `ai/gd1-mastery` (PR #21). Draft PR #22, đích `phuc-music`. Không merge.
Bám 04 mục 6.5, ADR-008 bản 4, hợp đồng test CP2 (nhóm V, K, C, R), G-3 cách B (Thắng chốt 31/10) và quyết định 8A, 9A của Phúc (04/11).
Các điểm "chờ Thắng" của ADR-008 (D-2, R-1, ngưỡng số chiều chung) được làm thành cấu hình, ghi rõ là đề xuất.

## A. Đã làm (đã chạy thật)

1. **Lõi gợi ý gồm các hàm thuần** trong `backend/app/ai/recommender/`. Các hàm này không đọc CSDL và không gọi mạng, nên GĐ4 dùng lại được cho thử nghiệm.
   - `vector.py`: vector `(value, assessed)` 14 chiều. Kỹ năng chưa đánh giá không bị tính là 0 (V3). Kỹ năng post_mvp bị bỏ qua (V5). `build_pool` dựng 2.000 ứng viên thành ma trận numpy.
   - `knn.py`:
     - Cosine chỉ tính trên chiều mà cả hai người đã đánh giá.
     - Cặp có độ dài 0 trên chiều chung bị loại với lý do `zero_norm` (Q-5).
     - Ngưỡng số chiều chung là tham số. Có dự phòng (a) và (b).
     - Lấy top 10, sắp theo độ tương đồng giảm dần, bằng nhau thì theo `user_id` (K10).
     - Có thêm Jaccard độ trùng kỹ năng, chỉ để báo cáo (3b).
   - `cf.py`: cf là tỷ lệ láng giềng có mastery ≥ 0,60. Mẫu số là số láng giềng hợp lệ (tối đa 10), kể cả láng giềng chưa làm kỹ năng đó (D-2). `mastery_as_of` lấy điểm ngay trước mốc thời gian, mốc chặt, để GĐ4 chống rò rỉ.
   - `scoring.py`:
     - Công thức đầy đủ 0,35 / 0,25 / 0,20 / 0,20. Khi không có láng giềng hợp lệ thì dùng công thức người học mới 0,55 / 0,25 / 0,20.
     - Điểm bài là trung bình trên các kỹ năng chưa thành thạo (bước 6).
   - `engine.py`:
     - Bước 1 lọc theo luật. Lý do loại: `no_mvp_skill`, `all_mastered`, `prereq_not_ready`. Kỹ năng chưa đánh giá được coi là 0 ở bước lọc.
     - Trả tối đa k ≤ 5 bài, không lặp. Có cờ `few_eligible` (R-1). Bằng điểm thì theo thứ tự chương trình.
   - `reasons.py`: lý do lấy từ tầng đóng góp nhiều điểm nhất, theo mẫu câu cố định (không dùng LLM), kèm huy hiệu "Theo mục tiêu", "Cần ôn tập", "Củng cố kỹ năng" hoặc "Phù hợp trình độ".
   - `content.py`: điểm nội dung là cosine giữa vector mục tiêu và vector mô tả kỹ năng, kẹp về [0, 1]. Khi không có embedding thì dùng TF-IDF ký tự cục bộ, có nhãn `tfidf`.
2. **Embedding** (`app/ai/embedder.py`):
   - `GeminiEmbedder` (SDK `google-genai`): chuẩn hóa vector về độ dài 1. Mọi lỗi được đổi thành `EmbeddingUnavailable`, và khóa không nằm trong `repr`.
   - `FakeEmbedder` cho test: tất định, không gọi mạng.
   - `CachedEmbedder`: đệm theo hash (mô hình, tác vụ, văn bản).
   - `get_embedder` trả `None` khi `AI_ENABLED=false` hoặc thiếu khóa.
3. **Mô tả kỹ năng** (`app/content/skill_descriptions.json`): 26 mô tả nháp (`status: draft`, có nguồn), Claude soạn theo 6A, chờ Đạt/Astra duyệt.
   - 13 vector của kỹ năng MVP đã tính bằng Gemini thật (`gemini-embedding-001`, 768 chiều, đã chuẩn hóa) bằng lệnh `python -m app.ai.build_skill_embeddings`, lưu ở `skill_embeddings.json` kèm hash của mô tả. Sửa mô tả mà quên tính lại thì test báo.
   - Mô tả nháp chỉ được dùng khi bật `ALLOW_DRAFT_SKILL_DESCRIPTIONS=1`. `APP_ENV=production` chặn cờ này, đúng quy tắc "không đưa nháp vào gợi ý". Khi chưa duyệt, tầng nội dung ở production trả `content_source: "none"`.
4. **Dịch vụ và API** (`services/recommendation_service.py`, `api/ai_recommend.py`):
   - `GET /api/v1/recommend?k=1..5` trả 3 danh sách theo G-3 cách B:
     - `continue`: bài đang học dở, chỉ để điều hướng.
     - `next`: bài chưa bắt đầu.
     - `review`: bài đã hoàn thành, nhãn "Ôn lại".
   - Kèm theo:
     - `weights_mode`.
     - `cf_source` (`real` / `synthetic` / `none`, theo 9A).
     - `fallback_reason`, `min_shared_dims`, `neighbors_count`.
     - `content_source`, `draft_descriptions`, `few_eligible`, `log_id`.
   - `POST /api/v1/recommend/{log_id}/click`: ghi lượt bấm để đo ở GĐ5. Nhật ký của người khác trả 404. Bài không có trong lần gợi ý trả 422.
   - `GET` và `PUT /api/v1/me/goal`: tối đa 500 ký tự, chuỗi rỗng thì xóa mục tiêu. Chỉ gửi văn bản mục tiêu cho Gemini, có test kiểm payload (03 Bảng 3).
   - Mỗi lần gợi ý ghi một dòng `recommendation_logs`.
5. **Giao diện**: thẻ "Gợi ý cho bạn" trên Dashboard (`components/learning/RecommendedLessons.tsx`).
   - Có 3 mục, mỗi bài có huy hiệu, lý do và phần "Vì sao gợi ý bài này?" hiện 4 thành phần điểm.
   - Có ô sửa mục tiêu. Nút "Mở bài" ghi lượt bấm rồi mở thẳng bài qua `/app/hoc?bai=L0x`.
6. **Hiệu năng (E11)**: với 2.000 người mô phỏng, đo 50 lần trên máy cloud bằng SQLite, cho kết quả trung vị 70 ms và p95 159–162 ms (yêu cầu ≤ 200 ms). Lần đo đầu được p95 191 ms, sau khi chuyển sang dựng ma trận numpy và chỉ lấy mastery của tối đa 10 láng giềng thì còn 159–162 ms. GĐ4 sẽ đo lại trên máy CI.

## B. File

| Nhóm | File |
|---|---|
| Lõi thuần | `backend/app/ai/recommender/{__init__,vector,knn,cf,scoring,reasons,content,engine}.py` |
| Embedding | `backend/app/ai/embedder.py`, `backend/app/ai/build_skill_embeddings.py` |
| Nội dung | `backend/app/content/skill_descriptions.{json,py}`, `backend/app/content/skill_embeddings.json` |
| Dịch vụ, API | `backend/app/services/recommendation_service.py`, `backend/app/api/ai_recommend.py`, `backend/app/api/router.py`, `backend/app/contracts/ai.py` |
| CSDL | `backend/app/db/models.py` (`User.goal_embedding`, `goal_embedding_model`, `RecommendationLog`), `backend/migrations/versions/20261104_ai_gd2_recommend.py`, `backend/app/db/session.py` (báo CSDL cũ) |
| Cấu hình | `backend/app/core/config.py`, `.env.example`, `backend/requirements.txt` (numpy, scikit-learn, google-genai), `backend/pytest.ini` (dấu `live`) |
| Test | `test_ai_gd2_vector_knn.py`, `test_ai_gd2_cf_scoring.py`, `test_ai_gd2_recommend_api.py`, `test_ai_gd2_embedder_content.py`, `test_ai_gd2_migration.py`, `test_ai_gd2_live.py`; sửa `test_ai_gd1_migration.py` (head đổi) |
| Frontend | `frontend/src/components/learning/RecommendedLessons.tsx`, `pages/Dashboard.tsx`, `pages/Learn.tsx` (`?bai=`), `api.ts` |
| Script, ảnh | `scripts/ai/gd2_do_thoi_gian.py`, `docs/minh-chung/anh/ai-gd2/goi-y-{may-tinh,dien-thoai}.png`, `goi-y-mo-bai-*.png` |
| CI | `.github/workflows/ci.yml`: bỏ nhóm `live`, mức tối thiểu 742 |

## C. Lệnh và kết quả (04/11/2026, máy cloud)

```bash
cd backend && python -m pytest -q -m "not postgres and not live"   # 742 passed, 24 deselected
cd backend && python -m pytest -q tests/test_ai_gd2_*.py           # 95 passed, 3 skipped (live)
cd backend && RUN_LIVE=1 AI_ENABLED=1 GEMINI_API_KEY=... python -m pytest -q -m live tests/test_ai_gd2_live.py   # 3 passed
cd backend && python ../scripts/ai/gd2_do_thoi_gian.py --n 2000 --lan 50   # trung vị ~70 ms, p95 ~160 ms
cd frontend && npm test && npm run build                           # Vitest 259 passed; build đạt
```

- CI: commit chỉ có test (`e1c6405`) được đẩy trước để CI đỏ, sau đó là code. Sau commit đỏ có 3 chỗ trong test phải sửa, ghi rõ ở commit `69b9447`:
  1. Bảng 21 của 04 làm tròn từng số hạng trước khi cộng (L09: 0,1085 được làm tròn thành 0,109), nên sai số cho phép nới thành 0,001.
  2. Ca "due": khi mastery = 0 thì tầng `(1 − mastery)` (0,25) lớn hơn tầng due (0,20), nên test phải đặt mastery 0,5.
  3. Lỗi kiểm tra đầu vào của dự án trả 400 chứ không phải 422.
- PostgreSQL: chạy `alembic upgrade head` và `check` trong job PostgreSQL của CI. Máy cloud không có PostgreSQL nên chưa chạy ở đây.
- **Gemini thật**: dùng khóa Phúc gửi, chỉ đặt trong file tạm của phiên, không vào repo. Bảng dưới là top 3 kỹ năng theo cosine:

| Mục tiêu | Gemini (embedding) | TF-IDF dự phòng |
|---|---|---|
| Mình muốn đệm hát nhạc pop bằng guitar | triad_build 0,721; function.progression 0,676; seventh_build 0,650 | triad_build 0,315; seventh_quality 0,132; function.dominant 0,121 |
| Tôi muốn chơi piano jazz | ii_v_i 0,671; triad_build 0,661; seventh_build 0,648 | triad_build 0,198; function.dominant 0,121; seventh_quality 0,106 |
| Học đọc tên nốt thăng giáng trên bản nhạc | pitch.spelling 0,779; interval.naming 0,692; scale.major 0,672 | pitch.spelling 0,428; triad_build 0,236; seventh_build 0,200 |
| Sáng tác vòng hợp âm cho bài hát | function.progression 0,746; triad_build 0,724; scale.major 0,708 | function.progression 0,461; function.predominant 0,210; function.tonic 0,197 |

- **Giao diện**: chạy thật với backend có `AI_ENABLED=1`, rồi dùng Playwright ở khổ 1280 px và 390 px.
  - Luồng: đăng ký, bỏ qua bài kiểm tra đầu vào, nhập mục tiêu "đệm hát nhạc pop bằng guitar", thấy L01 với nhãn "Theo mục tiêu" và độ hợp mục tiêu 63% (CSDL ghi `content_source = embedding`), bấm "Mở bài" thì vào thẳng Bài 1.
  - Console có một lỗi 401: đó là lượt làm mới phiên khi tải lại trang, đã có từ trước GĐ2.

## D. Thay đổi API và CSDL

- **Migration `d2b3c4d5e6f7`** chỉ thêm, có hạ phiên bản đầy đủ và có test.
  - `users.goal_embedding` (JSON) và `users.goal_embedding_model`. ERD 04 ghi `vector(384)` cho MiniLM. Gemini trả 768 chiều, và mô hình còn có thể đổi (Q-B), nên lưu JSON kèm tên mô hình. Tầng nội dung chỉ so hai vector cùng mô hình. Khác mô hình thì dùng TF-IDF.
  - Bảng `recommendation_logs` theo ERD 04, thêm `context` (cấu hình đã dùng) và `clicked_at`.
- **Cấu hình mới**:
  - `AI_ENABLED`, `GEMINI_API_KEY`.
  - `EMBEDDING_MODEL=gemini-embedding-001` và `EMBEDDING_DIM=768` (giữ tên biến theo 03).
  - `ALLOW_DRAFT_SKILL_DESCRIPTIONS`.
  - `REC_MIN_SHARED_DIMS=3` (tạm), `REC_FALLBACK=a`, `REC_NEIGHBORS_K=10`.
  - `KNN_REAL_MIN_USERS=30`, `KNN_REAL_MIN_DIMS=3`.
- **Cần làm trên máy Phúc**: file `.env` cũ có `EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2`. Phải đổi sang `gemini-embedding-001`. Nếu không, Gemini báo lỗi và tầng nội dung tự lùi về TF-IDF. Hệ thống không hỏng, nhưng gợi ý kém hơn.

## E. Giải thích cho nhóm

- **Ví dụ người học mới.** Người này chưa có kỹ năng nào được đánh giá, nên hệ thống không tìm láng giềng (`fallback_reason: no_assessed_dims`) và dùng công thức 0,55 / 0,25 / 0,20. L02 trở đi bị luật chặn vì kỹ năng tiên quyết còn 0, nên chỉ L01 được gợi ý và cờ `few_eligible` bật. Khi đã có mục tiêu, tầng nội dung đóng góp nhiều nhất (0,55 × 0,63 > 0,25), nên lý do là "Phù hợp với mục tiêu…".
- **Tầng cộng tác hiện chạy trên người mô phỏng.** Theo 9A, khi có ít hơn 30 người học thật có từ 3 chiều trở lên thì tầng cộng tác dùng người mô phỏng, và API ghi `cf_source: synthetic`. Hiện CSDL chưa có người mô phỏng (GĐ4 mới sinh), nên trên máy thật mọi người đều đi nhánh dự phòng (a). Đây là hành vi đúng theo ADR-008, không phải lỗi.
- **Không dùng `sklearn.NearestNeighbors` như bản pipeline gợi ý.** Ma trận của sklearn coi chiều chưa đánh giá là 0. ADR-008 lại yêu cầu tính cosine trên tập chiều chung riêng của từng cặp. Vì vậy phần này tự viết bằng numpy, có test K1 với số liệu của hợp đồng (0,8324 và 0,7894). scikit-learn chỉ dùng cho TF-IDF.
- **Điểm nội dung tính theo kỹ năng, không theo bài.** 04 mục 6.5 bước 2 ghi "vector mô tả kỹ năng". Pipeline của giảng viên ghi "vector bài học". Mình làm theo 04 vì tài liệu 2.1 thắng. Điểm của bài là trung bình trên các kỹ năng chưa thành thạo, giống mọi tầng khác.
- **Tiên quyết của L04 có `chord.seventh_quality`.** Theo 04, "kỹ năng của bài lấy từ skill_id của các câu". L04-Q03 gắn `voicing.guide_tones` (post_mvp), mà kỹ năng này cần `chord.seventh_quality`. Vì vậy L04 bị chặn tới khi `seventh_quality` đạt 0,60, khớp với mô phỏng GĐ0.

## F. Câu hội đồng có thể hỏi

- *"Sao người dùng thật lại được gợi ý từ dữ liệu giả?"* Chỉ khi có ít hơn 30 người thật đủ dữ liệu (9A). API và giao diện đều ghi rõ "dữ liệu mô phỏng". Khi đủ người thật, hệ thống tự chuyển sang người thật.
- *"Gemini lỗi thì sao?"* Embedding lỗi thì dùng TF-IDF cục bộ. Tắt AI thì vẫn gợi ý được bằng luật, mastery, lịch ôn và cộng tác. Có test với `AI_ENABLED=false` và test bảo đảm không gọi mạng trong CI.
- *"Gửi gì cho Google?"* Chỉ văn bản mục tiêu người học tự nhập và 26 mô tả kỹ năng công khai. Không gửi tên, email hay user_id. Có test kiểm payload.
- *"Vì sao cosine của Gemini đều 0,59–0,78?"* Mô hình embedding cho mọi đoạn văn tiếng Việt cùng chủ đề nhạc lý một mức tương đồng nền cao. Xem đề xuất P-2 ở mục G.

## G. Việc tiếp theo và người duyệt

| Mã | Ai | Việc |
|---|---|---|
| Q-E | Thắng | Duyệt migration `d2b3c4d5e6f7` (thêm 2 cột vào `users` và bảng `recommendation_logs`, lưu JSON thay vì `vector(384)`). Gộp với Q-D của GĐ1 |
| D-2, R-1 | Thắng | Đã cài đúng đề xuất ADR-008 dưới dạng cấu hình. Nếu Thắng chọn khác thì chỉ đổi `cf.py` hoặc `engine.py` và test, không đổi API |
| P-1 | Thắng | `REC_MIN_SHARED_DIMS=3` và dự phòng (a) là giá trị tạm. GĐ4 chạy đủ 6 cấu hình rồi mới chốt bằng ADR bổ sung |
| P-2 | Thắng | **Đề xuất, chưa làm**: cosine Gemini nằm trong khoảng 0,59–0,78, nên tầng nội dung chỉ làm điểm chênh khoảng 0,04–0,10 giữa kỹ năng hợp nhất và kém hợp nhất (0,35 hoặc 0,55 × 0,19). Có thể co giãn min–max theo từng người học trước khi nhân 0,35. Làm vậy là đổi công thức 04, nên cần Thắng duyệt và số liệu GĐ4 |
| Q-F | Đạt / Astra | Duyệt 26 mô tả kỹ năng (`skill_descriptions.json`). Mô tả nào duyệt xong thì đổi `status` sang `approved`, rồi chạy `build_skill_embeddings` nếu có sửa chữ. Chưa duyệt thì production chưa có tầng nội dung |
| Q-G | Phúc | Xem thẻ "Gợi ý cho bạn" (ảnh ở `docs/minh-chung/anh/ai-gd2/`). Đổi `EMBEDDING_MODEL` trong `.env` máy mình |
| Tiếp | Claude | GĐ3 AI Tutor (RAG, guardrail Music Engine, giải thích lỗi) trên nhánh `ai/gd3-tutor` xếp chồng, làm trong lúc chờ duyệt (10A) |

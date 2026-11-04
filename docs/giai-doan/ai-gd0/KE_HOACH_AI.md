# Kế hoạch triển khai pipeline AI (GĐ0)

Ngày 04/11/2026. Nhánh `ai/gd0-ke-hoach` tách từ `phuc-music` 79564d8. Giai đoạn này không viết code chạy cho người dùng: chỉ kiểm hiện trạng, chạy mốc test, chạy một script mô phỏng và lập kế hoạch.

Nguồn đã đọc: pipeline của thầy (`docs/tham-khao/PIPELINE_TRIEN_KHAI_AI_RECOMMENDER.md`), 04 mục 3.6, 6.3–6.6 và 8.4, 03 Bảng 3, ADR-001..013 trên `phuc-music`, ADR-008 cùng `CP2_ANH_XA_KY_NANG.md` trên PR #17, PR #14, `docs/phuc-music/`, `TIEN_DO.md`, `AI_USAGE.md`, `CI.md`.

Câu trả lời của Phúc cho 12 câu làm rõ (04/11 03:21): `1A 2A 3A 4 (đưa khóa) 5A 6A 7A 8A 9A 10A 11A 12A`. Bản câu hỏi nằm ở `/mnt/project-files/harmonymentor-ai-pipeline/CAU_HOI_LAM_RO_GD0.md`.

---

## 1. Kết quả kiểm tra thật

### 1.1. Git, PR, CI

| Mục | Kết quả |
|---|---|
| `phuc-music` | 79564d8, giống mô tả trong prompt. Head Alembic `b8d5e6f7a9c1` (cấu trúc bài hát), có `practice_attempts`. |
| PR mở | #12 (B#/Cb, đã gộp vào phuc-music), #14 (Leitner), #15 (piano), #16 (logo, đã gộp vào phuc-music), #17 (ADR-008, chỉ tài liệu), #18 (phuc-music → main), #19 (trang chủ thử nghiệm). Tất cả đích `main`. |
| Cherry-pick thử PR #17 (5 commit 9a2dc8f → e2ce120) lên phuc-music | Sạch, chỉ thêm `ADR-008`, `CP2_ANH_XA_KY_NANG.md`, `CP2_HOP_DONG_TEST.md`, 5 dòng ADR-003. |
| Cherry-pick thử PR #14 (f3bd6a4, 2e9fb70) | Code và test áp sạch (`review_scheduler.py` và 3 file test). Xung đột ở 4 file tài liệu/số: `ci.yml` (mức `--min-passed`), `CLAUDE.md`, `AI_USAGE.md`, `TIEN_DO.md`. Giải tay ở GĐ1. |
| CI | `ci.yml` chỉ bắt PR vào `main`. Theo câu 3A, nhánh này thêm `phuc-music` vào `pull_request.branches` (một dòng, không đổi job, không đụng ruleset `bao-ve-main`). |

### 1.2. Mốc test (chạy 04/11/2026 trên máy cloud, Python 3.13, Node 22)

| Lệnh | Kết quả |
|---|---|
| `cd backend && python -m pytest -q` | **592 passed, 21 skipped** (21 test PostgreSQL cần `TEST_DATABASE_URL`, CI chạy riêng) |
| `cd frontend && npm ci && npm run build` | Đạt (`built in 4.60s`, chỉ có cảnh báo kích thước chunk) |
| `cd frontend && npx vitest run` | **259 passed** / 9 file |

### 1.3. Nội dung và bế tắc tiên quyết (C1)

Lệnh: `python scripts/ai/gd0_mo_phong_mo_khoa.py`. Kết quả đầy đủ: [`mo_phong_mo_khoa_2026-11-04.md`](mo_phong_mo_khoa_2026-11-04.md).

Kỹ năng tiên quyết (đọc từ `skill_graph.PREREQUISITES`, tuple là `(kỹ năng, tiên quyết của nó)`):

| Bài | Tiên quyết ngoài bài | Câu | Thẻ máy chấm | Thẻ tự đánh giá |
|---|---|---|---|---|
| L02 | `pitch.spelling` | 1 | **0** | 1 |
| L02 | `chord.triad_build` | 3 | 3 | 0 |
| L03 | `roman.major_seventh` | 1 | 4 | 0 |
| L04 | `chord.seventh_quality` | 2 | **0** | 1 |
| L04 | `chord.seventh_build` | 2 | 2 | 0 |
| L04 | `function.progression` | 3 | 1 | 1 |

Ngày đầu tiên bài đủ điều kiện cho hệ gợi ý, với người làm đúng 100%, tự mở bài theo thứ tự mỗi ngày một bài (tầng 1 chỉ gợi ý, không khóa bài), mô phỏng 90 ngày:

| Kịch bản | L02 | L03 | L04 | pitch.spelling cuối kỳ | seventh_quality cuối kỳ |
|---|---|---|---|---|---|
| Chỉ câu bài tập (hiện trạng) | không | không | không | 0,300 | 0,510 |
| 2A (thẻ máy chấm đến hạn, tối đa 1 lượt/kỹ năng/ngày) | không | ngày 3 | không | 0,300 | 0,510 |
| 2A + 1A (thẻ tự đánh giá tính 0,5) | không | ngày 3 | không | 0,488 | 0,501 |
| 2A không giới hạn mỗi ngày (so sánh) | không | ngày 1 | không | 0,300 | 0,510 |

**Phát hiện quan trọng về 1A.** Lúc hỏi, mình viết rằng phương án 1A giúp pitch.spelling tăng "chậm". Mô phỏng cho thấy mình sai: EMA với kết quả 0,5 chỉ kéo điểm **về 0,5**, không bao giờ vượt 0,5. Vì vậy 1A không bao giờ mở được L02 (pitch.spelling dừng gần 0,49), và còn **kéo seventh_quality từ 0,51 xuống 0,50**. Ví dụ tính tay: 0,51 + 0,3 × (0,5 − 0,51) = 0,507. Mình đề xuất không bật 1A (chi tiết ở mục 7, Q-A).

Kết luận cho báo cáo:
- Với nội dung hiện có, chỉ **bài kiểm tra đầu vào (0,65)** mới đưa L02 và L04 vào danh sách gợi ý. Tài khoản demo cần lịch sử placement.
- 2A gỡ được L03 vào ngày thứ 3 (L02 học ngày 1: 0,30 → ôn ngày 1: 0,51 → ôn ngày 3: 0,657). Giới hạn 1 lượt/kỹ năng/ngày (2A) chặn cày điểm: không có giới hạn này thì 4 thẻ của roman.major_seventh đưa điểm lên 0,83 ngay trong ngày 1.
- Gỡ thật cần M19 (Thắng chốt 31/10, Astra soạn câu). Ít nhất 2 câu cho pitch.spelling và 1–2 câu (hoặc 1 thẻ máy chấm) cho seventh_quality.

### 1.4. Gemini (C3), kiểm bằng khóa thật ngày 04/11/2026

Trang `ai.google.dev` bị mạng của môi trường cloud chặn, nên bằng chứng chính là API `models.list` (câu 5A). Khóa chỉ nằm trong file tạm ngoài repo, không vào commit, log hay memory.

| Mục | Kết quả |
|---|---|
| `models.list` | Có `gemini-3.5-flash-lite` (bản `3.5-flash-lite-07-2026`), `gemini-3.6-flash` (`3.6-flash-07-2026`), `gemini-embedding-001`, `gemini-embedding-2` (bản chính thức), `gemini-embedding-2-preview`. Danh sách không còn `gemini-1.5-*`, `gemini-2.0-flash`, `text-embedding-004`. |
| Sinh văn bản, JSON schema, `gemini-3.5-flash-lite` | Đạt, 0,95 giây, 91 token. Trả `{"reply": "Hợp âm C7 (Đô bảy) gồm các nốt Đô (C), Mi (E), Sol (G) và Si giáng (Bb).", "notes": ["C","E","G","Bb"]}`, đúng với Engine. |
| `gemini-3.6-flash` | **Lỗi 503 "high demand"** ở lần gọi thử. Đây là bằng chứng thật cho việc phải có thử lại 1 lần và dự phòng theo luật. |
| `gemini-embedding-001`, `outputDimensionality=768`, `RETRIEVAL_QUERY` | Đạt, 768 số, **độ dài vector 0,586 (chưa chuẩn hóa)**. Code phải tự chuẩn hóa về độ dài 1 trước khi tính cosine và lưu. Giới hạn đầu vào 2.048 token, nên đoạn 80–100 từ không bị cắt (khác MiniLM 128 token của 04 mục 6.6). |
| `gemini-embedding-2`, 768 chiều | Đạt, vector đã chuẩn hóa (độ dài 1,0). Giới hạn đầu vào 8.192 token. |
| Gói SDK | `google-genai` có trên PyPI, bản mới nhất 2.34.0. |
| Giới hạn gói miễn phí | **Chưa đọc được** (chỉ có trong AI Studio). Cần Phúc chụp màn hình trang Rate limits của khóa (câu 5A). `AI_DAILY_BUDGET` để trống tới khi có số. |

Đề xuất cho ADR-014: mặc định `gemini-embedding-001` như prompt đã chọn. Ghi `gemini-embedding-2` là phương án thay thế đã ra bản chính thức, chọn sau khi đo Recall ở GĐ4 (mục 7, Q-B).

---

## 2. Bảng trạng thái module

| Module | Hiện trạng trên phuc-music | Giai đoạn làm |
|---|---|---|
| Ánh xạ kỹ năng (`group_code`, `srs_code`, ngưỡng) | Chưa có cột; bảng ánh xạ chỉ có trong PR #17 | GĐ1 |
| Mastery EMA, `mastery_states` | Chưa có. `attempts` có `correct`, `score`, `primary_error`, `exercise_version_id`; **không có `is_test`, `assisted`, `response_time_ms`** | GĐ1 |
| Leitner ôn trước hạn | Có ở PR #14, chưa có trên phuc-music | GĐ1 (cherry-pick) |
| Ôn tính mastery (2A) | Chưa có. `review_attempts` có `response_time_ms` | GĐ1 |
| Bài kiểm tra đầu vào | Chưa có | GĐ1 |
| Mô tả 26 kỹ năng | Chưa có trường mô tả | GĐ1 (nháp, câu 6A) |
| Gợi ý 3 tầng + API + thẻ Dashboard | Chưa có | GĐ2 |
| Embedding, `LLMProvider`, FakeEmbedder/FakeLLM | Chưa có. Có `AI_ENABLED=false`, `GEMINI_API_KEY=` trong `.env.example`; pgvector đã bật bằng migration `b2` | GĐ2 (embedder), GĐ3 (LLM) |
| RAG, guardrail, chat, giải thích lỗi | Chưa có. Engine có `tools.py`, `claims.py`, 14 mã lỗi | GĐ3 |
| Giới hạn lượt AI Tutor | Redis chỉ dùng cho khóa đăng nhập (`auth/login_limiter.py`); cần thêm bộ đếm mới | GĐ3 |
| Phân loại ý định cục bộ | Chưa có (câu 7A: TF-IDF ký tự + Logistic Regression) | GĐ3 |
| Đánh giá gợi ý, đánh giá RAG | Chưa có | GĐ4 |

Kho tri thức RAG: L01–L04 có 44 khối (L01 14, L02 10, L03 9, L04 11), L05–L08 có 0 khối. Khối dài nhất khoảng 450 từ. Ước tính 40–60 đoạn sau khi chia 80–100 từ; GĐ3 đếm chính xác. Bài ở cấp bài có trạng thái `reviewed`/`source_audited`, còn câu hỏi có `published`/`draft`, nên "bài đã xuất bản" sẽ định nghĩa là bài có `status = reviewed` và có ít nhất một câu `published` (ghi trong ADR GĐ3). L02-B05 (giải nghĩa maj7, 7) là khối đúng cho câu nghiệm thu "C7 khác Cmaj7 thế nào?".

---

## 3. Đối chiếu pipeline của thầy với tài liệu 2.1 và ADR

| # | Pipeline nói | 2.1 / ADR / hiện trạng | Cách xử lý |
|---|---|---|---|
| D1 | Ví dụ L03: due = 1 → 0,447 | Bảng 21 của 04 dùng due = 0. Với due = 1 điểm đúng là 0,647 và L03 xếp trên L10 (0,548) | Test cả hai ca. Ghi "Góp ý gửi thầy" (C2) |
| D2 | Điểm tính thẳng theo bài | 04 mục 6.5 bước 5–6: tính theo kỹ năng rồi lấy trung bình trên kỹ năng chưa thành thạo | Làm theo 04 |
| D3 | `content` so với mô tả **bài** | 04: so với mô tả **kỹ năng** | Làm theo 04; mô tả kỹ năng là nháp (6A) |
| D4 | Embedding `text-embedding-004` hoặc MiniLM 384 chiều | 03/04: MiniLM cục bộ 384 chiều, 128 token. Prompt (C4): Gemini API | ADR-014 ghi lệch SRS 03. `text-embedding-004` đã tắt nên không dùng |
| D5 | `gemini-1.5-flash`/`2.0-flash` | Đã ngừng | Dùng `gemini-3.5-flash-lite`, dự phòng `gemini-3.6-flash`, đọc từ biến môi trường |
| D6 | 14 nhóm `note_reading`… `song_form` | ADR-008: 14 nhóm khác tên (bảng mục 4) | Dùng ADR-008, báo cáo có bảng đối chiếu |
| D7 | Đoạn 80–120 từ | 04 mục 6.6: 80–100 từ | Làm 80–100 |
| D8 | JSON `explanation`, `music_claims` dạng câu chữ | 04 Bảng 13: `reply`, `citations`, `engine_claims`, `hint_level`, `suggested_actions`, `quiz`, `intent`; claim có cấu trúc | Làm theo 04; claim có cấu trúc để Engine kiểm |
| D9 | Claim sai → thay bằng câu trong `errors.py` | 04 mục 6.6: soạn lại 1 lần, vẫn sai thì dự phòng | Làm theo 04; dự phòng dựng từ Engine + đoạn bài học |
| D10 | 12 bài, 60 đoạn, ví dụ L09/L10 | Chỉ L01–L04 có nội dung chạy; L09–L12 là nháp | Không đưa nháp vào RAG/gợi ý; ví dụ dùng L01–L04 (C8) |
| D11 | Người mới chưa có lịch sử: bỏ tầng 3 | 04 giống vậy; ADR-008 thêm `zero_norm` và cf rỗng | Làm theo ADR-008 |
| D12 | `cf` = tỷ lệ láng giềng "học tốt bài tiếp theo" | 04: theo kỹ năng; ADR-008 mục 4 định nghĩa S0/S1/S2 (chờ Thắng) | Cờ cấu hình, mặc định theo ADR-008 bản 4 (8A) |
| D13 | Lịch: Đạt viết recommender 04–05/11 | Phân công project: Thắng phụ trách gợi ý; prompt: Claude làm | Claude làm, Thắng duyệt thuật toán, Đạt duyệt nội dung |
| D14 | HitRate/Precision@5 là chỉ số chính | Chỉ 4 bài chạy, @5 gần bão hòa (C6) | Báo đủ @5 theo SRS; chọn cấu hình theo @1, @3, MRR |
| D15 | Retention Predictor dùng `response_time_ms` | Chỉ `review_attempts` có cột này, `attempts` không có | GĐ6 dùng trên lượt ôn |
| D16 | Không nói về `assisted` | 04 mục 6.3: "đúng sau gợi ý" = 0,5. `attempts` chưa có cột | GĐ1 thêm `attempts.assisted` (migration chỉ thêm) |

---

## 4. Đối chiếu 14 nhóm kỹ năng (C5)

| # | ADR-008 | Pipeline | Khớp | Có dữ liệu với L01–L04 |
|---|---|---|---|---|
| 1 | note_names | note_reading | khớp | không (chưa có kỹ năng) |
| 2 | accidentals | (gộp trong note_reading) | một phần | **có** (pitch.spelling) |
| 3 | intervals | interval_calc | khớp | **có** |
| 4 | major_scales | scale_major | khớp | **có** |
| 5 | minor_scales | scale_minor | khớp | không |
| 6 | triads | triad_build | khớp | **có** |
| 7 | seventh_chords | seventh_build | khớp | **có** |
| 8 | diatonic_chords | roman_numeral | khớp | **có** |
| 9 | progressions | cadence | khớp | **có** |
| 10 | rhythm_basics | rhythm_basic | khớp | không |
| 11 | chromatic_harmony | secondary_dominant + modal_interchange | pipeline tách 2 | không (post_mvp) |
| 12 | pop_harmony | không có | không tương ứng | không |
| 13 | jazz_voicing | jazz_voicing + voice_leading | pipeline tách 2 | không (post_mvp) |
| 14 | jazz_scales_tensions | không có | không tương ứng | không |
| – | không có | song_form | không tương ứng | – |

7/14 chiều có dữ liệu.

---

## 5. Kế hoạch theo giai đoạn: file, thứ tự, tiêu chí xong

Mỗi giai đoạn: nhánh `ai/gd<n>-…` xếp chồng lên nhánh trước, Draft PR đích `phuc-music`, CI xanh, báo cáo `docs/giai-doan/ai-gd<n>/BAO_CAO.md`. Theo câu 10A, mình dừng báo cáo ở cuối mỗi giai đoạn nhưng làm tiếp giai đoạn sau trên nhánh xếp chồng trong lúc chờ duyệt.

```
phuc-music ─ ai/gd0-ke-hoach ─ ai/gd1-mastery ─ ai/gd2-goi-y ─ ai/gd3-tutor ─ ai/gd4-danh-gia
                                  (cherry-pick #14, #17)
```

### GĐ1 `ai/gd1-mastery` (04–06/11)
- Cherry-pick PR #17 (9a2dc8f, 771c39b, 7ca71fd, f4a97ec, e2ce120) và PR #14 (f3bd6a4, 2e9fb70), giải 4 xung đột tài liệu, ghi SHA gốc trong commit.
- Migration chỉ thêm (nối sau `b8d5e6f7a9c1`): `skills.group_code`, `srs_code`, `ready_threshold`, `mastery_threshold`; bảng `mastery_states`, `mastery_events` (để chống cày điểm và tính lại); `attempts.is_test`, `attempts.assisted`; `users.goal_text`, `users.goal_embedding`; bảng `placement_results`; `users.is_synthetic`.
- `backend/app/ai/mastery.py` (hàm thuần), `services/mastery_service.py` (cùng giao dịch với lượt làm và lượt ôn), `python -m app.ai.rebuild_mastery`.
- Luật ôn 2A: thẻ máy chấm, đến hạn hoặc quá hạn, tối đa 1 sự kiện/kỹ năng/ngày theo giờ Việt Nam, kể cả lượt ôn ngay sau khi xong bài. Ôn trước hạn và thẻ tự đánh giá không tính (xem Q-A).
- `GET/POST /api/v1/placement…`, trang placement sau đăng ký (bỏ qua được), `GET /api/v1/me/mastery`.
- Mô tả 26 kỹ năng nháp (`status: draft`, có nguồn).
- Test: nhóm M của hợp đồng CP2, dãy 0,30 → 0,51 → 0,66 → 0,76 → 0,83, ca S1–S15, tái hiện C1 trước khi sửa (CI đỏ rồi xanh), đường mở L03 theo ngày với `now` cố định, placement 0,65.
- Xong khi: test cũ + mới xanh; bảng mastery một người mẫu qua từng lượt trong báo cáo.

### GĐ2 `ai/gd2-goi-y` (06–07/11)
- `backend/app/ai/recommender/{rules,content,knn,scoring,reasons}.py` (hàm thuần), `services/recommendation_service.py`, `ai/embedder.py` (Gemini, Fake, chuẩn hóa vector, cache theo hash), `content/skill_embeddings.json`.
- `GET /api/v1/recommend`, `PUT /api/v1/me/goal`; `RecommendedLessons.tsx` trên Dashboard.
- Thêm `numpy`, `scikit-learn`, `google-genai` vào `requirements.txt`.
- Test: K, C, R của hợp đồng CP2; Bảng 21 (0,548 / 0,447 / 0,419) và ca due = 1 (0,647); trọng số ±0,05; xác thực.

### GĐ3 `ai/gd3-tutor` (07–09/11)
- `backend/app/ai/tutor/{chunker,retriever,bm25,llm,guardrail,prompt,intent}.py`, `services/ai_tutor_service.py`, `content/lesson_embeddings.json`, `python -m app.ai.build_index`.
- Bảng `chat_sessions`, `chat_messages`, `chat_feedback`; `POST /api/v1/chat/message`, `POST /api/v1/tutor/explain-attempt`; giới hạn 50 câu/giờ/người và ngân sách ngày.
- `FloatingTutorDrawer.tsx`, nút "Giải thích lỗi này".
- ADR-014 (embedding Gemini), ADR-015 (Retriever + AI Tutor).
- Test như prompt mục GĐ3.12 + 10 câu tấn công; bộ `live` 10 câu với Gemini thật.

### GĐ4 `ai/gd4-danh-gia` (09–10/11)
- `scripts/ai/sinh_nguoi_hoc.py` (module riêng, không import recommender), `scripts/ai/evaluate_recommender.py`, `scripts/ai/evaluate_rag.py`, bộ chuẩn 30 + 10 + 10 câu.
- Báo cáo `docs/giai-doan/ai-gd4/BAO_CAO_THUC_NGHIEM.md`.

GĐ5–GĐ8 làm sau mốc 10/11 theo prompt, mỗi mục một Draft PR.

---

## 6. Rủi ro

| Rủi ro | Mức | Cách giảm |
|---|---|---|
| L02/L04 không vào gợi ý tới khi có M19 | Cao | Placement, tài khoản demo có lịch sử, nhắc Astra/Thắng M19 cho pitch.spelling và seventh_quality |
| 5 cổng duyệt trong 6 ngày | Cao | Nhánh xếp chồng (10A); cắt theo thứ tự 11A |
| `gemini-3.6-flash` 503 lúc tải cao | Trung bình | Thử lại 1 lần, rồi dự phòng theo luật; demo dùng `3.5-flash-lite` |
| Chưa biết giới hạn gói miễn phí | Trung bình | Chờ ảnh AI Studio; tạm đặt ngân sách thấp (ví dụ 200 lượt/ngày) |
| Khóa Gemini đã gửi trong khung chat | Trung bình | Nên tạo khóa mới sau đợt demo và xóa khóa này; khóa không bao giờ vào repo |
| `gemini-embedding-001` trả vector chưa chuẩn hóa ở 768 chiều | Thấp | Chuẩn hóa trong `embedder.py`, có test |
| Dữ liệu mô phỏng gây vòng tròn | Trung bình | Bộ sinh độc lập, ghi giới hạn (04 mục 6.5) |
| Bộ chuẩn RAG do Claude soạn | Trung bình | Đạt đọc 10 câu ngẫu nhiên và ký (12A) |
| Học sinh dưới 18 tuổi dùng gói miễn phí | Trung bình | Thông báo trong khung chat; phiếu đồng ý ở GĐ5 (03 Bảng 3) |

---

## 7. Câu cần duyệt

**Q-A (Phúc).** Phương án 1A không mở được L02 và làm giảm seventh_quality (mục 1.3). Đề xuất: không tính thẻ tự đánh giá vào mastery (giữ đúng 2A), giữ một cờ cấu hình `MASTERY_SELF_CHECK_WEIGHT` mặc định 0 để chứng minh trong báo cáo. Gỡ thật bằng placement + M19.

**Q-B (Thắng).** Embedding mặc định `gemini-embedding-001` (768 chiều, tự chuẩn hóa) hay `gemini-embedding-2` (bản chính thức mới, đã chuẩn hóa, 8.192 token)? Đề xuất: 001 theo prompt, GĐ4 đo cả hai trên bộ chuẩn rồi chốt.

**Q-C (Phúc).** Ảnh chụp trang giới hạn của khóa trong AI Studio, để đặt `AI_DAILY_BUDGET`.

**Q-D (Thắng).** Duyệt danh sách migration chỉ thêm ở GĐ1 (mục 5), đặc biệt `mastery_events` và `attempts.assisted`, hai mục prompt chưa liệt kê.

**Ký "Người kiểm":** Thắng: ____ · Phúc: ____ · Đạt: ____

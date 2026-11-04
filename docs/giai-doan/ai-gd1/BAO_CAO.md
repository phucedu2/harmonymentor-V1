# Báo cáo GĐ1 pipeline AI: kỹ năng, mastery, luật ôn 2A, bài kiểm tra đầu vào

Ngày 04/11/2026. Nhánh `ai/gd1-mastery`, tách từ `ai/gd0-ke-hoach` (PR #20). Draft PR #21 đích `phuc-music`.

Quyết định đã dùng: 12 câu làm rõ (Phúc chọn A cả 12), Phúc chốt bỏ 1A lúc 04/11 03:30 (chỉ giữ luật 2A), D-3/L-3/L-4 Thắng chốt 31/10, ánh xạ kỹ năng ADR-008 bản 4.

## A. Đã làm (đã chạy thật)

1. **Đưa PR #17 và PR #14 vào nhánh** bằng cherry-pick `-x`: 9a2dc8f, 771c39b, 7ca71fd, f4a97ec, e2ce120 (ADR-008 + bảng ánh xạ + hợp đồng test), f3bd6a4, 2e9fb70 (Leitner ôn trước hạn). Phần code của PR #14 áp sạch. 4 file tài liệu bị xung đột, mình giữ bản `phuc-music` và nâng mức CI từ 592 lên 604. PR gốc không bị đụng tới.
2. **Ánh xạ kỹ năng** (`backend/app/ai/skill_mapping.py`): 26 kỹ năng → `srs_code`, `group_code`, `SKILL_GROUP_MAP_VERSION`, cùng hàm kiểm bảng ánh xạ. Seed điền các cột này vào bảng `skills`, kèm ngưỡng 0,6 và 0,8.
3. **Mastery EMA** (`backend/app/ai/mastery.py`, hàm thuần): `mới = cũ + 0,3 × (kết_quả − cũ)`.
   - Kết quả của một lượt làm câu: đúng lần đầu = 1, sai = 0 (mọi lượt sai), đúng ngay sau một lượt sai = 0,5. Đúng lặp lại sau khi đã đúng thì **không cộng**, nhưng vẫn tăng `attempts_count`.
   - Lượt `is_test` (Admin) và kỹ năng `post_mvp` không tạo dòng mastery.
4. **Luật ôn 2A**: một lượt ôn thành sự kiện mastery khi thỏa đủ ba điều kiện: thẻ máy chấm, thẻ đã đến hạn hoặc quá hạn, và kỹ năng đó chưa có lượt ôn nào được tính trong ngày (tính theo giờ Việt Nam). Kết quả đúng = 1, sai = 0. Ôn trước hạn và thẻ tự đánh giá không tính.
5. **Cùng giao dịch**: `submit_attempt` và `answer_review` ghi lượt làm và mastery trong cùng một lần commit (`services/mastery_service.py`).
6. **Tính lại từ lịch sử**: `python -m app.ai.rebuild_mastery [--user ID]` tính lại mastery theo thứ tự thời gian (placement → lượt làm → lượt ôn) và in dấu kiểm SHA-256. Test khẳng định kết quả bằng đúng kết quả cập nhật trực tiếp, và chạy hai lần ra cùng số.
7. **Bài kiểm tra đầu vào (UC-06)**:
   - API: `GET /api/v1/placement`, `POST /api/v1/placement/submit`, `POST /api/v1/placement/skip`.
   - Đề gồm 12 câu đã xuất bản, mỗi câu một kỹ năng MVP, đi theo thứ tự L01 → L04. Riêng `function.predominant` bị bỏ để đúng 12 câu; danh sách chờ Đạt duyệt.
   - Cách tính điểm: đúng → 0,65, sai → 0, câu bỏ trống = chưa đánh giá.
   - Làm lại phải xác nhận (không xác nhận thì trả 409), và không ghi đè kỹ năng đã có lịch sử học thật.
   - Lượt làm placement không ghi vào `attempts`, để lượt làm cùng câu trong bài sau này vẫn được tính là "đúng lần đầu".
8. **`GET /api/v1/me/mastery`**: chỉ trả kỹ năng MVP của chính người dùng, kèm `group_code`, `assessed` và `level` (not_assessed / learning / weak / ready / mastered).
9. **Frontend**:
   - Trang `/app/kiem-tra-dau-vao`: câu trắc nghiệm có nút chọn (role radio), câu tự luận có ô nhập, có nút bỏ qua.
   - Sau khi đăng ký, người dùng được chuyển tới trang này.
   - Tổng quan hiện thẻ mời làm bài khi người học chưa bắt đầu bài nào và chưa làm placement.

## B. File

| File | Vai trò |
|---|---|
| `backend/app/ai/skill_mapping.py` | Bảng ánh xạ ADR-008, kiểm hợp lệ |
| `backend/app/ai/mastery.py` | EMA, kết quả lượt làm, luật 2A, ngưỡng, ngày VN |
| `backend/app/ai/rebuild_mastery.py` | Lệnh tính lại |
| `backend/app/services/mastery_service.py` | Ghi mastery cùng giao dịch, placement, rebuild |
| `backend/app/services/placement_service.py` | Đề 12 câu, chấm, bỏ qua |
| `backend/app/api/ai_learning.py`, `backend/app/contracts/ai.py` | API + schema Pydantic |
| `backend/app/services/learning_service.py` | Thêm `now`, `is_test`, `due_before`, gọi mastery |
| `backend/app/db/models.py`, `backend/app/db/session.py` | Model mới, báo lỗi rõ khi CSDL SQLite cũ thiếu cột |
| `backend/migrations/versions/20261104_ai_gd1_mastery.py` | Migration chỉ thêm |
| `backend/tests/test_cp2_skill_mapping.py` (M1–M13), `test_cp2_mastery_ema.py` (S1–S10, B6, L-3), `test_cp2_mastery_scope.py` (S11–S15), `test_ai_gd1_review_mastery.py` (2A, C1), `test_ai_gd1_migration.py` | Test |
| `frontend/src/pages/app/PlacementPage.tsx`, `App.tsx`, `api.ts`, `Dashboard.tsx`, `RegisterPage.tsx` | Giao diện |
| `scripts/ai/gd1_nguoi_mau.py`, `docs/giai-doan/ai-gd1/nguoi_mau_2026-11-04.md` | Bảng người mẫu |
| `docs/minh-chung/anh/ai-gd1/*.png` | Ảnh máy tính 1280px + điện thoại 390px |

## C. Lệnh và kết quả (04/11/2026, máy cloud)

| Lệnh | Kết quả |
|---|---|
| `cd backend && python -m pytest -q` | **647 passed, 21 skipped** (604 sau cherry-pick + 43 test mới; 21 test PostgreSQL chạy ở CI) |
| `alembic -c alembic.ini upgrade head && alembic -c alembic.ini check` (SQLite) | Đạt, "No new upgrade operations detected" |
| CI run 41767797979 (commit df6cc1b, chỉ có test) | **Đỏ có chủ đích** |
| CI run 41768595585 (commit 0f728a1) | PostgreSQL + Alembic check: xanh; Frontend: xanh; SQLite: xem PR |
| `cd frontend && npm run build` | Đạt |
| `npx vitest run` | 259 passed |
| Playwright: đăng ký → trang kiểm tra đầu vào → nộp | Chạy được ở 1280px và 390px. Có 1 lỗi console 401 từ lần làm mới phiên trước khi đăng nhập (có sẵn từ trước, không do GĐ1) |

Sửa test cũ: `test_phuc_music_composition_migration.py` trước kiểm "head = b8d5e6f7a9c1". Nay head là migration GĐ1, nên test đó nâng tới đúng `b8d5e6f7a9c1` thay vì "head". Ý nghĩa test giữ nguyên, migration mới có test riêng.

## D. Thay đổi API và CSDL

| Endpoint | Xác thực | Ghi chú |
|---|---|---|
| `GET /api/v1/me/mastery` | Bắt buộc | `{skill_group_map_version, skills: [{skill_id, name, srs_code, group_code, assessed, score, attempts_count, level, ready_threshold, mastery_threshold}]}` |
| `GET /api/v1/placement` | Bắt buộc | `{status, questions: [{exercise_id, exercise_version_id, skill_id, kind, prompt, options}]}`. Không trả đáp án |
| `POST /api/v1/placement/submit` | Bắt buộc | `{answers: [{exercise_version_id, answer}], confirm_retake}` → `{status, results}`; 409 `PLACEMENT_ALREADY_DONE` |
| `POST /api/v1/placement/skip` | Bắt buộc | Chỉ ghi khi chưa làm |

Migration `c1a2b3d4e5f6` (sau `b8d5e6f7a9c1`) chỉ thêm, không đổi cột cũ:
- Cột mới: `skills.srs_code`, `skills.group_code`, `skills.ready_threshold`, `skills.mastery_threshold`, `attempts.is_test`, `review_attempts.due_before`.
- Bảng mới: `mastery_states`, `mastery_events`, `placement_results`.

Hạ phiên bản xóa đúng các phần trên, và test xác nhận dữ liệu cũ vẫn còn. Tương thích ngược: API cũ không đổi hình dạng. CSDL SQLite dev cũ phải chạy `alembic upgrade head` (hoặc xóa file) thì ứng dụng mới khởi động; ứng dụng sẽ báo rõ lệnh cần chạy.

Thêm hai mục so với danh sách được phép trong nhiệm vụ: `mastery_events` (nhật ký để giải thích điểm và kiểm rebuild) và `review_attempts.due_before` (để biết lượt ôn có đến hạn không khi tính lại). Hai mục này chờ Thắng duyệt (Q-D). `attempts.assisted` chưa thêm: chưa có tính năng gợi ý cho câu bài tập, nên sẽ làm ở GĐ3 cùng "Giải thích lỗi".

## E. Giải thích cho nhóm

**EMA là gì?** Đây là cách cập nhật điểm "nhớ lâu, nhưng nghiêng về gần đây": mỗi lượt kéo điểm đi 30% quãng đường tới kết quả của lượt đó. Từ 0, làm đúng thì 0 + 0,3 × (1 − 0) = 0,30. Làm sai từ 0,65 thì 0,65 + 0,3 × (0 − 0,65) = 0,455.

**Vì sao đúng lặp lại không cộng?** Nếu cộng, người học bấm cùng một câu đúng 5 lần là thành thạo mà không học thêm gì. Đây là luật chống cày điểm (S7).

**Vì sao lượt ôn được tính, nhưng mỗi ngày chỉ một lần?** Nhớ lại được sau một ngày là bằng chứng thật về việc học (đây là ý tưởng của lặp lại ngắt quãng). Ôn 4 thẻ liền tay trong 5 phút thì không chứng minh được thêm gì.

**Người mẫu** (`scripts/ai/gd1_nguoi_mau.py`, trích):

| # | Ngày | Nguồn | Kỹ năng | Kết quả | Trước → Sau |
|---|---|---|---|---|---|
| 2 | 02/11 | lượt làm | chord.triad_build | 1 | chưa đánh giá → 0,300 |
| 4 | 02/11 | lượt làm (gõ D F# A cho D minor) | chord.triad_build | 0 | 0,300 → 0,210 |
| 5 | 02/11 | sửa lại đúng | chord.triad_build | 0,5 | 0,210 → 0,297 |
| 7 | 02/11 | câu thứ ba | chord.triad_build | 1 | 0,297 → 0,508 |
| 10 | 03/11 | lượt làm L02 | roman.major_seventh | 1 | chưa đánh giá → 0,300 |
| 14 | 03/11 | ôn thẻ đến hạn (4 thẻ, chỉ 1 được tính) | roman.major_seventh | 1 | 0,300 → 0,510 |
| 15 | 05/11 | ôn thẻ đến hạn | roman.major_seventh | 1 | 0,510 → 0,657 (đủ học L03) |

Bảng này cho thấy một điều quan trọng: chỉ cần **sai một lần** ở L01 là `chord.triad_build` (tiên quyết của L02) dừng ở 0,508 nếu chỉ dựa vào câu bài tập. Người này phải ôn 3 thẻ máy chấm của kỹ năng đó qua các ngày mới đạt 0,60.

**Giới hạn:** bảng trên là mô phỏng, chạy với giờ cố định trên CSDL tạm, chưa chứng minh chất lượng với người học thật.

## F. Câu hội đồng có thể hỏi

1. *"Vì sao không cộng điểm khi làm đúng lại?"* Vì đó là cày điểm. Lượt đúng sau một lượt sai được 0,5, vì người học đã tự sửa được lỗi (Thắng trả lời).
2. *"Placement đặt 0,65 có tùy tiện không?"* Con số này do tài liệu 04 mục 6.3 và UC-06 quy định: trên 0,60 để mở bài sau, dưới 0,80 để chưa coi là thành thạo (Thắng).
3. *"Làm sao biết mastery không bị tính sai?"* Lệnh `rebuild_mastery` tính lại từ lịch sử, và test so kết quả đó với kết quả cập nhật trực tiếp; mọi lần đổi điểm đều có dòng trong `mastery_events` (Thắng).
4. *"Vì sao Admin làm bài không đổi điểm?"* Theo nguyên tắc 8, lượt của Admin có `is_test = true` để không làm bẩn thống kê (Đạt).
5. *"Người học làm sai bài kiểm tra đầu vào thì sao?"* Kỹ năng đó được đặt 0, câu bỏ trống là "chưa đánh giá", và học trong bài vẫn cộng bình thường (Phúc).

## G. Việc tiếp theo và người duyệt

1. ~~Thắng: duyệt migration (Q-D: `mastery_events`, `review_attempts.due_before`) và cách hiểu D-3/2A trong code.~~ Thắng đã duyệt 04/11/2026 (demo 10/11, "Thắng duyệt hết").
2. Đạt: duyệt danh sách 12 kỹ năng placement (bỏ `function.predominant`).
3. Phúc: xem ảnh trang kiểm tra đầu vào ở `docs/minh-chung/anh/ai-gd1/`.
4. GĐ2: hệ gợi ý 3 tầng, mô tả 26 kỹ năng (nháp), embedder Gemini/Fake.
5. Nhắc Astra/Thắng: câu M19 cho `pitch.spelling` và `chord.seventh_quality`. Nếu không có, L02/L04 chỉ mở được qua placement.

**Người kiểm:** Thắng ____ · Phúc ____ · Đạt ____

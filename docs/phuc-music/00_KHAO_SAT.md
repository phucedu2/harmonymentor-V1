# Bước 0. Khảo sát khu học: bản v0.5.3-dev và main

Ngày chạy: 31/10/2026. Nhánh `phuc-music` tách từ `origin/main` 58a6f52. Bước này chỉ đọc và chạy thử, chưa sửa code.

## 1. Kết luận chính

**Khu học của main đã là khu học của v0.5.3, được sửa tiếp.** 21 file frontend của tag thì 20 file vẫn còn trên main: 7 file giữ y nguyên, 13 file đã được sửa (dịch sang tiếng Việt, đổi sang router và token, thêm logic kiểm định người mới học). Chỉ `pages/HarmonyLab.tsx` bị xóa, nhưng ở tag file đó cũng chỉ là khung giữ chỗ 4 dòng ("Phase 0 skeleton", nút "AI Suggestions" bị tắt).

Vì vậy, "lấy bố cục v0.5.3" thực chất chỉ gồm 3 thứ có thể lấy về:

1. **Khung ngoài (shell):** thanh bên tối màu, mỗi mục có nhãn phụ nhỏ (HOME, LEARN, PRACTICE, CREATE, PROGRESS). Trên điện thoại, thanh này thành dải tab tối ở đầu trang. Main dùng `AppLayout` nền sáng của Tailwind, có tên người dùng và nút Đăng xuất.
2. **Bài học dạng một trang cuộn dài** (tag), thay vì chia bước "Bước 1/17" với nút Bước trước/Bước tiếp (main, PR #6). Hai cách này mâu thuẫn nhau: xem mục 6, câu M-1.
3. **Mục Harmony Lab trên thanh điều hướng.** Main đã đổi thành "Sáng tác" với trang "Sắp mở".

**Backend không có gì cần khôi phục.** Các hàm "bị xóa" trong `git diff v0.5.3-dev origin/main -- backend` thực ra chỉ đổi chữ ký: tag nhận `user_id="demo-user"` từ client, còn main lấy `user_id` từ token (nguyên tắc bất biến số 4). Main thêm 102 hàm và route mới. Trả lại `user_id` từ client là lỗ hổng bảo mật, nên không làm.

## 2. Lệnh đã chạy và kết quả

| Lệnh | Ở đâu | Kết quả |
|---|---|---|
| `cd backend && pytest -q` | main 58a6f52 | **325 passed, 21 skipped** trong 22,9 giây (21 test PostgreSQL cần `TEST_DATABASE_URL`) |
| `cd frontend && npm ci && npm run build` | main | **Đạt**, cảnh báo chunk `LessonRunner` 1.159 kB (gzip 703 kB) |
| `npm ci` | tag v0.5.3-dev | **Lỗi**: `package-lock.json` lệch với `package.json` (thiếu tone, vexflow trong lock). Phải dùng `npm install` |
| `npm run build` | tag | **Lỗi TypeScript**: `replaceAll` không có ở `lib` hiện tại (`lesson1Theory.ts` dòng 27 và 41). `vite dev` vẫn chạy được |
| uvicorn + vite cả hai bản, Playwright chụp 1440px và 390px | tag (cổng 8001/5174), main (8000/5173) | 26 ảnh + 6 ảnh ghép ở `anh/buoc-0/` |
| Luồng main: trang chủ → đăng ký → vào `/app` | main | Đăng ký xong vào thẳng `/app` (Tổng quan), đúng yêu cầu Bước 1 |

CI (`.github/workflows/ci.yml`) có 3 job: Backend SQLite (`--min-passed 325`), PostgreSQL 16 + pgvector (alembic + 21 test), Frontend (`npm ci && npm run build`). Ruleset `bao-ve-main` bắt buộc cả 3 job xanh.

## 3. Hiện trạng main

**Route frontend** (`frontend/src/App.tsx`):

| Khu | Route | Trang | Ghi chú |
|---|---|---|---|
| Công khai (`PublicLayout`) | `/`, `/dang-nhap`, `/dang-ky`, `*` | HomePage, LoginPage, RegisterPage, NotFoundPage | Tailwind |
| Người học (`RequireAuth` + `AppLayout`) | `/app` | Dashboard | bọc `legacy-page` (CSS cũ) |
| | `/app/hoc` | Learn → LessonRunner | `legacy-page` |
| | `/app/luyen-tap` | Practice | `legacy-page`, **không ghi lịch sử** (không gọi `/attempts`) |
| | `/app/tien-do` | Progress (kèm ôn thẻ Leitner) | `legacy-page` |
| | `/app/composition` | CompositionLabPage | "Sắp mở" |
| | `/app/ho-so` | ProfilePage | Tailwind |
| Quản trị | `/admin` | AdminHomePage (`RequireAdmin`) | Tailwind |

Component dùng chung đã có: `components/ui/{Button, Alert, TextField, PageLoader}`.

**API backend** (tiền tố `/api/v1`): auth (`register`, `login`, `refresh`, `logout`, `GET/PATCH me`); `lessons` (danh sách, chi tiết, `start`, `complete`); `attempts` (POST); `review` (`due`, `answer`); `learning/overview`; `engine/*` (chord, scale, interval, transpose, key, diatonic, roman, ai-tools, 7 route `grade/*`); `music/chords/*`; `admin/ping`.

**Bảng CSDL (16):** users, refresh_tokens, skills, skill_prerequisites, lessons, lesson_blocks, source_works, lesson_sources, exercises, exercise_versions, attempts, attempt_errors, lesson_progress, review_items, review_states, review_attempts. Có 5 migration. Chưa có bảng mastery, dự án sáng tác hay kiểm tra đầu vào.

**Nội dung:** `lesson_specs.json` có 8 bài. L01–L04 `reviewed` (đã chạy được), L05–L08 `source_audited` (chưa có câu hỏi, hiện "Sắp có"). SRS FR-03 yêu cầu 12 bài và 5 module.

## 4. So sánh từng trang (ảnh ở `anh/buoc-0/so-sanh-*.png`)

| Trang | Tag hơn main ở đâu | Main hơn tag ở đâu |
|---|---|---|
| Khung ngoài | Thanh bên tối, đậm chất "ứng dụng"; nhãn phụ tiếng Anh nhỏ | Có đăng nhập, tên người dùng, Đăng xuất, bỏ qua tới nội dung (a11y), Quản trị cho admin, logo |
| Tổng quan | Không có gì hơn | Lời chào theo tên, câu dẫn cho người mới, nhãn tiếng Việt, đếm đúng 4 bài chạy được (tag ghi 0/8) |
| Học (danh sách) | Không có gì hơn | Nhãn "Học ngay / Nên học sau Bài N / Sắp có", số phần, câu, thẻ; bỏ nhãn kỹ thuật `reviewed`/`source_audited` |
| Bài 1 | Cuộn một trang: thấy toàn bộ bài, có ô "Bài này bắt đầu từ con số 0" ngay đầu | Chia 17 bước, mục lục, tiến độ "Đúng 0/6 câu", lời giải sau 2 lần sai, 409 `LESSON_NOT_MASTERED`, phiên bản câu hỏi |
| Luyện tập | Không có gì hơn | 3 mức Dễ/Vừa/Khó bám nội dung bài, dùng piano tương tác |
| Tiến độ | Không có gì hơn | Thẻ tự đánh giá kiểu Anki, hộp Leitner x/5, thông báo kết quả ôn |
| Harmony Lab | Khung "C · G · Am · F" | "Sắp mở". Cả hai đều chưa có chức năng |

Trên điện thoại 390px: thanh tab của tag chiếm 5 cột cố định, chữ "Harmony Lab" xuống 2 dòng. Thanh tab của main cuộn ngang và bị cắt ở "Sáng…".

## 5. Danh sách file dự kiến lấy từ tag (Bước 1)

| File từ tag | Cách lấy | Lý do |
|---|---|---|
| `App.tsx`, phần shell (`app-shell`, `sidebar`, `main-nav`) | Chép **giao diện** vào `AppLayout.tsx`, giữ `NavLink`, `RequireAuth`, Đăng xuất | Phúc chọn bố cục v0.5.3, logic main |
| `styles.css`, các lớp `.app-shell .sidebar .brand .main-nav .sidebar-note` | Viết lại bằng Tailwind trong `AppLayout`, không chép CSS cũ | Bước 3 bỏ `legacy-page`; tránh thêm CSS cũ rồi lại xóa |
| `pages/HarmonyLab.tsx` | **Không lấy** | Chỉ là khung 4 dòng; Bước 4 làm xưởng thật |
| `LessonRunner.tsx` (bản cuộn) | **Chờ Phúc quyết M-1** | Mâu thuẫn với PR #6 |
| Các file còn lại | Giữ của main | Main đã chứa và sửa tiếp |

## 6. Mâu thuẫn và câu cần quyết

| Mã | Mâu thuẫn | Đề xuất |
|---|---|---|
| M-1 | "Bố cục v0.5.3" cho Bài 1 là cuộn một trang, nhưng "bài chia bước" của PR #6 nằm trong danh sách "không được mất" | Giữ chia bước của main. Lấy từ tag ô "Bài này bắt đầu từ con số 0" và thêm chế độ "Xem cả bài" (mục lục mở rộng) |
| M-2 | Thanh bên tối của tag và bảng màu "Đồng & Gỉ" (Bước 3, nền tối #081613) | Bước 1 dựng shell tag bằng token tạm; Bước 3 đổi sang #081613 / #45C2AB |
| M-3 | Nhãn phụ tiếng Anh của tag (HOME, LEARN…) và quy ước "giao diện tiếng Việt" | Bỏ nhãn phụ tiếng Anh, chỉ giữ cách trình bày |
| M-4 | Thanh điều hướng: tag ghi "Harmony Lab", main ghi "Sáng tác" (quyết định M3, đổi tên theo SRS) | Ghi "Sáng tác" |
| M-5 | Câu 2B (làm Practice ghi lịch sử và kiểm tra đầu vào theo D-3) trong khi L-1/L-2/L-5/L-6 và migration `client_attempt_id` (K-2) Thắng chưa chốt | Bước 2 chỉ làm phần đã chốt (D-3, L-3, L-4), phần chưa chốt để sau và ghi rõ trong báo cáo |
| M-6 | Hướng dẫn dự án dùng `docs/tai-lieu/v2.1/`, repo dùng `docs/SRS/` | Dùng `docs/SRS/` (Phúc đã quyết 26/10) |
| M-7 | Tag build lỗi và lock lệch | Không ảnh hưởng, vì không chép file cấu hình nào của tag |

## 7. File dễ xung đột với các PR đang mở

| PR | File chung với kế hoạch phuc-music | Khi nào đụng |
|---|---|---|
| #16 logo (`claude/project-thread-82ijft`) | `components/layout/Logo.tsx` (AppLayout dùng) | Bước 1, 3 |
| #12 HM-001 (`claude/project-thread-qdcaej`) | `theory/lesson1Theory.ts`, `audio/musicUtils.ts` | Bước 2 (đã chọn dựng tiếp trên #12) |
| #14 HM-012 Leitner | `services/review_scheduler.py` | Bước 2 nếu đụng ôn tập |
| #15 HM-011 | `backend/tests/test_hm011_input_method.py`, cách nhập piano | Bước 2 (Eb → D#) |
| #17 ADR-008 | Chỉ tài liệu | Không |
| `claude/reset-dev` | `backend/app/core/config.py` | Bước 4 nếu thêm cấu hình |

## 8. Rủi ro

- **Phạm vi lớn so với lịch.** CP2 là 03/11 và nhóm đang tập trung vào hệ gợi ý. Bước 1–4 khối lượng nhiều tuần; Bước 4 vượt phạm vi Giai đoạn 1 (cần ADR, Thắng ký).
- **Bundle LessonRunner 1,16 MB.** Thêm VexFlow/Tone vào xưởng sáng tác sẽ làm nặng hơn; cần tách chunk.
- **Docker chưa kiểm được trên cloud** (Docker Hub trả 429 ở lần rà soát 29/10). Ảnh lần này chạy bằng uvicorn + vite, không qua Docker.

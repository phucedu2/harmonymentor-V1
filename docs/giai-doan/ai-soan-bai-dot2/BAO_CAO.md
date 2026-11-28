# Đợt 2 AI soạn bài và giao diện (18/11/2026, ADR-029)

Phúc giao 5 việc, trả lời 12 câu: 1A 2A 3A 4A 5A 6A 7A 8A 9A 10A 11A 12B.

| Việc | Đã làm | File chính |
|---|---|---|
| 1. Bỏ chọn trang, tóm tắt hết tài liệu | Nút "AI soạn bài từ cả tài liệu", chia chương bằng luật, chạy nền, tiến độ từng phần, tạm dừng khi hết hạn mức và chạy tiếp | `backend/app/admin/ai_job.py`, `router.py`, `AiDraftTab.tsx` |
| 2. Không thêm kiến thức đã có | AI nhận danh mục "đã có" + máy so độ giống (e5/TF-IDF); phần không còn gì mới thì không tạo bài; mục "Kiến thức mới" ở trang Học; bài "Mở rộng" không tính thành thạo | `ai_job.py`, `ai_service.py`, `mastery_service.py`, `quiz_service.py`, `api/lessons.py`, `Learn.tsx` |
| 3. Mọi nút cùng quay | Mỗi nút một khóa riêng (`busyKey`), kể cả trong màn sửa bản nháp | `AiDraftTab.tsx` |
| 4. Hồ sơ lên góc phải + avatar | Menu ảnh đại diện (Hồ sơ, Đăng xuất) cho người học và Admin; 12 con vật SVG; chọn con vật trong trang Hồ sơ (giữ đủ thông tin cũ) | `AccountMenu.tsx`, `AnimalAvatar.tsx`, `AppLayout.tsx`, `ProfilePage.tsx`, `auth/avatars.py` |
| 5. Cửa sổ AI Tutor | Đổi cỡ 8 hướng, phóng to/thu về, thu nhỏ, nhớ cỡ; biểu tượng nốt nhạc trong bong bóng | `FloatingTutorDrawer.tsx`, `TutorIcon.tsx`, `useDraggable.ts` |

## Kiểm thử

- `pytest -q`: 1481 passed, 44 skipped (thêm 14 test ở `tests/test_ai_tom_tat_ca_file.py`). CI `--min-passed` 1467 → 1481.
- `npm test` (Vitest): 285 passed (thêm 3 test ảnh đại diện, có test so khớp danh sách con vật với máy chủ).
- `npm run build`: đạt.
- Playwright giao diện (`npx playwright test`): 26 passed, 3 skipped (thêm 2 test: đổi cỡ/phóng to/thu nhỏ AI Tutor, menu ảnh đại diện).
- Playwright backend thật (`e2e:live`): 7 passed (đăng xuất nay qua menu ảnh đại diện).
- Ảnh chụp app thật (SQLite, AI giả): `/mnt/project-files/ai-soan-bai-dot2/`.

## Chưa làm / cần nhóm

- Chưa chạy với Gemini thật (khóa ở máy Phúc). Cần thử 1 cuốn sách thật để hiệu chỉnh ngưỡng trùng.
- Máy Phúc: `docker compose up --build` tự nâng CSDL (migration `c7a8b9c0d1e2`).

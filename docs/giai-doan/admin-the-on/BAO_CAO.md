# Admin soạn thẻ ôn (FR-ADM-31..34), 25/11/2026

Quản trị viên thêm, sửa, xóa mềm thẻ ôn Leitner theo từng bài, gắn kỹ năng, và nhập thẻ từ file (mục `cards:`).

## Đã làm
- Cột `review_items.deleted_at` (migration `a1b2c3d4e5f7`, guard ở `session.py`). Mọi nơi đọc thẻ (ôn tập, bài học, gợi ý, kích hoạt) lọc thẻ đã xóa mềm.
- `backend/app/admin/card_admin.py`: sáu loại thẻ `recall`, `self_check`, `build_chord`, `build_scale`, `interval`, `roman`. Bốn loại sau do Music Engine tính đáp án, Admin không tự gõ.
- Thẻ Admin có id `<bài>-R01…` (file nhập: `<bài>-R-<key>`), gắn được vào mọi bài, kể cả bài gốc. Thẻ seed chỉ xem (409 `SEED_CARD`).
- Sửa thẻ ghi đè tại chỗ và ghi giá trị cũ vào nhật ký. Thêm thẻ vào bài người học đã hoàn thành thì kích hoạt thẻ cho họ (đến hạn ngay).
- Nhập file: mục `cards:` cùng quy tắc, báo `cards_added/cards_revised/cards_not_in_file`.
- Giao diện: `CardsPanel.tsx` trong tab Bài học.

## Kiểm chứng
pytest 1625 đạt + 44 bỏ qua; Vitest 313; `npm run build` đạt. Chạy trình duyệt thật (AI giả): thêm thẻ hợp âm Engine (đáp án Eb–Gb–Bbb–Db), bị từ chối khi ký hiệu sai, sửa, xóa.

## Chưa làm
- Thẻ nhập từ file không kích hoạt ngược cho người học đã hoàn thành bài từ trước (thêm bằng form thì có).
- Thẻ seed sửa qua `curriculum_specs`, không sửa trên web.

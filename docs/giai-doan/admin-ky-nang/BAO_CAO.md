# Admin: kỹ năng, tiên quyết, nguồn tài liệu (24/11/2026)

Đây là PR 3 trong 4 PR hoàn thiện khu Admin, theo lựa chọn 1A của Phúc. Tab mới tên **"Kỹ năng & nguồn"**. Không có
migration: tab dùng các bảng `skills`, `skill_prerequisites`, `source_works`, `lesson_sources` đã có.

| FR | Làm gì |
|---|---|
| FR-ADM-18/19 | Danh sách kỹ năng (lọc được): tên, miền, gốc hay tự thêm, có trong hệ gợi ý không, bài nào đang dùng. Thêm/sửa/xóa kỹ năng tự thêm (mã `custom.…`) |
| FR-ADM-20/21 | Thêm/gỡ kỹ năng tiên quyết. **Chặn vòng lặp**, kể cả vòng gián tiếp (A cần C, C cần B, B cần A). Không cho kỹ năng tự làm tiên quyết của chính nó |
| FR-ADM-22 | Gán bài cho kỹ năng: kỹ năng của bài là kỹ năng của các câu trong bài (04 mục 6.5). Chọn ở ô "Kỹ năng" trong form câu luyện tập (PR #76); tab này hiện bài nào đang dùng kỹ năng nào |
| FR-ADM-38 | Thêm/sửa nguồn (tên, tác giả, liên kết http/https). Gắn/gỡ nguồn cho bài tự tạo và bài AI. Mỗi bài phải còn ít nhất một nguồn (nguyên tắc 11) |

**Vì sao phần "gốc" chỉ xem:** seed chạy lại mỗi lần khởi động. Mỗi lần như vậy, seed ghi lại tên kỹ năng gốc, thêm
lại cạnh tiên quyết gốc, ghi lại thông tin nguồn gốc và dựng lại liên kết nguồn của bài gốc. Nếu cho sửa trên web thì
lần khởi động sau sẽ mất hết mà không báo. Vì thế máy chủ từ chối và chỉ chỗ cần sửa trong code (`skill_graph.py`,
`source_registry.py`, `curriculum_specs`).

**Giới hạn:**
- Kỹ năng tự thêm chưa có trong vector của hệ gợi ý (ADR-008), nên hiện nhãn "Ngoài hệ gợi ý".
- Xóa kỹ năng là xóa thật, nhưng chỉ khi chưa câu nào (kể cả câu đã bỏ) dùng nó, để lượt làm và mức thành thạo cũ còn
  đọc được.
- Ngưỡng thành thạo của kỹ năng không sửa qua web: 04 Bảng 19 quy định đổi ngưỡng phải qua nhóm.

## Kiểm chứng

- `pytest -q` (SQLite): 1591 passed, 44 skipped. Thêm 8 test ở `tests/test_admin_ky_nang.py`.
- `npm run build` đạt; Vitest 313/313.
- Thử trên trình duyệt (Playwright, app thật):
  - Thêm kỹ năng, thêm tiên quyết.
  - Thêm cạnh ngược lại thì bị từ chối: "đã (gián tiếp) cần … học trước, thêm cạnh này sẽ tạo vòng lặp".
  - Gỡ tiên quyết, xóa kỹ năng.
  - Thêm nguồn và gắn nguồn đó vào một bài AI.

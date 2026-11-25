# HarmonyMentor — Bước 4: hàng đợi bổ sung và duyệt dữ liệu

> Tất cả 38 mục dưới đây chỉ là ứng viên. Chưa được đưa vào training và chưa được phê duyệt.

## Thống kê

- 26 ứng viên A: trong học liệu, cần duyệt nội dung và citation.
- 4 ứng viên B: kiến thức âm nhạc ngoài bài, cần nguồn bổ sung; tạm giữ ngoài dataset.
- 8 ứng viên C: ngoài phạm vi, cần duyệt hành vi từ chối.
- Mẫu train đã lọc hiện tại: 8.
- Mục tiêu kỹ thuật: ít nhất 50 mẫu train đã duyệt.

## Phiếu quyết định

| ID | Nhóm | Quyết định | Người duyệt | Ngày | Quyền sử dụng/nguồn | Ghi chú |
|---|---|---|---|---|---|---|
| `A01` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A02` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A03` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A04` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A05` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A06` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A07` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A08` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A09` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A10` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A11` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A12` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A13` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A14` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A15` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A16` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A17` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A18` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A19` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A20` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A21` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A22` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A23` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A24` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A25` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `A26` | A — trong học liệu | **Giữ/Sửa/Loại** |  |  |  |  |
| `B01` | B — ngoài bài, chờ nguồn | **Giữ/Sửa/Loại** |  |  |  |  |
| `B02` | B — ngoài bài, chờ nguồn | **Giữ/Sửa/Loại** |  |  |  |  |
| `B03` | B — ngoài bài, chờ nguồn | **Giữ/Sửa/Loại** |  |  |  |  |
| `B04` | B — ngoài bài, chờ nguồn | **Giữ/Sửa/Loại** |  |  |  |  |
| `C01` | C — ngoài phạm vi | **Giữ/Sửa/Loại** |  |  |  |  |
| `C02` | C — ngoài phạm vi | **Giữ/Sửa/Loại** |  |  |  |  |
| `C03` | C — ngoài phạm vi | **Giữ/Sửa/Loại** |  |  |  |  |
| `C04` | C — ngoài phạm vi | **Giữ/Sửa/Loại** |  |  |  |  |
| `C05` | C — ngoài phạm vi | **Giữ/Sửa/Loại** |  |  |  |  |
| `C06` | C — ngoài phạm vi | **Giữ/Sửa/Loại** |  |  |  |  |
| `C07` | C — ngoài phạm vi | **Giữ/Sửa/Loại** |  |  |  |  |
| `C08` | C — ngoài phạm vi | **Giữ/Sửa/Loại** |  |  |  |  |

## Điều kiện để nhập vào dataset

Một ứng viên chỉ được nhập vào dataset được duyệt khi:

1. Có quyết định Giữ hoặc đã sửa xong.
2. Nội dung được người có trách nhiệm chuyên môn xem xét.
3. Nguồn/quyền sử dụng được xác nhận.
4. Đạt kiểm tra schema, citation, Music Engine (nếu có claim), tokenizer và assistant-only mask.
5. Không trùng với train/dev/test hiện có.

## Phản hồi đề nghị

```text
A01: Giữ/Sửa/Loại — người duyệt — nguồn/quyền — ghi chú
A02: Giữ/Sửa/Loại — người duyệt — nguồn/quyền — ghi chú
...
B01–B04: chỉ Giữ khi đã bổ sung và xác nhận nguồn
C01–C08: Giữ/Sửa/Loại — xác nhận hành vi từ chối
```

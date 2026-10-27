# ADR-006 · Phiên bản câu hỏi bất biến (HM-003)

Trạng thái: **Chấp nhận 27/10/2026**, gộp qua PR #11. Phúc xác nhận thay nhóm ADR này và D-1..D-4; Thắng và Đạt ký bổ sung. Phúc chốt 8 câu thiết kế và 7 câu triển khai (đều chọn phương án A), Astra phê duyệt có điều kiện phương án "B rút gọn cho Giai đoạn 1". Số ADR-005 để dành cho Retriever (GĐ3).

## Bối cảnh

Seed chạy mỗi lần API khởi động và ghi đè tại chỗ cả `exercise_versions` (đáp án, cấu hình chấm, lời giải, nguồn) lẫn `exercises` (đề bài, lựa chọn, loại câu, cách chấm). Vì đề bài và cách chấm nằm trên `exercises`, mọi phiên bản cũ "mượn" đề và cách chấm của bản mới.

Đã tái hiện: lượt làm đúng ở `L03-Q05-v1` (chấm `rubric`), sau khi seed lại bằng code mới (`L03-Q05` thành trắc nghiệm `exact`) thì gửi lại cùng câu trả lời vào v1 bị chấm **sai**. Điều này trái tài liệu 04 Bảng 5 ("Khi sửa câu hỏi, hệ thống tạo phiên bản mới để lượt làm cũ giữ đúng nghĩa"), FR-EX-10, FR-ADM-25, NFR-11.

## Quyết định

1. **Ảnh chụp đầy đủ trên phiên bản.** `exercise_versions` lưu thêm `kind`, `prompt`, `options`, `grading_strategy`. Ảnh chụp gồm 8 trường: 4 trường đó và `answer_key`, `grader_config`, `explanation`, `provenance`. `content_hash` là SHA-256 của ảnh chụp đã chuẩn hóa (JSON sắp khóa, Unicode NFC).
2. **Lệch ERD tài liệu 04 Bảng 5.** Các cột `kind`, `prompt`, `options`, `grading_strategy` vẫn ở `exercises` nhưng chỉ là **bản sao của phiên bản mới nhất trong nguồn**. Không dùng để chấm hay hiển thị. Khi nhóm làm tài liệu bản 2.2, đưa các cột ảnh chụp vào Bảng 5.
3. **Đã phát hành hoặc đã có lượt làm thì khóa.** Không sửa và không xóa được. Muốn sửa thì phát hành `n+1`.
4. **Seed không tự tăng version (2A).** Nội dung khác bản đã khóa thì gom xung đột, rollback toàn bộ và raise `SeedConflictError`. Khi đó API không khởi động. Lý do: tự tăng sẽ làm cùng một câu thành v5 ở máy này nhưng v6 ở máy khác.
5. **Danh tính câu bất biến (3A).** Đổi `lesson_id` hoặc `skill_id` thì phải tạo câu mới với id mới.
6. **Nộp vào bản cũ trả 409 (4A).** Mã `EXERCISE_VERSION_SUPERSEDED`, `fields.current_version_id` là bản hiện hành. Frontend báo bằng tiếng Việt, tải lại bài và không tự nộp lại.
7. **Không chấm lại lượt cũ (5A).** Đáp án bản cũ sai thì phát hành bản sửa; kết quả đã lưu giữ nguyên.
8. **Hoàn thành bài (6A).** Đúng ở bất kỳ phiên bản nào của câu cũng được tính. Bài đã `completed` giữ nguyên khi có câu mới. Bài đang học phải làm cả câu mới.
9. **Xóa mềm phải khai báo (7A).** `q(..., retired=True)` thì seed đặt `exercises.deleted_at`. Câu biến khỏi nguồn mà không khai báo thì báo `SEED_EXERCISE_MISSING`.
10. **Draft/published.** `exercise_versions.status`. Bản nháp sửa tại chỗ được khi chưa có lượt làm. `SHOW_DRAFT_CONTENT` mặc định tắt; bật khi `APP_ENV=production` thì API từ chối khởi động. Chỉ Đạt được đổi `draft` thành `published` (nguyên tắc 17).
11. **Phiên bản hiện hành** là bản có số lớn nhất trong các bản được phép hiện. Nếu bản đó `snapshot_origin='missing'` thì ẩn cả câu, không lùi về bản cũ hơn.

## Quyết định nghiệp vụ D-1..D-4 (Phúc xác nhận thay nhóm 27/10/2026)

| Mã | Nội dung | Người ký | Trạng thái |
|---|---|---|---|
| D-1 | `provenance` nằm trong ảnh chụp: sửa nguồn của bản đã phát hành phải tăng version, không sửa âm thầm | Đạt | Phúc xác nhận thay 27/10; Đạt ký bổ sung: ____ |
| D-2 | Đếm "sai 2 lần thì hiện lời giải" theo câu, cộng dồn qua các phiên bản (có test) | Thắng | Phúc xác nhận thay 27/10; Thắng ký bổ sung: ____ |
| D-3 | 24 phiên bản đang chạy để `published` khi migration. Đây là **dữ liệu kế thừa, chưa qua quy trình duyệt mới**, không có nghĩa Đạt đã duyệt từng câu | Đạt | Phúc xác nhận thay 27/10; Đạt ký bổ sung: ____ |
| D-4 | Dùng số ADR-006 | Thắng | Phúc xác nhận thay 27/10; Thắng ký bổ sung: ____ |

## Migration `d3a7f1c2e905` (nối vào `b2c4e6f80a13`)

- Không sửa migration cũ, không xóa hay thêm dòng nào; chỉ thêm cột và điền dữ liệu.
- Ảnh chụp lấy từ `backend/migrations/data/pr3_anh_chup_lich_su.json` (38 phiên bản trích từ git, có SHA-256). Chỉ điền cho phiên bản **đang có trong CSDL**, khi `answer_key`, `grader_config`, `explanation` và danh tính câu khớp git. Riêng bản mới nhất còn phải khớp đề đang lưu trên `exercises`. Không khớp thì `snapshot_origin='missing'`: không bịa đề, lượt làm giữ nguyên, câu đó không hiển thị và không chấm.
- PostgreSQL: trigger `hm_bao_ve_phien_ban_bai_tap` chặn UPDATE/DELETE trực tiếp trên bản đã khóa; trigger `hm_bao_ve_danh_tinh_cau_hoi` chặn đổi bài hoặc kỹ năng của câu đã có phiên bản.
- `downgrade()` từ chối chạy. Đường lùi duy nhất là khôi phục bản sao lưu `pg_dump` chụp trước khi upgrade.

## Giới hạn đã biết

- SQLite (dev/test) và CSDL tạo bằng `create_all` (`AUTO_CREATE_SCHEMA=1`) không có trigger; chỉ có lưới ORM. Câu SQL viết tay trên SQLite vẫn sửa được phiên bản.
- Người có quyền superuser PostgreSQL vẫn tắt được trigger. Đây là bảo vệ chống lỗi, không phải chống phá hoại.
- Flashcard (`review_items`) và `lesson_blocks` vẫn được ghi đè tại chỗ. Xem lại ở GĐ3 (trích dẫn `L0x-Byy`) và GĐ4 (Admin flashcard).
- Phiên bản `missing` không bao giờ được điền lại. Muốn câu hiện lại thì phát hành version mới.

## Ví dụ

`L01-Q01` đang ở v4. Đạt sửa đề trong `curriculum_specs.py` mà quên tăng version. Khi API khởi động, log báo:

`SEED_VERSION_CHANGED L01-Q01-v4 (trường khác: prompt): nội dung khác bản đã khóa...`

API không chạy. Đạt thêm `version=5` rồi chạy lại. Seed tạo `L01-Q01-v5`, còn v4 giữ nguyên cùng mọi lượt làm cũ. Người học đang mở trang cũ bấm "Kiểm tra" thì nhận thông báo "Câu hỏi vừa được cập nhật…" và thấy đề mới.

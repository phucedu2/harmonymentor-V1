# ADR-003 · Ánh xạ 26 kỹ năng của code sang 10 kỹ năng MVP của SRS 4.3

Trạng thái: **Đã chốt** (nhóm chấp nhận N1 18/10/2026; danh sách 12 bài duyệt 19/10/2026). Thực hiện ở Giai đoạn C.

## Bối cảnh

Skill Graph trong code có 26 kỹ năng (gồm secondary dominant, modal interchange, jazz voicing). SRS 4.3 chốt MVP ở 10 kỹ năng: note_names, accidentals, intervals, major_scales, minor_scales, triads, seventh_chords, diatonic_chords, progressions, rhythm_basics. Hệ gợi ý (CP2) và mastery hoạt động trên các kỹ năng này.

## Quyết định

- Thêm cột `skills.srs_code`: một trong 10 mã SRS hoặc `post_mvp`.
- Kỹ năng `post_mvp` vẫn giữ trong đồ thị (không xóa, không mất nguồn), nhưng không vào lộ trình, gợi ý hay mastery của MVP.
- Bảng ánh xạ chi tiết ở `docs/giai-doan/phase-A/PHASE_A_PLAN.md` mục 1.1.
- Kỹ năng SRS chưa có trong code (note_names, minor_scales, rhythm_basics) được thêm mới.

## Hệ quả

- Vector mastery cho KNN (CP2) có đúng 10 chiều, dễ giải thích.
- L05–L08 giữ dạng đặc tả cho bản sau MVP.

## Bổ sung 30/10/2026

- Thắng chốt chuyển `scale.parallel_minor` từ `minor_scales` sang `post_mvp`, vì kỹ năng này không chứng minh được việc dựng âm giai thứ. Mã `minor_scales` tạm chưa có kỹ năng nào. Bảng ở `PHASE_A_PLAN` mục 1.1 là bản lịch sử, không sửa. Bảng hiện hành nằm ở `docs/CP2_ANH_XA_KY_NANG.md`.
- Phần "vector 10 chiều" ở mục Hệ quả sẽ bị thay bằng vector 14 chiều theo `group_code` khi [ADR-008](ADR-008-vector-14-nhom.md) được duyệt. Phần phạm vi MVP giữ nguyên.

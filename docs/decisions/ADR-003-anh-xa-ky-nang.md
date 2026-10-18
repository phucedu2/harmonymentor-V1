# ADR-003 · Ánh xạ 26 kỹ năng của code sang 10 kỹ năng MVP của SRS 4.3

Trạng thái: **Đã chốt hướng** (nhóm chấp nhận N1, 18/10/2026); danh sách bài cụ thể chờ duyệt. Thực hiện ở Giai đoạn C.

## Bối cảnh

Skill Graph trong code có 26 kỹ năng (gồm secondary dominant, modal interchange, jazz voicing). SRS 4.3 chốt MVP ở 10 kỹ năng: note_names, accidentals, intervals, major_scales, minor_scales, triads, seventh_chords, diatonic_chords, progressions, rhythm_basics. Hệ gợi ý (CP2) và mastery hoạt động trên các kỹ năng này.

## Quyết định

- Thêm cột `skills.srs_code`: một trong 10 mã SRS hoặc `post_mvp`.
- Kỹ năng `post_mvp` vẫn giữ trong đồ thị (không xóa, không mất nguồn), nhưng không vào lộ trình, gợi ý hay mastery của MVP.
- Bảng ánh xạ chi tiết ở `docs/PHASE_A_PLAN.md` mục 1.1.
- Kỹ năng SRS chưa có trong code (note_names, minor_scales, rhythm_basics) được thêm mới.

## Hệ quả

- Vector mastery cho KNN (CP2) có đúng 10 chiều, dễ giải thích.
- L05–L08 giữ dạng đặc tả cho bản sau MVP.

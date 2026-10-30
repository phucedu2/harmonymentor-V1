# Phase 0.2 — Stabilize Assessment + Learning Skeleton

## 1. Mục tiêu

Phase này không thêm AI Harmony Assistant. Mục tiêu là làm Assessment Engine đủ đáng tin trước khi kết quả được dùng cho mastery/adaptive learning, đồng thời cho frontend/content workstream tiến song song.

## 2. Red → Green regression evidence

Trước khi sửa source, bộ `test_phase0_regressions.py` được thêm và chạy trên logic v0.1.0:

- 5 failed, 1 passed.
- F01: `G B D F F#` có thể bị chấm đúng.
- F03: `C E D F G A B` bị gán `NOT_IN_KEY` thay vì lỗi thứ tự bậc.
- F04: pattern tap rỗng + BPM 0 có thể trả `correct=true`; dữ liệu NaN/Infinity chưa bị chặn.

Sau khi sửa:

- regression file: 7 passed;
- full backend suite: **95 passed, 1 skipped**.

## 3. Quyết định grading đã áp dụng

### Full-chord exercise

`grade_build_chord` đang chấm **full chord-tone inventory**, không phải jazz voicing.

- order không quan trọng;
- thiếu tone: sai;
- thêm tone: sai;
- duplicate tone: sai;
- spelling vẫn được kiểm tra theo grading mode.

Jazz voicing sẽ có rubric riêng ở module `voicing/assessment` sau này vì voicing hợp lệ có thể cố ý lược/double tone.

### Correctness và diagnostics

Correctness dùng multiset độc lập. Diagnostics chỉ giải thích *vì sao sai*; diagnostics rỗng không thể biến một answer sai thành correct.

### Scale order

`WRONG_SCALE_DEGREE_ORDER` là mã đề xuất mới. Ví dụ D/E bị đổi chỗ trong C major không còn bị mô tả là “ngoài giọng”.

### Rhythm input

`grade_taps` hiện từ chối:

- expected pattern rỗng;
- BPM không hữu hạn hoặc <= 0;
- tolerance không hữu hạn hoặc <= 0;
- expected beats không hữu hạn/âm/không tăng;
- tap time không hữu hạn.

## 4. Frontend workstream

`App.tsx` trở thành app shell với 5 vùng:

- Dashboard
- Learn
- Practice
- Harmony Lab
- Progress

Prototype 4 bài cũ chuyển vào `pages/Practice.tsx`, không bị xóa.

## 5. Content workstream

`frontend/src/content/lessons.ts` hiện có:

- 8 lesson MVP;
- 6 quiz/lesson = 48 quiz;
- 8 flashcard/lesson = 64 flashcards;
- quiz kinds: `mcq`, `active_recall`, `build`, `context`, `applied`;
- grading strategies: `exact`, `music_engine`, `rubric`;
- source mapping sơ bộ cho từng lesson.

Tất cả lesson đang `draft`. Không coi các câu hỏi `rubric` là đã có grader tự động.

## 6. Chưa làm trong Phase 0.2

- DB/Alembic;
- Review scheduler persistence;
- ChordInspector endpoint;
- Tone.js/VexFlow;
- Harmony Lab thật;
- AI orchestration;
- MIDI;
- lesson renderer end-to-end.

## 7. Bước kế tiếp

**Phase 0.3 / 0.4 — Skeleton API + DB + content contract**, sau đó tạo milestone đầu tiên:

`Lesson 1 → checkpoint → lesson quiz → flashcard → review state`.

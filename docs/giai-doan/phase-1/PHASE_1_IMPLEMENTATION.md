# Phase 1 — Learning Platform Vertical Slice (`v0.4.0-dev`)

Phase 1 chuyển Lessons 1–4 từ content/API demo thành một learning flow có trạng thái thật:

```text
Dashboard
  -> Learn
  -> Lesson blocks
  -> inline checkpoints
  -> final lesson quiz
  -> persisted attempts/progress
  -> complete lesson
  -> activate spaced-review queue
  -> Progress / Review
```

## 1. LessonRenderer V2

`frontend/src/components/learning/LessonRunner.tsx` đã được viết lại theo flow học thay vì hiển thị toàn bộ content/quiz/flashcard như một trang debug.

- hiển thị learning objectives;
- render block theo loại (`theory`, `callout`, `progression`, `interactive`, `piano`, `summary`, `checkpoint`);
- 2 checkpoint inline/lesson;
- final quiz chỉ chứa các exercise chưa dùng làm checkpoint;
- progress bar dựa trên số exercise distinct đã attempt;
- completion button chỉ bật ở UI sau khi đã attempt đủ 6 exercise;
- review items chỉ preview trước khi complete; ReviewState thật vẫn được tạo ở backend;
- sources được chuyển xuống panel tham khảo để lesson bớt giống trang debug.

Backend completion API vẫn idempotent và không hard-gate bằng số attempt để không làm thay đổi contract dữ liệu cũ; gate của Phase 1 là UX policy.

## 2. Checkpoint contract

Lessons L01–L04 hiện có 7 blocks thay vì 5: 5 content blocks + 2 checkpoint blocks.

Checkpoint không copy question. Payload chỉ tham chiếu `exercise_id`, vì vậy cùng một audited `ExerciseVersion` được dùng cho inline checkpoint và evidence persistence.

Ví dụ:

```json
{
  "block_type": "checkpoint",
  "payload": {
    "exercise_id": "L04-Q04",
    "title": "Checkpoint · Guide tones"
  }
}
```

`seed_data._upsert_blocks()` rebuild block sequence theo lesson để việc chèn checkpoint không va chạm unique constraint `(lesson_id, position)` trên database Phase 0.4B đã tồn tại.

## 3. ChordInspector UI

Component mới:

```text
frontend/src/components/learning/ChordInspector.tsx
```

Nó gọi contract deterministic đã có:

```text
GET /api/v1/music/chords/inspect?symbol=G7&key=C
```

và hiển thị:

- chord symbol;
- chord quality;
- notes;
- formula;
- bass/inversion nếu có;
- Roman numeral/function nếu context key được cung cấp.

Desktop hỗ trợ hover/focus/click; thiết bị touch dùng click/tap. Progression block L03/L04 render từng chord thành ChordInspector thay vì text chết.

## 4. Learning progress API

Endpoint mới:

```text
POST /api/v1/lessons/{lesson_id}/start
GET  /api/v1/learning/overview?user_id=demo-user
```

Overview tổng hợp trực tiếp từ:

- `LessonProgress`;
- versioned `Attempt`;
- `ExerciseVersion -> Exercise -> Lesson`;
- active `ReviewState`.

Mỗi lesson trả:

- `status` (`not_started`, `started`, `completed`);
- distinct exercise attempted;
- distinct exercise từng trả lời đúng;
- total attempts/correct attempts;
- `practice_progress_percent`;
- attempted/correct exercise IDs.

Không tạo mastery score giả ở Phase 1.

## 5. Dashboard / Learn / Progress

### Dashboard

Đọc `LearningOverview` thật để hiển thị completed/started/review due/upcoming và lesson tiếp theo.

### Learn

Danh sách lesson hiện có trạng thái/progress. L05–L08 chưa runtime nên được khóa thay vì mở trang rỗng.

### Progress

Hiển thị practice evidence theo lesson, review đến hạn và review đã lên lịch. Thẻ đến hạn có thể trả lời trực tiếp qua Review API.

## 6. Những thứ cố tình chưa làm

Phase 1 chưa thêm dependency audio/notation mới:

- Tone.js;
- VexFlow;
- Web MIDI;
- backing track;
- AI Harmony Assistant.

`piano` block đã có vị trí trong LessonRenderer nhưng chỉ hiển thị learning task/phase note. Audio + interactive keyboard thuộc Phase 2.

## 7. Backward compatibility

- Music Engine/legacy Practice API giữ nguyên;
- schema database không đổi, do đó Phase 1 **không cần Alembic migration mới**;
- 2 migration cũ vẫn là head hợp lệ;
- source-audited 48 quiz/64 review bank không bị mở rộng;
- Lessons 5–8 vẫn là `source_audited` specs only.

## 8. Verification

Backend fresh SQLite:

```text
113 passed, 1 skipped
```

Skip là optional `music21` cross-check.

Alembic:

```text
upgrade head -> alembic check
No new upgrade operations detected.
```

Frontend source syntax:

```text
12 TS/TSX files transpiled
0 syntax diagnostics
```

`npm ci` trong môi trường đóng gói bị gián đoạn khi tải dependency và để lại package folders không hoàn chỉnh, vì vậy không tuyên bố production `npm run build` pass. `node_modules` đó bị loại khỏi artifact. Trên máy phát triển cần chạy sạch `npm install && npm run build`.

## 9. Definition of Done Phase 1

- L01–L04 mở từ Learn và tự tạo `started` progress.
- 2 inline checkpoint/lesson dùng cùng persisted exercise contract.
- final quiz lưu Attempt thật.
- progress list survives refresh vì đọc lại DB.
- progression L03/L04 có ChordInspector UI.
- complete lesson kích hoạt 8 review cards.
- Dashboard/Progress đọc aggregate state thật.
- backend regression suite xanh.

## 10. Bước tiếp theo

**Phase 2 — Interactive Music Layer**:

1. Virtual Piano V2 (input + octave-aware pitches);
2. Tone.js AudioEngine (piano playback + metronome);
3. VexFlow notation blocks;
4. nối `PIANO`, `AUDIO`, `NOTATION` blocks vào Lessons 1–4;
5. keyboard exercise evidence ở mức tối thiểu;
6. chỉ sau đó mới sang Harmony Lab/AI progression assistance.

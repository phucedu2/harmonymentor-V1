# ADR-010 (đề xuất) · Harmony Lab tối thiểu: Composition Engine theo luật và bảng dự án

Trạng thái: **Đề xuất 31/10/2026**, nhánh `phuc-music` (Draft PR #18). Phúc chọn làm Bước 4 ngay (câu 1A) và kèm ADR này để Thắng ký. Schema dự án làm theo ERD tài liệu 04 (câu 9A), phần nào lệch ERD thì cần Thắng duyệt. Phúc chọn phương án không thay cho việc Thắng duyệt. Luật nhạc lý và lời giải thích tiếng Việt cần Astra kiểm.

## Bối cảnh

- FR-17 (Harmony Lab) và FR-18 (gợi ý hợp âm) được tài liệu 04 xếp vào Giai đoạn 2. Mục 6.8 mô tả dữ liệu dự án, Bảng 8 liệt kê bảng, Bảng 23 liệt kê phép biến đổi, Bảng 24 liệt kê cảnh báo và Bảng 25 mô tả bố cục màn hình.
- Mục tiêu của người mới (Phúc): (A) dựng được backing track và (B) làm được vòng hợp âm lạ mà vẫn nghe được, đồng thời hiểu vì sao nó lạ.
- Hiện chưa có lớp AI nào trong code. Không có client LLM, không có `AI_ENABLED` (đó là phần việc của Đạt). Nguyên tắc 2, 3 và 5 yêu cầu AI chỉ xếp hạng hoặc giải thích, và mọi thứ phải chạy khi tắt AI.

## Quyết định đề xuất

1. **Composition Engine nằm ở `backend/app/composition/`** (SRS 10.4, N8), tách khỏi Music Engine. Module này chỉ chứa luật soạn nhạc. Mọi hợp âm, tên nốt và cao độ đều dựng bằng Music Engine (`transpose`, `build_chord`, `diatonic_chords`, `roman_numeral`, `chord_tones`). Hành vi của Music Engine không đổi.
2. **5 nhóm luật, mức độ lạ 0–3** (câu 8A của Phúc):

   | Mức | Luật | Ví dụ trong C trưởng |
   |---|---|---|
   | 0 | Thay hợp âm cùng chức năng (chủ I/iii/vi, hạ át ii/IV, át V/vii°) | C → Am |
   | 1 | Hợp âm át phụ V7/x cho hợp âm ở ô sau | C → E7 khi ô sau là Am |
   | 1 | Mượn hợp âm từ giọng thứ cùng tên: iv, ♭VI, ♭VII, ♭III | F → Fm, G → Bb |
   | 2 | Màu điệu thức: Mixolydian v, Lydian II, Dorian i (rõ nhất khi đi tới IV) | G → Gm, F → D |
   | 2 | Thay thế tritone cho hợp âm át | G → Db7 |
   | 3 | Chromatic mediant: cùng loại hợp âm, nốt gốc cách một quãng 3, nằm ngoài giọng | C → E, Ab, A |

   Ứng viên nào có nốt gốc mang dấu kép (ví dụ Bbb) thì bị bỏ, vì Engine chưa đọc được ký hiệu đó. Hệ thống không tự đổi sang tên đồng âm.
3. **Phân tích** (bài cuối khóa chỉ phân tích, không chấm, câu 10A):
   - Mỗi ô được gán một luật, một nhãn (I, V7/vi, ♭VI, subV7…), một mức độ lạ và một lý do tiếng Việt.
   - Có cảnh báo `NOT_IN_KEY` và `UNRESOLVED_DOMINANT` (Bảng 24). Cảnh báo không chặn lựa chọn.
   - `GRID_OVERFLOW` và `MELODY_CLASH` chưa áp dụng, vì lưới mỗi ô chỉ có một hợp âm và chưa có giai điệu.
4. **AI chưa tham gia.**
   - API trả `ranked_by: "rule"` và `ai_used: false`.
   - Khi lớp AI của Đạt sẵn sàng, AI chỉ được xếp lại thứ tự và viết lại lời giải thích của các ứng viên này (theo JSON schema). AI không được thêm hợp âm mới.
   - Nếu AI lỗi thì dùng thứ tự theo luật.
5. **Bảng dự án**: migration `f6a2b3c4d5e7` nối sau `e5f1a2b3c4d6`.

   | Bảng | Cột | So với ERD Bảng 8 |
   |---|---|---|
   | `composition_projects` | `id`, `user_id`, `name`, `key`, `tempo_bpm` (CHECK 60–160), `time_signature` (mặc định 4/4), `bars` (CHECK 4–8), `style`, `is_test`, `created_at`, `updated_at`, `deleted_at` | **Thêm** `style`, `created_at`, `updated_at` |
   | `chord_events` | `id`, `project_id`, `start_beat`, `duration_beats`, `symbol` | Đúng ERD (mỗi ô một hợp âm, 4 phách) |
   | `drum_events` | `id`, `project_id`, `drum` (kick/snare/hat), `start_beat`, `velocity` | Đúng ERD; trải ra từ mẫu nền lúc lưu |
   | `note_events`, `ai_suggestions` | | **Chưa tạo**: chưa có giai điệu, và gợi ý không lưu |

6. **API**:

   | Phương thức | Đường dẫn | Ai dùng được | Ghi chú |
   |---|---|---|---|
   | GET | `/api/v1/composition/options` | Công khai | Giọng (chỉ trưởng, QĐ-2.2) kèm hợp âm trong giọng, 4 mẫu nền, bảng mức độ lạ |
   | POST | `/api/v1/composition/voicings` | Công khai | Cao độ kèm quãng tám và nốt bass do Engine dựng, để phát và vẽ khuông |
   | POST | `/api/v1/composition/suggestions` | Người học | |
   | POST | `/api/v1/composition/analyze` | Người học | |
   | CRUD | `/api/v1/projects`, `/api/v1/projects/{id}` | Chủ dự án | Người khác nhận 404; xóa là xóa mềm; Admin có `is_test` |

7. **Mẫu nền** pop, ballad, bossa và lo-fi (`presets.py`):
   - Mỗi mẫu gồm trống, bass (nốt gốc/nốt năm) và nhịp đánh hợp âm, tính theo phách.
   - Mẫu do Claude soạn theo cách chơi phổ biến, chưa có nguồn đối chiếu. Nhóm nghe thử rồi chỉnh.
   - Frontend phát bằng Tone.js theo thời gian nhạc của Transport, nên đổi tempo không làm lệch các kênh.

## Phương án khác đã cân nhắc

- **Đặt luật vào Music Engine:**
  - Ưu điểm: một chỗ duy nhất.
  - Nhược điểm: phải sửa Engine và cần ADR riêng. Luật soạn nhạc lại không phải sự thật nhạc lý.
- **Lưu gợi ý vào `ai_suggestions` và chấp nhận qua `/suggestions/{id}/accept`** (tài liệu 04 ghi là hướng phát triển):
  - Ưu điểm: có nhật ký gợi ý để sau này đánh giá AI.
  - Nhược điểm: thêm bảng và API trong khi chưa có AI. Bản tối thiểu giữ nguyên tắc 5 ở giao diện: người học bấm "Dùng hợp âm này" rồi tự lưu.
- **Không thêm cột `style`, tự suy mẫu nền từ `drum_events`:**
  - Nhược điểm: không biết bass và nhịp đánh hợp âm, và mở lại dự án sẽ mất lựa chọn.

## Hệ quả

- Người học dựng được vòng hợp âm, nghe lặp với nhạc nền và lưu lại. Họ xin được gợi ý lạ tai kèm lý do, và đọc được vì sao cả vòng nghe lạ. Tất cả chạy mà không cần AI.
- Chỉ hỗ trợ giọng trưởng và mỗi ô một hợp âm.
- Còn mở:
  - Giai điệu (`note_events`), biến đổi "Dịch giọng" của Bảng 23 (hiện mới đổi theo bậc khi đổi giọng), nhật ký gợi ý, và xếp hạng bằng AI.
  - Thắng duyệt schema. Astra kiểm 5 luật và lời giải thích.

## Kiểm chứng

- `backend/tests/test_phuc_music_harmony_lab.py`:
  - luật cho C trưởng và đủ 15 giọng trưởng;
  - nốt ứng viên khớp `chord_tones`;
  - phân tích và cảnh báo;
  - chủ dự án, 404, xóa mềm, `is_test`, thời gian theo phách.
- `backend/tests/test_phuc_music_composition_migration.py`: migration khớp model và gỡ được.
- `frontend/tests/harmonyLab.test.ts`: lịch phát và lưới.
- `scripts/phuc-music/luong_buoc4_harmony_lab.cjs`: kịch bản người mới, mục tiêu A và B.

# Duyệt câu hỏi và thẻ ôn L05–L08

Người duyệt: **Đạt**. Lý thuyết đã duyệt (L05: caff321; L06–L08: PR #43). Phần dưới **chưa duyệt**: đang ở dạng nháp,
người học chưa thấy (chỉ hiện khi bật `SHOW_DRAFT_CONTENT`). Thẻ ôn chưa nạp vào CSDL.

Cách duyệt: tick ô "Đạt duyệt" hoặc ghi sửa ở cột "Ghi chú". Duyệt xong: chuyển id bài từ
`PENDING_REVIEW_LESSON_IDS` sang `MIGRATED_LESSON_IDS` trong `backend/app/content/curriculum_specs.py` (câu phát hành, thẻ ôn
được nạp, bài hoàn thành được). Câu đã phát hành thì bị khóa: sửa sau phải tăng `version` (ADR-006).

Cột "Music Engine": ✅ khớp, ❌ lệch; câu khái niệm thì Engine không kiểm được.

## L05 Secondary Dominants

### Câu hỏi

| Mã | Dạng | Đề | Lựa chọn | Đáp án | Music Engine | Đạt duyệt | Ghi chú |
|---|---|---|---|---|---|---|---|
| L05-Q01 | mcq | Trong C major, V7/ii là hợp âm nào? | A7, D7, E7, C7 | A7 | ký hiệu hợp lệ: A7 = A C# E G | ☐ |  |
| L05-Q02 | mcq | Trong C major, V7/V là hợp âm nào? | G7, D7, A7, B7 | D7 | ký hiệu hợp lệ: D7 = D F# A C | ☐ |  |
| L05-Q03 | active_recall | Trong C major, V7/vi là gì? | — | E7 | ký hiệu hợp lệ: E7 = E G# B D | ☐ |  |
| L05-Q04 | context | Trong C major, A7 → Dm7: A7 được phân tích thế nào? | — | V7/ii | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L05-Q05 | applied | Chọn cách thêm secondary dominant để tăng lực đi tới Am trong C major. | E7-Am, D7-Am, C7-Am, F7-Am | E7-Am | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L05-Q06 | mcq | Một secondary dominant có bắt buộc thiết lập tonic mới lâu dài không? | Có, Không | Không | — (khái niệm, Đạt kiểm tay) | ☐ |  |

### Thẻ ôn

| Mã | Mặt trước | Mặt sau | Đạt duyệt | Ghi chú |
|---|---|---|---|---|
| L05-F01 | V7/ii in C | A7 | ☐ |  |
| L05-F02 | V7/V in C | D7 | ☐ |  |
| L05-F03 | V7/vi in C | E7 | ☐ |  |
| L05-F04 | A7 → Dm7 in C | A7 = V7/ii | ☐ |  |
| L05-F05 | D7 → G7 in C | D7 = V7/V | ☐ |  |
| L05-F06 | E7 → Am7 in C | E7 = V7/vi | ☐ |  |
| L05-F07 | Secondary dominant làm gì? | Tạm thời tonicize/emphasize một chord đích bằng dominant-function harmony. | ☐ |  |
| L05-F08 | Secondary dominant = modulation hoàn chỉnh? | Không nhất thiết; tonicization có thể rất ngắn. | ☐ |  |

## L06 Modal Interchange trong Pop/Contemporary

### Câu hỏi

| Mã | Dạng | Đề | Lựa chọn | Đáp án | Music Engine | Đạt duyệt | Ghi chú |
|---|---|---|---|---|---|---|---|
| L06-Q01 | mcq | Trong C major, Fm thường được hiểu là borrowed chord nào? | ii, iv, V/V, bII | iv | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L06-Q02 | mcq | Parallel minor của C major là gì? | A minor, C minor, E minor, F minor | C minor | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L06-Q03 | active_recall | Trong C major, borrowed ♭VI triad từ parallel minor có root nào? | — | Ab | ký hiệu hợp lệ: Ab = Ab C Eb | ☐ |  |
| L06-Q04 | context | Trong C–F–Fm–C, chord nào tạo modal-mixture color rõ nhất? | — | Fm | ký hiệu hợp lệ: Fm = F Ab C | ☐ |  |
| L06-Q05 | mcq | Modal mixture có nhất thiết đổi harmonic function của chord không? | Luôn đổi, Không nhất thiết, Luôn thành dominant, Luôn thành tonic | Không nhất thiết | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L06-Q06 | applied | Chọn progression biến C–G–Am–F thành một phiên bản có borrowed iv. | C-G-Am-Fm, C-G-Am-G, C-D7-Am-F, C-G-E7-F | C-G-Am-Fm | — (khái niệm, Đạt kiểm tay) | ☐ |  |

### Thẻ ôn

| Mã | Mặt trước | Mặt sau | Đạt duyệt | Ghi chú |
|---|---|---|---|---|
| L06-F01 | Parallel minor của C major | C minor | ☐ |  |
| L06-F02 | iv borrowed in C major | Fm | ☐ |  |
| L06-F03 | ♭VI borrowed triad in C major | Ab | ☐ |  |
| L06-F04 | ♭VII borrowed triad in C major | Bb | ☐ |  |
| L06-F05 | C–F–Fm–C: Fm = ? | Borrowed iv / modal mixture | ☐ |  |
| L06-F06 | Modal mixture thường vay mượn giữa loại key nào? | Parallel major/minor | ☐ |  |
| L06-F07 | Borrowed chord có bắt buộc modulation? | Không. | ☐ |  |
| L06-F08 | Modal mixture chủ yếu thay đổi gì ở chord trong khung OMT? | Quality/color; function không nhất thiết đổi. | ☐ |  |

## L07 Jazz Tensions, Modes và Chord-Scale Context

### Câu hỏi

| Mã | Dạng | Đề | Lựa chọn | Đáp án | Music Engine | Đạt duyệt | Ghi chú |
|---|---|---|---|---|---|---|---|
| L07-Q01 | mcq | Các extension/tension number cơ bản phía trên seventh chord là bộ nào? | 2, 4, 6, 9, 11, 13, 1, 3, 5, 7, 8, 10 | 9, 11, 13 | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L07-Q02 | build | Dựng Cmaj7 chord tones trước khi thêm tension. | — | ['C', 'E', 'G', 'B'] | ✅ Cmaj7 = C E G B | ☐ |  |
| L07-Q03 | mcq | Trong basic ii–V–I chord-scale model ở C, Dm7 thường liên hệ với mode nào? | D Ionian, D Dorian, D Mixolydian, D Locrian | D Dorian | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L07-Q04 | mcq | Trong cùng model, G7 thường liên hệ với mode nào? | G Dorian, G Ionian, G Mixolydian, G Aeolian | G Mixolydian | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L07-Q05 | mcq | Trong cùng model, Cmaj7 thường liên hệ với mode nào? | C Ionian, C Dorian, C Mixolydian, C Locrian | C Ionian | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L07-Q06 | context | Vì sao không nên coi chord-scale table là một đáp án duy nhất cho mọi chord symbol? | — | ['ngữ cảnh', 'ngu canh', 'function', 'chức năng', 'chuc nang', 'voice leading', 'melody'] | — (khái niệm, Đạt kiểm tay) | ☐ |  |

### Thẻ ôn

| Mã | Mặt trước | Mặt sau | Đạt duyệt | Ghi chú |
|---|---|---|---|---|
| L07-F01 | Tension/extension numbers | 9, 11, 13 | ☐ |  |
| L07-F02 | Chord tones của Cmaj7 | C–E–G–B | ☐ |  |
| L07-F03 | Dm7 in C major: basic chord-scale | D Dorian | ☐ |  |
| L07-F04 | G7 in C major: basic chord-scale | G Mixolydian | ☐ |  |
| L07-F05 | Cmaj7 in C major: basic chord-scale | C Ionian | ☐ |  |
| L07-F06 | Chord-scale choice nên bắt đầu từ điều gì? | Key center + harmonic function/context | ☐ |  |
| L07-F07 | Chord tone vs tension | Chord tone định hình chord; tension mở rộng màu sắc theo context. | ☐ |  |
| L07-F08 | Chord-scale theory có thay thế ear/voice leading không? | Không; đó là một công cụ, có giới hạn. | ☐ |  |

## L08 Jazz Piano Voicing: shell voicing và guide-tone connection

### Câu hỏi

| Mã | Dạng | Đề | Lựa chọn | Đáp án | Music Engine | Đạt duyệt | Ghi chú |
|---|---|---|---|---|---|---|---|
| L08-Q01 | mcq | Trong basic shell/3-note frame của lesson, ba thành phần ưu tiên là gì? | Root-3rd-7th, Root-5th-9th, 3rd-5th-9th, Root-2nd-5th | Root-3rd-7th | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L08-Q02 | mcq | Theo OMT Jazz Voicings, chord tone nào thường có thể lược bỏ an toàn nhất trong nhiều voicing? | Root, Third, Fifth, Seventh | Fifth | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L08-Q03 | build | Nêu shell root–3rd–7th cho G7 bằng ba tên nốt. | — | ['g b f', 'g,b,f', 'g-b-f'] | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L08-Q04 | mcq | Smooth/lazy voice leading ưu tiên điều gì? | Move each voice as little as possible, Always jump by fifth, Always keep root on top, Always double the third | Move each voice as little as possible | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L08-Q05 | context | Trong G7 → Cmaj7, basic guide-tone connection nào phù hợp với lesson? | B stays; F moves to E, B moves to F; F stays, Both move up an octave, B moves to C; F moves to G | B stays; F moves to E | — (khái niệm, Đạt kiểm tay) | ☐ |  |
| L08-Q06 | applied | Vì sao bài 'dựng đầy đủ G7' và bài 'tạo shell voicing G7' không dùng cùng rubric? | — | ['voicing', 'lược', 'luoc', 'omit', 'full chord', 'inventory'] | — (khái niệm, Đạt kiểm tay) | ☐ |  |

### Thẻ ôn

| Mã | Mặt trước | Mặt sau | Đạt duyệt | Ghi chú |
|---|---|---|---|---|
| L08-F01 | Basic shell frame | Root–3rd–7th | ☐ |  |
| L08-F02 | G7 shell root–3–7 | G–B–F | ☐ |  |
| L08-F03 | Dm7 shell root–3–7 | D–F–C | ☐ |  |
| L08-F04 | Cmaj7 shell root–3–7 | C–E–B | ☐ |  |
| L08-F05 | Common tone có ích gì trong voice leading? | Giảm chuyển động và nối voicings mượt hơn. | ☐ |  |
| L08-F06 | OMT: smooth/lazy voice leading | Move each voice as little as possible. | ☐ |  |
| L08-F07 | G7 → Cmaj7: guide-tone pair | B stays; F → E | ☐ |  |
| L08-F08 | Chord formula vs voicing | Formula = chord-member inventory; voicing = cách phân bố/omit/double các nốt trong context. | ☐ |  |

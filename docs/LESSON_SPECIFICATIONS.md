# Lesson Specifications — Phase 2.3

Bank chuẩn hóa: **8 lessons / 48 quiz / 64 flashcards**. `curriculum_specs.py` là canonical source; file này là snapshot phục vụ review.

> **Quy tắc sửa câu hỏi (PR-3, ADR-006).** Phiên bản đã phát hành là bất biến; seed gặp nội dung lệch sẽ dừng và báo `SeedConflictError`.
> - Sửa đề, lựa chọn (kể cả thứ tự), loại câu, cách chấm, đáp án, cấu hình chấm, lời giải hoặc nguồn: tăng `version=n+1` trong `q(...)`.
> - Đổi kỹ năng hoặc chuyển bài: tạo id câu mới, câu cũ đặt `retired=True`.
> - Bỏ câu: đặt `retired=True`, không xóa mục khỏi file. Đổi thứ tự câu trong bài thì sửa thẳng.
> - Câu mới do Claude soạn: `status="draft"`; chỉ Đạt đổi thành `"published"`. Bản nháp chưa ai làm thì sửa thẳng được.
> - Đáp án bản cũ sai: phát hành bản sửa; lượt làm cũ giữ nguyên kết quả.

## L01 — Từ bàn phím đến hợp âm ba nốt

**Objectives**
- Nhận biết tên nốt và tự đếm được nửa cung trên bàn phím piano.
- Hiểu cách đếm số quãng và đọc các ký hiệu M3, m3, P5, d5.
- Dựng hợp âm trưởng, thứ và giảm bằng đúng tên nốt thay vì học thuộc một hợp âm C.
- Khám phá hợp âm chủ trên 12 nốt gốc và luyện dần 12 giọng trưởng + 12 giọng thứ.

**Target skills**
`pitch.spelling`, `interval.naming`, `chord.triad_formula`, `chord.triad_build`

**Sources**
- `OMT_V2` — Fundamentals → Intervals
- `OMT_V2` — Fundamentals → Triads
- `FANK_WIH` — Unit 1: Music Fundamentals — scales, intervals, triads
- `TEREFENKO_WB` — Part I, Ch.1 Music Fundamentals, PDF pp. 13–22

**Runtime block sequence**
- `L01-B01` [callout] — Bài này bắt đầu từ con số 0
- `L01-B02` [theory] — 1. Tên nốt và bàn phím piano
- `L01-B03` [piano] — Thử ngay: đếm số bước chứ không đếm số phím
- `L01-B04` [theory] — 2. Đếm số quãng và viết đúng tên nốt
- `L01-B05` [glossary] — 3. Năm chữ cái mô tả chất lượng quãng
- `L01-B06` [interval_explorer] — 4. Khám phá M3, m3, P5 và d5 trên 12 nốt gốc
- `L01-BCP1` [checkpoint] — Checkpoint · Đọc một quãng mới
- `L01-B08` [theory] — 5. Hợp âm ba nốt: dựng bằng hai bước
- `L01-B09` [triad_explorer] — 6. Dựng triad trên bất kỳ nốt gốc nào
- `L01-BCP2` [checkpoint] — Checkpoint · Dựng hợp âm ở nốt gốc khác C
- `L01-B10` [triad_notation_explorer] — 7. So sánh chất lượng hợp âm bằng cùng một nốt gốc
- `L01-B11` [triad_audio_explorer] — 8. Nghe sự thay đổi khi giữ nguyên nốt gốc
- `L01-B12` [key_overview] — 9. Tổng quan 24 Keys · 12 Major & 12 Minor
- `L01-B13` [summary] — 10. Tóm tắt trước khi làm quiz

**Quiz contract**
- `L01-Q01` [mcq/exact] `interval.naming` — Quãng từ F lên A là gì?
- `L01-Q02` [build/music_engine] `chord.triad_build` — Dựng hợp âm G major bằng tên nốt. Nhập ba nốt theo cùng một định dạng, ví dụ Nốt-Nốt-Nốt.
- `L01-Q03` [active_recall/exact] `chord.triad_formula` — Không nhìn đáp án: công thức minor triad là gì? Nhập theo định dạng như 1-3-5 (dùng chữ b thay cho ♭).
- `L01-Q04` [build/music_engine] `chord.triad_build` — Dựng hợp âm D minor bằng tên nốt. Nhập ba nốt, có thể ngăn cách bằng dấu -, khoảng trắng hoặc dấu phẩy.
- `L01-Q05` [context/rubric] `pitch.spelling` — F# và Gb có thể là cùng một phím trên piano. Điều đó có nghĩa chúng luôn được viết cùng một tên trong mọi ngữ cảnh không? Trả lời ngắn: Có hoặc Không.
- `L01-Q06` [build/music_engine] `chord.triad_build` — Dựng hợp âm B diminished. Nhập ba nốt, có thể ngăn cách bằng dấu -, khoảng trắng hoặc dấu phẩy.

**Review contract**
- `L01-F01` [recall/exact] `interval.naming` — Quãng F–A?
- `L01-F02` [recall/exact] `interval.naming` — Quãng D–F?
- `L01-F03` [recall/exact] `interval.naming` — Quãng G–D?
- `L01-F04` [recall/exact] `interval.naming` — Quãng B–F?
- `L01-F05` [build/music_engine] `chord.triad_build` — Build F major
- `L01-F06` [build/music_engine] `chord.triad_build` — Build A minor
- `L01-F07` [build/music_engine] `chord.triad_build` — Build B diminished
- `L01-F08` [context/rubric] `pitch.spelling` — Muốn viết một quãng 3 phía trên D, nốt trên phải thuộc họ chữ nào?

## L02 — Âm giai trưởng và hợp âm bảy điệu tính

**Objectives**
- Dựng âm giai trưởng đúng thứ tự bậc và spelling.
- Nhận diện chất lượng hợp âm bảy điệu tính trong major key.
- Dùng chord symbol và Roman numeral cơ bản cho seventh chords.

**Target skills**
`scale.major`, `chord.seventh_quality`, `chord.seventh_build`, `roman.major_seventh`

**Sources**
- `OMT_V2` — Fundamentals → Seventh Chords
- `OMT_V2` — Fundamentals → Roman Numerals
- `FANK_WIH` — Unit 1: Music Fundamentals — scales, intervals, triads
- `FANK_WIH` — Unit 2: Diatonic Harmony — Roman-numeral analysis, dominant seventh, diatonic seventh chords, smooth voice leading
- `TEREFENKO_WB` — Part I, Chs.4–5 Four-Part/Five-Part Chords, PDF pp. 29–43

**Runtime block sequence**
- `L02-B01` [callout] — Trước khi học seventh chord
- `L02-B02` [theory] — 1. Âm giai trưởng là một chuỗi 7 bậc
- `L02-B03` [notation] — 2. G major trên khuông
- `L02-BCP1` [checkpoint] — Checkpoint · Dựng major scale
- `L02-B04` [theory] — 3. Từ triad đến seventh chord
- `L02-B05` [glossary] — 4. Giải mã maj7, m7, 7, ø7 và số La Mã
- `L02-B06` [piano] — 5. Nghe bốn màu seventh chord
- `L02-BCP2` [checkpoint] — Checkpoint · Roman numeral
- `L02-B07` [audio] — 6. Nghe Cmaj7 và G7
- `L02-B08` [summary] — Ghi nhớ

**Quiz contract**
- `L02-Q01` [build/music_engine] `scale.major` — Dựng âm giai G major theo thứ tự đi lên, không lặp lại chủ âm ở cuối.
- `L02-Q02` [build/music_engine] `chord.seventh_build` — Dựng Cmaj7 đầy đủ bằng tên nốt.
- `L02-Q03` [active_recall/music_engine] `roman.major_seventh` — Trong C major, Dm7 mang Roman numeral nào?
- `L02-Q04` [mcq/exact] `chord.seventh_quality` — Trong C major, hợp âm bảy trên bậc V là gì?
- `L02-Q05` [mcq/exact] `chord.seventh_quality` — Trong C major, hợp âm bảy trên bậc vii là gì?
- `L02-Q06` [build/music_engine] `chord.seventh_build` — Dựng G7 đầy đủ bằng tên nốt.

**Review contract**
- `L02-F01` [build/music_engine] `scale.major` — G major scale
- `L02-F02` [build/music_engine] `chord.seventh_build` — Build Cmaj7
- `L02-F03` [build/music_engine] `chord.seventh_build` — Build Dm7
- `L02-F04` [context/exact] `roman.major_seventh` — V7 in C major
- `L02-F05` [context/exact] `roman.major_seventh` — ii7 in C major
- `L02-F06` [context/exact] `roman.major_seventh` — viiø7 in C major
- `L02-F07` [recall/rubric] `chord.seventh_quality` — Dominant seventh = triad quality + seventh quality?
- `L02-F08` [recall/music_engine] `roman.major_seventh` — Roman numeral của Dm7 trong C major

## L03 — Chức năng hòa âm: Tonic – Predominant/Subdominant – Dominant

**Objectives**
- Phân biệt tonic, predominant/subdominant và dominant trong một major-key phrase đơn giản.
- Phân tích chức năng theo ngữ cảnh thay vì chỉ nhìn chord symbol.
- Nhận diện luồng T → PD → D → T trong progression ngắn.

**Target skills**
`function.tonic`, `function.predominant`, `function.dominant`, `function.progression`

**Sources**
- `OMT_V2` — Introduction to Harmony, Cadences, and Phrase Endings
- `FANK_WIH` — Unit 2: Diatonic Harmony — Roman-numeral analysis, dominant seventh, diatonic seventh chords, smooth voice leading
- `TEREFENKO_WB` — Part I, Ch.3 Harmonic Function, PDF pp. 25–28
- `KHAIHOAN_JAZZ` — Ch.1, printed pp. 21–37

**Runtime block sequence**
- `L03-B01` [callout] — Chức năng hòa âm không phải tên loại hợp âm
- `L03-B02` [glossary] — 1. Ba chức năng nền tảng
- `L03-B03` [theory] — 2. Luồng T → PD → D → T
- `L03-BCP1` [checkpoint] — Checkpoint · Tonic function
- `L03-B04` [progression] — 3. Ví dụ chức năng
- `L03-B05` [audio] — 4. Nghe lực đi–về
- `L03-BCP2` [checkpoint] — Checkpoint · Dominant trong ngữ cảnh
- `L03-B06` [interactive] — 5. Tự phân tích trước khi xem đáp án
- `L03-B07` [summary] — Ghi nhớ

**Quiz contract**
- `L03-Q01` [mcq/exact] `function.tonic` — Trong C major, Cmaj7 ở vị trí ổn định cuối phrase thuộc chức năng nào?
- `L03-Q02` [mcq/exact] `function.predominant` — Trong Dm7 → G7 → Cmaj7 ở C major, Dm7 thường giữ vai trò nào?
- `L03-Q03` [mcq/exact] `function.dominant` — Trong Dm7 → G7 → Cmaj7, G7 giữ chức năng nào?
- `L03-Q04` [active_recall/rubric] `function.progression` — Viết thứ tự chức năng cơ bản của progression Cmaj7 → Dm7 → G7 → Cmaj7.
- `L03-Q05` [context/rubric] `function.progression` — Vì sao không nên gán chức năng chỉ từ tên hợp âm mà bỏ qua progression xung quanh?
- `L03-Q06` [applied/exact] `function.progression` — Chọn progression thể hiện rõ T → PD → D → T trong C major.

**Review contract**
- `L03-F01` [recall/rubric] `function.tonic` — Tonic function
- `L03-F02` [recall/rubric] `function.predominant` — Predominant/Subdominant function
- `L03-F03` [recall/rubric] `function.dominant` — Dominant function
- `L03-F04` [context/exact] `function.tonic` — Cmaj7 trong C major (ổn định cuối phrase)
- `L03-F05` [context/rubric] `function.predominant` — Dm7 trong Dm7–G7–Cmaj7
- `L03-F06` [context/exact] `function.dominant` — G7 trong Dm7–G7–Cmaj7
- `L03-F07` [recall/rubric] `function.progression` — Functional flow cơ bản
- `L03-F08` [context/rubric] `function.progression` — Function có phải thuộc tính cố định chỉ nhìn chord symbol?

## L04 — ii–V–I và guide-tone voice leading trên piano

**Objectives**
- Nhận diện và transpose ii–V–I major sang một số giọng.
- Xác định 3rd và 7th như guide tones trọng yếu của seventh chords trong bài.
- Mô tả voice leading mượt bằng common tone và chuyển động gần.

**Target skills**
`progression.ii_v_i`, `voicing.guide_tones`, `voicing.voice_leading`

**Sources**
- `OMT_V2` — Jazz → ii–V–I
- `OMT_V2` — Jazz → Jazz Voicings
- `TEREFENKO_WB` — Part I, Ch.6 The II–V–I Progression, PDF pp. 44–46
- `KHAIHOAN_JAZZ` — Ch.1, printed pp. 21–37
- `KHAIHOAN_JAZZ` — Ch.11, printed pp. 279–307

**Runtime block sequence**
- `L04-B01` [callout] — Đọc ii–V–I như thế nào?
- `L04-B02` [glossary] — 1. Guide tones và voice leading
- `L04-B03` [theory] — 2. Xây ii–V–I trong C major
- `L04-B04` [progression] — 3. ii–V–I in C
- `L04-BCP1` [checkpoint] — Checkpoint · Nhận diện ii–V–I
- `L04-B05` [notation] — 4. Guide tones của G7 giải về Cmaj7
- `L04-B06` [theory] — 5. Vì sao 3rd và 7th quan trọng?
- `L04-BCP2` [checkpoint] — Checkpoint · Guide tones
- `L04-B07` [piano] — 6. Piano task · từ chord inventory tới guide tones
- `L04-B08` [audio] — 7. Nghe ii–V–I trước và sau khi tăng tempo
- `L04-B09` [summary] — Ghi nhớ

**Quiz contract**
- `L04-Q01` [mcq/exact] `progression.ii_v_i` — ii–V–I trong C major là progression nào?
- `L04-Q02` [active_recall/exact] `progression.ii_v_i` — Viết ii–V–I trong F major bằng chord symbols.
- `L04-Q03` [build/music_engine] `voicing.guide_tones` — Dựng G7 đầy đủ; đây là bài chord inventory, chưa phải voicing.
- `L04-Q04` [active_recall/rubric] `voicing.guide_tones` — Guide tones cơ bản của G7 là hai nốt nào?
- `L04-Q05` [mcq/exact] `voicing.voice_leading` — Guide-tone motion nào mô tả G7 → Cmaj7 mượt trong lesson này?
- `L04-Q06` [applied/rubric] `voicing.voice_leading` — Mục tiêu chính của smooth/lazy voice leading giữa hai voicing là gì?

**Review contract**
- `L04-F01` [context/exact] `progression.ii_v_i` — ii–V–I in C
- `L04-F02` [context/exact] `progression.ii_v_i` — ii–V–I in F
- `L04-F03` [context/exact] `progression.ii_v_i` — ii–V–I in Bb
- `L04-F04` [build/rubric] `voicing.guide_tones` — Guide tones của G7
- `L04-F05` [build/rubric] `voicing.guide_tones` — Guide tones của Dm7
- `L04-F06` [context/rubric] `voicing.voice_leading` — G7 → Cmaj7: B đi đâu trong basic guide-tone example?
- `L04-F07` [context/exact] `voicing.voice_leading` — G7 → Cmaj7: F đi đâu?
- `L04-F08` [recall/rubric] `voicing.voice_leading` — Nguyên tắc smooth jazz voice leading

## L05 — Secondary Dominants

**Objectives**
- Nhận diện V7/x theo chord đích tạm thời.
- Dựng secondary dominant bằng dominant seventh của chord đích.
- Phân biệt tonicization ngắn với modulation ở mức nhập môn.

**Target skills**
`harmony.secondary_dominant.identify`, `harmony.secondary_dominant.build`, `harmony.secondary_dominant.apply`

**Sources**
- `OMT_V2` — Diatonic Harmony, Tonicization, and Modulation → Tonicization
- `FANK_WIH` — Unit 3: Chromatic Harmony — Secondary Dominants; Mode Mixture
- `KHAIHOAN_JAZZ` — Ch.2, printed pp. 71–102
- `TEREFENKO_WB` — Part II, Ch.13 Idiomatic Jazz Progressions, PDF pp. 82–93

**Quiz contract**
- `L05-Q01` [mcq/exact] `harmony.secondary_dominant.build` — Trong C major, V7/ii là hợp âm nào?
- `L05-Q02` [mcq/exact] `harmony.secondary_dominant.build` — Trong C major, V7/V là hợp âm nào?
- `L05-Q03` [active_recall/exact] `harmony.secondary_dominant.build` — Trong C major, V7/vi là gì?
- `L05-Q04` [context/exact] `harmony.secondary_dominant.identify` — Trong C major, A7 → Dm7: A7 được phân tích thế nào?
- `L05-Q05` [applied/exact] `harmony.secondary_dominant.apply` — Chọn cách thêm secondary dominant để tăng lực đi tới Am trong C major.
- `L05-Q06` [mcq/exact] `harmony.secondary_dominant.identify` — Một secondary dominant có bắt buộc thiết lập tonic mới lâu dài không?

**Review contract**
- `L05-F01` [recall/exact] `harmony.secondary_dominant.build` — V7/ii in C
- `L05-F02` [recall/exact] `harmony.secondary_dominant.build` — V7/V in C
- `L05-F03` [recall/exact] `harmony.secondary_dominant.build` — V7/vi in C
- `L05-F04` [context/exact] `harmony.secondary_dominant.identify` — A7 → Dm7 in C
- `L05-F05` [context/exact] `harmony.secondary_dominant.identify` — D7 → G7 in C
- `L05-F06` [context/exact] `harmony.secondary_dominant.identify` — E7 → Am7 in C
- `L05-F07` [recall/rubric] `harmony.secondary_dominant.identify` — Secondary dominant làm gì?
- `L05-F08` [context/rubric] `harmony.secondary_dominant.identify` — Secondary dominant = modulation hoàn chỉnh?

## L06 — Modal Interchange trong Pop/Contemporary

**Objectives**
- Nhận biết quan hệ parallel major/minor.
- Nhận diện borrowed chord phổ biến trong major-key context.
- Ứng dụng borrowed chord mà không mặc định đó là modulation.

**Target skills**
`scale.parallel_minor`, `harmony.modal_interchange.identify`, `harmony.modal_interchange.apply`

**Sources**
- `OMT_V2` — Chromaticism → Modal Mixture
- `FANK_WIH` — Unit 3: Chromatic Harmony — Secondary Dominants; Mode Mixture
- `KHAIHOAN_JAZZ` — Ch.5, printed pp. 170–188

**Quiz contract**
- `L06-Q01` [mcq/exact] `harmony.modal_interchange.identify` — Trong C major, Fm thường được hiểu là borrowed chord nào?
- `L06-Q02` [mcq/exact] `scale.parallel_minor` — Parallel minor của C major là gì?
- `L06-Q03` [active_recall/exact] `harmony.modal_interchange.identify` — Trong C major, borrowed ♭VI triad từ parallel minor có root nào?
- `L06-Q04` [context/exact] `harmony.modal_interchange.identify` — Trong C–F–Fm–C, chord nào tạo modal-mixture color rõ nhất?
- `L06-Q05` [mcq/exact] `harmony.modal_interchange.identify` — Modal mixture có nhất thiết đổi harmonic function của chord không?
- `L06-Q06` [applied/exact] `harmony.modal_interchange.apply` — Chọn progression biến C–G–Am–F thành một phiên bản có borrowed iv.

**Review contract**
- `L06-F01` [recall/exact] `scale.parallel_minor` — Parallel minor của C major
- `L06-F02` [context/exact] `harmony.modal_interchange.identify` — iv borrowed in C major
- `L06-F03` [context/exact] `harmony.modal_interchange.identify` — ♭VI borrowed triad in C major
- `L06-F04` [context/exact] `harmony.modal_interchange.identify` — ♭VII borrowed triad in C major
- `L06-F05` [context/rubric] `harmony.modal_interchange.identify` — C–F–Fm–C: Fm = ?
- `L06-F06` [recall/rubric] `scale.parallel_minor` — Modal mixture thường vay mượn giữa loại key nào?
- `L06-F07` [context/rubric] `harmony.modal_interchange.identify` — Borrowed chord có bắt buộc modulation?
- `L06-F08` [recall/rubric] `harmony.modal_interchange.identify` — Modal mixture chủ yếu thay đổi gì ở chord trong khung OMT?

## L07 — Jazz Tensions, Modes và Chord-Scale Context

**Objectives**
- Phân biệt chord tones với 9/11/13 trong extended-chord vocabulary.
- Nhận diện ba chord-scale quan hệ cơ bản của major ii–V–I.
- Hiểu chord-scale là công cụ theo context/function chứ không phải bảng đáp án tuyệt đối.

**Target skills**
`tension.naming`, `mode.basic`, `chord_scale.basic`, `chord_scale.context`

**Sources**
- `OMT_V2` — Jazz → Chord-Scale Theory
- `OMT_V2` — Jazz → Chord Symbols
- `TEREFENKO_WB` — Part I, Chs.7–8 Modes and Chord-Scale Theory, PDF pp. 47–53
- `KHAIHOAN_JAZZ` — Introduction + Ch.1, printed pp. 12–18 and 45–70

**Quiz contract**
- `L07-Q01` [mcq/exact] `tension.naming` — Các extension/tension number cơ bản phía trên seventh chord là bộ nào?
- `L07-Q02` [build/music_engine] `tension.naming` — Dựng Cmaj7 chord tones trước khi thêm tension.
- `L07-Q03` [mcq/exact] `chord_scale.basic` — Trong basic ii–V–I chord-scale model ở C, Dm7 thường liên hệ với mode nào?
- `L07-Q04` [mcq/exact] `chord_scale.basic` — Trong cùng model, G7 thường liên hệ với mode nào?
- `L07-Q05` [mcq/exact] `chord_scale.basic` — Trong cùng model, Cmaj7 thường liên hệ với mode nào?
- `L07-Q06` [context/rubric] `chord_scale.context` — Vì sao không nên coi chord-scale table là một đáp án duy nhất cho mọi chord symbol?

**Review contract**
- `L07-F01` [recall/exact] `tension.naming` — Tension/extension numbers
- `L07-F02` [build/music_engine] `tension.naming` — Chord tones của Cmaj7
- `L07-F03` [context/exact] `chord_scale.basic` — Dm7 in C major: basic chord-scale
- `L07-F04` [context/exact] `chord_scale.basic` — G7 in C major: basic chord-scale
- `L07-F05` [context/exact] `chord_scale.basic` — Cmaj7 in C major: basic chord-scale
- `L07-F06` [recall/rubric] `chord_scale.context` — Chord-scale choice nên bắt đầu từ điều gì?
- `L07-F07` [recall/rubric] `tension.naming` — Chord tone vs tension
- `L07-F08` [context/rubric] `chord_scale.context` — Chord-scale theory có thay thế ear/voice leading không?

## L08 — Jazz Piano Voicing: shell voicing và guide-tone connection

**Objectives**
- Phân biệt full chord inventory với một voicing hợp lệ.
- Dựng shell/3-note voicing root–3rd–7th trong phạm vi lesson.
- Nối voicings bằng common tones và chuyển động gần.

**Target skills**
`voicing.shell`, `voicing.guide_tones`, `voicing.voice_leading`

**Sources**
- `OMT_V2` — Jazz → Jazz Voicings
- `TEREFENKO_WB` — Part II, Chs.12–14 Keyboard Textures / Idiomatic Jazz Progressions / Voicings, PDF pp. 78–103
- `KHAIHOAN_JAZZ` — Ch.11, printed pp. 279–307

**Quiz contract**
- `L08-Q01` [mcq/exact] `voicing.shell` — Trong basic shell/3-note frame của lesson, ba thành phần ưu tiên là gì?
- `L08-Q02` [mcq/exact] `voicing.shell` — Theo OMT Jazz Voicings, chord tone nào thường có thể lược bỏ an toàn nhất trong nhiều voicing?
- `L08-Q03` [build/rubric] `voicing.shell` — Nêu shell root–3rd–7th cho G7 bằng ba tên nốt.
- `L08-Q04` [mcq/exact] `voicing.voice_leading` — Smooth/lazy voice leading ưu tiên điều gì?
- `L08-Q05` [context/exact] `voicing.voice_leading` — Trong G7 → Cmaj7, basic guide-tone connection nào phù hợp với lesson?
- `L08-Q06` [applied/rubric] `voicing.shell` — Vì sao bài 'dựng đầy đủ G7' và bài 'tạo shell voicing G7' không dùng cùng rubric?

**Review contract**
- `L08-F01` [recall/exact] `voicing.shell` — Basic shell frame
- `L08-F02` [build/rubric] `voicing.shell` — G7 shell root–3–7
- `L08-F03` [build/rubric] `voicing.shell` — Dm7 shell root–3–7
- `L08-F04` [build/rubric] `voicing.shell` — Cmaj7 shell root–3–7
- `L08-F05` [recall/rubric] `voicing.voice_leading` — Common tone có ích gì trong voice leading?
- `L08-F06` [recall/rubric] `voicing.voice_leading` — OMT: smooth/lazy voice leading
- `L08-F07` [context/rubric] `voicing.voice_leading` — G7 → Cmaj7: guide-tone pair
- `L08-F08` [context/rubric] `voicing.shell` — Chord formula vs voicing

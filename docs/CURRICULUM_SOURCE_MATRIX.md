# Curriculum Source Matrix — Phase 0.4B

Các lesson/quiz/flashcard trong bank này là **biên soạn mới**. Nguồn được dùng để xác minh khái niệm, phạm vi và dạng hoạt động; không sao chép nguyên bài tập/score/answer key độc quyền.

## Source registry

| ID | Nguồn | Vai trò | Access/licensing note |
|---|---|---|---|
| `OMT_V2` | Open Music Theory — Version 2 — Open Music Theory contributors | Primary source for fundamentals, tonicization, modal mixture, jazz basics, and popular-music concepts. | official_web_verified; CC BY-SA 4.0 except where a chapter/media item states otherwise |
| `FANK_WIH` | Working in Harmony — Gabriel Fankhauser | Academic cross-check for fundamentals, diatonic harmony, chromatic harmony, and voice leading. | official_site_verified; current PDFs are large and exact current PDF page locators are not locked in this phase; Reference use. Do not reproduce current PDF text/notation unless the current PDF license is checked. |
| `TEREFENKO_WB` | Workbook to Accompany Jazz Theory: From Basic to Advanced Study — Dariusz Terefenko | Primary pedagogical reference for keyboard realization, ear training, ii–V–I, chord-scale work, voicings, and jazz practice sequencing. | user_supplied_pdf_verified; Copyright Routledge/Taylor & Francis; reference only. Do not reproduce exercises, scores, or answer keys. |
| `KHAIHOAN_JAZZ` | Hòa âm Jazz cơ bản đến nâng cao — Trần Khải Hoàn | Vietnamese reference for jazz/modern harmonic function, tensions, secondary dominants, modal interchange, and voicing. | user_supplied_pdf_verified; Reference only unless the rights holder grants broader reuse. |

## Lesson matrix

| Lesson | Track | Target skills | Source locators | Runtime status |
|---|---|---|---|---|
| L01 — Nốt, quãng và cấu trúc hợp âm | Foundation | `pitch.spelling`<br>`interval.naming`<br>`chord.triad_formula`<br>`chord.triad_build` | `OMT_V2` — Fundamentals → Intervals<br>`OMT_V2` — Fundamentals → Triads<br>`FANK_WIH` — Unit 1: Music Fundamentals — scales, intervals, triads<br>`TEREFENKO_WB` — Part I, Ch.1 Music Fundamentals, PDF pp. 13–22 | reviewed |
| L02 — Âm giai trưởng và hợp âm bảy điệu tính | Foundation | `scale.major`<br>`chord.seventh_quality`<br>`chord.seventh_build`<br>`roman.major_seventh` | `OMT_V2` — Fundamentals → Seventh Chords<br>`OMT_V2` — Fundamentals → Roman Numerals<br>`FANK_WIH` — Unit 1: Music Fundamentals — scales, intervals, triads<br>`FANK_WIH` — Unit 2: Diatonic Harmony — Roman-numeral analysis, dominant seventh, diatonic seventh chords, smooth voice leading<br>`TEREFENKO_WB` — Part I, Chs.4–5 Four-Part/Five-Part Chords, PDF pp. 29–43 | reviewed |
| L03 — Chức năng hòa âm: Tonic – Predominant/Subdominant – Dominant | Harmony Core | `function.tonic`<br>`function.predominant`<br>`function.dominant`<br>`function.progression` | `OMT_V2` — Introduction to Harmony, Cadences, and Phrase Endings<br>`FANK_WIH` — Unit 2: Diatonic Harmony — Roman-numeral analysis, dominant seventh, diatonic seventh chords, smooth voice leading<br>`TEREFENKO_WB` — Part I, Ch.3 Harmonic Function, PDF pp. 25–28<br>`KHAIHOAN_JAZZ` — Ch.1, printed pp. 21–37 | reviewed |
| L04 — ii–V–I và guide-tone voice leading trên piano | Harmony Core | `progression.ii_v_i`<br>`voicing.guide_tones`<br>`voicing.voice_leading` | `OMT_V2` — Jazz → ii–V–I<br>`OMT_V2` — Jazz → Jazz Voicings<br>`TEREFENKO_WB` — Part I, Ch.6 The II–V–I Progression, PDF pp. 44–46<br>`KHAIHOAN_JAZZ` — Ch.1, printed pp. 21–37<br>`KHAIHOAN_JAZZ` — Ch.11, printed pp. 279–307 | reviewed |
| L05 — Secondary Dominants | Functional / Contemporary | `harmony.secondary_dominant.identify`<br>`harmony.secondary_dominant.build`<br>`harmony.secondary_dominant.apply` | `OMT_V2` — Diatonic Harmony, Tonicization, and Modulation → Tonicization<br>`FANK_WIH` — Unit 3: Chromatic Harmony — Secondary Dominants; Mode Mixture<br>`KHAIHOAN_JAZZ` — Ch.2, printed pp. 71–102<br>`TEREFENKO_WB` — Part II, Ch.13 Idiomatic Jazz Progressions, PDF pp. 82–93 | source_audited |
| L06 — Modal Interchange trong Pop/Contemporary | Functional / Contemporary | `scale.parallel_minor`<br>`harmony.modal_interchange.identify`<br>`harmony.modal_interchange.apply` | `OMT_V2` — Chromaticism → Modal Mixture<br>`FANK_WIH` — Unit 3: Chromatic Harmony — Secondary Dominants; Mode Mixture<br>`KHAIHOAN_JAZZ` — Ch.5, printed pp. 170–188 | source_audited |
| L07 — Jazz Tensions, Modes và Chord-Scale Context | Jazz | `tension.naming`<br>`mode.basic`<br>`chord_scale.basic`<br>`chord_scale.context` | `OMT_V2` — Jazz → Chord-Scale Theory<br>`OMT_V2` — Jazz → Chord Symbols<br>`TEREFENKO_WB` — Part I, Chs.7–8 Modes and Chord-Scale Theory, PDF pp. 47–53<br>`KHAIHOAN_JAZZ` — Introduction + Ch.1, printed pp. 12–18 and 45–70 | source_audited |
| L08 — Jazz Piano Voicing: shell voicing và guide-tone connection | Jazz | `voicing.shell`<br>`voicing.guide_tones`<br>`voicing.voice_leading` | `OMT_V2` — Jazz → Jazz Voicings<br>`TEREFENKO_WB` — Part II, Chs.12–14 Keyboard Textures / Idiomatic Jazz Progressions / Voicings, PDF pp. 78–103<br>`KHAIHOAN_JAZZ` — Ch.11, printed pp. 279–307 | source_audited |

## Audit rules

1. Claim/skill trước, exercise sau: mỗi exercise/review item mang `provenance` trong `curriculum_specs.py`.
2. Working in Harmony hiện được dùng như nguồn cross-check theo **unit/topic**; exact page locator của bản hiện tại chưa khóa vì PDF chính thức rất lớn và môi trường này không parse trực tiếp toàn bộ file.
3. Terefenko Workbook là nguồn pedagogical/reference only; không copy nguyên exercise, score, answer key hoặc copyrighted tune.
4. Open Music Theory được dùng theo chapter/section; nội dung có license CC BY-SA 4.0 trừ nơi được ghi khác.
5. Trần Khải Hoàn là tài liệu người dùng cung cấp; dùng để đối chiếu thuật ngữ và logic jazz/modern harmony tiếng Việt, không tái bản nguyên văn.
6. Lesson 1–4 đã migrate runtime DB; Lesson 5–8 mới ở mức source-audited specification.
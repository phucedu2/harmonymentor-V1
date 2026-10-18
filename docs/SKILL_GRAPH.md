# Skill Graph — MVP 8 lessons

Graph dùng prerequisite edges để adaptive layer sau này biết một kỹ năng cần bằng chứng nền nào trước. Phase 0.4B mới chuẩn hóa graph, chưa tính mastery aggregation.

## Skills by lesson

### L01 — Nốt, quãng và cấu trúc hợp âm
- `pitch.spelling` — Tên nốt và enharmonic spelling (foundation)
- `interval.naming` — Nhận diện/gọi tên quãng (foundation)
- `chord.triad_formula` — Công thức hợp âm ba (foundation)
- `chord.triad_build` — Dựng hợp âm ba (foundation)

### L02 — Âm giai trưởng và hợp âm bảy điệu tính
- `scale.major` — Dựng âm giai trưởng (foundation)
- `chord.seventh_quality` — Chất lượng hợp âm bảy (foundation)
- `chord.seventh_build` — Dựng hợp âm bảy (foundation)
- `roman.major_seventh` — Số La Mã cho hợp âm bảy trong giọng trưởng (foundation)

### L03 — Chức năng hòa âm: Tonic – Predominant/Subdominant – Dominant
- `function.tonic` — Chức năng tonic (harmony)
- `function.predominant` — Chức năng predominant/subdominant (harmony)
- `function.dominant` — Chức năng dominant (harmony)
- `function.progression` — Luồng chức năng T–PD–D–T (harmony)

### L04 — ii–V–I và guide-tone voice leading trên piano
- `progression.ii_v_i` — Nhận diện và dựng ii–V–I (jazz_core)
- `voicing.guide_tones` — Guide tones của hợp âm bảy (piano)
- `voicing.voice_leading` — Voice leading giữa voicings (piano)

### L05 — Secondary Dominants
- `harmony.secondary_dominant.identify` — Nhận diện secondary dominant (chromatic_harmony)
- `harmony.secondary_dominant.build` — Dựng secondary dominant (chromatic_harmony)
- `harmony.secondary_dominant.apply` — Ứng dụng secondary dominant (chromatic_harmony)

### L06 — Modal Interchange trong Pop/Contemporary
- `scale.parallel_minor` — Quan hệ major–parallel minor (chromatic_harmony)
- `harmony.modal_interchange.identify` — Nhận diện modal interchange (chromatic_harmony)
- `harmony.modal_interchange.apply` — Ứng dụng modal interchange (chromatic_harmony)

### L07 — Jazz Tensions, Modes và Chord-Scale Context
- `tension.naming` — Tên và bậc tension 9/11/13 (jazz)
- `mode.basic` — Các mode cơ bản dùng trong chord-scale (jazz)
- `chord_scale.basic` — Quan hệ chord–scale cơ bản (jazz)
- `chord_scale.context` — Chọn chord-scale theo chức năng/ngữ cảnh (jazz)

### L08 — Jazz Piano Voicing: shell voicing và guide-tone connection
- `voicing.shell` — Shell / 3-note voicing cơ bản (piano)
- `voicing.guide_tones` — Guide tones của hợp âm bảy (piano)
- `voicing.voice_leading` — Voice leading giữa voicings (piano)

## Prerequisite edges

- `pitch.spelling` → `interval.naming`
- `interval.naming` → `chord.triad_formula`
- `chord.triad_formula` → `chord.triad_build`
- `pitch.spelling` → `scale.major`
- `chord.triad_build` → `chord.seventh_quality`
- `chord.seventh_quality` → `chord.seventh_build`
- `scale.major` → `roman.major_seventh`
- `chord.seventh_quality` → `roman.major_seventh`
- `roman.major_seventh` → `function.tonic`
- `roman.major_seventh` → `function.predominant`
- `roman.major_seventh` → `function.dominant`
- `function.tonic` → `function.progression`
- `function.predominant` → `function.progression`
- `function.dominant` → `function.progression`
- `function.progression` → `progression.ii_v_i`
- `chord.seventh_build` → `progression.ii_v_i`
- `chord.seventh_quality` → `voicing.guide_tones`
- `progression.ii_v_i` → `voicing.guide_tones`
- `voicing.guide_tones` → `voicing.voice_leading`
- `voicing.guide_tones` → `voicing.shell`
- `function.dominant` → `harmony.secondary_dominant.identify`
- `roman.major_seventh` → `harmony.secondary_dominant.identify`
- `harmony.secondary_dominant.identify` → `harmony.secondary_dominant.build`
- `chord.seventh_build` → `harmony.secondary_dominant.build`
- `harmony.secondary_dominant.build` → `harmony.secondary_dominant.apply`
- `function.progression` → `harmony.secondary_dominant.apply`
- `scale.major` → `scale.parallel_minor`
- `scale.parallel_minor` → `harmony.modal_interchange.identify`
- `function.progression` → `harmony.modal_interchange.identify`
- `harmony.modal_interchange.identify` → `harmony.modal_interchange.apply`
- `chord.seventh_quality` → `tension.naming`
- `scale.major` → `mode.basic`
- `mode.basic` → `chord_scale.basic`
- `tension.naming` → `chord_scale.basic`
- `chord_scale.basic` → `chord_scale.context`
- `function.progression` → `chord_scale.context`
# HarmonyMentor Phase 2.2 — Lesson 1 zero-beginner pedagogy rewrite

## Trigger

Browser testing identified that Lesson 1 remained too dense for a learner starting from zero. The problem was not only terminology: the lesson lacked an early piano visualization, mixed symbol definitions with concrete interval examples, introduced unused interval concepts, used scale-degree-like shorthand before scale teaching, compared triads on different roots, and gave free-response inputs no format guidance.

## Implemented changes

1. Rewrote L01 objectives in plain Vietnamese without prerequisite jargon.
2. Moved Virtual Piano immediately after the note/semitone explanation.
3. Explicitly teaches the E-F and B-C half-step exception and whole-tone relationship.
4. Introduces same-key/different-name note naming in plain language before `enharmonic` / `spelling` terminology.
5. Adds the letter-family rule: a third above C must use an E-family spelling.
6. Separates interval-quality letters from concrete interval cards.
7. Removes `A4` and tritone from L01; adds `P5` and `d5`.
8. Rebuilds triad teaching around letter frame + root-to-note interval formula.
9. Adds diminished shorthand `1-b3-b5`.
10. Replaces B diminished comparison with parallel C diminished.
11. Reworks VexFlow examples into per-example cards for label alignment.
12. Adds shared free-response input hints/placeholders for checkpoints and quizzes.
13. Formula normalization accepts Unicode flat `♭` and ASCII `b`.
14. Publishes L01 assessment items as version `v3` to preserve prior attempt traceability.

## Runtime Lesson 1 structure

1. Tên nốt và bàn phím piano
2. Cùng một phím nhưng có thể có hai tên
3. Năm chữ cái dùng để mô tả chất lượng quãng
4. Bốn quãng cần dùng trong bài này
5. Hợp âm ba nốt: dựng bằng hai bước
6. Ba chất lượng hợp âm ba nốt
7. So sánh ba chất lượng trên cùng nốt gốc C
8. Nghe ba hợp âm với cùng nốt gốc
9. Tóm tắt trước khi làm quiz

Interactive piano, notation examples, and checkpoints are inserted between these sections without breaking the numbering.

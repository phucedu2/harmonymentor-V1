# Phase 2 Beginner Content Audit — updated in Phase 2.3

## Finding

Phase 1 proved the learning-platform architecture. Browser testing then exposed two pedagogical defects in Lesson 1: the content still relied too heavily on C-only examples, and interval-quality symbols were defined circularly rather than through a clear size/family model. Phase 2.3 treats both as content defects, not UI polish.

## Current zero-beginner sequence

```text
piano layout
→ semitone counting (start key = 0)
→ interval-number counting (start note = 1)
→ enharmonic/spelling rule
→ interval-quality families + visual spectrum
→ dynamic M3/m3/P5/d5 explorer across 12 roots
→ triad construction in two steps
→ dynamic Major/Minor/Diminished/Augmented explorer
→ notation + piano + audio on the selected root
→ 24-key tonic-triad overview in three tiers
→ checkpoint / quiz / spaced review
```

## Interval quality correction

HarmonyMentor now teaches two families:

- interval numbers 1/4/5/8 use `P` as the standard quality; `d ← P → A`;
- interval numbers 2/3/6/7 use adjacent `m ↔ M` standard sizes; `d ← m ↔ M → A`.

`Major` / `Minor` are defined first as interval sizes. Any brighter/darker listening description is explicitly presented only as a tendency, especially for thirds, not as the formal definition.

Concrete spelling examples make A/d symmetric while keeping the same letter number:

- `C→G = P5`; `C→G# = A5` while remaining a fifth;
- `C→G = P5`; `C→Gb = d5` while remaining a fifth.

Lesson 1 no longer introduces A4/tritone. A5 appears only to explain the optional augmented-triad extension.

## Multi-key correction

The learner begins with C but is no longer confined to C. One shared root state drives:

- interval target spelling;
- Virtual Piano highlighting;
- VexFlow notation;
- Tone.js audio;
- triad spelling and ChordInspector.

The selector covers 12 pitch positions and exposes enharmonic spelling choices for black-key roots. The lesson also contains a three-tier overview of the tonic triads representing 12 major and 12 minor keys.

The term “key” is deliberately scoped: Lesson 1 previews only the tonic triad associated with each key. Full scale/key theory remains Lesson 2.

## Assessment correction

Fixed checkpoints no longer reuse the C examples used in exposition:

- interval checkpoint: F→A;
- chord checkpoint: G major;
- later quiz items include D minor and B diminished.

Free-response placeholders show only format, never the current answer. Minor-triad formula guidance now uses `1-3-5` as the format example rather than leaking `1-b3-5`.

Optional random practice covers 12 interval roots or all 24 major/minor tonic triads. It is formative in this MVP and does not create mastery evidence.

## QA guardrails

Regression tests now verify:

- section numbering 1–10;
- start-note=1 vs start-key=0 counting rules;
- two interval-quality families and both visual spectrum rows;
- concrete A5/d5 spelling examples;
- shared dynamic-root block contracts;
- 12 selector positions and all 24 major/minor tonic-triad cards;
- non-C checkpoints and diversified review items;
- no answer-revealing minor-formula placeholder;
- dynamic ChordInspector refresh when the selected symbol changes;
- frontend spelling/notation paths for single and double accidentals.

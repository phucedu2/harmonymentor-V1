# HarmonyMentor AI - Phase 2 Interactive Music Layer (`v0.5.3-dev`)

HarmonyMentor is evolving from a deterministic music-theory prototype into a source-grounded learning platform. Phase 2 adds the first interactive music layer and also fixes a pedagogical problem found during Phase 1 testing: Lessons 1-4 were structurally complete but too compressed for a true beginner.

## What changed in Phase 2

### 1. Beginner content hardening

Lessons 1-4 teach prerequisite vocabulary before assessing it. Phase 2.3 hardens Lesson 1 after browser testing showed that the previous version still over-relied on C-only examples and did not make interval-quality relationships explicit enough.

- Lesson 1 now begins with the physical piano layout, explicitly teaches that **E-F and B-C have no black key between them**, and defines semitone / whole tone before interval arithmetic.
- The spelling section first explains the everyday idea (one piano key can have two names) and only then introduces the terms `enharmonic` and `spelling`.
- Interval quality is taught as two families: `P` for 1/4/5/8 and the `m↔M` pair for 2/3/6/7, with an explicit `d ← standard → A` visual spectrum. Lesson 1 still practices only `M3`, `m3`, `P5`, `d5`, while `A5` appears only to explain augmented triads.
- Triads are built in two steps: choose the correct letter frame (C-E-G, D-F-A...) and then apply interval formulas. A shared 12-root selector updates interval examples, triad spelling, piano highlighting, notation, and audio; the lesson adds a tiered overview of 12 major + 12 minor tonic triads.
- The parallel comparison now keeps root C throughout: C major, C minor, C diminished.
- Free-response placeholders show format only and never reveal the current answer. Checkpoints use non-C examples and provide optional randomized practice across 12 roots / 24 major-minor tonic triads.
- Lesson 2 defines whole step vs half step, major-scale pattern, seventh-chord symbols, Roman numerals, and key/tonic context.
- Lesson 3 separates chord structure from harmonic function and defines tonic, predominant/subdominant, dominant, and progression.
- Lesson 4 defines ii-V-I, guide tones, voice leading, common tone, and voicing before keyboard work.

### 2. Virtual Piano V2

`frontend/src/components/music/VirtualPiano.tsx`

- click/tap playback;
- octave-aware scientific pitch names;
- optional note selection;
- target/error highlighting;
- black-key enharmonic labels such as `C#/Db`;
- explicit separation between sounding pitch and spelling-sensitive grading.

The legacy Practice page now reuses the same piano component through `frontend/src/Piano.tsx`.

### 3. Tone.js AudioEngine

`frontend/src/audio/AudioEngine.ts`

Current MVP capabilities:

- play a single note;
- play a chord;
- schedule chord progressions;
- BPM control;
- metronome;
- shared transport cleanup.

The current sound source is a Tone.js `PolySynth` fallback so the interaction works without shipping unverified audio assets. A self-hosted licensed piano sample set can replace this through a later sampler increment without changing lesson contracts.

### 4. VexFlow notation blocks

`frontend/src/components/music/NotationStaff.tsx`

Phase 2 supports simple SVG notation examples for:

- intervals;
- triads/seventh-chord examples;
- guide-tone examples.

The renderer is intentionally narrow. It is not a score editor.

### 5. Reusable music lesson blocks

`LessonRunner` now understands:

```text
THEORY
CALLOUT
GLOSSARY
NOTATION
PROGRESSION
PIANO
AUDIO
CHECKPOINT
SUMMARY
```

This keeps interactive music features data-driven instead of hard-coding a unique React page for every lesson.

### 6. ChordInspector audio

ChordInspector still obtains deterministic chord facts from the backend Music Theory Engine. Phase 2 adds audio preview while retaining:

- chord tones;
- formula;
- slash-bass information;
- Roman numeral/function when a key is provided.

## Runtime curriculum status

```text
L01 Foundation                    reviewed / runtime / Phase 2 enriched
L02 Major Scale & Seventh Chords reviewed / runtime / Phase 2 enriched
L03 Harmonic Function            reviewed / runtime / Phase 2 enriched
L04 ii-V-I & Voice Leading       reviewed / runtime / Phase 2 enriched
L05 Secondary Dominants          source_audited spec only
L06 Modal Interchange            source_audited spec only
L07 Tensions / Chord-Scale       source_audited spec only
L08 Jazz Piano Voicing           source_audited spec only
```

Current block counts for the runtime lessons:

```text
L01 12 blocks
L02 10 blocks
L03  9 blocks
L04 11 blocks
```

The assessment bank remains 48 quiz items and 64 review items across the eight audited specifications. Only L01-L04 are runtime-migrated.

## Curriculum sources

Canonical source policy remains in `backend/app/content/source_registry.py`.

- Open Music Theory v2: foundation, functional basics, jazz basics, and Pop concepts.
- Working in Harmony: academic cross-check for fundamentals, diatonic/chromatic harmony, and voice leading.
- Terefenko Jazz Theory Workbook: keyboard, ear-training, ii-V-I, chord-scale, voicing, and practice design.
- Tran Khai Hoan: Vietnamese jazz-harmony reference for function, tensions, secondary dominants, modal interchange, and voicing.

The canonical lesson data is `backend/app/content/curriculum_specs.py`. `content/curriculum/lesson_specs.json` is a generated review snapshot.

## Dependencies added in Phase 2

Frontend `package.json` now includes:

```text
tone 15.1.22
vexflow 5.0.0
```

The stale Phase 1 lockfile is intentionally not shipped because this execution environment could not complete a fresh npm registry install. On the development machine, run `npm install` once and commit the newly generated `package-lock.json` after a successful build.

## Run locally

Backend:

```bash
cd backend
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run build
npm run dev
```

The browser must receive a user gesture before Web Audio can start; clicking a piano/audio control provides that gesture.

## Verification status

Backend test suite in the packaging environment:

```text
120 passed, 1 skipped
```

The skip is the optional `music21` cross-check when that dependency is unavailable.

Frontend source syntax transpilation:

```text
18 TypeScript/TSX files
0 syntax diagnostics
```

A complete `npm run build` is NOT claimed in the packaging environment because the npm registry install timed out and Tone/VexFlow were not locally installed there. This is why the stale lockfile was removed. Run the local install/build commands above before demo freeze.

See:

- `docs/BEGINNER_CONTENT_AUDIT_PHASE_2.md`
- `docs/PHASE_2_IMPLEMENTATION.md`
- `docs/VERIFICATION_PHASE_2.txt`
- `docs/CURRICULUM_SOURCE_MATRIX.md`
- `docs/LESSON_SPECIFICATIONS.md`

## Next implementation gate

Do not move directly to the AI assistant until Phase 2 receives a local browser smoke test. The next gate is:

1. `npm install && npm run build` on the project machine;
2. visually verify VexFlow notation and Virtual Piano layout;
3. verify browser audio + metronome interaction;
4. only then proceed to Harmony Lab and the composition/backing-track layer.


## Phase 2.1 hotfix

Fixed a VexFlow 5 `IncompleteVoice` crash in lesson notation blocks by using `Formatter.FormatAndDraw`, added local notation fallback handling, and wrapped the lesson runtime in a React error boundary so a visualization failure cannot blank the entire app.

## Phase 2.3 Multi-key Lesson 1 hardening

Lesson 1 now uses one shared root selection across its interval, triad, notation, piano, and audio explorers. The selector exposes all 12 pitch positions and an explicit enharmonic spelling choice for black-key roots. The new 24-key overview is deliberately presented as **tonic triads representing 12 major + 12 minor keys**; the full concept of key/scale remains Lesson 2 material. Random practice is formative only and does not update mastery in this MVP.

The interval-quality explanation also avoids treating “bright/dark” as the definition of Major/Minor. `Major` and `Minor` are taught first as interval sizes, with any listening-color description framed only as a tendency.

## Phase 2.2 Lesson 1 pedagogy rewrite

The Lesson 1 content contract was rewritten from a zero-beginner perspective after usability testing. The rewrite keeps the existing 8-lesson MVP architecture but turns L01 into a scaffolded sequence with continuous section numbering, early piano visualization, explicit spelling rules, interval formulas required by triad construction, parallel-root triad comparison, and format-aware answer inputs. L01 exercise versions are published as `v4` so earlier attempts remain traceable.

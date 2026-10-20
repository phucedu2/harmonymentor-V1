# Phase 2 - Interactive Music Layer

Version: `v0.5.0-dev`

## Goal

Add a reusable interactive music layer to the Phase 1 learning vertical slice while fixing the beginner-exposition gap discovered during hands-on testing.

## Frontend modules added

```text
frontend/src/audio/AudioEngine.ts
frontend/src/audio/musicUtils.ts
frontend/src/components/music/VirtualPiano.tsx
frontend/src/components/music/AudioControls.tsx
frontend/src/components/music/NotationStaff.tsx
frontend/src/components/music/GlossaryBlock.tsx
```

Modified integration points:

```text
frontend/src/Piano.tsx
frontend/src/components/learning/LessonRunner.tsx
frontend/src/components/learning/ChordInspector.tsx
frontend/src/styles.css
frontend/package.json
```

## Audio architecture

`AudioEngine` owns one Tone.js transport path for progression scheduling and metronome timing. UI components do not create independent schedulers.

The current instrument is a `PolySynth` fallback. This is deliberate: no third-party piano sample files are bundled without an explicit license decision. The API boundary is small enough to replace the synth with `Tone.Sampler` later.

## Piano architecture

Virtual Piano V2 works with scientific pitch names and preserves octave identity. Pitch-class highlighting is separate from selected sounding notes. This matters because future voicing/voice-leading exercises need register, while spelling exercises still require typed note names.

Black keys display both common enharmonic labels. A press selects a sounding pitch; it does not automatically prove spelling mastery.

## Notation architecture

VexFlow renders narrow educational examples to SVG. Phase 2 deliberately does not implement score editing, notation input, or full grand-staff authoring.

## Lesson block integration

The runtime lesson contract now supports music-aware blocks without lesson-specific React pages:

```text
glossary
notation
progression
piano
audio
```

Existing theory, callout, checkpoint, summary, and interactive blocks remain supported.

## Beginner exposition changes

The runtime block counts changed because definitions and examples were inserted before assessment:

```text
L01 12 blocks
L02 10 blocks
L03  9 blocks
L04 11 blocks
```

No quiz/review counts were expanded in this phase. The source-audited exercise bank remains unchanged in size.

## ChordInspector

Chord facts continue to come from `/api/v1/music/chords/inspect`. Phase 2 only adds playback and more beginner-friendly labels. LLM output is not used for chord tones, formula, Roman numeral, or harmonic function.

## Out of scope in this phase

- microphone pitch recognition;
- Web MIDI requirement;
- licensed realistic piano sample bundle;
- ear-training grading from recorded audio;
- full grand-staff editor;
- backing-track drums/bass;
- Harmony Assistant / LLM composition features.

## Exit criteria

Phase 2 is ready for local browser acceptance when:

- backend tests pass;
- frontend source syntax is clean;
- local `npm install && npm run build` passes;
- learner can open L01-L04 and see glossary/notation/piano/audio blocks;
- piano clicks produce sound after user gesture;
- progression playback and metronome work;
- ChordInspector can play inspected chords;
- notation examples render without overflow or runtime exceptions.

## Minimal keyboard evidence

Lesson 4 now includes one persisted keyboard-input path. The learner selects the sounding pitches of G7 on Virtual Piano; the frontend converts the selected scientific pitches to pitch classes and submits them to the existing audited `L04-Q03` exercise version. The backend Music Engine still decides correctness.

This evidence mode is intentionally enabled only where pitch-class input is unambiguous. It must not be used to claim spelling mastery for enharmonic cases such as G# versus Ab.

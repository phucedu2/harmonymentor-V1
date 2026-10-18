# Phase 0.4B — Curriculum Source Audit & Content Specification

Version: `v0.3.1-dev`

## Goal

Phase 0.4B closes the gap between a technically working learning contract and a curriculum that can be defended academically. It standardizes the source registry, skill graph and lesson specifications, rewrites the draft assessment bank against verified sources, then migrates Lessons 2–4 into runtime persistence.

## 1. Canonical curriculum source of truth

The old TypeScript content bank is no longer authoritative. Canonical files are:

```text
backend/app/content/source_registry.py
backend/app/content/skill_graph.py
backend/app/content/curriculum_specs.py
backend/app/content/seed_data.py
```

Generated review snapshots are under:

```text
content/curriculum/source_registry.json
content/curriculum/skill_graph.json
content/curriculum/lesson_specs.json
```

## 2. Source strategy

Four source IDs are registered:

- `OMT_V2`: primary open source for fundamentals, tonicization/modal mixture, jazz basics and Pop concepts.
- `FANK_WIH`: academic cross-check for fundamentals, diatonic/chromatic harmony and voice leading. Exact current PDF page locators are intentionally not claimed in this phase.
- `TEREFENKO_WB`: pedagogical reference for keyboard realization, ear training, ii–V–I, chord-scale, voicing and practice sequencing.
- `KHAIHOAN_JAZZ`: Vietnamese reference for harmonic function, tensions, secondary dominants, modal interchange and jazz voicing.

No proprietary workbook exercise, score, answer key, or copyrighted tune has been copied into the generated quiz bank. The source material is used to verify concepts, scope, sequencing and activity types; HarmonyMentor prompts are newly written.

## 3. Skill Graph

The MVP graph now contains:

```text
26 skills
36 prerequisite edges
8 lesson → skill mappings
```

The graph is tested as a DAG. Important chains include:

```text
pitch.spelling
  → interval.naming
  → chord.triad_formula
  → chord.triad_build
  → chord.seventh_quality
  → chord.seventh_build
```

and:

```text
roman.major_seventh
  → function.tonic / function.predominant / function.dominant
  → function.progression
  → progression.ii_v_i
  → voicing.guide_tones
  → voicing.voice_leading / voicing.shell
```

Chromatic and jazz branches remain connected to prerequisite evidence instead of becoming disconnected course labels.

## 4. Lesson specifications

All eight lesson specifications now declare:

- learning objectives;
- target skills;
- source locators;
- block outline;
- exactly six quiz items;
- exactly eight review items;
- grading strategy;
- item-level provenance.

Current runtime status:

```text
L01 reviewed + migrated
L02 reviewed + migrated
L03 reviewed + migrated
L04 reviewed + migrated
L05 source_audited spec only
L06 source_audited spec only
L07 source_audited spec only
L08 source_audited spec only
```

## 5. Assessment bank revision

The previous draft bank was replaced by a source-audited bank with exact totals:

```text
48 quiz items
64 review/flashcard items
```

Design rules:

1. objective music facts use deterministic `exact` or `music_engine` grading;
2. context/explanation questions use a deliberately narrow rubric;
3. full chord inventory and jazz voicing are different assessment targets;
4. harmonic function questions state a key/progression context where needed;
5. chord-scale questions explicitly avoid presenting the table as a universal single-answer system;
6. modal-interchange questions distinguish borrowing from full modulation;
7. review cards use recall/build/context tasks, not only passive flip cards.

## 6. Lessons 2–4 runtime migration

`seed_data.py` now fully seeds blocks, exercises, versioned answer keys and review items for L01–L04.

Each runtime lesson has:

```text
5 lesson blocks
6 quiz/exercises
8 review items
```

L02 adds live Music Engine grading for major-scale construction and Roman numerals. L03 exercises harmonic function in context. L04 exercises ii–V–I, guide tones and basic voice-leading reasoning.

## 7. Item-level provenance persistence

Phase 0.4B adds a second Alembic migration:

```text
c84d7c4b190a_add_content_provenance.py
```

New nullable JSON fields:

```text
exercise_versions.provenance
review_items.provenance
```

Nullable is intentional for legacy content: an old version without source audit must remain distinguishable from an audited version. L01 uses audited `v2`; L02–L04 use audited `v1`.

## 8. Compatibility note for old local SQLite databases

Early v0.3 local development could create tables with SQLAlchemy `create_all` without an Alembic version stamp. For disposable local data, delete `backend/harmonymentor_dev.db` and recreate it.

If the old local schema is known to match migration `097c446166e1`, it can be adopted with:

```bash
alembic -c alembic.ini stamp 097c446166e1
alembic -c alembic.ini upgrade head
```

Never stamp an unknown production database merely to bypass migration errors.

## 9. Verification

At close of Phase 0.4B:

```text
pytest: 109 passed, 1 skipped
```

The skipped test is the optional `music21` cross-check when that dependency is unavailable.

Alembic verification:

```text
fresh SQLite:
upgrade head → check → downgrade base → upgrade head = PASS

legacy v0.3 SQLite copy:
stamp 097c446166e1 → upgrade c84d7c4b190a = PASS
```

Fresh seeded database verification:

```text
8 lessons
26 skills
36 prerequisite edges
24 runtime exercises
24 exercise versions
32 runtime review items
L01–L04: 5 blocks / 6 exercises / 8 review items each
L05–L08: source-audited metadata only
```

## 10. Next phase

Phase 1 should not add more curriculum breadth first. It should prove one polished learning vertical slice across L01–L04:

```text
lesson explanation
→ checkpoint/quiz
→ deterministic feedback
→ review activation
→ progress evidence
→ ChordInspector
```

Only after that UX is stable should the project move to interactive Piano + Tone.js + VexFlow and then migrate L05–L08.

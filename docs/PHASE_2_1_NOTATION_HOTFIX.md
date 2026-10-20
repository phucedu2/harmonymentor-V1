# HarmonyMentor Phase 2.1 — Notation crash hotfix

## Symptom
Opening a lesson containing a `notation` block could blank the React application. Browser console showed:

`RuntimeError: IncompleteVoice: Voice does not have enough notes.`

The stack originated at `NotationStaff.tsx` during `Formatter.joinVoices(...)`.

## Root cause
`NotationStaff` manually created a VexFlow `Voice`. In VexFlow 5 the default voice mode is `STRICT`, which requires the tick duration to fill the configured voice. HarmonyMentor lesson notation blocks are short educational snippets, not guaranteed to represent complete measures. A strict voice is therefore the wrong abstraction and may throw `IncompleteVoice` during formatting.

## Fix
- Removed manual strict `Voice` construction.
- Use `Formatter.FormatAndDraw(...)`, whose VexFlow 5 implementation creates a `Voice` in `SOFT` mode for a single notation example.
- Validate notation pitches instead of silently coercing invalid strings to `C4`.
- Catch VexFlow rendering failures locally and show a notation fallback instead of allowing one visualization failure to blank the entire lesson page.
- Added regression tests that prevent reintroducing the strict-voice path.

## Console messages that are not the crash
- React DevTools message: informational.
- Tone.js `AudioContext was not allowed to start`: browser autoplay policy warning before a user gesture; audio playback functions call `Tone.start()` after user interaction.
- `Permissions policy violation: unload` and `Unchecked runtime.lastError`: commonly emitted by browser extensions / embedded tooling and are not the VexFlow lesson crash.

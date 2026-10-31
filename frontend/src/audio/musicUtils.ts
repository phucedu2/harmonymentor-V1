const PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const NATURAL_PC: Record<string, number> = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };

function accidentalOffset(text: string): number {
  const normalized = text.replaceAll("♯", "#").replaceAll("♭", "b");
  let offset = 0;
  for (const char of normalized) {
    if (char === "#") offset += 1;
    else if (char === "b") offset -= 1;
    else if (char === "x") offset += 2;
  }
  return offset;
}

function parsePitchSpelling(note: string): { letter: string; accidental: string; pc: number } | null {
  const match = note.trim().match(/^([A-Ga-g])((?:#{1,2}|b{1,2}|x|♯{1,2}|♭{1,2})?)/);
  if (!match) return null;
  const letter = match[1].toUpperCase();
  const accidental = match[2] ?? "";
  const pc = ((NATURAL_PC[letter] + accidentalOffset(accidental)) % 12 + 12) % 12;
  return { letter, accidental, pc };
}

export function normalizePitchClass(note: string): string {
  const parsed = parsePitchSpelling(note);
  if (!parsed) return note.trim();
  return PITCH_CLASSES[parsed.pc];
}

// Không quy về pitch class trước (không % 12): số quãng tám đi theo chữ cái, nên
// B#4 = 72 và Cb5 = 71, giống Note.midi của Music Engine (SRS 4.4.1, HM-001).
export function scientificToMidi(note: string): number | null {
  const match = note.trim().match(/^([A-Ga-g])((?:#{1,2}|b{1,2}|x|♯{1,2}|♭{1,2})?)(-?\d+)$/);
  if (!match) return null;
  const octave = Number(match[3]);
  return (octave + 1) * 12 + NATURAL_PC[match[1].toUpperCase()] + accidentalOffset(match[2] ?? "");
}

export function midiToScientific(midi: number): string {
  const pc = PITCH_CLASSES[((midi % 12) + 12) % 12];
  const octave = Math.floor(midi / 12) - 1;
  return `${pc}${octave}`;
}

export function pitchClassOf(note: string): string {
  return normalizePitchClass(note.replace(/-?\d+$/, ""));
}

export function pitchClassesToAscendingNotes(pitches: string[], startOctave = 4): string[] {
  let previousMidi = -Infinity;
  return pitches.map((pitch, index) => {
    const pc = normalizePitchClass(pitch);
    const pcIndex = PITCH_CLASSES.indexOf(pc);
    if (pcIndex < 0) return `${pitch}${startOctave}`;
    let octave = startOctave;
    let midi = (octave + 1) * 12 + pcIndex;
    if (index > 0) {
      while (midi <= previousMidi) {
        octave += 1;
        midi += 12;
      }
    }
    previousMidi = midi;
    return `${pc}${octave}`;
  });
}

export function parseProgressionSymbols(text: string): string[] {
  return text
    .split("=")[0]
    .trim()
    .split(/\s*(?:→|->|–|—)\s*/)
    .map((part) => part.trim())
    .filter(Boolean);
}

// Phím đen không cho biết tên nốt: phím giữa D và E vừa là D# vừa là Eb. Khi hiện phím người học
// đã bấm, ghi cả hai tên (D#/Eb4) để không ngầm "sửa" Eb thành D#. Tên chính tả đúng theo
// hợp âm do Music Engine trả trong lời giải; payload gửi máy chủ vẫn là tên thăng (HM-011).
const BLACK_KEY_LABELS: Record<string, string> = { "C#": "C#/Db", "D#": "D#/Eb", "F#": "F#/Gb", "G#": "G#/Ab", "A#": "A#/Bb" };

export function pianoKeyLabel(scientific: string): string {
  const match = scientific.trim().match(/^(.*?)(-?\d+)?$/);
  const name = match?.[1] ?? scientific;
  const octave = match?.[2] ?? "";
  const label = BLACK_KEY_LABELS[normalizePitchClass(name)] ?? name;
  return `${label}${octave}`;
}

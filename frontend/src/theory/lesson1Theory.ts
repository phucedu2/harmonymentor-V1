export type IntervalCode = "M3" | "m3" | "P5" | "d5" | "A5";
export type TriadQuality = "major" | "minor" | "diminished" | "augmented";

const LETTERS = ["C", "D", "E", "F", "G", "A", "B"] as const;
const NATURAL_PC: Record<string, number> = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };

const INTERVALS: Record<IntervalCode, { number: number; semitones: number; label: string }> = {
  M3: { number: 3, semitones: 4, label: "Quãng 3 trưởng" },
  m3: { number: 3, semitones: 3, label: "Quãng 3 thứ" },
  P5: { number: 5, semitones: 7, label: "Quãng 5 đúng" },
  d5: { number: 5, semitones: 6, label: "Quãng 5 giảm" },
  A5: { number: 5, semitones: 8, label: "Quãng 5 tăng" },
};

const TRIADS: Record<TriadQuality, { label: string; suffix: string; third: IntervalCode; fifth: IntervalCode; formula: string }> = {
  major: { label: "Major · Trưởng", suffix: "", third: "M3", fifth: "P5", formula: "1–3–5" },
  minor: { label: "Minor · Thứ", suffix: "m", third: "m3", fifth: "P5", formula: "1–♭3–5" },
  diminished: { label: "Diminished · Giảm", suffix: "dim", third: "m3", fifth: "d5", formula: "1–♭3–♭5" },
  augmented: { label: "Augmented · Tăng", suffix: "aug", third: "M3", fifth: "A5", formula: "1–3–#5" },
};

function mod12(value: number) {
  return ((value % 12) + 12) % 12;
}

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

export function parseSpelledPitch(note: string): { letter: string; accidental: string; pc: number } {
  const match = note.trim().match(/^([A-Ga-g])((?:#{1,2}|b{1,2}|x|♯{1,2}|♭{1,2})?)$/);
  if (!match) throw new Error(`Không đọc được tên nốt ${note}`);
  const letter = match[1].toUpperCase();
  const accidental = match[2].replaceAll("♯", "#").replaceAll("♭", "b");
  return { letter, accidental, pc: mod12(NATURAL_PC[letter] + accidentalOffset(accidental)) };
}

function accidentalForDelta(delta: number): string {
  let value = delta;
  while (value > 6) value -= 12;
  while (value < -6) value += 12;
  if (value === 0) return "";
  if (value === 1) return "#";
  if (value === 2) return "##";
  if (value === -1) return "b";
  if (value === -2) return "bb";
  // Lesson 1 selector is designed so simple intervals stay within double accidentals.
  return value > 0 ? "#".repeat(value) : "b".repeat(Math.abs(value));
}

export function spellInterval(root: string, code: IntervalCode): string {
  const parsed = parseSpelledPitch(root);
  const spec = INTERVALS[code];
  const rootLetterIndex = LETTERS.indexOf(parsed.letter as (typeof LETTERS)[number]);
  const targetLetter = LETTERS[(rootLetterIndex + spec.number - 1) % 7];
  const desiredPc = mod12(parsed.pc + spec.semitones);
  const naturalPc = NATURAL_PC[targetLetter];
  let delta = desiredPc - naturalPc;
  if (delta > 6) delta -= 12;
  if (delta < -6) delta += 12;
  return `${targetLetter}${accidentalForDelta(delta)}`;
}

export function intervalExample(root: string, code: IntervalCode) {
  const spec = INTERVALS[code];
  return {
    code,
    label: spec.label,
    semitones: spec.semitones,
    root,
    upper: spellInterval(root, code),
  };
}

export function triadLetterFrame(root: string): string[] {
  const parsed = parseSpelledPitch(root);
  const rootLetterIndex = LETTERS.indexOf(parsed.letter as (typeof LETTERS)[number]);
  return [
    root,
    LETTERS[(rootLetterIndex + 2) % 7],
    LETTERS[(rootLetterIndex + 4) % 7],
  ];
}

export function buildTriad(root: string, quality: TriadQuality) {
  const spec = TRIADS[quality];
  const notes = [root, spellInterval(root, spec.third), spellInterval(root, spec.fifth)];
  return {
    root,
    quality,
    label: spec.label,
    formula: spec.formula,
    intervalFormula: `${spec.third} + ${spec.fifth}`,
    symbol: `${root}${spec.suffix}`,
    notes,
  };
}

export function toScientificInterval(root: string, code: IntervalCode, rootOctave = 4): string[] {
  const parsed = parseSpelledPitch(root);
  const spec = INTERVALS[code];
  const upper = spellInterval(root, code);
  const upperOctave = rootOctave + Math.floor((parsed.pc + spec.semitones) / 12);
  return [`${root}${rootOctave}`, `${upper}${upperOctave}`];
}

export function toScientificTriad(root: string, quality: TriadQuality, rootOctave = 4): string[] {
  const parsed = parseSpelledPitch(root);
  const spec = TRIADS[quality];
  const triad = buildTriad(root, quality);
  return [
    `${triad.notes[0]}${rootOctave}`,
    `${triad.notes[1]}${rootOctave + Math.floor((parsed.pc + INTERVALS[spec.third].semitones) / 12)}`,
    `${triad.notes[2]}${rootOctave + Math.floor((parsed.pc + INTERVALS[spec.fifth].semitones) / 12)}`,
  ];
}

export function equivalentPitchClass(a: string, b: string): boolean {
  try {
    return parseSpelledPitch(a).pc === parseSpelledPitch(b).pc;
  } catch {
    return false;
  }
}

export const LESSON1_INTERVAL_CODES: IntervalCode[] = ["M3", "m3", "P5", "d5"];
export const LESSON1_TRIAD_QUALITIES: TriadQuality[] = ["major", "minor", "diminished", "augmented"];

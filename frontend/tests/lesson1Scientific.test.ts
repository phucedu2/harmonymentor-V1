// HM-001 / NL-L01-01: khuông nhạc, tên nốt và MIDI của L01 phải cùng mô tả một cao độ.
// Đáp án lấy từ Music Engine qua fixtures/l01_engine_scientific.json (scripts/sinh_bang_l01_engine.py).
import { describe, expect, it } from "vitest";
import golden from "./fixtures/l01_engine_scientific.json";
import { midiToScientific, scientificToMidi } from "../src/audio/musicUtils";
import { toScientificInterval, toScientificTriad, type IntervalCode, type TriadQuality } from "../src/theory/lesson1Theory";

const SEMITONES: Record<IntervalCode, number> = { M3: 4, m3: 3, P5: 7, d5: 6, A5: 8 };

describe("ca bắt buộc của ticket", () => {
  it.each([
    ["G#", "M3", "G#4", "B#4", 72],
    ["E", "A5", "E4", "B#4", 72],
    ["Ab", "m3", "Ab4", "Cb5", 71],
    ["F", "d5", "F4", "Cb5", 71],
  ] as const)("%s4 + %s → %s–%s, MIDI nốt trên %i", (root, code, lower, upper, midi) => {
    expect(toScientificInterval(root, code)).toEqual([lower, upper]);
    expect(scientificToMidi(upper)).toBe(midi);
  });

  it("hợp âm G# trưởng và F giảm", () => {
    expect(toScientificTriad("G#", "major")).toEqual(["G#4", "B#4", "D#5"]);
    expect(toScientificTriad("F", "diminished")).toEqual(["F4", "Ab4", "Cb5"]);
  });

  it.each([
    ["B#3", 60], ["B#4", 72], ["Cb4", 59], ["Cb5", 71], ["B##4", 73], ["Cbb5", 70],
  ] as const)("scientificToMidi(%s) = %i", (note, midi) => {
    expect(scientificToMidi(note)).toBe(midi);
  });

  it("các ca thông thường không đổi", () => {
    expect(toScientificInterval("C", "M3")).toEqual(["C4", "E4"]);
    expect(toScientificInterval("D", "m3")).toEqual(["D4", "F4"]);
    expect(toScientificInterval("G", "P5")).toEqual(["G4", "D5"]);
    expect(["C4", "E4", "D4", "F4", "G4", "D5"].map(scientificToMidi)).toEqual([60, 64, 62, 65, 67, 74]);
  });

  it("nhận ký hiệu x, ♯, ♭ và từ chối chuỗi không phải scientific pitch", () => {
    expect(scientificToMidi("Bx4")).toBe(73);
    expect(scientificToMidi("B♯4")).toBe(72);
    expect(scientificToMidi("C♭5")).toBe(71);
    expect(scientificToMidi("C♭♭5")).toBe(70);
    expect(scientificToMidi("B#")).toBeNull();
    expect(scientificToMidi("H4")).toBeNull();
  });
});

describe("đối chiếu Music Engine trên mọi nốt gốc L01", () => {
  it("bảng phủ đủ 17 cách viết nốt gốc", () => {
    expect(golden.roots).toHaveLength(17);
  });

  it.each(golden.intervals.map((row) => [row.root, row.code, row] as const))("quãng %s + %s", (root, code, row) => {
    const expected = row.notes.map((n) => n.name);
    const notes = toScientificInterval(root, code as IntervalCode);
    expect(notes).toEqual(expected);
    const midi = notes.map(scientificToMidi);
    expect(midi).toEqual(row.notes.map((n) => n.midi));
    // Khoảng cách trên khuông phải đúng số nửa cung của quãng.
    expect(midi[1]! - midi[0]!).toBe(SEMITONES[code as IntervalCode]);
  });

  it.each(golden.triads.map((row) => [row.root, row.quality, row] as const))("hợp âm %s %s", (root, quality, row) => {
    const notes = toScientificTriad(root, quality as TriadQuality);
    expect(notes).toEqual(row.notes.map((n) => n.name));
    const midi = notes.map(scientificToMidi) as number[];
    expect(midi).toEqual(row.notes.map((n) => n.midi));
    // Thế gốc, đi lên, gọn trong một quãng tám.
    expect(midi[0]! < midi[1]! && midi[1]! < midi[2]! && midi[2]! - midi[0]! < 12).toBe(true);
  });

  it.each(golden.midi.map((row) => [row.name, row.midi] as const))("MIDI %s = %i như Engine", (name, midi) => {
    expect(scientificToMidi(name)).toBe(midi);
  });
});

describe("đường phát âm của NoteAudioButton", () => {
  // NoteAudioButton đổi scientific → MIDI → tên theo dấu thăng trước khi gửi Tone.
  const sounding = (notes: string[]) => notes.map((n) => midiToScientific(scientificToMidi(n)!));

  it("cao độ gửi Tone trùng cao độ trên khuông", () => {
    expect(sounding(toScientificInterval("G#", "M3"))).toEqual(["G#4", "C5"]);
    expect(sounding(toScientificInterval("Ab", "m3"))).toEqual(["G#4", "B4"]);
    expect(sounding(toScientificTriad("F", "diminished"))).toEqual(["F4", "G#4", "B4"]);
  });
});

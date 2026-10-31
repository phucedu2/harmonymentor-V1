// phuc-music Bước 2: piano không được hiện "D#" khi người học bấm phím Eb (lỗi đã biết "Eb → D#").
import { describe, expect, it } from "vitest";
import { pianoKeyLabel } from "../src/audio/musicUtils";

describe("nhãn phím piano đã bấm", () => {
  it.each([
    ["D#4", "D#/Eb4"], ["C#3", "C#/Db3"], ["F#4", "F#/Gb4"], ["G#5", "G#/Ab5"], ["A#4", "A#/Bb4"],
  ])("phím đen %s hiện cả hai tên: %s", (note, label) => {
    expect(pianoKeyLabel(note)).toBe(label);
  });

  it.each([["C4", "C4"], ["E4", "E4"], ["B3", "B3"]])("phím trắng %s giữ nguyên", (note, label) => {
    expect(pianoKeyLabel(note)).toBe(label);
  });

  it("không kèm quãng tám vẫn đọc được", () => {
    expect(pianoKeyLabel("D#")).toBe("D#/Eb");
  });
});

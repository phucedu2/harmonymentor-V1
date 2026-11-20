// phuc-music Bước 2: lesson1Theory.ts chỉ gọi API Music Engine, không tự tính nốt.
import { afterEach, describe, expect, it, vi } from "vitest";
import golden from "./fixtures/l01_engine_scientific.json";
import { readFileSync } from "node:fs";
import { api, type Lesson1Theory } from "../src/api";
import { clearLesson1TheoryCache, fetchLesson1Theory, intervalOf, pitchNames, triadOf } from "../src/theory/lesson1Theory";

// Dựng câu trả lời API giả từ bảng vàng (bảng sinh bởi Engine; backend test khẳng định API trùng bảng).
function fakeResponse(root: string): Lesson1Theory {
  return {
    root, root_octave: 4, letter_frame: [],
    intervals: golden.intervals.filter((r) => r.root === root).map((r) => ({ code: r.code, semitones: 0, upper: r.notes[1].name.replace(/\d+$/, ""), pitches: r.notes })),
    triads: golden.triads.filter((r) => r.root === root).map((r) => ({
      quality: r.quality, symbol: root, formula: [], interval_formula: [], notes: r.notes.map((n) => n.name.replace(/\d+$/, "")), pitches: r.notes,
    })),
  };
}

afterEach(() => {
  vi.restoreAllMocks();
  clearLesson1TheoryCache();
});

describe("lấy dữ liệu Bài 1 từ Music Engine", () => {
  it("gọi API một lần cho mỗi nốt gốc rồi dùng bộ đệm", async () => {
    const spy = vi.spyOn(api, "lesson1Theory").mockImplementation(async (root) => fakeResponse(root));
    const a = await fetchLesson1Theory("G#");
    const b = await fetchLesson1Theory("G#");
    await fetchLesson1Theory("Ab");
    expect(a).toBe(b);
    expect(spy).toHaveBeenCalledTimes(2);
    expect(spy).toHaveBeenNthCalledWith(1, "G#");
  });

  it("lỗi mạng không nằm lại trong bộ đệm", async () => {
    const spy = vi.spyOn(api, "lesson1Theory")
      .mockRejectedValueOnce({ code: "NETWORK", message: "mất mạng" })
      .mockImplementation(async (root) => fakeResponse(root));
    await expect(fetchLesson1Theory("F")).rejects.toMatchObject({ code: "NETWORK" });
    await Promise.resolve();
    const data = await fetchLesson1Theory("F");
    expect(spy).toHaveBeenCalledTimes(2);
    expect(pitchNames(triadOf(data, "diminished"))).toEqual(["F4", "Ab4", "Cb5"]);
  });

  it("đọc quãng và hợp âm theo mã, báo lỗi khi máy chủ thiếu", () => {
    const data = fakeResponse("G#");
    expect(intervalOf(data, "M3").upper).toBe("B#");
    expect(pitchNames(intervalOf(data, "M3"))).toEqual(["G#4", "B#4"]);
    expect(() => intervalOf({ ...data, intervals: [] }, "M3")).toThrow("M3");
    expect(() => triadOf({ ...data, triads: [] }, "major")).toThrow("major");
  });

  it("mã nguồn không còn tự tính nhạc lý (không bảng nửa cung, không dựng quãng)", () => {
    const source = readFileSync(new URL("../src/theory/lesson1Theory.ts", import.meta.url), "utf8");
    expect(source).not.toMatch(/NATURAL_PC|semitones:\s*\d|spellInterval|mod12/);
  });
});

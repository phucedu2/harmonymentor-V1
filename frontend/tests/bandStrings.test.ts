// GĐ4 (08/11/2026): kênh Dây (cello) và ba âm sắc guitar. Cao độ cello lấy từ nốt Engine đã dựng cho phím (chỉ dời
// quãng tám); bật/tắt kênh Dây không được làm đổi các kênh khác; mẫu cello có đủ nốt trong tầm đệm.
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import { foldIntoCello, humanize, stringsPad } from "../src/audio/band/humanize";
import { GUITAR_TONE_PRESETS, resolveGuitarTone } from "../src/audio/band/mixer";
import type { SampleManifest } from "../src/audio/band/samples";
import { BAND_CHANNELS, DEFAULT_MIX, GUITAR_TONE_LABELS, type Arrangement } from "../src/audio/band/types";

const load = (name: string) => JSON.parse(readFileSync(new URL(`./fixtures/arrangement-${name}.json`, import.meta.url), "utf8")) as Arrangement;
const pop = load("pop");
const rock = load("rock");
const manifest = JSON.parse(readFileSync(new URL("../public/samples/manifest.json", import.meta.url), "utf8")) as SampleManifest;

describe("kênh Dây (cello)", () => {
  it("mặc định tắt, và có trong danh sách kênh", () => {
    expect(BAND_CHANNELS).toContain("strings");
    expect(DEFAULT_MIX.strings.muted).toBe(true);
  });

  it("dời quãng tám giữ nguyên tên nốt và nằm trong tầm cello đệm", () => {
    for (let m = 20; m <= 100; m += 1) {
      const f = foldIntoCello(m);
      expect(f % 12).toBe(m % 12);
      expect(f).toBeGreaterThanOrEqual(43);
      expect(f).toBeLessThanOrEqual(64);
    }
  });

  it("mỗi nhát cello là nốt có trong hợp âm phím (cùng tên nốt) và dùng nhạc cụ cello", () => {
    const pad = stringsPad(pop);
    expect(pad.length).toBeGreaterThan(0);
    const pcsByBeat = new Map<number, Set<number>>();
    for (const e of pop.tracks.keys.events) {
      const set = pcsByBeat.get(e.beat) ?? new Set<number>();
      e.midi.forEach((m) => set.add(m % 12));
      pcsByBeat.set(e.beat, set);
    }
    for (const h of pad) {
      expect(h.channel).toBe("strings");
      expect(h.instrument).toBe("cello");
      expect(pcsByBeat.get(h.beat)?.has((h.midi as number) % 12)).toBe(true);
    }
  });

  it("bật kênh Dây chỉ thêm nhát, không đổi nhát của các kênh khác", () => {
    const base = humanize(rock, { seed: 3, bpm: 110 });
    const withStrings = humanize(rock, { seed: 3, bpm: 110, strings: true });
    expect(withStrings.filter((h) => h.channel !== "strings")).toEqual(base);
    expect(withStrings.some((h) => h.channel === "strings")).toBe(true);
  });

  it("manifest có cello đủ nốt trong tầm đệm, giấy phép CC0", () => {
    const cello = manifest.instruments.cello;
    expect(cello.source.license).toMatch(/CC0/);
    const midis = new Set(cello.pieces.notes.map((z) => z.midi));
    for (const m of [43, 48, 55, 60, 64]) {
      const near = Math.min(...[...midis].map((x) => Math.abs((x as number) - m)));
      expect(near).toBeLessThanOrEqual(2); // dời tối đa 2 nửa cung: vẫn nghe tự nhiên
    }
  });
});

describe("âm sắc guitar", () => {
  it("có đúng ba âm sắc để chọn cộng một chế độ theo phong cách", () => {
    expect(Object.keys(GUITAR_TONE_LABELS)).toEqual(["auto", "clean", "light", "heavy"]);
    expect(Object.keys(GUITAR_TONE_PRESETS)).toEqual(["clean", "light", "heavy"]);
  });

  it("auto theo phong cách: có méo → rè mạnh, không méo → sạch; các lựa chọn khác giữ nguyên", () => {
    expect(resolveGuitarTone("auto", true)).toBe("heavy");
    expect(resolveGuitarTone("auto", false)).toBe("clean");
    expect(resolveGuitarTone("light", true)).toBe("light");
    expect(resolveGuitarTone("clean", true)).toBe("clean");
  });

  it("độ méo tăng dần sạch < rè nhẹ < rè mạnh; sạch không méo; rè mạnh giữ giá trị overdrive cũ", () => {
    const { clean, light, heavy } = GUITAR_TONE_PRESETS;
    expect(clean.wet).toBe(0);
    expect(clean.drive).toBe(0);
    expect(light.drive).toBeGreaterThan(clean.drive);
    expect(heavy.drive).toBeGreaterThan(light.drive);
    expect(heavy).toEqual({ pre: 160, drive: 0.55, wet: 1, hp: 90, cab: 5500 });
    expect(light.cab).toBeGreaterThan(heavy.cab); // rè nhẹ sáng hơn rè mạnh
  });
});

// Backing track "ban nhạc thật" (02/11/2026, ADR-012 đề xuất): humanize có seed, giới hạn ±30 ms, rải hợp âm,
// quạt guitar, swing, dẫn giọng và fill trên bản phối thật do backend sinh (fixture), manifest mẫu đủ nhạc cụ.
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import { MAX_OFFSET_SEC, humanize, onsetOffsets, rng, swingBeat } from "../src/audio/band/humanize";
import type { Arrangement } from "../src/audio/band/types";
import { zonesFor, type SampleManifest } from "../src/audio/band/samples";

const load = (name: string) => JSON.parse(readFileSync(new URL(`./fixtures/arrangement-${name}.json`, import.meta.url), "utf8")) as Arrangement;
const pop = load("pop");
const lofi = load("lofi");
const jazz = load("jazz");
const rock = load("rock");
const manifest = JSON.parse(readFileSync(new URL("../public/samples/manifest.json", import.meta.url), "utf8")) as SampleManifest;

describe("humanize có seed", () => {
  it("cùng seed → cùng kết quả; khác seed → khác", () => {
    expect(humanize(pop, { seed: 5, bpm: 100 })).toEqual(humanize(pop, { seed: 5, bpm: 100 }));
    expect(humanize(pop, { seed: 5, bpm: 100 })).not.toEqual(humanize(pop, { seed: 6, bpm: 100 }));
  });

  it("PRNG mulberry32 lặp lại đúng dãy", () => {
    const a = rng(42); const b = rng(42);
    expect([a(), a(), a()]).toEqual([b(), b(), b()]);
  });

  it("không nhát nào lệch quá ±30 ms (pocket + nhiễu), mọi phong cách", () => {
    for (const arr of [pop, lofi, jazz, rock]) {
      const hits = humanize(arr, { seed: 9, bpm: arr.bpm });
      for (const ch of ["drums", "bass", "chords", "guitar"] as const) {
        for (const off of onsetOffsets(hits, ch)) expect(Math.abs(off)).toBeLessThanOrEqual(MAX_OFFSET_SEC + 1e-9);
      }
    }
  });

  it("lệch thật sự có (không phải đúng tuyệt đối như máy) và lực đánh thay đổi", () => {
    const hits = humanize(pop, { seed: 2, bpm: 100 }).filter((h) => h.channel === "drums");
    const offsets = new Set(hits.map((h) => h.offset.toFixed(4)));
    expect(offsets.size).toBeGreaterThan(hits.length / 2);
    const hatVels = hits.filter((h) => h.piece === "hh_c").map((h) => h.vel.toFixed(3));
    expect(new Set(hatVels).size).toBeGreaterThan(10);
  });

  it("lo-fi: snare trễ trung bình 15–30 ms (pocket lười)", () => {
    const sn = humanize(lofi, { seed: 3, bpm: 80 }).filter((h) => h.piece === "snare").map((h) => h.offset);
    const mean = sn.reduce((a, b) => a + b, 0) / sn.length;
    expect(mean).toBeGreaterThan(0.015);
    expect(mean).toBeLessThanOrEqual(0.03);
  });

  it("piano rải hợp âm từ trầm lên: nốt cao vang sau nốt trầm", () => {
    const hits = humanize(pop, { seed: 4, bpm: 100 }).filter((h) => h.channel === "chords");
    const first = hits.filter((h) => h.beat === hits[0].beat);
    const sorted = [...first].sort((a, b) => (a.midi ?? 0) - (b.midi ?? 0));
    expect(sorted[sorted.length - 1].offset).toBeGreaterThan(sorted[0].offset);
  });

  it("guitar quạt lên: dây cao vang trước, nhẹ hơn quạt xuống", () => {
    const hits = humanize(load("pop"), { seed: 1, bpm: 100 }).filter((h) => h.channel === "guitar");
    const ups = hits.filter((h) => h.art === "up");
    const downs = hits.filter((h) => h.art === "down");
    if (ups.length) {
      const beat = ups[0].beat;
      const strum = ups.filter((h) => h.beat === beat).sort((a, b) => a.offset - b.offset);
      expect(strum[0].midi!).toBeGreaterThan(strum[strum.length - 1].midi!);
      const avg = (xs: typeof hits) => xs.reduce((a, h) => a + h.vel, 0) / xs.length;
      expect(avg(ups)).toBeLessThan(avg(downs));
    }
  });

  it("swing: móc kép thứ hai của cặp dời tới tỷ lệ swing, phách chính giữ nguyên", () => {
    expect(swingBeat(1.25, 0.58, "16n")).toBeCloseTo(1.29);
    expect(swingBeat(1.5, 0.6, "8n")).toBeCloseTo(1.6);
    expect(swingBeat(2, 0.6, "8n")).toBe(2);
    expect(swingBeat(1.25, 0, "16n")).toBe(1.25);
  });
});

describe("bản phối từ backend (fixture)", () => {
  const blocks = (arr: Arrangement) => {
    const out: number[][] = [];
    for (const e of arr.tracks.keys.events) if (e.art !== "lh" && JSON.stringify(out.at(-1)) !== JSON.stringify(e.midi)) out.push(e.midi);
    return out;
  };
  const move = (a: number[], b: number[]) => a.length === b.length
    ? [...a].sort((x, y) => x - y).reduce((s, x, i) => s + Math.abs(x - [...b].sort((p, q) => p - q)[i]), 0) : 99;

  it("dẫn giọng: đổi hợp âm pop đi ≤ 7 nửa cung tổng cộng", () => {
    const bs = blocks(pop);
    for (let i = 1; i < bs.length; i += 1) expect(move(bs[i - 1], bs[i])).toBeLessThanOrEqual(7);
  });

  it("fill (tom) chỉ nằm ở ô cuối mỗi vòng", () => {
    const barsPerCycle = pop.bars_per_cycle;
    const toms = pop.tracks.drums.events.filter((e) => e.drum.startsWith("tom_"));
    expect(toms.length).toBeGreaterThan(0);
    for (const t of toms) expect(Math.floor(t.beat / 4) % barsPerCycle).toBe(barsPerCycle - 1);
  });

  it("mọi phong cách có đủ nhạc cụ trong manifest mẫu", () => {
    for (const arr of [pop, lofi, jazz, rock]) {
      expect(manifest.instruments[arr.tracks.keys.instrument]).toBeDefined();
      expect(manifest.instruments[arr.tracks.bass.instrument]).toBeDefined();
      const pieces = new Set(Object.keys(manifest.instruments.drums.pieces).concat(Object.keys(manifest.instruments.perc.pieces)));
      for (const e of arr.tracks.drums.events) expect(pieces.has(e.drum)).toBe(true);
    }
  });
});

describe("manifest mẫu", () => {
  it("piano ≥ 3 lớp lực, trống ≥ 2 lớp, snare/hat có round-robin", () => {
    expect(manifest.instruments.piano.layers).toBeGreaterThanOrEqual(3);
    const sn = manifest.instruments.drums.pieces.snare;
    expect(new Set(sn.map((z) => z.layer)).size).toBeGreaterThanOrEqual(2);
    expect(new Set(sn.filter((z) => z.layer === sn[0].layer).map((z) => z.rr)).size).toBeGreaterThanOrEqual(2);
    expect(new Set(manifest.instruments.drums.pieces.hh_c.map((z) => z.rr)).size).toBeGreaterThanOrEqual(2);
  });

  it("chỉ có giấy phép CC0 hoặc CC BY", () => {
    for (const inst of Object.values(manifest.instruments)) expect(["CC0 1.0", "CC BY 3.0"]).toContain(inst.source.license);
  });

  it("bản nhẹ (điện thoại) dùng ít mẫu hơn bản đầy đủ", () => {
    const full = Object.values(zonesFor(manifest.instruments.piano, false)).flat().length;
    const lite = Object.values(zonesFor(manifest.instruments.piano, true)).flat().length;
    expect(lite).toBeLessThan(full);
    expect(lite).toBeGreaterThan(0);
  });
});

describe("bàn trộn: bộ cắt mềm cuối chuỗi", async () => {
  const { softClip } = await import("../src/audio/band/mixer");
  it("giữ nguyên tín hiệu nhỏ, không bao giờ vượt trần 0,97 (âm thanh float: 1,0 mới là vỡ)", () => {
    expect(softClip(0.5)).toBe(0.5);
    expect(softClip(-0.7)).toBe(-0.7);
    for (const x of [0.8, 1, 1.5, 2, 10]) {
      expect(softClip(x)).toBeLessThanOrEqual(0.97);
      expect(softClip(-x)).toBeCloseTo(-softClip(x));
    }
    expect(softClip(0.9)).toBeGreaterThan(softClip(0.8)); // đơn điệu: to hơn vẫn to hơn, chỉ nén lại
  });
});

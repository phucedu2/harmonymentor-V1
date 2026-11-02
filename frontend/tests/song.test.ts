// Chế độ Bài hát (02/11/2026, ADR-013 đề xuất): lịch phát theo khối không rơi/trùng nhát, tempo chậm dần,
// tự động hóa tại một phách, thao tác form trên dòng thời gian, và humanize có kênh hook.
// Fixture song-pop-short.json do backend thật sinh (arrange_song pop, Ngắn, C–G–Am–F, seed 1).
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import { humanize } from "../src/audio/band/humanize";
import {
  BLOCK_BEATS, automationAt, beatToSeconds, blockOf, mmss, sectionAt, splitBlocks, tempoAt,
} from "../src/audio/band/songSchedule";
import type { Arrangement, FormSection, PlayHit } from "../src/audio/band/types";
import {
  MAX_SONG_BARS, addSection, barOptions, emptyForm, formForSave, moveSection, patchSection, removeSection, totalBars,
} from "../src/components/compose/songForm";

const song = JSON.parse(readFileSync(new URL("./fixtures/song-pop-short.json", import.meta.url), "utf8")) as Arrangement;

const hit = (beat: number): PlayHit => ({ channel: "drums", instrument: "drums", beat, offset: 0, dur: 0.1, midi: null, piece: "kick", vel: 0.8, art: "hit" });

describe("lịch phát theo khối 16 phách", () => {
  it("nhát đúng ranh giới thuộc khối sau, sát ranh giới thuộc khối trước", () => {
    expect(blockOf(0)).toBe(0);
    expect(blockOf(15.999)).toBe(0);
    expect(blockOf(16)).toBe(1);
    expect(blockOf(16 - 1e-12)).toBe(1); // sai số dấu phẩy động không đẩy nhát về khối trước
    expect(blockOf(47.5)).toBe(2);
  });

  it("chia khối giữ đủ mọi nhát, không trùng (bài thật)", () => {
    const hits = humanize(song, { seed: 3, bpm: song.bpm });
    const blocks = splitBlocks(hits);
    const flat = [...blocks.values()].flat();
    expect(flat.length).toBe(hits.length);
    expect(new Set(flat).size).toBe(hits.length);
    for (const [k, list] of blocks) {
      for (const h of list) {
        expect(h.beat).toBeGreaterThanOrEqual(k * BLOCK_BEATS - 1e-9);
        expect(h.beat).toBeLessThan((k + 1) * BLOCK_BEATS);
      }
    }
    // Bài Ngắn 24 ô = 96 phách → 6 khối có nhát (có thể thêm khối đuôi ngân)
    expect(blocks.size).toBeGreaterThanOrEqual(6);
  });

  it("nhát giả ở đúng mọi ranh giới không rơi", () => {
    const hits = [0, 16, 32, 48, 63.75, 64].map(hit);
    const blocks = splitBlocks(hits);
    expect([...blocks.keys()].sort()).toEqual([0, 1, 2, 3, 4]);
    expect(blocks.get(3)?.map((h) => h.beat)).toEqual([48, 63.75]);
  });
});

describe("tempo và giây thật", () => {
  const map = [{ beat: 0, bpm: 100, ramp: false }, { beat: 88, bpm: 100, ramp: false }, { beat: 96, bpm: 85, ramp: true }];

  it("không có bản đồ tempo → giây = phách × 60 / BPM", () => {
    expect(beatToSeconds(96, 120)).toBeCloseTo(48, 6);
    expect(tempoAt(50, 120)).toBe(120);
  });

  it("chậm dần tuyến tính 100 → 85 BPM trong 2 ô cuối", () => {
    expect(tempoAt(40, 100, map)).toBe(100);
    expect(tempoAt(92, 100, map)).toBeCloseTo(92.5, 6);
    expect(tempoAt(96, 100, map)).toBe(85);
    expect(tempoAt(200, 100, map)).toBe(85);
  });

  it("đoạn chậm dần dài hơn đúng tích phân 60/tempo", () => {
    const plain = beatToSeconds(96, 100);
    const rit = beatToSeconds(96, 100, map);
    // ∫ 60/(100 − 15t/8) dt từ 0 tới 8 phách = 60·8/15·ln(100/85)
    const expected = (88 * 60) / 100 + ((60 * 8) / 15) * Math.log(100 / 85);
    expect(rit).toBeGreaterThan(plain);
    expect(rit).toBeCloseTo(expected, 2);
  });

  it("m:ss", () => {
    expect(mmss(0)).toBe("0:00");
    expect(mmss(65.4)).toBe("1:05");
    expect(mmss(179.6)).toBe("3:00");
  });
});

describe("tự động hóa tại một phách (nhảy tới giữa bài)", () => {
  it("mặc định khi chưa có điểm nào", () => {
    expect(automationAt([], 10)).toEqual({ master: 0, filter: 20000, reverb: 1, reverb_return: 1 });
  });

  it("đặt ngay, rồi dốc tuyến tính cho dB, dốc mũ cho bộ lọc", () => {
    const pts = [
      { beat: 0, target: "master" as const, value: -6, ramp: 0 },
      { beat: 16, target: "master" as const, value: 0, ramp: 8 },
      { beat: 0, target: "filter" as const, value: 500, ramp: 0 },
      { beat: 0, target: "filter" as const, value: 20000, ramp: 16 },
    ];
    expect(automationAt(pts, 8).master).toBe(-6);
    expect(automationAt(pts, 20).master).toBeCloseTo(-3, 6);
    expect(automationAt(pts, 30).master).toBe(0);
    // dốc mũ: giữa đường 500 → 20000 là trung bình nhân ≈ 3162 Hz, không phải trung bình cộng
    expect(automationAt(pts, 8).filter).toBeCloseTo(Math.sqrt(500 * 20000), 0);
    expect(automationAt(pts, 40).filter).toBe(20000);
  });

  it("bài thật: Chorus to hơn Verse theo thiết kế", () => {
    const sections = song.sections ?? [];
    const verse = sections.find((s) => s.type === "verse");
    const chorus = sections.find((s) => s.type === "chorus");
    expect(verse && chorus).toBeTruthy();
    const pts = song.automation ?? [];
    const v = automationAt(pts, verse!.start_beat + 2).master;
    const c = automationAt(pts, chorus!.start_beat + 2).master;
    expect(c).toBeGreaterThan(v);
  });

  it("sectionAt trả đoạn đang phát, ngoài bài → null", () => {
    const sections = song.sections ?? [];
    expect(sectionAt(sections, 0)?.type).toBe(sections[0].type);
    const last = sections[sections.length - 1];
    expect(sectionAt(sections, last.end_beat - 0.01)?.id).toBe(last.id);
    expect(sectionAt(sections, last.end_beat)).toBeNull();
  });
});

describe("kênh hook", () => {
  it("humanize sinh nhát kênh hook, cao độ đúng như backend (frontend không tự tính nốt)", () => {
    const hits = humanize(song, { seed: 1, bpm: song.bpm }).filter((h) => h.channel === "hook");
    const events = song.tracks.hook?.events ?? [];
    expect(events.length).toBeGreaterThan(0);
    const midis = events.flatMap((e) => e.midi);
    expect(hits.length).toBe(midis.length);
    expect(new Set(hits.map((h) => h.midi))).toEqual(new Set(midis));
    for (const h of hits) expect(h.midi).toBeGreaterThanOrEqual(72);
  });
});

describe("thao tác form trên dòng thời gian", () => {
  const base: FormSection[] = [
    { id: "s1", type: "intro", label: null, bars: 4, progression: "A", energy: 1, feel: "auto", hook: true, transition: "auto", seed: null },
    { id: "s2", type: "verse", label: null, bars: 8, progression: "A", energy: 2, feel: "auto", hook: true, transition: "auto", seed: null },
    { id: "s3", type: "chorus", label: null, bars: 8, progression: "B", energy: 4, feel: "auto", hook: true, transition: "auto", seed: null },
  ];

  it("thêm đoạn sau vị trí, id mới không trùng, mặc định theo vai trò", () => {
    const out = addSection(base, "bridge", 1);
    expect(out.map((s) => s.type)).toEqual(["intro", "verse", "bridge", "chorus"]);
    expect(new Set(out.map((s) => s.id)).size).toBe(4);
    expect(out[2]).toMatchObject({ bars: 8, progression: "C", energy: 3 });
    expect(addSection(base, "intro", -1)[0].id).not.toBe("s1");
  });

  it("không vượt 160 ô", () => {
    const big = Array.from({ length: 10 }, (_, i) => ({ ...base[1], id: `v${i}`, bars: 16 }));
    expect(totalBars(big)).toBe(MAX_SONG_BARS);
    expect(addSection(big, "outro", 9)).toBe(big);
    expect(patchSection(big, 0, { bars: 12 })).not.toBe(big);
    expect(patchSection(base, 0, { bars: 200 })).toBe(base);
  });

  it("kéo đổi thứ tự, chỉ số sai thì giữ nguyên", () => {
    expect(moveSection(base, 2, 0).map((s) => s.id)).toEqual(["s3", "s1", "s2"]);
    expect(moveSection(base, 0, 2).map((s) => s.id)).toEqual(["s2", "s3", "s1"]);
    expect(moveSection(base, 0, 5)).toBe(base);
  });

  it("không xóa đoạn cuối cùng", () => {
    expect(removeSection(base, 1).map((s) => s.id)).toEqual(["s1", "s3"]);
    const one = [base[0]];
    expect(removeSection(one, 0)).toBe(one);
  });

  it("lựa chọn số ô gồm bội số độ dài vòng (vòng 3 ô → 3, 6, 9, 12, 15)", () => {
    expect(barOptions(4)).toEqual([2, 4, 8, 12, 16]);
    expect(barOptions(3)).toEqual([2, 3, 4, 6, 8, 9, 12, 15, 16]);
  });

  it("lưu: vòng A lấy từ lưới, vòng trống gửi null", () => {
    const f = { ...emptyForm(["C", "G"]), progressions: { A: ["X"], B: [null, null], C: ["F", null] } };
    const saved = formForSave(f, ["C", "G", "Am", "F"]);
    expect(saved.progressions).toEqual({ A: ["C", "G", "Am", "F"], B: null, C: ["F", null] });
    expect(emptyForm(["C"]).modulate.enabled).toBe(false); // QĐ 5A: chuyển giọng tắt mặc định
  });
});

import { describe, expect, it } from "vitest";
import { AUTO_FLOOR_CAP, highpass, LEGACY, MicPipeline, NoiseFloor, ROBUST, VoteStabilizer } from "./pipeline";
import { rms, yin } from "./yin";

const SR = 48000;

function tone(hz: number, amp = 0.1, n = 2048, noise = 0, seed = 3): Float32Array {
  const out = new Float32Array(n);
  let s = seed;
  const rand = () => { s = (s * 16807) % 2147483647; return s / 2147483647 - 0.5; };
  for (let i = 0; i < n; i += 1) out[i] = amp * (Math.sin((2 * Math.PI * hz * i) / SR) + 0.5 * Math.sin((4 * Math.PI * hz * i) / SR)) + noise * rand();
  return out;
}
const yinOnly = (f: Float32Array, sr: number) => { const r = yin(f, sr); return r && r.clarity >= 0.8 ? r.hz : null; };

describe("lọc trầm", () => {
  it("giảm tiếng ù 50 Hz (> 6 dB), giữ nốt E2 82 Hz (mất < 6 dB) và A3 220 Hz", () => {
    const gain = (hz: number) => { const x = tone(hz, 0.1, 16384); const y = highpass(x, SR); return rms(y.subarray(8192)) / rms(x.subarray(8192)); };
    expect(20 * Math.log10(gain(50))).toBeLessThan(-6);
    expect(20 * Math.log10(gain(82.41))).toBeGreaterThan(-6);
    expect(20 * Math.log10(gain(220))).toBeGreaterThan(-0.5);
  });
});

describe("nền ồn", () => {
  it("chưa đủ 1 giây thì chưa tin nền; sau đó bám theo đáy, không bị nốt đàn to kéo lên", () => {
    const f = new NoiseFloor();
    for (let i = 0; i < 24; i += 1) expect(f.update(0.01)).toBe(0);
    for (let i = 0; i < 60; i += 1) f.update(0.01);
    expect(f.level).toBeCloseTo(0.01, 3);
    for (let i = 0; i < 50; i += 1) f.update(0.1);   // 2 giây một nốt to
    expect(f.level).toBeCloseTo(0.01, 3);
  });

  it("tụt ngay khi ồn giảm, nhưng không vượt trần tự đo", () => {
    const f = new NoiseFloor();
    for (let i = 0; i < 40; i += 1) f.update(0.05);
    expect(f.level).toBeCloseTo(AUTO_FLOOR_CAP, 5);
    for (let i = 0; i < 40; i += 1) f.update(0.004);
    expect(f.level).toBeLessThan(0.006);
  });

  it("đo nền (calibrate) nới trần lên theo phòng ồn thật", () => {
    const f = new NoiseFloor();
    f.calibrate(0.05);
    expect(f.level).toBeCloseTo(0.05, 3);
    for (let i = 0; i < 20; i += 1) f.update(0.06);
    expect(f.level).toBeCloseTo(0.05, 2);
  });
});

describe("bỏ phiếu 5/7", () => {
  const hz = 261.63;
  it("vẫn nhận nốt khi 2 khung bị nhiễu/bỏ trong 7 khung", () => {
    const s = new VoteStabilizer();
    const seq = [hz, hz, null, hz, 392, hz, hz];
    const got = seq.map((h) => s.push(h)).filter(Boolean);
    expect(got).toHaveLength(1);
    expect(Math.abs(got[0]!.hz - hz)).toBeLessThan(1);
  });
  it("không báo hai lần cho một nốt ngân; im lặng rồi đàn lại thì báo lại", () => {
    const s = new VoteStabilizer();
    let n = 0;
    for (let i = 0; i < 20; i += 1) if (s.push(hz)) n += 1;
    expect(n).toBe(1);
    for (let i = 0; i < 7; i += 1) s.push(null);
    for (let i = 0; i < 8; i += 1) if (s.push(hz)) n += 1;
    expect(n).toBe(2);
  });
  it("tiếng ồn chập chờn khác nhau (không khung nào trùng nốt quá 4 lần) không ra nốt", () => {
    const s = new VoteStabilizer();
    const noise = [200, null, 330, 150, null, 500, 200, 330, null, 150, 420, null, 200, 500];
    expect(noise.map((h) => s.push(h)).filter(Boolean)).toHaveLength(0);
  });
});

describe("đường xử lý", () => {
  const run = (cfg: typeof ROBUST, frames: Float32Array[]) => {
    const p = new MicPipeline(yinOnly, cfg);
    return frames.map((f) => p.push(f, SR)).filter((r) => r.note).map((r) => r.note!);
  };

  it("nghe ra một nốt C4 từ 10 khung đàn", () => {
    const notes = run(ROBUST, Array.from({ length: 10 }, () => tone(261.63)));
    expect(notes).toHaveLength(1);
  });

  it("ngưỡng thích nghi: sau 1 giây nền ồn đều bị bỏ qua (ngưỡng cũ thì vẫn ghi), nốt to hơn vẫn nghe được", () => {
    const hum = tone(110, 0.02);   // ù đều, to hơn ngưỡng im lặng cố định 0,005
    const old = new MicPipeline(yinOnly, LEGACY), now = new MicPipeline(yinOnly, ROBUST);
    let a, b;
    for (let i = 0; i < 40; i += 1) { a = old.push(hum, SR); b = now.push(hum, SR); }
    expect(a!.hz).not.toBeNull();
    expect(b!.hz).toBeNull();
    expect(b!.gate).toBeGreaterThan(b!.level);
    const notes = Array.from({ length: 10 }, () => now.push(tone(329.63, 0.15), SR)).filter((r) => r.note).map((r) => r.note!);
    expect(notes.filter((n) => Math.abs(n.hz - 329.63) < 5)).toHaveLength(1);
  });

  it("đo nền xong thì không nhận nốt trong lúc đo", async () => {
    const p = new MicPipeline(yinOnly, ROBUST);
    const done = p.calibrate(200);
    const outs = Array.from({ length: 6 }, () => p.push(tone(220, 0.01), SR));
    expect(outs.every((o) => o.note === null)).toBe(true);
    expect(await done).toBeCloseTo(rms(tone(220, 0.01)), 3);
    expect(p.calibrating).toBe(false);
  });
});

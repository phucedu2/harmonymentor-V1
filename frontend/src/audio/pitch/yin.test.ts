import { describe, expect, it } from "vitest";
import { NoteStabilizer, semitoneBucket } from "./stabilizer";
import { rms, yin } from "./yin";

const SR = 48000;
const cents = (a: number, b: number) => 1200 * Math.log2(a / b);

/** Sóng có các họa âm (giống dây đàn hơn sóng sin). amps[k] = biên độ họa âm k+1. */
function tone(hz: number, amps = [1], n = 2048, sr = SR, noise = 0, seed = 1): Float32Array {
  const out = new Float32Array(n);
  let s = seed;
  const rand = () => { s = (s * 16807) % 2147483647; return s / 2147483647 - 0.5; };
  for (let i = 0; i < n; i += 1) {
    let v = 0;
    amps.forEach((a, k) => { v += a * Math.sin(2 * Math.PI * hz * (k + 1) * i / sr); });
    out[i] = 0.3 * v + noise * rand();
  }
  return out;
}

describe("YIN", () => {
  it.each([82.41, 110, 196, 261.63, 329.63, 440, 659.25, 1046.5])("đo đúng sóng sin %s Hz trong ±5 cent", (hz) => {
    const r = yin(tone(hz), SR);
    expect(r).not.toBeNull();
    expect(Math.abs(cents(r!.hz, hz))).toBeLessThan(5);
  });

  it("họa âm 2 mạnh hơn âm gốc vẫn ra âm gốc, không nhảy lên quãng tám", () => {
    const r = yin(tone(196, [0.4, 1, 0.6, 0.3]), SR);
    expect(Math.abs(cents(r!.hz, 196))).toBeLessThan(10);
  });

  it("thiếu hẳn âm gốc (loa điện thoại nhỏ) vẫn nghe ra cao độ", () => {
    const r = yin(tone(110, [0, 1, 0.8, 0.6, 0.4]), SR);
    expect(Math.abs(cents(r!.hz, 110))).toBeLessThan(10);
  });

  it("chịu được nhiễu nhẹ", () => {
    const r = yin(tone(329.63, [1, 0.5, 0.3], 2048, SR, 0.05), SR);
    expect(Math.abs(cents(r!.hz, 329.63))).toBeLessThan(10);
  });

  it("tiếng ồn trắng không có cao độ thì trả null", () => {
    expect(yin(tone(1, [0], 2048, SR, 1), SR)).toBeNull();
  });

  it("chạy được ở 44,1 kHz", () => {
    const r = yin(tone(440, [1, 0.5], 2048, 44100), 44100);
    expect(Math.abs(cents(r!.hz, 440))).toBeLessThan(5);
  });

  it("rms của sóng sin biên độ 0,3 ≈ 0,212", () => {
    expect(rms(tone(440))).toBeCloseTo(0.3 / Math.SQRT2, 2);
  });
});

describe("NoteStabilizer", () => {
  it("chỉ báo một lần khi nốt giữ đủ 5 khung, lấy trung vị", () => {
    const s = new NoteStabilizer(5, 3);
    const seq = [330, 329, 331, 329.5, 330.2, 330, 330, 330];
    const out = seq.map((hz) => s.push(hz)).filter(Boolean);
    expect(out).toHaveLength(1);
    expect(out[0]!.hz).toBe(330);
  });

  it("đổi nốt thì báo nốt mới; cùng nốt chỉ báo lại sau khi ngắt tiếng", () => {
    const s = new NoteStabilizer(3, 2);
    const ev = (xs: (number | null)[]) => xs.map((hz) => s.push(hz)).filter(Boolean).length;
    expect(ev([262, 262, 262, 262])).toBe(1);
    expect(ev([330, 330, 330])).toBe(1);
    expect(ev([330, 330, 330])).toBe(0);
    expect(ev([null, null, 330, 330, 330])).toBe(1);
  });

  it("tiếng chập chờn (1 khung im) không làm đếm lại nốt", () => {
    const s = new NoteStabilizer(3, 3);
    const out = [440, 440, 440, null, 440, 440, 440].map((hz) => s.push(hz)).filter(Boolean);
    expect(out).toHaveLength(1);
  });

  it("nhóm theo nửa cung: 440 và 445 Hz cùng nhóm, 466 Hz khác nhóm", () => {
    expect(semitoneBucket(440)).toBe(semitoneBucket(445));
    expect(semitoneBucket(466.16)).toBe(semitoneBucket(440) + 1);
  });
});

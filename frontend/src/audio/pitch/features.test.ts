// So bản TypeScript với số Python xuất ra (train.py --fixture): cùng khung âm thanh thật → cùng đặc trưng,
// cùng nốt, cùng xác suất. Lệch là dấu hiệu hai bản tính khác nhau, model trên trình duyệt sẽ đoán sai.
import { describe, expect, it } from "vitest";
import modelJson from "../../../public/models/pitch_mlp.json";
import fixture from "./__fixtures__/parity.json";
import { fft, features, modelHz, N_FEATURES, parseModel, predictProba } from "./features";

const model = parseModel(modelJson);
const frameOf = (b64: string) => new Float32Array(Uint8Array.from(atob(b64), (c) => c.charCodeAt(0)).buffer);

describe("FFT", () => {
  it("sóng cos đúng tại ô 8 cho đỉnh ở ô 8 và ô n−8", () => {
    const n = 64, re = new Float64Array(n), im = new Float64Array(n);
    for (let i = 0; i < n; i += 1) re[i] = Math.cos((2 * Math.PI * 8 * i) / n);
    fft(re, im);
    expect(Math.hypot(re[8], im[8])).toBeCloseTo(n / 2, 6);
    expect(Math.hypot(re[3], im[3])).toBeLessThan(1e-9);
  });
});

describe("model nhận diện nốt khớp Python", () => {
  it("model có đúng 254 đặc trưng, lớp 0 = không có nốt, rồi 49 nốt (E2–E6)", () => {
    expect(model.mean.length).toBe(N_FEATURES);
    expect(model.classes.slice(0, 2)).toEqual([0, 40]);
    expect(model.classes).toHaveLength(50);
    expect(model.classes[model.classes.length - 1]).toBe(88);
  });

  it.each(fixture.items.map((it, i) => [i, it] as const))("khung %i: đặc trưng, nốt, xác suất, Hz giống Python", (_, item) => {
    const frame = frameOf(item.frame);
    const { x } = features(frame, fixture.sample_rate);
    item.features.forEach((v, i) => expect(Math.abs(x[i] - v)).toBeLessThan(1e-4));
    const p = predictProba(model, x);
    const k = p.indexOf(Math.max(...p));
    expect(model.classes[k]).toBe(item.top_class);
    expect(p[k]).toBeCloseTo(item.top_prob, 3);
    const r = modelHz(model, frame, fixture.sample_rate);
    if (item.top_prob >= model.abstain) expect(r!.hz).toBeCloseTo(item.hz, 1);
  });
});

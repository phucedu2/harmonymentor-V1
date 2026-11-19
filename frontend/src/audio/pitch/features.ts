// ADR-030 bước 2: đặc trưng + model MLP chạy ngay trên trình duyệt (âm thanh không rời máy).
// Giống hệt scripts/ai/pitch/dac_trung.py; test features.test.ts so với số do Python xuất (__fixtures__/parity.json).
// Model chỉ chọn "nốt nào" (một nửa cung); Hz chính xác lấy từ đáy đường YIN, rồi Music Engine đặt tên nốt.
import { cmndCurve, parabolicTau } from "./yin";

export const GRID_LO = 36, GRID_STEP = 1 / 3, N_GRID = 181;
export const SPEC_LO = 36, SPEC_HI = 108, N_SPEC = SPEC_HI - SPEC_LO + 1;
export const N_FEATURES = N_GRID + N_SPEC;

const midiToHz = (m: number) => 440 * 2 ** ((m - 69) / 12);

/** FFT phức cơ số 2 tại chỗ (Cooley–Tukey). n phải là lũy thừa của 2. */
export function fft(re: Float64Array, im: Float64Array): void {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i += 1) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (-2 * Math.PI) / len;
    for (let i = 0; i < n; i += len) {
      for (let k = 0; k < len / 2; k += 1) {
        const wr = Math.cos(ang * k), wi = Math.sin(ang * k);
        const ur = re[i + k], ui = im[i + k];
        const xr = re[i + k + len / 2], xi = im[i + k + len / 2];
        const vr = xr * wr - xi * wi, vi = xr * wi + xi * wr;
        re[i + k] = ur + vr; im[i + k] = ui + vi;
        re[i + k + len / 2] = ur - vr; im[i + k + len / 2] = ui - vi;
      }
    }
  }
}

export type Features = { x: Float64Array; cmnd: Float64Array };

/** 181 giá trị đường YIN trên lưới 1/3 nửa cung + 73 ô phổ theo nửa cung (log, chuẩn hóa về đỉnh = 1). */
export function features(frame: Float32Array, sr: number): Features {
  const taus = Array.from({ length: N_GRID }, (_, i) => sr / midiToHz(GRID_LO + GRID_STEP * i));
  const tauMax = Math.ceil(Math.max(...taus)) + 1;
  const cmnd = cmndCurve(frame, tauMax);
  const x = new Float64Array(N_FEATURES);
  taus.forEach((t, i) => {
    const lo = Math.floor(t), frac = t - lo;
    x[i] = Math.min(2, Math.max(0, cmnd[lo] * (1 - frac) + cmnd[lo + 1] * frac));
  });
  const n = frame.length;
  const re = new Float64Array(n), im = new Float64Array(n);
  for (let i = 0; i < n; i += 1) re[i] = frame[i] * (0.5 - 0.5 * Math.cos((2 * Math.PI * i) / n));
  fft(re, im);
  const binHz = sr / n;
  let peak = 0;
  for (let k = 0; k < N_SPEC; k += 1) {
    const m = SPEC_LO + k;
    const lo = Math.floor(midiToHz(m - 0.5) / binHz), hi = Math.ceil(midiToHz(m + 0.5) / binHz);
    let best = 0;
    for (let b = lo; b <= hi && b <= n / 2; b += 1) best = Math.max(best, Math.hypot(re[b], im[b]));
    x[N_GRID + k] = Math.log1p(best);
    peak = Math.max(peak, x[N_GRID + k]);
  }
  for (let k = 0; k < N_SPEC; k += 1) x[N_GRID + k] /= peak + 1e-9;
  return { x, cmnd };
}

/** Hz chính xác ở đáy d' trong ±0,5 nửa cung quanh nốt model chọn, giữ trong nốt đó. */
export function refineHz(cmnd: Float64Array, sr: number, midi: number): number {
  const tLo = Math.floor(sr / midiToHz(midi + 0.5));
  const tHi = Math.min(cmnd.length - 2, Math.ceil(sr / midiToHz(midi - 0.5)));
  let t = tLo;
  for (let k = tLo; k <= tHi; k += 1) if (cmnd[k] < cmnd[t]) t = k;
  t = Math.max(1, t);
  const hz = sr / parabolicTau(cmnd, t);
  return Math.min(midiToHz(midi + 0.49), Math.max(midiToHz(midi - 0.49), hz));
}

type Layer = { in: number; out: number; W: Float32Array; b: Float32Array };
export type PitchModel = { classes: number[]; abstain: number; mean: Float32Array; scale: Float32Array; layers: Layer[] };

type ModelJson = { version: number; n_features: number; classes: number[]; abstain: number; activation: string;
  mean: string; scale: string; layers: { in: number; out: number; W: string; b: string }[] };

function f32(b64: string): Float32Array {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i += 1) bytes[i] = bin.charCodeAt(i);
  return new Float32Array(bytes.buffer);
}

export function parseModel(json: ModelJson): PitchModel {
  if (json.version !== 1 || json.n_features !== N_FEATURES || json.activation !== "relu") throw new Error("pitch model không khớp phiên bản");
  return { classes: json.classes, abstain: json.abstain, mean: f32(json.mean), scale: f32(json.scale),
    layers: json.layers.map((l) => ({ in: l.in, out: l.out, W: f32(l.W), b: f32(l.b) })) };
}

/** Lan truyền xuôi: chuẩn hóa → (W·x + b, ReLU) ở lớp ẩn → softmax ở lớp ra. Trả xác suất từng nốt. */
export function predictProba(model: PitchModel, feat: Float64Array): Float64Array {
  let h = new Float64Array(feat.length);
  for (let i = 0; i < feat.length; i += 1) h[i] = (feat[i] - model.mean[i]) / model.scale[i];
  model.layers.forEach((layer, li) => {
    const out = new Float64Array(layer.out);
    for (let o = 0; o < layer.out; o += 1) out[o] = layer.b[o];
    for (let i = 0; i < layer.in; i += 1) {
      const v = h[i];
      if (v === 0) continue;
      const row = i * layer.out;
      for (let o = 0; o < layer.out; o += 1) out[o] += v * layer.W[row + o];
    }
    if (li < model.layers.length - 1) for (let o = 0; o < layer.out; o += 1) out[o] = Math.max(0, out[o]);
    h = out;
  });
  const mx = Math.max(...h);
  let sum = 0;
  for (let o = 0; o < h.length; o += 1) { h[o] = Math.exp(h[o] - mx); sum += h[o]; }
  for (let o = 0; o < h.length; o += 1) h[o] /= sum;
  return h;
}

/** Model đoán Hz, hoặc null khi không có nốt / không chắc (xác suất cao nhất < ngưỡng). */
export function modelHz(model: PitchModel, frame: Float32Array, sr: number): { hz: number; midi: number; prob: number } | null {
  const { x, cmnd } = features(frame, sr);
  const p = predictProba(model, x);
  let k = 0;
  for (let i = 1; i < p.length; i += 1) if (p[i] > p[k]) k = i;
  const midi = model.classes[k];
  // Lớp 0 = "không có nốt" (ù điện, tiếng ồn): model học cách im lặng thay vì đoán bừa.
  if (p[k] < model.abstain || midi === 0) return null;
  return { hz: refineHz(cmnd, sr, midi), midi, prob: p[k] };
}

let loading: Promise<PitchModel> | null = null;
/** Nạp model lười (~210 KB) chỉ khi người học bật micro. */
export function loadPitchModel(url = "/models/pitch_mlp.json"): Promise<PitchModel> {
  loading ??= fetch(url).then((r) => {
    if (!r.ok) throw new Error(`pitch model ${r.status}`);
    return r.json() as Promise<ModelJson>;
  }).then(parseModel).catch((e) => { loading = null; throw e; });
  return loading;
}

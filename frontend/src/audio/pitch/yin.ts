// ADR-031: thuật toán YIN (de Cheveigné & Kawahara, 2002) tìm tần số cơ bản của MỘT nốt từ một khung âm thanh.
// Chỉ đo tần số (Hz). Tên nốt luôn do Music Engine đặt (GET /engine/note-from-frequency), frontend không tự tính.
// Bản Python giống hệt ở scripts/ai/pitch/dac_trung.py để so với model ở bước 2; sửa một bên thì sửa cả hai.

export type YinOptions = { minHz?: number; maxHz?: number; threshold?: number };
export type YinResult = { hz: number; clarity: number };

export const YIN_DEFAULTS = { minHz: 70, maxHz: 1500, threshold: 0.15 } as const;

/** Năng lượng trung bình (RMS). Dưới ngưỡng coi là im lặng, khỏi đo để tránh bắt nhầm tiếng ồn. */
export function rms(frame: Float32Array): number {
  let sum = 0;
  for (let i = 0; i < frame.length; i += 1) sum += frame[i] * frame[i];
  return Math.sqrt(sum / Math.max(1, frame.length));
}

/** d'(τ) cho τ = 0..tauMax+1 (bước 1 + 2 của YIN). Model ở bước 2 cũng đọc đường cong này (features.ts). */
export function cmndCurve(frame: Float32Array, tauMax: number): Float64Array {
  const w = Math.floor(frame.length / 2);
  const d = new Float64Array(tauMax + 2);
  for (let tau = 1; tau <= tauMax + 1; tau += 1) {
    let sum = 0;
    for (let j = 0; j < w; j += 1) { const diff = frame[j] - frame[j + tau]; sum += diff * diff; }
    d[tau] = sum;
  }
  const cmnd = new Float64Array(tauMax + 2);
  cmnd[0] = 1;
  let running = 0;
  for (let tau = 1; tau <= tauMax + 1; tau += 1) {
    running += d[tau];
    cmnd[tau] = running > 0 ? (d[tau] * tau) / running : 1;
  }
  return cmnd;
}

/** Nội suy parabol quanh đáy τ để ra τ lẻ (chính xác hơn 1 mẫu). */
export function parabolicTau(cmnd: Float64Array, tau: number): number {
  const a = cmnd[tau - 1], b = cmnd[tau], c = cmnd[tau + 1];
  const denom = a - 2 * b + c;
  const shift = denom > 0 ? (a - c) / (2 * denom) : 0;
  return tau + Math.max(-1, Math.min(1, shift));
}

/**
 * Trả tần số cơ bản và độ rõ (0..1), hoặc null nếu khung không có cao độ rõ.
 * Bước 1: hàm sai khác d(τ) = Σ (x[j] − x[j+τ])². Sóng lặp lại sau τ mẫu thì d(τ) ≈ 0.
 * Bước 2: chuẩn hóa tích lũy d'(τ), để d' không nhỏ dần theo τ (lỗi bắt nhầm quãng tám thấp).
 * Bước 3: lấy τ đầu tiên có d' < ngưỡng rồi trượt tới đáy, nội suy parabol cho τ lẻ, f0 = sampleRate / τ.
 */
export function yin(frame: Float32Array, sampleRate: number, opts: YinOptions = {}): YinResult | null {
  const { minHz, maxHz, threshold } = { ...YIN_DEFAULTS, ...opts };
  const w = Math.floor(frame.length / 2);
  const tauMin = Math.max(2, Math.floor(sampleRate / maxHz));
  const tauMax = Math.min(w - 1, Math.ceil(sampleRate / minHz));
  if (tauMax <= tauMin + 1) return null;
  const cmnd = cmndCurve(frame, tauMax);
  let tau = -1;
  for (let t = tauMin; t <= tauMax; t += 1) {
    if (cmnd[t] < threshold) {
      while (t + 1 <= tauMax && cmnd[t + 1] < cmnd[t]) t += 1;
      tau = t;
      break;
    }
  }
  if (tau < 0) return null;
  return { hz: sampleRate / parabolicTau(cmnd, tau), clarity: Math.max(0, Math.min(1, 1 - cmnd[tau])) };
}

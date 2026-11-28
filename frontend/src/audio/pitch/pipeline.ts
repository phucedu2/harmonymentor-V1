// ADR-039: đường xử lý nghe nốt có chống tạp âm. Một chỗ duy nhất cho cả trình duyệt (micListener) lẫn bộ đo
// (frontend/scripts/danh_gia_micro.ts), để số đo là của chính đoạn code người học chạy.
// Các bước: lọc trầm (HPF) → ngưỡng thích nghi theo "nền ồn" → nhận diện (YIN/model) → bỏ phiếu 5/7 khung.
import { rms } from "./yin";
import type { PitchDetector } from "./micListener";
import type { StableNote } from "./stabilizer";
import { NoteStabilizer, semitoneBucket } from "./stabilizer";

/** Dưới mức này (≈ −46 dBFS) coi là im lặng, dù nền ồn thấp đến đâu. */
export const SILENCE_RMS = 0.005;
export const TICK_MS = 40;

// ---- Lọc trầm -------------------------------------------------------------------------------------------------
/** Tần số cắt: dưới E2 (82 Hz) nên không cắt nốt đàn, nhưng bỏ tiếng ù điện 50/60 Hz và rung bàn/quạt. */
export const HPF_HZ = 70;
export const HPF_STAGES = 2;
/** Q của BiquadFilterNode tính bằng dB: −3,01 dB = Butterworth (Q = 1/√2). */
export const HPF_Q_DB = 20 * Math.log10(Math.SQRT1_2);

/** Cùng công thức RBJ mà BiquadFilterNode(highpass) dùng; để bộ đo lọc giống hệt trình duyệt. */
export function highpass(x: Float32Array, sr: number, hz = HPF_HZ, stages = HPF_STAGES): Float32Array {
  const w0 = (2 * Math.PI * hz) / sr, c = Math.cos(w0), alpha = Math.sin(w0) / (2 * Math.SQRT1_2);
  const a0 = 1 + alpha;
  const b0 = (1 + c) / 2 / a0, b1 = -(1 + c) / a0, b2 = b0, a1 = (-2 * c) / a0, a2 = (1 - alpha) / a0;
  let cur = x;
  for (let s = 0; s < stages; s += 1) {
    const y = new Float32Array(cur.length);
    let x1 = 0, x2 = 0, y1 = 0, y2 = 0;
    for (let i = 0; i < cur.length; i += 1) {
      const v = b0 * cur[i] + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2;
      x2 = x1; x1 = cur[i]; y2 = y1; y1 = v; y[i] = v;
    }
    cur = y;
  }
  return cur;
}

// ---- Nền ồn ---------------------------------------------------------------------------------------------------
/** Cửa sổ tìm đáy: 5 giây. Người học đàn từng nốt có quãng nghỉ, nên trong 5 giây luôn có lúc chỉ còn tiếng ồn. */
const FLOOR_WINDOW = 125;
/** Chưa đủ 1 giây dữ liệu thì chưa tin nền (lúc vừa bật micro có thể đang ngân sẵn một nốt). */
const FLOOR_MIN_TICKS = 25;
/** Nền tự đo không vượt mức này (≈ −34 dBFS): tránh ngưỡng nuốt luôn nốt đàn. Muốn cao hơn phải bấm "Đo nền". */
export const AUTO_FLOOR_CAP = 0.02;

/** Ước lượng mức ồn nền bằng "thống kê cực tiểu": đáy của mức RMS đã làm mượt trong 5 giây gần nhất. */
export class NoiseFloor {
  level = 0;
  private smooth: number | null = null;
  private ring: number[] = [];
  private cap = AUTO_FLOOR_CAP;

  update(level: number): number {
    this.smooth = this.smooth === null ? level : this.smooth + (level - this.smooth) * 0.3;
    this.ring.push(this.smooth);
    if (this.ring.length > FLOOR_WINDOW) this.ring.shift();
    if (this.ring.length < FLOOR_MIN_TICKS) { this.level = 0; return 0; }
    this.level = Math.min(Math.min(...this.ring), this.cap);
    return this.level;
  }

  /** Nút "Đo nền": người học giữ im lặng 1–2 giây; lấy trung vị làm đáy cho 5 giây tới và nới trần theo mức đó. */
  calibrate(medianLevel: number) {
    this.cap = Math.max(AUTO_FLOOR_CAP, medianLevel * 1.2);
    this.smooth = medianLevel;
    this.ring = new Array(FLOOR_WINDOW).fill(medianLevel);
    this.level = Math.min(medianLevel, this.cap);
  }
}

// ---- Bỏ phiếu -------------------------------------------------------------------------------------------------
/** Giống NoteStabilizer nhưng chịu được khung nhiễu lẻ tẻ: trong 7 khung gần nhất có ≥ `need` khung cùng một nốt là tính. */
export class VoteStabilizer {
  private win: (number | null)[] = [];
  private hzs: (number | null)[] = [];
  private current: number | null = null;   // nửa cung đã báo, chưa nhả

  constructor(private size = 7, private need = 5, private release = 2) {}

  reset() { this.win = []; this.hzs = []; this.current = null; }

  push(hz: number | null): StableNote | null {
    this.win.push(hz === null ? null : semitoneBucket(hz));
    this.hzs.push(hz);
    if (this.win.length > this.size) { this.win.shift(); this.hzs.shift(); }
    const counts = new Map<number, number>();
    for (const b of this.win) if (b !== null) counts.set(b, (counts.get(b) ?? 0) + 1);
    let best: number | null = null, bestN = 0;
    for (const [b, n] of counts) if (n > bestN) { best = b; bestN = n; }
    if (this.current !== null) {
      // Nhả khi nốt đang giữ chỉ còn ≤ `release` phiếu trong cửa sổ: im lặng hoặc đổi nốt.
      if ((counts.get(this.current) ?? 0) <= this.release) this.current = null;
      else return null;
    }
    if (best === null || bestN < this.need) return null;
    this.current = best;
    const same = this.hzs.filter((h, i) => h !== null && this.win[i] === best) as number[];
    same.sort((a, b) => a - b);
    return { hz: same[Math.floor(same.length / 2)], frames: bestN };
  }
}

// ---- Đường xử lý -----------------------------------------------------------------------------------------------
export type PipelineConfig = {
  /** Lọc trầm trước khi phân tích. */
  hpf: boolean;
  /** Ngưỡng im lặng thích nghi theo nền ồn. */
  adaptiveGate: boolean;
  /** Ngưỡng = nền ồn × hệ số này (≈ +4 dB). Thấp hơn thì nhạy hơn nhưng dễ nhận tạp âm. */
  gateRatio: number;
  /** Bỏ phiếu 5/7 thay cho "5 khung liên tiếp". */
  vote: boolean;
};
/** Hành vi trước ADR-039 (ADR-032): để so trước/sau cùng một bộ đo. */
export const LEGACY: PipelineConfig = { hpf: false, adaptiveGate: false, gateRatio: 1, vote: false };
export const ROBUST: PipelineConfig = { hpf: true, adaptiveGate: true, gateRatio: 1.6, vote: true };

export type PipelineFrame = { level: number; floor: number; gate: number; hz: number | null; note: StableNote | null };

export class MicPipeline {
  readonly floor = new NoiseFloor();
  private stab: NoteStabilizer | VoteStabilizer;
  private calib: number[] | null = null;
  private calibNeed = 0;
  private calibDone: ((median: number) => void) | null = null;

  constructor(private detect: PitchDetector, private cfg: PipelineConfig = ROBUST) {
    this.stab = cfg.vote ? new VoteStabilizer() : new NoteStabilizer();
  }

  /** Đo nền trong `ms` mili-giây (các khung trong lúc đo không nhận nốt). Trả mức nền (trung vị). */
  calibrate(ms = 1500): Promise<number> {
    return new Promise((resolve) => {
      this.calib = [];
      this.calibNeed = Math.max(5, Math.round(ms / TICK_MS));
      this.calibDone = resolve;
    });
  }

  get calibrating() { return this.calib !== null; }

  push(frame: Float32Array, sr: number): PipelineFrame {
    const level = rms(frame);
    if (this.calib) {
      this.calib.push(level);
      if (this.calib.length >= this.calibNeed) {
        const s = [...this.calib].sort((a, b) => a - b);
        const med = s[Math.floor(s.length / 2)];
        this.floor.calibrate(med);
        const done = this.calibDone;
        this.calib = null; this.calibDone = null;
        done?.(med);
      }
      return { level, floor: this.floor.level, gate: SILENCE_RMS, hz: null, note: null };
    }
    const floor = this.cfg.adaptiveGate ? this.floor.update(level) : 0;
    const gate = Math.max(SILENCE_RMS, floor * this.cfg.gateRatio);
    const hz = level >= gate ? this.detect(frame, sr) : null;
    return { level, floor, gate, hz, note: this.stab.push(hz) };
  }
}

// ADR-032: nghe micro trên trình duyệt. Âm thanh chỉ xử lý trong máy người học, không ghi âm, không gửi đi;
// mỗi nốt ổn định chỉ gửi MỘT con số (Hz) cho Music Engine đặt tên.
import { modelHz, type PitchModel } from "./features";
import type { StableNote } from "./stabilizer";
import { HPF_HZ, HPF_Q_DB, HPF_STAGES, LEGACY, MicPipeline, ROBUST, SILENCE_RMS, TICK_MS, type PipelineConfig } from "./pipeline";
import { yin } from "./yin";

export type PitchDetector = (frame: Float32Array, sampleRate: number) => number | null;
export type MicFrame = { level: number; hz: number | null; floor: number; gate: number };
export type MicError = "unsupported" | "denied" | "no-device" | "failed";

export { SILENCE_RMS };
const FRAME = 2048;

export const yinDetector: PitchDetector = (frame, sr) => {
  const r = yin(frame, sr);
  return r && r.clarity >= 0.8 ? r.hz : null;
};

export type DetectorKind = "hybrid" | "yin" | "model";
export const DETECTOR_LABEL: Record<DetectorKind, string> = {
  model: "Model AI chống tạp âm (khuyên dùng)", hybrid: "Kết hợp YIN + model AI (ít sót nốt khi phòng yên)", yin: "Chỉ thuật toán YIN",
};

/** Bước 2: model MLP. Kết hợp = dùng YIN khi YIN chắc chắn (rất chính xác), YIN bỏ qua thì hỏi model
 *  (model chịu nhiễu và tiếng ù tốt hơn). Số đo: docs/giai-doan/nhan-dien-not-micro/KET_QUA_MODEL.md. */
export function makeDetector(kind: DetectorKind, model: PitchModel | null): PitchDetector {
  if (kind === "yin" || !model) return yinDetector;
  const byModel: PitchDetector = (frame, sr) => modelHz(model, frame, sr)?.hz ?? null;
  if (kind === "model") return byModel;
  return (frame, sr) => yinDetector(frame, sr) ?? byModel(frame, sr);
}

export function micSupported(): boolean {
  return typeof navigator !== "undefined" && Boolean(navigator.mediaDevices?.getUserMedia) && typeof AudioContext !== "undefined";
}

export function classifyMicError(e: unknown): MicError {
  const name = (e as { name?: string })?.name;
  if (name === "NotAllowedError" || name === "SecurityError") return "denied";
  if (name === "NotFoundError" || name === "OverconstrainedError") return "no-device";
  return "failed";
}

export type MicSession = {
  stop: () => void; sampleRate: number;
  /** Đo nền ồn: người học giữ im lặng; trả mức RMS nền (trung vị). */
  calibrate: (ms?: number) => Promise<number>;
};

/** Mở micro và gọi onFrame mỗi 40 ms, onNote khi một nốt giữ đủ lâu. `pipeline` = LEGACY để so với ADR-032. */
export async function startMic(opts: {
  detector?: PitchDetector;
  pipeline?: PipelineConfig;
  onFrame?: (f: MicFrame) => void;
  onNote: (n: StableNote) => void;
}): Promise<MicSession> {
  if (!micSupported()) throw Object.assign(new Error("unsupported"), { name: "Unsupported" });
  // Tắt khử vọng/khử ồn/tự chỉnh âm lượng của trình duyệt: các bộ lọc này làm méo cao độ nốt đàn (ADR-039 có số đo).
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false },
  });
  const ctx = new AudioContext();
  const source = ctx.createMediaStreamSource(stream);
  const cfg = opts.pipeline ?? ROBUST;
  // Lọc trầm giống hệt pipeline.highpass() dùng trong bộ đo: 2 tầng Butterworth 70 Hz.
  let tail: AudioNode = source;
  const filters: BiquadFilterNode[] = [];
  if (cfg.hpf) {
    for (let i = 0; i < HPF_STAGES; i += 1) {
      const f = ctx.createBiquadFilter();
      f.type = "highpass"; f.frequency.value = HPF_HZ; f.Q.value = HPF_Q_DB;
      tail.connect(f); tail = f; filters.push(f);
    }
  }
  const analyser = ctx.createAnalyser();
  analyser.fftSize = FRAME;
  tail.connect(analyser);
  const buf = new Float32Array(FRAME);
  const pipe = new MicPipeline(opts.detector ?? yinDetector, cfg);
  const timer = window.setInterval(() => {
    analyser.getFloatTimeDomainData(buf);
    const r = pipe.push(buf, ctx.sampleRate);
    opts.onFrame?.({ level: r.level, hz: r.hz, floor: r.floor, gate: r.gate });
    if (r.note) opts.onNote(r.note);
  }, TICK_MS);
  return {
    sampleRate: ctx.sampleRate,
    calibrate: (ms) => pipe.calibrate(ms),
    stop: () => {
      window.clearInterval(timer);
      source.disconnect();
      filters.forEach((f) => f.disconnect());
      stream.getTracks().forEach((t) => t.stop());
      void ctx.close();
    },
  };
}

export { LEGACY, ROBUST };

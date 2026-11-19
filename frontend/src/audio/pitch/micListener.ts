// ADR-030: nghe micro trên trình duyệt. Âm thanh chỉ xử lý trong máy người học, không ghi âm, không gửi đi;
// mỗi nốt ổn định chỉ gửi MỘT con số (Hz) cho Music Engine đặt tên.
import { NoteStabilizer, type StableNote } from "./stabilizer";
import { rms, yin } from "./yin";

export type PitchDetector = (frame: Float32Array, sampleRate: number) => number | null;
export type MicFrame = { level: number; hz: number | null };
export type MicError = "unsupported" | "denied" | "no-device" | "failed";

/** Dưới mức này (≈ −46 dBFS) coi là im lặng. */
export const SILENCE_RMS = 0.005;
const FRAME = 2048;
const TICK_MS = 40;

export const yinDetector: PitchDetector = (frame, sr) => {
  const r = yin(frame, sr);
  return r && r.clarity >= 0.8 ? r.hz : null;
};

export function micSupported(): boolean {
  return typeof navigator !== "undefined" && Boolean(navigator.mediaDevices?.getUserMedia) && typeof AudioContext !== "undefined";
}

export function classifyMicError(e: unknown): MicError {
  const name = (e as { name?: string })?.name;
  if (name === "NotAllowedError" || name === "SecurityError") return "denied";
  if (name === "NotFoundError" || name === "OverconstrainedError") return "no-device";
  return "failed";
}

export type MicSession = { stop: () => void; sampleRate: number };

/** Mở micro và gọi onFrame mỗi 40 ms, onNote khi một nốt giữ đủ lâu. */
export async function startMic(opts: {
  detector?: PitchDetector;
  onFrame?: (f: MicFrame) => void;
  onNote: (n: StableNote) => void;
}): Promise<MicSession> {
  if (!micSupported()) throw Object.assign(new Error("unsupported"), { name: "Unsupported" });
  // Tắt khử vọng/khử ồn/tự chỉnh âm lượng: các bộ lọc này làm méo cao độ của nhạc cụ.
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false },
  });
  const ctx = new AudioContext();
  const source = ctx.createMediaStreamSource(stream);
  const analyser = ctx.createAnalyser();
  analyser.fftSize = FRAME;
  source.connect(analyser);
  const buf = new Float32Array(FRAME);
  const stab = new NoteStabilizer();
  const detect = opts.detector ?? yinDetector;
  const timer = window.setInterval(() => {
    analyser.getFloatTimeDomainData(buf);
    const level = rms(buf);
    const hz = level >= SILENCE_RMS ? detect(buf, ctx.sampleRate) : null;
    opts.onFrame?.({ level, hz });
    const note = stab.push(hz);
    if (note) opts.onNote(note);
  }, TICK_MS);
  return {
    sampleRate: ctx.sampleRate,
    stop: () => {
      window.clearInterval(timer);
      source.disconnect();
      stream.getTracks().forEach((t) => t.stop());
      void ctx.close();
    },
  };
}

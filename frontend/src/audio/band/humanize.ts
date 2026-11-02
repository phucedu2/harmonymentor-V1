// Lệch phách người (humanize) cho bản phối: thuần (không Tone.js) để test bằng Vitest, có seed để nghe lại y hệt.
//
// Vì sao cần: máy đánh đúng tuyệt đối từng mili-giây và cùng một lực nên nghe "như máy". Người chơi thật:
// - lệch thời gian một chút quanh phách (phân phối chuẩn, σ vài ms), và có "pocket" theo phong cách
//   (lo-fi: snare trễ 20–30 ms; jazz: ride hơi đẩy trước);
// - đánh phách mạnh to hơn phách yếu, lực đổi nhẹ từng nhát (±8%);
// - không bấm cả hợp âm cùng lúc: piano rải 5–25 ms từ trầm lên, guitar quạt xuống thì dây trầm trước,
//   quạt lên thì dây cao trước và nhẹ hơn.
import type { Arrangement, BandChannel, NoteEvent, PlayHit } from "./types";

export const MAX_OFFSET_SEC = 0.03; // không lệch quá ±30 ms (pocket + nhiễu), để không thành "đánh sai nhịp"

/** PRNG mulberry32: nhanh, có seed, cùng seed → cùng dãy số trên mọi trình duyệt. */
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Số ngẫu nhiên phân phối chuẩn (Box–Muller). */
export function gaussian(rand: () => number): number {
  const u = Math.max(rand(), 1e-12);
  const v = rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

const clamp = (x: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, x));

/** Swing theo tỷ lệ cặp nốt: với "8n", nốt móc đơn thứ hai của mỗi phách dời từ 0,5 tới `ratio`. */
export function swingBeat(beat: number, ratio: number, sub: "8n" | "16n"): number {
  if (!ratio || ratio === 0.5) return beat;
  const unit = sub === "8n" ? 1 : 0.5; // độ dài một cặp nốt (phách)
  const base = Math.floor(beat / unit + 1e-9) * unit;
  const pos = (beat - base) / unit; // 0..1 trong cặp
  if (Math.abs(pos - 0.5) < 1e-6) return base + ratio * unit;
  return beat;
}

const HAT_PIECES = new Set(["hh_c", "hh_o", "hh_p", "br_hh", "shaker", "tamb"]);
const RIDE_PIECES = new Set(["ride", "ride_b", "br_ride"]);
const PERC = new Set(["conga_h", "conga_l", "shaker", "tamb", "tri", "clap"]);

function drumPocket(piece: string, pocket: Arrangement["feel"]["pocket_ms"]): number {
  if (piece === "kick") return pocket.kick ?? 0;
  if (["snare", "rim", "xstick", "br_snare", "clap"].includes(piece)) return pocket.snare ?? 0;
  if (RIDE_PIECES.has(piece)) return pocket.ride ?? pocket.hat ?? 0;
  if (HAT_PIECES.has(piece)) return pocket.hat ?? 0;
  return 0;
}

/** Phách mạnh to hơn: phách 1 > phách 3 > phách 2, 4 > nốt lệch phách. */
function accent(beat: number): number {
  const inBar = ((beat % 4) + 4) % 4;
  if (Math.abs(inBar) < 1e-6) return 1.0;
  if (Math.abs(inBar - 2) < 1e-6) return 0.95;
  if (Math.abs(inBar - Math.round(inBar)) < 1e-6) return 0.9;
  return 0.84;
}

const KEY_INST: Record<string, string> = { piano: "piano", epiano: "epiano", clav: "clav" };

export type HumanizeOptions = { seed: number; bpm: number; lite?: boolean };

/**
 * Biến bản phối (phách, nốt, lực 1–127) thành danh sách nhát phát có lệch người.
 * Cùng (bản phối, seed, bpm) → cùng kết quả.
 */
export function humanize(arr: Arrangement, opts: HumanizeOptions): PlayHit[] {
  const rand = rng(opts.seed * 7919 + 17);
  const feel = arr.feel;
  const secPerBeat = 60 / opts.bpm;
  const hits: PlayHit[] = [];
  const timing = (sigmaMs: number, pocketMs: number) =>
    clamp((pocketMs + gaussian(rand) * sigmaMs) / 1000, -MAX_OFFSET_SEC, MAX_OFFSET_SEC);
  const velocity = (vel: number, beat: number, spread = 0.08) =>
    clamp((vel / 127) * accent(beat) * (1 + (rand() * 2 - 1) * spread), 0.04, 1);
  const swung = (beat: number) => swingBeat(beat, feel.swing, feel.swing_sub);

  // Trống: mỗi nhát lệch riêng; hat/ride có nhấn theo phách; ghost note giữ nhỏ.
  for (const e of arr.tracks.drums.events) {
    const piece = e.drum;
    const isPerc = PERC.has(piece);
    hits.push({
      channel: "drums", instrument: isPerc ? "perc" : "drums", beat: swung(e.beat),
      offset: timing(feel.sigma_ms.drums * (isPerc ? 1.3 : 1), drumPocket(piece, feel.pocket_ms)),
      dur: 1, midi: null, piece, vel: velocity(e.vel, e.beat, e.vel < 45 ? 0.15 : 0.08), art: "hit",
    });
  }

  // Phím: rải hợp âm từ trầm lên (tay người không bấm cùng lúc); tay trái giữ nhịp chặt hơn.
  const keysInst = KEY_INST[arr.tracks.keys.instrument] ?? "piano";
  for (const e of arr.tracks.keys.events) {
    const base = timing(feel.sigma_ms.keys, feel.pocket_ms.keys ?? 0);
    const [rollLo, rollHi] = feel.roll_ms;
    const rollMs = e.art === "roll" ? rollHi * 1.6 : rollLo + rand() * (rollHi - rollLo);
    const notes = [...e.midi].sort((a, b) => a - b);
    notes.forEach((m, i) => {
      const spread = e.art === "lh" ? 0 : (i * rollMs) / Math.max(notes.length - 1, 1) / 1000;
      hits.push({
        channel: "chords", instrument: keysInst, beat: swung(e.beat), offset: clamp(base + spread * (e.art === "roll" ? 1 : 0.5), -MAX_OFFSET_SEC, 0.08),
        // Ngân: piano có pedal giữ tới khi đổi hợp âm, nên độ dài thay đổi nhẹ quanh giá trị nốt.
        dur: e.dur * (0.92 + rand() * 0.1), midi: m, piece: null,
        vel: velocity(e.vel * (i === notes.length - 1 ? 1.06 : 0.96), e.beat), art: e.art,
      });
    });
  }

  // Bass: lệch nhẹ, để hở một chút trước nốt sau (người chơi nhấc ngón), nốt chết rất ngắn.
  const bassInst = arr.tracks.bass.instrument;
  for (const e of arr.tracks.bass.events) {
    hits.push({
      channel: "bass", instrument: bassInst, beat: swung(e.beat),
      offset: timing(feel.sigma_ms.bass, feel.pocket_ms.bass ?? 0),
      dur: e.art === "dead" ? 0.08 : Math.max(0.1, e.dur * (0.86 + rand() * 0.08)), midi: e.midi[0], piece: null,
      vel: velocity(e.vel, e.beat, 0.07), art: e.art,
    });
  }

  // Guitar: quạt xuống trầm → cao, quạt lên cao → trầm và nhẹ hơn; mỗi dây cách 8–20 ms tùy tốc độ quạt.
  for (const e of arr.tracks.guitar.events) {
    const base = timing(feel.sigma_ms.guitar, feel.pocket_ms.guitar ?? 0);
    const [sLo, sHi] = feel.strum_ms;
    const gap = (sLo + rand() * (sHi - sLo)) / 1000;
    const up = e.art === "up";
    const notes = [...e.midi].sort((a, b) => (up ? b - a : a - b));
    const muted = e.art === "mute" || e.art === "palm";
    notes.forEach((m, i) => {
      hits.push({
        channel: "guitar", instrument: muted ? "guitar_mute" : "guitar", beat: swung(e.beat),
        offset: clamp(base + (e.art === "pick" ? 0 : i * gap), -MAX_OFFSET_SEC, 0.12),
        dur: muted ? Math.min(e.dur, 0.2) : e.dur * (0.9 + rand() * 0.1), midi: m, piece: null,
        vel: velocity(e.vel * (up ? 0.82 : 1) * (1 - i * 0.03), e.beat), art: e.art,
      });
    });
  }
  // Hook nhạc cụ (chế độ Bài hát): câu ngắn tầm cao, lệch nhẹ như tay phải người chơi; kênh riêng "Hook".
  for (const e of arr.tracks.hook?.events ?? []) {
    hits.push({
      channel: "hook", instrument: "hook", beat: swung(e.beat),
      offset: timing(feel.sigma_ms.keys, feel.pocket_ms.keys ?? 0),
      dur: e.dur * (0.9 + rand() * 0.08), midi: e.midi[0], piece: null, vel: velocity(e.vel, e.beat, 0.06), art: e.art,
    });
  }
  return hits.sort((a, b) => a.beat - b.beat || a.offset - b.offset);
}

/** Độ lệch của "nhát đầu" mỗi sự kiện (không tính phần rải/quạt có chủ ý) — để test giới hạn ±30 ms. */
export function onsetOffsets(hits: PlayHit[], channel: BandChannel): number[] {
  const seen = new Map<string, number>();
  for (const h of hits) {
    if (h.channel !== channel) continue;
    const k = `${h.beat}`;
    const prev = seen.get(k);
    if (prev === undefined || h.offset < prev) seen.set(k, h.offset);
  }
  return [...seen.values()];
}

export type { NoteEvent };

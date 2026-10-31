// Lịch phát của Harmony Lab (phuc-music Bước 4), tách khỏi Tone.js để test được bằng Vitest.
// Tính theo phách; cao độ lấy từ API voicings (Music Engine), file này không tự tính nốt.
import type { ComposeStyle, ComposeVoicing } from "../api";

export type Channel = "chords" | "bass" | "drums";
export type TrackEvent =
  | { channel: "chords"; beat: number; beats: number; midi: number[] }
  | { channel: "bass"; beat: number; beats: number; midi: number[] }
  | { channel: "drums"; beat: number; drum: "kick" | "snare" | "hat"; velocity: number };

export const BEATS_PER_BAR = 4;

/** Lịch phát cho cả lưới: ô trống thì không có hợp âm và bass, trống vẫn chạy để giữ nhịp. */
export function buildSchedule(bars: (ComposeVoicing | null)[], style: ComposeStyle): TrackEvent[] {
  const events: TrackEvent[] = [];
  bars.forEach((voicing, bar) => {
    const start = bar * BEATS_PER_BAR;
    for (const hit of style.drums) events.push({ channel: "drums", beat: start + hit.beat, drum: hit.drum, velocity: hit.velocity });
    if (!voicing) return;
    for (const part of style.chords) events.push({ channel: "chords", beat: start + part.beat, beats: part.beats, midi: voicing.pitches.map((p) => p.midi) });
    for (const part of style.bass) events.push({ channel: "bass", beat: start + part.beat, beats: part.beats, midi: [voicing.bass[part.tone].midi] });
  });
  return events.sort((a, b) => a.beat - b.beat);
}

/** Phách → thời gian nhạc của Tone ("ô:phách:móc kép"), ví dụ 5.5 → "1:1:2". */
export function beatToTransport(beat: number): string {
  const bar = Math.floor(beat / BEATS_PER_BAR);
  const quarter = Math.floor(beat % BEATS_PER_BAR);
  const sixteenth = Math.round((beat % 1) * 4 * 1000) / 1000;
  return `${bar}:${quarter}:${sixteenth}`;
}

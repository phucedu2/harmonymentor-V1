// Lịch phát bài dài (chế độ Bài hát, ADR-013 đề xuất): hàm thuần, không Tone.js, để test bằng Vitest.
//
// Vì sao lên lịch theo khối: bài 2–4 phút có 3 000–8 000 nhát. Đẩy hết lên Transport một lần làm trình duyệt khựng
// lúc bấm Phát (đo được ~200 ms trên laptop phổ thông) và giữ hàng nghìn sự kiện trong bộ nhớ. Ta chia bài thành khối
// 4 ô (16 phách): khi đang phát khối k thì xếp lịch khối k+1, luôn đi trước một khối (~10 giây ở 100 BPM).
import type { AutomationPoint, PlayHit, SongSection, TempoPoint } from "./types";

export const BLOCK_BEATS = 16;

/** Khối chứa phách `beat`. Ranh giới nửa mở [k·B, (k+1)·B): nhát đúng ở phách đầu khối thuộc khối sau. */
export function blockOf(beat: number, blockBeats = BLOCK_BEATS): number {
  return Math.floor(beat / blockBeats + 1e-9);
}

/** Chia nhát theo khối. Mỗi nhát nằm ở đúng một khối (không rơi, không trùng ở ranh giới). */
export function splitBlocks(hits: PlayHit[], blockBeats = BLOCK_BEATS): Map<number, PlayHit[]> {
  const out = new Map<number, PlayHit[]>();
  for (const h of hits) {
    const k = blockOf(h.beat, blockBeats);
    const list = out.get(k);
    if (list) list.push(h); else out.set(k, [h]);
  }
  return out;
}

/** Tempo tại một phách, tính cả đoạn chậm dần tuyến tính (ritardando). */
export function tempoAt(beat: number, baseBpm: number, map: TempoPoint[] = []): number {
  let bpm = baseBpm;
  for (let i = 0; i < map.length; i += 1) {
    const p = map[i];
    if (beat < p.beat) {
      if (p.ramp && i > 0) {
        const a = map[i - 1];
        const t = Math.max(0, (beat - a.beat) / (p.beat - a.beat));
        return a.bpm + (p.bpm - a.bpm) * t;
      }
      return bpm;
    }
    bpm = p.bpm;
  }
  return bpm;
}

/** Giây thật từ đầu bài tới phách `beat` (tích phân 60/tempo), để hiện phút:giây và con trỏ trên dòng thời gian. */
export function beatToSeconds(beat: number, baseBpm: number, map: TempoPoint[] = []): number {
  if (!map.length) return (beat * 60) / baseBpm;
  // Chia nhỏ 1/8 phách: đủ chính xác (< 1 ms) cho đoạn chậm dần vài ô.
  const step = 0.125;
  let t = 0;
  for (let b = 0; b < beat; b += step) {
    const len = Math.min(step, beat - b);
    t += (len * 60) / tempoAt(b + len / 2, baseBpm, map);
  }
  return t;
}

/** Giá trị của từng thông số tự động hóa tại phách `beat` (để nhảy tới giữa bài mà mức âm lượng/bộ lọc vẫn đúng). */
export function automationAt(points: AutomationPoint[], beat: number): Record<AutomationPoint["target"], number> {
  const state: Record<AutomationPoint["target"], number> = { master: 0, filter: 20000, reverb: 1, reverb_return: 1 };
  const sorted = [...points].sort((a, b) => a.beat - b.beat);
  for (const p of sorted) {
    if (p.beat > beat) break;
    const from = state[p.target];
    if (p.ramp > 0 && beat < p.beat + p.ramp) {
      const t = (beat - p.beat) / p.ramp;
      state[p.target] = p.target === "filter" ? from * (p.value / from) ** t : from + (p.value - from) * t;
    } else {
      state[p.target] = p.value;
    }
  }
  return state;
}

/** Đoạn đang phát tại phách `beat` (null nếu ngoài bài). */
export function sectionAt(sections: SongSection[], beat: number): SongSection | null {
  return sections.find((s) => s.start_beat <= beat && beat < s.end_beat) ?? null;
}

/** "m:ss" cho giây. */
export function mmss(sec: number): string {
  const s = Math.max(0, Math.round(sec));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

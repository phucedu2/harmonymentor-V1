// FX chuyển đoạn (chế độ Bài hát, QĐ 6A): dựng trong code, không thêm mẫu âm thanh mới.
// - Cymbal ngược: lấy chính mẫu crash CC0 đang dùng (Big Rusty Drums), đảo ngược buffer → tiếng "hút" vào phách 1.
// - Riser: tiếng ồn trắng qua bộ lọc dải quét từ 300 Hz lên 7 kHz, to dần, cắt gọn đúng ranh giới đoạn.
// Cả hai đi vào kênh Trống, nên tắt kênh Trống thì FX cũng tắt, và limiter tổng vẫn chặn đỉnh.
import * as Tone from "tone";

import { bufferFor, type InstrumentManifest } from "./samples";

const reversedCache = new Map<string, AudioBuffer>();

/** Bản đảo ngược của một AudioBuffer (mỗi kênh đọc từ cuối lên đầu). Thuần, dùng lại được trong Tone.Offline. */
export function reverseBuffer(src: AudioBuffer, ctx: BaseAudioContext): AudioBuffer {
  const out = ctx.createBuffer(src.numberOfChannels, src.length, src.sampleRate);
  for (let c = 0; c < src.numberOfChannels; c += 1) {
    const from = src.getChannelData(c);
    const to = out.getChannelData(c);
    for (let i = 0, n = from.length; i < n; i += 1) to[i] = from[n - 1 - i];
  }
  return out;
}

/** Lấy mẫu crash lực vừa trong manifest trống (null nếu chưa tải mẫu: khi đó dùng tiếng ồn thay thế). */
function crashBuffer(drums: InstrumentManifest | undefined): AudioBuffer | null {
  const zones = drums?.pieces.crash ?? [];
  if (!zones.length) return null;
  const zone = zones[Math.floor(zones.length / 2)];
  const buf = bufferFor(zone.file);
  return buf?.loaded ? (buf.get() ?? null) : null;
}

export class SongFx {
  private nodes: Tone.ToneAudioNode[] = [];
  private context = Tone.getContext();

  constructor(private output: Tone.InputNode, private drums?: InstrumentManifest) {}

  /** Cymbal ngược dài `durSec`, KẾT THÚC đúng lúc `endTime` (phách 1 của đoạn mới). */
  reverseCymbal(endTime: number, durSec: number, gain = 0.8): void {
    const crash = crashBuffer(this.drums);
    const start = Math.max(this.context.currentTime, endTime - durSec);
    if (!crash) { this.riser(start, endTime - start, gain * 0.5, 2500); return; }
    const key = `${crash.length}:${crash.sampleRate}`;
    let rev = reversedCache.get(key);
    if (!rev || rev.sampleRate !== this.context.sampleRate) {
      rev = reverseBuffer(crash, this.context.rawContext as BaseAudioContext);
      reversedCache.set(key, rev);
    }
    const g = new Tone.Gain({ context: this.context, gain: 0 }).connect(this.output);
    const src = new Tone.ToneBufferSource({ context: this.context, url: new Tone.ToneAudioBuffer(rev) }).connect(g);
    // Lấy đoạn CUỐI của bản đảo (= phần đầu tiếng crash, chỗ sáng nhất) để cao trào rơi đúng phách.
    const offset = Math.max(0, rev.duration - (endTime - start));
    g.gain.setValueAtTime(0, start);
    g.gain.linearRampToValueAtTime(gain, endTime - 0.01);
    g.gain.linearRampToValueAtTime(0, endTime + 0.01);
    src.start(start, offset);
    src.stop(endTime + 0.03);
    this.nodes.push(g, src);
  }

  /** Riser: ồn trắng qua bộ lọc dải quét lên, to dần trong `durSec`, cắt ở `start + durSec`. */
  riser(start: number, durSec: number, gain = 0.35, topHz = 7000): void {
    const t0 = Math.max(this.context.currentTime, start);
    const end = t0 + Math.max(0.2, durSec);
    const g = new Tone.Gain({ context: this.context, gain: 0 }).connect(this.output);
    const filter = new Tone.Filter({ context: this.context, type: "bandpass", frequency: 300, Q: 1.2 }).connect(g);
    const noise = new Tone.Noise({ context: this.context, type: "white" }).connect(filter);
    filter.frequency.setValueAtTime(300, t0);
    filter.frequency.exponentialRampToValueAtTime(topHz, end);
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(gain, end - 0.02);
    g.gain.linearRampToValueAtTime(0, end);
    noise.start(t0).stop(end + 0.02);
    this.nodes.push(g, filter, noise);
  }

  dispose(): void {
    for (const n of this.nodes) { try { n.dispose(); } catch { /* đã hủy */ } }
    this.nodes = [];
  }
}

// Nhạc cụ mẫu nhiều lớp lực (velocity layer) + round-robin, và synth dự phòng khi chưa tải được mẫu.
//
// Vì sao không dùng Tone.Sampler có sẵn: Tone.Sampler chỉ có MỘT lớp cho mỗi nốt, nên đánh nhẹ hay mạnh chỉ là to/nhỏ
// cùng một tiếng. Piano thật đánh mạnh thì sáng và "cứng" hơn hẳn, nên ta chọn mẫu theo lớp lực rồi mới chỉnh âm lượng.
// Round-robin: hai nhát snare liền nhau dùng hai mẫu thu khác nhau, tránh tiếng "súng máy" (machine-gun).
import * as Tone from "tone";

import type { PlayHit } from "./types";
import { bufferFor, zonesFor, type InstrumentManifest, type SampleZone } from "./samples";

export interface BandInstrument {
  play(hit: PlayHit, time: number, durSec: number): void;
  releaseAll(time?: number): void;
  dispose(): void;
}

// Thời gian nhả phím/dây (giây): piano nhả damper chậm, clavi và tiếng tắt dây rất nhanh.
const RELEASE: Record<string, number> = { piano: 0.35, epiano: 0.3, clav: 0.06, bass: 0.1, upright: 0.14, guitar: 0.16, guitar_mute: 0.04, cello: 0.6 };
// Vị trí trái/phải trong dàn trống, nhìn từ khán giả (hat lệch phải ~20%, như yêu cầu "pan kiểu phòng thu").
const DRUM_PAN: Record<string, number> = {
  kick: 0, snare: 0, rim: 0, xstick: 0, br_snare: 0, hh_c: 0.22, hh_o: 0.22, hh_p: 0.22, br_hh: 0.22,
  ride: -0.28, ride_b: -0.28, br_ride: -0.28, crash: -0.38, tom_h: -0.12, tom_m: 0.08, tom_f: 0.32,
  conga_h: 0.4, conga_l: 0.45, shaker: -0.42, tamb: 0.35, tri: -0.5, clap: 0,
};
const MAX_VOICES = 48;

type Voice = { src: Tone.ToneBufferSource; gain: Tone.Gain; end: number };

export class SampledInstrument implements BandInstrument {
  private zones: Record<string, SampleZone[]>;
  private layers: number[];
  private rrCounter = new Map<string, number>();
  private voices: Voice[] = [];
  private openHats: Voice[] = [];
  private pans = new Map<string, Tone.Panner>();
  // Giữ context lúc dựng: Tone.Offline trả context gốc về trước khi thu, nên giọng tạo lúc phát phải ghi rõ context.
  private context = Tone.getContext();

  constructor(private key: string, manifest: InstrumentManifest, lite: boolean, private output: Tone.InputNode) {
    this.zones = zonesFor(manifest, lite);
    this.layers = [...new Set(Object.values(this.zones).flat().map((z) => z.layer))].sort((a, b) => a - b);
  }

  /** Lớp lực theo velocity: chia đều các lớp có sẵn; vị trí trong lớp → âm lượng 0,55..1 (≈ -5 dB..0 dB). */
  private layerFor(vel: number): { layer: number; gain: number } {
    const n = this.layers.length;
    const scaled = Math.min(0.9999, Math.max(0, vel)) * n;
    const idx = Math.floor(scaled);
    return { layer: this.layers[idx], gain: 0.55 + 0.45 * (scaled - idx) };
  }

  private pick(piece: string, midi: number | null, layer: number): SampleZone | undefined {
    const zones = this.zones[piece] ?? [];
    if (!zones.length) return undefined;
    const sameLayer = zones.filter((z) => z.layer === layer);
    const pool = sameLayer.length ? sameLayer : zones;
    let candidates = pool;
    if (midi !== null) {
      // Nốt mẫu gần nhất; bằng khoảng cách thì lấy mẫu thấp hơn (dịch lên nghe tự nhiên hơn dịch xuống).
      const best = Math.min(...pool.map((z) => Math.abs((z.midi ?? 0) - midi)));
      candidates = pool.filter((z) => Math.abs((z.midi ?? 0) - midi) === best);
      const lowest = Math.min(...candidates.map((z) => z.midi ?? 0));
      candidates = candidates.filter((z) => z.midi === lowest);
    }
    const key = `${piece}:${candidates[0].layer}:${candidates[0].midi}`;
    const n = this.rrCounter.get(key) ?? 0;
    this.rrCounter.set(key, n + 1);
    return candidates[n % candidates.length];
  }

  private dest(piece: string): Tone.InputNode {
    if (this.key !== "drums" && this.key !== "perc") return this.output;
    let p = this.pans.get(piece);
    if (!p) {
      p = new Tone.Panner({ context: this.context, pan: DRUM_PAN[piece] ?? 0 }).connect(this.output);
      this.pans.set(piece, p);
    }
    return p;
  }

  play(hit: PlayHit, time: number, durSec: number): void {
    const piece = hit.piece ?? "notes";
    const { layer, gain } = this.layerFor(hit.vel);
    const zone = this.pick(piece, hit.midi, layer);
    const buffer = zone && bufferFor(zone.file);
    if (!zone || !buffer || !buffer.loaded) return;
    const rate = hit.midi !== null && zone.midi !== null ? 2 ** ((hit.midi - zone.midi - zone.cents / 100) / 12) : 1;
    // Ghost note rất nhỏ; lớp lực đã mang âm sắc, phần còn lại là âm lượng.
    const level = gain * (hit.vel < 0.3 ? hit.vel / 0.3 : 1);
    const g = new Tone.Gain({ context: this.context, gain: level }).connect(this.dest(piece));
    const src = new Tone.ToneBufferSource({ context: this.context, url: buffer, playbackRate: rate, fadeIn: 0.002 }).connect(g);
    src.start(time);
    const sampleLen = buffer.duration / rate;
    let end = time + sampleLen;
    if (hit.midi !== null) {
      const release = RELEASE[this.key] ?? 0.15;
      const stopAt = time + Math.max(0.03, durSec);
      if (stopAt < end) {
        g.gain.setValueAtTime(level, stopAt);
        g.gain.setTargetAtTime(0, stopAt, release / 3);
        end = stopAt + release * 1.5;
        src.stop(end);
      }
    }
    // Hi-hat đóng/đạp chặn tiếng hi-hat mở đang ngân (như chân đạp khép hai lá cymbal).
    if (piece === "hh_c" || piece === "hh_p") {
      for (const v of this.openHats) if (v.end > time) { v.gain.gain.setTargetAtTime(0, time, 0.015); v.end = time + 0.08; v.src.stop(v.end); }
      this.openHats = [];
    }
    const voice = { src, gain: g, end };
    if (piece === "hh_o") this.openHats.push(voice);
    this.sweep();
    this.voices.push(voice);
    // Giới hạn số giọng để không rè trên laptop phổ thông: tắt nhanh giọng cũ nhất.
    const active = this.voices.filter((v) => v.end > time);
    if (active.length > MAX_VOICES) {
      const old = active[0];
      old.gain.gain.setTargetAtTime(0, time, 0.01);
      old.end = time + 0.05;
      try { old.src.stop(old.end); } catch { /* đã dừng */ }
    }
  }

  /**
   * Dọn giọng đã tắt hẳn. Không dùng `onended` để dispose: trong Tone.Offline, gọi stop() rồi dispose trong onended
   * làm nguồn bị hủy trước khi thu (đo được: bản thu im lặng hoàn toàn), nên dọn trễ theo thời điểm kết thúc đã biết.
   */
  private sweep(): void {
    const now = this.context.currentTime;
    // Tone.Offline chạy hết đồng hồ (currentTime giả) TRƯỚC rồi mới thu âm thật. Hủy nút ở đây thì giọng chưa kịp
    // kêu đã mất: bản thu im lặng, chỉ còn ~2 giây cuối (đo 02/11/2026, mọi bản "sau" ở nghe-thu đều dính).
    // Nên khi thu offline chỉ bỏ khỏi danh sách theo dõi, để context offline tự giải phóng sau khi thu xong.
    const offline = this.context.isOffline;
    const keep: Voice[] = [];
    for (const v of this.voices) {
      if (v.end + 0.5 < now) { if (!offline) { v.src.dispose(); v.gain.dispose(); } } else keep.push(v);
    }
    this.voices = keep;
  }

  releaseAll(time = this.context.now()): void {
    for (const v of this.voices) {
      v.gain.gain.cancelScheduledValues(time);
      v.gain.gain.setTargetAtTime(0, time, 0.05);
      try { v.src.stop(time + 0.3); } catch { /* đã dừng */ }
    }
  }

  dispose(): void {
    this.releaseAll();
    for (const p of this.pans.values()) p.dispose();
  }
}

/** Synth dự phòng (âm cũ của Bước 4): dùng khi mẫu lỗi mạng hoặc không giải mã được — không bao giờ im lặng. */
export class SynthInstrument implements BandInstrument {
  private poly?: Tone.PolySynth;
  private mono?: Tone.MonoSynth;
  private kick?: Tone.MembraneSynth;
  private noise?: Tone.NoiseSynth;
  private metal?: Tone.MetalSynth;

  constructor(key: string, output: Tone.InputNode) {
    if (key === "drums" || key === "perc") {
      this.kick = new Tone.MembraneSynth({ pitchDecay: 0.04, octaves: 6, envelope: { attack: 0.001, decay: 0.3, sustain: 0, release: 0.1 } }).connect(output);
      this.noise = new Tone.NoiseSynth({ noise: { type: "white" }, envelope: { attack: 0.001, decay: 0.15, sustain: 0 } }).connect(output);
      this.metal = new Tone.MetalSynth({ envelope: { attack: 0.001, decay: 0.05, release: 0.01 }, harmonicity: 5.1, modulationIndex: 32, resonance: 4000, octaves: 1.5 }).connect(output);
      this.metal.volume.value = -22;
      this.noise.volume.value = -8;
    } else if (key === "bass" || key === "upright") {
      this.mono = new Tone.MonoSynth({ oscillator: { type: "triangle" }, envelope: { attack: 0.01, decay: 0.2, sustain: 0.5, release: 0.2 }, filterEnvelope: { attack: 0.01, decay: 0.2, sustain: 0.3, baseFrequency: 120, octaves: 2 } }).connect(output);
    } else {
      this.poly = new Tone.PolySynth(Tone.Synth, { oscillator: { type: "triangle" }, envelope: { attack: 0.02, decay: 0.3, sustain: 0.4, release: 0.8 } }).connect(output);
      this.poly.volume.value = -8;
    }
  }

  play(hit: PlayHit, time: number, durSec: number): void {
    if (hit.piece) {
      if (hit.piece === "kick" || hit.piece.startsWith("tom") || hit.piece.startsWith("conga")) this.kick?.triggerAttackRelease(hit.piece === "kick" ? "C1" : "G1", "8n", time, hit.vel);
      else if (["snare", "rim", "xstick", "br_snare", "clap"].includes(hit.piece)) this.noise?.triggerAttackRelease("16n", time, hit.vel);
      else this.metal?.triggerAttackRelease("C6", "32n", time, hit.vel);
      return;
    }
    const freq = Tone.Frequency(hit.midi ?? 60, "midi").toFrequency();
    if (this.mono) this.mono.triggerAttackRelease(freq, durSec, time, hit.vel);
    else this.poly?.triggerAttackRelease(freq, durSec, time, hit.vel * 0.8);
  }

  releaseAll(): void { this.poly?.releaseAll(); this.mono?.triggerRelease(); }

  dispose(): void { for (const n of [this.poly, this.mono, this.kick, this.noise, this.metal]) n?.dispose(); }
}

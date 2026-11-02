// Bàn trộn kiểu phòng thu: mỗi kênh = Gain vào → (hiệu ứng riêng) → EQ3 → Compressor → Panner → Fader;
// hai bus "send" dùng chung (reverb phòng + delay); bus chính có compressor nhẹ + limiter -2 dB + bộ cắt mềm để không vỡ tiếng.
//
// Vì sao dùng bus send: nếu mỗi nhạc cụ có reverb riêng, CPU tốn gấp 4 và các nhạc cụ nghe như ở 4 phòng khác nhau.
// Một reverb chung, mỗi kênh gửi vào một lượng khác nhau (trống nhiều hơn bass) → cả ban nhạc "đứng trong một phòng".
import * as Tone from "tone";

import type { BandChannel, BandMix, StyleFx } from "./types";

type Strip = { input: Tone.Gain; fader: Tone.Volume; send: Tone.Gain; delaySend: Tone.Gain; nodes: Tone.ToneAudioNode[] };

// Lượng gửi reverb theo kênh (nhân với mức reverb của phong cách): bass gần như khô để tiếng trầm không đục.
const SEND: Record<BandChannel, number> = { chords: 1, bass: 0.12, guitar: 0.9, drums: 0.75 };
// Âm lượng nền mỗi kênh (dB) để cân ban nhạc trước khi người dùng kéo fader.
const BASE_DB: Record<BandChannel, number> = { chords: -7, bass: -5, guitar: 0, drums: 4 };
// Bù riêng theo phong cách (dB), từ số đo LUFS từng kênh thu solo ngày 02/11/2026 (scripts/backing-track): mật độ
// nốt mỗi phong cách khác nhau (ballad thưa, bossa dày) nên cùng một fader nghe to nhỏ khác nhau. Đích: phím ≈ trống,
// bass thấp hơn ~2 dB, guitar đệm thấp hơn ~2 dB (rock: guitar dẫn, phím lùi lại). Jazz/ballad để trống nhẹ hơn.
const STYLE_TRIM: Record<string, Partial<Record<BandChannel, number>>> = {
  pop: { chords: -1.5, bass: 1, drums: 1 },
  ballad: { chords: 4.5, bass: 3.5, drums: 1 },
  bossa: { chords: -6.5, bass: 1.5, guitar: -2, drums: -3 },
  lofi: { chords: -6.5, bass: -0.5, drums: 0.5 },
  jazz: { chords: -0.5, bass: 0.5, drums: 2 },
  rock: { chords: -0.5, bass: -1.5, guitar: -10, drums: -0.5 },
  indie: { chords: 4, bass: 5, guitar: 6, drums: 1 },
  funk: { chords: 0, bass: -1.5, guitar: 1.5 },
  rnb: { chords: -6.5, drums: -1 },
};
// Bù âm lượng tổng: đo bản thu pop -23,5 LUFS khi chưa bù; sau khi cân kênh, +6 dB đưa về -16..-18 LUFS (mức nghe thoải mái trên web);
// limiter -2 dB phía sau chặn đỉnh (chừa chỗ cho đỉnh xuyên mẫu) nên không vỡ tiếng.
const MAKEUP_DB = 6;
const PAN: Record<BandChannel, number> = { chords: 0.05, bass: 0, guitar: -0.3, drums: 0 };

const ROOM: Record<StyleFx["room"], { decay: number; preDelay: number }> = {
  room: { decay: 1.1, preDelay: 0.008 }, plate: { decay: 1.9, preDelay: 0.015 }, hall: { decay: 3.0, preDelay: 0.025 },
};

/** Đường cong cắt mềm: |x| ≤ 0,7 giữ nguyên; trên đó nén kiểu tanh về trần 0,97. */
export function softClip(x: number): number {
  const a = Math.abs(x);
  if (a <= 0.7) return x;
  return Math.sign(x) * (0.7 + 0.27 * Math.tanh((a - 0.7) / 0.27));
}

export class BandMixer {
  readonly strips: Record<BandChannel, Strip>;
  private master: Tone.Gain;
  private reverb: Tone.Reverb;
  private delay: Tone.FeedbackDelay;
  private extra: Tone.ToneAudioNode[] = [];
  private vinyl: Tone.Player | null = null;
  readonly ready: Promise<void>;

  constructor(readonly fx: StyleFx, destination: Tone.InputNode = Tone.getDestination(), readonly style = "") {
    // Limiter của Web Audio (DynamicsCompressor) có attack nên tiếng kick vẫn lọt đỉnh 0 dBFS (đo được 30-120 mẫu chạm
    // trần mỗi bản thu 16 s). Thêm bộ cắt mềm cuối chuỗi: tuyến tính dưới 0,7, cong dần tới trần 0,97, không bao giờ vỡ tiếng.
    // WaveShaper chỉ nhận [-1, 1]: chia đôi trước rồi nhân đôi trong đường cong, để đỉnh tới 2,0 (+6 dB) vẫn cong mềm.
    const clipper = new Tone.WaveShaper((x) => softClip(x * 2), 8192).connect(destination);
    const pad = new Tone.Gain(0.5).connect(clipper);
    const limiter = new Tone.Limiter(-2).connect(pad);
    this.extra.push(clipper, pad);
    const glue = new Tone.Compressor({ threshold: -14, ratio: 2, attack: 0.02, release: 0.25 }).connect(limiter);
    this.extra.push(limiter, glue);
    let masterOut: Tone.InputNode = glue;
    if (fx.lofi) {
      // Lo-fi: lọc thấp ~4,2 kHz + bão hòa nhẹ + wow/flutter (rung cao độ ±5 cent như băng/đĩa cũ).
      const lp = new Tone.Filter({ type: "lowpass", frequency: 4200, Q: 0.5 }).connect(glue);
      const sat = new Tone.Distortion({ distortion: 0.08, wet: 0.35 }).connect(lp);
      const wow = new Tone.Vibrato({ frequency: 0.55, depth: 0.06, wet: 1 }).connect(sat);
      this.extra.push(lp, sat, wow);
      masterOut = wow;
    }
    this.master = new Tone.Gain(Tone.dbToGain(MAKEUP_DB)).connect(masterOut);

    const room = ROOM[fx.room];
    this.reverb = new Tone.Reverb({ decay: room.decay, preDelay: room.preDelay, wet: 1 }).connect(this.master);
    this.delay = new Tone.FeedbackDelay({ delayTime: "8n.", feedback: 0.28, wet: 1 }).connect(this.master);
    const delayFilter = new Tone.Filter({ type: "lowpass", frequency: 3000 }).connect(this.delay);
    this.extra.push(delayFilter);
    this.ready = this.reverb.ready;

    const make = (ch: BandChannel): Strip => {
      const fader = new Tone.Volume(BASE_DB[ch]).connect(this.master);
      const panner = new Tone.Panner(PAN[ch]).connect(fader);
      const comp = new Tone.Compressor(ch === "drums" ? { threshold: -16, ratio: 3, attack: 0.008, release: 0.15 }
        : ch === "bass" ? { threshold: -20, ratio: 4, attack: 0.01, release: 0.2 } : { threshold: -18, ratio: 2.5, attack: 0.015, release: 0.25 }).connect(panner);
      // EQ: bass giữ đáy; phím/guitar cắt bớt dải trầm để nhường bass (tránh "đục").
      const eq = new Tone.EQ3(ch === "bass" ? { low: 2, mid: -1, high: -2 } : ch === "drums" ? { low: 1, mid: -1, high: 1 }
        : { low: -4, mid: 0, high: 0, lowFrequency: 220 }).connect(comp);
      const nodes: Tone.ToneAudioNode[] = [fader, panner, comp, eq];
      let head: Tone.InputNode = eq;
      if (ch === "guitar" && fx.drive) {
        // Overdrive mô phỏng ampli + loa thùng 4x12: méo → cắt < 90 Hz và > 5,5 kHz → nén.
        const cab = new Tone.Filter({ type: "lowpass", frequency: 5500, Q: 0.7 }).connect(eq);
        const hp = new Tone.Filter({ type: "highpass", frequency: 90 }).connect(cab);
        const drive = new Tone.Distortion({ distortion: 0.55, oversample: "2x" }).connect(hp);
        const pre = new Tone.Filter({ type: "highpass", frequency: 160 }).connect(drive);
        nodes.push(cab, hp, drive, pre);
        head = pre;
      }
      if (ch === "guitar" && fx.chorus) {
        const chorus = new Tone.Chorus({ frequency: 0.8, delayTime: 3.5, depth: 0.5, spread: 140, wet: 0.45 }).connect(head);
        chorus.start();
        nodes.push(chorus);
        head = chorus;
      }
      const input = new Tone.Gain(1).connect(head);
      const send = new Tone.Gain(fx.reverb * SEND[ch] * 2.2).connect(this.reverb);
      const delaySend = new Tone.Gain(ch === "guitar" || ch === "chords" ? fx.delay : 0).connect(delayFilter);
      fader.connect(send);
      fader.connect(delaySend);
      nodes.push(send, delaySend, input);
      return { input, fader, send, delaySend, nodes };
    };
    this.strips = { chords: make("chords"), bass: make("bass"), guitar: make("guitar"), drums: make("drums") };
    if (fx.lofi) this.vinyl = this.makeVinyl();
  }

  /** Tiếng đĩa than: tiếng xì rất nhỏ + tiếng lách tách ngẫu nhiên (bộ đệm 4 giây lặp lại, sinh bằng hạt giống cố định). */
  private makeVinyl(): Tone.Player {
    const sr = Tone.getContext().sampleRate;
    const len = sr * 4;
    const buf = Tone.getContext().createBuffer(1, len, sr);
    const data = buf.getChannelData(0);
    let s = 12345;
    const rand = () => { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; };
    let lp = 0;
    for (let i = 0; i < len; i += 1) {
      lp = lp * 0.97 + (rand() * 2 - 1) * 0.03;
      data[i] = lp * 0.25;
      if (rand() < 0.00035) data[i] += (rand() * 2 - 1) * 0.6;
    }
    const player = new Tone.Player(new Tone.ToneAudioBuffer(buf)).connect(this.master);
    player.loop = true;
    player.volume.value = -30;
    return player;
  }

  setVinyl(on: boolean, time?: number): void {
    if (!this.vinyl) return;
    if (on && this.vinyl.state !== "started") this.vinyl.start(time);
    if (!on && this.vinyl.state === "started") this.vinyl.stop(time);
  }

  /** Fader 0..1 → dB (đường cong log như fader thật), cộng mức nền của kênh. */
  applyMix(mix: BandMix): void {
    for (const ch of Object.keys(this.strips) as BandChannel[]) {
      const { volume, muted } = mix[ch];
      const fader = this.strips[ch].fader;
      // Đặt âm lượng trước rồi mới tắt tiếng: với Tone.Volume, gán volume sau khi mute sẽ bật tiếng lại.
      fader.volume.value = BASE_DB[ch] + (STYLE_TRIM[this.style]?.[ch] ?? 0) + 20 * Math.log10(Math.max(volume, 0.001) / 0.8);
      fader.mute = muted || volume <= 0.001;
    }
  }

  input(ch: BandChannel): Tone.Gain {
    return this.strips[ch].input;
  }

  dispose(): void {
    this.vinyl?.dispose();
    for (const strip of Object.values(this.strips)) for (const n of strip.nodes) n.dispose();
    for (const n of this.extra) n.dispose();
    this.reverb.dispose();
    this.delay.dispose();
    this.master.dispose();
  }
}

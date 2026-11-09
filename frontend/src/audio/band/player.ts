// Phát bản phối bằng ban nhạc mẫu thật (ADR-012 đề xuất). Lịch theo phách trên Transport của Tone.js, nên đổi
// tempo khi đang phát không làm lệch kênh (tài liệu 04 mục 6.8: giây = phách × 60 / BPM, chỉ tính lúc phát).
// Mẫu chưa tải được (lỗi mạng, trình duyệt không giải mã .ogg) → tự dùng synth dự phòng, không im lặng.
//
// Chế độ Bài hát (ADR-013 đề xuất): lên lịch theo khối 4 ô (songSchedule.ts), áp automation âm lượng/bộ lọc/reverb,
// tempo chậm dần ở kết bài, FX chuyển đoạn (cymbal ngược, riser), nhảy tới đoạn bất kỳ và lặp riêng một đoạn.
import * as Tone from "tone";

import { humanize } from "./humanize";
import { SampledInstrument, SynthInstrument, type BandInstrument } from "./instruments";
import { BandMixer } from "./mixer";
import { instrumentsFor, loadInstruments, loadManifest, preferLite, type LoadProgress } from "./samples";
import { SongFx } from "./songFx";
import { BLOCK_BEATS, automationAt, beatToSeconds, splitBlocks, tempoAt } from "./songSchedule";
import { BAND_CHANNELS, type Arrangement, type BandChannel, type BandMix, type GuitarTone, type PlayHit } from "./types";

export type PlayOptions = {
  arrangement: Arrangement;
  bpm: number;
  seed: number;
  loop: boolean;
  mix: BandMix;
  /** Âm sắc guitar; bỏ trống = theo phong cách. */
  guitarTone?: GuitarTone;
  vinyl?: boolean;
  /** Chế độ Bài hát: phát từ phách này (bấm một đoạn trên dòng thời gian để nhảy tới). */
  startBeat?: number;
  /** Chế độ Bài hát: chỉ lặp [start, end) (để học sinh tập riêng Chorus). */
  loopRange?: { start: number; end: number } | null;
  onBar: (bar: number) => void;
  onEnd: () => void;
  onProgress?: (p: LoadProgress) => void;
};

const CHANNEL_OF: Record<string, BandChannel> = {
  piano: "chords", epiano: "chords", clav: "chords", bass: "bass", upright: "bass",
  guitar: "guitar", guitar_mute: "guitar", drums: "drums", perc: "drums", cello: "strings",
};

const isSong = (arr: Arrangement) => arr.mode === "song";

/** Nhạc cụ cần tải: thêm nhạc cụ của hook (vd bossa phím điện nhưng hook là piano). */
function neededKeys(arr: Arrangement, strings = false): string[] {
  const keys = instrumentsFor({ keys: arr.tracks.keys.instrument, bass: arr.tracks.bass.instrument }, true);
  if (strings) keys.push("cello");
  const hook = arr.tracks.hook;
  if (hook && hook.events.length && !keys.includes(hook.instrument)) keys.push(hook.instrument);
  return keys;
}

/** Dựng nhạc cụ cho một bản phối, nối vào bàn trộn. Dùng chung cho phát trực tiếp và thu offline (Tone.Offline). */
export async function buildBand(arr: Arrangement, lite: boolean, useSamples: boolean, mixer: BandMixer, withStrings = false) {
  const keys = instrumentsFor({ keys: arr.tracks.keys.instrument, bass: arr.tracks.bass.instrument }, true);
  if (withStrings) keys.push("cello");
  const manifest = useSamples ? await loadManifest() : null;
  const band = new Map<string, BandInstrument>();
  for (const key of keys) {
    const out = mixer.input(CHANNEL_OF[key]);
    band.set(key, manifest ? new SampledInstrument(key, manifest.instruments[key], lite, out) : new SynthInstrument(key, out));
  }
  // Hook có nhạc cụ riêng nối vào kênh "Hook", để kéo fader Hook không đổi âm lượng phím đệm.
  const hook = arr.tracks.hook;
  if (hook && hook.events.length) {
    const out = mixer.input("hook");
    band.set("hook", manifest ? new SampledInstrument(hook.instrument, manifest.instruments[hook.instrument], lite, out)
      : new SynthInstrument(hook.instrument, out));
  }
  return band;
}

/** Xếp lịch các nhát lên Transport; trả id để xóa khi dừng. */
export function scheduleHits(transport: ReturnType<typeof Tone.getTransport>, hits: PlayHit[], band: Map<string, BandInstrument>): number[] {
  const ppq = transport.PPQ;
  return hits.map((hit) => transport.schedule((time) => {
    const inst = band.get(hit.instrument);
    // Độ dài tính theo tempo hiện tại lúc phát (người dùng có thể kéo tempo khi đang nghe).
    const durSec = (hit.dur * 60) / transport.bpm.value;
    inst?.play(hit, Math.max(0, time + hit.offset), durSec);
  }, `${Math.round(hit.beat * ppq)}i`));
}

/**
 * Lịch phần "bài hát" ngoài nốt: automation, tempo chậm dần, FX chuyển đoạn. Chỉ xếp những gì nằm trong [from, to).
 * `scaleBpm` = tempo người dùng / tempo bản phối (người dùng kéo tempo thì tempo_map co giãn theo).
 */
export function scheduleSongExtras(transport: ReturnType<typeof Tone.getTransport>, arr: Arrangement, mixer: BandMixer,
  fx: SongFx, from: number, to: number, scaleBpm: number): number[] {
  const ppq = transport.PPQ;
  const ids: number[] = [];
  const secPerBeat = () => 60 / transport.bpm.value;
  for (const p of arr.automation ?? []) {
    if (p.beat < from || p.beat >= to) continue;
    ids.push(transport.schedule((time) => mixer.automate(p, p.ramp * secPerBeat(), time), `${Math.round(p.beat * ppq)}i`));
  }
  const map = arr.tempo_map ?? [];
  map.forEach((p, i) => {
    if (p.beat < from || p.beat >= to) return;
    const next = map[i + 1];
    ids.push(transport.schedule((time) => {
      transport.bpm.setValueAtTime(p.bpm * scaleBpm, time);
      if (next?.ramp) {
        const sec = ((next.beat - p.beat) * 60) / (((p.bpm + next.bpm) / 2) * scaleBpm);
        transport.bpm.linearRampToValueAtTime(next.bpm * scaleBpm, time + sec);
      }
    }, `${Math.round(p.beat * ppq)}i`));
  });
  for (const e of arr.fx_events ?? []) {
    const end = e.beat + e.dur;
    if (end <= from || e.beat >= to) continue;
    // Xếp ở phách bắt đầu FX; thời điểm kết thúc tính theo tempo lúc đó (FX nằm trong 1–2 ô, tempo không đổi).
    ids.push(transport.schedule((time) => {
      const dur = e.dur * secPerBeat();
      if (e.kind === "reverse_cymbal") fx.reverseCymbal(time + dur, dur, e.gain ?? 0.8);
      else fx.riser(time, dur, 0.3);
    }, `${Math.round(Math.max(from, e.beat) * ppq)}i`));
  }
  return ids;
}

class BandPlayer {
  private mixer: BandMixer | null = null;
  private band: Map<string, BandInstrument> | null = null;
  private fx: SongFx | null = null;
  private bandKey = "";
  private scheduled: number[] = [];
  private mix: BandMix | null = null;
  private userBpm = 100;
  private songScale = 1;
  /** "sample" khi đang dùng mẫu thật, "synth" khi phải dùng synth dự phòng. */
  mode: "sample" | "synth" = "sample";
  lastError: string | null = null;

  /** Tải trước mẫu của phong cách (gọi khi người dùng chọn phong cách) để bấm Phát nghe ngay. */
  async preload(arr: Arrangement, onProgress?: (p: LoadProgress) => void, strings = false): Promise<void> {
    await loadInstruments(neededKeys(arr, strings), preferLite(), onProgress);
  }

  private async ensureBand(arr: Arrangement, onProgress?: (p: LoadProgress) => void, strings = false) {
    const fxKey = JSON.stringify(arr.fx);
    const key = `${arr.style}|${fxKey}|${arr.tracks.keys.instrument}|${arr.tracks.bass.instrument}|${arr.tracks.hook?.instrument ?? "-"}|${arr.tracks.hook?.events.length ? 1 : 0}|${strings ? "s" : "-"}`;
    if (this.band && this.bandKey === key) return;
    this.disposeBand();
    this.mixer = new BandMixer(arr.fx, Tone.getDestination(), arr.style);
    let useSamples = true;
    try {
      await this.preload(arr, onProgress, strings);
    } catch (e) {
      useSamples = false;
      this.lastError = e instanceof Error ? e.message : String(e);
    }
    this.mode = useSamples ? "sample" : "synth";
    this.band = await buildBand(arr, preferLite(), useSamples, this.mixer, strings);
    const manifest = useSamples ? await loadManifest().catch(() => null) : null;
    this.fx = new SongFx(this.mixer.input("drums"), manifest?.instruments.drums);
    await this.mixer.ready;
    this.bandKey = key;
  }

  setMix(mix: BandMix): void {
    this.mix = mix;
    this.mixer?.applyMix(mix);
  }

  /** Đổi âm sắc guitar ngay khi đang nghe (chỉ đổi tham số bộ lọc/méo, không dựng lại ban nhạc). */
  setGuitarTone(tone: GuitarTone): void {
    this.mixer?.setGuitarTone(tone);
  }

  setVinyl(on: boolean): void {
    this.mixer?.setVinyl(on);
  }

  setBpm(bpm: number): void {
    this.userBpm = bpm;
    Tone.getTransport().bpm.value = bpm;
  }

  async play(o: PlayOptions): Promise<void> {
    await Tone.start();
    this.stop();
    // Kênh Dây (cello) chỉ tải mẫu và phát khi người học bật; tắt thì bản phối nghe y hệt trước đây.
    const strings = !(o.mix.strings?.muted ?? true);
    await this.ensureBand(o.arrangement, o.onProgress, strings);
    this.setMix(o.mix);
    this.mixer?.setGuitarTone(o.guitarTone ?? "auto");
    const arr = o.arrangement;
    const transport = Tone.getTransport();
    this.userBpm = o.bpm;
    transport.bpm.cancelScheduledValues(0);
    transport.bpm.value = o.bpm;
    transport.swing = 0; // swing đã tính trong humanize theo từng phong cách
    const hits = humanize(arr, { seed: o.seed, bpm: o.bpm, strings });
    this.mixer?.resetAutomation();
    if (isSong(arr)) this.playSong(o, hits);
    else this.playLoop(o, hits);
    this.mixer?.setVinyl(Boolean(o.vinyl) && arr.fx.lofi);
    transport.start("+0.1");
  }

  /** Chế độ Vòng lặp (như trước 02/11 chiều): 4 vòng, lặp thì quay về vòng 2. */
  private playLoop(o: PlayOptions, hits: PlayHit[]): void {
    const arr = o.arrangement;
    const transport = Tone.getTransport();
    const ppq = transport.PPQ;
    transport.position = 0;
    const beatsPerCycle = arr.bars_per_cycle * 4;
    transport.loop = o.loop;
    // Lặp lại thì quay về vòng 2 (vòng 1 là phần mở mộc, QĐ 10A).
    transport.loopStart = `${arr.loop_from_cycle * beatsPerCycle * ppq}i`;
    transport.loopEnd = `${arr.total_beats * ppq}i`;
    this.scheduled = scheduleHits(transport, hits, this.band!);
    for (let bar = 0; bar < arr.total_beats / 4; bar += 1) {
      this.scheduled.push(transport.schedule((time) => {
        Tone.getDraw().schedule(() => o.onBar(bar % arr.bars_per_cycle), time);
      }, `${bar * 4 * ppq}i`));
    }
    if (!o.loop) {
      this.scheduled.push(transport.schedule((time) => {
        Tone.getDraw().schedule(() => { this.stop(); o.onEnd(); }, time + 1.5);
      }, `${arr.total_beats * ppq}i`));
    }
  }

  /** Chế độ Bài hát: lịch theo khối, automation đúng trạng thái tại điểm bắt đầu, lặp đoạn tùy chọn. */
  private playSong(o: PlayOptions, hits: PlayHit[]): void {
    const arr = o.arrangement;
    const transport = Tone.getTransport();
    const ppq = transport.PPQ;
    const range = o.loopRange ?? null;
    const start = range ? range.start : Math.max(0, o.startBeat ?? 0);
    const end = range ? range.end : arr.total_beats;
    this.songScale = o.bpm / arr.bpm;
    // Tempo và mức automation đúng như khi phát từ đầu tới `start` (nhảy giữa bài vẫn đúng độ to, bộ lọc).
    transport.bpm.value = tempoAt(start, arr.bpm, arr.tempo_map) * this.songScale;
    const state = automationAt(arr.automation ?? [], start);
    const now = Tone.now();
    for (const target of Object.keys(state) as (keyof typeof state)[]) this.mixer!.automate({ target, value: state[target] }, 0, now);
    transport.position = `${Math.round(start * ppq)}i`;

    const blocks = splitBlocks(hits, BLOCK_BEATS);
    const first = Math.floor(start / BLOCK_BEATS);
    const last = Math.floor((end - 1e-6) / BLOCK_BEATS);
    const inRange = (h: PlayHit) => h.beat >= start - 1e-9 && h.beat < end - 1e-9;
    if (range) {
      // Lặp một đoạn (≤ 16 ô): xếp cả đoạn một lần, Transport tự lặp các sự kiện trong vùng lặp.
      transport.loop = true;
      transport.loopStart = `${Math.round(start * ppq)}i`;
      transport.loopEnd = `${Math.round(end * ppq)}i`;
      const all: PlayHit[] = [];
      for (let k = first; k <= last; k += 1) all.push(...(blocks.get(k) ?? []).filter(inRange));
      this.scheduled.push(...scheduleHits(transport, all, this.band!));
      this.scheduled.push(...scheduleSongExtras(transport, arr, this.mixer!, this.fx!, start, end, this.songScale));
    } else {
      transport.loop = false;
      const queueBlock = (k: number) => {
        if (k > last) return;
        const list = (blocks.get(k) ?? []).filter(inRange);
        this.scheduled.push(...scheduleHits(transport, list, this.band!));
        const a = Math.max(start, k * BLOCK_BEATS);
        const z = Math.min(end, (k + 1) * BLOCK_BEATS);
        this.scheduled.push(...scheduleSongExtras(transport, arr, this.mixer!, this.fx!, a, z, this.songScale));
      };
      queueBlock(first);
      queueBlock(first + 1);
      // Đang ở đầu khối k thì xếp khối k+2: luôn có sẵn ít nhất một khối phía trước.
      for (let k = first + 1; k <= last; k += 1) {
        const kk = k;
        this.scheduled.push(transport.schedule(() => queueBlock(kk + 1), `${kk * BLOCK_BEATS * ppq}i`));
      }
      const tail = (arr.tail_beats ?? 0) * 60 / (arr.bpm * 0.85);
      this.scheduled.push(transport.schedule((time) => {
        Tone.getDraw().schedule(() => { this.stop(); o.onEnd(); }, time + 1.5 + tail);
      }, `${Math.round(end * ppq)}i`));
    }
    const firstBar = Math.floor(start / 4);
    for (let bar = firstBar; bar < Math.ceil(end / 4); bar += 1) {
      const b = bar;
      this.scheduled.push(transport.schedule((time) => {
        Tone.getDraw().schedule(() => o.onBar(b), time);
      }, `${b * 4 * ppq}i`));
    }
  }

  stop(): void {
    const transport = Tone.getTransport();
    for (const id of this.scheduled) transport.clear(id);
    this.scheduled = [];
    transport.stop();
    transport.loop = false;
    transport.bpm.cancelScheduledValues(0);
    transport.bpm.value = this.userBpm;
    for (const inst of this.band?.values() ?? []) inst.releaseAll();
    this.mixer?.setVinyl(false);
    this.fx?.dispose();
  }

  private disposeBand(): void {
    for (const inst of this.band?.values() ?? []) inst.dispose();
    this.fx?.dispose();
    this.mixer?.dispose();
    this.band = null;
    this.mixer = null;
    this.fx = null;
  }
}

export const bandPlayer = new BandPlayer();

/**
 * Thu bản phối thành AudioBuffer, chỉ dùng nội bộ để nghe so sánh (không cho người dùng xuất).
 * Gọi `loadInstruments` trước để mẫu đã giải nén. Bài hát: thu cả automation, tempo chậm dần, FX chuyển đoạn.
 *
 * Vì sao không dùng Tone.Offline + Transport: Tone chạy hết đồng hồ trước rồi mới thu, nên MỌI giọng (6 000–8 000
 * nhát một bài) được tạo và nối sẵn từ đầu; Chrome phải kéo qua tất cả ở mỗi khối 128 mẫu → thời gian thu tăng theo
 * bình phương (đo 02/11/2026: 2 000 giọng/60 s mất 164 s, bài Vừa 155 s mất 9 phút). Ở đây dùng
 * OfflineAudioContext.suspend(): cứ mỗi CHUNK giây dừng lại, tạo giọng cho đoạn kế tiếp rồi chạy tiếp → tuyến tính.
 * Thời điểm mỗi nhát tính thẳng bằng songSchedule.beatToSeconds (cùng công thức với dòng thời gian), nên tempo
 * chậm dần khớp với Transport khi phát trực tiếp.
 */
export async function renderOffline(arr: Arrangement, bpm: number, seed: number, seconds: number, mix: BandMix): Promise<Tone.ToneAudioBuffer> {
  const CHUNK = 2;
  // OfflineAudioContext gốc của trình duyệt (bản bọc của Tone không có suspend()).
  const native = new OfflineAudioContext(2, Math.ceil(seconds * 44100), 44100);
  const ctx = new Tone.OfflineContext(native as unknown as Tone.BaseContext["rawContext"] as never);
  const prev = Tone.getContext();
  Tone.setContext(ctx);
  try {
    const mixer = new BandMixer(arr.fx, ctx.destination, arr.style);
    await mixer.ready;
    mixer.applyMix(mix);
    const band = await buildBand(arr, false, true, mixer);
    const scale = bpm / arr.bpm;
    const map = (arr.tempo_map ?? []).map((p) => ({ ...p, bpm: p.bpm * scale }));
    const sec = (beat: number) => beatToSeconds(beat, bpm, map);
    const hits = humanize(arr, { seed, bpm }).map((h) => ({ h, t: Math.max(0, sec(h.beat) + h.offset) }))
      .sort((a, b) => a.t - b.t);
    if (isSong(arr)) {
      const manifest = await loadManifest();
      const fx = new SongFx(mixer.input("drums"), manifest.instruments.drums);
      mixer.resetAutomation(0);
      for (const p of arr.automation ?? []) mixer.automate(p, sec(p.beat + p.ramp) - sec(p.beat), sec(p.beat));
      for (const e of arr.fx_events ?? []) {
        const a = sec(e.beat), b = sec(e.beat + e.dur);
        if (e.kind === "reverse_cymbal") fx.reverseCymbal(b, b - a, e.gain ?? 0.8);
        else fx.riser(a, b - a, 0.3);
      }
    }
    if (arr.fx.lofi) mixer.setVinyl(true, 0);
    const raw = native;
    let k = 0;
    const scheduleUpTo = (until: number) => {
      for (; k < hits.length && hits[k].t < until; k += 1) {
        const { h, t } = hits[k];
        band.get(h.instrument)?.play(h, t, (h.dur * 60) / tempoAt(h.beat, bpm, map));
      }
    };
    // Khối đầu xếp ngay; mỗi lần dừng ở t thì xếp các nhát trong [t + CHUNK, t + 2·CHUNK) để luôn đi trước một khối.
    scheduleUpTo(CHUNK * 2);
    for (let t = CHUNK; t < seconds; t += CHUNK) {
      const until = t + CHUNK * 2;
      raw.suspend(t).then(() => { scheduleUpTo(until); return raw.resume(); });
    }
    const buffer = await raw.startRendering();
    for (const inst of band.values()) inst.dispose();
    return new Tone.ToneAudioBuffer(buffer);
  } finally {
    Tone.setContext(prev);
  }
}

export { BAND_CHANNELS, neededKeys };

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
import { BLOCK_BEATS, automationAt, splitBlocks, tempoAt } from "./songSchedule";
import { BAND_CHANNELS, type Arrangement, type BandChannel, type BandMix, type PlayHit } from "./types";

export type PlayOptions = {
  arrangement: Arrangement;
  bpm: number;
  seed: number;
  loop: boolean;
  mix: BandMix;
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
  guitar: "guitar", guitar_mute: "guitar", drums: "drums", perc: "drums",
};

const isSong = (arr: Arrangement) => arr.mode === "song";

/** Nhạc cụ cần tải: thêm nhạc cụ của hook (vd bossa phím điện nhưng hook là piano). */
function neededKeys(arr: Arrangement): string[] {
  const keys = instrumentsFor({ keys: arr.tracks.keys.instrument, bass: arr.tracks.bass.instrument }, true);
  const hook = arr.tracks.hook;
  if (hook && hook.events.length && !keys.includes(hook.instrument)) keys.push(hook.instrument);
  return keys;
}

/** Dựng nhạc cụ cho một bản phối, nối vào bàn trộn. Dùng chung cho phát trực tiếp và thu offline (Tone.Offline). */
export async function buildBand(arr: Arrangement, lite: boolean, useSamples: boolean, mixer: BandMixer) {
  const keys = instrumentsFor({ keys: arr.tracks.keys.instrument, bass: arr.tracks.bass.instrument }, true);
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
  async preload(arr: Arrangement, onProgress?: (p: LoadProgress) => void): Promise<void> {
    await loadInstruments(neededKeys(arr), preferLite(), onProgress);
  }

  private async ensureBand(arr: Arrangement, onProgress?: (p: LoadProgress) => void) {
    const fxKey = JSON.stringify(arr.fx);
    const key = `${arr.style}|${fxKey}|${arr.tracks.keys.instrument}|${arr.tracks.bass.instrument}|${arr.tracks.hook?.instrument ?? "-"}|${arr.tracks.hook?.events.length ? 1 : 0}`;
    if (this.band && this.bandKey === key) return;
    this.disposeBand();
    this.mixer = new BandMixer(arr.fx, Tone.getDestination(), arr.style);
    let useSamples = true;
    try {
      await this.preload(arr, onProgress);
    } catch (e) {
      useSamples = false;
      this.lastError = e instanceof Error ? e.message : String(e);
    }
    this.mode = useSamples ? "sample" : "synth";
    this.band = await buildBand(arr, preferLite(), useSamples, this.mixer);
    const manifest = useSamples ? await loadManifest().catch(() => null) : null;
    this.fx = new SongFx(this.mixer.input("drums"), manifest?.instruments.drums);
    await this.mixer.ready;
    this.bandKey = key;
  }

  setMix(mix: BandMix): void {
    this.mix = mix;
    this.mixer?.applyMix(mix);
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
    await this.ensureBand(o.arrangement, o.onProgress);
    this.setMix(o.mix);
    const arr = o.arrangement;
    const transport = Tone.getTransport();
    this.userBpm = o.bpm;
    transport.bpm.cancelScheduledValues(0);
    transport.bpm.value = o.bpm;
    transport.swing = 0; // swing đã tính trong humanize theo từng phong cách
    const hits = humanize(arr, { seed: o.seed, bpm: o.bpm });
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
 * Thu bản phối thành AudioBuffer (Tone.Offline), chỉ dùng nội bộ để nghe so sánh trước/sau (không cho người dùng xuất).
 * Gọi `loadInstruments` trước để mẫu đã giải nén. Bài hát: thu cả automation, tempo chậm dần, FX chuyển đoạn.
 */
export async function renderOffline(arr: Arrangement, bpm: number, seed: number, seconds: number, mix: BandMix): Promise<Tone.ToneAudioBuffer> {
  return Tone.Offline(async ({ transport }) => {
    const mixer = new BandMixer(arr.fx, Tone.getDestination(), arr.style);
    await mixer.ready;
    mixer.applyMix(mix);
    const band = await buildBand(arr, false, true, mixer);
    transport.bpm.value = bpm;
    scheduleHits(transport, humanize(arr, { seed, bpm }), band);
    if (isSong(arr)) {
      const manifest = await loadManifest();
      const fx = new SongFx(mixer.input("drums"), manifest.instruments.drums);
      mixer.resetAutomation(0);
      scheduleSongExtras(transport, arr, mixer, fx, 0, arr.total_beats + 1, bpm / arr.bpm);
    }
    if (arr.fx.lofi) mixer.setVinyl(true, 0);
    transport.start(0);
  }, seconds, 2);
}

export { BAND_CHANNELS, neededKeys };

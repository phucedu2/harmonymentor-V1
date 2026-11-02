// Phát bản phối bằng ban nhạc mẫu thật (ADR-012 đề xuất). Lịch theo phách trên Transport của Tone.js, nên đổi
// tempo khi đang phát không làm lệch kênh (tài liệu 04 mục 6.8: giây = phách × 60 / BPM, chỉ tính lúc phát).
// Mẫu chưa tải được (lỗi mạng, trình duyệt không giải mã .ogg) → tự dùng synth dự phòng, không im lặng.
import * as Tone from "tone";

import { humanize } from "./humanize";
import { SampledInstrument, SynthInstrument, type BandInstrument } from "./instruments";
import { BandMixer } from "./mixer";
import { instrumentsFor, loadInstruments, loadManifest, preferLite, type LoadProgress } from "./samples";
import { BAND_CHANNELS, type Arrangement, type BandChannel, type BandMix, type PlayHit } from "./types";

export type PlayOptions = {
  arrangement: Arrangement;
  bpm: number;
  seed: number;
  loop: boolean;
  mix: BandMix;
  vinyl?: boolean;
  onBar: (bar: number) => void;
  onEnd: () => void;
  onProgress?: (p: LoadProgress) => void;
};

const CHANNEL_OF: Record<string, BandChannel> = {
  piano: "chords", epiano: "chords", clav: "chords", bass: "bass", upright: "bass",
  guitar: "guitar", guitar_mute: "guitar", drums: "drums", perc: "drums",
};

/** Dựng nhạc cụ cho một bản phối, nối vào bàn trộn. Dùng chung cho phát trực tiếp và thu offline (Tone.Offline). */
export async function buildBand(arr: Arrangement, lite: boolean, useSamples: boolean, mixer: BandMixer) {
  const keys = instrumentsFor({ keys: arr.tracks.keys.instrument, bass: arr.tracks.bass.instrument }, true);
  const manifest = useSamples ? await loadManifest() : null;
  const band = new Map<string, BandInstrument>();
  for (const key of keys) {
    const out = mixer.input(CHANNEL_OF[key]);
    band.set(key, manifest ? new SampledInstrument(key, manifest.instruments[key], lite, out) : new SynthInstrument(key, out));
  }
  return band;
}

/** Xếp lịch mọi nhát lên Transport; trả id để xóa khi dừng. */
export function scheduleHits(transport: ReturnType<typeof Tone.getTransport>, hits: PlayHit[], band: Map<string, BandInstrument>): number[] {
  const ppq = transport.PPQ;
  return hits.map((hit) => transport.schedule((time) => {
    const inst = band.get(hit.instrument);
    // Độ dài tính theo tempo hiện tại lúc phát (người dùng có thể kéo tempo khi đang nghe).
    const durSec = (hit.dur * 60) / transport.bpm.value;
    inst?.play(hit, Math.max(0, time + hit.offset), durSec);
  }, `${Math.round(hit.beat * ppq)}i`));
}

class BandPlayer {
  private mixer: BandMixer | null = null;
  private band: Map<string, BandInstrument> | null = null;
  private bandKey = "";
  private scheduled: number[] = [];
  private mix: BandMix | null = null;
  /** "sample" khi đang dùng mẫu thật, "synth" khi phải dùng synth dự phòng. */
  mode: "sample" | "synth" = "sample";
  lastError: string | null = null;

  /** Tải trước mẫu của phong cách (gọi khi người dùng chọn phong cách) để bấm Phát nghe ngay. */
  async preload(arr: Arrangement, onProgress?: (p: LoadProgress) => void): Promise<void> {
    const keys = instrumentsFor({ keys: arr.tracks.keys.instrument, bass: arr.tracks.bass.instrument }, true);
    await loadInstruments(keys, preferLite(), onProgress);
  }

  private async ensureBand(arr: Arrangement, onProgress?: (p: LoadProgress) => void) {
    const fxKey = JSON.stringify(arr.fx);
    const key = `${arr.style}|${fxKey}|${arr.tracks.keys.instrument}|${arr.tracks.bass.instrument}`;
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
    Tone.getTransport().bpm.value = bpm;
  }

  async play(o: PlayOptions): Promise<void> {
    await Tone.start();
    this.stop();
    await this.ensureBand(o.arrangement, o.onProgress);
    this.setMix(o.mix);
    const arr = o.arrangement;
    const transport = Tone.getTransport();
    transport.bpm.value = o.bpm;
    transport.swing = 0; // swing đã tính trong humanize theo từng phong cách
    transport.position = 0;
    const beatsPerCycle = arr.bars_per_cycle * 4;
    const ppq = transport.PPQ;
    transport.loop = o.loop;
    // Lặp lại thì quay về vòng 2 (vòng 1 là phần mở mộc, QĐ 10A).
    transport.loopStart = `${arr.loop_from_cycle * beatsPerCycle * ppq}i`;
    transport.loopEnd = `${arr.total_beats * ppq}i`;
    const hits = humanize(arr, { seed: o.seed, bpm: o.bpm });
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
    this.mixer?.setVinyl(Boolean(o.vinyl) && arr.fx.lofi);
    transport.start("+0.1");
  }

  stop(): void {
    const transport = Tone.getTransport();
    for (const id of this.scheduled) transport.clear(id);
    this.scheduled = [];
    transport.stop();
    transport.loop = false;
    for (const inst of this.band?.values() ?? []) inst.releaseAll();
    this.mixer?.setVinyl(false);
  }

  private disposeBand(): void {
    for (const inst of this.band?.values() ?? []) inst.dispose();
    this.mixer?.dispose();
    this.band = null;
    this.mixer = null;
  }
}

export const bandPlayer = new BandPlayer();

/**
 * Thu bản phối thành AudioBuffer (Tone.Offline), chỉ dùng nội bộ để nghe so sánh trước/sau (không cho người dùng xuất).
 * Gọi `loadInstruments` trước để mẫu đã giải nén.
 */
export async function renderOffline(arr: Arrangement, bpm: number, seed: number, seconds: number, mix: BandMix): Promise<Tone.ToneAudioBuffer> {
  return Tone.Offline(async ({ transport }) => {
    const mixer = new BandMixer(arr.fx, Tone.getDestination(), arr.style);
    await mixer.ready;
    mixer.applyMix(mix);
    const band = await buildBand(arr, false, true, mixer);
    transport.bpm.value = bpm;
    scheduleHits(transport, humanize(arr, { seed, bpm }), band);
    if (arr.fx.lofi) mixer.setVinyl(true, 0);
    transport.start(0);
  }, seconds, 2);
}

export { BAND_CHANNELS };

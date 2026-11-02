// Thu WAV trước/sau cho docs/backing-track/nghe-thu (nội bộ, không có trong bản build; người dùng không xuất được file).
// "Trước" = lịch phát synth cũ (commit 50604f0, bản sao ở dev/legacy); "sau" = ban nhạc mẫu thật + humanize.
import * as Tone from "tone";

// Gỡ lỗi khi thu: lộ Tone đúng bản mà các module dùng.
(window as unknown as { __Tone: typeof Tone }).__Tone = Tone;

import { renderOffline } from "../src/audio/band/player";
import { instrumentsFor, loadInstruments } from "../src/audio/band/samples";
import { DEFAULT_MIX, type Arrangement } from "../src/audio/band/types";
import { BackingTrackPlayer } from "./legacy/backingTrack";
import { buildSchedule } from "./legacy/trackSchedule";
import oldStyles from "./legacy/old_styles.json";

function wav(buffer: AudioBuffer): ArrayBuffer {
  const ch = buffer.numberOfChannels, n = buffer.length, sr = buffer.sampleRate;
  const out = new ArrayBuffer(44 + n * ch * 2);
  const v = new DataView(out);
  const str = (o: number, s: string) => { for (let i = 0; i < s.length; i += 1) v.setUint8(o + i, s.charCodeAt(i)); };
  str(0, "RIFF"); v.setUint32(4, 36 + n * ch * 2, true); str(8, "WAVE"); str(12, "fmt ");
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, ch, true); v.setUint32(24, sr, true);
  v.setUint32(28, sr * ch * 2, true); v.setUint16(32, ch * 2, true); v.setUint16(34, 16, true); str(36, "data");
  v.setUint32(40, n * ch * 2, true);
  const data = Array.from({ length: ch }, (_, c) => buffer.getChannelData(c));
  let o = 44;
  for (let i = 0; i < n; i += 1) for (let c = 0; c < ch; c += 1) {
    const s = Math.max(-1, Math.min(1, data[c][i]));
    v.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7fff, true); o += 2;
  }
  return out;
}

const b64 = (buf: ArrayBuffer) => {
  const bytes = new Uint8Array(buf); let s = "";
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(s);
};

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`/api/v1${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(`${path} ${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

declare global { interface Window { renderAfter: unknown; renderBefore: unknown } }

window.renderAfter = async (style: string, chords: string[], seed: number, energy: number, bpm: number | null, seconds: number,
  only?: string) => {
  const arr = await post<Arrangement>("/composition/arrangement", { key: "C", style, chords, seed, energy, bpm });
  const t0 = performance.now();
  await loadInstruments(instrumentsFor({ keys: arr.tracks.keys.instrument, bass: arr.tracks.bass.instrument }, true), false);
  const loadMs = performance.now() - t0;
  const useBpm = bpm ?? arr.bpm;
  const len = Math.min(seconds, (arr.total_beats * 60) / useBpm + 2);
  const t1 = performance.now();
  // `only`: thu riêng một kênh (để đo mức từng kênh khi cân mix).
  const mix = only ? Object.fromEntries(Object.entries(DEFAULT_MIX).map(([k, v]) => [k, { ...v, muted: k !== only }])) as typeof DEFAULT_MIX : DEFAULT_MIX;
  const buf = await renderOffline(arr, useBpm, seed, len, mix);
  return { wav: b64(wav(buf.get()!)), bpm: useBpm, loadMs, renderMs: performance.now() - t1, seconds: len, colors: arr.colors };
};

window.renderBefore = async (oldStyle: string, chords: string[], bpm: number | null, seconds: number) => {
  const style = (oldStyles as { id: string; default_bpm: number; swing: number }[]).find((s) => s.id === oldStyle)!;
  const voicings = await post<Record<string, never>>("/composition/voicings", { chords: [...new Set(chords)] });
  const events = buildSchedule(chords.map((c) => voicings[c]), style as never);
  const useBpm = bpm ?? style.default_bpm;
  const buf = await Tone.Offline(async () => {
    const player = new BackingTrackPlayer();
    await player.play({ events, bars: chords.length, bpm: useBpm, swing: style.swing, loop: true, onBar: () => {}, onEnd: () => {} });
  }, seconds, 2);
  return { wav: b64(wav(buf.get()!)), bpm: useBpm, seconds };
};

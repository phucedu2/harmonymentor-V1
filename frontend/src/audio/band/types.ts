// Kiểu dữ liệu bản phối do backend trả về (POST /composition/arrangement, ADR-012 đề xuất).
// Cao độ (midi) do Music Engine dựng ở backend; frontend chỉ lệch phách người (humanize), phát và trộn.

export type BandChannel = "chords" | "bass" | "guitar" | "drums";
export const BAND_CHANNELS: BandChannel[] = ["chords", "bass", "guitar", "drums"];

export type NoteArt = "block" | "roll" | "lh" | "sustain" | "dead" | "pick" | "down" | "up" | "mute" | "palm" | "stab";
export type NoteEvent = { beat: number; dur: number; midi: number[]; vel: number; art: NoteArt };
export type DrumEvent = { beat: number; drum: string; vel: number };

export type Feel = {
  swing: number; // tỷ lệ chia cặp nốt (0 hoặc 0,5 = thẳng; 0,58 = lắc nhẹ; 0,66 = chia ba)
  swing_sub: "8n" | "16n";
  sigma_ms: Record<"drums" | "bass" | "keys" | "guitar", number>;
  pocket_ms: Partial<Record<"kick" | "snare" | "hat" | "ride" | "bass" | "keys" | "guitar", number>>;
  roll_ms: [number, number];
  strum_ms: [number, number];
};

export type StyleFx = { reverb: number; room: "room" | "plate" | "hall"; delay: number; lofi: boolean; chorus: boolean; drive: boolean };

export type Arrangement = {
  version: number; style: string; seed: number; energy: number; bpm: number; grid: number;
  bars_per_cycle: number; cycles: number; loop_from_cycle: number; total_beats: number;
  feel: Feel; fx: StyleFx;
  colors: { bar: number; symbol: string | null; played: string | null }[];
  tracks: {
    keys: { instrument: "piano" | "epiano" | "clav"; events: NoteEvent[] };
    bass: { instrument: "bass" | "upright"; events: NoteEvent[] };
    guitar: { instrument: "guitar"; events: NoteEvent[] };
    drums: { kit: string; events: DrumEvent[] };
  };
};

/** Một nhát đã humanize, sẵn sàng phát: `beat` đã có swing, `offset` (giây) là lệch người, `dur` tính bằng phách. */
export type PlayHit = {
  channel: BandChannel;
  instrument: string; // khóa trong manifest mẫu: piano, epiano, clav, bass, upright, guitar, guitar_mute, drums, perc
  beat: number;
  offset: number;
  dur: number;
  midi: number | null; // null với trống/bộ gõ
  piece: string | null; // mã trống
  vel: number; // 0..1
  art: NoteArt | "hit";
};

export type ChannelMix = { volume: number; muted: boolean };
export type BandMix = Record<BandChannel, ChannelMix>;
export const DEFAULT_MIX: BandMix = {
  chords: { volume: 0.8, muted: false }, bass: { volume: 0.8, muted: false },
  guitar: { volume: 0.8, muted: false }, drums: { volume: 0.8, muted: false },
};

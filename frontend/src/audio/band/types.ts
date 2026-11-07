// Kiểu dữ liệu bản phối do backend trả về (POST /composition/arrangement, ADR-012 đề xuất).
// Cao độ (midi) do Music Engine dựng ở backend; frontend chỉ lệch phách người (humanize), phát và trộn.

export type BandChannel = "chords" | "bass" | "guitar" | "drums" | "hook";
export const BAND_CHANNELS: BandChannel[] = ["chords", "bass", "guitar", "drums", "hook"];

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

// --- chế độ Bài hát (POST /composition/song, ADR-013 đề xuất) ---
export type SectionType = "intro" | "verse" | "pre" | "chorus" | "post" | "bridge" | "breakdown" | "solo" | "outro";
export type TransitionKind = "auto" | "none" | "fill_small" | "fill_big" | "snare_build" | "drop_bar" | "stop_time" | "pickup" | "riser" | "reverse_cymbal";
export type EndingKind = "auto" | "fade" | "ritardando_fermata" | "big_hit" | "tag_x3";
export type SongLength = "short" | "medium" | "full";
export type ProgressionSlot = "A" | "B" | "C";
export type FormSection = {
  id: string; type: SectionType; label: string | null; bars: number; progression: ProgressionSlot; energy: number;
  feel: "auto" | "normal" | "half" | "double"; hook: boolean; transition: TransitionKind; seed: number | null;
};
export type SongForm = {
  length: SongLength; hook: boolean; modulate: { enabled: boolean; semitones: 1 | 2 }; ending: EndingKind;
  progressions: { A: (string | null)[]; B: (string | null)[] | null; C: (string | null)[] | null };
  sections?: FormSection[];
};
export type SongSection = {
  id: string; type: SectionType; label: string; start_beat: number; end_beat: number; bars: number;
  progression: ProgressionSlot; progression_requested: ProgressionSlot; energy: number; design_energy: number;
  feel: string; transition: TransitionKind | null; hook_bars: number; key: string; note_vi: string;
};
/** Tự động hóa: tới `beat` thì đưa `target` tới `value` trong `ramp` phách (0 = đặt ngay). */
export type AutomationPoint = { beat: number; target: "master" | "filter" | "reverb" | "reverb_return"; value: number; ramp: number };
export type TempoPoint = { beat: number; bpm: number; ramp: boolean };
export type FxEvent = { beat: number; kind: "riser" | "reverse_cymbal"; dur: number; gain?: number };

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
    hook?: { instrument: "piano" | "epiano" | "clav" | "guitar"; events: NoteEvent[] };
  };
  // Chỉ có ở chế độ Bài hát:
  mode?: "song";
  key?: string;
  total_bars?: number;
  tail_beats?: number;
  duration_sec?: number;
  sections?: SongSection[];
  automation?: AutomationPoint[];
  tempo_map?: TempoPoint[];
  key_map?: { beat: number; key: string }[];
  fx_events?: FxEvent[];
  surprises?: { beat: number; kind: string; section: string; label_vi: string }[];
  ending?: EndingKind;
  bars?: { bar: number; symbol: string | null; played: string | null; section: number }[];
  suggestions?: Partial<Record<ProgressionSlot, { slot: ProgressionSlot; chords: string[]; numerals: string[]; reason_vi: string }>>;
  form?: SongForm & { sections: FormSection[] };
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
  hook: { volume: 0.8, muted: false },
};

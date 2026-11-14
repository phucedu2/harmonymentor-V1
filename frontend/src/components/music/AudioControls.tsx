import { useEffect, useMemo, useState } from "react";
import { api, type ChordInspection } from "../../api";
import { audioEngine } from "../../audio/AudioEngine";
import { buttonClass } from "../ui/Button";
import { midiToScientific, pitchClassesToAscendingNotes, scientificToMidi } from "../../audio/musicUtils";

export function NoteAudioButton({ notes, label = "Nghe" }: { notes: string[]; label?: string }) {
  const play = async () => {
    // Dynamic lesson spelling may contain E#, Cb, bb or ##. Tone only needs sounding pitch,
    // so convert scientific spellings through MIDI before playback while the UI keeps the
    // pedagogically correct spelling for notation and grading.
    const scientific = notes.every((note) => /\d$/.test(note))
      ? notes.map((note) => {
          const midi = scientificToMidi(note);
          return midi === null ? note : midiToScientific(midi);
        })
      : pitchClassesToAscendingNotes(notes);
    await audioEngine.playChord(scientific, "2n");
  };
  return <button type="button" className={buttonClass("secondary")} onClick={() => void play()}><span aria-hidden="true">▶</span> {label}</button>;
}

export function ProgressionAudio({
  symbols,
  contextKey,
  initialBpm = 80,
}: {
  symbols: string[];
  contextKey?: string;
  initialBpm?: number;
}) {
  const [bpm, setBpm] = useState(initialBpm);
  const [chords, setChords] = useState<ChordInspection[]>([]);
  const [busy, setBusy] = useState(false);
  const [metronome, setMetronome] = useState(false);
  const signature = useMemo(() => symbols.join("|"), [symbols]);

  useEffect(() => {
    let cancelled = false;
    setChords([]);
    void Promise.all(symbols.map((symbol) => api.inspectChord(symbol, contextKey))).then((data) => {
      if (!cancelled) setChords(data);
    }).catch(() => undefined);
    return () => { cancelled = true; };
  }, [signature, contextKey]);

  useEffect(() => () => audioEngine.stopAll(), []);

  const play = async () => {
    if (chords.length !== symbols.length) return;
    setBusy(true);
    try {
      await audioEngine.playProgression(chords.map((chord) => ({ notes: pitchClassesToAscendingNotes(chord.notes, 3), beats: 4 })), bpm);
    } finally {
      setBusy(false);
    }
  };

  const toggleMetronome = async () => {
    if (metronome) {
      audioEngine.stopMetronome();
      setMetronome(false);
    } else {
      await audioEngine.startMetronome(bpm);
      setMetronome(true);
    }
  };

  return <div className="mt-3 flex flex-wrap items-center gap-2">
    <button type="button" className={buttonClass("primary")} onClick={() => void play()} disabled={busy || chords.length !== symbols.length}><span aria-hidden="true">▶</span> Phát vòng hợp âm</button>
    <button type="button" aria-pressed={metronome} className={buttonClass(metronome ? "primary" : "secondary")} onClick={() => void toggleMetronome()}>{metronome ? "■ Dừng máy đếm nhịp" : "♩ Máy đếm nhịp"}</button>
    <label className="inline-flex items-center gap-2 text-sm text-muted">Tốc độ (BPM) <input className="min-h-11 w-20 rounded-lg border border-line bg-surface px-2 text-ink" type="number" min={40} max={180} value={bpm} onChange={(event) => setBpm(Math.max(40, Math.min(180, Number(event.target.value) || 80)))} /></label>
    <button type="button" className={buttonClass("ghost")} onClick={() => { audioEngine.stopAll(); setMetronome(false); }}>Dừng âm thanh</button>
  </div>;
}

export function ChordAudioSet({ symbols, contextKey }: { symbols: string[]; contextKey?: string }) {
  const [chords, setChords] = useState<ChordInspection[]>([]);
  useEffect(() => {
    let cancelled = false;
    void Promise.all(symbols.map((symbol) => api.inspectChord(symbol, contextKey))).then((data) => {
      if (!cancelled) setChords(data);
    }).catch(() => undefined);
    return () => { cancelled = true; };
  }, [symbols.join("|"), contextKey]);

  return <div className="mt-3 flex flex-wrap items-center gap-2">
    {symbols.map((symbol) => {
      const chord = chords.find((item) => item.symbol === symbol);
      return <button
        type="button"
        key={symbol}
        className={buttonClass("secondary")}
        aria-label={`Nghe hợp âm ${symbol}`}
        disabled={!chord}
        onClick={() => chord && void audioEngine.playChord(pitchClassesToAscendingNotes(chord.notes, 3), "2n")}
      >▶ {symbol}</button>;
    })}
  </div>;
}

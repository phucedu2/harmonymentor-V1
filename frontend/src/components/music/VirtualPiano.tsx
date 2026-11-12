import { useMemo, useState } from "react";
import { audioEngine } from "../../audio/AudioEngine";
import { midiToScientific, pianoKeyLabel, pitchClassOf } from "../../audio/musicUtils";

type Props = {
  startMidi?: number;
  endMidi?: number;
  highlightedPitchClasses?: string[];
  incorrectPitchClasses?: string[];
  selectedNotes?: string[];
  onSelectionChange?: (notes: string[]) => void;
  selectionMode?: boolean;
  showLabels?: boolean;
  showOctaveNumbers?: boolean;
};

type PianoKey = { midi: number; note: string; pitchClass: string; black: boolean };

const BLACK_PCS = new Set(["C#", "D#", "F#", "G#", "A#"]);
const ENHARMONIC_LABELS: Record<string, string> = {
  "C#": "C#/Db", "D#": "D#/Eb", "F#": "F#/Gb", "G#": "G#/Ab", "A#": "A#/Bb",
};

export default function VirtualPiano({
  startMidi = 48,
  endMidi = 72,
  highlightedPitchClasses = [],
  incorrectPitchClasses = [],
  selectedNotes: controlledSelected,
  onSelectionChange,
  selectionMode = false,
  showLabels = true,
  showOctaveNumbers = true,
}: Props) {
  const [internalSelected, setInternalSelected] = useState<string[]>([]);
  const selected = controlledSelected ?? internalSelected;
  const highlighted = useMemo(() => new Set(highlightedPitchClasses.map(pitchClassOf)), [highlightedPitchClasses]);
  const incorrect = useMemo(() => new Set(incorrectPitchClasses.map(pitchClassOf)), [incorrectPitchClasses]);
  const keys = useMemo<PianoKey[]>(() => {
    const result: PianoKey[] = [];
    for (let midi = startMidi; midi <= endMidi; midi += 1) {
      const note = midiToScientific(midi);
      const pc = pitchClassOf(note);
      result.push({ midi, note, pitchClass: pc, black: BLACK_PCS.has(pc) });
    }
    return result;
  }, [startMidi, endMidi]);

  const whiteKeys = keys.filter((key) => !key.black);
  const blackKeys = keys.filter((key) => key.black);
  const whiteIndexByMidi = new Map<number, number>();
  whiteKeys.forEach((key, index) => whiteIndexByMidi.set(key.midi, index));

  const setSelected = (next: string[]) => {
    if (!controlledSelected) setInternalSelected(next);
    onSelectionChange?.(next);
  };

  const press = async (key: PianoKey) => {
    await audioEngine.playNote(key.note);
    if (!selectionMode) return;
    const exists = selected.includes(key.note);
    setSelected(exists ? selected.filter((note) => note !== key.note) : [...selected, key.note]);
  };

  const positionBlack = (midi: number) => {
    let previousWhite = midi - 1;
    while (!whiteIndexByMidi.has(previousWhite) && previousWhite >= startMidi) previousWhite -= 1;
    const index = whiteIndexByMidi.get(previousWhite) ?? 0;
    return ((index + 1) / whiteKeys.length) * 100;
  };

  // Phím đúng/sai luôn có thêm dấu ✓/✗ và aria-label, không chỉ đổi màu (WCAG 1.4.1).
  const stateLabel = (active: boolean, target: boolean, wrong: boolean) =>
    [active && "đang chọn", target && "nốt cần tìm", wrong && "nốt sai"].filter(Boolean).join(", ");

  return <div className="mt-4">
    <div className="relative h-36 max-w-[900px] select-none sm:h-48" role="group" aria-label="Bàn phím piano ảo. Bấm phím để nghe nốt.">
      <div className="flex h-full">
        {whiteKeys.map((key) => {
          const active = selected.includes(key.note);
          const target = highlighted.has(key.pitchClass);
          const wrong = incorrect.has(key.pitchClass);
          const state = stateLabel(active, target, wrong);
          return <button
            type="button"
            key={key.note}
            className={`relative h-full flex-1 rounded-b-md border border-r-0 border-ink/40 text-ink transition-colors last:border-r active:translate-y-0.5 ${wrong ? "bg-danger-soft shadow-[inset_0_-6px_0_var(--color-danger)]" : active ? "bg-primary-soft shadow-[inset_0_-6px_0_var(--color-primary)]" : target ? "bg-primary-soft/70" : "bg-surface hover:bg-bg"}`}
            onClick={() => void press(key)}
            aria-pressed={selectionMode ? active : undefined}
            aria-label={`Phím ${key.note}${state ? `, ${state}` : ""}`}
            title={key.note}
          >
            {target && <span aria-hidden="true" className="absolute inset-x-1 top-1 h-1.5 rounded-full" style={{ background: noteColor(key.pitchClass) }} />}
            {(showLabels || wrong || target) && <span aria-hidden="true" className="absolute bottom-2 left-1/2 -translate-x-1/2 font-mono text-[10px]">{wrong ? "✗" : target && !showLabels ? "●" : showOctaveNumbers ? key.note : key.pitchClass}</span>}
          </button>;
        })}
      </div>
      {blackKeys.map((key) => {
        const active = selected.includes(key.note);
        const target = highlighted.has(key.pitchClass);
        const wrong = incorrect.has(key.pitchClass);
        const state = stateLabel(active, target, wrong);
        return <button
          type="button"
          key={key.note}
          className={`absolute top-0 z-10 h-[62%] w-6 rounded-b-md border border-black text-shell-text sm:w-[30px] ${wrong ? "bg-danger shadow-[inset_0_-5px_0_var(--color-danger-soft)]" : active ? "bg-primary shadow-[inset_0_-5px_0_var(--color-signature)]" : target ? "bg-primary-strong" : "bg-shell hover:bg-shell-raised"}`}
          style={{ left: `calc(${positionBlack(key.midi)}% - 13px)` }}
          onClick={() => void press(key)}
          aria-pressed={selectionMode ? active : undefined}
          aria-label={`Phím ${pianoKeyLabel(key.note)}${state ? `, ${state}` : ""}`}
          title={`${key.note} (${ENHARMONIC_LABELS[key.pitchClass] ?? key.pitchClass})`}
        >
          {(showLabels || wrong) && <span aria-hidden="true" className="absolute bottom-2 left-1/2 -translate-x-1/2 -rotate-90 font-mono text-[8px] whitespace-nowrap">{wrong ? "✗" : ENHARMONIC_LABELS[key.pitchClass] ?? key.pitchClass}</span>}
        </button>;
      })}
    </div>
    <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted">
      <span>Bấm phím (hoặc Tab rồi Enter) để nghe nốt.</span>
      {selectionMode && <><span aria-live="polite">Đã chọn: {selected.length ? selected.map(pianoKeyLabel).join(" · ") : "chưa có"}</span><button type="button" className="inline-flex min-h-11 items-center font-semibold text-primary hover:underline" onClick={() => setSelected([])}>Xóa chọn</button></>}
      <small className="basis-full">Phím đen có thể có hai tên, ví dụ C#/Db. Đây là hai cách gọi cho cùng một phím; bài học sẽ giải thích khi nào cần dùng tên nào. Khi bài tập yêu cầu viết tên nốt, hãy trả lời bằng chữ thay vì chỉ dựa vào vị trí phím đàn.</small>
    </div>
  </div>;
}

// Màu nốt theo vòng quãng năm (token --color-note-* trong index.css); chỉ trang trí.
const NOTE_TOKEN: Record<string, string> = {
  C: "c", "C#": "db", D: "d", "D#": "eb", E: "e", F: "f", "F#": "fs", G: "g", "G#": "ab", A: "a", "A#": "bb", B: "b",
};
const noteColor = (pitchClass: string) => `var(--color-note-${NOTE_TOKEN[pitchClass] ?? "c"})`;

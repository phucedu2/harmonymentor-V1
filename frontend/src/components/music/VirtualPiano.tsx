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

  return <div className="virtual-piano-shell">
    <div className="virtual-piano" role="group" aria-label="Bàn phím piano ảo">
      <div className="white-keys">
        {whiteKeys.map((key) => {
          const active = selected.includes(key.note);
          const target = highlighted.has(key.pitchClass);
          const wrong = incorrect.has(key.pitchClass);
          return <button
            type="button"
            key={key.note}
            className={`piano-key white-key ${active ? "selected" : ""} ${target ? "highlighted" : ""} ${wrong ? "incorrect" : ""}`}
            onClick={() => void press(key)}
            aria-pressed={selectionMode ? active : undefined}
            title={key.note}
          >
            {showLabels && <span>{showOctaveNumbers ? key.note : key.pitchClass}</span>}
          </button>;
        })}
      </div>
      {blackKeys.map((key) => {
        const active = selected.includes(key.note);
        const target = highlighted.has(key.pitchClass);
        const wrong = incorrect.has(key.pitchClass);
        return <button
          type="button"
          key={key.note}
          className={`piano-key black-key ${active ? "selected" : ""} ${target ? "highlighted" : ""} ${wrong ? "incorrect" : ""}`}
          style={{ left: `calc(${positionBlack(key.midi)}% - 15px)` }}
          onClick={() => void press(key)}
          aria-pressed={selectionMode ? active : undefined}
          title={`${key.note} (${ENHARMONIC_LABELS[key.pitchClass] ?? key.pitchClass})`}
        >
          {showLabels && <span>{ENHARMONIC_LABELS[key.pitchClass] ?? key.pitchClass}</span>}
        </button>;
      })}
    </div>
    <div className="piano-caption">
      <span>Click/tap để nghe nốt.</span>
      {selectionMode && <><span>Đã chọn: {selected.length ? selected.map(pianoKeyLabel).join(" · ") : "chưa có"}</span><button type="button" className="text-button" onClick={() => setSelected([])}>Xóa chọn</button></>}
      <small>Phím đen có thể có hai tên, ví dụ C#/Db. Đây là hai cách gọi cho cùng một phím; bài học sẽ giải thích khi nào cần dùng tên nào. Khi bài tập yêu cầu viết tên nốt, hãy trả lời bằng chữ thay vì chỉ dựa vào vị trí phím đàn.</small>
    </div>
  </div>;
}

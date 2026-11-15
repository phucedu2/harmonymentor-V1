import { useEffect, useState } from "react";
import { api } from "../../api";
import { progressionLabelSuffix, progressionText } from "../../lib/progressionText";
import { ChordAudioSet, ProgressionAudio } from "../music/AudioControls";
import * as ui from "./lessonStyles";
import { ProgressionInspector } from "./ChordInspector";

const FALLBACK_KEYS = ["C", "G", "D", "A", "E", "B", "F", "Bb", "Eb", "Ab", "Db", "Gb"];

/**
 * Vòng hợp âm của một khối bài học, đổi được sang 12 giọng.
 * Bài khai báo số La Mã (`numerals`) và giọng mặc định; ký hiệu hợp âm luôn do Music Engine tính qua API,
 * nên khối này không bao giờ tự suy ra hợp âm (nguyên tắc bất biến 1).
 */
export default function KeyedProgression({ mode, numerals, defaultKey, prompt, bpm, contextKey }: {
  mode: "progression" | "audio-progression" | "audio-chords";
  numerals: string[];
  defaultKey: string;
  prompt?: string | null;
  bpm: number;
  contextKey?: string;
}) {
  const [key, setKey] = useState(defaultKey);
  const [keys, setKeys] = useState<string[]>(FALLBACK_KEYS);
  const [symbols, setSymbols] = useState<string[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    api.progressionInKey(key, numerals)
      .then((r) => { if (!cancelled) { setSymbols(r.symbols); setKeys(r.keys); } })
      .catch(() => { if (!cancelled) { setSymbols(null); setError("Không tính được vòng hợp âm ở giọng này."); } });
    return () => { cancelled = true; };
  }, [key, numerals.join("|")]);

  const picker = <label className="mt-2 inline-flex items-center gap-2 text-sm text-muted">Giọng
    <select className="min-h-11 rounded-lg border border-line bg-surface px-2 text-ink" value={key} onChange={(e) => setKey(e.target.value)} aria-label="Chọn giọng cho ví dụ">
      {keys.map((k) => <option key={k} value={k}>{k}{k === defaultKey ? " (mặc định của bài)" : ""}</option>)}
    </select>
  </label>;

  return <div>
    {picker}
    {error && <div role="alert" className={ui.resultBad}>{error}</div>}
    {symbols && mode === "progression" && <>
      <ProgressionInspector text={progressionText(symbols, prompt ? progressionLabelSuffix(prompt) : "")} contextKey={key} />
      {symbols.length > 1 && <ProgressionAudio symbols={symbols} contextKey={key} initialBpm={bpm} />}
    </>}
    {symbols && mode === "audio-progression" && symbols.length > 1 && <ProgressionAudio symbols={symbols} contextKey={key} initialBpm={bpm} />}
    {symbols && mode === "audio-chords" && <ChordAudioSet symbols={symbols} contextKey={key} />}
  </div>;
}

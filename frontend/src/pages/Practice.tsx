import { useEffect, useState } from "react";
import { api, splitNotes, type EngineError, type GradeResult, type LearningOverview } from "../api";
// Practice dùng chung piano tương tác với Learn (v0.5.3); Piano.tsx dạng SVG chỉ còn cho trang chủ.
import VirtualPiano from "../components/music/VirtualPiano";

const pick = <T,>(xs: T[]) => xs[Math.floor(Math.random() * xs.length)];

// Đề luyện tập theo mức, bám nội dung đã dạy: người mới chỉ gặp những gì Bài 1 đã giải thích,
// thay vì Ab7 hay m7b5 ngay câu đầu.
type Level = "de" | "vua" | "kho";
type LevelSpec = {
  label: string; note: string;
  roots: string[]; chordSuffixes: string[]; intervals: string[];
  scaleKeys: string[]; scaleTypes: string[]; romanKeys: string[]; romanSevenths: boolean;
};
const WHITE_KEYS = ["C", "D", "E", "F", "G", "A", "B"];
const LEVELS: Record<Level, LevelSpec> = {
  de: {
    label: "Dễ", note: "Nội dung Bài 1: hợp âm trưởng, thứ, giảm trên phím trắng; quãng M3, m3, P5, d5. Âm giai và số La Mã chỉ ở giọng C, G, F (Bài 2 dạy kỹ).",
    roots: WHITE_KEYS, chordSuffixes: ["", "m", "dim"], intervals: ["m3", "M3", "P5", "d5"],
    scaleKeys: ["C", "G", "F"], scaleTypes: ["major"], romanKeys: ["C"], romanSevenths: false,
  },
  vua: {
    label: "Vừa", note: "Thêm nốt gốc có dấu hóa, hợp âm bảy (7, maj7, m7), hợp âm tăng, các quãng trong một quãng tám và âm giai thứ tự nhiên.",
    roots: [...WHITE_KEYS, "Bb", "Eb", "F#", "Ab", "Db"], chordSuffixes: ["", "m", "dim", "aug", "7", "maj7", "m7"],
    intervals: ["m2", "M2", "m3", "M3", "P4", "P5", "d5", "m6", "M6", "m7", "M7", "P8"],
    scaleKeys: ["C", "G", "D", "A", "F", "Bb", "Eb"], scaleTypes: ["major", "natural_minor"], romanKeys: ["C", "G", "F", "D", "Bb"], romanSevenths: true,
  },
  kho: {
    label: "Khó", note: "Đủ 12 nốt gốc, hợp âm m7b5 và dim7, quãng tăng/giảm, 12 giọng trưởng.",
    roots: ["C", "D", "E", "F", "G", "A", "B", "Bb", "Eb", "Ab", "F#", "Db"],
    chordSuffixes: ["", "m", "dim", "aug", "7", "maj7", "m7", "m7b5", "dim7"],
    intervals: ["m2", "M2", "m3", "M3", "P4", "A4", "d5", "P5", "m6", "M6", "m7", "M7", "P8"],
    scaleKeys: ["C", "G", "D", "A", "E", "B", "F#", "F", "Bb", "Eb", "Ab", "Db"], scaleTypes: ["major", "natural_minor"],
    romanKeys: ["C", "G", "D", "A", "E", "B", "F#", "F", "Bb", "Eb", "Ab", "Db"], romanSevenths: true,
  },
};
const LEVEL_KEY = "hm.practice-level";

// Mức mặc định theo bài đã hoàn thành: xong Bài 2 thì Vừa, xong Bài 4 thì Khó.
function suggestedLevel(overview: LearningOverview | null): Level {
  const done = new Set(overview?.lessons.filter((lesson) => lesson.status === "completed").map((lesson) => lesson.lesson_id));
  if (done.has("L04")) return "kho";
  if (done.has("L02")) return "vua";
  return "de";
}

function readLevel(): Level | null {
  try { const value = window.localStorage.getItem(LEVEL_KEY); return value === "de" || value === "vua" || value === "kho" ? value : null; }
  catch { return null; }
}

type Tab = "chord" | "interval" | "scale" | "roman";
const TABS: { id: Tab; label: string }[] = [
  { id: "chord", label: "Dựng hợp âm" },
  { id: "interval", label: "Gọi tên quãng" },
  { id: "scale", label: "Dựng âm giai" },
  { id: "roman", label: "Số La Mã" },
];

export default function PracticePage() {
  const [tab, setTab] = useState<Tab>("chord");
  const [chosen, setChosen] = useState<Level | null>(readLevel);
  const [suggested, setSuggested] = useState<Level>("de");
  useEffect(() => { api.learningOverview().then((overview) => setSuggested(suggestedLevel(overview))).catch(() => undefined); }, []);
  const level = chosen ?? suggested;
  const spec = LEVELS[level];
  const choose = (value: Level) => {
    setChosen(value);
    try { window.localStorage.setItem(LEVEL_KEY, value); } catch { /* không lưu được thì chỉ mất lựa chọn khi tải lại */ }
  };
  return (
    <section>
      <div className="page-heading">
        <div><span className="eyebrow">LUYỆN TẬP</span><h2>Luyện tập nhạc lý</h2></div>
        <p>Câu hỏi ngẫu nhiên, không tính điểm. Làm sai thoải mái: mỗi câu đều có đáp án và lời nhắc vì sao sai.</p>
      </div>
      <div className="level-row" role="group" aria-label="Mức độ">
        <b>Mức độ:</b>
        {(Object.keys(LEVELS) as Level[]).map((value) => (
          <button key={value} type="button" className={level === value ? "on" : "ghost"} aria-pressed={level === value} onClick={() => choose(value)}>
            {LEVELS[value].label}{value === suggested ? " (gợi ý)" : ""}
          </button>
        ))}
      </div>
      <p className="level-note">{spec.note}</p>
      <nav className="tabs" role="tablist" aria-label="Dạng bài tập">
        {TABS.map((t) => (
          <button key={t.id} role="tab" aria-selected={tab === t.id} className={tab === t.id ? "on" : ""}
            onClick={() => setTab(t.id)}>{t.label}</button>
        ))}
      </nav>
      {tab === "chord" && <ChordExercise key={level} spec={spec} />}
      {tab === "interval" && <IntervalExercise key={level} spec={spec} />}
      {tab === "scale" && <ScaleExercise key={level} spec={spec} />}
      {tab === "roman" && <RomanExercise key={level} spec={spec} />}
    </section>
  );
}

function useGrader() {
  const [result, setResult] = useState<GradeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const run = async (fn: () => Promise<GradeResult>) => {
    setBusy(true); setError(null);
    try { setResult(await fn()); }
    catch (e) {
      const err = e as EngineError;
      setResult(null); setError(err.message ? `${err.message}. Hãy dùng tên chữ cái C D E F G A B, thêm # hoặc b cho dấu thăng/giáng.` : "Không kết nối được máy chủ. Hãy thử tải lại trang.");
    } finally { setBusy(false); }
  };
  return { result, error, busy, run, reset: () => { setResult(null); setError(null); } };
}

function Exercise(props: {
  prompt: React.ReactNode; hint: string; placeholder: string;
  onSubmit: (answer: string) => Promise<GradeResult>; onNext: () => void; showPiano?: boolean;
}) {
  const [answer, setAnswer] = useState("");
  const g = useGrader();
  const next = () => { setAnswer(""); g.reset(); props.onNext(); };
  const expected = g.result ? ([] as string[]).concat(g.result.expected) : [];
  return (
    <section className="card exercise-card">
      <div className="prompt">{props.prompt}</div><p className="hint">{props.hint}</p>
      <form onSubmit={(e) => { e.preventDefault(); if (answer.trim()) g.run(() => props.onSubmit(answer)); }}>
        <input value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder={props.placeholder} aria-label="Đáp án" />
        <button type="submit" disabled={g.busy || !answer.trim()}>Kiểm tra</button>
        <button type="button" className="ghost" onClick={next}>Câu khác</button>
      </form>
      {g.error && <div className="result bad">{g.error}</div>}
      {g.result && (
        <div className={`result ${g.result.correct ? "good" : "bad"}`}>
          <strong>{g.result.correct ? "Chính xác!" : "Chưa đúng."}</strong>
          {!g.result.correct && <p>{g.result.message_vi}</p>}
          {!g.result.correct && <p>Đáp án đúng: <b>{expected.join(" ")}</b></p>}
          {g.result.convention_verified === false && <p className="codes">Lưu ý: cách viết ký hiệu này chưa được đối chiếu với tài liệu nguồn.</p>}
        </div>
      )}
      {props.showPiano && g.result && <VirtualPiano highlightedPitchClasses={expected} incorrectPitchClasses={g.result.correct ? [] : splitNotes(answer)} showLabels={false} startMidi={48} endMidi={72} />}
    </section>
  );
}

function ChordExercise({ spec }: { spec: LevelSpec }) {
  const make = () => pick(spec.roots) + pick(spec.chordSuffixes);
  const [symbol, setSymbol] = useState(make);
  return <Exercise prompt={<>Dựng hợp âm <span className="big">{symbol}</span></>}
    hint="Gõ các nốt cách nhau bằng dấu cách, dấu phẩy hoặc gạch ngang. Tên nốt phải đúng chính tả (Ab khác G#)."
    placeholder="ví dụ: G B D F" onSubmit={(a) => api.gradeBuildChord(symbol, splitNotes(a))}
    onNext={() => setSymbol(make())} showPiano />;
}

function IntervalExercise({ spec }: { spec: LevelSpec }) {
  const [question, setQuestion] = useState<{ lower: string; upper: string } | null>(null);
  const make = async () => {
    const lower = pick(spec.roots) + "4";
    const { note } = await api.transpose(lower, pick(spec.intervals));
    setQuestion({ lower, upper: note });
  };
  useEffect(() => { make().catch(() => setQuestion(null)); }, []);
  if (!question) return <section className="card">Đang tải câu hỏi…</section>;
  return <Exercise prompt={<>Quãng đi lên từ <span className="big">{question.lower}</span> tới <span className="big">{question.upper}</span> là gì?</>}
    hint="Viết tính chất + số: P, M, m, A, d. Ví dụ M3, A4, d5." placeholder="ví dụ: M3"
    onSubmit={(a) => api.gradeIdentifyInterval(question.lower, question.upper, a)} onNext={make} />;
}

function ScaleExercise({ spec }: { spec: LevelSpec }) {
  const make = () => ({ tonic: pick(spec.scaleKeys), type: pick(spec.scaleTypes) });
  const [question, setQuestion] = useState(make);
  const label = question.type === "major" ? "trưởng" : "thứ tự nhiên";
  return <Exercise prompt={<>Dựng âm giai <span className="big">{question.tonic} {label}</span></>}
    hint="Viết 7 nốt đi lên, không lặp lại chủ âm. Thứ tự bậc là một phần của đáp án."
    placeholder="ví dụ: D E F# G A B C#" onSubmit={(a) => api.gradeBuildScale(question.tonic, question.type, splitNotes(a))}
    onNext={() => setQuestion(make())} showPiano />;
}

function RomanExercise({ spec }: { spec: LevelSpec }) {
  const [question, setQuestion] = useState<{ key: string; chord: string } | null>(null);
  const make = async () => {
    const key = pick(spec.romanKeys); const chords = await api.diatonic(key, spec.romanSevenths && Math.random() < 0.5);
    setQuestion({ key, chord: pick(chords).chord });
  };
  useEffect(() => { make().catch(() => setQuestion(null)); }, []);
  if (!question) return <section className="card">Đang tải câu hỏi…</section>;
  return <Exercise prompt={<>Trong giọng <span className="big">{question.key} trưởng</span>, hợp âm <span className="big">{question.chord}</span> là bậc nào?</>}
    hint="Chữ hoa = trưởng, chữ thường = thứ, ° = giảm, ø7 = nửa giảm."
    placeholder="ví dụ: ii7" onSubmit={(a) => api.gradeRoman(question.key, question.chord, a)} onNext={make} />;
}

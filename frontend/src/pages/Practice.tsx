import { useEffect, useState } from "react";
import { api, splitNotes, type EngineError, type GradeResult } from "../api";
// Practice dùng chung piano tương tác với Learn (v0.5.3); Piano.tsx dạng SVG chỉ còn cho trang chủ.
import VirtualPiano from "../components/music/VirtualPiano";

const pick = <T,>(xs: T[]) => xs[Math.floor(Math.random() * xs.length)];
const ROOTS = ["C", "D", "E", "F", "G", "A", "B", "Bb", "Eb", "Ab", "F#", "Db"];
const CHORD_SUFFIXES = ["", "m", "dim", "aug", "7", "maj7", "m7", "m7b5", "dim7"];
const INTERVALS = ["m2", "M2", "m3", "M3", "P4", "A4", "d5", "P5", "m6", "M6", "m7", "M7", "P8"];
const MAJOR_KEYS = ["C", "G", "D", "A", "E", "B", "F#", "F", "Bb", "Eb", "Ab", "Db"];

type Tab = "chord" | "interval" | "scale" | "roman";
const TABS: { id: Tab; label: string }[] = [
  { id: "chord", label: "Dựng hợp âm" },
  { id: "interval", label: "Gọi tên quãng" },
  { id: "scale", label: "Dựng âm giai" },
  { id: "roman", label: "Số La Mã" },
];

export default function PracticePage() {
  const [tab, setTab] = useState<Tab>("chord");
  return (
    <section>
      <div className="page-heading">
        <div><span className="eyebrow">PRACTICE</span><h2>Luyện tập nhạc lý</h2></div>
        <p>Giữ lại 4 dạng bài của prototype v0.1.0 trong khu vực Practice.</p>
      </div>
      <nav className="tabs" role="tablist" aria-label="Dạng bài tập">
        {TABS.map((t) => (
          <button key={t.id} role="tab" aria-selected={tab === t.id} className={tab === t.id ? "on" : ""}
            onClick={() => setTab(t.id)}>{t.label}</button>
        ))}
      </nav>
      {tab === "chord" && <ChordExercise />}
      {tab === "interval" && <IntervalExercise />}
      {tab === "scale" && <ScaleExercise />}
      {tab === "roman" && <RomanExercise />}
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
      setResult(null); setError(err.message ?? "Không gọi được backend. Bạn đã chạy uvicorn chưa?");
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
          {g.result.errors.length > 0 && <p className="codes">Mã lỗi: {[...new Set(g.result.errors.map((e) => e.code + (e.proposed ? " (đề xuất)" : "")))].join(", ")}</p>}
          {g.result.convention_verified === false && <p className="codes">Lưu ý: cách viết ký hiệu này chưa có nguồn xác minh.</p>}
        </div>
      )}
      {props.showPiano && g.result && <VirtualPiano highlightedPitchClasses={expected} incorrectPitchClasses={g.result.correct ? [] : splitNotes(answer)} showLabels={false} startMidi={48} endMidi={72} />}
    </section>
  );
}

function ChordExercise() {
  const make = () => pick(ROOTS) + pick(CHORD_SUFFIXES);
  const [symbol, setSymbol] = useState(make);
  return <Exercise prompt={<>Dựng hợp âm <span className="big">{symbol}</span></>}
    hint="Gõ các nốt cách nhau bằng dấu cách. Tên nốt phải đúng chính tả (Ab khác G#)."
    placeholder="ví dụ: G B D F" onSubmit={(a) => api.gradeBuildChord(symbol, splitNotes(a))}
    onNext={() => setSymbol(make())} showPiano />;
}

function IntervalExercise() {
  const [question, setQuestion] = useState<{ lower: string; upper: string } | null>(null);
  const make = async () => {
    const lower = pick(ROOTS) + "4";
    const { note } = await api.transpose(lower, pick(INTERVALS));
    setQuestion({ lower, upper: note });
  };
  useEffect(() => { make().catch(() => setQuestion(null)); }, []);
  if (!question) return <section className="card">Đang tải câu hỏi… (cần chạy backend)</section>;
  return <Exercise prompt={<>Quãng đi lên từ <span className="big">{question.lower}</span> tới <span className="big">{question.upper}</span> là gì?</>}
    hint="Viết tính chất + số: P, M, m, A, d. Ví dụ M3, A4, d5." placeholder="ví dụ: M3"
    onSubmit={(a) => api.gradeIdentifyInterval(question.lower, question.upper, a)} onNext={make} />;
}

function ScaleExercise() {
  const make = () => ({ tonic: pick(MAJOR_KEYS), type: pick(["major", "natural_minor"]) });
  const [question, setQuestion] = useState(make);
  const label = question.type === "major" ? "trưởng" : "thứ tự nhiên";
  return <Exercise prompt={<>Dựng âm giai <span className="big">{question.tonic} {label}</span></>}
    hint="Viết 7 nốt đi lên, không lặp lại chủ âm. Thứ tự bậc là một phần của đáp án."
    placeholder="ví dụ: D E F# G A B C#" onSubmit={(a) => api.gradeBuildScale(question.tonic, question.type, splitNotes(a))}
    onNext={() => setQuestion(make())} showPiano />;
}

function RomanExercise() {
  const [question, setQuestion] = useState<{ key: string; chord: string } | null>(null);
  const make = async () => {
    const key = pick(MAJOR_KEYS); const chords = await api.diatonic(key, Math.random() < 0.5);
    setQuestion({ key, chord: pick(chords).chord });
  };
  useEffect(() => { make().catch(() => setQuestion(null)); }, []);
  if (!question) return <section className="card">Đang tải câu hỏi… (cần chạy backend)</section>;
  return <Exercise prompt={<>Trong giọng <span className="big">{question.key} trưởng</span>, hợp âm <span className="big">{question.chord}</span> là bậc nào?</>}
    hint="Chữ hoa = trưởng, chữ thường = thứ, ° = giảm, ø7 = nửa giảm."
    placeholder="ví dụ: ii7" onSubmit={(a) => api.gradeRoman(question.key, question.chord, a)} onNext={make} />;
}

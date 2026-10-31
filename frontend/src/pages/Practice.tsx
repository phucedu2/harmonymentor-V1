import { useCallback, useEffect, useState } from "react";
import {
  api, splitNotes, type EngineError, type LearningOverview, type PracticeAttemptResult, type PracticeHistory,
  type PracticeHistoryItem, type PracticeKind, type PracticeLevel,
} from "../api";
// Practice dùng chung piano tương tác với Learn (v0.5.3); Piano.tsx dạng SVG chỉ còn cho trang chủ.
import VirtualPiano from "../components/music/VirtualPiano";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Badge, Card, CardTitle, PageHeading, ResultBox, ToggleGroup } from "../components/ui/Page";

const pick = <T,>(xs: T[]) => xs[Math.floor(Math.random() * xs.length)];

// Đề luyện tập theo mức, bám nội dung đã dạy: người mới chỉ gặp những gì Bài 1 đã giải thích,
// thay vì Ab7 hay m7b5 ngay câu đầu.
type Level = PracticeLevel;
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

type Tab = PracticeKind;
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
  // Sau mỗi lượt nộp, tải lại lịch sử để người học thấy lượt vừa làm đã được ghi.
  const [history, setHistory] = useState<PracticeHistory | null>(null);
  const [historyError, setHistoryError] = useState(false);
  const refreshHistory = useCallback(() => {
    api.practiceHistory(10).then((data) => { setHistory(data); setHistoryError(false); }).catch(() => setHistoryError(true));
  }, []);
  useEffect(refreshHistory, [refreshHistory]);
  const ctx: ExerciseContext = { spec, level, onRecorded: refreshHistory };
  const choose = (value: Level) => {
    setChosen(value);
    try { window.localStorage.setItem(LEVEL_KEY, value); } catch { /* không lưu được thì chỉ mất lựa chọn khi tải lại */ }
  };
  return (
    <section>
      <PageHeading eyebrow="Luyện tập" title="Luyện tập nhạc lý">
        Câu hỏi ngẫu nhiên, máy chấm bằng Music Engine. Mỗi lượt được ghi vào lịch sử của bạn nhưng chưa tính vào mức thành thạo, nên cứ làm sai thoải mái.
      </PageHeading>
      <div className="mb-2 flex flex-wrap items-center gap-3">
        <span id="muc-do" className="text-sm font-semibold text-ink">Mức độ</span>
        <ToggleGroup label="Mức độ" value={level} onChange={choose}
          options={(Object.keys(LEVELS) as Level[]).map((value) => ({ value, label: `${LEVELS[value].label}${value === suggested ? " (gợi ý)" : ""}` }))} />
      </div>
      <p className="mb-4 text-sm text-muted">{spec.note}</p>
      <ToggleGroup className="mb-4" label="Dạng bài tập" value={tab} onChange={setTab} options={TABS.map((t) => ({ value: t.id, label: t.label }))} />
      {tab === "chord" && <ChordExercise key={level} {...ctx} />}
      {tab === "interval" && <IntervalExercise key={level} {...ctx} />}
      {tab === "scale" && <ScaleExercise key={level} {...ctx} />}
      {tab === "roman" && <RomanExercise key={level} {...ctx} />}
      <PracticeHistoryPanel history={history} failed={historyError} />
    </section>
  );
}

type ExerciseContext = { spec: LevelSpec; level: Level; onRecorded: () => void };

function useGrader() {
  const [result, setResult] = useState<PracticeAttemptResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const run = async (fn: () => Promise<PracticeAttemptResult>) => {
    setBusy(true); setError(null);
    try { setResult(await fn()); }
    catch (e) {
      const err = e as EngineError;
      setResult(null); setError(err.message ? `${err.message}. Hãy dùng tên chữ cái C D E F G A B, thêm # hoặc b cho dấu thăng/giáng.` : "Không kết nối được máy chủ. Hãy thử tải lại trang.");
    } finally { setBusy(false); }
  };
  return { result, error, busy, run, reset: () => { setResult(null); setError(null); } };
}

// Mỗi dạng bài chỉ sinh đề; chấm và ghi lịch sử luôn qua POST /practice/attempts.
function Exercise(props: {
  prompt: React.ReactNode; hint: string; placeholder: string; kind: PracticeKind; ctx: ExerciseContext;
  question: Record<string, string>; listAnswer?: boolean; onNext: () => void; showPiano?: boolean;
}) {
  const [answer, setAnswer] = useState("");
  const g = useGrader();
  const next = () => { setAnswer(""); g.reset(); props.onNext(); };
  const expected = g.result ? ([] as string[]).concat(g.result.expected) : [];
  const submit = async () => {
    const res = await api.practiceAttempt(props.kind, props.ctx.level, props.question, props.listAnswer ? splitNotes(answer) : answer.trim());
    props.ctx.onRecorded();
    return res;
  };
  return (
    <Card className="max-w-3xl">
      <p className="text-xl leading-snug text-ink">{props.prompt}</p><p className="mt-2 text-sm text-muted">{props.hint}</p>
      <form className="mt-4 flex flex-wrap gap-2" onSubmit={(e) => { e.preventDefault(); if (answer.trim()) g.run(submit); }}>
        <input className="min-h-11 min-w-0 flex-[1_1_14rem] rounded-lg border border-line bg-surface px-3 font-mono text-base text-ink placeholder:text-muted" value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder={props.placeholder} aria-label="Đáp án" />
        <Button type="submit" disabled={g.busy || !answer.trim()}>Kiểm tra</Button>
        <Button type="button" variant="secondary" onClick={next}>Câu khác</Button>
      </form>
      {g.error && <div className="mt-3"><Alert tone="danger">{g.error}</Alert></div>}
      {g.result && (
        <ResultBox correct={g.result.correct}>
          {!g.result.correct && <p>{g.result.message_vi}</p>}
          {!g.result.correct && <p>Đáp án đúng: <b className="font-mono">{expected.join(" ")}</b></p>}
          {g.result.convention_verified === false && <p className="text-xs text-muted">Lưu ý: cách viết ký hiệu này chưa được đối chiếu với tài liệu nguồn.</p>}
        </ResultBox>
      )}
      {props.showPiano && g.result && <VirtualPiano highlightedPitchClasses={expected} incorrectPitchClasses={g.result.correct ? [] : splitNotes(answer)} showLabels={false} startMidi={48} endMidi={72} />}
    </Card>
  );
}

function ChordExercise(ctx: ExerciseContext) {
  const { spec } = ctx;
  const make = () => pick(spec.roots) + pick(spec.chordSuffixes);
  const [symbol, setSymbol] = useState(make);
  return <Exercise prompt={<>Dựng hợp âm <span className="font-mono font-semibold text-primary">{symbol}</span></>}
    hint="Gõ các nốt cách nhau bằng dấu cách, dấu phẩy hoặc gạch ngang. Tên nốt phải đúng chính tả (Ab khác G#)."
    placeholder="ví dụ: G B D F" kind="chord" ctx={ctx} question={{ symbol }} listAnswer
    onNext={() => setSymbol(make())} showPiano />;
}

function IntervalExercise(ctx: ExerciseContext) {
  const { spec } = ctx;
  const [question, setQuestion] = useState<{ lower: string; upper: string } | null>(null);
  const make = async () => {
    const lower = pick(spec.roots) + "4";
    const { note } = await api.transpose(lower, pick(spec.intervals));
    setQuestion({ lower, upper: note });
  };
  useEffect(() => { make().catch(() => setQuestion(null)); }, []);
  if (!question) return <Card className="text-muted">Đang tải câu hỏi…</Card>;
  return <Exercise prompt={<>Quãng đi lên từ <span className="font-mono font-semibold text-primary">{question.lower}</span> tới <span className="font-mono font-semibold text-primary">{question.upper}</span> là gì?</>}
    hint="Viết tính chất + số: P, M, m, A, d. Ví dụ M3, A4, d5." placeholder="ví dụ: M3"
    kind="interval" ctx={ctx} question={question} onNext={make} />;
}

function ScaleExercise(ctx: ExerciseContext) {
  const { spec } = ctx;
  const make = () => ({ tonic: pick(spec.scaleKeys), type: pick(spec.scaleTypes) });
  const [question, setQuestion] = useState(make);
  const label = question.type === "major" ? "trưởng" : "thứ tự nhiên";
  return <Exercise prompt={<>Dựng âm giai <span className="font-mono font-semibold text-primary">{question.tonic} {label}</span></>}
    hint="Viết 7 nốt đi lên, không lặp lại chủ âm. Thứ tự bậc là một phần của đáp án."
    placeholder="ví dụ: D E F# G A B C#" kind="scale" ctx={ctx}
    question={{ tonic: question.tonic, scale_type: question.type }} listAnswer
    onNext={() => setQuestion(make())} showPiano />;
}

function RomanExercise(ctx: ExerciseContext) {
  const { spec } = ctx;
  const [question, setQuestion] = useState<{ key: string; chord: string } | null>(null);
  const make = async () => {
    const key = pick(spec.romanKeys); const chords = await api.diatonic(key, spec.romanSevenths && Math.random() < 0.5);
    setQuestion({ key, chord: pick(chords).chord });
  };
  useEffect(() => { make().catch(() => setQuestion(null)); }, []);
  if (!question) return <Card className="text-muted">Đang tải câu hỏi…</Card>;
  return <Exercise prompt={<>Trong giọng <span className="font-mono font-semibold text-primary">{question.key} trưởng</span>, hợp âm <span className="font-mono font-semibold text-primary">{question.chord}</span> là bậc nào?</>}
    hint="Chữ hoa = trưởng, chữ thường = thứ, ° = giảm, ø7 = nửa giảm."
    placeholder="ví dụ: ii7" kind="roman" ctx={ctx} question={question} onNext={make} />;
}

const KIND_LABEL: Record<PracticeKind, string> = { chord: "Hợp âm", interval: "Quãng", scale: "Âm giai", roman: "Số La Mã" };

// Tóm tắt đề để đọc lại trong lịch sử; chỉ ghép chữ, không tính nhạc lý.
function describeQuestion(item: PracticeHistoryItem): string {
  const q = item.question;
  if (item.kind === "chord") return `Dựng ${q.symbol}`;
  if (item.kind === "interval") return `${q.lower} → ${q.upper}`;
  if (item.kind === "scale") return `${q.tonic} ${q.scale_type === "major" ? "trưởng" : "thứ tự nhiên"}`;
  return `${q.chord} trong ${q.key} trưởng`;
}

function PracticeHistoryPanel({ history, failed }: { history: PracticeHistory | null; failed: boolean }) {
  return (
    <Card className="mt-6" aria-labelledby="practice-history-title">
      <CardTitle><span id="practice-history-title">Lịch sử luyện tập</span></CardTitle>
      {failed && <p className="mt-2 text-sm text-muted">Chưa tải được lịch sử. Lượt làm vẫn được chấm; hãy tải lại trang sau.</p>}
      {!failed && !history && <p className="mt-2 text-sm text-muted">Đang tải lịch sử…</p>}
      {history && history.stats.length === 0 && <p className="mt-2 text-sm text-muted">Chưa có lượt nào. Làm thử một câu ở trên nhé.</p>}
      {history && history.stats.length > 0 && (
        <>
          <ul className="mt-3 flex flex-wrap gap-2">
            {history.stats.map((stat) => (
              <li key={stat.kind}><Badge tone="muted">{KIND_LABEL[stat.kind]}: {stat.correct}/{stat.attempts} đúng</Badge></li>
            ))}
          </ul>
          <ol className="mt-3 grid gap-1.5 text-sm">
            {history.items.map((item) => (
              <li key={item.id} className={`rounded-lg border-l-4 bg-bg px-3 py-2 text-ink ${item.correct ? "border-success" : "border-danger"}`}>
                <span aria-hidden="true" className={item.correct ? "text-success" : "text-danger"}>{item.correct ? "✓" : "✗"}</span>
                <span className="sr-only">{item.correct ? "Đúng" : "Sai"}:</span>
                {" "}{KIND_LABEL[item.kind]} · {describeQuestion(item)} · bạn trả lời <b className="font-mono">{([] as string[]).concat(item.answer).join(" ")}</b>
              </li>
            ))}
          </ol>
          <p className="mt-3 text-sm text-muted">Thống kê tính trên toàn bộ lượt làm; danh sách hiện 10 lượt gần nhất.</p>
        </>
      )}
    </Card>
  );
}

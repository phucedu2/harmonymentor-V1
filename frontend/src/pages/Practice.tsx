import { useCallback, useEffect, useState } from "react";
import {
  api, splitNotes, type AttemptResult, type BankQuestion, type EngineError, type LearningOverview, type PracticeAttemptResult,
  type PracticeHistory, type PracticeHistoryItem, type PracticeKind, type PracticeLevel,
} from "../api";
import { ChoiceList, OpenAnswer } from "../components/learning/AnswerInputs";
// Practice dùng chung piano tương tác với Learn (v0.5.3); Piano.tsx dạng SVG chỉ còn cho trang chủ.
import VirtualPiano from "../components/music/VirtualPiano";
import MicNoteInput from "../components/music/MicNoteInput";
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

// Mức mặc định theo bài đã hoàn thành: xong L02 thì Vừa, xong L03 thì Khó. Mức Khó chỉ dùng kiến thức
// L01–L02 ở mọi giọng nên không chờ L04 (ii–V–I đã dời xuống M4 Jazz theo SRS Bảng 7).
function suggestedLevel(overview: LearningOverview | null): Level {
  const done = new Set(overview?.lessons.filter((lesson) => lesson.status === "completed").map((lesson) => lesson.lesson_id));
  if (done.has("L03")) return "kho";
  if (done.has("L02")) return "vua";
  return "de";
}

function readLevel(): Level | null {
  try { const value = window.localStorage.getItem(LEVEL_KEY); return value === "de" || value === "vua" || value === "kho" ? value : null; }
  catch { return null; }
}

type Tab = PracticeKind | "bank";
const TABS: { id: Tab; label: string }[] = [
  { id: "chord", label: "Dựng hợp âm" },
  { id: "interval", label: "Gọi tên quãng" },
  { id: "scale", label: "Dựng âm giai" },
  { id: "roman", label: "Số La Mã" },
  { id: "bank", label: "Từ tài liệu" },
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
      {tab === "bank" && <BankPractice key={level} level={level} />}
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
  // GĐ5: hợp âm và âm giai trả lời được bằng cách bấm piano; máy chủ chấm theo phím (lớp cao độ) rồi nhắc cách viết.
  // ADR-028: "Trắc nghiệm" = chọn 1 trong 4 phương án do Music Engine sinh (lỗi hay gặp); chấm vẫn bằng đúng hàm Engine.
  // ADR-031: "micro" = đàn/hát từng nốt, chấm theo cao độ giống bấm phím.
  const [mode, setMode] = useState<"text" | "piano" | "choice" | "micro">("text");
  const [keys, setKeys] = useState<string[]>([]);
  const [options, setOptions] = useState<string[] | null>(null);
  const [picked, setPicked] = useState<string[]>([]);
  const piano = props.showPiano && mode === "piano";
  const mic = props.showPiano && mode === "micro";
  const [micNotes, setMicNotes] = useState<string[]>([]);
  const choosing = mode === "choice";
  const g = useGrader();
  const questionKey = JSON.stringify(props.question);
  useEffect(() => {
    if (!choosing) return;
    let live = true;
    setOptions(null); setPicked([]);
    api.practiceOptions(props.kind, props.question).then((r) => { if (live) setOptions(r.options); })
      .catch(() => { if (live) setOptions([]); });
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [choosing, questionKey, props.kind]);
  const next = () => { setAnswer(""); setKeys([]); setMicNotes([]); setPicked([]); g.reset(); props.onNext(); };
  const expected = g.result ? ([] as string[]).concat(g.result.expected) : [];
  const given = piano ? keys : mic ? micNotes : choosing ? splitNotes(picked[0] ?? "") : splitNotes(answer);
  const submit = async () => {
    const chosen = picked[0] ?? "";
    const res = piano
      ? await api.practiceAttempt(props.kind, props.ctx.level, props.question, keys, "piano")
      : mic
      ? await api.practiceAttempt(props.kind, props.ctx.level, props.question, micNotes, "micro")
      : choosing
      ? await api.practiceAttempt(props.kind, props.ctx.level, props.question, props.listAnswer ? splitNotes(chosen) : chosen, "choice")
      : await api.practiceAttempt(props.kind, props.ctx.level, props.question, props.listAnswer ? splitNotes(answer) : answer.trim());
    props.ctx.onRecorded();
    return res;
  };
  const ready = piano ? keys.length > 0 : mic ? micNotes.length > 0 : choosing ? picked.length > 0 : Boolean(answer.trim());
  const modes = [{ value: "text" as const, label: props.showPiano ? "Gõ tên nốt" : "Gõ đáp án" }, { value: "choice" as const, label: "Trắc nghiệm" },
    ...(props.showPiano ? [{ value: "piano" as const, label: "Bấm piano" }, { value: "micro" as const, label: "Đàn bằng micro" }] : [])];
  return (
    <Card className="max-w-3xl">
      <p className="text-xl leading-snug text-ink">{props.prompt}</p>
      <p className="mt-2 text-sm text-muted">{mic ? (props.kind === "scale"
        ? "Đàn hoặc hát lần lượt 7 nốt đi lên, mỗi nốt giữ khoảng nửa giây. Máy chấm theo cao độ, rồi nhắc cách viết tên nốt chuẩn."
        : "Đàn từng nốt của hợp âm (rải từng nốt, không đánh cùng lúc), thứ tự nào cũng được. Máy chấm theo cao độ.") : choosing ? "Chọn một phương án. Các phương án sai là lỗi người học hay mắc, đọc kỹ chính tả tên nốt." : piano ? (props.kind === "scale"
        ? "Bấm lần lượt 7 phím đi lên theo thứ tự bậc. Máy chấm theo phím, rồi nhắc bạn cách viết tên nốt chuẩn."
        : "Bấm các phím của hợp âm (thứ tự nào cũng được). Máy chấm theo phím, rồi nhắc bạn cách viết tên nốt chuẩn.") : props.hint}</p>
      <ToggleGroup className="mt-3" label="Cách trả lời" value={mode} onChange={(v) => { setMode(v); g.reset(); }} options={modes} />
      {mic && <MicNoteInput notes={micNotes} onChange={setMicNotes} disabled={Boolean(g.result)}
        highlighted={g.result ? expected : []} incorrect={g.result && !g.result.correct ? given : []} />}
      {piano && <VirtualPiano selectionMode selectedNotes={keys} onSelectionChange={setKeys} showLabels={false} startMidi={48} endMidi={72}
        highlightedPitchClasses={g.result ? expected : []} incorrectPitchClasses={g.result && !g.result.correct ? given : []} />}
      <form className="mt-4 flex flex-wrap gap-2" onSubmit={(e) => { e.preventDefault(); if (ready) g.run(submit); }}>
        {choosing && <div className="w-full">{options === null ? <p className="text-sm text-muted">Đang tạo phương án…</p>
          : options.length === 0 ? <p className="text-sm text-muted">Chưa tạo được phương án cho đề này, bấm “Câu khác”.</p>
          : <ChoiceList options={options} value={picked} onChange={setPicked} disabled={Boolean(g.result)} label="Các phương án" />}</div>}
        {!piano && !mic && !choosing && <input className="min-h-11 min-w-0 flex-[1_1_14rem] rounded-lg border border-line bg-surface px-3 font-mono text-base text-ink placeholder:text-muted" value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder={props.placeholder} aria-label="Đáp án" />}
        <Button type="submit" disabled={g.busy || !ready}>Kiểm tra</Button>
        <Button type="button" variant="secondary" onClick={next}>Câu khác</Button>
      </form>
      {g.error && <div className="mt-3"><Alert tone="danger">{g.error}</Alert></div>}
      {g.result && (
        <ResultBox correct={g.result.correct}>
          {(!g.result.correct || piano || mic) && <p>{g.result.message_vi}</p>}
          {!g.result.correct && <p>Đáp án đúng: <b className="font-mono">{expected.join(" ")}</b></p>}
          {g.result.convention_verified === false && <p className="text-xs text-muted">Lưu ý: cách viết ký hiệu này chưa được đối chiếu với tài liệu nguồn.</p>}
        </ResultBox>
      )}
      {props.showPiano && !piano && !mic && g.result && <VirtualPiano highlightedPitchClasses={expected} incorrectPitchClasses={g.result.correct ? [] : given} showLabels={false} startMidi={48} endMidi={72} />}
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

const BANK_KIND: Record<string, string> = {
  mcq: "Trắc nghiệm", true_false: "Đúng hay sai", multi_select: "Chọn nhiều đáp án", short: "Tự luận ngắn", build: "Tự dựng", open: "Tự luận mở",
};

// ADR-028 (1B): câu AI soạn từ tài liệu, Quản trị viên đã duyệt. Câu chấm tất định đi qua /attempts nên tính mức thành thạo;
// câu tự luận mở chỉ để tự luyện (đáp án mẫu + nhận xét AI), không tính.
function BankPractice({ level }: { level: Level }) {
  const [skills, setSkills] = useState<{ skill_id: string; name: string; count: number }[] | null>(null);
  const [skill, setSkill] = useState<string>("");
  const [set, setSet] = useState<BankQuestion[] | null>(null);
  const [index, setIndex] = useState(0);
  const [failed, setFailed] = useState(false);
  useEffect(() => { api.bankSkills().then((r) => setSkills(r.skills)).catch(() => setFailed(true)); }, []);
  const load = useCallback(() => {
    setSet(null); setIndex(0);
    api.bank(skill || null, level).then((r) => setSet(r.questions)).catch(() => setFailed(true));
  }, [skill, level]);
  useEffect(load, [load]);
  if (failed) return <Card className="max-w-3xl text-muted">Chưa tải được câu hỏi từ tài liệu. Hãy tải lại trang sau.</Card>;
  if (!skills) return <Card className="max-w-3xl text-muted">Đang tải…</Card>;
  if (skills.length === 0) return <Card className="max-w-3xl"><p className="text-ink">Chưa có câu luyện tập nào từ tài liệu.</p>
    <p className="mt-1 text-sm text-muted">Câu ở đây do AI soạn từ tài liệu nhạc lý và được Quản trị viên duyệt trước khi xuất bản.</p></Card>;
  const q = set?.[index];
  return <div className="grid max-w-3xl gap-3">
    <label className="flex flex-wrap items-center gap-2 text-sm font-semibold text-ink">Kỹ năng
      <select value={skill} onChange={(e) => setSkill(e.target.value)} className="min-h-10 rounded-lg border border-line bg-surface px-2 font-normal">
        <option value="">Tất cả kỹ năng</option>
        {skills.map((s) => <option key={s.skill_id} value={s.skill_id}>{s.name} ({s.count} câu)</option>)}
      </select></label>
    <p className="text-sm text-muted">Mức độ đang chọn ứng với: Dễ = nhớ khái niệm, Vừa = hiểu, Khó = vận dụng. Câu chấm được tính vào mức thành thạo của kỹ năng.</p>
    {!set && <Card className="text-muted">Đang tải câu hỏi…</Card>}
    {set && set.length === 0 && <Card className="text-muted">Kỹ năng này chưa có câu.</Card>}
    {set && q && <BankQuestionCard key={q.exercise_version_id} q={q} n={index + 1} total={set.length}
      onNext={() => (index + 1 < set.length ? setIndex(index + 1) : load())} last={index + 1 >= set.length} />}
  </div>;
}

function BankQuestionCard({ q, n, total, onNext, last }: { q: BankQuestion; n: number; total: number; onNext: () => void; last: boolean }) {
  const multi = Boolean(q.allowed_input_methods?.includes("multi_choice"));
  const [picked, setPicked] = useState<string[]>([]);
  const [text, setText] = useState("");
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const ready = q.options?.length ? picked.length > 0 : Boolean(text.trim());
  const submit = async () => {
    setBusy(true); setError(null);
    try {
      setResult(q.options?.length
        ? await api.submitAttempt(q.exercise_version_id, multi ? picked : picked[0], multi ? "multi_choice" : "choice")
        : await api.submitAttempt(q.exercise_version_id, text.trim(), "text"));
    } catch (e) { setError((e as { message?: string }).message ?? "Chưa nộp được, thử lại."); }
    finally { setBusy(false); }
  };
  return <Card>
    <p className="text-xs font-semibold tracking-wide text-muted uppercase">Câu {n}/{total} · {BANK_KIND[q.kind] ?? q.kind}</p>
    <p className="mt-1 text-lg leading-snug text-ink">{q.prompt}</p>
    <div className="mt-3">
      {q.open ? <OpenAnswer versionId={q.exercise_version_id} label={`Câu trả lời: ${q.prompt}`} />
        : q.options?.length ? <ChoiceList options={q.options} multi={multi} value={picked} onChange={setPicked} disabled={Boolean(result)} label="Các phương án" />
        : <input value={text} onChange={(e) => setText(e.target.value)} disabled={Boolean(result)} aria-label={`Câu trả lời: ${q.prompt}`}
            placeholder="Gõ đáp án" className="min-h-11 w-full rounded-lg border border-line bg-surface px-3 font-mono text-base text-ink" />}
    </div>
    <div className="mt-3 flex flex-wrap gap-2">
      {!q.open && !result && <Button disabled={busy || !ready} loading={busy} onClick={submit}>Kiểm tra</Button>}
      {(q.open || result) && <Button variant={q.open && !result ? "secondary" : "primary"} onClick={onNext}>{last ? "Làm bộ câu khác" : "Câu tiếp theo"}</Button>}
    </div>
    {error && <div className="mt-3"><Alert tone="danger">{error}</Alert></div>}
    {result && <ResultBox correct={result.correct}>
      {!result.correct && result.feedback && <p>{result.feedback}</p>}
      {result.explanation && <p className="mt-1">{result.explanation}</p>}
    </ResultBox>}
  </Card>;
}

const KIND_LABEL: Record<PracticeKind, string> = { chord: "Hợp âm", interval: "Quãng", scale: "Âm giai", roman: "Số La Mã" };

// Tóm tắt đề để đọc lại trong lịch sử; chỉ ghép chữ, không tính nhạc lý.
function describeQuestion(item: PracticeHistoryItem): string {
  const q = item.question;
  // Lượt bấm piano chấm theo phím (dễ hơn chấm chính tả), ghi rõ để người học không lẫn.
  const via = q.input === "piano" ? " (bấm piano)" : q.input === "micro" ? " (đàn qua micro)" : q.input === "choice" ? " (trắc nghiệm)" : "";
  if (item.kind === "chord") return `Dựng ${q.symbol}${via}`;
  if (item.kind === "interval") return `${q.lower} → ${q.upper}${via}`;
  if (item.kind === "scale") return `${q.tonic} ${q.scale_type === "major" ? "trưởng" : "thứ tự nhiên"}${via}`;
  return `${q.chord} trong ${q.key} trưởng${via}`;
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

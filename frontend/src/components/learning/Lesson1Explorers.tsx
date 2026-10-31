import { useEffect, useMemo, useState } from "react";
import * as ui from "./lessonStyles";
import { buttonClass } from "../ui/Button";
import { api, type ApiError, type ChordInspection } from "../../api";
import { NoteAudioButton } from "../music/AudioControls";
import NotationStaff from "../music/NotationStaff";
import VirtualPiano from "../music/VirtualPiano";
import ChordInspector from "./ChordInspector";
import {
  ROOT_KEY_OPTIONS,
  TRIAD_KEY_TIERS,
  type KeyOverviewTier,
} from "../../content/lessons";
import {
  INTERVAL_LABELS,
  LESSON1_INTERVAL_CODES,
  TRIAD_LABELS,
  fetchLesson1Theory,
  intervalOf,
  pitchNames,
  triadOf,
  useLesson1Theory,
  type IntervalCode,
  type Lesson1TheoryState,
  type TriadQuality,
} from "../../theory/lesson1Theory";
import type { Lesson1Theory } from "../../api";

export function RootKeySelector({ value, onChange, compact = false }: { value: string; onChange: (root: string) => void; compact?: boolean }) {
  const option = ROOT_KEY_OPTIONS.find((item) => item.spellings.includes(value)) ?? ROOT_KEY_OPTIONS[0];
  return <div className={`my-3 grid gap-2.5 rounded-xl border border-line bg-bg ${compact ? "p-2.5" : "p-3"}`}>
    <div className="flex flex-wrap items-baseline gap-2.5"><b>Nốt gốc</b><span className="text-xs text-muted">Chọn 1 trong 12 vị trí cao độ</span></div>
    <div className="grid grid-cols-3 gap-1.5 sm:grid-cols-4 lg:grid-cols-6" role="group" aria-label="Chọn nốt gốc">
      {ROOT_KEY_OPTIONS.map((item) => <button
        type="button"
        key={item.label}
        className={ui.choice(item.spellings.includes(value), "text-center font-mono")}
        aria-pressed={item.spellings.includes(value)}
        onClick={() => onChange(item.defaultSpelling)}
      >{item.label}</button>)}
    </div>
    {option.spellings.length > 1 && <div className="flex flex-wrap items-center gap-2 text-xs text-muted" role="group" aria-label="Cách viết nốt gốc">
      <span>Cách viết đang dùng:</span>
      {option.spellings.map((spelling) => <button type="button" key={spelling} aria-pressed={value === spelling} className={ui.choice(value === spelling, "font-mono")} onClick={() => onChange(spelling)}>{spelling}</button>)}
      <small className="basis-full">Hai cách viết có thể cùng phím đàn nhưng tạo spelling khác nhau khi dựng quãng/hợp âm.</small>
    </div>}
  </div>;
}

// Chỉ đổi kiểu chữ (b → ♭, # → ♯) cho bậc Engine trả về, không tính gì thêm.
const prettyDegree = (degree: string) => degree.replace(/b/g, "♭").replace(/#/g, "♯");

// Trạng thái chờ/lỗi dùng chung: dữ liệu nhạc lý đến từ máy chủ nên có thể chậm hoặc lỗi mạng.
function TheoryStatus({ state }: { state: Lesson1TheoryState }) {
  if (state.status === "loading") return <p className={ui.muted} role="status">Đang lấy nốt từ máy chủ…</p>;
  if (state.status === "error") return <div className={ui.resultBad} role="alert">Chưa tải được nốt nhạc: {state.error}. Hãy thử chọn lại nốt gốc hoặc tải lại trang.</div>;
  return null;
}

export function IntervalExplorer({ root, onRootChange, prompt }: { root: string; onRootChange: (root: string) => void; prompt?: string }) {
  const [active, setActive] = useState<IntervalCode>("M3");
  const theory = useLesson1Theory(root);
  const data = theory.data;
  const example = data ? intervalOf(data, active) : null;

  return <article className={`${ui.block} ${ui.blockTone.explorer}`}>
    <span className={ui.kicker}>Khám phá tương tác</span>
    <h3>4. Khám phá M3, m3, P5 và d5 trên 12 nốt gốc</h3>
    {prompt && <p>{prompt}</p>}
    <RootKeySelector value={root} onChange={onRootChange} />
    <TheoryStatus state={theory} />
    {data && example && <>
      <div className="my-3 grid grid-cols-2 gap-2 sm:grid-cols-4" role="group" aria-label="Chọn loại quãng">
        {LESSON1_INTERVAL_CODES.map((code) => <button type="button" key={code} className={ui.choice(active === code, "flex flex-col items-start gap-0.5")} aria-pressed={active === code} onClick={() => setActive(code)}>
          <b className="font-mono">{code}</b><span className="text-xs font-normal text-muted">{intervalOf(data, code).semitones} nửa cung</span>
        </button>)}
      </div>
      <div className="grid items-stretch gap-3 md:grid-cols-[minmax(14rem,0.8fr)_1.2fr]">
        <div className="flex flex-col items-start gap-2 rounded-xl border border-line bg-surface p-4 [&_p]:my-0">
          <span className="text-xs font-semibold tracking-wide text-muted uppercase">Đang xem</span>
          <strong className="font-mono text-2xl">{data.root} → {example.upper}</strong>
          <p>{INTERVAL_LABELS[active]}: giữ đúng số quãng theo chữ cái và có khoảng cách {example.semitones} nửa cung.</p>
          <NoteAudioButton notes={pitchNames(example)} label={`Nghe ${active}`} />
        </div>
        <NotationStaff groups={[{ label: `${active} · ${data.root}–${example.upper}`, notes: pitchNames(example) }]} caption="Ký âm cập nhật theo nốt gốc và loại quãng đang chọn." />
      </div>
      <VirtualPiano highlightedPitchClasses={[data.root, example.upper]} showOctaveNumbers={false} />
    </>}
  </article>;
}

const QUALITY_ORDER: TriadQuality[] = ["major", "minor", "diminished", "augmented"];

export function TriadExplorer({ root, onRootChange, prompt, note }: { root: string; onRootChange: (root: string) => void; prompt?: string; note?: string }) {
  const [active, setActive] = useState<TriadQuality>("major");
  const theory = useLesson1Theory(root);
  const data = theory.data;

  return <article className={`${ui.block} ${ui.blockTone.explorer}`}>
    <span className={ui.kicker}>Dựng hợp âm ba nốt</span>
    <h3>6. Dựng triad trên bất kỳ nốt gốc nào</h3>
    {prompt && <p>{prompt}</p>}
    <RootKeySelector value={root} onChange={onRootChange} />
    <TheoryStatus state={theory} />
    {data && <TriadExplorerBody data={data} active={active} onActive={setActive} note={note} />}
  </article>;
}

function TriadExplorerBody({ data, active, onActive, note }: { data: Lesson1Theory; active: TriadQuality; onActive: (quality: TriadQuality) => void; note?: string }) {
  const major = triadOf(data, "major");
  const minor = triadOf(data, "minor");
  const current = triadOf(data, active);
  return <>
    <div className="my-3 grid gap-3 sm:grid-cols-2 [&>div]:flex [&>div]:flex-col [&>div]:gap-1 [&>div]:rounded-xl [&>div]:border [&>div]:border-line [&>div]:bg-surface [&>div]:p-3 [&_p]:my-0 [&_p]:text-xs [&_p]:text-muted [&_span]:text-xs [&_span]:font-semibold [&_span]:tracking-wide [&_span]:text-primary [&_span]:uppercase [&_strong]:font-mono [&_strong]:text-lg">
      <div><span>Bước 1 · khung chữ cái 1–3–5</span><strong>{data.letter_frame.join(" – ")}</strong><p>Giữ đúng họ chữ của nốt thứ ba và thứ năm trước khi quyết định dấu hóa.</p></div>
      <div><span>Bước 2 · đếm nửa cung</span><strong>{TRIAD_LABELS.major}: {major.notes.join("–")}</strong><strong>{TRIAD_LABELS.minor}: {minor.notes.join("–")}</strong><p>Cùng một vị trí root trên piano có thể cần spelling khác khi đổi Major/Minor.</p></div>
    </div>
    <div className="grid grid-cols-2 gap-2 lg:grid-cols-4" role="group" aria-label="Chọn loại hợp âm">
      {QUALITY_ORDER.map((quality) => {
        const triad = triadOf(data, quality);
        return <button type="button" key={quality} className={ui.choice(active === quality, "flex flex-col items-start gap-0.5")} aria-pressed={active === quality} onClick={() => onActive(quality)}>
          <span className="text-xs">{TRIAD_LABELS[quality]}</span><b className="font-mono text-base">{triad.formula.map(prettyDegree).join("–")}</b><strong className="font-mono text-xs">{triad.notes.join(" – ")}</strong><small className="font-normal text-muted">{triad.interval_formula.join(" + ")}</small>
        </button>;
      })}
    </div>
    {note && <div className="mt-3 rounded-md border-l-4 border-primary bg-primary-soft px-3 py-2">{note}</div>}
    <div className="mt-3 flex flex-wrap items-center gap-2">
      <ChordInspector symbol={current.symbol} displayLabel={current.symbol} eager />
      <NoteAudioButton notes={pitchNames(current)} label={`Nghe ${current.symbol}`} />
      <span className={ui.hint}>Đang tô sáng: {current.notes.join(" – ")}</span>
    </div>
    <VirtualPiano highlightedPitchClasses={current.notes} showOctaveNumbers={false} />
  </>;
}

export function TriadNotationExplorer({ root, onRootChange, prompt }: { root: string; onRootChange: (root: string) => void; prompt?: string }) {
  const [active, setActive] = useState<TriadQuality>("major");
  const theory = useLesson1Theory(root);
  const data = theory.data;
  return <article className={`${ui.block} ${ui.blockTone.explorer}`}>
    <span className={ui.kicker}>Ký âm + piano</span><h3>7. So sánh chất lượng hợp âm bằng cùng một nốt gốc</h3>
    {prompt && <p>{prompt}</p>}
    <RootKeySelector value={root} onChange={onRootChange} compact />
    <TheoryStatus state={theory} />
    {data && <>
      <div className="my-2.5 flex flex-wrap gap-2" role="group" aria-label="Chọn loại hợp âm">{QUALITY_ORDER.map((quality) => <button type="button" key={quality} className={ui.choice(active === quality)} aria-pressed={active === quality} onClick={() => setActive(quality)}>{TRIAD_LABELS[quality]}</button>)}</div>
      <NotationStaff
        groups={QUALITY_ORDER.map((quality) => {
          const triad = triadOf(data, quality);
          return { label: `${triad.symbol} · ${triad.notes.join("–")}`, notes: pitchNames(triad) };
        })}
        caption="Giữ nguyên root để nhìn rõ nốt thứ ba và thứ năm thay đổi như thế nào."
      />
      <VirtualPiano highlightedPitchClasses={triadOf(data, active).notes} showOctaveNumbers={false} />
    </>}
  </article>;
}

export function TriadAudioExplorer({ root, onRootChange, prompt }: { root: string; onRootChange: (root: string) => void; prompt?: string }) {
  const theory = useLesson1Theory(root);
  const data = theory.data;
  return <article className={`${ui.block} ${ui.blockTone.explorer}`}>
    <span className={ui.kicker}>Nghe</span><h3>8. Nghe sự thay đổi khi giữ nguyên nốt gốc</h3>
    {prompt && <p>{prompt}</p>}
    <RootKeySelector value={root} onChange={onRootChange} compact />
    <TheoryStatus state={theory} />
    {data && <div className="mt-3 flex flex-wrap items-center gap-2">
      {QUALITY_ORDER.map((quality) => {
        const triad = triadOf(data, quality);
        return <NoteAudioButton key={quality} notes={pitchNames(triad)} label={`${triad.symbol} · ${TRIAD_LABELS[quality]}`} />;
      })}
    </div>}
  </article>;
}

export function KeyOverview24({ prompt }: { prompt?: string }) {
  const [tierId, setTierId] = useState(TRIAD_KEY_TIERS[0].id);
  const tier: KeyOverviewTier = TRIAD_KEY_TIERS.find((item) => item.id === tierId) ?? TRIAD_KEY_TIERS[0];
  return <article className={ui.block}>
    <span className={ui.kicker}>24 giọng · hợp âm chủ</span><h3>9. Tổng quan 24 giọng · 12 trưởng & 12 thứ</h3>
    {prompt && <p>{prompt}</p>}
    <div className="my-2.5 flex flex-wrap gap-2" role="group" aria-label="Cấp độ luyện 24 giọng">
      {TRIAD_KEY_TIERS.map((item) => <button type="button" aria-pressed={tier.id === item.id} className={ui.choice(tier.id === item.id)} key={item.id} onClick={() => setTierId(item.id)}>{item.title}</button>)}
    </div>
    <p className={ui.muted}>{tier.note}</p>
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
      {tier.keys.map((item) => <div className="flex min-w-0 items-center justify-between gap-2 rounded-xl border border-line bg-bg p-2.5" key={item.symbol}>
        <span className="text-xs font-semibold">{item.label}</span>
        <ChordInspector symbol={item.symbol} displayLabel={item.symbol} compact />
      </div>)}
    </div>
  </article>;
}

function splitAnswerNotes(text: string) {
  return text.replaceAll("♭", "b").replaceAll("♯", "#").split(/[\s,;\-–—]+/).map((part) => part.trim()).filter(Boolean);
}

export function RandomPracticePanel({ mode }: { mode: "interval" | "triad" }) {
  const [nonce, setNonce] = useState(() => Math.floor(Math.random() * 100000));
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [expectedChord, setExpectedChord] = useState<ChordInspection | null>(null);

  type Question = { kind: "interval"; root: string; code: IntervalCode } | { kind: "triad"; symbol: string; label: string };
  const question = useMemo<Question>(() => {
    if (mode === "interval") {
      const rootOption = ROOT_KEY_OPTIONS[(nonce * 7 + 3) % ROOT_KEY_OPTIONS.length];
      const code = LESSON1_INTERVAL_CODES[(nonce * 5 + 1) % LESSON1_INTERVAL_CODES.length];
      return { kind: "interval", root: rootOption.defaultSpelling, code };
    }
    const allKeys = TRIAD_KEY_TIERS.flatMap((tier) => tier.keys);
    const key = allKeys[(nonce * 11 + 5) % allKeys.length];
    return { kind: "triad", symbol: key.symbol, label: key.label };
  }, [mode, nonce]);

  // Đề và đáp án đều từ Music Engine: nốt trên của quãng lấy từ /music/lesson1, chấm bằng /engine/grade/*.
  const [intervalUpper, setIntervalUpper] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    setAnswer("");
    setFeedback(null);
    setExpectedChord(null);
    setIntervalUpper(null);
    let alive = true;
    if (question.kind === "interval") {
      void fetchLesson1Theory(question.root)
        .then((data) => { if (alive) setIntervalUpper(intervalOf(data, question.code).upper); })
        .catch(() => { if (alive) setFeedback("Chưa lấy được câu hỏi từ máy chủ. Bấm \"Đổi câu khác\" để thử lại."); });
    } else {
      void api.inspectChord(question.symbol).then((chord) => { if (alive) setExpectedChord(chord); }).catch(() => undefined);
    }
    return () => { alive = false; };
  }, [question]);

  const check = async () => {
    if (!answer.trim()) return;
    setBusy(true);
    try {
      if (question.kind === "interval" && intervalUpper) {
        const result = await api.gradeIdentifyInterval(question.root, intervalUpper, answer.trim());
        setFeedback(result.correct ? `Đúng · ${answer.trim()}` : `Chưa đúng. ${result.message_vi} Hãy đếm chữ cái trước rồi đếm nửa cung.`);
        return;
      }
      if (question.kind === "triad" && expectedChord) {
        const result = await api.gradeBuildChord(question.symbol, splitAnswerNotes(answer));
        setFeedback(result.correct ? `Đúng · ${expectedChord.symbol} = ${expectedChord.notes.join("–")}` : `Chưa đúng. ${result.message_vi} ${expectedChord.symbol} được viết ${expectedChord.notes.join("–")}.`);
      }
    } catch (err) {
      setFeedback(`Chưa chấm được: ${(err as { message?: string })?.message ?? "lỗi mạng"}.`);
    } finally {
      setBusy(false);
    }
  };

  return <div className="mt-4 grid gap-2 border-t border-dashed border-primary/40 pt-3.5 [&_p]:my-0">
    <div className="flex flex-col"><b>Luyện tập ngẫu nhiên</b><small className={ui.hint}>{mode === "triad" ? "Hợp âm chủ của 24 giọng trưởng/thứ · phần luyện thêm, không tính điểm" : "12 nốt gốc × 4 loại quãng · phần luyện thêm, không tính điểm"}</small></div>
    <p>{question.kind === "interval" ? (intervalUpper ? `Quãng từ ${question.root} lên ${intervalUpper} là gì?` : "Đang lấy câu hỏi…") : `Dựng ${question.label}. Hãy nhập ba tên nốt.`}</p>
    {mode === "interval" ? <div className="flex flex-wrap gap-2" role="group" aria-label="Chọn đáp án">{LESSON1_INTERVAL_CODES.map((code) => <button type="button" key={code} aria-pressed={answer === code} className={ui.choice(answer === code, "font-mono")} onClick={() => setAnswer(code)}>{code}</button>)}</div> : <input className={ui.input} aria-label="Ba tên nốt của hợp âm" value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder="Ví dụ định dạng: Nốt-Nốt-Nốt" />}
    <div className="flex flex-wrap items-center gap-2">
      <button type="button" className={buttonClass("primary")} disabled={busy || !answer.trim() || (question.kind === "triad" && !expectedChord) || (question.kind === "interval" && !intervalUpper)} onClick={() => void check()}>Kiểm tra nhanh</button>
      <button type="button" className={ui.textButton} onClick={() => setNonce((value) => value + 1 + Math.floor(Math.random() * 97))}>Đổi câu khác</button>
    </div>
    {feedback && <div role="status" className={feedback.startsWith("Đúng") ? ui.resultGood : ui.resultBad}><span aria-hidden="true">{feedback.startsWith("Đúng") ? "✓ " : "✗ "}</span>{feedback}</div>}
  </div>;
}

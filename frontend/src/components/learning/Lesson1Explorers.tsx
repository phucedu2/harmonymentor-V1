import { useEffect, useMemo, useState } from "react";
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
  LESSON1_INTERVAL_CODES,
  buildTriad,
  intervalExample,
  toScientificInterval,
  toScientificTriad,
  triadLetterFrame,
  type IntervalCode,
  type TriadQuality,
} from "../../theory/lesson1Theory";
import { normalizePitchClass } from "../../audio/musicUtils";

export function RootKeySelector({ value, onChange, compact = false }: { value: string; onChange: (root: string) => void; compact?: boolean }) {
  const option = ROOT_KEY_OPTIONS.find((item) => item.spellings.includes(value)) ?? ROOT_KEY_OPTIONS[0];
  return <div className={`root-selector ${compact ? "compact" : ""}`}>
    <div className="root-selector-label"><b>Nốt gốc</b><span>Chọn 1 trong 12 vị trí cao độ</span></div>
    <div className="root-selector-grid" role="group" aria-label="Chọn nốt gốc">
      {ROOT_KEY_OPTIONS.map((item) => <button
        type="button"
        key={item.label}
        className={item.spellings.includes(value) ? "selected" : ""}
        onClick={() => onChange(item.defaultSpelling)}
      >{item.label}</button>)}
    </div>
    {option.spellings.length > 1 && <div className="enharmonic-choice">
      <span>Cách viết đang dùng:</span>
      {option.spellings.map((spelling) => <button type="button" key={spelling} className={value === spelling ? "selected" : ""} onClick={() => onChange(spelling)}>{spelling}</button>)}
      <small>Hai cách viết có thể cùng phím đàn nhưng tạo spelling khác nhau khi dựng quãng/hợp âm.</small>
    </div>}
  </div>;
}

export function IntervalExplorer({ root, onRootChange, prompt }: { root: string; onRootChange: (root: string) => void; prompt?: string }) {
  const [active, setActive] = useState<IntervalCode>("M3");
  const example = useMemo(() => intervalExample(root, active), [root, active]);
  const scientific = useMemo(() => toScientificInterval(root, active), [root, active]);

  return <article className="lesson-content-block explorer-block">
    <span className="section-kicker">Khám phá tương tác</span>
    <h3>4. Khám phá M3, m3, P5 và d5 trên 12 nốt gốc</h3>
    {prompt && <p>{prompt}</p>}
    <RootKeySelector value={root} onChange={onRootChange} />
    <div className="interval-choice-row" role="group" aria-label="Chọn loại quãng">
      {LESSON1_INTERVAL_CODES.map((code) => {
        const item = intervalExample(root, code);
        return <button type="button" key={code} className={active === code ? "selected" : ""} onClick={() => setActive(code)}>
          <b>{code}</b><span>{item.semitones} nửa cung</span>
        </button>;
      })}
    </div>
    <div className="explorer-result-grid">
      <div className="explainer-card">
        <span>Đang xem</span>
        <strong>{root} → {example.upper}</strong>
        <p>{example.label}: giữ đúng số quãng theo chữ cái và có khoảng cách {example.semitones} nửa cung.</p>
        <NoteAudioButton notes={scientific} label={`Nghe ${active}`} />
      </div>
      <NotationStaff groups={[{ label: `${active} · ${root}–${example.upper}`, notes: scientific }]} caption="Ký âm cập nhật theo nốt gốc và loại quãng đang chọn." />
    </div>
    <VirtualPiano highlightedPitchClasses={[root, example.upper]} showOctaveNumbers={false} />
  </article>;
}

const QUALITY_ORDER: TriadQuality[] = ["major", "minor", "diminished", "augmented"];

export function TriadExplorer({ root, onRootChange, prompt, note }: { root: string; onRootChange: (root: string) => void; prompt?: string; note?: string }) {
  const [active, setActive] = useState<TriadQuality>("major");
  const frame = triadLetterFrame(root);
  const major = buildTriad(root, "major");
  const minor = buildTriad(root, "minor");
  const current = buildTriad(root, active);
  const scientific = toScientificTriad(root, active);

  return <article className="lesson-content-block explorer-block triad-explorer">
    <span className="section-kicker">Dựng hợp âm ba nốt</span>
    <h3>6. Dựng triad trên bất kỳ nốt gốc nào</h3>
    {prompt && <p>{prompt}</p>}
    <RootKeySelector value={root} onChange={onRootChange} />
    <div className="construction-steps">
      <div><span>Bước 1 · khung chữ cái 1–3–5</span><strong>{frame.join(" – ")}</strong><p>Giữ đúng họ chữ của nốt thứ ba và thứ năm trước khi quyết định dấu hóa.</p></div>
      <div><span>Bước 2 · đếm nửa cung</span><strong>{major.label}: {major.notes.join("–")}</strong><strong>{minor.label}: {minor.notes.join("–")}</strong><p>Cùng một vị trí root trên piano có thể cần spelling khác khi đổi Major/Minor.</p></div>
    </div>
    <div className="triad-quality-grid">
      {QUALITY_ORDER.map((quality) => {
        const triad = buildTriad(root, quality);
        return <button type="button" key={quality} className={active === quality ? "selected" : ""} onClick={() => setActive(quality)}>
          <span>{triad.label}</span><b>{triad.formula}</b><strong>{triad.notes.join(" – ")}</strong><small>{triad.intervalFormula}</small>
        </button>;
      })}
    </div>
    {note && <div className="pedagogy-note">{note}</div>}
    <div className="interactive-output-row">
      <ChordInspector symbol={current.symbol} displayLabel={current.symbol} eager />
      <NoteAudioButton notes={scientific} label={`Nghe ${current.symbol}`} />
      <span className="muted">Đang tô sáng: {current.notes.join(" – ")}</span>
    </div>
    <VirtualPiano highlightedPitchClasses={current.notes} showOctaveNumbers={false} />
  </article>;
}

export function TriadNotationExplorer({ root, onRootChange, prompt }: { root: string; onRootChange: (root: string) => void; prompt?: string }) {
  const [active, setActive] = useState<TriadQuality>("major");
  const groups = QUALITY_ORDER.map((quality) => {
    const triad = buildTriad(root, quality);
    return { label: `${triad.symbol} · ${triad.notes.join("–")}`, notes: toScientificTriad(root, quality) };
  });
  const current = buildTriad(root, active);
  return <article className="lesson-content-block explorer-block">
    <span className="section-kicker">Ký âm + piano</span><h3>7. So sánh chất lượng hợp âm bằng cùng một nốt gốc</h3>
    {prompt && <p>{prompt}</p>}
    <RootKeySelector value={root} onChange={onRootChange} compact />
    <div className="quality-tabs">{QUALITY_ORDER.map((quality) => <button type="button" key={quality} className={active === quality ? "selected" : ""} onClick={() => setActive(quality)}>{buildTriad(root, quality).label}</button>)}</div>
    <NotationStaff groups={groups} caption="Giữ nguyên root để nhìn rõ nốt thứ ba và thứ năm thay đổi như thế nào." />
    <VirtualPiano highlightedPitchClasses={current.notes} showOctaveNumbers={false} />
  </article>;
}

export function TriadAudioExplorer({ root, onRootChange, prompt }: { root: string; onRootChange: (root: string) => void; prompt?: string }) {
  return <article className="lesson-content-block explorer-block">
    <span className="section-kicker">Nghe</span><h3>8. Nghe sự thay đổi khi giữ nguyên nốt gốc</h3>
    {prompt && <p>{prompt}</p>}
    <RootKeySelector value={root} onChange={onRootChange} compact />
    <div className="chord-audio-set">
      {QUALITY_ORDER.map((quality) => {
        const triad = buildTriad(root, quality);
        return <NoteAudioButton key={quality} notes={toScientificTriad(root, quality)} label={`${triad.symbol} · ${triad.label}`} />;
      })}
    </div>
  </article>;
}

export function KeyOverview24({ prompt }: { prompt?: string }) {
  const [tierId, setTierId] = useState(TRIAD_KEY_TIERS[0].id);
  const tier: KeyOverviewTier = TRIAD_KEY_TIERS.find((item) => item.id === tierId) ?? TRIAD_KEY_TIERS[0];
  return <article className="lesson-content-block key-overview-block">
    <span className="section-kicker">24 giọng · hợp âm chủ</span><h3>9. Tổng quan 24 giọng · 12 trưởng & 12 thứ</h3>
    {prompt && <p>{prompt}</p>}
    <div className="tier-tabs" role="tablist" aria-label="Cấp độ luyện 24 giọng">
      {TRIAD_KEY_TIERS.map((item) => <button type="button" role="tab" aria-selected={tier.id === item.id} className={tier.id === item.id ? "selected" : ""} key={item.id} onClick={() => setTierId(item.id)}>{item.title}</button>)}
    </div>
    <p className="muted">{tier.note}</p>
    <div className="key-card-grid">
      {tier.keys.map((item) => <div className="key-card" key={item.symbol}>
        <span>{item.label}</span>
        <ChordInspector symbol={item.symbol} displayLabel={item.symbol} compact />
      </div>)}
    </div>
  </article>;
}

function splitAnswerNotes(text: string) {
  return text.replaceAll("♭", "b").replaceAll("♯", "#").split(/[\s,;\-–—]+/).map((part) => part.trim()).filter(Boolean);
}

function sameSpelledNotes(input: string[], expected: string[]) {
  if (input.length !== expected.length) return false;
  const normalize = (value: string) => value.replaceAll("♭", "b").replaceAll("♯", "#").toUpperCase();
  return input.map(normalize).sort().join("|") === expected.map(normalize).sort().join("|");
}

export function RandomPracticePanel({ mode }: { mode: "interval" | "triad" }) {
  const [nonce, setNonce] = useState(() => Math.floor(Math.random() * 100000));
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [expectedChord, setExpectedChord] = useState<ChordInspection | null>(null);

  const question = useMemo(() => {
    if (mode === "interval") {
      const rootOption = ROOT_KEY_OPTIONS[(nonce * 7 + 3) % ROOT_KEY_OPTIONS.length];
      const root = rootOption.defaultSpelling;
      const code = LESSON1_INTERVAL_CODES[(nonce * 5 + 1) % LESSON1_INTERVAL_CODES.length];
      const ex = intervalExample(root, code);
      return { root, code, upper: ex.upper, prompt: `Quãng từ ${root} lên ${ex.upper} là gì?` };
    }
    const allKeys = TRIAD_KEY_TIERS.flatMap((tier) => tier.keys);
    const key = allKeys[(nonce * 11 + 5) % allKeys.length];
    return { symbol: key.symbol, prompt: `Dựng ${key.label}. Hãy nhập ba tên nốt.` };
  }, [mode, nonce]);

  useEffect(() => {
    setAnswer("");
    setFeedback(null);
    setExpectedChord(null);
    if (mode === "triad" && "symbol" in question && question.symbol) {
      void api.inspectChord(question.symbol).then(setExpectedChord).catch(() => undefined);
    }
  }, [mode, nonce, question]);

  const check = () => {
    if (!answer.trim()) return;
    if (mode === "interval" && "code" in question) {
      setFeedback(answer.trim() === question.code ? `Đúng · ${question.code}` : `Chưa đúng. Đáp án là ${question.code}. Hãy đếm chữ cái trước rồi đếm nửa cung.`);
      return;
    }
    if (mode === "triad" && expectedChord) {
      const correct = sameSpelledNotes(splitAnswerNotes(answer), expectedChord.notes);
      setFeedback(correct ? `Đúng · ${expectedChord.symbol} = ${expectedChord.notes.join("–")}` : `Chưa đúng. ${expectedChord.symbol} được viết ${expectedChord.notes.join("–")}. Chú ý viết đúng tên nốt (spelling).`);
    }
  };

  return <div className="random-practice-panel">
    <div className="random-practice-head"><b>Luyện tập ngẫu nhiên</b><small>{mode === "triad" ? "Hợp âm chủ của 24 giọng trưởng/thứ · phần luyện thêm, không tính điểm" : "12 nốt gốc × 4 loại quãng · phần luyện thêm, không tính điểm"}</small></div>
    <p>{question.prompt}</p>
    {mode === "interval" ? <div className="option-row">{LESSON1_INTERVAL_CODES.map((code) => <button type="button" key={code} className={answer === code ? "option selected" : "option"} onClick={() => setAnswer(code)}>{code}</button>)}</div> : <input value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder="Ví dụ định dạng: Nốt-Nốt-Nốt" />}
    <div className="actions">
      <button type="button" disabled={!answer.trim() || (mode === "triad" && !expectedChord)} onClick={check}>Kiểm tra nhanh</button>
      <button type="button" className="text-button" onClick={() => setNonce((value) => value + 1 + Math.floor(Math.random() * 97))}>Đổi câu khác</button>
    </div>
    {feedback && <div className={`result ${feedback.startsWith("Đúng") ? "good" : "bad"}`}>{feedback}</div>}
  </div>;
}

export function pitchClassesForTriad(root: string, quality: TriadQuality) {
  return buildTriad(root, quality).notes.map(normalizePitchClass);
}

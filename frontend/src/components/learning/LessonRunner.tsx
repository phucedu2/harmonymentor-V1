import { useEffect, useMemo, useState } from "react";
import {
  api,
  type ApiError,
  type AttemptResult,
  type LessonDetail,
  type LessonExercise,
  type LessonLearningProgress,
} from "../../api";
import ChordInspector, { ProgressionInspector } from "./ChordInspector";
import { parseProgressionSymbols, pitchClassOf } from "../../audio/musicUtils";
import { ChordAudioSet, ProgressionAudio } from "../music/AudioControls";
import GlossaryBlock from "../music/GlossaryBlock";
import NotationStaff from "../music/NotationStaff";
import VirtualPiano from "../music/VirtualPiano";
import {
  IntervalExplorer,
  KeyOverview24,
  RandomPracticePanel,
  TriadAudioExplorer,
  TriadExplorer,
  TriadNotationExplorer,
} from "./Lesson1Explorers";

const EXERCISE_KIND_LABELS: Record<string, string> = {
  mcq: "Trắc nghiệm",
  active_recall: "Tự nhớ",
  build: "Tự dựng",
  context: "Theo ngữ cảnh",
  applied: "Vận dụng",
};

type InputPresentation = { placeholder: string; hint?: string };

function inputPresentation(exercise: LessonExercise): InputPresentation {
  if (exercise.skill_id === "chord.triad_formula") {
    return {
      placeholder: "Ví dụ định dạng: 1-3-5",
      hint: "Bạn có thể gõ b thay cho ♭; dấu gạch ngang -, – đều được chấp nhận ở các câu công thức hỗ trợ chuẩn hóa ký hiệu.",
    };
  }
  if (exercise.skill_id.startsWith("chord.") && exercise.kind === "build") {
    return {
      placeholder: "Ví dụ định dạng: Nốt-Nốt-Nốt",
      hint: "Tên nốt có thể ngăn cách bằng dấu -, khoảng trắng hoặc dấu phẩy. Có thể gõ Eb hoặc E♭.",
    };
  }
  if (exercise.skill_id.includes("scale") && exercise.kind === "build") {
    return {
      placeholder: "Ví dụ định dạng: Nốt-Nốt-Nốt-...",
      hint: "Nhập các nốt theo đúng thứ tự; có thể dùng dấu -, khoảng trắng hoặc dấu phẩy.",
    };
  }
  if (exercise.skill_id === "pitch.spelling") {
    return { placeholder: "Nhập câu trả lời ngắn", hint: "Trả lời ngắn bằng từ hoặc một câu ngắn." };
  }
  if (exercise.kind === "active_recall") {
    return { placeholder: "Nhập câu trả lời của bạn", hint: "Hãy tự nhớ trước khi xem lại nội dung phía trên." };
  }
  return { placeholder: "Nhập câu trả lời", hint: "Trả lời theo đúng ký hiệu được dùng trong câu hỏi." };
}

export default function LessonRunner({
  lesson,
  initialProgress,
  onBack,
  onProgressChanged,
}: {
  lesson: LessonDetail;
  initialProgress?: LessonLearningProgress;
  onBack: () => void;
  onProgressChanged?: () => void;
}) {
  const [attempted, setAttempted] = useState<Set<string>>(new Set(initialProgress?.attempted_exercise_ids ?? []));
  const [correct, setCorrect] = useState<Set<string>>(new Set(initialProgress?.correct_exercise_ids ?? []));
  const [completion, setCompletion] = useState<string | null>(null);
  const [completeError, setCompleteError] = useState<string | null>(null);
  const [lesson1Root, setLesson1Root] = useState("C");

  useEffect(() => {
    void api.startLesson(lesson.id).then(() => onProgressChanged?.()).catch(() => undefined);
  }, [lesson.id]);

  const exerciseMap = useMemo(() => new Map(lesson.exercises.map((exercise) => [exercise.id, exercise])), [lesson.exercises]);
  const checkpointIds = useMemo(() => new Set(
    lesson.blocks
      .filter((block) => block.block_type === "checkpoint" && typeof block.payload.exercise_id === "string")
      .map((block) => String(block.payload.exercise_id)),
  ), [lesson.blocks]);
  const finalQuiz = lesson.exercises.filter((exercise) => !checkpointIds.has(exercise.id));
  const attemptedCount = attempted.size;
  const practicePercent = lesson.exercises.length ? Math.round(attemptedCount / lesson.exercises.length * 100) : 0;
  const allAttempted = lesson.exercises.length > 0 && attemptedCount >= lesson.exercises.length;
  const alreadyCompleted = initialProgress?.status === "completed" || Boolean(completion);

  const noteAttempt = (exerciseId: string, result: AttemptResult) => {
    setAttempted((previous) => new Set(previous).add(exerciseId));
    if (result.correct) setCorrect((previous) => new Set(previous).add(exerciseId));
    onProgressChanged?.();
  };

  const complete = async () => {
    setCompleteError(null);
    try {
      const result = await api.completeLesson(lesson.id);
      const due = result.first_review_due_at ? new Date(result.first_review_due_at).toLocaleString() : "chưa có";
      setCompletion(`Đã hoàn thành lesson và kích hoạt ${result.activated_review_items} thẻ ôn. Lượt ôn đầu: ${due}.`);
      onProgressChanged?.();
    } catch (e) {
      const err = e as ApiError;
      setCompleteError(err.message ?? err.code);
    }
  };

  return <section className="lesson-runner">
    <button className="text-button" onClick={onBack}>← Tất cả lesson</button>
    <div className="page-heading lesson-title-row">
      <div><span className="eyebrow">{lesson.track}</span><h2>{lesson.order}. {lesson.title}</h2></div>
      <span className={`status ${lesson.status}`}>{lesson.status}</span>
    </div>

    <article className="lesson-progress-card">
      <div><b>Tiến độ thực hành</b><span>{attemptedCount}/{lesson.exercises.length} câu đã làm · {correct.size} câu đã từng trả lời đúng</span></div>
      <div className="progress-track" aria-label={`Tiến độ ${practicePercent}%`}><span style={{ width: `${practicePercent}%` }} /></div>
      <strong>{practicePercent}%</strong>
    </article>

    <article className="learning-objectives">
      <span className="section-kicker">Mục tiêu học tập</span>
      <ul>{lesson.objectives.map((objective) => <li key={objective}>{objective}</li>)}</ul>
    </article>

    <div className="lesson-flow">
      {lesson.blocks.map((block) => (
        <BlockRenderer
          key={block.id}
          block={block}
          exerciseMap={exerciseMap}
          attempted={attempted}
          correct={correct}
          onAttempt={noteAttempt}
          lesson1Root={lesson1Root}
          onLesson1RootChange={setLesson1Root}
        />
      ))}
    </div>

    <article className="card block final-quiz-card">
      <div className="section-heading"><div><span className="section-kicker">Lesson quiz</span><h3>Kiểm tra cuối bài</h3></div><span className="muted">{finalQuiz.length} câu · active recall ưu tiên hơn nhận diện</span></div>
      {finalQuiz.length === 0 && <p className="muted">Các câu của lesson này hiện đang được dùng làm checkpoint.</p>}
      <div className="quiz-stack">{finalQuiz.map((exercise) => (
        <ExerciseCard key={exercise.id} exercise={exercise} attempted={attempted.has(exercise.id)} correct={correct.has(exercise.id)} onAttempt={noteAttempt} />
      ))}</div>
    </article>

    <article className="card block review-preview-card">
      <div className="section-heading"><div><span className="section-kicker">Retention</span><h3>Flashcards sẽ vào Review Queue</h3></div><span className="pill">1 → 3 → 7 → 14 → 30 ngày</span></div>
      <p className="muted">Các thẻ bên dưới chỉ là preview. Sau khi hoàn thành lesson, ReviewState thật sẽ được tạo trong database.</p>
      <div className="flash-grid">{lesson.review_items.slice(0, 4).map((item) => <Flashcard key={item.id} front={item.front} back={item.back} mode={item.mode} />)}</div>
    </article>

    <article className="card block completion-card">
      <div><span className="section-kicker">Finish</span><h3>Hoàn thành lesson</h3></div>
      <p>{alreadyCompleted ? "Lesson này đã được đánh dấu hoàn thành. Review queue được quản lý ở trang Tiến độ." : allAttempted ? "Bạn đã làm đủ các checkpoint và câu cuối bài. Có thể kích hoạt lịch ôn." : `Hãy làm đủ ${lesson.exercises.length} câu trước khi hoàn thành. Hiện tại: ${attemptedCount}/${lesson.exercises.length}.`}</p>
      <button disabled={!allAttempted || alreadyCompleted} onClick={complete}>{alreadyCompleted ? "Đã hoàn thành" : "Hoàn thành & kích hoạt ôn tập"}</button>
      {completion && <div className="result good">{completion}</div>}
      {completeError && <div className="result bad">{completeError}</div>}
    </article>

    <details className="sources-panel">
      <summary>Tài liệu tham khảo của lesson ({lesson.sources.length})</summary>
      <ul>{lesson.sources.map((source) => <li key={`${source.source_id}-${source.locator}`}><b>{source.title}</b><br/><span className="muted">{source.locator}</span>{source.note && <><br/><small>{source.note}</small></>}</li>)}</ul>
    </details>
  </section>;
}

function BlockRenderer({
  block,
  exerciseMap,
  attempted,
  correct,
  onAttempt,
  lesson1Root,
  onLesson1RootChange,
}: {
  block: LessonDetail["blocks"][number];
  exerciseMap: Map<string, LessonExercise>;
  attempted: Set<string>;
  correct: Set<string>;
  onAttempt: (exerciseId: string, result: AttemptResult) => void;
  lesson1Root: string;
  onLesson1RootChange: (root: string) => void;
}) {
  const title = typeof block.payload.title === "string" ? block.payload.title : block.block_type;
  const paragraphs = Array.isArray(block.payload.paragraphs) ? block.payload.paragraphs as string[] : [];
  const items = Array.isArray(block.payload.items) ? block.payload.items as string[] : [];
  const prompt = typeof block.payload.prompt === "string" ? block.payload.prompt : null;
  const note = typeof block.payload.note === "string" ? block.payload.note : null;
  const contextKey = typeof block.payload.key === "string" ? block.payload.key : undefined;
  const [pianoSelection, setPianoSelection] = useState<string[]>([]);
  const [pianoEvidenceResult, setPianoEvidenceResult] = useState<AttemptResult | null>(null);
  const [pianoEvidenceError, setPianoEvidenceError] = useState<string | null>(null);
  const [pianoEvidenceBusy, setPianoEvidenceBusy] = useState(false);
  const highlighted = Array.isArray(block.payload.highlight) ? block.payload.highlight.filter((item): item is string => typeof item === "string") : [];
  const progression = Array.isArray(block.payload.progression) ? block.payload.progression.filter((item): item is string => typeof item === "string") : [];
  const chords = Array.isArray(block.payload.chords) ? block.payload.chords.filter((item): item is string => typeof item === "string") : [];
  const bpm = typeof block.payload.bpm === "number" ? block.payload.bpm : 80;

  if (block.block_type === "checkpoint") {
    const exerciseId = typeof block.payload.exercise_id === "string" ? block.payload.exercise_id : "";
    const exercise = exerciseMap.get(exerciseId);
    if (!exercise) return null;
    return <article className="checkpoint-block">
      <div className="checkpoint-label"><span>Checkpoint</span>{attempted.has(exercise.id) && <b className={correct.has(exercise.id) ? "done-good" : "done-tried"}>{correct.has(exercise.id) ? "✓ Đã đúng" : "↻ Đã thử"}</b>}</div>
      <h3>{title}</h3>
      {note && <p className="muted">{note}</p>}
      <ExerciseCard exercise={exercise} attempted={attempted.has(exercise.id)} correct={correct.has(exercise.id)} onAttempt={onAttempt} inline />
      {(block.payload.random_practice === "interval" || block.payload.random_practice === "triad") && <RandomPracticePanel mode={block.payload.random_practice} />}
    </article>;
  }

  if (block.block_type === "interval_explorer") {
    return <IntervalExplorer root={lesson1Root} onRootChange={onLesson1RootChange} prompt={prompt ?? undefined} />;
  }

  if (block.block_type === "triad_explorer") {
    const pedagogicNote = typeof block.payload.note === "string" ? block.payload.note : undefined;
    return <TriadExplorer root={lesson1Root} onRootChange={onLesson1RootChange} prompt={prompt ?? undefined} note={pedagogicNote} />;
  }

  if (block.block_type === "triad_notation_explorer") {
    return <TriadNotationExplorer root={lesson1Root} onRootChange={onLesson1RootChange} prompt={prompt ?? undefined} />;
  }

  if (block.block_type === "triad_audio_explorer") {
    return <TriadAudioExplorer root={lesson1Root} onRootChange={onLesson1RootChange} prompt={prompt ?? undefined} />;
  }

  if (block.block_type === "key_overview") {
    return <KeyOverview24 prompt={prompt ?? undefined} />;
  }

  if (block.block_type === "progression") {
    const symbols = prompt ? parseProgressionSymbols(prompt) : [];
    return <article className="lesson-content-block progression-block">
      <span className="section-kicker">Progression</span><h3>{title}</h3>
      {prompt && <ProgressionInspector text={prompt} contextKey={contextKey} />}
      <p className="interaction-hint">Rê chuột, focus hoặc nhấn vào từng hợp âm để xem cấu tạo. Bạn cũng có thể nghe cả progression.</p>
      {symbols.length > 1 && <ProgressionAudio symbols={symbols} contextKey={contextKey} initialBpm={bpm} />}
    </article>;
  }

  if (block.block_type === "glossary") {
    const rawTerms = Array.isArray(block.payload.terms) ? block.payload.terms : [];
    const terms = rawTerms.filter((item): item is { symbol?: string; term: string; definition: string; example?: string } => {
      if (!item || typeof item !== "object") return false;
      const value = item as Record<string, unknown>;
      return typeof value.term === "string" && typeof value.definition === "string";
    });
    const intro = typeof block.payload.intro === "string" ? block.payload.intro : undefined;
    const kicker = typeof block.payload.kicker === "string" ? block.payload.kicker : undefined;
    const rawSpectrums = Array.isArray(block.payload.spectrums) ? block.payload.spectrums : [];
    const spectrums = rawSpectrums.flatMap((item) => {
      if (!item || typeof item !== "object") return [];
      const value = item as Record<string, unknown>;
      if (typeof value.label !== "string" || typeof value.text !== "string") return [];
      return [{ label: value.label, text: value.text }];
    });
    return <GlossaryBlock title={title} intro={intro} terms={terms} spectrums={spectrums} kicker={kicker} />;
  }

  if (block.block_type === "notation") {
    const rawGroups = Array.isArray(block.payload.groups) ? block.payload.groups : [];
    const groups = rawGroups.flatMap((item) => {
      if (!item || typeof item !== "object") return [];
      const value = item as Record<string, unknown>;
      const notes = Array.isArray(value.notes) ? value.notes.filter((note): note is string => typeof note === "string") : [];
      if (!notes.length) return [];
      return [{ label: typeof value.label === "string" ? value.label : undefined, notes }];
    });
    const caption = typeof block.payload.caption === "string" ? block.payload.caption : undefined;
    return <article className="lesson-content-block notation-block"><span className="section-kicker">Ký âm</span><h3>{title}</h3><NotationStaff groups={groups} caption={caption} /></article>;
  }

  if (block.block_type === "audio") {
    return <article className="lesson-content-block audio-block">
      <span className="section-kicker">Nghe</span><h3>{title}</h3>
      {prompt && <p>{prompt}</p>}
      {progression.length > 1 && <ProgressionAudio symbols={progression} contextKey={contextKey} initialBpm={bpm} />}
      {chords.length > 0 && <ChordAudioSet symbols={chords} contextKey={contextKey} />}
    </article>;
  }

  if (block.block_type === "piano") {
    const selectionMode = block.payload.selection_mode === true;
    const exerciseId = typeof block.payload.exercise_id === "string" ? block.payload.exercise_id : "";
    const evidenceMode = typeof block.payload.evidence_mode === "string" ? block.payload.evidence_mode : "";
    const exercise = exerciseMap.get(exerciseId);
    const submitLabel = typeof block.payload.submit_label === "string" ? block.payload.submit_label : "Check piano answer";
    const submitPianoEvidence = async () => {
      if (!exercise || evidenceMode !== "pitch_class" || pianoSelection.length === 0) return;
      const pitchClasses = [...new Set(pianoSelection.map(pitchClassOf))];
      setPianoEvidenceBusy(true);
      setPianoEvidenceError(null);
      try {
        const response = await api.submitAttempt(exercise.version_id, pitchClasses.join(" "));
        setPianoEvidenceResult(response);
        onAttempt(exercise.id, response);
      } catch (e) {
        const err = e as ApiError;
        setPianoEvidenceError(err.message ?? err.code);
      } finally {
        setPianoEvidenceBusy(false);
      }
    };
    return <article className="lesson-content-block piano-task-block">
      <span className="section-kicker">Piano tương tác</span><h3>{title}</h3>
      {prompt && <p>{prompt}</p>}
      {progression.length > 1 && <ProgressionAudio symbols={progression} contextKey={contextKey} initialBpm={bpm} />}
      <VirtualPiano
        highlightedPitchClasses={highlighted}
        selectionMode={selectionMode}
        selectedNotes={pianoSelection}
        onSelectionChange={setPianoSelection}
        showOctaveNumbers={block.payload.show_octave_numbers !== false}
      />
      {exercise && evidenceMode === "pitch_class" && <div className="piano-evidence">
        <button type="button" disabled={pianoEvidenceBusy || pianoSelection.length === 0} onClick={() => void submitPianoEvidence()}>{pianoEvidenceBusy ? "Checking..." : submitLabel}</button>
        {pianoEvidenceResult && <div className={`result ${pianoEvidenceResult.correct ? "good" : "bad"}`}><b>{pianoEvidenceResult.correct ? "OK" : "Try again"}</b><p>{pianoEvidenceResult.feedback}</p></div>}
        {pianoEvidenceError && <div className="result bad">{pianoEvidenceError}</div>}
      </div>}
    </article>;
  }

  if (block.block_type === "interactive") {
    return <article className="lesson-content-block interactive-block">
      <span className="section-kicker">Guided interaction</span><h3>{title}</h3>
      {prompt && <p>{prompt}</p>}
    </article>;
  }

  if (block.block_type === "callout") {
    return <article className="lesson-content-block callout-block"><span className="section-kicker">Lưu ý</span><h3>{title}</h3>{prompt && <p>{prompt}</p>}</article>;
  }

  if (block.block_type === "summary") {
    return <article className="lesson-content-block summary-block"><span className="section-kicker">Tóm tắt</span><h3>{title}</h3>{items.length > 0 && <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>}</article>;
  }

  return <article className="lesson-content-block">
    <span className="section-kicker">{block.block_type}</span><h3>{title}</h3>
    {paragraphs.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
    {items.length > 0 && <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>}
    {prompt && <p className="callout">{prompt}</p>}
    {block.block_type === "theory" && title.toLowerCase().includes("triad") && <div className="inline-chords"><ChordInspector symbol="C" /><ChordInspector symbol="Cm" /><ChordInspector symbol="Cdim" /><ChordInspector symbol="Caug" /></div>}
  </article>;
}

function ExerciseCard({
  exercise,
  attempted,
  correct,
  onAttempt,
  inline = false,
}: {
  exercise: LessonExercise;
  attempted: boolean;
  correct: boolean;
  onAttempt: (exerciseId: string, result: AttemptResult) => void;
  inline?: boolean;
}) {
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!answer.trim()) return;
    setBusy(true); setError(null);
    try {
      const response = await api.submitAttempt(exercise.version_id, answer);
      setResult(response);
      onAttempt(exercise.id, response);
    } catch (e) {
      const err = e as ApiError;
      setError(err.message ?? err.code);
    } finally { setBusy(false); }
  };

  return <div className={`quiz-item ${inline ? "inline-quiz" : ""}`}>
    <div className="quiz-meta"><span>{EXERCISE_KIND_LABELS[exercise.kind] ?? exercise.kind.replace(/_/g, " ")}</span>{attempted && <span className={correct ? "mini-state good-state" : "mini-state tried-state"}>{correct ? "✓ Đã đúng" : "Đã thử"}</span>}</div>
    <b>{exercise.prompt}</b>
    {exercise.options && <div className="option-row">{exercise.options.map((option) => <button type="button" key={option} className={answer === option ? "option selected" : "option"} onClick={() => setAnswer(option)}>{option}</button>)}</div>}
    {!exercise.options && (() => {
      const presentation = inputPresentation(exercise);
      return <>
        <input value={answer} onChange={(event) => setAnswer(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void submit(); }} placeholder={presentation.placeholder} aria-describedby={`${exercise.id}-input-hint`} />
        {presentation.hint && <small id={`${exercise.id}-input-hint`} className="input-format-hint">{presentation.hint}</small>}
      </>;
    })()}
    <div className="actions"><button disabled={busy || !answer.trim()} onClick={submit}>{busy ? "Đang kiểm tra…" : attempted ? "Kiểm tra lại" : "Kiểm tra"}</button></div>
    {result && <div className={`result ${result.correct ? "good" : "bad"}`}><b>{result.correct ? "Chính xác" : "Chưa đúng"}</b><p>{result.feedback}</p>{result.primary_error && <small>{result.primary_error}</small>}</div>}
    {error && <div className="result bad">{error}</div>}
  </div>;
}

function Flashcard({ front, back, mode }: { front: string; back: string; mode: string }) {
  const [revealed, setRevealed] = useState(false);
  return <button type="button" className="flash flash-button" onClick={() => setRevealed((value) => !value)}>
    <small>{mode}</small><b>{front}</b><span>{revealed ? back : "Tự nhớ đáp án rồi mới nhấn để kiểm tra"}</span>
  </button>;
}

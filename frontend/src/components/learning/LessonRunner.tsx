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
}: {
  block: LessonDetail["blocks"][number];
  exerciseMap: Map<string, LessonExercise>;
  attempted: Set<string>;
  correct: Set<string>;
  onAttempt: (exerciseId: string, result: AttemptResult) => void;
}) {
  const title = typeof block.payload.title === "string" ? block.payload.title : block.block_type;
  const paragraphs = Array.isArray(block.payload.paragraphs) ? block.payload.paragraphs as string[] : [];
  const items = Array.isArray(block.payload.items) ? block.payload.items as string[] : [];
  const prompt = typeof block.payload.prompt === "string" ? block.payload.prompt : null;
  const note = typeof block.payload.note === "string" ? block.payload.note : null;
  const contextKey = typeof block.payload.key === "string" ? block.payload.key : undefined;

  if (block.block_type === "checkpoint") {
    const exerciseId = typeof block.payload.exercise_id === "string" ? block.payload.exercise_id : "";
    const exercise = exerciseMap.get(exerciseId);
    if (!exercise) return null;
    return <article className="checkpoint-block">
      <div className="checkpoint-label"><span>Checkpoint</span>{attempted.has(exercise.id) && <b className={correct.has(exercise.id) ? "done-good" : "done-tried"}>{correct.has(exercise.id) ? "✓ Đã đúng" : "↻ Đã thử"}</b>}</div>
      <h3>{title}</h3>
      {note && <p className="muted">{note}</p>}
      <ExerciseCard exercise={exercise} attempted={attempted.has(exercise.id)} correct={correct.has(exercise.id)} onAttempt={onAttempt} inline />
    </article>;
  }

  if (block.block_type === "progression") {
    return <article className="lesson-content-block progression-block">
      <span className="section-kicker">Progression</span><h3>{title}</h3>
      {prompt && <ProgressionInspector text={prompt} contextKey={contextKey} />}
      <p className="interaction-hint">Rê chuột, focus hoặc nhấn vào từng hợp âm để xem cấu tạo.</p>
    </article>;
  }

  if (block.block_type === "piano") {
    return <article className="lesson-content-block piano-task-block">
      <span className="section-kicker">Keyboard task</span><h3>{title}</h3>
      {prompt && <p>{prompt}</p>}
      <div className="phase-note">Phase 1 giữ nhiệm vụ keyboard trong flow học. Audio/MIDI tương tác được nối ở Phase 2.</div>
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
    {block.block_type === "theory" && title.toLowerCase().includes("triad") && <div className="inline-chords"><ChordInspector symbol="C" /><ChordInspector symbol="Cm" /><ChordInspector symbol="Bdim" /></div>}
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
    <div className="quiz-meta"><span>{exercise.kind.replace(/_/g, " ")}</span><code>{exercise.skill_id}</code>{attempted && <span className={correct ? "mini-state good-state" : "mini-state tried-state"}>{correct ? "✓" : "tried"}</span>}</div>
    <b>{exercise.prompt}</b>
    {exercise.options && <div className="option-row">{exercise.options.map((option) => <button type="button" key={option} className={answer === option ? "option selected" : "option"} onClick={() => setAnswer(option)}>{option}</button>)}</div>}
    {!exercise.options && <input value={answer} onChange={(event) => setAnswer(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void submit(); }} placeholder="Nhập đáp án" />}
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

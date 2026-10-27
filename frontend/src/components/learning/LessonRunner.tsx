import { useEffect, useMemo, useRef, useState } from "react";
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

export const REVIEW_MODE_LABELS: Record<string, string> = {
  recall: "Tự nhớ",
  build: "Tự dựng",
  context: "Theo ngữ cảnh",
};

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
      hint: "Có thể gõ b thay cho ♭, ngăn cách bằng dấu cách, dấu phẩy hoặc gạch ngang.",
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

// Nhãn tiếng Việt cho từng loại khối; người học không cần thấy tên kỹ thuật như "theory".
const BLOCK_LABELS: Record<string, string> = {
  theory: "Lý thuyết",
  callout: "Lưu ý",
  piano: "Piano tương tác",
  glossary: "Thuật ngữ",
  checkpoint: "Kiểm tra nhanh",
  interval_explorer: "Khám phá quãng",
  triad_explorer: "Dựng hợp âm",
  triad_notation_explorer: "Ký âm + piano",
  triad_audio_explorer: "Nghe",
  key_overview: "24 giọng",
  progression: "Vòng hợp âm",
  notation: "Ký âm",
  audio: "Nghe",
  summary: "Tóm tắt",
  interactive: "Thực hành có hướng dẫn",
};

type Step = { id: string; label: string; title: string; render: () => JSX.Element; exerciseId?: string };

const stepStorageKey = (lessonId: string) => `hm.lesson-step.${lessonId}`;

function readStoredStep(lessonId: string): number {
  try { return Number(window.localStorage.getItem(stepStorageKey(lessonId)) ?? 0) || 0; }
  catch { return 0; }
}

export default function LessonRunner({
  lesson,
  initialProgress,
  onBack,
  onProgressChanged,
  onLessonOutdated,
}: {
  lesson: LessonDetail;
  initialProgress?: LessonLearningProgress;
  onBack: () => void;
  onProgressChanged?: () => void;
  // Gọi khi máy chủ báo câu hỏi đã có phiên bản mới (409 EXERCISE_VERSION_SUPERSEDED): trang tải lại bài.
  onLessonOutdated?: () => Promise<void>;
}) {
  const [attempted, setAttempted] = useState<Set<string>>(new Set(initialProgress?.attempted_exercise_ids ?? []));
  const [correct, setCorrect] = useState<Set<string>>(new Set(initialProgress?.correct_exercise_ids ?? []));
  const [completion, setCompletion] = useState<string | null>(null);
  const [completeError, setCompleteError] = useState<string | null>(null);
  const [startError, setStartError] = useState(false);
  const [outdatedNotice, setOutdatedNotice] = useState<string | null>(null);
  const [lesson1Root, setLesson1Root] = useState("C");
  const [stepIndex, setStepIndex] = useState(() => readStoredStep(lesson.id));
  const topRef = useRef<HTMLDivElement>(null);
  const indexRef = useRef<HTMLDetailsElement>(null);

  useEffect(() => {
    // Lưu "đã bắt đầu" thất bại không chặn việc học (bài đã tải, câu trả lời vẫn được lưu), nhưng phải báo
    // cho người học thay vì im lặng. Không tự gửi lại; lần gọi nào thành công thì ẩn thông báo.
    void api.startLesson(lesson.id)
      .then(() => { setStartError(false); onProgressChanged?.(); })
      .catch(() => setStartError(true));
  }, [lesson.id]);

  const exerciseMap = useMemo(() => new Map(lesson.exercises.map((exercise) => [exercise.id, exercise])), [lesson.exercises]);
  const checkpointIds = useMemo(() => new Set(
    lesson.blocks
      .filter((block) => block.block_type === "checkpoint" && typeof block.payload.exercise_id === "string")
      .map((block) => String(block.payload.exercise_id)),
  ), [lesson.blocks]);
  const finalQuiz = lesson.exercises.filter((exercise) => !checkpointIds.has(exercise.id));
  const total = lesson.exercises.length;
  const correctCount = lesson.exercises.filter((exercise) => correct.has(exercise.id)).length;
  const masteryPercent = total ? Math.round(correctCount / total * 100) : 0;
  // Hoàn thành bài = mọi câu đã đúng ít nhất một lần (backend kiểm lại, trả 409 nếu thiếu).
  const allCorrect = total > 0 && correctCount >= total;
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
      const due = result.first_review_due_at ? new Date(result.first_review_due_at).toLocaleDateString("vi-VN") : "chưa có";
      setCompletion(`Bạn đã hoàn thành bài! ${result.activated_review_items} thẻ ôn đã vào lịch, lượt ôn đầu tiên vào ngày ${due}.`);
      setStartError(false); // hoàn thành đã tạo dòng tiến độ, cảnh báo lúc mở bài không còn đúng
      onProgressChanged?.();
    } catch (e) {
      const err = e as ApiError;
      setCompleteError(err.message ?? err.code);
    }
  };

  // Không tự nộp lại câu trả lời cũ: đề có thể đã đổi, người học phải đọc đề mới rồi trả lời lại (ADR-006).
  const handleOutdated = async () => {
    setOutdatedNotice("Câu hỏi này vừa được cập nhật. Đang tải lại đề mới…");
    try {
      if (!onLessonOutdated) throw new Error("LESSON_RELOAD_UNAVAILABLE");
      await onLessonOutdated();
      setOutdatedNotice("Câu hỏi vừa được cập nhật nên bài đã tải lại đề mới. Câu trả lời trước chưa được chấm, hãy đọc lại đề và trả lời lại.");
    } catch {
      setOutdatedNotice("Câu hỏi vừa được cập nhật nhưng chưa tải lại được đề mới. Hãy quay lại danh sách bài rồi mở lại bài này.");
    }
  };

  const blockProps = { exerciseMap, attempted, correct, onAttempt: noteAttempt, onOutdated: handleOutdated, lesson1Root, onLesson1RootChange: setLesson1Root };
  const steps: Step[] = [
    {
      id: "intro", label: "Mở đầu", title: "Bài này giúp bạn làm được gì",
      render: () => <article className="learning-objectives">
        <span className="section-kicker">Mục tiêu học tập</span>
        <ul>{lesson.objectives.map((objective) => <li key={objective}>{objective}</li>)}</ul>
        <p className="muted">Bài gồm {lesson.blocks.length} phần ngắn và {total} câu hỏi. Bấm "Tiếp" để đi từng phần; tiến độ được lưu lại nếu bạn rời đi.</p>
      </article>,
    },
    ...lesson.blocks.map((block): Step => ({
      id: block.id,
      label: BLOCK_LABELS[block.block_type] ?? "Nội dung",
      title: typeof block.payload.title === "string" ? block.payload.title : (BLOCK_LABELS[block.block_type] ?? "Nội dung"),
      exerciseId: block.block_type === "checkpoint" && typeof block.payload.exercise_id === "string" ? block.payload.exercise_id : undefined,
      render: () => <BlockRenderer key={block.id} block={block} {...blockProps} />,
    })),
    {
      id: "quiz", label: "Kiểm tra", title: "Kiểm tra cuối bài",
      render: () => <article className="card block final-quiz-card">
        <div className="section-heading"><div><span className="section-kicker">Kiểm tra cuối bài</span><h3>Tự làm, không nhìn lại lý thuyết</h3></div><span className="muted">{finalQuiz.length} câu · sai 2 lần sẽ có lời giải</span></div>
        {finalQuiz.length === 0 && <p className="muted">Các câu của bài này nằm ở phần kiểm tra nhanh trong bài.</p>}
        <div className="quiz-stack">{finalQuiz.map((exercise) => (
          <ExerciseCard key={exercise.version_id} exercise={exercise} attempted={attempted.has(exercise.id)} correct={correct.has(exercise.id)} onAttempt={noteAttempt} onOutdated={handleOutdated} />
        ))}</div>
      </article>,
    },
    {
      id: "finish", label: "Hoàn thành", title: "Hoàn thành bài và lên lịch ôn",
      render: () => <>
        <article className="card block completion-card">
          <div><span className="section-kicker">Hoàn thành</span><h3>Hoàn thành bài</h3></div>
          <p>{alreadyCompleted ? "Bạn đã hoàn thành bài này. Lịch ôn nằm ở trang Tiến độ." : allCorrect ? "Bạn đã trả lời đúng tất cả các câu. Bấm nút bên dưới để hoàn thành và lên lịch ôn." : `Bạn cần trả lời đúng cả ${total} câu (mỗi câu đúng ít nhất một lần). Hiện đã đúng ${correctCount}/${total}.`}</p>
          {!alreadyCompleted && !allCorrect && <ul className="remaining-list">{lesson.exercises.filter((exercise) => !correct.has(exercise.id)).map((exercise) => {
            const target = steps.findIndex((step) => step.exerciseId === exercise.id);
            return <li key={exercise.id}><button type="button" className="text-button" onClick={() => goTo(target >= 0 ? target : steps.length - 2)}>{exercise.prompt}</button></li>;
          })}</ul>}
          <button disabled={!allCorrect || alreadyCompleted} onClick={complete}>{alreadyCompleted ? "Đã hoàn thành" : "Hoàn thành & lên lịch ôn"}</button>
          {completion && <div className="result good">{completion}</div>}
          {completeError && <div className="result bad">{completeError}</div>}
        </article>
        <article className="card block review-preview-card">
          <div className="section-heading"><div><span className="section-kicker">Ôn tập</span><h3>Thẻ ghi nhớ của bài</h3></div><span className="pill">Leitner: 1 → 2 → 4 → 8 → 16 ngày</span></div>
          <p className="muted">Khi hoàn thành bài, các thẻ này vào lịch ôn ở trang Tiến độ. Nhớ đúng thì lần ôn sau giãn ra, quên thì ôn lại từ ngày mai.</p>
          <div className="flash-grid">{lesson.review_items.slice(0, 4).map((item) => <Flashcard key={item.id} front={item.front} back={item.back} mode={item.mode} />)}</div>
        </article>
        <details className="sources-panel">
          <summary>Tài liệu tham khảo của bài ({lesson.sources.length})</summary>
          <ul>{lesson.sources.map((source) => <li key={`${source.source_id}-${source.locator}`}><b>{source.title}</b><br/><span className="muted">{source.locator}</span>{source.note && <><br/><small>{source.note}</small></>}</li>)}</ul>
        </details>
      </>,
    },
  ];

  const current = Math.min(Math.max(stepIndex, 0), steps.length - 1);
  function goTo(index: number) {
    const next = Math.min(Math.max(index, 0), steps.length - 1);
    setStepIndex(next);
    try { window.localStorage.setItem(stepStorageKey(lesson.id), String(next)); } catch { /* chế độ riêng tư: chỉ mất vị trí đã lưu */ }
    if (indexRef.current) indexRef.current.open = false;
    topRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  const step = steps[current];

  return <section className="lesson-runner" ref={topRef}>
    <button className="text-button" onClick={onBack}>← Tất cả bài học</button>
    <div className="page-heading lesson-title-row">
      <div><span className="eyebrow">{lesson.track}</span><h2>Bài {lesson.order}. {lesson.title}</h2></div>
    </div>

    <article className="lesson-progress-card">
      <div><b>Bước {current + 1}/{steps.length}</b><span>Đã đúng {correctCount}/{total} câu hỏi</span></div>
      <div className="progress-track" aria-label={`Đã đúng ${masteryPercent}% câu hỏi`}><span style={{ width: `${masteryPercent}%` }} /></div>
      <strong>{masteryPercent}%</strong>
    </article>
    {outdatedNotice && <div className="result bad" role="status">{outdatedNotice}</div>}
    {startError && <div className="result bad" role="alert">Chưa lưu được trạng thái bắt đầu bài. Bạn vẫn học bình thường; tiến độ sẽ được lưu khi bạn hoàn thành bài.</div>}

    <div className="lesson-stepper">
      <details className="step-index" ref={indexRef}>
        <summary>Mục lục bài học</summary>
        <ol>{steps.map((item, index) => {
          const done = item.exerciseId ? correct.has(item.exerciseId) : index < current;
          return <li key={item.id}><button type="button" className={index === current ? "current" : ""} aria-current={index === current ? "step" : undefined} onClick={() => goTo(index)}>
            <span className="step-dot">{done ? "✓" : index + 1}</span><span><small>{item.label}</small>{item.title}</span>
          </button></li>;
        })}</ol>
      </details>

      <div className="lesson-flow" key={step.id}>{step.render()}</div>

      <nav className="step-nav" aria-label="Chuyển bước">
        <button type="button" className="ghost" disabled={current === 0} onClick={() => goTo(current - 1)}>← Bước trước</button>
        <span className="muted">{step.exerciseId && !correct.has(step.exerciseId) ? "Bạn có thể đi tiếp và quay lại câu này sau." : `${step.label} · ${current + 1}/${steps.length}`}</span>
        <button type="button" disabled={current === steps.length - 1} onClick={() => goTo(current + 1)}>{current === steps.length - 2 ? "Tới phần hoàn thành →" : "Bước tiếp →"}</button>
      </nav>
    </div>
  </section>;
}

function BlockRenderer({
  block,
  exerciseMap,
  attempted,
  correct,
  onAttempt,
  onOutdated,
  lesson1Root,
  onLesson1RootChange,
}: {
  block: LessonDetail["blocks"][number];
  exerciseMap: Map<string, LessonExercise>;
  attempted: Set<string>;
  correct: Set<string>;
  onAttempt: (exerciseId: string, result: AttemptResult) => void;
  onOutdated: () => Promise<void>;
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
      <div className="checkpoint-label"><span>Kiểm tra nhanh</span>{attempted.has(exercise.id) && <b className={correct.has(exercise.id) ? "done-good" : "done-tried"}>{correct.has(exercise.id) ? "✓ Đã đúng" : "↻ Đã thử"}</b>}</div>
      <h3>{title}</h3>
      {note && <p className="muted">{note}</p>}
      <ExerciseCard key={exercise.version_id} exercise={exercise} attempted={attempted.has(exercise.id)} correct={correct.has(exercise.id)} onAttempt={onAttempt} onOutdated={onOutdated} inline />
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
      <span className="section-kicker">Vòng hợp âm</span><h3>{title}</h3>
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
    const submitLabel = typeof block.payload.submit_label === "string" ? block.payload.submit_label : "Kiểm tra bằng piano";
    const submitPianoEvidence = async () => {
      if (!exercise || evidenceMode !== "pitch_class" || pianoSelection.length === 0) return;
      const pitchClasses = [...new Set(pianoSelection.map(pitchClassOf))];
      setPianoEvidenceBusy(true);
      setPianoEvidenceError(null);
      try {
        // Phím đàn không phân biệt D# với Eb: backend chỉ chấm cao độ cho bài nộp bằng piano.
        const response = await api.submitAttempt(exercise.version_id, pitchClasses.join(" "), "piano");
        setPianoEvidenceResult(response);
        onAttempt(exercise.id, response);
      } catch (e) {
        const err = e as ApiError;
        if (err.code === "EXERCISE_VERSION_SUPERSEDED") {
          setPianoSelection([]);
          setPianoEvidenceResult(null);
          await onOutdated();
          return;
        }
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
        <button type="button" disabled={pianoEvidenceBusy || pianoSelection.length === 0} onClick={() => void submitPianoEvidence()}>{pianoEvidenceBusy ? "Đang kiểm tra…" : submitLabel}</button>
        {pianoEvidenceResult && <div className={`result ${pianoEvidenceResult.correct ? "good" : "bad"}`}><b>{pianoEvidenceResult.correct ? "Chính xác" : "Chưa đúng, thử lại nhé"}</b><p>{pianoEvidenceResult.feedback}</p>{pianoEvidenceResult.explanation && <p className="explanation"><b>Giải thích:</b> {pianoEvidenceResult.explanation}</p>}</div>}
        {pianoEvidenceError && <div className="result bad">{pianoEvidenceError}</div>}
      </div>}
    </article>;
  }

  if (block.block_type === "interactive") {
    return <article className="lesson-content-block interactive-block">
      <span className="section-kicker">Thực hành có hướng dẫn</span><h3>{title}</h3>
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
    <span className="section-kicker">{BLOCK_LABELS[block.block_type] ?? "Nội dung"}</span><h3>{title}</h3>
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
  onOutdated,
  inline = false,
}: {
  exercise: LessonExercise;
  attempted: boolean;
  correct: boolean;
  onAttempt: (exerciseId: string, result: AttemptResult) => void;
  onOutdated: () => Promise<void>;
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
      const response = await api.submitAttempt(exercise.version_id, answer, exercise.options ? "choice" : "text");
      setResult(response);
      onAttempt(exercise.id, response);
    } catch (e) {
      const err = e as ApiError;
      setResult(null);
      if (err.code === "EXERCISE_VERSION_SUPERSEDED") {
        // Thẻ câu hỏi có key là version_id nên tải lại xong sẽ dựng thẻ mới với ô trả lời trống.
        await onOutdated();
        return;
      }
      setError(`${err.message ?? err.code}. Hãy dùng tên chữ cái C D E F G A B (có thể gõ Đô Rê Mi), thêm # hoặc b cho dấu thăng/giáng.`);
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
    {result && <div className={`result ${result.correct ? "good" : "bad"}`} role="status">
      <b>{result.correct ? "Chính xác!" : "Chưa đúng"}</b>
      {!result.correct && result.feedback && <p>{result.feedback}</p>}
      {result.explanation
        ? <p className="explanation"><b>Giải thích:</b> {result.explanation}</p>
        : !result.correct && <p className="muted">Thử lại nhé. Nếu sai thêm {Math.max(1, 2 - result.wrong_attempts)} lần nữa, lời giải sẽ hiện ra.</p>}
    </div>}
    {error && <div className="result bad">{error}</div>}
  </div>;
}

function Flashcard({ front, back, mode }: { front: string; back: string; mode: string }) {
  const [revealed, setRevealed] = useState(false);
  return <button type="button" className="flash flash-button" onClick={() => setRevealed((value) => !value)}>
    <small>{REVIEW_MODE_LABELS[mode] ?? mode}</small><b>{front}</b><span>{revealed ? back : "Tự nhớ đáp án trước, rồi bấm để lật thẻ"}</span>
  </button>;
}

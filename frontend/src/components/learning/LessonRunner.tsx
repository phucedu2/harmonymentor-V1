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
import * as ui from "./lessonStyles";
import { TermText, firstAppearances } from "./TermText";
import { Button } from "../ui/Button";
import { Badge, ChipButton, ProgressBar, ResultBox } from "../ui/Page";

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
// A = backing track, B = vòng hợp âm lạ (mục tiêu sản phẩm của phuc-music).
const GOAL_LABELS: Record<string, string> = { A: "Mục tiêu A · Backing track", B: "Mục tiêu B · Vòng hợp âm lạ" };

const BLOCK_LABELS: Record<string, string> = {
  theory: "Lý thuyết",
  callout: "Lưu ý",
  compose_link: "Dùng vào sáng tác",
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

// Các khối chữ được chú giải thuật ngữ; khối "theory" và khối không có nhãn riêng dùng bộ hiển thị mặc định.
const ANNOTATED_BLOCKS = new Set(["callout", "interactive", "summary"]);

function blockTexts(payload: Record<string, unknown>): string[] {
  const pick = (value: unknown) => (Array.isArray(value) ? value.filter((x): x is string => typeof x === "string") : typeof value === "string" ? [value] : []);
  return [...pick(payload.paragraphs), ...pick(payload.items), ...pick(payload.prompt)];
}

type Step = { id: string; label: string; title: string; render: () => JSX.Element; exerciseId?: string };

const stepStorageKey = (lessonId: string) => `hm.lesson-step.${lessonId}`;

const viewStorageKey = "hm.lesson-view";

function readStoredView(): boolean {
  try { return window.localStorage.getItem(viewStorageKey) === "all"; } catch { return false; }
}

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
  // "Xem cả bài" (bố cục cuộn một trang của v0.5.3) và "Từng bước" (PR #6) dùng chung một danh sách
  // bước và cùng trạng thái chấm, nên đổi chế độ không làm mất câu đã đúng.
  const [viewAll, setViewAll] = useState(() => readStoredView());
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

  // Chú giải thuật ngữ ở khối chữ đầu tiên nhắc tới nó (bỏ qua khối thuật ngữ vì khối đó tự giải nghĩa).
  const termMap = useMemo(() => firstAppearances(lesson.blocks
    .filter((block) => ANNOTATED_BLOCKS.has(block.block_type) || !BLOCK_LABELS[block.block_type] || block.block_type === "theory")
    .map((block) => ({ id: block.id, texts: blockTexts(block.payload) }))), [lesson.blocks]);
  const blockProps = { exerciseMap, attempted, correct, onAttempt: noteAttempt, onOutdated: handleOutdated, lesson1Root, onLesson1RootChange: setLesson1Root };
  const steps: Step[] = [
    {
      id: "intro", label: "Mở đầu", title: "Bài này giúp bạn làm được gì",
      render: () => <article className={ui.block}>
        <span className={ui.kicker}>Mục tiêu học tập</span>
        <ul>{lesson.objectives.map((objective) => <li key={objective}>{objective}</li>)}</ul>
        <p className={ui.muted}>Bài gồm {lesson.blocks.length} phần ngắn và {total} câu hỏi. {viewAll ? "Cuộn xuống để đọc lần lượt; câu đã trả lời đúng được lưu lại." : 'Bấm "Bước tiếp" để đi từng phần; tiến độ được lưu lại nếu bạn rời đi.'}</p>
      </article>,
    },
    ...lesson.blocks.map((block): Step => ({
      id: block.id,
      label: BLOCK_LABELS[block.block_type] ?? "Nội dung",
      title: typeof block.payload.title === "string" ? block.payload.title : (BLOCK_LABELS[block.block_type] ?? "Nội dung"),
      exerciseId: block.block_type === "checkpoint" && typeof block.payload.exercise_id === "string" ? block.payload.exercise_id : undefined,
      render: () => <BlockRenderer key={block.id} block={block} terms={termMap.get(block.id)} {...blockProps} />,
    })),
    {
      id: "quiz", label: "Kiểm tra", title: "Kiểm tra cuối bài",
      render: () => <article className={ui.block}>
        <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between"><div><span className={ui.kicker}>Kiểm tra cuối bài</span><h3>Tự làm, không nhìn lại lý thuyết</h3></div><span className={ui.hint}>{finalQuiz.length} câu · sai 2 lần sẽ có lời giải</span></div>
        {finalQuiz.length === 0 && <p className={ui.muted}>Các câu của bài này nằm ở phần kiểm tra nhanh trong bài.</p>}
        <div className="mt-3 grid gap-3">{finalQuiz.map((exercise) => (
          <ExerciseCard key={exercise.version_id} exercise={exercise} attempted={attempted.has(exercise.id)} correct={correct.has(exercise.id)} onAttempt={noteAttempt} onOutdated={handleOutdated} />
        ))}</div>
      </article>,
    },
    {
      id: "finish", label: "Hoàn thành", title: "Hoàn thành bài và lên lịch ôn",
      render: () => <>
        <article className={`${ui.block} border-primary/40`}>
          <div><span className={ui.kicker}>Hoàn thành</span><h3>Hoàn thành bài</h3></div>
          <p>{alreadyCompleted ? "Bạn đã hoàn thành bài này. Lịch ôn nằm ở trang Tiến độ." : allCorrect ? "Bạn đã trả lời đúng tất cả các câu. Bấm nút bên dưới để hoàn thành và lên lịch ôn." : `Bạn cần trả lời đúng cả ${total} câu (mỗi câu đúng ít nhất một lần). Hiện đã đúng ${correctCount}/${total}.`}</p>
          {!alreadyCompleted && !allCorrect && <ul>{lesson.exercises.filter((exercise) => !correct.has(exercise.id)).map((exercise) => {
            const target = steps.findIndex((step) => step.exerciseId === exercise.id);
            return <li key={exercise.id}><button type="button" className={ui.textButton} onClick={() => goTo(target >= 0 ? target : steps.length - 2)}>{exercise.prompt}</button></li>;
          })}</ul>}
          <Button size="lg" className="mt-2" disabled={!allCorrect || alreadyCompleted} onClick={complete}>{alreadyCompleted ? "Đã hoàn thành" : "Hoàn thành và lên lịch ôn"}</Button>
          {completion && <ResultBox correct title="Hoàn thành!">{completion}</ResultBox>}
          {completeError && <ResultBox correct={false} title="Chưa hoàn thành được">{completeError}</ResultBox>}
        </article>
        <article className={`${ui.block} mt-4`}>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between"><div><span className={ui.kicker}>Ôn tập</span><h3>Thẻ ghi nhớ của bài</h3></div><Badge>Lịch ôn: 1 → 2 → 4 → 8 → 16 ngày</Badge></div>
          <p className={ui.muted}>Khi hoàn thành bài, các thẻ này vào lịch ôn ở trang Tiến độ. Nhớ đúng thì lần ôn sau giãn ra, quên thì ôn lại từ ngày mai.</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">{lesson.review_items.slice(0, 4).map((item) => <Flashcard key={item.id} front={item.front} back={item.back} mode={item.mode} />)}</div>
        </article>
        <details className="mt-4 rounded-xl border border-line bg-surface px-4 py-3">
          <summary className="min-h-11 cursor-pointer content-center font-semibold">Tài liệu tham khảo của bài ({lesson.sources.length})</summary>
          <ul className="mt-2 grid gap-3">{lesson.sources.map((source) => <li key={`${source.source_id}-${source.locator}`}><b>{source.title}</b><br/><span className={ui.hint}>{source.locator}</span>{source.note && <><br/><small className={ui.hint}>{source.note}</small></>}</li>)}</ul>
        </details>
      </>,
    },
  ];

  const current = Math.min(Math.max(stepIndex, 0), steps.length - 1);
  function changeView(all: boolean) {
    setViewAll(all);
    try { window.localStorage.setItem(viewStorageKey, all ? "all" : "steps"); } catch { /* chế độ riêng tư: chỉ mất lựa chọn */ }
  }
  function goTo(index: number) {
    const next = Math.min(Math.max(index, 0), steps.length - 1);
    if (viewAll) {
      // Trong chế độ xem cả bài, mọi bước đã nằm trên trang: chỉ cuộn tới bước đó.
      document.getElementById(`buoc-${steps[next].id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    setStepIndex(next);
    try { window.localStorage.setItem(stepStorageKey(lesson.id), String(next)); } catch { /* chế độ riêng tư: chỉ mất vị trí đã lưu */ }
    if (indexRef.current) indexRef.current.open = false;
    topRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  const step = steps[current];

  return <section className="scroll-mt-4 pb-20 sm:pb-0" ref={topRef}>
    <button className={ui.textButton} onClick={onBack}>← Tất cả bài học</button>
    <header className="mt-2 mb-4">
      <p className={ui.kicker}>{lesson.track}</p>
      <h1 className="mt-1 font-display text-3xl leading-tight font-semibold text-ink">Bài {lesson.order}. {lesson.title}</h1>
    </header>

    <div className="mb-4 grid items-center gap-2 rounded-2xl border border-primary/25 bg-surface px-4 py-3 sm:grid-cols-[minmax(10rem,1fr)_2fr_auto] sm:gap-4">
      <div className="flex flex-col"><b className="text-ink">{viewAll ? `${steps.length} bước` : `Bước ${current + 1}/${steps.length}`}</b><span className="text-xs text-muted">Đã đúng {correctCount}/{total} câu hỏi</span></div>
      <ProgressBar value={masteryPercent} label={`Đã đúng ${masteryPercent}% câu hỏi`} />
      <strong className="font-mono text-primary">{masteryPercent}%</strong>
    </div>
    {outdatedNotice && <div className={ui.resultBad} role="status">{outdatedNotice}</div>}
    {startError && <div className={ui.resultBad} role="alert">Chưa lưu được trạng thái bắt đầu bài. Bạn vẫn học bình thường; tiến độ sẽ được lưu khi bạn hoàn thành bài.</div>}

    <div className="my-3 inline-flex gap-2" role="group" aria-label="Cách xem bài">
      <ChipButton pressed={!viewAll} onClick={() => changeView(false)}>Từng bước</ChipButton>
      <ChipButton pressed={viewAll} onClick={() => changeView(true)}>Xem cả bài</ChipButton>
    </div>

    {viewAll ? <div className="grid gap-6">
      {steps.map((item, index) => <section key={item.id} id={`buoc-${item.id}`} className="grid scroll-mt-4 gap-1.5" aria-label={`Bước ${index + 1}: ${item.title}`}>
        <p className={ui.kicker}>Bước {index + 1}/{steps.length} · {item.label}</p>
        {item.render()}
      </section>)}
    </div> : <div className="grid gap-4">
      <details className="rounded-xl border border-line bg-surface px-4 py-2" ref={indexRef}>
        <summary className="min-h-11 cursor-pointer content-center font-semibold">Mục lục bài học</summary>
        <ol className="mt-2 mb-2 grid gap-1">{steps.map((item, index) => {
          const done = item.exerciseId ? correct.has(item.exerciseId) : index < current;
          const here = index === current;
          return <li key={item.id}><button type="button" aria-current={here ? "step" : undefined} onClick={() => goTo(index)}
            className={`flex min-h-11 w-full items-center gap-3 rounded-lg border px-2 py-1.5 text-left text-ink hover:bg-primary-soft ${here ? "border-primary bg-primary-soft" : "border-transparent"}`}>
            <span className={`grid size-7 flex-none place-items-center rounded-full text-xs font-semibold ${done ? "bg-success-soft text-success" : "bg-bg text-muted"}`}>{done ? "✓" : index + 1}</span>
            <span className="flex flex-col"><small className="text-xs text-muted">{item.label}</small>{item.title}</span>
          </button></li>;
        })}</ol>
      </details>

      <div className="grid gap-3" key={step.id}>{step.render()}</div>

      {/* Nút chuyển bước dính đáy màn hình: trên điện thoại 360px nút chính luôn nhìn thấy. */}
      <nav className="fixed inset-x-0 bottom-0 z-20 flex items-center justify-between gap-3 border-t border-line bg-bg/95 px-4 py-3 backdrop-blur sm:sticky sm:inset-x-auto sm:px-0" aria-label="Chuyển bước">
        <Button variant="secondary" disabled={current === 0} onClick={() => goTo(current - 1)}>← Bước trước</Button>
        <span className="hidden text-center text-sm text-muted sm:block">{step.exerciseId && !correct.has(step.exerciseId) ? "Bạn có thể đi tiếp và quay lại câu này sau." : `${step.label} · ${current + 1}/${steps.length}`}</span>
        <Button disabled={current === steps.length - 1} onClick={() => goTo(current + 1)}>{current === steps.length - 2 ? "Tới phần hoàn thành →" : "Bước tiếp →"}</Button>
      </nav>
    </div>}
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
  terms,
}: {
  block: LessonDetail["blocks"][number];
  terms?: Set<string>;
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
  // Mỗi thuật ngữ chỉ chú giải một lần trong khối, dù xuất hiện ở nhiều đoạn.
  const claimed = new Set<string>();
  const t = (text: string) => <TermText text={text} terms={terms} claimed={claimed} />;

  if (block.block_type === "checkpoint") {
    const exerciseId = typeof block.payload.exercise_id === "string" ? block.payload.exercise_id : "";
    const exercise = exerciseMap.get(exerciseId);
    if (!exercise) return null;
    return <article className={`${ui.block} ${ui.blockTone.checkpoint}`}>
      <div className="flex items-center justify-between gap-3"><span className={ui.kicker}>Kiểm tra nhanh</span>{attempted.has(exercise.id) && <Badge tone={correct.has(exercise.id) ? "success" : "warning"}>{correct.has(exercise.id) ? "✓ Đã đúng" : "↻ Đã thử"}</Badge>}</div>
      <h3>{title}</h3>
      {note && <p className={ui.muted}>{note}</p>}
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
    return <article className={ui.block}>
      <span className={ui.kicker}>Vòng hợp âm</span><h3>{title}</h3>
      {prompt && <ProgressionInspector text={prompt} contextKey={contextKey} />}
      <p className="text-xs text-muted">Rê chuột, focus hoặc nhấn vào từng hợp âm để xem cấu tạo. Bạn cũng có thể nghe cả progression.</p>
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
    return <article className={`${ui.block} overflow-x-auto`}><span className={ui.kicker}>Ký âm</span><h3>{title}</h3><NotationStaff groups={groups} caption={caption} /></article>;
  }

  if (block.block_type === "audio") {
    return <article className={`${ui.block} ${ui.blockTone.audio}`}>
      <span className={ui.kicker}>Nghe</span><h3>{title}</h3>
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
    return <article className={`${ui.block} ${ui.blockTone.piano}`}>
      <span className={ui.kicker}>Piano tương tác</span><h3>{title}</h3>
      {prompt && <p>{prompt}</p>}
      {progression.length > 1 && <ProgressionAudio symbols={progression} contextKey={contextKey} initialBpm={bpm} />}
      <VirtualPiano
        highlightedPitchClasses={highlighted}
        selectionMode={selectionMode}
        selectedNotes={pianoSelection}
        onSelectionChange={setPianoSelection}
        showOctaveNumbers={block.payload.show_octave_numbers !== false}
      />
      {exercise && evidenceMode === "pitch_class" && <div className="mt-3 grid items-start gap-2">
        <Button className="justify-self-start" disabled={pianoEvidenceBusy || pianoSelection.length === 0} onClick={() => void submitPianoEvidence()}>{pianoEvidenceBusy ? "Đang kiểm tra…" : submitLabel}</Button>
        {pianoEvidenceResult && <ResultBox correct={pianoEvidenceResult.correct} title={pianoEvidenceResult.correct ? "Chính xác" : "Chưa đúng, thử lại nhé"}><p>{pianoEvidenceResult.feedback}</p>{pianoEvidenceResult.explanation && <p className={ui.explanation}><b>Giải thích:</b> {pianoEvidenceResult.explanation}</p>}</ResultBox>}
        {pianoEvidenceError && <div className={ui.resultBad}>{pianoEvidenceError}</div>}
      </div>}
    </article>;
  }

  if (block.block_type === "interactive") {
    return <article className={`${ui.block} ${ui.blockTone.interactive}`}>
      <span className={ui.kicker}>Thực hành có hướng dẫn</span><h3>{title}</h3>
      {prompt && <p>{t(prompt)}</p>}
    </article>;
  }

  if (block.block_type === "callout") {
    return <article className={`${ui.block} ${ui.blockTone.callout}`}><span className={ui.kicker}>Lưu ý</span><h3>{title}</h3>{prompt && <p>{t(prompt)}</p>}</article>;
  }

  if (block.block_type === "compose_link") {
    // Nhãn mục tiêu A/B do backend gửi trong payload.goals; frontend chỉ hiển thị.
    const goals = Array.isArray(block.payload.goals) ? block.payload.goals.filter((g): g is string => typeof g === "string") : [];
    return <article className={`${ui.block} ${ui.blockTone.compose}`}><span className={ui.kicker}>Dùng vào sáng tác</span><h3>{title}</h3>
      {goals.length > 0 && <p className="flex flex-wrap gap-2">{goals.map((goal) => <Badge key={goal} tone="warning">{GOAL_LABELS[goal] ?? `Mục tiêu ${goal}`}</Badge>)}</p>}
      {items.length > 0 && <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>}
    </article>;
  }

  if (block.block_type === "summary") {
    return <article className={`${ui.block} ${ui.blockTone.summary}`}><span className={ui.kicker}>Tóm tắt</span><h3>{title}</h3>{items.length > 0 && <ul>{items.map((item) => <li key={item}>{t(item)}</li>)}</ul>}</article>;
  }

  return <article className={ui.block}>
    <span className={ui.kicker}>{BLOCK_LABELS[block.block_type] ?? "Nội dung"}</span><h3>{title}</h3>
    {paragraphs.map((paragraph) => <p key={paragraph}>{t(paragraph)}</p>)}
    {items.length > 0 && <ul>{items.map((item) => <li key={item}>{t(item)}</li>)}</ul>}
    {prompt && <p className="rounded-lg bg-primary-soft px-3 py-2 text-ink">{t(prompt)}</p>}
    {block.block_type === "theory" && title.toLowerCase().includes("triad") && <div className="mt-3 flex flex-wrap gap-2"><ChordInspector symbol="C" /><ChordInspector symbol="Cm" /><ChordInspector symbol="Cdim" /><ChordInspector symbol="Caug" /></div>}
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

  const kindLabel = EXERCISE_KIND_LABELS[exercise.kind] ?? exercise.kind.replace(/_/g, " ");
  return <div className={inline ? "grid gap-2 pt-3" : "grid gap-2 rounded-xl border border-line bg-bg p-4"}>
    <div className="flex items-center justify-between gap-2 text-xs font-semibold tracking-wide text-muted uppercase"><span>{kindLabel}</span>{attempted && <Badge tone={correct ? "success" : "warning"}>{correct ? "✓ Đã đúng" : "Đã thử"}</Badge>}</div>
    <b className="text-ink">{exercise.prompt}</b>
    {exercise.options && <div className="flex flex-wrap gap-2" role="group" aria-label="Các lựa chọn">{exercise.options.map((option) => <button type="button" key={option} aria-pressed={answer === option} className={ui.choice(answer === option)} onClick={() => setAnswer(option)}>{option}</button>)}</div>}
    {!exercise.options && (() => {
      const presentation = inputPresentation(exercise);
      return <>
        <input className={ui.input} aria-label={`Câu trả lời: ${exercise.prompt}`} value={answer} onChange={(event) => setAnswer(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void submit(); }} placeholder={presentation.placeholder} aria-describedby={`${exercise.id}-input-hint`} />
        {presentation.hint && <small id={`${exercise.id}-input-hint`} className={ui.hint}>{presentation.hint}</small>}
      </>;
    })()}
    <div><Button disabled={busy || !answer.trim()} onClick={submit}>{busy ? "Đang kiểm tra…" : attempted ? "Kiểm tra lại" : "Kiểm tra"}</Button></div>
    {result && <ResultBox correct={result.correct} title={result.correct ? "Chính xác!" : "Chưa đúng"}>
      {!result.correct && result.feedback && <p>{result.feedback}</p>}
      {result.explanation
        ? <p className={ui.explanation}><b>Giải thích:</b> {result.explanation}</p>
        : !result.correct && <p className={ui.muted}>Thử lại nhé. Nếu sai thêm {Math.max(1, 2 - result.wrong_attempts)} lần nữa, lời giải sẽ hiện ra.</p>}
    </ResultBox>}
    {error && <div className={ui.resultBad}>{error}</div>}
  </div>;
}

function Flashcard({ front, back, mode }: { front: string; back: string; mode: string }) {
  const [revealed, setRevealed] = useState(false);
  return <button type="button" aria-expanded={revealed} className="grid w-full gap-1 rounded-xl border border-line bg-bg p-4 text-left text-ink hover:border-primary" onClick={() => setRevealed((value) => !value)}>
    <small className="text-xs font-semibold tracking-wide text-muted uppercase">{REVIEW_MODE_LABELS[mode] ?? mode}</small><b>{front}</b><span className={revealed ? "text-ink" : "text-muted"}>{revealed ? back : "Tự nhớ đáp án trước, rồi bấm để lật thẻ"}</span>
  </button>;
}

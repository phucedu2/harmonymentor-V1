import { useEffect, useMemo, useState } from "react";
import { api, type ApiError, type LearningOverview, type LessonDetail, type LessonSummary } from "../api";
import LessonErrorBoundary from "../components/learning/LessonErrorBoundary";
import LessonRunner from "../components/learning/LessonRunner";
import { Alert } from "../components/ui/Alert";
import { PageLoader } from "../components/ui/PageLoader";
import { Badge, PageHeading, ProgressBar } from "../components/ui/Page";

export default function LearnPage() {
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [overview, setOverview] = useState<LearningOverview | null>(null);
  const [selected, setSelected] = useState<LessonDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshProgress = async () => {
    try { setOverview(await api.learningOverview()); }
    catch { /* Learn content remains usable if progress endpoint is temporarily unavailable. */ }
  };

  useEffect(() => {
    Promise.all([api.listLessons(), api.learningOverview()])
      .then(([lessonRows, progress]) => { setLessons(lessonRows); setOverview(progress); })
      .catch((e: ApiError) => setError(e.message ?? e.code))
      .finally(() => setLoading(false));
  }, []);

  const progressMap = useMemo(() => new Map((overview?.lessons ?? []).map((row) => [row.lesson_id, row])), [overview]);
  const nextLessonId = lessons.find((lesson) => lesson.exercise_count > 0 && progressMap.get(lesson.id)?.status !== "completed")?.id;

  const open = async (id: string) => {
    setError(null); setLoading(true);
    try {
      const detail = await api.getLesson(id);
      setSelected(detail);
      // Không gọi startLesson ở đây: LessonRunner tự gọi khi mở bài. Gọi ở cả hai nơi tạo 2 request
      // song song và từng làm PostgreSQL trả 500 (HM-010).
      await refreshProgress();
    } catch (e) {
      const err = e as ApiError;
      setError(err.message ?? err.code);
    } finally { setLoading(false); }
  };

  if (selected) return (
    <LessonErrorBoundary key={selected.id} onReset={() => { setSelected(null); void refreshProgress(); }}>
      <LessonRunner
        lesson={selected}
        initialProgress={progressMap.get(selected.id)}
        onBack={() => { setSelected(null); void refreshProgress(); }}
        onProgressChanged={() => { void refreshProgress(); }}
        onLessonOutdated={async () => {
          // Lỗi tải lại để LessonRunner báo cho người học, không thay bằng màn hình lỗi chung.
          const detail = await api.getLesson(selected.id);
          setSelected(detail);
          await refreshProgress();
        }}
      />
    </LessonErrorBoundary>
  );

  return <section>
    <PageHeading eyebrow="Học" title="Lộ trình học hòa âm">
      Học theo thứ tự: mỗi bài có lý thuyết ngắn, phần bấm thử trên piano, câu kiểm tra nhanh và bài kiểm tra cuối. Bài sau dùng kiến thức của bài trước.
    </PageHeading>
    {loading && <PageLoader label="Đang tải bài học…" />}
    {error && <Alert tone="danger">Không tải được bài học: {error}. Hãy thử tải lại trang.</Alert>}
    <ol className="grid gap-3" aria-label="Danh sách bài học">
      {lessons.map((lesson) => {
        const progress = progressMap.get(lesson.id);
        const runnable = lesson.exercise_count > 0;
        // Gợi ý thứ tự: bài chưa xong đầu tiên là "Học ngay"; bài sau nó vẫn mở nhưng nhắc học bài trước.
        const isNext = lesson.id === nextLessonId;
        const done = progress?.status === "completed";
        const started = progress?.status === "started";
        const label = done ? "Đã xong" : !runnable ? "Sắp có" : started ? "Đang học" : isNext ? "Học ngay" : `Nên học sau Bài ${lesson.order - 1}`;
        const tone = done ? "success" : runnable && (isNext || started) ? "primary" : "muted";
        const pct = done ? 100 : Math.round((progress?.correct_exercises ?? 0) / Math.max(1, lesson.exercise_count) * 100);
        return <li key={lesson.id}>
          <button
            type="button"
            data-lesson-id={lesson.id}
            onClick={() => runnable && void open(lesson.id)}
            disabled={!runnable}
            aria-label={`Bài ${lesson.order}. ${lesson.title}. ${label}`}
            className={`grid w-full grid-cols-[2.5rem_1fr] items-center gap-x-4 gap-y-2 rounded-2xl border bg-surface p-4 text-left transition-colors sm:grid-cols-[2.5rem_1fr_auto] ${runnable ? "border-line hover:border-primary" : "cursor-not-allowed border-dashed border-line bg-bg"} ${isNext ? "border-primary/50" : ""}`}
          >
            <span className={`grid size-10 place-items-center rounded-xl font-mono text-sm font-semibold ${done ? "bg-success-soft text-success" : runnable ? "bg-primary-soft text-primary-strong" : "bg-bg text-muted"}`} aria-hidden="true">{lesson.order}</span>
            <span className="min-w-0">
              <span className="block text-xs font-semibold tracking-wide text-muted uppercase">{lesson.track}</span>
              <span className="block font-semibold text-ink">{lesson.title}</span>
              <span className="mt-0.5 block text-sm text-muted">{runnable ? `${lesson.block_count} phần · ${lesson.exercise_count} câu hỏi · ${lesson.review_item_count} thẻ ôn` : "Nhóm đang soạn nội dung bài này"}</span>
              {runnable && <span className="mt-2 flex items-center gap-3">
                <ProgressBar className="w-32 shrink-0" value={pct} label={`Tiến độ bài ${lesson.order}`} />
                <span className="text-xs text-muted">{done ? "Hoàn thành" : started ? `Đã đúng ${progress?.correct_exercises}/${progress?.exercise_count} câu` : "Chưa bắt đầu"}</span>
              </span>}
            </span>
            <Badge tone={tone} className="col-start-2 justify-self-start sm:col-start-auto sm:justify-self-end">{label}</Badge>
          </button>
        </li>;
      })}
    </ol>
  </section>;
}

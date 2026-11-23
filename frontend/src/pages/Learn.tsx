import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router";
import { api, type ApiError, type LearningOverview, type LessonDetail, type LessonSummary } from "../api";
import LessonErrorBoundary from "../components/learning/LessonErrorBoundary";
import LessonRunner from "../components/learning/LessonRunner";
import { Alert } from "../components/ui/Alert";
import { PageLoader } from "../components/ui/PageLoader";
import { Badge, PageHeading, ProgressBar } from "../components/ui/Page";

const NEW_DAYS = 14;   // nhãn "Mới" cho bài AI đăng trong 14 ngày gần nhất

export default function LearnPage() {
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [overview, setOverview] = useState<LearningOverview | null>(null);
  const [selected, setSelected] = useState<LessonDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // ?bai=L02: mở thẳng bài được gợi ý từ Dashboard (RecommendedLessons). Chỉ mở một lần.
  const [params, setParams] = useSearchParams();
  // Ghi lại liên kết đã mở để StrictMode chạy effect hai lần không mở bài hai lần; trích dẫn mới của AI Tutor
  // (khác bài hoặc khác khối) vẫn mở được dù đang ở trang Học.
  const handledLink = useRef<string | null>(null);
  const [focusBlock, setFocusBlock] = useState<string | null>(null);

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
  // ADR-029 (7A): bài AI soạn từ tài liệu (Quản trị viên đã duyệt) gom vào mục "Kiến thức mới", không chen vào lộ trình.
  const course = lessons.filter((l) => !l.ai_generated);
  const fresh = lessons.filter((l) => l.ai_generated).sort((a, b) => (b.published_at ?? "").localeCompare(a.published_at ?? ""));
  const nextLessonId = course.find((lesson) => lesson.exercise_count > 0 && progressMap.get(lesson.id)?.status !== "completed")?.id;

  const open = async (id: string, preview = false) => {
    setError(null); setLoading(true);
    try {
      const detail = await api.getLesson(id, preview);
      setSelected(detail);
      // Không gọi startLesson ở đây: LessonRunner tự gọi khi mở bài. Gọi ở cả hai nơi tạo 2 request
      // song song và từng làm PostgreSQL trả 500 (HM-010).
      await refreshProgress();
    } catch (e) {
      const err = e as ApiError;
      setError(err.message ?? err.code);
    } finally { setLoading(false); }
  };

  // ?xem_truoc=AI-…: Quản trị viên xem trước bài AI đang ẩn (ADR-033). Lượt làm của admin là is_test nên không tính mastery.
  useEffect(() => {
    const preview = params.get("xem_truoc");
    if (!preview || loading || handledLink.current === `preview|${preview}`) return;
    handledLink.current = `preview|${preview}`;
    setParams({}, { replace: true });
    void open(preview, true);
  }, [params, loading]);

  useEffect(() => {
    const wanted = params.get("bai");
    const block = params.get("khoi");
    if (!wanted) { handledLink.current = null; return; }
    const key = `${wanted}|${block ?? ""}`;
    if (handledLink.current === key || loading || !lessons.some((l) => l.id === wanted)) return;
    handledLink.current = key;
    setParams({}, { replace: true });
    setFocusBlock(block);
    if (selected?.id === wanted) return;  // bài đang mở: chỉ cần chuyển tới khối
    void open(wanted);
  }, [params, loading, lessons]);

  if (selected) return (
    <LessonErrorBoundary key={selected.id} onReset={() => { setSelected(null); void refreshProgress(); }}>
      <LessonRunner
        lesson={selected}
        focusBlockId={focusBlock}
        initialProgress={progressMap.get(selected.id)}
        onBack={() => { setSelected(null); void refreshProgress(); }}
        onProgressChanged={() => { void refreshProgress(); }}
        onLessonOutdated={async () => {
          // Lỗi tải lại để LessonRunner báo cho người học, không thay bằng màn hình lỗi chung.
          const detail = await api.getLesson(selected.id, true);
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
    {fresh.length > 0 && <section aria-labelledby="kien-thuc-moi" className="mb-6 rounded-2xl border border-primary/40 bg-primary-soft/40 p-4">
      <h2 id="kien-thuc-moi" className="font-display text-lg font-semibold text-ink">Kiến thức mới</h2>
      <p className="mt-1 text-sm text-muted">Bài soạn từ tài liệu nhạc lý mới, chỉ gồm điều lộ trình chưa dạy. Quản trị viên đã duyệt trước khi đăng.
        Bài “Mở rộng” là kiến thức ngoài lộ trình: làm để biết thêm, không tính vào mức thành thạo.</p>
      <ul className="mt-3 grid gap-2 sm:grid-cols-2" aria-label="Danh sách kiến thức mới">
        {fresh.map((lesson) => {
          const done = progressMap.get(lesson.id)?.status === "completed";
          const isNew = !!lesson.published_at && Date.now() - Date.parse(lesson.published_at) < NEW_DAYS * 86_400_000;
          return <li key={lesson.id}>
            <button type="button" data-lesson-id={lesson.id} onClick={() => lesson.exercise_count > 0 && void open(lesson.id)}
              disabled={lesson.exercise_count === 0}
              className="grid h-full w-full gap-1 rounded-xl border border-line bg-surface p-3 text-left transition-colors hover:border-primary disabled:cursor-not-allowed">
              <span className="flex flex-wrap gap-1.5">
                {isNew && !done && <Badge tone="primary">Mới</Badge>}
                {lesson.expansion && <Badge tone="warning">Mở rộng</Badge>}
                {done && <Badge tone="success">Đã xong</Badge>}
              </span>
              <span className="font-semibold text-ink">{lesson.title}</span>
              <span className="text-sm text-muted">{lesson.block_count} phần · {lesson.exercise_count} câu hỏi</span>
            </button>
          </li>;
        })}
      </ul>
    </section>}
    <ol className="grid gap-3" aria-label="Danh sách bài học">
      {course.map((lesson) => {
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

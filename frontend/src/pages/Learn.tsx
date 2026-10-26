import { useEffect, useMemo, useState } from "react";
import { api, type ApiError, type LearningOverview, type LessonDetail, type LessonSummary } from "../api";
import LessonErrorBoundary from "../components/learning/LessonErrorBoundary";
import LessonRunner from "../components/learning/LessonRunner";

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
      />
    </LessonErrorBoundary>
  );

  return <section>
    <div className="page-heading"><div><span className="eyebrow">HỌC</span><h2>Lộ trình học hòa âm</h2></div>
      <p>Học theo thứ tự: mỗi bài có lý thuyết ngắn, phần bấm thử trên piano, câu kiểm tra nhanh và bài kiểm tra cuối. Bài sau dùng kiến thức của bài trước.</p></div>
    {loading && <article className="card">Đang tải bài học…</article>}
    {error && <article className="result bad">Không tải được bài học: {error}. Hãy thử tải lại trang.</article>}
    <div className="lesson-list">
      {lessons.map((lesson) => {
        const progress = progressMap.get(lesson.id);
        const runnable = lesson.exercise_count > 0;
        // Gợi ý thứ tự: bài chưa xong đầu tiên là "Học ngay"; bài sau nó vẫn mở nhưng nhắc học bài trước.
        const isNext = lesson.id === nextLessonId;
        const label = progress?.status === "completed" ? "Đã xong" : !runnable ? "Sắp có" : progress?.status === "started" ? "Đang học" : isNext ? "Học ngay" : `Nên học sau Bài ${lesson.order - 1}`;
        return <button className={`lesson-row ${!runnable ? "lesson-locked" : ""}`} key={lesson.id} onClick={() => runnable && void open(lesson.id)} disabled={!runnable}>
          <span className="lesson-index">{lesson.order}</span>
          <span className="lesson-main">
            <small>{lesson.track}</small><b>{lesson.title}</b>
            <span>{runnable ? `${lesson.block_count} phần · ${lesson.exercise_count} câu hỏi · ${lesson.review_item_count} thẻ ôn` : "Nhóm đang soạn nội dung bài này"}</span>
            {runnable && <span className="lesson-progress-inline"><span><i style={{ width: `${progress?.status === "completed" ? 100 : Math.round((progress?.correct_exercises ?? 0) / Math.max(1, lesson.exercise_count) * 100)}%` }} /></span><em>{progress?.status === "completed" ? "Hoàn thành" : progress?.status === "started" ? `Đã đúng ${progress.correct_exercises}/${progress.exercise_count} câu` : "Chưa bắt đầu"}</em></span>}
          </span>
          <span className={`status ${progress?.status === "completed" ? "completed" : runnable && (isNext || progress?.status === "started") ? "ready" : "locked"}`}>{label}</span>
        </button>;
      })}
    </div>
  </section>;
}

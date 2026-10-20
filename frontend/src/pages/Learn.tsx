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

  const open = async (id: string) => {
    setError(null); setLoading(true);
    try {
      const detail = await api.getLesson(id);
      setSelected(detail);
      await api.startLesson(id);
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
    <div className="page-heading"><div><span className="eyebrow">LEARN</span><h2>Lộ trình học hòa âm</h2></div>
      <p>Lessons 1–4 đang chạy thành vertical slice: theory → checkpoint → lesson quiz → review. Lessons 5–8 giữ source-audited specification để không vượt scope.</p></div>
    {loading && <article className="card">Đang tải Learning Platform…</article>}
    {error && <article className="result bad">{error}. Hãy kiểm tra FastAPI backend.</article>}
    <div className="lesson-list">
      {lessons.map((lesson) => {
        const progress = progressMap.get(lesson.id);
        const runnable = lesson.exercise_count > 0;
        return <button className={`lesson-row ${!runnable ? "lesson-locked" : ""}`} key={lesson.id} onClick={() => runnable && void open(lesson.id)} disabled={!runnable}>
          <span className="lesson-index">{lesson.order}</span>
          <span className="lesson-main">
            <small>{lesson.track}</small><b>{lesson.title}</b>
            <span>{lesson.exercise_count} quiz · {lesson.review_item_count} review cards · {lesson.block_count} blocks</span>
            {runnable && <span className="lesson-progress-inline"><span><i style={{ width: `${progress?.practice_progress_percent ?? 0}%` }} /></span><em>{progress?.status === "completed" ? "Hoàn thành" : progress?.status === "started" ? `Đã làm ${progress.attempted_exercises}/${progress.exercise_count}` : "Chưa bắt đầu"}</em></span>}
          </span>
          <span className={`status ${progress?.status === "completed" ? "completed" : lesson.status}`}>{progress?.status === "completed" ? "completed" : lesson.status}</span>
        </button>;
      })}
    </div>
  </section>;
}

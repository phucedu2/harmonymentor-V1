import { useEffect, useMemo, useState } from "react";
import { api, type LearningOverview } from "../api";

export default function DashboardPage({ onNavigate }: { onNavigate: (page: "learn" | "practice" | "progress") => void }) {
  const [overview, setOverview] = useState<LearningOverview | null>(null);
  useEffect(() => { api.learningOverview().then(setOverview).catch(() => setOverview(null)); }, []);

  const nextLesson = useMemo(() => {
    if (!overview) return null;
    return overview.lessons.find((lesson) => lesson.exercise_count > 0 && lesson.status !== "completed")
      ?? overview.lessons.find((lesson) => lesson.exercise_count > 0)
      ?? null;
  }, [overview]);

  return <section>
    <div className="page-heading"><div><span className="eyebrow">DASHBOARD</span><h2>Học – nhớ – vận dụng hòa âm</h2></div>
      <p>Phase 2 adds beginner-safe explanations, notation, virtual piano, audio playback and metronome to the learning loop.</p></div>
    <div className="metric-grid four-metrics">
      <article className="card metric"><b>{overview?.completed_lessons ?? "–"}/{overview?.total_lessons ?? "–"}</b><span>lesson hoàn thành</span></article>
      <article className="card metric"><b>{overview?.started_lessons ?? "–"}</b><span>lesson đã bắt đầu</span></article>
      <article className="card metric"><b>{overview?.due_reviews ?? "–"}</b><span>review đến hạn</span></article>
      <article className="card metric"><b>{overview?.upcoming_reviews ?? "–"}</b><span>review đã lên lịch</span></article>
    </div>

    <div className="dashboard-grid">
      <article className="card hero-card">
        <span className="pill">Continue learning</span>
        <h3>{nextLesson ? `${nextLesson.order}. ${nextLesson.title}` : "Learning Platform"}</h3>
        {nextLesson ? <>
          <p>{nextLesson.status === "not_started" ? "Bắt đầu lesson tiếp theo trong vertical slice." : `Đã làm ${nextLesson.attempted_exercises}/${nextLesson.exercise_count} câu. Tiếp tục từ checkpoint/quiz.`}</p>
          <div className="progress-track"><span style={{ width: `${nextLesson.practice_progress_percent}%` }} /></div>
        </> : <p>Backend chưa trả Learning Overview.</p>}
        <div className="actions"><button onClick={() => onNavigate("learn")}>Mở Learn</button><button className="ghost" onClick={() => onNavigate("practice")}>Practice tự do</button></div>
      </article>

      <article className="card review-today-card">
        <span className="section-kicker">Review today</span>
        <h3>{overview?.due_reviews ?? 0} thẻ đến hạn</h3>
        <p className="muted">Spaced review chỉ được kích hoạt sau khi hoàn thành lesson. Thẻ mới bắt đầu ở +1 ngày.</p>
        <button className="ghost" onClick={() => onNavigate("progress")}>Xem tiến độ & lịch ôn</button>
      </article>
    </div>
  </section>;
}

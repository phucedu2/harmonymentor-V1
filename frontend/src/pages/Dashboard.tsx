import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { api, type LearningOverview } from "../api";
import { useAuth } from "../auth/AuthProvider";

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [overview, setOverview] = useState<LearningOverview | null>(null);
  useEffect(() => { api.learningOverview().then(setOverview).catch(() => setOverview(null)); }, []);

  const nextLesson = useMemo(() => {
    if (!overview) return null;
    return overview.lessons.find((lesson) => lesson.exercise_count > 0 && lesson.status !== "completed")
      ?? overview.lessons.find((lesson) => lesson.exercise_count > 0)
      ?? null;
  }, [overview]);

  return <section>
    <div className="page-heading"><div><span className="eyebrow">TỔNG QUAN</span><h2>Chào {user?.display_name}</h2></div>
      <p>{overview && overview.started_lessons === 0 ? "Bạn chưa cần biết gì về nhạc lý. Hãy bắt đầu từ Bài 1: chỉ cần nhìn bàn phím piano và đếm." : "Học tiếp bài đang dở, rồi ôn các thẻ đến hạn để nhớ lâu."}</p></div>
    <div className="metric-grid four-metrics">
      <article className="card metric"><b>{overview?.completed_lessons ?? "–"}/{overview?.lessons.filter((lesson) => lesson.exercise_count > 0).length ?? "–"}</b><span>bài đã hoàn thành</span></article>
      <article className="card metric"><b>{overview?.started_lessons ?? "–"}</b><span>bài đã bắt đầu</span></article>
      <article className="card metric"><b>{overview?.due_reviews ?? "–"}</b><span>thẻ cần ôn hôm nay</span></article>
      <article className="card metric"><b>{overview?.upcoming_reviews ?? "–"}</b><span>thẻ đã lên lịch</span></article>
    </div>

    <div className="dashboard-grid">
      <article className="card hero-card">
        <span className="pill">{nextLesson?.status === "not_started" ? "Bắt đầu học" : "Học tiếp"}</span>
        <h3>{nextLesson ? `Bài ${nextLesson.order}. ${nextLesson.title}` : "Đang tải lộ trình…"}</h3>
        {nextLesson ? <>
          <p>{nextLesson.status === "not_started" ? "Bài tiếp theo trong lộ trình của bạn." : `Đã đúng ${nextLesson.correct_exercises}/${nextLesson.exercise_count} câu. Học tiếp từ chỗ bạn dừng.`}</p>
          <div className="progress-track"><span style={{ width: `${Math.round(nextLesson.correct_exercises / Math.max(1, nextLesson.exercise_count) * 100)}%` }} /></div>
        </> : <p className="muted">Nếu trang không tải được, hãy thử tải lại.</p>}
        <div className="actions"><button onClick={() => navigate("/app/hoc")}>{nextLesson?.status === "not_started" ? "Bắt đầu bài học" : "Học tiếp"}</button><button className="ghost" onClick={() => navigate("/app/luyen-tap")}>Luyện tập tự do</button></div>
      </article>

      <article className="card review-today-card">
        <span className="section-kicker">Ôn tập hôm nay</span>
        <h3>{overview?.due_reviews ?? 0} thẻ cần ôn</h3>
        <p className="muted">Thẻ ôn xuất hiện sau khi bạn hoàn thành một bài. Lần ôn đầu là ngày hôm sau; nhớ đúng thì lần sau giãn ra 2, 4, 8, 16 ngày.</p>
        <button className="ghost" onClick={() => navigate("/app/tien-do")}>Xem tiến độ & lịch ôn</button>
      </article>
    </div>
  </section>;
}

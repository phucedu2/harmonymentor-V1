import { useEffect, useState } from "react";
import { api, type ApiError, type LearningOverview, type ReviewState } from "../api";

export default function ProgressPage() {
  const [overview, setOverview] = useState<LearningOverview | null>(null);
  const [due, setDue] = useState<ReviewState[]>([]);
  const [scheduled, setScheduled] = useState<ReviewState[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setError(null);
    try {
      const [learning, dueRows, allRows] = await Promise.all([
        api.learningOverview(),
        api.dueReviews("demo-user", false),
        api.dueReviews("demo-user", true),
      ]);
      setOverview(learning);
      setDue(dueRows);
      setScheduled(allRows.filter((item) => !dueRows.some((dueItem) => dueItem.review_item_id === item.review_item_id)));
    } catch (e) {
      const err = e as ApiError;
      setError(err.message ?? err.code);
    }
  };

  useEffect(() => { void load(); }, []);

  return <section>
    <div className="page-heading"><div><span className="eyebrow">PROGRESS</span><h2>Tiến độ học & Review Queue</h2></div><p>Progress được tổng hợp từ Attempt + LessonProgress + ReviewState thật, không dùng số liệu giả.</p></div>
    {error && <div className="result bad">{error}</div>}

    <div className="metric-grid">
      <article className="card metric"><b>{overview?.completed_lessons ?? 0}</b><span>lesson completed</span></article>
      <article className="card metric"><b>{due.length}</b><span>thẻ đến hạn</span></article>
      <article className="card metric"><b>{scheduled.length}</b><span>thẻ sắp tới</span></article>
    </div>

    <article className="card block">
      <div className="section-heading"><div><span className="section-kicker">Lessons</span><h3>Practice evidence</h3></div><span className="muted">Tính theo số exercise distinct đã làm</span></div>
      <div className="progress-lesson-list">{overview?.lessons.map((lesson) => <div className="progress-lesson" key={lesson.lesson_id}>
        <div className="progress-lesson-title"><span>{lesson.order}</span><div><b>{lesson.title}</b><small>{lesson.track} · {lesson.status}</small></div></div>
        <div className="progress-track"><span style={{ width: `${lesson.practice_progress_percent}%` }} /></div>
        <div className="progress-stats"><span>{lesson.attempted_exercises}/{lesson.exercise_count} exercises</span><span>{lesson.correct_exercises} từng đúng</span><span>{lesson.attempt_count} attempts</span></div>
      </div>)}</div>
    </article>

    <div className="two-col block">
      <article className="card"><h3>Review đến hạn</h3>{due.length === 0 ? <p className="muted">Chưa có thẻ đến hạn. Sau khi hoàn thành lesson, lượt đầu được lên lịch sau 1 ngày.</p> : <div className="review-list">{due.map((item) => <ReviewCard key={item.review_item_id} item={item} onDone={load} />)}</div>}</article>
      <article className="card"><h3>Đã lên lịch</h3>{scheduled.length === 0 ? <p className="muted">Chưa có thẻ tương lai.</p> : <ul className="scheduled-list">{scheduled.slice(0, 12).map((item) => <li key={item.review_item_id}><b>{item.front}</b><small>Stage {item.stage} · {item.interval_days} ngày · {new Date(item.due_at).toLocaleString()}</small></li>)}</ul>}</article>
    </div>
  </section>;
}

function ReviewCard({ item, onDone }: { item: ReviewState; onDone: () => Promise<void> }) {
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    if (!answer.trim()) return;
    setBusy(true);
    try {
      const result = await api.answerReview(item.review_item_id, answer, "auto");
      setFeedback(`${result.correct ? "Đúng" : "Chưa đúng"}. Lịch tiếp theo: ${result.interval_days} ngày.`);
      await onDone();
    } catch (e) {
      const err = e as ApiError;
      setFeedback(err.message ?? err.code);
    } finally { setBusy(false); }
  };
  return <div className="review-card"><small>{item.mode} · {item.skill_id}</small><b>{item.front}</b><input value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder="Tự nhớ rồi nhập đáp án" /><button disabled={busy || !answer.trim()} onClick={submit}>Ôn thẻ</button>{feedback && <span>{feedback}</span>}</div>;
}

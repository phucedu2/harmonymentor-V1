import { useEffect, useState } from "react";
import { api, type ApiError, type LearningOverview, type ReviewState } from "../api";
import { REVIEW_MODE_LABELS } from "../components/learning/LessonRunner";

const STATUS_LABELS: Record<string, string> = { not_started: "Chưa bắt đầu", started: "Đang học", completed: "Đã hoàn thành" };

export default function ProgressPage() {
  const [overview, setOverview] = useState<LearningOverview | null>(null);
  const [due, setDue] = useState<ReviewState[]>([]);
  const [scheduled, setScheduled] = useState<ReviewState[]>([]);
  const [error, setError] = useState<string | null>(null);
  // Thẻ vừa ôn rời khỏi danh sách đến hạn, nên kết quả hiện ở đây thay vì trên thẻ.
  const [notice, setNotice] = useState<{ good: boolean; text: string } | null>(null);

  const load = async () => {
    setError(null);
    try {
      const [learning, dueRows, allRows] = await Promise.all([
        api.learningOverview(),
        api.dueReviews(false),
        api.dueReviews(true),
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
    <div className="page-heading"><div><span className="eyebrow">TIẾN ĐỘ</span><h2>Tiến độ học & lịch ôn</h2></div><p>Số liệu lấy từ chính các lần bạn làm bài và ôn thẻ.</p></div>
    {error && <div className="result bad">{error}</div>}

    <div className="metric-grid">
      <article className="card metric"><b>{overview?.completed_lessons ?? 0}</b><span>bài đã hoàn thành</span></article>
      <article className="card metric"><b>{due.length}</b><span>thẻ đến hạn</span></article>
      <article className="card metric"><b>{scheduled.length}</b><span>thẻ sắp tới</span></article>
    </div>

    <article className="card block">
      <div className="section-heading"><div><span className="section-kicker">Bài học</span><h3>Bạn đã làm được gì</h3></div><span className="muted">Tính theo số câu đã trả lời đúng ít nhất một lần</span></div>
      <div className="progress-lesson-list">{overview?.lessons.filter((lesson) => lesson.exercise_count > 0).map((lesson) => <div className="progress-lesson" key={lesson.lesson_id}>
        <div className="progress-lesson-title"><span>{lesson.order}</span><div><b>{lesson.title}</b><small>{lesson.track} · {STATUS_LABELS[lesson.status] ?? lesson.status}</small></div></div>
        <div className="progress-track"><span style={{ width: `${lesson.status === "completed" ? 100 : Math.round(lesson.correct_exercises / Math.max(1, lesson.exercise_count) * 100)}%` }} /></div>
        <div className="progress-stats"><span>Đúng {lesson.correct_exercises}/{lesson.exercise_count} câu</span><span>{lesson.attempt_count} lần trả lời</span></div>
      </div>)}</div>
    </article>

    <div className="two-col block">
      <article className="card"><h3>Thẻ cần ôn hôm nay</h3>{due.length === 0 ? <p className="muted">Chưa có thẻ cần ôn. Sau khi hoàn thành một bài, lượt ôn đầu tiên là ngày hôm sau.</p> : <div className="review-list">{due.map((item) => <ReviewCard key={item.review_item_id} item={item} onDone={async (result) => { setNotice(result); await load(); }} />)}</div>}{notice && <div className={`result ${notice.good ? "good" : "bad"}`} role="status">{notice.text}</div>}</article>
      <article className="card"><h3>Đã lên lịch</h3>{scheduled.length === 0 ? <p className="muted">Chưa có thẻ tương lai.</p> : <ul className="scheduled-list">{scheduled.slice(0, 12).map((item) => <li key={item.review_item_id}><b>{item.front}</b><small>Hộp {item.leitner_box}/5 · ôn lại ngày {new Date(item.due_at).toLocaleDateString("vi-VN")}</small></li>)}</ul>}</article>
    </div>
  </section>;
}

function ReviewCard({ item, onDone }: { item: ReviewState; onDone: (result: { good: boolean; text: string }) => Promise<void> }) {
  const [answer, setAnswer] = useState("");
  const [revealed, setRevealed] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const send = async (value: string, rating: "auto" | "good" | "again") => {
    setBusy(true);
    try {
      const result = await api.answerReview(item.review_item_id, value, rating);
      const next = `ôn lại sau ${result.interval_days} ngày (hộp ${result.leitner_box}/5)`;
      await onDone({
        good: result.correct,
        text: result.correct ? `"${item.front}": đúng. Thẻ lên hộp ${result.leitner_box}, ${next}.` : `"${item.front}": chưa đúng. ${result.feedback ?? ""} Thẻ về hộp 1, ${next}.`,
      });
    } catch (e) {
      const err = e as ApiError;
      setFeedback(err.message ?? err.code);
    } finally { setBusy(false); }
  };
  const label = <small>{REVIEW_MODE_LABELS[item.mode] ?? item.mode} · hộp {item.leitner_box}/5</small>;
  // Thẻ ý mở: máy không chấm được câu tự luận, nên người học lật thẻ và tự đánh giá (kiểu Anki).
  if (item.self_check) return <div className="review-card">{label}<b>{item.front}</b>
    {revealed
      ? <><p className="review-back">{item.back}</p><div className="review-actions">
          <button disabled={busy} onClick={() => void send("", "good")}>Mình đã nhớ đúng</button>
          <button className="ghost" disabled={busy} onClick={() => void send("", "again")}>Mình chưa nhớ</button>
        </div></>
      : <button className="ghost" onClick={() => setRevealed(true)}>Tự nhớ trong đầu, rồi lật thẻ</button>}
    {feedback && <span>{feedback}</span>}
  </div>;
  return <div className="review-card">{label}<b>{item.front}</b><input value={answer} onChange={(event) => setAnswer(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && answer.trim()) void send(answer, "auto"); }} placeholder="Nhập đáp án từ trí nhớ" /><button disabled={busy || !answer.trim()} onClick={() => void send(answer, "auto")}>Kiểm tra</button>{feedback && <span>{feedback}</span>}</div>;
}

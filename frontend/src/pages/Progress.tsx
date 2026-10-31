import { useEffect, useState } from "react";
import { api, type ApiError, type LearningOverview, type ReviewState } from "../api";
import { REVIEW_MODE_LABELS } from "../components/learning/LessonRunner";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Card, CardTitle, Kicker, Metric, PageHeading, ProgressBar, ResultBox } from "../components/ui/Page";

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
    <PageHeading eyebrow="Tiến độ" title="Tiến độ học và lịch ôn">Số liệu lấy từ chính các lần bạn làm bài và ôn thẻ.</PageHeading>
    {error && <div className="mb-4"><Alert tone="danger">{error}</Alert></div>}

    <div className="mb-4 grid grid-cols-3 gap-3">
      <Metric value={overview?.completed_lessons ?? 0} label="bài đã hoàn thành" />
      <Metric value={due.length} label="thẻ đến hạn" />
      <Metric value={scheduled.length} label="thẻ sắp tới" />
    </div>

    <div className="mb-4 grid gap-4 md:grid-cols-2">
      <Card>
        <CardTitle>Thẻ cần ôn hôm nay</CardTitle>
        {due.length === 0
          ? <p className="mt-2 text-muted">Chưa có thẻ cần ôn. Sau khi hoàn thành một bài, lượt ôn đầu tiên là ngày hôm sau.</p>
          : <div className="mt-3 grid gap-3">{due.map((item) => <ReviewCard key={item.review_item_id} item={item} onDone={async (result) => { setNotice(result); await load(); }} />)}</div>}
        {notice && <ResultBox correct={notice.good} title={notice.good ? "Nhớ đúng" : "Chưa đúng"}>{notice.text}</ResultBox>}
      </Card>
      <Card>
        <CardTitle>Đã lên lịch</CardTitle>
        {scheduled.length === 0 ? <p className="mt-2 text-muted">Chưa có thẻ tương lai.</p> : <ul className="mt-3 divide-y divide-line">
          {scheduled.slice(0, 12).map((item) => <li key={item.review_item_id} className="py-2">
            <b className="block text-ink">{item.front}</b>
            <small className="text-muted">Hộp {item.leitner_box}/5 · ôn lại ngày {new Date(item.due_at).toLocaleDateString("vi-VN")}</small>
          </li>)}
        </ul>}
      </Card>
    </div>

    <Card>
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div><Kicker>Bài học</Kicker><CardTitle className="mt-1">Bạn đã làm được gì</CardTitle></div>
        <span className="text-sm text-muted">Tính theo số câu đã trả lời đúng ít nhất một lần</span>
      </div>
      <ul className="mt-4 grid gap-4">{overview?.lessons.filter((lesson) => lesson.exercise_count > 0).map((lesson) => <li key={lesson.lesson_id} className="grid gap-2">
        <div className="flex items-center gap-3">
          <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-primary-soft font-mono text-sm font-semibold text-primary-strong" aria-hidden="true">{lesson.order}</span>
          <div className="min-w-0"><b className="block text-ink">{lesson.title}</b><small className="text-muted">{lesson.track} · {STATUS_LABELS[lesson.status] ?? lesson.status}</small></div>
        </div>
        <ProgressBar value={lesson.status === "completed" ? 100 : lesson.correct_exercises / Math.max(1, lesson.exercise_count) * 100} label={`Tiến độ bài ${lesson.order}`} />
        <div className="flex justify-between text-sm text-muted"><span>Đúng {lesson.correct_exercises}/{lesson.exercise_count} câu</span><span>{lesson.attempt_count} lần trả lời</span></div>
      </li>)}</ul>
    </Card>
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
  const label = <small className="text-xs font-semibold tracking-wide text-muted uppercase">{REVIEW_MODE_LABELS[item.mode] ?? item.mode} · hộp {item.leitner_box}/5</small>;
  const box = "grid gap-2 rounded-xl border border-line bg-bg p-4";
  // Thẻ ý mở: máy không chấm được câu tự luận, nên người học lật thẻ và tự đánh giá (kiểu Anki).
  if (item.self_check) return <div className={box}>{label}<b className="text-ink">{item.front}</b>
    {revealed
      ? <><p className="rounded-lg bg-surface p-3 text-ink">{item.back}</p><div className="flex flex-wrap gap-2">
          <Button disabled={busy} onClick={() => void send("", "good")}>Mình đã nhớ đúng</Button>
          <Button variant="secondary" disabled={busy} onClick={() => void send("", "again")}>Mình chưa nhớ</Button>
        </div></>
      : <Button variant="secondary" className="justify-self-start" onClick={() => setRevealed(true)}>Tự nhớ trong đầu, rồi lật thẻ</Button>}
    {feedback && <Alert tone="danger">{feedback}</Alert>}
  </div>;
  return <div className={box}>{label}<b className="text-ink">{item.front}</b>
    <div className="flex flex-wrap gap-2">
      <input aria-label={`Đáp án cho thẻ: ${item.front}`} className="min-h-11 min-w-0 flex-1 rounded-lg border border-line bg-surface px-3 text-base text-ink" value={answer} onChange={(event) => setAnswer(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && answer.trim()) void send(answer, "auto"); }} placeholder="Nhập đáp án từ trí nhớ" />
      <Button disabled={busy || !answer.trim()} onClick={() => void send(answer, "auto")}>Kiểm tra</Button>
    </div>
    {feedback && <Alert tone="danger">{feedback}</Alert>}
  </div>;
}

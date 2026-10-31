import { useEffect, useMemo, useState } from "react";
import { api, type LearningOverview } from "../api";
import { useAuth } from "../auth/AuthProvider";
import { ButtonLink } from "../components/ui/Button";
import { Badge, Card, CardTitle, Kicker, Metric, PageHeading, ProgressBar } from "../components/ui/Page";

export default function DashboardPage() {
  const { user } = useAuth();
  const [overview, setOverview] = useState<LearningOverview | null>(null);
  useEffect(() => { api.learningOverview().then(setOverview).catch(() => setOverview(null)); }, []);

  const nextLesson = useMemo(() => {
    if (!overview) return null;
    return overview.lessons.find((lesson) => lesson.exercise_count > 0 && lesson.status !== "completed")
      ?? overview.lessons.find((lesson) => lesson.exercise_count > 0)
      ?? null;
  }, [overview]);
  const runnable = overview?.lessons.filter((lesson) => lesson.exercise_count > 0).length;
  const fresh = nextLesson?.status === "not_started";

  return <section>
    <PageHeading eyebrow="Tổng quan" title={`Chào ${user?.display_name ?? "bạn"}`}>
      {overview && overview.started_lessons === 0
        ? "Bạn chưa cần biết gì về nhạc lý. Hãy bắt đầu từ Bài 1: chỉ cần nhìn bàn phím piano và đếm."
        : "Học tiếp bài đang dở, rồi ôn các thẻ đến hạn để nhớ lâu."}
    </PageHeading>

    {/* Một việc chính: học tiếp. Nút chính đặt ngay đầu trang để luôn thấy trên màn 360px. */}
    <Card className="mb-4 border-primary/30 p-6">
      <Badge>{fresh ? "Bắt đầu học" : "Học tiếp"}</Badge>
      <CardTitle className="mt-3 text-2xl">{nextLesson ? `Bài ${nextLesson.order}. ${nextLesson.title}` : "Đang tải lộ trình…"}</CardTitle>
      {nextLesson ? <>
        <p className="mt-2 text-muted">{fresh ? "Bài tiếp theo trong lộ trình của bạn." : `Đã đúng ${nextLesson.correct_exercises}/${nextLesson.exercise_count} câu. Học tiếp từ chỗ bạn dừng.`}</p>
        <ProgressBar className="mt-4" value={nextLesson.correct_exercises / Math.max(1, nextLesson.exercise_count) * 100} label={`Tiến độ ${nextLesson.title}`} />
      </> : <p className="mt-2 text-muted">Nếu trang không tải được, hãy thử tải lại.</p>}
      <div className="mt-5 flex flex-wrap gap-3">
        <ButtonLink to="/app/hoc" size="lg">{fresh ? "Bắt đầu bài học" : "Học tiếp"}</ButtonLink>
        <ButtonLink to="/app/luyen-tap" variant="secondary" size="lg">Luyện tập tự do</ButtonLink>
      </div>
    </Card>

    <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
      <Metric value={`${overview?.completed_lessons ?? "–"}/${runnable ?? "–"}`} label="bài đã hoàn thành" />
      <Metric value={overview?.started_lessons ?? "–"} label="bài đã bắt đầu" />
      <Metric value={overview?.due_reviews ?? "–"} label="thẻ cần ôn hôm nay" />
      <Metric value={overview?.upcoming_reviews ?? "–"} label="thẻ đã lên lịch" />
    </div>

    <Card>
      <Kicker>Ôn tập hôm nay</Kicker>
      <CardTitle className="mt-1">{overview?.due_reviews ?? 0} thẻ cần ôn</CardTitle>
      <p className="mt-2 text-muted">Thẻ ôn xuất hiện sau khi bạn hoàn thành một bài. Lần ôn đầu là ngày hôm sau; nhớ đúng thì lần sau giãn ra 2, 4, 8, 16 ngày.</p>
      <ButtonLink to="/app/tien-do" variant="ghost" className="mt-3 -ml-4">Xem tiến độ và lịch ôn</ButtonLink>
    </Card>
  </section>;
}

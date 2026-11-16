import { useEffect, useMemo, useState } from "react";
import { api, type LearningOverview, type PlacementStatus } from "../api";
import { useAuth } from "../auth/AuthProvider";
import RecommendedLessons from "../components/learning/RecommendedLessons";
import { ButtonLink } from "../components/ui/Button";
import { Badge, Card, CardTitle, Kicker, Metric, PageHeading, ProgressBar } from "../components/ui/Page";

export default function DashboardPage() {
  const { user } = useAuth();
  const [overview, setOverview] = useState<LearningOverview | null>(null);
  const [placement, setPlacement] = useState<PlacementStatus | null>(null);
  useEffect(() => { api.learningOverview().then(setOverview).catch(() => setOverview(null)); }, []);
  useEffect(() => { api.placement().then((p) => setPlacement(p.status)).catch(() => setPlacement(null)); }, []);

  const nextLesson = useMemo(() => {
    if (!overview) return null;
    return overview.lessons.find((lesson) => lesson.exercise_count > 0 && lesson.status !== "completed")
      ?? overview.lessons.find((lesson) => lesson.exercise_count > 0)
      ?? null;
  }, [overview]);
  const runnable = overview?.lessons.filter((lesson) => lesson.exercise_count > 0).length;
  const fresh = nextLesson?.status === "not_started";
  const showPlacement = placement === "not_started" && overview?.started_lessons === 0;
  // Còn đang tải (chưa biết) và người học chưa bắt đầu bài nào: giữ chỗ để không giật bố cục.
  const placementPending = !showPlacement && (placement === null || overview === null);

  return <section>
    <PageHeading eyebrow="Tổng quan" title={`Chào ${user?.display_name ?? "bạn"}`}>
      {overview && overview.started_lessons === 0
        ? "Bạn chưa cần biết gì về nhạc lý. Hãy bắt đầu từ Bài 1: chỉ cần nhìn bàn phím piano và đếm."
        : "Học tiếp bài đang dở, rồi ôn các thẻ đến hạn để nhớ lâu."}
    </PageHeading>

    {/* Một việc chính: học tiếp. Nút chính đặt ngay đầu trang để luôn thấy trên màn 360px. */}
    <Card className="mb-4 border-primary/30 p-6">
      <Badge>{fresh ? "Bắt đầu học" : "Học tiếp"}</Badge>
      {/* FE-017: tiêu đề luôn chừa 2 dòng và thanh tiến độ luôn có mặt, để lúc dữ liệu về thẻ không đổi chiều cao. */}
      <CardTitle className="mt-3 min-h-16 text-2xl">{nextLesson ? `Bài ${nextLesson.order}. ${nextLesson.title}` : "Đang tải lộ trình…"}</CardTitle>
      <p className="mt-2 min-h-6 text-muted">{nextLesson ? (fresh ? "Bài tiếp theo trong lộ trình của bạn." : `Đã đúng ${nextLesson.correct_exercises}/${nextLesson.exercise_count} câu. Học tiếp từ chỗ bạn dừng.`) : "Nếu trang không tải được, hãy thử tải lại."}</p>
      <ProgressBar className="mt-4" value={nextLesson ? nextLesson.correct_exercises / Math.max(1, nextLesson.exercise_count) * 100 : 0} label={nextLesson ? `Tiến độ ${nextLesson.title}` : "Tiến độ bài học tiếp theo"} />
      <div className="mt-5 grid gap-3 sm:flex sm:flex-wrap">
        <ButtonLink to="/app/hoc" size="lg">{fresh ? "Bắt đầu bài học" : "Học tiếp"}</ButtonLink>
        <ButtonLink to="/app/luyen-tap" variant="secondary" size="lg">Luyện tập tự do</ButtonLink>
      </div>
    </Card>

    {/* FE-011: lời mời kiểm tra đầu vào nằm dưới CTA chính (không chen lên trên). FE-017: giữ chỗ khi chưa biết
        trạng thái, nếu không thẻ này hiện muộn và đẩy cả trang xuống (CLS 0,22). */}
    {showPlacement ? <Card className="mb-4 flex min-h-40 flex-col items-start justify-center p-4">
      <p className="mb-2">Đã biết chút nhạc lý? Làm bài kiểm tra đầu vào 12 câu để hệ thống gợi ý bài phù hợp hơn.</p>
      <ButtonLink to="/app/kiem-tra-dau-vao" variant="secondary">Làm bài kiểm tra đầu vào</ButtonLink>
    </Card> : placementPending ? <div aria-hidden="true" className="mb-4 min-h-40" /> : null}

    <RecommendedLessons ready={overview !== null} excludeLessonId={fresh ? nextLesson?.lesson_id : undefined} />

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

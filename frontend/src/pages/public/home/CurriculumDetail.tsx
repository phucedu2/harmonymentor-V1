import { useState } from "react";
import { Link } from "react-router";
import type { LessonSummary } from "../../../api";
import { Alert } from "../../../components/ui/Alert";
import { Button } from "../../../components/ui/Button";
import { useAuth } from "../../../auth/AuthProvider";
import { buildModules, dangSoan, KY_HIEU_DANG_CAU, TEN_DANG_CAU, uocLuongPhut } from "./curriculum";
import { useLazySection, useLessonKinds, usePublicLessons } from "./data";
import { curriculum } from "./copy";

function KindBadges({ kinds }: { kinds: string[] }) {
  if (kinds.length === 0) return null;
  return (
    <ul className="mt-3 flex flex-wrap gap-1.5">
      {kinds.map((kind) => (
        <li key={kind} className="hm-kind">
          <span aria-hidden="true" className="font-mono">{KY_HIEU_DANG_CAU[kind] ?? "•"}</span>
          {TEN_DANG_CAU[kind] ?? kind}
        </li>
      ))}
    </ul>
  );
}

function LessonCard({ lesson, kinds, to }: { lesson: LessonSummary; kinds: string[]; to: string }) {
  // Trên điện thoại không có rê chuột nên thẻ mở bằng cách chạm; máy tính vẫn mở khi rê chuột (CSS).
  const [open, setOpen] = useState(false);
  const soan = dangSoan(lesson);
  const headingId = `bai-${lesson.id}`;

  return (
    <article className="hm-card reveal" data-open={open}>
      <button type="button" className="hm-card-top" aria-expanded={open} aria-controls={`${headingId}-chi-tiet`} onClick={() => setOpen((v) => !v)}>
        <div className="flex items-start gap-3">
          <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-md bg-[var(--w-ivory)] font-mono text-xs font-semibold text-[var(--w-deep-text)]">
            {lesson.order}
          </span>
          <div className="min-w-0 flex-1">
            <h4 id={headingId} className="font-semibold leading-snug text-ink">{lesson.title}</h4>
            {lesson.objectives[0] && <p className="mt-1.5 text-sm text-[var(--w-ink-soft)]">{lesson.objectives[0]}</p>}
          </div>
          {soan && <span className="shrink-0 rounded-full bg-[var(--w-ivory)] px-2 py-0.5 text-xs text-[var(--w-ink-soft)]">{curriculum.draftBadge}</span>}
        </div>
        <p className="mt-3 font-mono text-xs text-[var(--w-ink-soft)]">
          {lesson.block_count} phần lý thuyết · {lesson.exercise_count} câu hỏi · {lesson.review_item_count} thẻ ôn ·{" "}
          {uocLuongPhut(lesson.block_count, lesson.exercise_count)} phút
        </p>
        <KindBadges kinds={kinds} />
      </button>

      <div className="hm-card-more" id={`${headingId}-chi-tiet`}>
        <div>
          <div className="border-t border-[var(--w-line)] px-5 py-4">
            {lesson.objectives.length > 1 && (
              <>
                <p className="text-xs font-semibold uppercase tracking-wider text-[var(--w-ink-soft)]">Mục tiêu của bài</p>
                <ul className="mt-2 space-y-1.5 text-sm text-[var(--w-ink-soft)]">
                  {lesson.objectives.map((o) => <li key={o}>· {o}</li>)}
                </ul>
              </>
            )}
            <Link to={to} className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-[var(--w-deep-text)] underline-offset-4 hover:underline">
              {curriculum.openLabel} <span aria-hidden="true">→</span>
              <span className="sr-only">: {lesson.title}</span>
            </Link>
          </div>
        </div>
      </div>
    </article>
  );
}

export function CurriculumDetail() {
  const { status } = useAuth();
  const lessons = usePublicLessons();
  const [ref, near] = useLazySection<HTMLDivElement>();
  const modules = buildModules(lessons.data ?? []);
  const kindsByLesson = useLessonKinds(lessons.data ?? [], near);

  return (
    <div ref={ref}>
      {lessons.isPending && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" aria-busy="true" aria-label="Đang tải chương trình học">
          {[0, 1, 2].map((i) => <div key={i} className="h-44 animate-pulse rounded-[20px] bg-line/60 motion-reduce:animate-none" />)}
        </div>
      )}
      {lessons.isError && (
        <Alert tone="danger" action={<Button variant="ghost" onClick={() => lessons.refetch()}>Thử lại</Button>}>
          Chưa tải được chương trình học. {lessons.error.message}
        </Alert>
      )}
      {lessons.data && modules.length === 0 && <Alert>Chương trình học đang được soạn, bạn quay lại sau nhé.</Alert>}

      <div className="space-y-12">
        {modules.map((mod) => (
          <section key={mod.track} aria-labelledby={`ct-${mod.track}`}>
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h3 id={`ct-${mod.track}`} className="display reveal text-2xl">{mod.track}</h3>
              <p className="reveal font-mono text-xs text-[var(--w-ink-soft)]">
                {mod.lessonCount} bài · {mod.exerciseCount} câu hỏi · khoảng {mod.minutes} phút
              </p>
            </div>
            <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {mod.lessons.map((lesson) => (
                <LessonCard
                  key={lesson.id}
                  lesson={lesson}
                  kinds={kindsByLesson[lesson.id] ?? []}
                  // Chưa đăng nhập thì "Xem bài" dẫn sang đăng ký, vì khu học cần tài khoản.
                  to={status === "authenticated" ? `/app/hoc?bai=${encodeURIComponent(lesson.id)}` : "/dang-ky"}
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

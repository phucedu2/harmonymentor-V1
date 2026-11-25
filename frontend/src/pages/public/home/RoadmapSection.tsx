import { useRef } from "react";
import { Alert } from "../../../components/ui/Alert";
import { Button } from "../../../components/ui/Button";
import { useMotion, useMotionEffect } from "../wow/motion";
import { useReducedMotion } from "../wow/WowScenes";
import { buildModules } from "./curriculum";
import { usePublicLessons } from "./data";
import { roadmap } from "./copy";

type Step = { name: string; meta: string[]; body: string; finish?: boolean };

function Dot({ index, finish }: { index: number; finish?: boolean }) {
  return <span className="hm-road-dot" aria-hidden="true">{finish ? "★" : index + 1}</span>;
}

export function RoadmapSection() {
  const lessons = usePublicLessons();
  const root = useRef<HTMLDivElement>(null);
  const fill = useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();
  const motion = useMotion(!reduce);

  const modules = buildModules(lessons.data ?? []);
  const steps: Step[] = modules.map((mod) => ({
    name: mod.track,
    meta: [
      roadmap.lessonsLabel.replace("{n}", String(mod.lessonCount)),
      roadmap.exercisesLabel.replace("{n}", String(mod.exerciseCount)),
      roadmap.minutesLabel.replace("{n}", String(mod.minutes)),
    ],
    body: mod.outcome ? `${roadmap.outcomePrefix} ${mod.outcome}` : "",
  }));
  if (steps.length > 0) steps.push({ name: roadmap.finish.name, meta: [], body: roadmap.finish.body, finish: true });

  // Đường nối tô dần theo cuộn (scrub nhẹ, không ghim trang). Biến --hm-fill đi từ 0 tới 1.
  useMotionEffect(motion, root, ({ gsap }) => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      if (!fill.current) return;
      // Dưới 768px đường nối nằm dọc nên tô theo scaleY, từ 768px trở lên nằm ngang nên tô theo scaleX.
      const doc = window.matchMedia("(min-width: 768px)").matches ? { scaleX: 1 } : { scaleY: 1 };
      gsap.to(fill.current, {
        ...doc, ease: "none",
        scrollTrigger: { trigger: root.current, start: "top 75%", end: "bottom 70%", scrub: 0.5 },
      });
    });
    return () => mm.revert();
  }, [steps.length]);

  if (lessons.isError) {
    return (
      <Alert tone="danger" action={<Button variant="ghost" onClick={() => lessons.refetch()}>Thử lại</Button>}>
        Chưa tải được lộ trình. {lessons.error.message}
      </Alert>
    );
  }
  if (lessons.isPending) {
    return (
      <div className="grid gap-4 md:grid-cols-5" aria-busy="true" aria-label="Đang tải lộ trình">
        {[0, 1, 2, 3, 4].map((i) => <div key={i} className="h-40 animate-pulse rounded-[20px] bg-line/60 motion-reduce:animate-none" />)}
      </div>
    );
  }
  if (steps.length === 0) return <Alert>Lộ trình đang được soạn, bạn quay lại sau nhé.</Alert>;

  return (
    <div ref={root} className="hm-road">
      {/* Đường nối: ngang (máy tính) nằm ngay dưới hàng chấm, dọc (điện thoại) chạy bên trái. */}
      <div aria-hidden="true" className="hm-road-line left-[1.3rem] top-6 h-[calc(100%-3rem)] w-[2px] md:left-[6%] md:top-[1.3rem] md:h-[2px] md:w-[88%]">
        <div ref={fill} className="hm-road-fill" />
      </div>
      <ol className="relative grid gap-8 md:grid-cols-5 md:gap-4">
        {steps.map((step, i) => (
          <li key={step.name} className="hm-road-step reveal flex gap-4 md:block" data-done="true" data-finish={step.finish ? "true" : undefined}>
            <Dot index={i} finish={step.finish} />
            <div className="md:mt-5">
              <h3 className="display text-xl leading-tight">{step.name}</h3>
              {step.meta.length > 0 && (
                <p className="mt-1 font-mono text-xs text-[var(--w-ink-soft)]">{step.meta.join(" · ")}</p>
              )}
              <p className="mt-2 text-sm text-[var(--w-ink-soft)]">{step.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

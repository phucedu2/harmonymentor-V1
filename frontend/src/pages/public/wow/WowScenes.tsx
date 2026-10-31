import { useEffect, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import Lenis from "lenis";
import "lenis/dist/lenis.css";
import { api } from "../../../api";
import { pitchClassesToAscendingNotes } from "../../../audio/musicUtils";
import { prettyNote } from "../../../lib/notation";
import Piano from "../../../Piano";
import { SoundToggle, useSound } from "./sound";
import "./wow.css";

gsap.registerPlugin(ScrollTrigger, useGSAP);

// ---------- Tiện ích chung ----------

const REDUCE_QUERY = "(prefers-reduced-motion: reduce)";
/** true khi người dùng bật "giảm chuyển động" trong hệ điều hành: khi đó trang dùng bản tĩnh, không pin, không cuộn mượt. */
export function useReducedMotion() {
  return useSyncExternalStore(
    (cb) => {
      const mq = window.matchMedia(REDUCE_QUERY);
      mq.addEventListener("change", cb);
      return () => mq.removeEventListener("change", cb);
    },
    () => window.matchMedia(REDUCE_QUERY).matches,
    () => false,
  );
}

/** Cuộn mượt bằng Lenis, đồng bộ với ScrollTrigger. Trả về hàm cuộn tới phần tử (dùng cho link #chuong-trinh). */
export function useSmoothScroll(enabled: boolean) {
  const lenisRef = useRef<Lenis | null>(null);
  useEffect(() => {
    if (!enabled) return;
    const lenis = new Lenis({ lerp: 0.11 });
    lenis.on("scroll", ScrollTrigger.update);
    const tick = (time: number) => lenis.raf(time * 1000);
    gsap.ticker.add(tick);
    gsap.ticker.lagSmoothing(0);
    lenisRef.current = lenis;
    return () => {
      gsap.ticker.remove(tick);
      lenis.destroy();
      lenisRef.current = null;
    };
  }, [enabled]);
  return (el: HTMLElement) => {
    if (lenisRef.current) lenisRef.current.scrollTo(el, { offset: -16 });
    else el.scrollIntoView({ behavior: enabled ? "smooth" : "auto" });
  };
}

// Bảng âm hiệu ứng khi rê chuột qua chữ tiêu đề. Đây là âm thanh trang trí (ngũ cung Đô),
// không phải dữ liệu nhạc lý cho bài học, nên không cần lấy từ Music Engine.
const SFX_NOTES = ["C5", "D5", "E5", "G5", "A5", "C6"];

// ---------- Cảnh 1: Hero ----------

const FLOATERS = [
  { x: "3%", y: "30%", s: 56, c: "var(--w-verdigris)", d: 1.4 },
  { x: "70%", y: "10%", s: 38, c: "var(--w-brass)", d: 0.8, noStem: true },
  { x: "74%", y: "64%", s: 72, c: "var(--w-mid)", d: 1.9 },
  { x: "18%", y: "72%", s: 30, c: "var(--w-brass)", d: 0.6 },
  { x: "50%", y: "8%", s: 22, c: "var(--w-verdigris)", d: 0.5, noStem: true },
  { x: "92%", y: "82%", s: 26, c: "var(--w-felt)", d: 1.1, noStem: true },
  { x: "36%", y: "86%", s: 44, c: "var(--w-deep)", d: 1.6 },
];

function SplitWords({ text, onChar }: { text: string; onChar: (i: number) => void }) {
  let n = 0;
  return (
    <>
      {text.split(" ").map((word, wi) => (
        <span key={wi}>
          {wi > 0 && " "}
          <span className="wow-word">
            {Array.from(word).map((ch) => {
              const i = n++;
              return <span key={i} className="wow-char" onMouseEnter={() => onChar(i)}>{ch}</span>;
            })}
          </span>
        </span>
      ))}
    </>
  );
}

export function Hero({ cta, onExplore }: { cta: ReactNode; onExplore: () => void }) {
  const root = useRef<HTMLElement>(null);
  const { play } = useSound();
  const reduce = useReducedMotion();

  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.from(".wow-char", { yPercent: 110, rotate: 8, opacity: 0, duration: 0.9, ease: "expo.out", stagger: 0.025 });
      gsap.from(".hero-fade", { y: 24, opacity: 0, duration: 0.8, ease: "power3.out", stagger: 0.12, delay: 0.5 });
      gsap.from(".wow-float span", { scale: 0, opacity: 0, duration: 1.2, ease: "back.out(2)", stagger: 0.08, delay: 0.2 });
      // Cuộn xuống: các nốt bay lên theo độ sâu khác nhau (parallax), tiêu đề thu nhỏ và mờ dần.
      gsap.utils.toArray<HTMLElement>(".wow-float span").forEach((el) => {
        gsap.to(el, {
          yPercent: -260 * Number(el.dataset.depth), rotate: 40 * Number(el.dataset.depth), ease: "none",
          scrollTrigger: { trigger: root.current, start: "top top", end: "bottom top", scrub: true },
        });
      });
      gsap.to(".hero-inner", {
        scale: 0.86, opacity: 0, y: -60, ease: "none",
        scrollTrigger: { trigger: root.current, start: "top top", end: "bottom top", scrub: true },
      });
    });
    return () => mm.revert();
  }, { scope: root });

  return (
    <section ref={root} className="wow-hero" aria-labelledby="hero-title">
      <div className="wow-float" aria-hidden="true">
        {FLOATERS.map((f, i) => (
          <span key={i} data-depth={f.d} className={f.noStem ? "no-stem" : ""}
            style={{ left: f.x, top: f.y, ["--s" as string]: `${f.s}px`, ["--c" as string]: f.c }} />
        ))}
      </div>
      <div className="hero-inner mx-auto w-full max-w-6xl px-4 py-16 sm:px-6">
        <div className="hero-fade mb-8 flex flex-wrap items-center justify-between gap-3">
          <span className="wow-kicker" style={{ color: "var(--w-verdigris)" }}>Nền tảng học nhạc lý · tiếng Việt</span>
          <SoundToggle />
        </div>
        <h1 id="hero-title" className="display">
          <SplitWords text="Hiểu nhạc lý" onChar={(i) => play([SFX_NOTES[i % SFX_NOTES.length]], "16n")} />
          <br />
          <em><SplitWords text="bằng cách chơi nó." onChar={(i) => play([SFX_NOTES[(i + 2) % SFX_NOTES.length]], "16n")} /></em>
        </h1>
        <p className="lead hero-fade mt-8 max-w-xl text-lg sm:text-xl">
          Bắt đầu từ con số 0. Cuộn xuống để nghe một nốt nhạc biến thành hợp âm, rồi thành cả một bài hát.
          {" "}<span className="text-base opacity-80">(Bật âm thanh ở góc trên để nghe.)</span>
        </p>
        <div className="hero-fade mt-10 flex flex-wrap items-center gap-3">
          {cta}
          <button type="button" className="wow-ghost" onClick={onExplore}>Xem chương trình</button>
        </div>
        {!reduce && <div className="wow-scrollhint hero-fade mt-14 text-center text-xs tracking-[0.2em]">CUỘN ĐỂ CHƠI<i /></div>}
      </div>
    </section>
  );
}

// ---------- Cảnh 2: Từ một nốt đến một hợp âm ----------

const LETTERS = "CDEFGAB";
const QUALITY_VI: Record<string, string> = { maj: "trưởng", min: "thứ" };
const NOTE_COLORS = ["var(--w-deep)", "var(--w-mid)", "var(--w-verdigris)"];

/** Vị trí dọc trên khuông khóa Sol, tính theo bậc chữ cái (chỉ để VẼ, không suy luận nhạc lý). */
function staffY(scientific: string, bottomLineY: number, gap: number) {
  const m = /^([A-G])[#b]*(-?\d+)$/.exec(scientific);
  if (!m) return bottomLineY;
  const diatonic = Number(m[2]) * 7 + LETTERS.indexOf(m[1]);
  const e4 = 4 * 7 + LETTERS.indexOf("E");
  return bottomLineY - (diatonic - e4) * (gap / 2);
}

function Staff({ notes }: { notes: string[] }) {
  const gap = 22, top = 60, bottom = top + gap * 4, x0 = 30, x1 = 470;
  return (
    <svg viewBox="0 0 500 260" className="w-full max-w-xl" role="img" aria-label={`Khuông nhạc với các nốt ${notes.join(", ")}`}>
      {[0, 1, 2, 3, 4].map((i) => <line key={i} className="staff" x1={x0} x2={x1} y1={top + i * gap} y2={top + i * gap} />)}
      <text x={x0 + 4} y={bottom + 10} fontSize="120" fontFamily="serif" fill="var(--w-lacquer)">𝄞</text>
      {notes.map((n, i) => {
        const y = staffY(n, bottom, gap);
        const x = 270;
        return (
          <g key={n} className={`note note-${i}`} style={{ ["--c" as string]: NOTE_COLORS[i % 3] }}>
            {y > bottom + gap / 2 - 1 && <line className="staff" x1={x - 26} x2={x + 26} y1={bottom + gap} y2={bottom + gap} />}
            <ellipse cx={x} cy={y} rx="17" ry="12.5" transform={`rotate(-20 ${x} ${y})`} />
            <text x={x + 34 + (i % 2) * 26} y={y + 7} fontSize="22">{prettyNote(n.replace(/-?\d+$/, ""))}</text>
          </g>
        );
      })}
    </svg>
  );
}

export function StaffScene() {
  const root = useRef<HTMLElement>(null);
  const reduce = useReducedMotion();
  const { play } = useSound();
  const chord = useQuery({ queryKey: ["chord-inspect", "C", ""], queryFn: () => api.inspectChord("C"), staleTime: Infinity });
  const names = chord.data?.notes ?? [];
  const playable = pitchClassesToAscendingNotes(names, 4);
  const formula = chord.data?.formula ?? [];
  const lastStep = useRef(-1);
  const playRef = useRef(play);
  playRef.current = play;

  const steps = names.length === 3 ? [
    { kicker: "Một nốt", title: <>Mọi thứ bắt đầu từ <b>{prettyNote(names[0])}</b>.</>, body: "Một nốt đứng một mình: đơn giản, rõ ràng. Đây là nốt gốc." },
    { kicker: "Hai nốt", title: <>Thêm <b>{prettyNote(names[1])}</b>, bậc {formula[1]}.</>, body: "Hai nốt vang cùng lúc bắt đầu có màu sắc. Bậc 3 quyết định hợp âm vui hay buồn." },
    { kicker: "Ba nốt", title: <>Chồng <b>{prettyNote(names[2])}</b>: hợp âm {prettyNote(chord.data!.symbol)} {QUALITY_VI[chord.data!.quality] ?? chord.data!.quality}.</>, body: "Ba nốt xếp chồng cách quãng ba là một hợp âm. Bạn vừa dựng hợp âm đầu tiên." },
  ] : [];

  useGSAP(() => {
    if (reduce || steps.length === 0) return;
    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: root.current, start: "top top", end: "+=220%", scrub: 0.6, pin: true,
        onUpdate: (self) => {
          const step = Math.min(2, Math.floor(self.progress * 3.2));
          if (step !== lastStep.current && self.progress > 0.02) {
            lastStep.current = step;
            playRef.current(playable.slice(0, step + 1), "4n");
          }
        },
      },
    });
    gsap.set(".note", { opacity: 0, y: -80 });
    gsap.set(".wow-step", { opacity: 0, y: 30 });
    [0, 1, 2].forEach((i) => {
      tl.to(`.note-${i}`, { opacity: 1, y: 0, duration: 0.6, ease: "back.out(2.2)" }, i);
      tl.to(`.step-${i}`, { opacity: 1, y: 0, duration: 0.4 }, i);
      if (i < 2) tl.to(`.step-${i}`, { opacity: 0, y: -30, duration: 0.3 }, i + 0.8);
    });
    tl.to({}, { duration: 0.4 });
  }, { scope: root, dependencies: [reduce, steps.length], revertOnUpdate: true });

  return (
    <section ref={root} className="wow-staff-scene wow-staff" aria-labelledby="staff-title">
      <div className="mx-auto grid min-h-svh max-w-6xl items-center gap-8 px-4 py-16 sm:px-6 md:grid-cols-2">
        <div>
          <p className="wow-kicker">Bài 1 trong 30 giây</p>
          <h2 id="staff-title" className="display mt-3 text-4xl sm:text-5xl">Từ một nốt đến một hợp âm</h2>
          <div className={reduce ? "mt-8 space-y-6" : "relative mt-8 h-48"}>
            {chord.isPending && <p className="text-[var(--w-ink-soft)]">Đang hỏi Music Engine…</p>}
            {chord.isError && <p className="text-[var(--w-felt)]">Chưa kết nối được Music Engine. Bạn vẫn có thể cuộn tiếp.</p>}
            {steps.map((s, i) => (
              <div key={i} className={reduce ? "" : `wow-step step-${i}`}>
                <p className="wow-kicker" style={{ color: "var(--w-brass)" }}>{s.kicker}</p>
                <p className="display mt-2 text-2xl sm:text-3xl">{s.title}</p>
                <p className="mt-2 text-[var(--w-ink-soft)]">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="flex justify-center">{playable.length > 0 && <Staff notes={playable} />}</div>
      </div>
    </section>
  );
}

// ---------- Cảnh 3: Vòng hợp âm cuộn ngang ----------

const PROGRESSION = ["C", "G", "Am", "F"];
const FUNCTION_VI: Record<string, string> = { tonic: "Chủ (ổn định)", dominant: "Át (căng, muốn về)", predominant: "Hạ át (chuẩn bị)", subdominant: "Hạ át (chuẩn bị)" };

export function ProgressionScene() {
  const root = useRef<HTMLElement>(null);
  const track = useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();
  const { play } = useSound();
  const [active, setActive] = useState(0);
  const activeRef = useRef(-1);
  const results = useQueries({
    queries: PROGRESSION.map((s) => ({ queryKey: ["chord-inspect", s, "C"], queryFn: () => api.inspectChord(s, "C"), staleTime: Infinity })),
  });
  const chords = results.map((r) => r.data);
  const ready = chords.every(Boolean);
  const playables = chords.map((c) => (c ? pitchClassesToAscendingNotes(c.notes, 3) : []));
  const playRef = useRef({ play, playables });
  playRef.current = { play, playables };

  useGSAP(() => {
    if (reduce || !ready || !track.current) return;
    const distance = () => Math.max(0, track.current!.scrollWidth - window.innerWidth + 32);
    gsap.to(track.current, {
      x: () => -distance(), ease: "none",
      scrollTrigger: {
        trigger: root.current, start: "top top", end: () => `+=${distance() + window.innerHeight * 0.6}`,
        scrub: 0.5, pin: true, invalidateOnRefresh: true,
        onUpdate: (self) => {
          const i = Math.min(PROGRESSION.length - 1, Math.round(self.progress * (PROGRESSION.length - 1)));
          if (i !== activeRef.current) {
            activeRef.current = i;
            setActive(i);
            if (self.progress > 0.01) playRef.current.play(playRef.current.playables[i], "2n");
          }
        },
      },
    });
  }, { scope: root, dependencies: [reduce, ready], revertOnUpdate: true });

  return (
    <section ref={root} className="wow-prog" aria-labelledby="prog-title">
      <div className="flex min-h-svh flex-col justify-center py-16">
        <div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
          <p className="wow-kicker" style={{ color: "var(--w-verdigris)" }}>Bước tiếp theo</p>
          <h2 id="prog-title" className="display mt-3 max-w-3xl text-4xl sm:text-5xl">
            Bốn hợp âm này nằm trong <em>hàng nghìn</em> bài hát pop.
          </h2>
          <p className="mt-4 max-w-2xl opacity-80">Cuộn để đi qua vòng I – V – vi – IV. Mỗi hợp âm có một “vai”: ổn định, căng, buồn, chuẩn bị.</p>
        </div>
        <div className={reduce ? "mt-10 overflow-x-auto px-4 sm:px-6" : "mt-10 overflow-hidden"}>
          <div ref={track} className="flex gap-6 px-4 sm:px-[max(1.5rem,calc((100vw-72rem)/2+1.5rem))]">
            {PROGRESSION.map((s, i) => {
              const c = chords[i];
              return (
                <article key={s} className="wow-card" data-active={!reduce && i === active}>
                  <div className="flex items-baseline justify-between">
                    <span className="display text-6xl">{prettyNote(c?.symbol ?? s)}</span>
                    <span className="roman text-3xl">{c?.context?.roman ?? ""}</span>
                  </div>
                  <p className="mt-2 text-sm opacity-80">{c?.context?.function ? FUNCTION_VI[c.context.function] ?? c.context.function : " "}</p>
                  <p className="mt-4 font-mono text-lg" style={{ color: "var(--w-verdigris)" }}>{c ? c.notes.map(prettyNote).join(" · ") : "…"}</p>
                  <div className="mt-4"><Piano active={c?.notes ?? []} label={c ? `Hợp âm ${c.symbol}: ${c.notes.join(", ")}` : "Bàn phím piano"} /></div>
                  {reduce && (
                    <button type="button" className="wow-ghost mt-4 py-2 text-sm" onClick={() => play(playables[i], "2n")}>Nghe {s}</button>
                  )}
                </article>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

/** Các khối có class .reveal hiện dần khi cuộn tới (chỉ khi không bật giảm chuyển động). */
export function useReveal(scope: React.RefObject<HTMLElement | null>, deps: unknown[]) {
  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      ScrollTrigger.batch(".reveal", {
        start: "top 88%",
        onEnter: (els) => gsap.fromTo(els, { y: 48, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, ease: "power3.out", stagger: 0.08, overwrite: true }),
      });
    });
    return () => mm.revert();
  }, { scope, dependencies: deps, revertOnUpdate: true });
}

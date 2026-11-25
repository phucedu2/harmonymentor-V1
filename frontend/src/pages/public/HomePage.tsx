import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api";
import { useAuth } from "../../auth/AuthProvider";
import Piano from "../../Piano";
import { prettyNote } from "../../lib/notation";
import { Alert } from "../../components/ui/Alert";
import { Button, Spinner } from "../../components/ui/Button";
import { Link } from "react-router";
import { SoundProvider, SoundToggle, useSound } from "./wow/sound";
import { Hero, ProgressionScene, StaffScene, useReducedMotion, useReveal, useSmoothScroll } from "./wow/WowScenes";
import { pitchClassesToAscendingNotes } from "../../audio/musicUtils";
import { CurriculumDetail } from "./home/CurriculumDetail";
import { RoadmapSection } from "./home/RoadmapSection";
import { OutcomesSection } from "./home/OutcomesSection";
import { FeatureBento } from "./home/FeatureBento";
import { curriculum, features, outcomes, roadmap } from "./home/copy";
import "./home/home.css";

// Các hợp âm để bấm thử; nốt luôn lấy từ Music Engine, không viết sẵn ở đây.
const DEMO_CHORDS = ["C", "Am", "G7", "Ebm7b5"];

function ChordDemo() {
  const [symbol, setSymbol] = useState(DEMO_CHORDS[0]);
  const chord = useQuery({ queryKey: ["chord-inspect", symbol], queryFn: () => api.inspectChord(symbol), staleTime: Infinity });
  const { play } = useSound();
  // Nghe hợp âm vừa chọn (chỉ khi người dùng đã bật âm thanh); nốt lấy từ Music Engine.
  useEffect(() => {
    if (chord.data) play(pitchClassesToAscendingNotes(chord.data.notes, 3), "2n");
  }, [chord.data, play]);

  return (
    <div className="wow-panel reveal p-6 shadow-sm">
      <p className="text-sm font-medium text-muted">Bấm thử một hợp âm</p>
      <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Chọn hợp âm">
        {DEMO_CHORDS.map((s) => (
          <button
            key={s}
            type="button"
            aria-pressed={s === symbol}
            onClick={() => setSymbol(s)}
            className={`rounded-full border px-4 py-1.5 font-mono text-sm transition-colors ${
              s === symbol ? "border-[var(--w-deep)] bg-[var(--w-deep)] text-white" : "border-[var(--w-line)] bg-[var(--w-panel)] text-ink hover:border-[var(--w-deep)]"
            }`}
          >
            {prettyNote(s)}
          </button>
        ))}
      </div>
      <div className="mt-4 min-h-12" aria-live="polite">
        {chord.isPending && <span className="flex items-center gap-2 text-sm text-muted"><Spinner /> Đang tính các nốt…</span>}
        {chord.isError && (
          <Alert tone="danger" action={<Button variant="ghost" onClick={() => chord.refetch()}>Thử lại</Button>}>
            Chưa lấy được các nốt. {chord.error.message}
          </Alert>
        )}
        {chord.data && (
          <p className="text-sm text-muted">
            <span className="font-mono text-base font-semibold text-ink">{prettyNote(chord.data.symbol)}</span> gồm{" "}
            <span className="font-mono text-base font-semibold text-[var(--w-deep-text)]">{chord.data.notes.map(prettyNote).join(" · ")}</span>
          </p>
        )}
      </div>
      <Piano active={chord.data?.notes ?? []} label={chord.data ? `Piano tô sáng các nốt ${chord.data.notes.join(", ")}` : "Bàn phím piano"} />
    </div>
  );
}

function HomeContent() {
  const { status } = useAuth();
  const { hash } = useLocation();
  const reduce = useReducedMotion();
  const scrollTo = useSmoothScroll(!reduce);
  const root = useRef<HTMLDivElement>(null);
  useReveal(root, []);

  const goTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) scrollTo(el);
  };

  // React Router không tự cuộn tới #chuong-trinh, nên cuộn thủ công khi hash đổi.
  useEffect(() => {
    if (hash) goTo(hash.slice(1));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hash]);

  const cta = status === "authenticated"
    ? <Link to="/app" className="wow-cta">Tiếp tục học →</Link>
    : <Link to="/dang-ky" className="wow-cta">Bắt đầu miễn phí →</Link>;

  return (
    <div ref={root} className="wow">
      <Hero cta={cta} onExplore={() => goTo("lo-trinh")} />
      <StaffScene />
      <ProgressionScene />

      <section className="py-20" aria-labelledby="thu-title">
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 sm:px-6 md:grid-cols-[1fr_1.1fr]">
          <div className="reveal">
            <p className="wow-kicker">Tự tay thử</p>
            <h2 id="thu-title" className="display mt-3 text-4xl sm:text-5xl">Bấm một hợp âm, <em>nghe</em> và <em>thấy</em> nó.</h2>
            <p className="mt-4 max-w-md text-[var(--w-ink-soft)]">Mỗi nốt bạn thấy đều do bộ máy nhạc lý của HarmonyMentor tính ra, kể cả hợp âm khó như E♭m7♭5.</p>
            <SoundToggle className="on-light mt-6" />
          </div>
          <ChordDemo />
        </div>
      </section>

      <section id="lo-trinh" className="scroll-mt-6 border-t border-[var(--w-line)] py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="wow-kicker reveal">{roadmap.kicker}</p>
          <h2 className="display reveal mt-3 text-4xl">{roadmap.title}</h2>
          <p className="reveal mt-3 max-w-2xl text-[var(--w-ink-soft)]">{roadmap.lead}</p>
          <div className="mt-12"><RoadmapSection /></div>
        </div>
      </section>

      <section id="hoc-gi" className="scroll-mt-6 border-t border-[var(--w-line)] py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="wow-kicker reveal">{outcomes.kicker}</p>
          <h2 className="display reveal mt-3 text-4xl">{outcomes.title}</h2>
          <p className="reveal mt-3 max-w-2xl text-[var(--w-ink-soft)]">{outcomes.lead}</p>
          <div className="mt-10"><OutcomesSection /></div>
        </div>
      </section>

      <section id="tinh-nang" className="scroll-mt-6 border-t border-[var(--w-line)] py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="wow-kicker reveal">{features.kicker}</p>
          <h2 className="display reveal mt-3 text-4xl">{features.title}</h2>
          <p className="reveal mt-3 max-w-2xl text-[var(--w-ink-soft)]">{features.lead}</p>
          <div className="mt-10"><FeatureBento /></div>
        </div>
      </section>

      <section id="chuong-trinh" className="scroll-mt-6 border-t border-[var(--w-line)] py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="wow-kicker reveal">{curriculum.kicker}</p>
          <h2 className="display reveal mt-3 text-4xl">{curriculum.title}</h2>
          <p className="reveal mt-3 max-w-2xl text-[var(--w-ink-soft)]">{curriculum.lead}</p>
          <div className="mt-10"><CurriculumDetail /></div>
        </div>
      </section>

      <section className="wow-final py-20 text-center">
        <div className="reveal mx-auto max-w-3xl px-4">
          <h2 className="display text-4xl sm:text-6xl">Hợp âm đầu tiên của bạn đang chờ.</h2>
          <div className="mt-8 flex justify-center">{cta}</div>
        </div>
      </section>
    </div>
  );
}

export default function HomePage() {
  return (
    <SoundProvider>
      <HomeContent />
    </SoundProvider>
  );
}

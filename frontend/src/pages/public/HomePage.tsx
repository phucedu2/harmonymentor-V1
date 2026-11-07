import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api, type LessonSummary } from "../../api";
import { useAuth } from "../../auth/AuthProvider";
import Piano from "../../Piano";
import { prettyNote } from "../../lib/notation";
import { Alert } from "../../components/ui/Alert";
import { Button, Spinner } from "../../components/ui/Button";
import { Link } from "react-router";
import { SoundProvider, SoundToggle, useSound } from "./wow/sound";
import { Hero, ProgressionScene, StaffScene, useReducedMotion, useReveal, useSmoothScroll } from "./wow/WowScenes";
import { pitchClassesToAscendingNotes } from "../../audio/musicUtils";

// Các hợp âm để bấm thử; nốt luôn lấy từ Music Engine, không viết sẵn ở đây.
const DEMO_CHORDS = ["C", "Am", "G7", "Ebm7b5"];

const FEATURES = [
  { title: "Luyện tập có chẩn đoán", body: "Làm sai không chỉ nhận chữ “Sai”: hệ thống chỉ ra nốt nào lệch và vì sao, ví dụ dùng quãng 7 trưởng thay cho quãng 7 thứ.", ready: true },
  { title: "Ôn tập đúng lúc", body: "Thẻ ghi nhớ tự hẹn ngày ôn lại: nhớ tốt thì giãn ra, quên thì ôn sớm hơn.", ready: true },
  { title: "AI Tutor có trích dẫn", body: "Hỏi bằng tiếng Việt; câu trả lời dẫn về đúng bài học, nốt nhạc được bộ chấm nhạc lý kiểm tra.", ready: false },
  { title: "Composition Lab", body: "Ghép vòng hợp âm, giai điệu và nhịp trống rồi nghe ngay thành quả của mình.", ready: false },
];

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
              s === symbol ? "border-[var(--w-deep)] bg-[var(--w-deep)] text-white" : "border-[var(--w-line)] bg-white text-ink hover:border-[var(--w-deep)]"
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
            <span className="font-mono text-base font-semibold text-[var(--w-deep)]">{chord.data.notes.map(prettyNote).join(" · ")}</span>
          </p>
        )}
      </div>
      <Piano active={chord.data?.notes ?? []} label={chord.data ? `Piano tô sáng các nốt ${chord.data.notes.join(", ")}` : "Bàn phím piano"} />
    </div>
  );
}

function groupByTrack(lessons: LessonSummary[]) {
  const groups = new Map<string, LessonSummary[]>();
  [...lessons].sort((a, b) => a.order - b.order).forEach((lesson) => {
    groups.set(lesson.track, [...(groups.get(lesson.track) ?? []), lesson]);
  });
  return [...groups.entries()];
}

function Curriculum() {
  // FR-VIS-02: chương trình học lấy từ API, không viết sẵn danh sách bài ở frontend.
  const lessons = useQuery({ queryKey: ["lessons", "public"], queryFn: api.listLessons });
  const groups = useMemo(() => groupByTrack(lessons.data ?? []), [lessons.data]);

  if (lessons.isPending) {
    return (
      <div className="grid gap-4 md:grid-cols-2" aria-busy="true" aria-label="Đang tải chương trình học">
        {[0, 1].map((i) => <div key={i} className="h-40 animate-pulse rounded-xl bg-line/60" />)}
      </div>
    );
  }
  if (lessons.isError) {
    return (
      <Alert tone="danger" action={<Button variant="ghost" onClick={() => lessons.refetch()}>Thử lại</Button>}>
        Chưa tải được chương trình học. {lessons.error.message}
      </Alert>
    );
  }
  if (groups.length === 0) return <Alert>Chương trình học đang được soạn, bạn quay lại sau nhé.</Alert>;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {groups.map(([track, items]) => (
        <article key={track} className="wow-panel reveal p-6">
          <h3 className="display text-xl">{track}</h3>
          <ol className="mt-3 space-y-2">
            {items.map((lesson) => (
              <li key={lesson.id} className="flex items-start gap-3 text-sm">
                <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-md bg-[var(--w-ivory)] font-mono text-xs font-semibold text-[var(--w-deep)]">{lesson.order}</span>
                <span className="flex-1 text-ink">{lesson.title}</span>
                {lesson.exercise_count === 0 && <span className="shrink-0 rounded-full bg-bg px-2 py-0.5 text-xs text-muted">Sắp có</span>}
              </li>
            ))}
          </ol>
        </article>
      ))}
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
      <Hero cta={cta} onExplore={() => goTo("chuong-trinh")} />
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

      <section id="chuong-trinh" className="scroll-mt-6 border-t border-[var(--w-line)] py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <p className="wow-kicker reveal">Lộ trình</p>
          <h2 className="display reveal mt-3 text-4xl">Chương trình học</h2>
          <p className="reveal mt-3 max-w-2xl text-[var(--w-ink-soft)]">Đi từ tên nốt, quãng, âm giai tới hợp âm và vòng hợp âm. Mỗi bài có lý thuyết ngắn, ví dụ nghe được và bài kiểm tra cuối bài.</p>
          <div className="mt-10"><Curriculum /></div>
        </div>
      </section>

      <section id="tinh-nang" className="scroll-mt-6 pb-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="display reveal text-4xl">Tính năng</h2>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((f) => (
              <article key={f.title} className="wow-panel reveal p-6">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="font-semibold">{f.title}</h3>
                  {!f.ready && <span className="shrink-0 rounded-full bg-[var(--w-ivory)] px-2 py-0.5 text-xs font-medium text-[var(--w-deep)]">Sắp ra mắt</span>}
                </div>
                <p className="mt-2 text-sm text-[var(--w-ink-soft)]">{f.body}</p>
              </article>
            ))}
          </div>
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

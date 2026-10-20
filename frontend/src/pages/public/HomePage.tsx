import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api, type LessonSummary } from "../../api";
import { useAuth } from "../../auth/AuthProvider";
import Piano from "../../Piano";
import { prettyNote } from "../../lib/notation";
import { Alert } from "../../components/ui/Alert";
import { Button, ButtonLink, Spinner } from "../../components/ui/Button";

// Các hợp âm để bấm thử; nốt luôn lấy từ Music Engine, không viết sẵn ở đây.
const DEMO_CHORDS = ["C", "Am", "G7", "Ebm7b5"];

const FEATURES = [
  { title: "Luyện tập có chẩn đoán", body: "Làm sai không chỉ nhận chữ “Sai”: hệ thống chỉ ra nốt nào lệch và vì sao, ví dụ dùng quãng 7 trưởng thay cho quãng 7 thứ.", ready: true },
  { title: "Ôn tập đúng lúc", body: "Thẻ ghi nhớ tự hẹn ngày ôn lại: nhớ tốt thì giãn ra, quên thì ôn sớm hơn.", ready: true },
  { title: "AI Tutor có trích dẫn", body: "Hỏi bằng tiếng Việt; câu trả lời dẫn về đúng bài học và nốt nhạc được Music Engine kiểm tra.", ready: false },
  { title: "Composition Lab", body: "Ghép vòng hợp âm, giai điệu và nhịp trống rồi nghe ngay thành quả của mình.", ready: false },
];

function ChordDemo() {
  const [symbol, setSymbol] = useState(DEMO_CHORDS[0]);
  const chord = useQuery({ queryKey: ["chord-inspect", symbol], queryFn: () => api.inspectChord(symbol), staleTime: Infinity });

  return (
    <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
      <p className="text-sm font-medium text-muted">Bấm thử một hợp âm</p>
      <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Chọn hợp âm">
        {DEMO_CHORDS.map((s) => (
          <button
            key={s}
            type="button"
            aria-pressed={s === symbol}
            onClick={() => setSymbol(s)}
            className={`rounded-full border px-4 py-1.5 font-mono text-sm transition-colors ${
              s === symbol ? "border-primary bg-primary text-white" : "border-line bg-surface text-ink hover:border-primary"
            }`}
          >
            {prettyNote(s)}
          </button>
        ))}
      </div>
      <div className="mt-4 min-h-12" aria-live="polite">
        {chord.isPending && <span className="flex items-center gap-2 text-sm text-muted"><Spinner /> Đang hỏi Music Engine…</span>}
        {chord.isError && (
          <Alert tone="danger" action={<Button variant="ghost" onClick={() => chord.refetch()}>Thử lại</Button>}>
            Chưa lấy được nốt từ Music Engine. {chord.error.message}
          </Alert>
        )}
        {chord.data && (
          <p className="text-sm text-muted">
            <span className="font-mono text-base font-semibold text-ink">{prettyNote(chord.data.symbol)}</span> gồm{" "}
            <span className="font-mono text-base font-semibold text-primary">{chord.data.notes.map(prettyNote).join(" · ")}</span>
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
        <article key={track} className="rounded-xl border border-line bg-surface p-5">
          <h3 className="font-semibold text-ink">{track}</h3>
          <ol className="mt-3 space-y-2">
            {items.map((lesson) => (
              <li key={lesson.id} className="flex items-start gap-3 text-sm">
                <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-md bg-primary-soft font-mono text-xs font-semibold text-primary">{lesson.order}</span>
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

export default function HomePage() {
  const { status } = useAuth();
  const { hash } = useLocation();

  // React Router không tự cuộn tới #chuong-trinh, nên cuộn thủ công khi hash đổi.
  useEffect(() => {
    if (hash) document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: "smooth" });
  }, [hash]);

  return (
    <>
      <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-12 sm:px-6 md:grid-cols-[1.1fr_1fr] md:py-20">
        <div>
          <h1 className="text-4xl font-bold leading-tight tracking-tight text-ink sm:text-5xl">Hiểu nhạc lý bằng cách chơi nó.</h1>
          <p className="mt-4 max-w-xl text-lg text-muted">
            Học → Luyện tập → Chẩn đoán lỗi → Sáng tác. Mỗi đáp án được Music Engine kiểm tra, mỗi lỗi sai đi kèm lời giải thích dễ hiểu.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            {status === "authenticated"
              ? <ButtonLink to="/app" size="lg">Tiếp tục học</ButtonLink>
              : <ButtonLink to="/dang-ky" size="lg">Bắt đầu miễn phí</ButtonLink>}
            <ButtonLink to="/#chuong-trinh" variant="secondary" size="lg">Xem chương trình</ButtonLink>
          </div>
        </div>
        <ChordDemo />
      </section>

      <section id="chuong-trinh" className="scroll-mt-6 border-t border-line bg-surface/60 py-14">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-2xl font-bold">Chương trình học</h2>
          <p className="mt-2 max-w-2xl text-muted">Đi từ tên nốt, quãng, âm giai tới hợp âm và vòng hợp âm. Mỗi bài có lý thuyết ngắn, ví dụ nghe được và bài kiểm tra cuối bài.</p>
          <div className="mt-8"><Curriculum /></div>
        </div>
      </section>

      <section id="tinh-nang" className="scroll-mt-6 py-14">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-2xl font-bold">Tính năng</h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((f) => (
              <article key={f.title} className="rounded-xl border border-line bg-surface p-5">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="font-semibold">{f.title}</h3>
                  {!f.ready && <span className="shrink-0 rounded-full bg-accent-soft px-2 py-0.5 text-xs font-medium text-accent">Sắp ra mắt</span>}
                </div>
                <p className="mt-2 text-sm text-muted">{f.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

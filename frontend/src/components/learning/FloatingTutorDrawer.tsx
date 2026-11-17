import { useEffect, useRef, useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router";
import { api, type ApiError, type ChatReply } from "../../api";
import { TUTOR_EXPLAIN_EVENT, type TutorExplainDetail } from "../../lib/tutorBus";
import { Button, Spinner } from "../ui/Button";
import { useDraggable } from "./useDraggable";

// Khung AI Tutor nổi ở góc phải dưới trên mọi trang /app/* (04 Bảng 25, đề GĐ3 mục 11).
// Mọi phán đoán nhạc lý, trích dẫn và nhãn "Đã kiểm bằng Music Engine" đều do máy chủ quyết; ở đây chỉ hiển thị.

type Item =
  | { kind: "user"; id: string; text: string }
  | { kind: "assistant"; id: string; data: ChatReply; explainFor?: { attemptId: string; prompt: string } }
  | { kind: "error"; id: string; text: string; retry?: () => void };

const FALLBACK_NOTE: Record<string, string> = {
  ai_disabled: "AI đang tắt, đây là câu trả lời lấy từ bài học.",
  timeout: "AI trả lời quá lâu, mình dùng câu trả lời lấy từ bài học.",
  rate_limited: "AI đang quá tải, mình dùng câu trả lời lấy từ bài học.",
  unavailable: "AI đang lỗi, mình dùng câu trả lời lấy từ bài học.",
  global_budget: "Hôm nay hệ thống đã dùng hết lượt AI, mình dùng câu trả lời lấy từ bài học.",
  engine_contradiction: "Câu AI soạn sai với Music Engine nên đã được thay bằng câu trả lời an toàn.",
  answer_leak: "Câu AI soạn để lộ đáp án nên đã được thay bằng gợi ý viết sẵn.",
  format_error: "AI trả lời sai định dạng nên đã được thay bằng câu trả lời lấy từ bài học.",
  prompt_leak: "Câu trả lời bị chặn vì không an toàn.",
};

// Màu nhãn nguồn theo luồng: người học thấy ngay câu trả lời lấy từ đâu (góp ý thầy G1/G3).
const FLOW_STYLE: Record<string, string> = {
  A: "bg-primary-soft text-primary",
  B: "bg-warning-soft text-warning",
  C: "bg-surface text-muted border border-line",
  D: "bg-success-soft text-success",
};

let seq = 0;
const nextId = () => `m${++seq}`;

function contextFromPath(pathname: string, search: string) {
  const page = pathname.startsWith("/app/hoc") ? "learn" : pathname.replace("/app/", "").split("/")[0] || "dashboard";
  const lesson = new URLSearchParams(search).get("bai") ?? undefined;
  return { page, lesson_id: lesson };
}

function Stars({ messageId }: { messageId: number }) {
  const [stars, setStars] = useState(0);
  const [failed, setFailed] = useState(false);
  const rate = async (n: number) => {
    setStars(n); setFailed(false);
    try { await api.rateChatMessage(messageId, n); } catch { setFailed(true); }
  };
  return <div className="mt-1 flex items-center gap-0.5" role="group" aria-label="Chấm câu trả lời">
    {[1, 2, 3, 4, 5].map((n) => <button key={n} type="button" aria-label={`${n} sao`} aria-pressed={stars >= n}
      className={`text-base leading-none ${stars >= n ? "text-warning" : "text-line hover:text-warning"}`} onClick={() => void rate(n)}>★</button>)}
    {failed && <span className="ml-1 text-xs text-danger">Chưa lưu được</span>}
  </div>;
}

export function AssistantBubble({ data, onCite, onOpen, onMoreHint, busy }: {
  data: ChatReply; onCite: (lesson: string, block: string) => void; onOpen: (path: string) => void;
  onMoreHint?: () => void; busy: boolean;
}) {
  const contradicted = data.engine_claims.some((c) => c.status !== "verified");
  const lessonCites = data.citations.filter((c) => c.lesson_id !== "HELP");
  return <div className="max-w-[92%] rounded-2xl rounded-bl-sm border border-line bg-surface px-3 py-2 text-sm text-ink">
    {data.source_label && data.flow && <p className={`mb-1 inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${FLOW_STYLE[data.flow] ?? "text-muted"}`}>
      {data.source_label}
    </p>}
    {data.hint_level > 0 && <p className="mb-1 text-xs font-semibold text-muted">Gợi ý mức {data.hint_level}/3</p>}
    <p className="whitespace-pre-line">{data.reply}</p>
    {lessonCites.length > 0 && <div className="mt-2 flex flex-wrap gap-1.5" aria-label="Nguồn trong bài học">
      {lessonCites.map((c) => <button key={c.block_id} type="button" title={`${c.lesson_title} · ${c.title}`}
        className="rounded-md border border-primary/40 bg-primary-soft px-2 py-0.5 text-xs font-semibold text-primary hover:border-primary"
        onClick={() => onCite(c.lesson_id, c.block_id)}>[{c.lesson_id}] {c.title}</button>)}
    </div>}
    {(data.help_page || (data.flow === "B" && data.suggested_lesson)) && <div className="mt-2 flex flex-wrap gap-1.5">
      {data.help_page && <button type="button" onClick={() => onOpen(data.help_page!.path)}
        className="rounded-md border border-success/40 bg-success-soft px-2 py-0.5 text-xs font-semibold text-success hover:border-success">
        Mở trang {data.help_page.title}</button>}
      {data.flow === "B" && data.suggested_lesson && <button type="button"
        onClick={() => onOpen(`/app/hoc?bai=${encodeURIComponent(data.suggested_lesson!.lesson_id)}`)}
        className="rounded-md border border-primary/40 bg-primary-soft px-2 py-0.5 text-xs font-semibold text-primary hover:border-primary">
        Mở bài {data.suggested_lesson.lesson_id}: {data.suggested_lesson.title}</button>}
    </div>}
    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
      {data.verified_label && <span className="rounded-full bg-success-soft px-2 py-0.5 font-semibold text-success">✓ {data.verified_label}</span>}
      {!data.verified_label && contradicted && <span className="rounded-full bg-warning-soft px-2 py-0.5 font-semibold text-warning">Có chỗ chưa kiểm được bằng Music Engine</span>}
      {data.status !== "ok" && <span className="text-muted">{FALLBACK_NOTE[data.fallback_reason ?? ""] ?? "Câu trả lời dự phòng."}</span>}
    </div>
    {onMoreHint && data.next_hint_level && <Button variant="ghost" className="mt-1 !min-h-8 !px-2 text-xs" onClick={onMoreHint} disabled={busy}>
      Gợi ý thêm (mức {data.next_hint_level})
    </Button>}
    <Stars messageId={data.message_id} />
  </div>;
}

export default function FloatingTutorDrawer() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Item[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [remaining, setRemaining] = useState<number | null>(null);
  // FE-002: trên điện thoại (< md) nút tròn thu vào mép phải khi đang cuộn xuống đọc bài, hiện lại khi cuộn lên
  // hoặc tới cuối trang, để không che chữ/đáp án. Máy tính không đổi.
  const [tucked, setTucked] = useState(false);
  useEffect(() => {
    let last = window.scrollY;
    const onScroll = () => {
      const y = window.scrollY;
      const atEnd = window.innerHeight + y >= document.documentElement.scrollHeight - 24;
      if (atEnd || y < 80 || y < last - 4) setTucked(false);
      else if (y > last + 4) setTucked(true);
      last = y;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  // Kéo được nút tròn (mọi cỡ màn hình, thả ra dạt vào mép gần nhất) và khung chat (từ 640 px, kéo ở thanh tiêu đề).
  // Vị trí nhớ theo máy; nút ↺ trong khung đưa cả hai về góc phải dưới.
  const [wide, setWide] = useState(() => typeof window !== "undefined" && window.matchMedia?.("(min-width: 640px)").matches === true);
  useEffect(() => {
    const mq = window.matchMedia?.("(min-width: 640px)");
    if (!mq) return;
    const on = () => setWide(mq.matches);
    mq.addEventListener?.("change", on);
    return () => mq.removeEventListener?.("change", on);
  }, []);
  const fab = useDraggable<HTMLButtonElement>({ key: "hm-ai-nut", snapX: true });
  const panel = useDraggable<HTMLElement>({ key: "hm-ai-khung", enabled: wide });
  const fabLeft = fab.pos !== null && fab.pos.x < window.innerWidth / 2;
  const moved = fab.pos !== null || panel.pos !== null;
  const resetPlace = () => { fab.reset(); panel.reset(); };
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => { listRef.current?.scrollTo({ top: listRef.current.scrollHeight }); }, [items, busy]);
  useEffect(() => { if (open) inputRef.current?.focus(); }, [open]);

  const push = (item: Item) => setItems((rows) => [...rows, item]);

  const run = async (call: () => Promise<ChatReply>, explainFor?: { attemptId: string; prompt: string }) => {
    setBusy(true);
    try {
      const data = await call();
      setSessionId(data.session_id);
      setRemaining(data.quota_remaining_today);
      push({ kind: "assistant", id: nextId(), data, explainFor });
    } catch (e) {
      const err = e as ApiError;
      const text = err.code === "AI_QUOTA_EXCEEDED"
        ? err.message ?? "Bạn đã dùng hết lượt hỏi AI hôm nay."
        : `Chưa gửi được: ${err.message ?? err.code}.`;
      push({ kind: "error", id: nextId(), text, retry: err.code === "AI_QUOTA_EXCEEDED" ? undefined : () => void run(call, explainFor) });
    } finally { setBusy(false); }
  };

  const send = (event?: FormEvent) => {
    event?.preventDefault();
    const message = text.trim();
    if (!message || busy) return;
    setText("");
    push({ kind: "user", id: nextId(), text: message });
    void run(() => api.chatMessage(message, sessionId, contextFromPath(location.pathname, location.search)));
  };

  const explain = (attemptId: string, prompt: string, level?: number) => {
    setOpen(true);
    push({ kind: "user", id: nextId(), text: level ? `Gợi ý thêm cho: ${prompt}` : `Giải thích lỗi: ${prompt}` });
    void run(() => api.explainAttempt(attemptId, sessionId, level), { attemptId, prompt });
  };

  // Nút "Giải thích lỗi này" trên thẻ câu hỏi gửi sự kiện; khung chat tự mở và hỏi máy chủ.
  const explainRef = useRef(explain);
  explainRef.current = explain;
  useEffect(() => {
    const onExplain = (e: Event) => {
      const { attemptId, prompt } = (e as CustomEvent<TutorExplainDetail>).detail;
      explainRef.current(attemptId, prompt);
    };
    window.addEventListener(TUTOR_EXPLAIN_EVENT, onExplain);
    return () => window.removeEventListener(TUTOR_EXPLAIN_EVENT, onExplain);
  }, []);

  // Nút "Gợi ý thêm" chỉ hiện ở câu giải thích mới nhất của mỗi lượt làm, tránh bấm lại mức cũ.
  const lastExplainId = new Map<string, string>();
  for (const item of items) if (item.kind === "assistant" && item.explainFor) lastExplainId.set(item.explainFor.attemptId, item.id);

  const cite = (lesson: string, block: string) => navigate(`/app/hoc?bai=${encodeURIComponent(lesson)}&khoi=${encodeURIComponent(block)}`);

  return <>
    {open && <section ref={panel.ref} role="dialog" aria-label="AI Tutor" aria-modal="false" style={panel.style}
      className={`fixed inset-x-2 bottom-2 z-50 flex max-h-[85vh] md:bottom-24 md:max-h-[75vh] flex-col overflow-hidden rounded-2xl border border-line bg-bg shadow-2xl sm:inset-x-auto sm:w-[380px] ${fabLeft && !panel.pos ? "sm:left-5" : "sm:right-5"} ${panel.dragging ? "select-none opacity-95" : ""}`}>
      <header {...panel.handlers} className={`flex items-center justify-between gap-2 border-b border-line bg-surface px-4 py-3 ${wide ? (panel.dragging ? "cursor-grabbing" : "cursor-grab") : ""}`}>
        {wide && <button type="button" onKeyDown={panel.onKeyDown} title="Kéo thanh này để di chuyển khung; hoặc bấm vào đây rồi dùng phím mũi tên"
          aria-label="Di chuyển khung AI Tutor bằng phím mũi tên" className="-ml-2 grid size-9 shrink-0 place-items-center rounded-md text-lg leading-none text-muted hover:bg-bg hover:text-ink">⠿</button>}
        <div className="min-w-0 flex-1">
          <h2 className="font-display text-base font-semibold text-ink">AI Tutor</h2>
          <p className="text-xs text-muted">Trả lời dựa trên bài học, nốt nhạc kiểm bằng Music Engine{remaining !== null ? ` · còn ${remaining} lượt hôm nay` : ""}</p>
        </div>
        {moved && <button type="button" className="grid size-11 shrink-0 place-items-center rounded-full text-xl leading-none text-muted hover:bg-bg hover:text-ink"
          aria-label="Đưa AI Tutor về góc phải dưới" title="Đưa về góc phải dưới" onClick={resetPlace}>↺</button>}
        <button type="button" className="grid size-11 shrink-0 place-items-center rounded-full text-2xl leading-none text-muted hover:bg-bg hover:text-ink" aria-label="Đóng AI Tutor" onClick={() => setOpen(false)}>×</button>
      </header>
      <div ref={listRef} className="flex flex-1 flex-col gap-2 overflow-y-auto px-3 py-3" aria-live="polite">
        {items.length === 0 && <p className="rounded-lg bg-primary-soft px-3 py-2 text-sm text-ink">
          Hỏi mình về nốt, quãng, hợp âm, âm giai hay vòng hòa âm trong các bài, ví dụ “C7 khác Cmaj7 thế nào?”, hoặc cách dùng trang web. Câu ngoài bài học mình sẽ ghi rõ nguồn, không biết thì nói không biết. Sau khi làm sai một câu, bấm “Giải thích lỗi này” để nhận gợi ý từng bước.
        </p>}
        {items.map((item) => item.kind === "user"
          ? <p key={item.id} className="ml-auto max-w-[85%] rounded-2xl rounded-br-sm bg-primary px-3 py-2 text-sm text-on-primary">{item.text}</p>
          : item.kind === "error"
            ? <div key={item.id} role="alert" className="rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">
                {item.text}{item.retry && <button type="button" className="ml-2 font-semibold underline" onClick={item.retry}>Thử lại</button>}
              </div>
            : <AssistantBubble key={item.id} data={item.data} onCite={cite} onOpen={(path) => navigate(path)} busy={busy}
                onMoreHint={item.explainFor && item.data.next_hint_level && lastExplainId.get(item.explainFor.attemptId) === item.id
                  ? () => explain(item.explainFor!.attemptId, item.explainFor!.prompt, item.data.next_hint_level!) : undefined} />)}
        {busy && <p className="flex items-center gap-2 text-sm text-muted"><Spinner /> Mình đang soạn câu trả lời…</p>}
      </div>
      <form onSubmit={send} className="border-t border-line bg-surface p-3">
        <label htmlFor="tutor-input" className="sr-only">Câu hỏi cho AI Tutor</label>
        <textarea id="tutor-input" ref={inputRef} rows={2} maxLength={1000} value={text} onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
          className="w-full resize-none rounded-lg border border-line bg-bg px-3 py-2 text-sm text-ink focus:border-primary"
          placeholder="Nhập câu hỏi nhạc lý…" />
        <div className="mt-2 flex items-center justify-between gap-2">
          <small className="text-xs text-muted">Đừng gửi tên thật, số điện thoại hay thông tin cá nhân.</small>
          <Button type="submit" disabled={busy || !text.trim()} className="!min-h-9 !px-3">Gửi</Button>
        </div>
      </form>
    </section>}
    {/* FE-001: trên điện thoại khung chat phủ gần hết màn hình và có nút × riêng, nên ẩn nút tròn khi khung mở;
        trước đây nút tròn nằm đè lên nút "Gửi". FE-002: nút nhỏ hơn (48px), thu vào mép khi cuộn xuống; FE-023: kéo được;
        khi nhận focus bàn phím thì luôn hiện đủ (focus-visible:translate-x-0). */}
    <button ref={fab.ref} type="button" {...fab.handlers} onKeyDown={fab.onKeyDown} style={fab.style}
      onClick={() => { if (!fab.consumeDrag()) setOpen((v) => !v); }} aria-expanded={open} aria-label={open ? "Đóng AI Tutor" : "Mở AI Tutor"}
      title="Bấm để hỏi AI Tutor. Kéo để đổi chỗ (hoặc phím mũi tên)."
      data-tucked={(tucked && !fab.dragging) || undefined}
      className={`fixed right-3 bottom-24 z-40 size-12 touch-none items-center justify-center rounded-full bg-primary text-sm font-bold text-on-primary shadow-xl ring-2 ring-bg hover:bg-primary-strong focus-visible:translate-x-0 motion-reduce:transition-none md:right-5 md:bottom-5 md:flex md:size-14 md:translate-x-0 ${fab.dragging ? "cursor-grabbing scale-110" : "cursor-grab transition-transform duration-200"} ${tucked && !fab.dragging ? (fabLeft ? "max-md:-translate-x-[calc(100%+0.5rem)]" : "max-md:translate-x-[calc(100%+0.5rem)]") : ""} ${open ? "hidden" : "flex"}`}>
      {open ? "×" : "AI"}
    </button>
  </>;
}

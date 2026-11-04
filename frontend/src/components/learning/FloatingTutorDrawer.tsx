import { useEffect, useRef, useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router";
import { api, type ApiError, type ChatReply } from "../../api";
import { TUTOR_EXPLAIN_EVENT, type TutorExplainDetail } from "../../lib/tutorBus";
import { Button, Spinner } from "../ui/Button";

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

function AssistantBubble({ data, onCite, onMoreHint, busy }: {
  data: ChatReply; onCite: (lesson: string, block: string) => void; onMoreHint?: () => void; busy: boolean;
}) {
  const contradicted = data.engine_claims.some((c) => c.status !== "verified");
  return <div className="max-w-[92%] rounded-2xl rounded-bl-sm border border-line bg-surface px-3 py-2 text-sm text-ink">
    {data.hint_level > 0 && <p className="mb-1 text-xs font-semibold text-muted">Gợi ý mức {data.hint_level}/3</p>}
    <p className="whitespace-pre-line">{data.reply}</p>
    {data.citations.length > 0 && <div className="mt-2 flex flex-wrap gap-1.5" aria-label="Nguồn trong bài học">
      {data.citations.map((c) => <button key={c.block_id} type="button" title={`${c.lesson_title} · ${c.title}`}
        className="rounded-md border border-primary/40 bg-primary-soft px-2 py-0.5 text-xs font-semibold text-primary hover:border-primary"
        onClick={() => onCite(c.lesson_id, c.block_id)}>[{c.lesson_id}] {c.title}</button>)}
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
    {open && <section role="dialog" aria-label="AI Tutor" aria-modal="false"
      className="fixed inset-x-2 bottom-20 z-40 flex max-h-[75vh] flex-col overflow-hidden rounded-2xl border border-line bg-bg shadow-2xl sm:inset-x-auto sm:right-5 sm:w-[380px]">
      <header className="flex items-center justify-between gap-2 border-b border-line bg-surface px-4 py-3">
        <div>
          <h2 className="font-display text-base font-semibold text-ink">AI Tutor</h2>
          <p className="text-xs text-muted">Trả lời dựa trên bài học, nốt nhạc kiểm bằng Music Engine{remaining !== null ? ` · còn ${remaining} lượt hôm nay` : ""}</p>
        </div>
        <button type="button" className="rounded-md px-2 py-1 text-lg leading-none text-muted hover:text-ink" aria-label="Đóng AI Tutor" onClick={() => setOpen(false)}>×</button>
      </header>
      <div ref={listRef} className="flex flex-1 flex-col gap-2 overflow-y-auto px-3 py-3" aria-live="polite">
        {items.length === 0 && <p className="rounded-lg bg-primary-soft px-3 py-2 text-sm text-ink">
          Hỏi mình về nốt, quãng, hợp âm, âm giai hay vòng hòa âm, ví dụ “C7 khác Cmaj7 thế nào?”. Sau khi làm sai một câu, bấm “Giải thích lỗi này” để nhận gợi ý từng bước.
        </p>}
        {items.map((item) => item.kind === "user"
          ? <p key={item.id} className="ml-auto max-w-[85%] rounded-2xl rounded-br-sm bg-primary px-3 py-2 text-sm text-white">{item.text}</p>
          : item.kind === "error"
            ? <div key={item.id} role="alert" className="rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">
                {item.text}{item.retry && <button type="button" className="ml-2 font-semibold underline" onClick={item.retry}>Thử lại</button>}
              </div>
            : <AssistantBubble key={item.id} data={item.data} onCite={cite} busy={busy}
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
    <button type="button" onClick={() => setOpen((v) => !v)} aria-expanded={open} aria-label={open ? "Đóng AI Tutor" : "Mở AI Tutor"}
      className="fixed right-5 bottom-5 z-40 flex size-14 items-center justify-center rounded-full bg-primary text-sm font-bold text-white shadow-xl hover:bg-primary-strong">
      {open ? "×" : "AI"}
    </button>
  </>;
}

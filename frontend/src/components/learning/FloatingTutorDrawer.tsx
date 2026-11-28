import { useEffect, useRef, useState, useSyncExternalStore, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router";
import { api, type ApiError, type ChatReply } from "../../api";
import { TUTOR_EXPLAIN_EVENT, type TutorExplainDetail } from "../../lib/tutorBus";
import { Button, Spinner } from "../ui/Button";
import { activateTutorScope, patchTutorContext, readTutorContext, subscribeTutorContext } from "../../lib/tutorContext";
import { ROOT_KEY_OPTIONS } from "../../content/lessons";

// Khung AI Tutor nổi ở góc phải dưới trên mọi trang /app/* (04 Bảng 25, đề GĐ3 mục 11).
// Mọi phán đoán nhạc lý, trích dẫn và nhãn "Đã kiểm bằng Music Engine" đều do máy chủ quyết; ở đây chỉ hiển thị.

type Item =
  | { kind: "user"; id: string; text: string }
  | { kind: "assistant"; id: string; data: ChatReply; explainFor?: { attemptId: string; prompt: string } }
  | { kind: "error"; id: string; text: string; retry?: () => void };

const FALLBACK_NOTE: Record<string, string> = {
  ai_disabled: "Trợ lý AI đang tắt.",
  timeout: "AI trả lời quá lâu.",
  rate_limited: "AI đang quá tải.",
  unavailable: "AI đang tạm thời không khả dụng.",
  global_budget: "Hôm nay hệ thống đã dùng hết lượt AI.",
  engine_contradiction: "Câu AI soạn sai với Music Engine nên đã được thay bằng câu trả lời an toàn.",
  answer_leak: "Câu AI soạn để lộ đáp án nên đã được thay bằng gợi ý viết sẵn.",
  format_error: "AI trả lời sai định dạng nên đã được thay bằng câu trả lời lấy từ bài học.",
  prompt_leak: "Câu trả lời bị chặn vì không an toàn.",
  lesson_ungrounded: "AI chưa có nguồn bài học để trả lời nên đã được thay bằng câu trả lời lấy từ bài học.",
  engine_fact_missing: "Chưa xác minh được bậc hợp âm bằng Music Engine nên đã dùng câu trả lời an toàn.",
  engine_fact_mismatch: "Câu AI soạn không khớp kết quả của Music Engine nên đã được thay bằng câu trả lời an toàn.",
  out_of_scope_intent: "Câu hỏi nằm ngoài phạm vi bài học nên đã dùng câu trả lời an toàn.",
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
  const showVerified = data.verified && !!data.verified_label && data.engine_claims.length > 0 && !contradicted;
  const lessonCites = data.citations.filter((c) => c.lesson_id !== "HELP");
  return <div className="max-w-[92%] rounded-2xl rounded-bl-sm border border-line bg-surface px-3 py-2 text-sm text-ink">
    {data.source_label && data.flow && <p className={`mb-1 inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${FLOW_STYLE[data.flow] ?? "text-muted"}`}>
      {data.source_label}
    </p>}
    {data.hint_level > 0 && <p className="mb-1 text-xs font-semibold text-muted">Gợi ý mức {data.hint_level}/3</p>}
    <p className="whitespace-pre-line">{data.reply}</p>
    {data.supplemental_source && data.supplemental_source.url.startsWith("https://") && <a
      className="mt-2 inline-block text-xs font-semibold text-primary underline"
      href={data.supplemental_source.url} target="_blank" rel="noopener noreferrer">
      {data.supplemental_source.title}
    </a>}
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
      {showVerified && <span title="Chỉ xác minh các dữ kiện nhận diện được trong câu trả lời; không xác minh toàn bộ lời giải hoặc mức độ phù hợp với câu hỏi." className="rounded-full bg-success-soft px-2 py-0.5 font-semibold text-success">✓ Đã kiểm tra dữ kiện nhạc lý hiển thị bằng Music Engine</span>}
      {!showVerified && contradicted && <span className="rounded-full bg-warning-soft px-2 py-0.5 font-semibold text-warning">Có chỗ chưa kiểm được bằng Music Engine</span>}
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
  const contextScope = location.pathname + location.search;
  const musicContext = useSyncExternalStore(subscribeTutorContext, () => readTutorContext(contextScope));
  useEffect(() => { activateTutorScope(contextScope); }, [contextScope]);

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
    // Capture the context now: retry must not inherit a later selection.
    const context = { ...contextFromPath(location.pathname, location.search), ...readTutorContext(contextScope) };
    // Dùng lại phiên để hỏi nối tiếp được ("Vậy nó là bậc mấy?"). Backend chỉ dùng lịch sử khi câu hỏi
    // chỉ tới hợp âm trước đó; câu độc lập không nhận lịch sử (xem ai_tutor_service.handle_message).
    void run(() => api.chatMessage(message, sessionId, context));
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
          <p className="text-xs text-muted">Trả lời dựa trên bài học, Music Engine và nguồn tham khảo đã duyệt{remaining !== null ? ` · còn ${remaining} lượt hôm nay` : ""}</p>
        </div>
        <button type="button" className="rounded-md px-2 py-1 text-lg leading-none text-muted hover:text-ink" aria-label="Đóng AI Tutor" onClick={() => setOpen(false)}>×</button>
      </header>
      <div ref={listRef} className="flex flex-1 flex-col gap-2 overflow-y-auto px-3 py-3" aria-live="polite">
        {items.length === 0 && <p className="rounded-lg bg-primary-soft px-3 py-2 text-sm text-ink">
          Hỏi mình về nốt, quãng, hợp âm, âm giai hay vòng hòa âm trong các bài, ví dụ “C7 khác Cmaj7 thế nào?”, hoặc cách dùng trang web. Câu ngoài bài học mình sẽ ghi rõ nguồn, không biết thì nói không biết. Sau khi làm sai một câu, bấm “Giải thích lỗi này” để nhận gợi ý từng bước.
        </p>}
        {items.map((item) => item.kind === "user"
          ? <p key={item.id} className="ml-auto max-w-[85%] rounded-2xl rounded-br-sm bg-primary px-3 py-2 text-sm text-white">{item.text}</p>
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
        <fieldset className="mb-2 grid gap-1 text-xs">
          <legend>Giọng để hỏi AI (không đổi đề bài)</legend>
          <div className="flex gap-2">
            <select aria-label="Giọng ngữ cảnh AI" value={musicContext.selected_key ?? ""}
              onChange={(e) => patchTutorContext(contextScope, { selected_key: e.target.value || undefined, mode: e.target.value ? musicContext.mode ?? "major" : undefined })}>
              <option value="">Chưa chọn giọng</option>
              {ROOT_KEY_OPTIONS.flatMap((item) => item.spellings).map((key) => <option key={key} value={key}>{key}</option>)}
            </select>
            <select aria-label="Loại giọng ngữ cảnh AI" disabled={!musicContext.selected_key} value={musicContext.mode ?? "major"}
              onChange={(e) => patchTutorContext(contextScope, { mode: e.target.value as "major" | "natural_minor" })}>
              <option value="major">Trưởng</option><option value="natural_minor">Thứ tự nhiên</option>
            </select>
          </div>
          <span>Đang xem: {musicContext.selected_chord ? `hợp âm ${musicContext.selected_chord}` : musicContext.selected_root ? `nốt gốc ${musicContext.selected_root}` : "chưa chọn hợp âm"}. Nốt gốc không tự xác định giọng.</span>
        </fieldset>
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
      className="fixed right-4 bottom-24 z-40 flex size-14 md:right-5 md:bottom-5 items-center justify-center rounded-full bg-primary text-sm font-bold text-white shadow-xl hover:bg-primary-strong">
      {open ? "×" : "AI"}
    </button>
  </>;
}

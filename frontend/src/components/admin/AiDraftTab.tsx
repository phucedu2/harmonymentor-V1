import { useEffect, useState, type FormEvent } from "react";
import { api, type AiBudget, type AiDocument, type AiDraft, type AiDraftRow, type AiFlag, type AiJob, type AiQuestion, type AiQuestionKind } from "../../api";
import { remapAfterBlockRemoved, unackedCount } from "../../lib/aiDraftReview";
import { Button } from "../ui/Button";
import { Badge, Card, CardTitle, ProgressBar } from "../ui/Page";

const errMsg = (e: unknown) => (e as { message?: string }).message ?? "Có lỗi xảy ra, thử lại sau.";
const KIND: Record<AiQuestionKind, string> = {
  mcq: "Trắc nghiệm", true_false: "Đúng/Sai", multi_select: "Chọn nhiều", short: "Tự luận ngắn",
  build_chord: "Dựng hợp âm", build_scale: "Dựng âm giai", open: "Tự luận mở",
};
const LEVEL: Record<string, string> = { nho: "Nhớ", hieu: "Hiểu", van_dung: "Vận dụng" };
const show = (v: string | string[] | null | undefined) => (Array.isArray(v) ? v.join(" ") : v ?? "—");
// Câu cũ (trước ADR-028) chưa có needs_review: chỉ câu dựng hợp âm/âm giai là Engine tự kiểm.
const needsReview = (q: AiQuestion) => q.needs_review ?? !["build_chord", "build_scale"].includes(q.kind);

const NODE: Record<string, string> = {
  extract: "Lấy chữ", retrieve: "Tìm bài đã có", generate: "AI soạn", retry_json: "Thử lại JSON", dedup: "Bỏ ý trùng",
  validate: "Kiểm câu bằng Engine", flags: "Tính cờ duyệt", draft: "Lưu bản nháp", error: "Lỗi", top_up: "Gọi bù câu luyện tập",
};
// Hạn mức Gemini chung (ADR-033, V5): bản miễn phí 30 lượt/ngày, 40% soạn bài, 60% AI Tutor.
function BudgetLine({ budget }: { budget?: AiBudget }) {
  if (!budget || !budget.total) return null;
  const left = Math.max(0, budget.authoring.limit - budget.authoring.used);
  const at = new Date(budget.resets_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
  return <p className="text-xs text-muted">Lượt Gemini cho soạn bài hôm nay: còn {left}/{budget.authoring.limit} (AI Tutor {budget.tutor.used}/{budget.tutor.limit}), đặt lại lúc {at}.</p>;
}
function NodeLog({ log }: { log?: { node: string; ms: number; in?: number; out?: number; note?: string }[] }) {
  if (!log?.length) return null;
  return <details className="w-full text-xs text-muted"><summary className="cursor-pointer">Nhật ký từng bước ({log.length})</summary>
    <ol className="list-decimal pl-5">{log.map((r, i) => <li key={i}><b>{NODE[r.node] ?? r.node}</b> · {r.ms} ms
      {r.in !== undefined ? ` · vào ${r.in}` : ""}{r.out !== undefined ? ` · ra ${r.out}` : ""}{r.note ? ` · ${r.note}` : ""}</li>)}</ol></details>;
}
function FlagItem({ f, checked, disabled, onChange }: { f: AiFlag; checked: boolean; disabled: boolean; onChange: (v: boolean) => void }) {
  return <li className={`rounded border p-2 ${checked ? "border-line" : "border-warning"}`}>
    <p><b>{f.label}</b>{f.where.startsWith("block:") ? ` (khối ${f.where.slice(6)})` : f.where.startsWith("question:") ? ` (câu ${f.where.slice(9)})` : ""}: {f.detail}</p>
    <label className="mt-1 flex items-center gap-2 font-semibold"><input type="checkbox" checked={checked} disabled={disabled}
      onChange={(e) => onChange(e.target.checked)} />Đã đối chiếu với tài liệu gốc</label></li>;
}

// AI chỉ soạn BẢN NHÁP (ADR-025). Bài chỉ tới học sinh khi Quản trị viên bấm xuất bản ở đây.
function DraftEditor({ draftId, onClose }: { draftId: string; onClose: () => void }) {
  const [draft, setDraft] = useState<AiDraft | null>(null);
  const [ack, setAck] = useState(false);
  // Khóa hành động đang chạy: chỉ nút vừa bấm hiện vòng quay, các nút khác chỉ tạm khóa.
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [moreKinds, setMoreKinds] = useState<AiQuestionKind[]>([]);
  const load = () => api.aiDraft(draftId).then(setDraft).catch((e) => setMsg(errMsg(e)));
  useEffect(() => { load(); }, [draftId]);
  if (!draft) return <p className="text-muted">{msg ?? "Đang tải…"}</p>;
  const c = draft.content;
  const open = draft.status === "draft";
  const flags = draft.engine.contradicted.length;
  const set = (patch: Partial<typeof c>) => setDraft({ ...draft, content: { ...c, ...patch } });
  // ADR-033: cờ duyệt là cảnh báo; mỗi cờ phải tick "Đã đối chiếu" (lưu theo mã cờ) thì mới xuất bản được.
  const reviewFlags = draft.flags ?? [];
  const acked = c.acknowledged_flags ?? [];
  const unacked = unackedCount(reviewFlags, acked);
  const toggleFlag = (id: string, v: boolean) => set({ acknowledged_flags: v ? [...acked, id] : acked.filter((x) => x !== id) });
  const body = () => ({ title: c.title, objectives: c.objectives, blocks: c.blocks, questions: c.questions, expansion: Boolean(c.expansion), acknowledged_flags: acked });
  // Xóa khối thì câu gắn khối đó mất chỗ gắn (cần duyệt lại), câu gắn khối sau dời số thứ tự.
  const removeBlock = (i: number) => set({ blocks: c.blocks.filter((_, j) => j !== i), questions: remapAfterBlockRemoved(c.questions, i) });
  const flagsAt = (where: string) => reviewFlags.filter((f) => f.where === where);
  const run = async (key: string, fn: () => Promise<void>) => { setBusy(key); setMsg(null); try { await fn(); } catch (e) { setMsg(errMsg(e)); } finally { setBusy(null); } };
  const save = () => run("save", async () => { setDraft(await api.aiSaveDraft(draft.id, body())); setAck(false); setMsg("Đã lưu, soát lại bằng Music Engine và tính lại cờ duyệt."); });
  // Lưu trước khi xuất bản: dấu "Đã duyệt" vừa tick chỉ có hiệu lực khi máy chủ đã lưu (máy chủ kiểm lại lúc xuất bản).
  const publish = () => run("publish", async () => {
    const saved = await api.aiSaveDraft(draft.id, body());
    const left = unackedCount(saved.flags, saved.content.acknowledged_flags);
    if (left) { setDraft(saved); setMsg(`Sửa đổi vừa rồi sinh ${left} cờ mới cần đối chiếu trước khi xuất bản.`); return; }
    const r = await api.aiPublish(draft.id, ack);
    setMsg(`Đã xuất bản bài “${r.title}” ở trạng thái ẨN. Bấm “Xem như học sinh” để kiểm, rồi “Hiện cho học sinh”.`); await load(); });
  const reveal = () => run("reveal", async () => {
    const r = await api.adminVisibility(draft.published_lesson_id!, false);
    setMsg(`Học sinh đã thấy bài.${r.tutor_index ? ` AI Tutor đã nạp ${r.tutor_index.chunks} đoạn${r.tutor_index.qdrant === "error" ? " (Qdrant lỗi, AI Tutor vẫn tìm được bằng đường dự phòng)" : ""}.` : ""}`);
    setDraft({ ...draft, lesson_hidden: false }); });
  const pending = c.questions.filter((q) => needsReview(q) && !q.reviewed).length;
  const setQ = (i: number, patch: Partial<AiQuestion>) => set({ questions: c.questions.map((x, j) => (j === i ? { ...x, ...patch } : x)) });
  const more = () => run("more", async () => {
    setMsg("AI đang soạn thêm câu luyện tập, có thể mất đến một phút…");
    // Lưu sửa đổi trước, vì sinh thêm câu đọc bản nháp đang lưu trên máy chủ.
    await api.aiSaveDraft(draft.id, body());
    const before = c.questions.length;
    const next = await api.aiMoreQuestions(draft.id, moreKinds);
    setDraft(next); setMsg(`AI đã thêm ${next.content.questions.length - before} câu. Câu Engine không kiểm được cần bạn đọc và tick “Đã duyệt”.`);
  });
  const reject = () => run("reject", async () => { if (!window.confirm("Từ chối bản nháp này?")) return; await api.aiReject(draft.id); await load(); });

  return <div className="grid gap-3">
    <div className="flex flex-wrap items-center gap-2">
      <Button variant="ghost" onClick={onClose}>← Danh sách</Button>
      <Badge tone={draft.status === "published" ? "success" : draft.status === "rejected" ? "muted" : "warning"}>
        {draft.status === "published" ? "Đã xuất bản" : draft.status === "rejected" ? "Đã từ chối" : "Bản nháp"}</Badge>
      <span className="text-sm text-muted">Nguồn: {draft.document?.source_title}{c.part ? ` · ${c.part.heading}` : ""}, trang {draft.page_from}–{draft.page_to} · AI: {draft.model}</span>
    </div>
    {(c.duplicates?.length ?? 0) > 0 && <details className="rounded-lg border border-line p-3 text-sm">
      <summary className="cursor-pointer font-semibold">{c.duplicates!.length} ý trong phần này trang web đã có nên AI đã bỏ</summary>
      <ul className="mt-2 grid gap-1">{c.duplicates!.map((d, i) => <li key={i}><b>{d.concept}</b>{d.where ? <> · đã có ở {d.where}</> : null}
        <span className="text-muted"> ({d.by === "ai" ? "AI nhận ra" : `máy so độ giống ${d.score?.toFixed(2)}`})</span></li>)}</ul></details>}
    <p className="rounded-lg bg-primary-soft p-2 text-sm">AI chỉ tóm tắt và gợi ý. Hãy đọc đối chiếu với tài liệu gốc trước khi xuất bản. Đáp án câu dựng hợp âm/âm giai do Music Engine tính, không phải AI.</p>

    <div className={`rounded-lg border p-3 text-sm ${flags ? "border-danger" : "border-line"}`} role={flags ? "alert" : "status"}>
      {draft.engine.checked === 0 ? "Music Engine: không có khẳng định nốt/hợp âm nào để soát."
        : flags === 0 ? `Music Engine đã soát ${draft.engine.checked} khẳng định: không thấy chỗ sai.`
        : <><p className="font-semibold text-danger">Music Engine thấy {flags} chỗ có thể sai:</p>
            <ul className="mt-1 list-disc pl-5">{draft.engine.contradicted.map((f, i) => <li key={i}>({(f as { where?: string }).where}) viết “{f.claimed}”, Engine tính “{f.engine}”</li>)}</ul></>}
    </div>

    {c.truncated && <p className="rounded-lg border border-warning p-3 text-sm" role="alert">{c.truncated}</p>}
    {reviewFlags.filter((f) => !f.where.startsWith("block:")).length > 0 && <ul className="grid gap-2 text-sm" aria-label="Cờ chung của bản nháp">
      {reviewFlags.filter((f) => !f.where.startsWith("block:")).map((f) => <FlagItem key={f.id} f={f} checked={acked.includes(f.id)} disabled={!open} onChange={(v) => toggleFlag(f.id, v)} />)}</ul>}
    {open && <BudgetLine budget={draft.budget} />}

    <label className={`flex items-start gap-2 rounded-lg border p-3 text-sm ${c.expansion ? "border-primary bg-primary-soft" : "border-line"}`}>
      <input type="checkbox" className="mt-1" checked={Boolean(c.expansion)} disabled={!open} onChange={(e) => set({ expansion: e.target.checked })} />
      <span><b>Bài “Mở rộng”</b>: kiến thức mới chưa khớp kỹ năng nào của lộ trình. Học sinh vẫn làm và được chấm, nhưng câu luyện tập
        không tính vào mức thành thạo và không vào Quiz kỹ năng. AI đề xuất, bạn quyết định.</span></label>
    <label className="text-sm font-semibold" htmlFor="ai-title">Tên bài</label>
    <input id="ai-title" value={c.title} disabled={!open} onChange={(e) => set({ title: e.target.value })} className="min-h-10 rounded-lg border border-line bg-surface px-3" />
    <label className="text-sm font-semibold" htmlFor="ai-obj">Mục tiêu (mỗi dòng một mục)</label>
    <textarea id="ai-obj" rows={3} value={c.objectives.join("\n")} disabled={!open} onChange={(e) => set({ objectives: e.target.value.split("\n").filter((l) => l.trim()) })} className="rounded-lg border border-line bg-surface p-2" />

    <h3 className="font-semibold">Khối lý thuyết ({c.blocks.length})</h3>
    {c.blocks.map((b, i) => <Card key={i} className="grid gap-2 p-3">
      <input aria-label={`Tiêu đề khối ${i + 1}`} value={b.title} disabled={!open} className="min-h-9 rounded border border-line bg-surface px-2 font-semibold"
        onChange={(e) => set({ blocks: c.blocks.map((x, j) => (j === i ? { ...x, title: e.target.value } : x)) })} />
      <textarea aria-label={`Nội dung khối ${i + 1}`} rows={4} value={b.paragraphs.join("\n\n")} disabled={!open} className="rounded border border-line bg-surface p-2"
        onChange={(e) => set({ blocks: c.blocks.map((x, j) => (j === i ? { ...x, paragraphs: e.target.value.split(/\n\s*\n/).filter((l) => l.trim()) } : x)) })} />
      <p className="text-xs text-muted">Lấy từ trang {b.page}{b.page_claimed ? ` (AI ghi trang ${b.page_claimed}, ngoài phần này)` : ""}</p>
      {flagsAt(`block:${i + 1}`).length > 0 && <ul className="grid gap-2 text-sm" aria-label={`Cờ của khối ${i + 1}`}>
        {flagsAt(`block:${i + 1}`).map((f) => <FlagItem key={f.id} f={f} checked={acked.includes(f.id)} disabled={!open} onChange={(v) => toggleFlag(f.id, v)} />)}</ul>}
      {open && <Button variant="ghost" onClick={() => removeBlock(i)}>Xóa khối này</Button>}
    </Card>)}

    <h3 className="font-semibold">Câu luyện tập ({c.questions.length})</h3>
    <p className="text-sm text-muted">Câu có nhãn “Engine đã kiểm” có đáp án do Music Engine tính. Câu “Cần duyệt” là câu khái niệm Engine không kiểm được:
      đọc kỹ đề, đáp án, giải thích rồi tick “Đã duyệt” thì mới xuất bản được.</p>
    {c.questions.map((q, i) => <Card key={i} className={`grid gap-2 p-3 ${needsReview(q) && !q.reviewed ? "border-warning" : ""}`}>
      <p className="flex flex-wrap items-center gap-1.5 text-xs text-muted">
        <Badge tone="muted">{KIND[q.kind] ?? q.kind}</Badge>{q.level && <Badge tone="muted">{LEVEL[q.level]}</Badge>}
        {needsReview(q) ? <Badge tone={q.reviewed ? "success" : "warning"}>{q.reviewed ? "Đã duyệt" : "Cần duyệt"}</Badge> : <Badge tone="success">Engine đã kiểm</Badge>}
        kỹ năng {q.skill_id} · trang {q.page}{typeof q.block_ref === "number" ? ` · khối ${q.block_ref}` : ""}</p>
      {(q.review_notes?.length ?? 0) > 0 && <ul className="list-disc pl-5 text-sm text-warning">{q.review_notes!.map((n, k) => <li key={k}>{n}</li>)}</ul>}
      <textarea aria-label={`Đề câu ${i + 1}`} rows={2} value={q.prompt} disabled={!open} className="rounded border border-line bg-surface p-2"
        onChange={(e) => setQ(i, { prompt: e.target.value, reviewed: false })} />
      {q.engine_note && <p className="text-sm text-warning">{q.engine_note}</p>}
      {(q.kind === "mcq" || q.kind === "true_false") && <p className="text-sm">Phương án: {q.options?.map((o) => o === q.answer ? `✔ ${o}` : o).join(" · ")}</p>}
      {q.kind === "multi_select" && <p className="text-sm">Phương án: {q.options?.map((o) => q.answers?.includes(o) ? `✔ ${o}` : o).join(" · ")}</p>}
      {q.option_feedback && Object.keys(q.option_feedback).length > 0 && <ul className="list-disc pl-5 text-xs text-muted">
        {Object.entries(q.option_feedback).map(([o, why]) => <li key={o}><b>{o}</b>: {why}</li>)}</ul>}
      {(q.kind === "build_chord" || q.kind === "build_scale" || q.kind === "short") &&
        <p className="text-sm">Đáp án do Music Engine tính: <b>{show(q.engine_answer)}</b>{q.kind === "build_chord" ? ` (${q.symbol})` : q.kind === "build_scale" ? ` (${q.tonic} ${q.scale_type})` : ""}</p>}
      {q.kind === "open" && <>
        <label className="text-sm font-semibold" htmlFor={`ai-model-${i}`}>Đáp án mẫu</label>
        <textarea id={`ai-model-${i}`} rows={3} value={q.model_answer ?? ""} disabled={!open} className="rounded border border-line bg-surface p-2 text-sm"
          onChange={(e) => setQ(i, { model_answer: e.target.value, reviewed: false })} />
        <label className="text-sm font-semibold" htmlFor={`ai-rubric-${i}`}>Ý chấm (mỗi dòng một ý, 2–5 ý)</label>
        <textarea id={`ai-rubric-${i}`} rows={3} value={(q.rubric ?? []).join("\n")} disabled={!open} className="rounded border border-line bg-surface p-2 text-sm"
          onChange={(e) => setQ(i, { rubric: e.target.value.split("\n").filter((l) => l.trim()), reviewed: false })} />
      </>}
      <textarea aria-label={`Lời giải câu ${i + 1}`} rows={2} value={q.explanation} disabled={!open} placeholder="Lời giải" className="rounded border border-line bg-surface p-2 text-sm"
        onChange={(e) => setQ(i, { explanation: e.target.value })} />
      {open && <div className="flex flex-wrap items-center gap-3">
        {needsReview(q) && <label className="flex items-center gap-2 text-sm font-semibold"><input type="checkbox" checked={Boolean(q.reviewed)}
          onChange={(e) => setQ(i, { reviewed: e.target.checked })} />Đã duyệt: tôi đã đọc đề, đáp án và lời giải</label>}
        <Button variant="ghost" onClick={() => set({ questions: c.questions.filter((_, j) => j !== i) })}>Xóa câu này</Button>
      </div>}
    </Card>)}
    {open && <div className="grid gap-2 rounded-lg border border-line p-3">
      <p className="text-sm font-semibold">AI sinh thêm câu luyện tập (tối đa 20 câu mỗi bài)</p>
      <div className="flex flex-wrap gap-3 text-sm">{(Object.keys(KIND) as AiQuestionKind[]).map((k) => <label key={k} className="flex items-center gap-1">
        <input type="checkbox" checked={moreKinds.includes(k)} onChange={(e) => setMoreKinds(e.target.checked ? [...moreKinds, k] : moreKinds.filter((x) => x !== k))} />{KIND[k]}</label>)}</div>
      <p className="text-xs text-muted">Không tick dạng nào thì AI trộn đủ các dạng. Sửa đổi chưa lưu sẽ được lưu trước.</p>
      <div><Button variant="secondary" loading={busy === "more"} disabled={busy !== null || c.questions.length >= 20} onClick={more}>AI sinh thêm câu</Button></div>
    </div>}
    {c.dropped_questions.length > 0 && <details className="text-sm text-muted"><summary>{c.dropped_questions.length} câu AI gợi ý đã bị loại tự động</summary>
      <ul className="list-disc pl-5">{c.dropped_questions.map((d, i) => <li key={i}>{d}</li>)}</ul></details>}

    {open && <div className="grid gap-2 rounded-lg border border-line p-3">
      <div className="flex flex-wrap gap-2">
        <Button variant="secondary" loading={busy === "save"} disabled={busy !== null} onClick={save}>Lưu và soát lại</Button>
        <Button variant="ghost" disabled={busy !== null} onClick={reject}>Từ chối bản nháp</Button>
      </div>
      {flags > 0 && <label className="flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={ack} onChange={(e) => setAck(e.target.checked)} />
        Tôi đã đối chiếu tài liệu gốc và vẫn muốn xuất bản dù Engine báo nghi sai.</label>}
      {unacked > 0 && <p className="text-sm text-warning" role="status">Còn {unacked} cờ chưa đối chiếu. Đọc lại trang gốc rồi tick “Đã đối chiếu” ở từng cờ.</p>}
      {pending > 0 && <p className="text-sm text-warning" role="status">Còn {pending} câu cần duyệt. Đọc kỹ rồi tick “Đã duyệt” ở từng câu.</p>}
      <Button loading={busy === "publish"} disabled={busy !== null || (flags > 0 && !ack) || pending > 0 || unacked > 0} onClick={publish}>Xuất bản thành bài học</Button>
      <p className="text-xs text-muted">Bấm xuất bản sẽ tự lưu các sửa đổi rồi soát lại bằng Music Engine. Bài mới ở trạng thái ẩn: xem trước như học sinh rồi mới hiện.</p>
    </div>}
    {draft.status === "published" && draft.published_lesson_id && <div className="flex flex-wrap items-center gap-2 rounded-lg border border-line p-3 text-sm">
      <a className="font-semibold text-primary underline" href={`/app/hoc?xem_truoc=${encodeURIComponent(draft.published_lesson_id)}`} target="_blank" rel="noreferrer">Xem như học sinh</a>
      {draft.lesson_hidden === false ? <Badge tone="success">Học sinh đã thấy bài</Badge>
        : <Button variant="secondary" loading={busy === "reveal"} disabled={busy !== null} onClick={reveal}>Hiện cho học sinh</Button>}
      <span className="text-xs text-muted">Lượt làm thử của Quản trị viên không tính vào thống kê. Ẩn lại ở thẻ Bài học.</span></div>}
    {msg && <p role="status" className="text-sm">{msg}</p>}
  </div>;
}

const PART: Record<AiJob["parts"][number]["status"], { label: string; tone: "success" | "warning" | "muted" | "primary" | "danger" }> = {
  pending: { label: "Chờ", tone: "muted" },
  running: { label: "AI đang soạn…", tone: "primary" },
  done: { label: "Có bản nháp", tone: "success" },
  no_new: { label: "Không có gì mới", tone: "muted" },
  not_theory: { label: "Không phải nhạc lý", tone: "muted" },
  failed: { label: "Lỗi", tone: "danger" },
};
const PAUSE: Record<string, string> = {
  quota: "Gemini báo hết hạn mức. Đợi hạn mức hồi (thường sau 15:00 giờ Việt Nam hoặc hôm sau) rồi bấm “Chạy tiếp”: hệ thống làm nốt từ phần đang dở.",
  daily_limit: "Đã dùng hết lượt Gemini dành cho soạn bài hôm nay (hạn mức chung với AI Tutor). Sau 15:00 giờ Việt Nam bấm “Chạy tiếp”.",
  unavailable: "Hai phần liền nhau lỗi nên hệ thống tạm dừng để không tốn lượt. Bấm “Chạy tiếp” để thử lại các phần lỗi.",
  interrupted: "Máy chủ khởi động lại giữa chừng. Bấm “Chạy tiếp” để làm nốt.",
  admin: "Bạn đã dừng việc này.",
  document_deleted: "Tài liệu đã bị xóa.",
};

// Tiến độ tóm tắt cả tài liệu (ADR-029): mỗi phần (chương) thành một bản nháp; phần trùng kiến thức đã có thì không tạo bài.
function JobPanel({ job, busy, onResume, onCancel, onOpen }: {
  job: AiJob; busy: boolean; onResume: () => void; onCancel: () => void; onOpen: (draftId: string) => void;
}) {
  const pct = Math.round((job.finished / Math.max(1, job.total)) * 100);
  const running = job.status === "running";
  const noNew = job.parts.filter((p) => p.status === "no_new").length;
  return <div className="mt-3 grid gap-2 rounded-lg bg-bg p-3 text-sm" aria-label="Tiến độ AI tóm tắt">
    <div className="flex flex-wrap items-center gap-3">
      <ProgressBar className="w-40 shrink-0" value={pct} label="Tiến độ tóm tắt" />
      <span role="status">{running ? `AI đang soạn phần ${Math.min(job.finished + 1, job.total)}/${job.total}…`
        : job.status === "done" ? `Xong ${job.total} phần: ${job.drafts} bản nháp mới${noNew ? `, ${noNew} phần không có gì mới` : ""}.`
        : job.status === "paused" ? `Tạm dừng ở ${job.finished}/${job.total} phần.` : `Đã dừng ở ${job.finished}/${job.total} phần.`}</span>
      {job.status === "paused" && <Button variant="secondary" loading={busy} onClick={onResume}>Chạy tiếp</Button>}
      {(running || job.status === "paused") && <Button variant="ghost" disabled={busy} onClick={onCancel}>Dừng hẳn</Button>}
    </div>
    {job.status === "paused" && job.pause_reason && <p className="text-warning">{PAUSE[job.pause_reason] ?? job.pause_reason}</p>}
    <BudgetLine budget={job.budget} />
    <ol className="grid gap-1.5">{job.parts.map((p) => <li key={p.index} className="flex flex-wrap items-center gap-2">
      <Badge tone={PART[p.status].tone}>{PART[p.status].label}</Badge>
      <span className="font-medium">{p.heading}</span><span className="text-muted">trang {p.page_from}–{p.page_to}</span>
      {p.draft_id && <Button variant="ghost" className="!min-h-8 !px-2" onClick={() => onOpen(p.draft_id!)}>Mở bản nháp</Button>}
      {p.note && <span className="w-full text-xs text-muted">{p.note}</span>}
      <NodeLog log={p.log} />
      {p.duplicates.length > 0 && <details className="w-full text-xs text-muted"><summary className="cursor-pointer">{p.duplicates.length} ý đã có trên trang web, không soạn lại</summary>
        <ul className="list-disc pl-5">{p.duplicates.map((d, i) => <li key={i}>{d.concept}{d.where ? ` (đã có ở ${d.where})` : ""}</li>)}</ul></details>}
    </li>)}</ol>
    {job.skipped_pages.length > 0 && <details className="text-xs text-muted"><summary className="cursor-pointer">Đã bỏ qua {job.skipped_pages.length} trang không phải nội dung</summary>
      <ul className="list-disc pl-5">{job.skipped_pages.map((s) => <li key={s.page}>Trang {s.page}: {s.reason}</li>)}</ul></details>}
  </div>;
}

export default function AiDraftTab() {
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [ai, setAi] = useState<{ env_ready: boolean; switch_on: boolean } | null>(null);
  const [docs, setDocs] = useState<AiDocument[]>([]);
  const [drafts, setDrafts] = useState<AiDraftRow[]>([]);
  const [jobs, setJobs] = useState<AiJob[]>([]);
  const [openId, setOpenId] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [fileKey, setFileKey] = useState(0);   // AUD-05: đổi key để ô chọn tệp trống lại sau khi tải lên xong
  const [title, setTitle] = useState("");
  const [note, setNote] = useState("");
  const [consent, setConsent] = useState(false);
  // Mỗi nút có khóa riêng: bấm soạn một tài liệu thì chỉ nút của tài liệu đó quay (trước đây mọi nút cùng quay).
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [pasted, setPasted] = useState("");

  const load = () => {
    api.aiDocuments().then(setDocs).catch(() => undefined);
    api.aiDrafts().then(setDrafts).catch(() => undefined);
    api.aiJobs().then(setJobs).catch(() => undefined);
  };
  const loadStatus = () => api.aiStatus().then((s) => { setEnabled(s.enabled); setAi(s); }).catch(() => setEnabled(false));
  useEffect(() => { loadStatus(); load(); }, []);
  // ADR-036: công tắc lưu CSDL, tắt cả AI Tutor lẫn soạn bài; khóa Gemini vẫn chỉ nằm trong .env.
  const flipSwitch = async () => {
    if (!ai) return;
    if (ai.switch_on && !window.confirm("Tắt AI cho toàn hệ thống? AI Tutor và AI soạn bài dừng gọi Gemini, app vẫn chạy bằng luật dự phòng.")) return;
    setBusyKey("switch");
    try { await api.adminSetAiSwitch(!ai.switch_on); await loadStatus(); }
    catch (e) { setMsg((e as { message?: string }).message ?? "Không đổi được công tắc AI."); }
    finally { setBusyKey(null); }
  };
  // Việc đang chạy nền: hỏi tiến độ mỗi 3 giây; xong thì tải lại danh sách bản nháp.
  const anyRunning = jobs.some((j) => j.status === "running");
  useEffect(() => {
    if (!anyRunning || openId) return;
    const t = window.setInterval(() => {
      api.aiJobs().then((next) => {
        setJobs(next);
        if (!next.some((j) => j.status === "running")) api.aiDrafts().then(setDrafts).catch(() => undefined);
      }).catch(() => undefined);
    }, 3000);
    return () => window.clearInterval(t);
  }, [anyRunning, openId]);

  const act = async (key: string, fn: () => Promise<string | null | void>) => {
    setBusyKey(key); setMsg(null);
    try { const m = await fn(); if (m) setMsg(m); } catch (err) { setMsg(errMsg(err)); } finally { setBusyKey(null); }
  };
  const upload = (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;
    void act("upload", async () => { const d = await api.aiUpload(file, title, note, consent); setFile(null); setFileKey((k) => k + 1); setTitle(""); setNote(""); setConsent(false); load(); return d.relevance_reason ?? "Đã tải lên và trích chữ."; });
  };
  const paste = () => act("paste", async () => { const d = await api.aiPasteText(pasted, title, note, consent); setPasted(""); setTitle(""); setNote(""); setConsent(false); load(); return d.relevance_reason ?? "Đã nhận chữ."; });
  const review = (d: AiDocument, decision: "approve" | "reject") => act(`review:${d.id}`, async () => {
    await api.aiReviewDocument(d.id, decision); load();
    return decision === "approve" ? "Đã duyệt: tài liệu dùng được để soạn bài." : "Đã từ chối và xóa chữ đã lưu.";
  });
  const upsertJob = (job: AiJob) => setJobs((rows) => [job, ...rows.filter((j) => j.document_id !== job.document_id)]);
  const summarize = (d: AiDocument) => act(`doc:${d.id}`, async () => { upsertJob(await api.aiSummarize(d.id)); });
  const resume = (job: AiJob) => act(`job:${job.id}`, async () => { upsertJob(await api.aiResumeJob(job.id)); });
  const cancel = (job: AiJob) => act(`job:${job.id}`, async () => {
    if (!window.confirm("Dừng hẳn việc tóm tắt này? Các bản nháp đã soạn vẫn giữ lại.")) return;
    upsertJob(await api.aiCancelJob(job.id));
  });
  const pending = docs.filter((d) => d.relevance_status === "pending");
  const ready = docs.filter((d) => d.relevance_status === "accepted");
  const jobOf = new Map(jobs.map((j) => [j.document_id, j]));

  if (openId) return <DraftEditor draftId={openId} onClose={() => { setOpenId(null); load(); }} />;
  if (enabled === null) return <p className="text-muted">Đang tải…</p>;

  return <div className="grid gap-4">
    {ai && <Card className="flex flex-wrap items-center justify-between gap-2 p-3">
      <p className="text-sm"><span className="font-semibold">Công tắc AI: {ai.switch_on ? "Đang bật" : "Đang tắt"}</span>
        {!ai.env_ready && <span className="text-muted"> · máy chủ chưa có <code>AI_ENABLED=true</code> hoặc khóa Gemini trong .env, bật công tắc cũng chưa có AI</span>}</p>
      <Button variant="secondary" loading={busyKey === "switch"} onClick={flipSwitch}>{ai.switch_on ? "Tắt AI" : "Bật AI"}</Button>
    </Card>}
    {!enabled && <p role="status" className="rounded-lg border border-line p-3 text-sm">Tính năng AI đang tắt ({ai && !ai.switch_on ? "Quản trị viên đã tắt công tắc" : <>chưa bật <code>AI_ENABLED</code> hoặc chưa có khóa Gemini</>}). Bạn vẫn xem được các bản nháp cũ.</p>}
    <Card className="p-4">
      <CardTitle>Tải tài liệu nhạc lý</CardTitle>
      <form onSubmit={upload} className="mt-2 grid gap-2">
        <input key={fileKey} type="file" accept=".pdf,.docx,.md,.txt,.png,.jpg,.jpeg,.webp,.xml,.musicxml,.mxl,.mid,.midi" aria-label="Tệp tài liệu" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Nguồn: tên sách, tác giả, năm (bắt buộc)" aria-label="Nguồn tài liệu" className="min-h-10 rounded-lg border border-line bg-surface px-3" />
        <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Ghi chú nguồn (không bắt buộc)" aria-label="Ghi chú nguồn" className="min-h-10 rounded-lg border border-line bg-surface px-3" />
        <label className="flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
          Tôi có quyền dùng tài liệu này, và hiểu rằng nội dung tài liệu sẽ được gửi tới Gemini (Google) để tóm tắt.</label>
        <p className="text-xs text-muted">PDF (kể cả ảnh quét), DOCX, ảnh (OCR), MusicXML, MIDI, MD, TXT; tối đa 10 MB. Hệ thống chấm điểm liên quan nhạc lý: tài liệu lạc đề bị từ chối, tài liệu chưa chắc vào hàng chờ duyệt.</p>
        <Button type="submit" loading={busyKey === "upload"} disabled={busyKey !== null || !file || !consent || !title.trim()}>Tải lên</Button>
      </form>
      <details className="mt-3"><summary className="cursor-pointer text-sm font-semibold">Hoặc dán chữ trực tiếp</summary>
        <textarea rows={5} value={pasted} onChange={(e) => setPasted(e.target.value)} aria-label="Chữ dán vào" placeholder="Dán đoạn lý thuyết nhạc lý vào đây (dùng chung nguồn và ô xác nhận ở trên)" className="mt-2 w-full rounded-lg border border-line bg-surface p-2" />
        <Button variant="secondary" loading={busyKey === "paste"} disabled={busyKey !== null || !pasted.trim() || !consent || !title.trim()} onClick={paste}>Kiểm tra và nhận chữ</Button>
      </details>
      {/* AUD-06: thông báo ngay dưới khung tải lên; trước đây ở cuối trang dài, bấm xong không thấy kết quả. */}
      {msg && <p role="status" className="mt-3 rounded-lg bg-primary-soft p-2 text-sm">{msg}</p>}
    </Card>

    {pending.length > 0 && <Card className="p-4"><CardTitle>Chờ duyệt nội dung nhạc lý ({pending.length})</CardTitle>
      <p className="mt-1 text-sm text-muted">Hệ thống chưa chắc các tài liệu này nói về nhạc lý. Xem lý do rồi duyệt hoặc từ chối; tài liệu chưa duyệt chưa dùng để soạn bài được.</p>
      <ul className="mt-2 grid gap-3">{pending.map((d) => <li key={d.id} className="rounded-lg border border-line p-3">
        <p className="font-semibold">{d.filename} <span className="text-sm font-normal text-muted">· {d.source_title} · điểm {Math.round((d.relevance_score ?? 0) * 100)}/100</span></p>
        <p className="mt-1 text-sm">{d.relevance_reason}</p>
        <div className="mt-2 flex flex-wrap gap-2"><Button loading={busyKey === `review:${d.id}`} disabled={busyKey === `review:${d.id}`} onClick={() => review(d, "approve")}>Duyệt, dùng được</Button>
          <Button variant="ghost" disabled={busyKey === `review:${d.id}`} onClick={() => review(d, "reject")}>Từ chối</Button></div></li>)}</ul></Card>}

    {ready.length > 0 && <Card className="p-4"><CardTitle>Tài liệu đã tải</CardTitle>
      <p className="mt-1 text-sm text-muted">AI tóm tắt toàn bộ tài liệu: tự chia theo chương, bỏ bìa, mục lục, tài liệu tham khảo; mỗi chương thành một bản nháp bài học kèm luyện tập.
        Kiến thức trang web đã dạy thì không soạn lại. Việc chạy nền, bạn có thể làm việc khác rồi quay lại.</p>
      <ul className="mt-2 grid gap-3">
      {ready.map((d) => { const job = jobOf.get(d.id); const active = job && (job.status === "running" || job.status === "paused");
        return <li key={d.id} className="rounded-lg border border-line p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-semibold">{d.filename} <span className="text-sm font-normal text-muted">· {d.page_count} trang/đoạn · {d.source_title}</span></p>
            {!active && <Button loading={busyKey === `doc:${d.id}`} disabled={!enabled || busyKey === `doc:${d.id}`} onClick={() => summarize(d)}>
              {job ? "AI soạn lại từ cả tài liệu" : "AI soạn bài từ cả tài liệu"}</Button>}
          </div>
          {job && <JobPanel job={job} busy={busyKey === `job:${job.id}`} onResume={() => resume(job)} onCancel={() => cancel(job)} onOpen={setOpenId} />}
        </li>; })}
    </ul></Card>}

    <Card className="p-4"><CardTitle>Bản nháp</CardTitle>
      {drafts.length === 0 ? <p className="mt-2 text-sm text-muted">Chưa có bản nháp nào.</p> : <ul className="mt-2 grid gap-2">
        {drafts.map((d) => <li key={d.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line p-2">
          <span>{d.title} <span className="text-sm text-muted">· {d.questions} câu{d.flags ? ` · ${d.flags} cờ Engine` : ""}{d.review_flags ? ` · ${d.review_flags} cờ chưa đối chiếu` : ""}</span>{" "}
            <Badge tone={d.status === "published" ? "success" : d.status === "rejected" ? "muted" : "warning"}>{d.status === "published" ? (d.lesson_hidden ? "Đã xuất bản · đang ẩn" : "Đã xuất bản · học sinh thấy") : d.status === "rejected" ? "Từ chối" : "Nháp"}</Badge></span>
          <Button variant="secondary" onClick={() => setOpenId(d.id)}>Mở</Button></li>)}
      </ul>}
    </Card>
  </div>;
}

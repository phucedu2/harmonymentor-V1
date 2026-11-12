import { useEffect, useState, type FormEvent } from "react";
import { api, type AiDocument, type AiDraft, type AiDraftRow, type AiQuestion } from "../../api";
import { Button } from "../ui/Button";
import { Badge, Card, CardTitle } from "../ui/Page";

const errMsg = (e: unknown) => (e as { message?: string }).message ?? "Có lỗi xảy ra, thử lại sau.";
const KIND: Record<AiQuestion["kind"], string> = { mcq: "Trắc nghiệm", build_chord: "Dựng hợp âm", build_scale: "Dựng âm giai" };

// AI chỉ soạn BẢN NHÁP (ADR-025). Bài chỉ tới học sinh khi Quản trị viên bấm xuất bản ở đây.
function DraftEditor({ draftId, onClose }: { draftId: string; onClose: () => void }) {
  const [draft, setDraft] = useState<AiDraft | null>(null);
  const [ack, setAck] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const load = () => api.aiDraft(draftId).then(setDraft).catch((e) => setMsg(errMsg(e)));
  useEffect(() => { load(); }, [draftId]);
  if (!draft) return <p className="text-muted">{msg ?? "Đang tải…"}</p>;
  const c = draft.content;
  const open = draft.status === "draft";
  const flags = draft.engine.contradicted.length;
  const set = (patch: Partial<typeof c>) => setDraft({ ...draft, content: { ...c, ...patch } });
  const run = async (fn: () => Promise<void>) => { setBusy(true); setMsg(null); try { await fn(); } catch (e) { setMsg(errMsg(e)); } finally { setBusy(false); } };
  const save = () => run(async () => { setDraft(await api.aiSaveDraft(draft.id, { title: c.title, objectives: c.objectives, blocks: c.blocks, questions: c.questions })); setAck(false); setMsg("Đã lưu và soát lại bằng Music Engine."); });
  const publish = () => run(async () => { const r = await api.aiPublish(draft.id, ack); setMsg(`Đã xuất bản bài “${r.title}”. Học sinh thấy ngay.`); await load(); });
  const reject = () => run(async () => { if (!window.confirm("Từ chối bản nháp này?")) return; await api.aiReject(draft.id); await load(); });

  return <div className="grid gap-3">
    <div className="flex flex-wrap items-center gap-2">
      <Button variant="ghost" onClick={onClose}>← Danh sách</Button>
      <Badge tone={draft.status === "published" ? "success" : draft.status === "rejected" ? "muted" : "warning"}>
        {draft.status === "published" ? "Đã xuất bản" : draft.status === "rejected" ? "Đã từ chối" : "Bản nháp"}</Badge>
      <span className="text-sm text-muted">Nguồn: {draft.document?.source_title}, trang {draft.page_from}–{draft.page_to} · AI: {draft.model}</span>
    </div>
    <p className="rounded-lg bg-primary-soft p-2 text-sm">AI chỉ tóm tắt và gợi ý. Hãy đọc đối chiếu với tài liệu gốc trước khi xuất bản. Đáp án câu dựng hợp âm/âm giai do Music Engine tính, không phải AI.</p>

    <div className={`rounded-lg border p-3 text-sm ${flags ? "border-danger" : "border-line"}`} role={flags ? "alert" : "status"}>
      {draft.engine.checked === 0 ? "Music Engine: không có khẳng định nốt/hợp âm nào để soát."
        : flags === 0 ? `Music Engine đã soát ${draft.engine.checked} khẳng định: không thấy chỗ sai.`
        : <><p className="font-semibold text-danger">Music Engine thấy {flags} chỗ có thể sai:</p>
            <ul className="mt-1 list-disc pl-5">{draft.engine.contradicted.map((f, i) => <li key={i}>({(f as { where?: string }).where}) viết “{f.claimed}”, Engine tính “{f.engine}”</li>)}</ul></>}
    </div>

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
      <p className="text-xs text-muted">Lấy từ trang {b.page}</p>
      {open && <Button variant="ghost" onClick={() => set({ blocks: c.blocks.filter((_, j) => j !== i) })}>Xóa khối này</Button>}
    </Card>)}

    <h3 className="font-semibold">Câu hỏi gợi ý ({c.questions.length})</h3>
    {c.questions.map((q, i) => <Card key={i} className="grid gap-2 p-3">
      <p className="text-xs text-muted"><Badge tone="muted">{KIND[q.kind]}</Badge> kỹ năng {q.skill_id} · trang {q.page}</p>
      <textarea aria-label={`Đề câu ${i + 1}`} rows={2} value={q.prompt} disabled={!open} className="rounded border border-line bg-surface p-2"
        onChange={(e) => set({ questions: c.questions.map((x, j) => (j === i ? { ...x, prompt: e.target.value } : x)) })} />
      {q.kind === "mcq" && <p className="text-sm">Phương án: {q.options?.map((o) => o === q.answer ? `✔ ${o}` : o).join(" · ")}</p>}
      {q.kind !== "mcq" && <p className="text-sm">Đáp án do Music Engine tính: <b>{q.engine_answer?.join(" ") ?? "—"}</b> ({q.symbol ?? `${q.tonic} ${q.scale_type}`})</p>}
      <textarea aria-label={`Lời giải câu ${i + 1}`} rows={2} value={q.explanation} disabled={!open} placeholder="Lời giải" className="rounded border border-line bg-surface p-2 text-sm"
        onChange={(e) => set({ questions: c.questions.map((x, j) => (j === i ? { ...x, explanation: e.target.value } : x)) })} />
      {open && <Button variant="ghost" onClick={() => set({ questions: c.questions.filter((_, j) => j !== i) })}>Xóa câu này</Button>}
    </Card>)}
    {c.dropped_questions.length > 0 && <details className="text-sm text-muted"><summary>{c.dropped_questions.length} câu AI gợi ý đã bị loại tự động</summary>
      <ul className="list-disc pl-5">{c.dropped_questions.map((d, i) => <li key={i}>{d}</li>)}</ul></details>}

    {open && <div className="grid gap-2 rounded-lg border border-line p-3">
      <div className="flex flex-wrap gap-2">
        <Button variant="secondary" loading={busy} onClick={save}>Lưu và soát lại</Button>
        <Button variant="ghost" onClick={reject}>Từ chối bản nháp</Button>
      </div>
      {flags > 0 && <label className="flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={ack} onChange={(e) => setAck(e.target.checked)} />
        Tôi đã đối chiếu tài liệu gốc và vẫn muốn xuất bản dù Engine báo nghi sai.</label>}
      <Button loading={busy} disabled={flags > 0 && !ack} onClick={publish}>Xuất bản thành bài học</Button>
      <p className="text-xs text-muted">Lưu các sửa đổi trước khi xuất bản. Bài mới hiện ở cuối danh sách bài học.</p>
    </div>}
    {msg && <p role="status" className="text-sm">{msg}</p>}
  </div>;
}

export default function AiDraftTab() {
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [docs, setDocs] = useState<AiDocument[]>([]);
  const [drafts, setDrafts] = useState<AiDraftRow[]>([]);
  const [openId, setOpenId] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [note, setNote] = useState("");
  const [consent, setConsent] = useState(false);
  const [range, setRange] = useState<Record<string, { from: string; to: string; topic: string }>>({});
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const load = () => { api.aiDocuments().then(setDocs).catch(() => undefined); api.aiDrafts().then(setDrafts).catch(() => undefined); };
  useEffect(() => { api.aiStatus().then((s) => setEnabled(s.enabled)).catch(() => setEnabled(false)); load(); }, []);

  const upload = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setBusy(true); setMsg(null);
    try { await api.aiUpload(file, title, note, consent); setFile(null); setTitle(""); setNote(""); setConsent(false); load(); setMsg("Đã tải lên và trích chữ."); }
    catch (err) { setMsg(errMsg(err)); } finally { setBusy(false); }
  };
  const make = async (d: AiDocument) => {
    const r = range[d.id] ?? { from: "1", to: String(Math.min(d.page_count, 5)), topic: "" };
    setBusy(true); setMsg("AI đang soạn bản nháp, có thể mất đến một phút…");
    try { const draft = await api.aiMakeDraft(d.id, Number(r.from), Number(r.to), r.topic); load(); setOpenId(draft.id); setMsg(null); }
    catch (err) { setMsg(errMsg(err)); } finally { setBusy(false); }
  };

  if (openId) return <DraftEditor draftId={openId} onClose={() => { setOpenId(null); load(); }} />;
  if (enabled === null) return <p className="text-muted">Đang tải…</p>;

  return <div className="grid gap-4">
    {!enabled && <p role="status" className="rounded-lg border border-line p-3 text-sm">Tính năng AI đang tắt (chưa bật <code>AI_ENABLED</code> hoặc chưa có khóa Gemini). Bạn vẫn xem được các bản nháp cũ.</p>}
    <Card className="p-4">
      <CardTitle>Tải tài liệu nhạc lý</CardTitle>
      <form onSubmit={upload} className="mt-2 grid gap-2">
        <input type="file" accept=".pdf,.docx,.md,.txt" aria-label="Tệp tài liệu" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Nguồn: tên sách, tác giả, năm (bắt buộc)" aria-label="Nguồn tài liệu" className="min-h-10 rounded-lg border border-line bg-surface px-3" />
        <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Ghi chú nguồn (không bắt buộc)" aria-label="Ghi chú nguồn" className="min-h-10 rounded-lg border border-line bg-surface px-3" />
        <label className="flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
          Tôi có quyền dùng tài liệu này, và hiểu rằng nội dung các trang đã chọn sẽ được gửi tới Gemini (Google) để tóm tắt.</label>
        <p className="text-xs text-muted">PDF, DOCX, MD, TXT, tối đa 10 MB. PDF ảnh quét (không có chữ) chưa đọc được.</p>
        <Button type="submit" loading={busy} disabled={!file || !consent || !title.trim()}>Tải lên</Button>
      </form>
    </Card>

    {docs.length > 0 && <Card className="p-4"><CardTitle>Tài liệu đã tải</CardTitle><ul className="mt-2 grid gap-3">
      {docs.map((d) => { const r = range[d.id] ?? { from: "1", to: String(Math.min(d.page_count, 5)), topic: "" };
        const upd = (patch: Partial<typeof r>) => setRange({ ...range, [d.id]: { ...r, ...patch } });
        return <li key={d.id} className="rounded-lg border border-line p-3">
          <p className="font-semibold">{d.filename} <span className="text-sm font-normal text-muted">· {d.page_count} trang/đoạn · {d.source_title}</span></p>
          <div className="mt-2 flex flex-wrap items-end gap-2 text-sm">
            <label>Từ trang <input type="number" min={1} max={d.page_count} value={r.from} onChange={(e) => upd({ from: e.target.value })} className="ml-1 w-20 rounded border border-line bg-surface px-2 py-1" /></label>
            <label>đến <input type="number" min={1} max={d.page_count} value={r.to} onChange={(e) => upd({ to: e.target.value })} className="ml-1 w-20 rounded border border-line bg-surface px-2 py-1" /></label>
            <input value={r.topic} onChange={(e) => upd({ topic: e.target.value })} placeholder="Chủ đề (không bắt buộc)" aria-label="Chủ đề" className="min-h-9 flex-1 rounded border border-line bg-surface px-2" />
            <Button loading={busy} disabled={!enabled} onClick={() => make(d)}>AI soạn bản nháp</Button>
          </div></li>; })}
    </ul></Card>}

    <Card className="p-4"><CardTitle>Bản nháp</CardTitle>
      {drafts.length === 0 ? <p className="mt-2 text-sm text-muted">Chưa có bản nháp nào.</p> : <ul className="mt-2 grid gap-2">
        {drafts.map((d) => <li key={d.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line p-2">
          <span>{d.title} <span className="text-sm text-muted">· {d.questions} câu{d.flags ? ` · ${d.flags} cờ Engine` : ""}</span>{" "}
            <Badge tone={d.status === "published" ? "success" : d.status === "rejected" ? "muted" : "warning"}>{d.status === "published" ? "Đã xuất bản" : d.status === "rejected" ? "Từ chối" : "Nháp"}</Badge></span>
          <Button variant="secondary" onClick={() => setOpenId(d.id)}>Mở</Button></li>)}
      </ul>}
    </Card>
    {msg && <p role="status" className="text-sm">{msg}</p>}
  </div>;
}

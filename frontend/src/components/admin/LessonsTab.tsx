import { useEffect, useState } from "react";
import { api, type AdminBlock, type AdminLessonDetail, type AdminLessonRow, type AdminRevision } from "../../api";
import { Button } from "../ui/Button";
import { Badge, Card } from "../ui/Page";

// Trường chữ sửa được: khớp danh sách ở backend (content_service). Trường khác (loại khối, mã bài tập, hợp âm…) bị khóa.
const TEXT_KEYS = ["title", "prompt", "note", "intro", "kicker"];
const LIST_KEYS = ["paragraphs", "items"];
const TERM_FIELDS = ["symbol", "term", "definition", "example"] as const;
type Payload = Record<string, unknown>;
type Term = Partial<Record<(typeof TERM_FIELDS)[number], string>>;
const errMsg = (e: unknown) => (e as { message?: string }).message ?? "Có lỗi xảy ra, thử lại sau.";

function EngineBox({ report }: { report: AdminBlock["engine"] }) {
  if (!report.checked) return <p className="text-xs text-muted">Music Engine: không có khẳng định nốt/hợp âm nào để soát.</p>;
  if (!report.contradicted.length) return <p className="text-xs text-success">Music Engine đã soát {report.checked} khẳng định: không thấy chỗ sai ({report.verified} khớp, {report.unsupported} chưa kiểm được).</p>;
  return <div role="alert" className="rounded-lg border border-danger p-2 text-sm">
    <p className="font-semibold text-danger">Music Engine thấy {report.contradicted.length} chỗ có thể sai:</p>
    <ul className="mt-1 list-disc pl-5">{report.contradicted.map((c, i) => <li key={i}>Bài viết ghi “{c.claimed}”, Engine tính “{c.engine}” ({JSON.stringify(c.args)})</li>)}</ul>
  </div>;
}

function Field({ k, value, onChange }: { k: string; value: unknown; onChange: (v: unknown) => void }) {
  const id = `f-${k}`;
  if (typeof value === "string" && TEXT_KEYS.includes(k)) {
    return <div><label htmlFor={id} className="text-sm font-semibold">{k}</label>
      <textarea id={id} rows={value.length > 90 ? 3 : 1} value={value} onChange={(e) => onChange(e.target.value)} className="mt-1 w-full rounded-lg border border-line bg-surface p-2" /></div>;
  }
  if (Array.isArray(value) && LIST_KEYS.includes(k) && value.every((x) => typeof x === "string")) {
    return <div><label htmlFor={id} className="text-sm font-semibold">{k} (mỗi dòng một mục)</label>
      <textarea id={id} rows={Math.min(10, value.length + 1)} value={(value as string[]).join("\n")} onChange={(e) => onChange(e.target.value.split("\n").filter((l) => l.trim() !== ""))}
        className="mt-1 w-full rounded-lg border border-line bg-surface p-2" /></div>;
  }
  if (k === "terms" && Array.isArray(value)) {
    return <fieldset className="grid gap-2"><legend className="text-sm font-semibold">Thuật ngữ</legend>
      {(value as Term[]).map((t, i) => <div key={i} className="grid gap-1 rounded-lg border border-line p-2 sm:grid-cols-2">
        {TERM_FIELDS.filter((f) => f in t).map((f) => <label key={f} className="text-xs">{f}
          <input value={t[f] ?? ""} onChange={(e) => onChange((value as Term[]).map((x, j) => (j === i ? { ...x, [f]: e.target.value } : x)))}
            className="mt-0.5 min-h-9 w-full rounded border border-line bg-surface px-2 text-sm" /></label>)}
      </div>)}</fieldset>;
  }
  return <p className="text-xs text-muted">Trường “{k}” bị khóa (không sửa ở đây).</p>;
}

function BlockEditor({ lessonId, block, onChanged }: { lessonId: string; block: AdminBlock; onChanged: () => void }) {
  const [open, setOpen] = useState(false);
  const [payload, setPayload] = useState<Payload>(block.payload);
  const [note, setNote] = useState("");
  const [rev, setRev] = useState<{ id: string; engine: AdminBlock["engine"] } | null>(null);
  const [ack, setAck] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [history, setHistory] = useState<AdminRevision[] | null>(null);
  const [preview, setPreview] = useState(false);
  const flags = rev?.engine.contradicted.length ?? 0;
  const run = async (fn: () => Promise<void>) => { setBusy(true); setMsg(null); try { await fn(); } catch (e) { setMsg(errMsg(e)); } finally { setBusy(false); } };

  const save = () => run(async () => { const r = await api.adminSaveDraft(lessonId, block.id, payload, note); setRev({ id: r.revision_id, engine: r.engine }); setAck(false); setMsg("Đã lưu bản nháp. Học sinh chưa thấy thay đổi."); });
  const publish = () => run(async () => { await api.adminPublish(rev!.id, ack); setRev(null); setMsg("Đã xuất bản. Học sinh thấy ngay nội dung mới."); onChanged(); });
  const loadHistory = () => run(async () => setHistory(await api.adminHistory(lessonId, block.id)));
  const restore = (id: string | null) => run(async () => {
    if (!window.confirm(id ? "Khôi phục bản này và xuất bản ngay?" : "Quay về nội dung gốc của hệ thống?")) return;
    await api.adminRestore(lessonId, block.id, id); setMsg("Đã khôi phục."); setHistory(null); onChanged();
  });

  return <li className="rounded-lg border border-line p-3">
    <button type="button" className="flex w-full flex-wrap items-center gap-2 text-left" aria-expanded={open} onClick={() => setOpen(!open)}>
      <span className="font-semibold">#{block.position} · {block.block_type}</span>
      {block.edited && <Badge tone="warning">Đã sửa</Badge>}{block.draft_revision_id && <Badge tone="muted">Có bản nháp</Badge>}
      {block.engine.contradicted.length > 0 && <Badge tone="warning">Engine nghi sai</Badge>}
      <span className="truncate text-sm text-muted">{String(block.payload.title ?? block.payload.prompt ?? "")}</span>
    </button>
    {open && <div className="mt-3 grid gap-3">
      {Object.entries(payload).map(([k, v]) => <Field key={k} k={k} value={v} onChange={(nv) => setPayload({ ...payload, [k]: nv })} />)}
      <div><label htmlFor={`note-${block.id}`} className="text-sm font-semibold">Ghi chú thay đổi (không bắt buộc)</label>
        <input id={`note-${block.id}`} value={note} maxLength={500} onChange={(e) => setNote(e.target.value)} className="mt-1 min-h-10 w-full rounded-lg border border-line bg-surface px-3" /></div>
      <div className="flex flex-wrap gap-2">
        <Button variant="secondary" loading={busy} onClick={save}>Lưu bản nháp</Button>
        <Button variant="ghost" onClick={() => setPreview(!preview)}>{preview ? "Ẩn xem trước" : "Xem trước"}</Button>
        <Button variant="ghost" onClick={loadHistory}>Lịch sử</Button>
        {block.edited && <Button variant="ghost" onClick={() => restore(null)}>Về bản gốc</Button>}
      </div>
      {preview && <div className="rounded-lg bg-primary-soft p-3" aria-label="Xem trước">
        {typeof payload.title === "string" && <h4 className="font-bold">{payload.title}</h4>}
        {Array.isArray(payload.paragraphs) && (payload.paragraphs as string[]).map((p, i) => <p key={i} className="mt-1">{p}</p>)}
        {Array.isArray(payload.items) && <ul className="mt-1 list-disc pl-5">{(payload.items as string[]).map((p, i) => <li key={i}>{p}</li>)}</ul>}
        {typeof payload.note === "string" && <p className="mt-1 text-sm">{payload.note}</p>}
      </div>}
      {rev && <div className="grid gap-2 rounded-lg border border-line p-3">
        <EngineBox report={rev.engine} />
        {flags > 0 && <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} className="mt-1" />
          Tôi đã đối chiếu và vẫn muốn xuất bản dù Engine báo nghi sai.</label>}
        <Button loading={busy} disabled={flags > 0 && !ack} onClick={publish}>Xuất bản cho học sinh</Button>
      </div>}
      {msg && <p role="status" className="text-sm">{msg}</p>}
      {history && <ul className="grid gap-1 text-sm">{history.length === 0 ? <li className="text-muted">Chưa có phiên bản nào.</li> : history.map((h) => <li key={h.id} className="flex flex-wrap items-center gap-2">
        <Badge tone={h.status === "published" ? "success" : "muted"}>{h.status === "published" ? "Đã xuất bản" : h.status === "draft" ? "Nháp" : h.status}</Badge>
        <span>{h.created_at.slice(0, 16).replace("T", " ")}{h.note ? ` · ${h.note}` : ""}</span>
        <Button variant="ghost" onClick={() => restore(h.id)}>Khôi phục</Button></li>)}</ul>}
    </div>}
  </li>;
}

function LessonEditor({ id, onBack, onChanged }: { id: string; onBack: () => void; onChanged: () => void }) {
  const [detail, setDetail] = useState<AdminLessonDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = () => api.adminLesson(id).then(setDetail).catch(() => setError("Chưa tải được bài."));
  useEffect(() => { load(); }, [id]);
  const toggleHidden = async () => {
    if (!detail) return;
    try { await api.adminVisibility(id, !detail.lesson.hidden); await load(); onChanged(); } catch (e) { setError(errMsg(e)); }
  };
  if (error) return <p role="alert" className="text-danger">{error}</p>;
  if (!detail) return <p className="text-muted">Đang tải…</p>;
  return <div className="grid gap-3">
    <div className="flex flex-wrap items-center gap-2">
      <Button variant="ghost" onClick={onBack}>← Danh sách bài</Button>
      <h2 className="text-lg font-bold">Bài {detail.lesson.order}. {detail.lesson.title}</h2>
      {detail.lesson.hidden && <Badge tone="warning">Đang ẩn</Badge>}
      <Button variant="secondary" className="ml-auto" onClick={toggleHidden}>{detail.lesson.hidden ? "Hiện lại cho học sinh" : "Ẩn khỏi học sinh"}</Button>
    </div>
    <p className="text-sm text-muted">Chỉ sửa được chữ của khối lý thuyết. Câu hỏi ({detail.exercises.length}) không sửa ở đây để giữ nguyên đáp án và lịch sử chấm (ADR-006).</p>
    <ul className="grid gap-2">{detail.blocks.map((b) => <BlockEditor key={`${b.id}-${b.edited}`} lessonId={id} block={b} onChanged={() => { load(); onChanged(); }} />)}</ul>
  </div>;
}

export default function LessonsTab() {
  const [rows, setRows] = useState<AdminLessonRow[] | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const load = () => api.adminLessons().then(setRows).catch(() => setFailed(true));
  useEffect(() => { load(); }, []);
  if (openId) return <LessonEditor id={openId} onBack={() => setOpenId(null)} onChanged={load} />;
  if (failed) return <p role="alert" className="text-danger">Chưa tải được danh sách bài.</p>;
  if (!rows) return <p className="text-muted">Đang tải…</p>;
  return <ul className="grid gap-2">{rows.map((l) => <li key={l.id}><Card className="flex flex-wrap items-center justify-between gap-2 p-3">
    <div><p className="font-semibold">Bài {l.order}. {l.title} {l.hidden && <Badge tone="warning">Ẩn</Badge>}</p>
      <p className="text-sm text-muted">{l.block_count} khối · {l.exercise_count} câu hỏi · {l.edited_blocks} khối đã sửa · {l.draft_blocks} bản nháp</p></div>
    <Button variant="secondary" onClick={() => setOpenId(l.id)}>Sửa nội dung</Button></Card></li>)}</ul>;
}

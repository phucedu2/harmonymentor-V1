import { useEffect, useRef, useState, type ReactNode } from "react";
import { api, type AdminBlock, type AdminImportRow, type AdminLessonDetail, type AdminLessonRow, type AdminRevision } from "../../api";
import { Button } from "../ui/Button";
import { Badge, Card } from "../ui/Page";
import CardsPanel from "./CardsPanel";
import ExercisesPanel from "./ExercisesPanel";

// Trường chữ sửa được: khớp danh sách ở backend (content_service). Trường khác (loại khối, mã bài tập, hợp âm…) bị khóa.
const TEXT_KEYS = ["title", "prompt", "note", "intro", "kicker"];
const LIST_KEYS = ["paragraphs", "items"];
const TERM_FIELDS = ["symbol", "term", "definition", "example"] as const;
type Payload = Record<string, unknown>;
type Term = Partial<Record<(typeof TERM_FIELDS)[number], string>>;
// FE-025: tên trường và loại khối hiện bằng tiếng Việt (trước hiện mã code "prompt", "callout"…); mã vẫn giữ trong ngoặc
// để đối chiếu với nội dung YAML khi cần.
const FIELD_VI: Record<string, string> = { title: "Tiêu đề", prompt: "Đề bài", note: "Ghi chú", intro: "Mở đầu", kicker: "Dòng nhỏ phía trên tiêu đề",
  paragraphs: "Các đoạn văn", items: "Các ý", symbol: "Ký hiệu", term: "Thuật ngữ", definition: "Định nghĩa", example: "Ví dụ" };
const BLOCK_VI: Record<string, string> = { theory: "Lý thuyết", callout: "Ô lưu ý", piano: "Đàn piano", glossary: "Thuật ngữ", summary: "Tóm tắt",
  audio: "Nghe ví dụ", checkpoint: "Câu hỏi kiểm tra", compose_link: "Liên kết Sáng tác", interactive: "Tương tác", notation: "Khuông nhạc",
  progression: "Vòng hợp âm", key_overview: "Tổng quan giọng", interval_explorer: "Khám phá quãng", triad_explorer: "Khám phá hợp âm ba",
  triad_audio_explorer: "Nghe hợp âm ba", triad_notation_explorer: "Hợp âm ba trên khuông" };
const fieldName = (k: string) => FIELD_VI[k] ?? k;
const errMsg = (e: unknown) => (e as { message?: string }).message ?? "Có lỗi xảy ra, thử lại sau.";

function EngineBox({ report }: { report: AdminBlock["engine"] }) {
  if (!report.checked) return <p className="text-xs text-muted">Music Engine: không có khẳng định nốt/hợp âm nào để soát.</p>;
  if (!report.contradicted.length) return <p className="text-xs text-success">Music Engine đã soát {report.checked} khẳng định: không thấy chỗ sai ({report.verified} khớp, {report.unsupported} chưa kiểm được).</p>;
  return <div role="alert" className="rounded-lg border border-danger p-2 text-sm">
    <p className="font-semibold text-danger">Music Engine thấy {report.contradicted.length} chỗ có thể sai:</p>
    <ul className="mt-1 list-disc pl-5">{report.contradicted.map((c, i) => <li key={i}>Bài viết ghi “{c.claimed}”, Engine tính “{c.engine}” ({JSON.stringify(c.args)})</li>)}</ul>
  </div>;
}

// idPrefix theo khối: mở hai khối cùng lúc trước đây sinh hai id "f-title" trùng nhau, nhãn trỏ nhầm ô.
function Field({ k, value, onChange, idPrefix }: { k: string; value: unknown; onChange: (v: unknown) => void; idPrefix: string }) {
  const id = `${idPrefix}-${k}`;
  if (typeof value === "string" && TEXT_KEYS.includes(k)) {
    return <div><label htmlFor={id} className="text-sm font-semibold">{fieldName(k)}</label>
      <textarea id={id} rows={value.length > 90 ? 3 : 1} value={value} onChange={(e) => onChange(e.target.value)} className="mt-1 w-full rounded-lg border border-line bg-surface p-2" /></div>;
  }
  if (Array.isArray(value) && LIST_KEYS.includes(k) && value.every((x) => typeof x === "string")) {
    return <div><label htmlFor={id} className="text-sm font-semibold">{fieldName(k)} (mỗi dòng một mục)</label>
      <textarea id={id} rows={Math.min(10, value.length + 1)} value={(value as string[]).join("\n")} onChange={(e) => onChange(e.target.value.split("\n").filter((l) => l.trim() !== ""))}
        className="mt-1 w-full rounded-lg border border-line bg-surface p-2" /></div>;
  }
  if (k === "terms" && Array.isArray(value)) {
    return <fieldset className="grid gap-2"><legend className="text-sm font-semibold">Thuật ngữ</legend>
      {(value as Term[]).map((t, i) => <div key={i} className="grid gap-1 rounded-lg border border-line p-2 sm:grid-cols-2">
        {TERM_FIELDS.filter((f) => f in t).map((f) => <label key={f} className="text-xs">{fieldName(f)}
          <input value={t[f] ?? ""} onChange={(e) => onChange((value as Term[]).map((x, j) => (j === i ? { ...x, [f]: e.target.value } : x)))}
            className="mt-0.5 min-h-9 w-full rounded border border-line bg-surface px-2 text-sm" /></label>)}
      </div>)}</fieldset>;
  }
  return <p className="text-xs text-muted">Trường “{fieldName(k)}” bị khóa (không sửa ở đây).</p>;
}

function BlockEditor({ lessonId, block, onChanged, controls }: { lessonId: string; block: AdminBlock; onChanged: () => void; controls?: ReactNode }) {
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
      <span className="font-semibold">#{block.position} · {BLOCK_VI[block.block_type] ?? block.block_type}</span>
      {block.edited && <Badge tone="warning">Đã sửa</Badge>}{block.draft_revision_id && <Badge tone="muted">Có bản nháp</Badge>}
      {block.engine.contradicted.length > 0 && <Badge tone="warning">Engine nghi sai</Badge>}
      <span className="truncate text-sm text-muted">{String(block.payload.title ?? block.payload.prompt ?? "")}</span>
    </button>
    {controls && <div className="mt-2 flex flex-wrap gap-1">{controls}</div>}
    {open && <div className="mt-3 grid gap-3">
      {Object.entries(payload).map(([k, v]) => <Field key={k} k={k} idPrefix={`f-${block.id}`} value={v} onChange={(nv) => setPayload({ ...payload, [k]: nv })} />)}
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
  const headingRef = useRef<HTMLHeadingElement>(null);
  const load = () => api.adminLesson(id).then(setDetail).catch(() => setError("Chưa tải được bài."));
  useEffect(() => { load(); }, [id]);
  // Nút "Sửa nội dung" vừa bấm đã biến mất: đưa focus tới tiêu đề bài để bàn phím/trình đọc màn hình không rơi về đầu trang.
  const loaded = detail !== null;
  useEffect(() => { if (loaded) headingRef.current?.focus(); }, [loaded]);
  const toggleHidden = async () => {
    if (!detail) return;
    try { await api.adminVisibility(id, !detail.lesson.hidden); await load(); onChanged(); } catch (e) { setError(errMsg(e)); }
  };
  const remove = async () => {
    if (!detail || !window.confirm(`Xóa bài “${detail.lesson.title}”? Học sinh sẽ không thấy bài này nữa.`)) return;
    try { await api.adminDeleteLesson(id); onChanged(); onBack(); } catch (e) { setError(errMsg(e)); }
  };
  // FR-ADM-14 (Phúc 3A): xóa và đổi thứ tự khối chỉ ở bài M-/AI-; bài gốc dựng lại khối mỗi lần seed chạy.
  const moveBlock = async (i: number, d: -1 | 1) => {
    if (!detail) return;
    const ids = detail.blocks.map((b) => b.id);
    [ids[i], ids[i + d]] = [ids[i + d], ids[i]];
    try { await api.adminReorderBlocks(id, ids); await load(); onChanged(); } catch (e) { setError(errMsg(e)); }
  };
  const dropBlock = async (b: AdminBlock) => {
    if (!window.confirm(`Xóa khối #${b.position} “${String(b.payload.title ?? "")}”? Nội dung khối vẫn lưu trong nhật ký.`)) return;
    try { await api.adminDeleteBlock(id, b.id); await load(); onChanged(); } catch (e) { setError(errMsg(e)); }
  };
  if (error) return <p role="alert" className="text-danger">{error}</p>;
  if (!detail) return <p role="status" className="text-muted">Đang tải…</p>;
  const editable = id.startsWith("M-") || id.startsWith("AI-");
  const n = detail.blocks.length;
  return <div className="grid gap-3">
    <div className="flex flex-wrap items-center gap-2">
      <Button variant="ghost" onClick={onBack}>← Danh sách bài</Button>
      <h2 ref={headingRef} tabIndex={-1} className="text-lg font-bold outline-none">{detail.lesson.order ? `Bài ${detail.lesson.order}. ` : ""}{detail.lesson.title}</h2>
      {detail.lesson.hidden && <Badge tone="warning">Đang ẩn</Badge>}
      <Button variant="secondary" className="ml-auto" onClick={toggleHidden}>{detail.lesson.hidden ? "Hiện lại cho học sinh" : "Ẩn khỏi học sinh"}</Button>
    </div>
    <LessonMeta id={id} detail={detail} onSaved={() => { load(); onChanged(); }} />
    <ul className="grid gap-2">{detail.blocks.map((b, i) => <BlockEditor key={`${b.id}-${b.edited}-${b.position}`} lessonId={id} block={b} onChanged={() => { load(); onChanged(); }}
      controls={editable ? <>
        <Button variant="ghost" aria-label={`Đưa khối #${b.position} lên`} disabled={i === 0} onClick={() => moveBlock(i, -1)}>↑</Button>
        <Button variant="ghost" aria-label={`Đưa khối #${b.position} xuống`} disabled={i === n - 1} onClick={() => moveBlock(i, 1)}>↓</Button>
        <Button variant="ghost" aria-label={`Xóa khối #${b.position}`} disabled={n === 1} onClick={() => dropBlock(b)}>Xóa khối</Button>
      </> : undefined} />)}</ul>
    {editable && <AddBlock lessonId={id} onAdded={() => { load(); onChanged(); }} />}
    <ExercisesPanel lessonId={id} />
    <CardsPanel lessonId={id} />
    <div className="border-t border-line pt-3"><Button variant="ghost" onClick={remove}>Xóa bài này</Button>
      <span className="ml-2 text-xs text-muted">Xóa mềm: học sinh không thấy nữa, khôi phục được ở cuối danh sách bài.</span></div>
  </div>;
}

// FR-ADM-14: sửa tên và mục tiêu của mọi bài; bài gốc có thêm nút về tên gốc (seed không ghi đè bản sửa).
function LessonMeta({ id, detail, onSaved }: { id: string; detail: AdminLessonDetail; onSaved: () => void }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState(detail.lesson.title);
  const [objectives, setObjectives] = useState(detail.objectives.join("\n"));
  const [msg, setMsg] = useState<string | null>(null);
  const seed = !(id.startsWith("M-") || id.startsWith("AI-"));
  const save = async (reset = false) => {
    setMsg(null);
    try {
      const r = await api.adminUpdateLessonMeta(id, reset ? { reset: true }
        : { title, objectives: objectives.split("\n").map((x) => x.trim()).filter(Boolean) });
      setTitle(r.title); setObjectives(r.objectives.join("\n"));
      setMsg(r.changed ? "Đã lưu. Học sinh thấy tên mới ngay." : "Không có gì thay đổi."); onSaved();
    } catch (e) { setMsg(errMsg(e)); }
  };
  if (!open) return <div><Button variant="ghost" onClick={() => setOpen(true)}>Sửa tên và mục tiêu bài</Button>
    {detail.meta_edited && <Badge tone="warning">Tên đã sửa</Badge>}</div>;
  const box = "mt-1 w-full rounded-lg border border-line bg-surface p-2";
  return <Card className="grid gap-2 p-3">
    <label className="text-sm font-semibold">Tên bài<input className={box} value={title} maxLength={240} onChange={(e) => setTitle(e.target.value)} /></label>
    <label className="text-sm font-semibold">Mục tiêu (mỗi dòng một mục)<textarea rows={3} className={box} value={objectives} onChange={(e) => setObjectives(e.target.value)} /></label>
    <div className="flex flex-wrap gap-2"><Button disabled={!title.trim()} onClick={() => save()}>Lưu tên và mục tiêu</Button>
      {seed && detail.meta_edited && <Button variant="ghost" onClick={() => save(true)}>Về tên gốc</Button>}
      <Button variant="ghost" onClick={() => setOpen(false)}>Đóng</Button></div>
    {msg && <p role="status" className="text-sm">{msg}</p>}
  </Card>;
}

// FR-ADM-39 (Phúc 4A): nhập JSON/YAML; "Kiểm thử" chỉ báo sẽ đổi gì, "Nhập" mới ghi. Bài nhập mới ở trạng thái ẩn.
function ImportCard({ onDone }: { onDone: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [fileKey, setFileKey] = useState(0);
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [result, setResult] = useState<{ dry: boolean; rows: AdminImportRow[] } | null>(null);
  const run = async (dry: boolean) => {
    if (!file) return;
    setBusy(true); setErrors([]); setResult(null);
    try {
      const r = await api.adminImport(file, dry);
      setResult({ dry, rows: r.lessons });
      if (!dry) { setFile(null); setFileKey((k) => k + 1); onDone(); }
    } catch (e) {
      const m = errMsg(e);
      const [head, ...rest] = m.split(" | ");
      const [lead, first] = head.includes(": ") && head.includes("chưa nhập gì") ? [head.slice(0, head.indexOf(": ")), head.slice(head.indexOf(": ") + 2)] : [head, ""];
      setErrors([lead, ...[first, ...rest].filter(Boolean)]);
    } finally { setBusy(false); }
  };
  const template = async () => {
    try {
      const t = await api.adminImportTemplate();
      const url = URL.createObjectURL(new Blob([t.content], { type: "text/yaml;charset=utf-8" }));
      const a = document.createElement("a"); a.href = url; a.download = t.filename; a.click(); URL.revokeObjectURL(url);
    } catch (e) { setErrors([errMsg(e)]); }
  };
  return <Card className="grid gap-2 p-3">
    <p className="font-semibold">Nhập nội dung từ file</p>
    <p className="text-sm text-muted">File .yaml hoặc .json theo mẫu: bài, khối lý thuyết, câu luyện tập, nguồn. Music Engine kiểm đáp án.
      Nhập lại cùng mã bài thì cập nhật, không tạo bản trùng.</p>
    <div className="flex flex-wrap items-center gap-2">
      <input key={fileKey} type="file" accept=".yaml,.yml,.json" aria-label="File nội dung" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      <Button variant="secondary" loading={busy} disabled={!file || busy} onClick={() => run(true)}>Kiểm thử</Button>
      <Button loading={busy} disabled={!file || busy} onClick={() => run(false)}>Nhập</Button>
      <Button variant="ghost" onClick={template}>Tải file mẫu</Button>
    </div>
    {errors.length > 0 && <div role="alert" className="text-sm text-danger"><p className="font-semibold">{errors[0]}</p>
      {errors.length > 1 && <ul className="list-disc pl-5">{errors.slice(1).map((x, i) => <li key={i}>{x}</li>)}</ul>}</div>}
    {result && <div role="status" className="text-sm">
      <p className="font-semibold">{result.dry ? "Kiểm thử xong, chưa ghi gì. Nếu nhập sẽ:" : "Đã nhập:"}</p>
      <ul className="list-disc pl-5">{result.rows.map((r) => <li key={r.id}>
        {r.created ? "Tạo bài mới" : "Cập nhật bài"} “{r.title}” ({r.id}){r.created ? ", đang ẩn" : ""}
        {r.blocks_changed ? " · dựng lại khối" : ""}{r.exercises_added.length ? ` · thêm ${r.exercises_added.length} câu` : ""}
        {r.exercises_revised.length ? ` · sửa ${r.exercises_revised.length} câu (tăng phiên bản)` : ""}
        {r.cards_added.length ? ` · thêm ${r.cards_added.length} thẻ ôn${r.cards_activated_for ? ` (đã kích hoạt cho ${r.cards_activated_for} người học xong bài)` : ""}` : ""}{r.cards_revised.length ? ` · sửa ${r.cards_revised.length} thẻ ôn` : ""}
        {r.sources_added ? ` · thêm ${r.sources_added} nguồn` : ""}
        {!r.created && !r.blocks_changed && !r.exercises_added.length && !r.exercises_revised.length && !r.sources_added && !r.cards_added.length && !r.cards_revised.length ? " · không đổi gì" : ""}
        {r.exercises_not_in_file.length > 0 && <span className="text-warning"> · {r.exercises_not_in_file.length} câu không còn trong file (giữ nguyên, bỏ tay nếu cần)</span>}
        {r.cards_not_in_file.length > 0 && <span className="text-warning"> · {r.cards_not_in_file.length} thẻ không còn trong file (giữ nguyên, xóa tay nếu cần)</span>}
      </li>)}</ul></div>}
  </Card>;
}

function AddBlock({ lessonId, onAdded }: { lessonId: string; onAdded: () => void }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const add = async () => {
    try { await api.adminAddBlock(lessonId, title, text.split("\n").filter((l) => l.trim())); setTitle(""); setText(""); setOpen(false); onAdded(); }
    catch (e) { setMsg(errMsg(e)); }
  };
  if (!open) return <Button variant="secondary" onClick={() => setOpen(true)}>Thêm khối lý thuyết</Button>;
  return <div className="grid gap-2 rounded-lg border border-line p-3">
    <label className="text-sm font-semibold">Tiêu đề khối<input value={title} onChange={(e) => setTitle(e.target.value)} className="mt-1 min-h-10 w-full rounded-lg border border-line bg-surface px-3" /></label>
    <label className="text-sm font-semibold">Các đoạn văn (mỗi dòng một đoạn)<textarea rows={5} value={text} onChange={(e) => setText(e.target.value)} className="mt-1 w-full rounded-lg border border-line bg-surface p-2" /></label>
    <div className="flex gap-2"><Button disabled={!title.trim() || !text.trim()} onClick={add}>Thêm khối</Button><Button variant="ghost" onClick={() => setOpen(false)}>Hủy</Button></div>
    {msg && <p role="status" className="text-sm">{msg}</p>}
  </div>;
}

// FR-ADM-13: bài mới cần ít nhất một khối lý thuyết; bài ở trạng thái ẩn tới khi bấm "Hiện lại cho học sinh".
function CreateLesson({ onCreated }: { onCreated: (id: string) => void }) {
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({ title: "", objectives: "", block_title: "", paragraphs: "" });
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const split = (s: string) => s.split("\n").map((x) => x.trim()).filter(Boolean);
  const create = async () => {
    setBusy(true); setMsg(null);
    try { const r = await api.adminCreateLesson({ title: f.title, objectives: split(f.objectives), block_title: f.block_title, paragraphs: split(f.paragraphs) }); onCreated(r.id); }
    catch (e) { setMsg(errMsg(e)); } finally { setBusy(false); }
  };
  if (!open) return <Button onClick={() => setOpen(true)}>Tạo bài mới</Button>;
  const box = "mt-1 w-full rounded-lg border border-line bg-surface p-2";
  return <Card className="grid gap-2 p-3">
    <label className="text-sm font-semibold">Tên bài<input className={box} value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></label>
    <label className="text-sm font-semibold">Mục tiêu (mỗi dòng một mục, không bắt buộc)<textarea rows={2} className={box} value={f.objectives} onChange={(e) => setF({ ...f, objectives: e.target.value })} /></label>
    <label className="text-sm font-semibold">Tiêu đề khối lý thuyết đầu tiên<input className={box} value={f.block_title} onChange={(e) => setF({ ...f, block_title: e.target.value })} /></label>
    <label className="text-sm font-semibold">Các đoạn văn (mỗi dòng một đoạn)<textarea rows={4} className={box} value={f.paragraphs} onChange={(e) => setF({ ...f, paragraphs: e.target.value })} /></label>
    <p className="text-xs text-muted">Bài mới ở trạng thái ẩn. Thêm câu luyện tập, xem trước, rồi bấm “Hiện lại cho học sinh”.</p>
    <div className="flex gap-2"><Button loading={busy} disabled={busy || !f.title.trim() || !f.block_title.trim() || !f.paragraphs.trim()} onClick={create}>Tạo bài</Button>
      <Button variant="ghost" onClick={() => setOpen(false)}>Hủy</Button></div>
    {msg && <p role="status" className="text-sm">{msg}</p>}
  </Card>;
}

export default function LessonsTab() {
  const [rows, setRows] = useState<AdminLessonRow[] | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const load = () => api.adminLessons().then(setRows).catch(() => setFailed(true));
  useEffect(() => { load(); }, []);
  if (openId) return <LessonEditor id={openId} onBack={() => setOpenId(null)} onChanged={load} />;
  if (failed) return <p role="alert" className="text-danger">Chưa tải được danh sách bài.</p>;
  if (!rows) return <p role="status" className="text-muted">Đang tải…</p>;
  const live = rows.filter((l) => !l.deleted);
  const gone = rows.filter((l) => l.deleted);
  // FR-ADM-16: đổi chỗ hai bài liền nhau rồi gửi cả danh sách; máy chủ từ chối nếu danh sách đã cũ.
  const move = async (i: number, d: -1 | 1) => {
    const ids = live.map((l) => l.id);
    [ids[i], ids[i + d]] = [ids[i + d], ids[i]];
    try { await api.adminReorder(ids); setMsg(null); await load(); } catch (e) { setMsg(errMsg(e)); }
  };
  const restore = async (id: string) => { try { await api.adminRestoreLesson(id); await load(); } catch (e) { setMsg(errMsg(e)); } };
  return <div className="grid gap-3">
    <CreateLesson onCreated={(id) => { load(); setOpenId(id); }} />
    <ImportCard onDone={load} />
    {msg && <p role="alert" className="text-danger">{msg}</p>}
    <ul className="grid gap-2">{live.map((l, i) => <li key={l.id}><Card className="flex flex-wrap items-center justify-between gap-2 p-3">
      <div><p className="font-semibold">Bài {l.order}. {l.title} {l.hidden && <Badge tone="warning">Ẩn</Badge>}</p>
        <p className="text-sm text-muted">{l.block_count} khối · {l.exercise_count} câu hỏi · {l.edited_blocks} khối đã sửa · {l.draft_blocks} bản nháp</p></div>
      <div className="flex gap-1">
        <Button variant="ghost" aria-label={`Đưa bài ${l.order} lên`} disabled={i === 0} onClick={() => move(i, -1)}>↑</Button>
        <Button variant="ghost" aria-label={`Đưa bài ${l.order} xuống`} disabled={i === live.length - 1} onClick={() => move(i, 1)}>↓</Button>
        <Button variant="secondary" aria-label={`Sửa nội dung bài ${l.order}`} onClick={() => setOpenId(l.id)}>Sửa nội dung</Button></div>
    </Card></li>)}</ul>
    {gone.length > 0 && <details><summary className="cursor-pointer text-sm font-semibold">Bài đã xóa ({gone.length})</summary>
      <ul className="mt-2 grid gap-2">{gone.map((l) => <li key={l.id} className="flex items-center justify-between gap-2 rounded-lg border border-line p-2 text-sm">
        <span>{l.title}</span><Button variant="ghost" onClick={() => restore(l.id)}>Khôi phục</Button></li>)}</ul></details>}
  </div>;
}

import { useEffect, useState } from "react";
import { api, type AdminTemplateCatalogue, type AdminTemplatePreview } from "../../api";
import { Button } from "../ui/Button";

// FR-ADM-30 (Phúc 7A): mẫu câu có tham số. Đề, đáp án, lời giải đều do Music Engine dựng; Quản trị viên xem trước rồi mới lưu.
const errMsg = (e: unknown) => (e as { message?: string }).message ?? "Có lỗi xảy ra, thử lại sau.";
const input = "mt-1 min-h-10 w-full rounded-lg border border-line bg-surface px-3";

export default function TemplatesPanel({ lessonId, onSaved }: { lessonId: string; onSaved: () => void }) {
  const [open, setOpen] = useState(false);
  const [cat, setCat] = useState<AdminTemplateCatalogue | null>(null);
  const [tid, setTid] = useState("chord_tones");
  const [vals, setVals] = useState<Record<string, string>>({});
  const [skill, setSkill] = useState("");
  const [level, setLevel] = useState("hieu");
  const [preview, setPreview] = useState<AdminTemplatePreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => {
    if (open && !cat) api.adminQuestionTemplates().then((c) => { setCat(c); setSkill(c.skills.find((s) => s.startsWith("chord.")) ?? c.skills[0] ?? ""); })
      .catch((e) => setMsg(errMsg(e)));
  }, [open]);
  const tpl = cat?.templates.find((t) => t.id === tid);
  const body = () => ({ template: tid, params: vals, skill_id: skill, level });
  const pick = (id: string) => {
    setTid(id); setVals({}); setPreview(null); setMsg(null);
    const hint = cat?.templates.find((t) => t.id === id)?.skill_hint ?? "";
    setSkill(cat?.skills.find((s) => s.startsWith(hint)) ?? skill);
  };
  const run = async (save: boolean) => {
    setBusy(true); setMsg(null);
    try {
      if (!save) { setPreview(await api.adminTemplatePreview(lessonId, body())); return; }
      const r = await api.adminTemplateSave(lessonId, body());
      setMsg(`Đã lưu ${r.added.length} câu${r.duplicates.length ? `, bỏ ${r.duplicates.length} câu đã có trong bài` : ""}.`);
      setPreview(null); onSaved();
    } catch (e) { setMsg(errMsg(e)); } finally { setBusy(false); }
  };
  if (!open) return <Button variant="secondary" onClick={() => setOpen(true)}>Tạo câu từ mẫu</Button>;
  return <section className="grid gap-3 rounded-lg border border-line p-3" aria-label="Tạo câu từ mẫu">
    <h3 className="font-bold">Tạo câu từ mẫu</h3>
    {cat && tpl && <>
      <label className="text-sm font-semibold">Mẫu
        <select id="tpl-id" className={input} value={tid} onChange={(e) => pick(e.target.value)}>
          {cat.templates.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}</select></label>
      <p className="text-sm text-muted">Mẫu: “{tpl.pattern}”. Mỗi ô nhập nhiều giá trị cách nhau bằng dấu phẩy; máy sinh mọi tổ hợp (tối đa 30 câu).</p>
      <div className="grid gap-2 sm:grid-cols-2">{tpl.params.map((p) => <label key={p.key} className="text-sm font-semibold">{p.label}
        <input className={input} placeholder={p.example} value={vals[p.key] ?? ""} onChange={(e) => { setVals({ ...vals, [p.key]: e.target.value }); setPreview(null); }} /></label>)}</div>
      <div className="grid gap-2 sm:grid-cols-2">
        <label className="text-sm font-semibold">Kỹ năng<select id="tpl-skill" className={input} value={skill} onChange={(e) => setSkill(e.target.value)}>
          {cat.skills.map((s) => <option key={s} value={s}>{s}</option>)}</select></label>
        <label className="text-sm font-semibold">Mức độ<select className={input} value={level} onChange={(e) => setLevel(e.target.value)}>
          {cat.levels.map((l) => <option key={l} value={l}>{l}</option>)}</select></label></div>
      <div className="flex gap-2">
        <Button loading={busy} disabled={busy} onClick={() => run(false)}>Xem trước</Button>
        <Button variant="ghost" onClick={() => setOpen(false)}>Đóng</Button></div>
    </>}
    {msg && <p role="status" className="rounded-lg bg-primary-soft p-2 text-sm">{msg}</p>}
    {preview && <div className="grid gap-2">
      <ul className="grid gap-1 text-sm">{preview.items.map((i) => <li key={i.prompt} className="rounded border border-line p-2">
        <b>{i.prompt}</b><br />Đáp án (Engine): {i.answer}</li>)}</ul>
      {preview.skipped.map((s) => <p key={s.prompt} className="text-sm text-warning">Bỏ “{s.prompt}”: {s.reason}</p>)}
      <Button loading={busy} disabled={busy || preview.items.length === 0} onClick={() => run(true)}>Lưu {preview.items.length} câu vào bài</Button>
    </div>}
  </section>;
}

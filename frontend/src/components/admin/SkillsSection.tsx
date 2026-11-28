import { useEffect, useState } from "react";
import { api, type AdminSkill } from "../../api";
import { Button } from "../ui/Button";
import { Badge, Card, CardTitle } from "../ui/Page";

// FR-ADM-18..22 (Phúc 1A ngày 25/11). Kỹ năng/cạnh gốc của hệ thống chỉ xem: seed ghi lại mỗi lần khởi động.
// Kỹ năng của bài = kỹ năng các câu của bài (04 mục 6.5): đổi ở ô "Kỹ năng" trong form câu luyện tập.
// 27/11/2026 (Phúc 2A): không còn là tab riêng mà là mục "Nâng cao" thu gọn trong tab Bài học. Vẫn cần vì AI soạn bài
// chỉ gán được kỹ năng có sẵn: kiến thức mới (vd quãng kép) muốn có mastery riêng thì phải thêm kỹ năng ở đây.
// Phần Nguồn tài liệu bỏ khỏi giao diện: AI soạn bài tự gắn nguồn (tên tài liệu + trang), bài gốc do curriculum_specs.
const errMsg = (e: unknown) => (e as { message?: string }).message ?? "Có lỗi xảy ra, thử lại sau.";
const box = "min-h-10 rounded-lg border border-line bg-surface px-3";
// 10 nhóm MVP của hệ gợi ý (ADR-008): kỹ năng tự tạo phải thuộc một nhóm để được tính mastery và gợi ý (ADR-037).
const GROUPS: [string, string][] = [["note_names", "Tên nốt"], ["accidentals", "Dấu hóa"], ["intervals", "Quãng"], ["major_scales", "Âm giai trưởng"],
  ["minor_scales", "Âm giai thứ"], ["triads", "Hợp âm ba"], ["seventh_chords", "Hợp âm bảy"], ["diatonic_chords", "Hợp âm trong giọng"],
  ["progressions", "Vòng hợp âm"], ["rhythm_basics", "Nhịp cơ bản"]];
const GROUP_VI = Object.fromEntries(GROUPS);

function Thresholds({ skill, onSaved }: { skill: AdminSkill; onSaved: (msg: string) => void }) {
  const [ready, setReady] = useState(String(skill.ready_threshold ?? 0.6));
  const [mastery, setMastery] = useState(String(skill.mastery_threshold ?? 0.8));
  const [err, setErr] = useState<string | null>(null);
  const save = async () => {
    setErr(null);
    try {
      const r = await api.adminSetThresholds(skill.id, Number(ready.replace(",", ".")), Number(mastery.replace(",", ".")));
      onSaved(r.changed ? "Đã lưu ngưỡng." : "Ngưỡng không đổi.");
    } catch (e) { setErr(errMsg(e)); }
  };
  return <div className="mt-2 flex flex-wrap items-end gap-2">
    <label className="text-xs font-semibold">Ngưỡng sẵn sàng<input aria-label={`Ngưỡng sẵn sàng của ${skill.id}`} className={`${box} mt-1 block w-24`} inputMode="decimal" value={ready} onChange={(e) => setReady(e.target.value)} /></label>
    <label className="text-xs font-semibold">Ngưỡng thành thạo<input aria-label={`Ngưỡng thành thạo của ${skill.id}`} className={`${box} mt-1 block w-24`} inputMode="decimal" value={mastery} onChange={(e) => setMastery(e.target.value)} /></label>
    <Button variant="secondary" aria-label={`Lưu ngưỡng của ${skill.id}`} onClick={save}>Lưu ngưỡng</Button>
    {err && <span role="alert" className="text-xs text-danger">{err}</span>}
  </div>;
}

export default function SkillsSection() {
  const [skills, setSkills] = useState<AdminSkill[] | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [form, setForm] = useState({ slug: "", name: "", domain: "theory", group_code: "" });
  const [pre, setPre] = useState<Record<string, string>>({});
  const [q, setQ] = useState("");

  const load = () => {
    api.adminSkills().then(setSkills).catch((e) => setMsg(errMsg(e)));
  };
  useEffect(load, []);
  const run = async (fn: () => Promise<unknown>, ok: string) => {
    setMsg(null);
    try { await fn(); setMsg(ok); load(); } catch (e) { setMsg(errMsg(e)); }
  };
  if (!skills) return <p role="status" className="text-muted">{msg ?? "Đang tải…"}</p>;
  const name = new Map(skills.map((s) => [s.id, s.name]));
  const shown = skills.filter((s) => !q || `${s.id} ${s.name}`.toLowerCase().includes(q.toLowerCase()));

  return <div className="grid gap-4">
    {msg && <p role="status" className="rounded-lg bg-primary-soft p-2 text-sm">{msg}</p>}
    <Card className="grid gap-2 p-4">
      <CardTitle>Thêm kỹ năng</CardTitle>
      <div className="grid gap-2 sm:grid-cols-4">
        <label className="text-sm font-semibold">Mã (không dấu)<input className={`${box} mt-1 w-full`} placeholder="quang_ghep" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} /></label>
        <label className="text-sm font-semibold">Tên<input className={`${box} mt-1 w-full`} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        <label className="text-sm font-semibold">Miền<input className={`${box} mt-1 w-full`} value={form.domain} onChange={(e) => setForm({ ...form, domain: e.target.value })} /></label>
        <label className="text-sm font-semibold">Nhóm gợi ý<select id="new-skill-group" className={`${box} mt-1 w-full`} value={form.group_code} onChange={(e) => setForm({ ...form, group_code: e.target.value })}>
          <option value="">(chọn nhóm)</option>{GROUPS.map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
      </div>
      <p className="text-xs text-muted">Mã được thêm tiền tố “custom.”. Kỹ năng thuộc nhóm đã chọn nên được tính mastery và đưa vào vector hệ gợi ý như kỹ năng gốc.</p>
      <div><Button disabled={!form.slug.trim() || !form.name.trim() || !form.group_code}
        onClick={() => run(() => api.adminCreateSkill(form).then(() => setForm({ slug: "", name: "", domain: "theory", group_code: "" })), "Đã thêm kỹ năng.")}>Thêm kỹ năng</Button></div>
    </Card>

    <Card className="grid gap-2 p-4">
      <CardTitle>Kỹ năng và tiên quyết ({skills.length})</CardTitle>
      <label htmlFor="skill-q" className="sr-only">Lọc kỹ năng</label>
      <input id="skill-q" className={box} placeholder="Lọc theo mã hoặc tên" value={q} onChange={(e) => setQ(e.target.value)} />
      <ul className="grid gap-2">{shown.map((s) => <li key={s.id} className="rounded-lg border border-line p-3 text-sm">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold">{s.name}</span><code className="text-xs text-muted">{s.id}</code>
          {s.seed ? <Badge tone="muted">Gốc</Badge> : <Badge>Tự thêm</Badge>}{s.mvp && s.group_code && <Badge tone="muted">{GROUP_VI[s.group_code] ?? s.group_code}</Badge>}{!s.mvp && <Badge tone="warning">Ngoài hệ gợi ý</Badge>}
          {!s.seed && <Button variant="ghost" className="ml-auto" onClick={() => {
            if (window.confirm(`Xóa kỹ năng ${s.id}?`)) run(() => api.adminDeleteSkill(s.id), "Đã xóa kỹ năng.");
          }}>Xóa</Button>}
        </div>
        {!s.seed && <div className="mt-1 flex items-center gap-2">
          <label className="text-xs font-semibold" htmlFor={`grp-${s.id}`}>Nhóm gợi ý</label>
          <select id={`grp-${s.id}`} className={box} value={s.mvp ? s.group_code ?? "" : ""}
            onChange={(e) => e.target.value && run(() => api.adminUpdateSkill(s.id, { name: s.name, domain: s.domain, group_code: e.target.value }), "Đã đổi nhóm kỹ năng.")}>
            <option value="">{s.mvp ? "(giữ nguyên)" : "(chưa chọn: ngoài hệ gợi ý)"}</option>
            {GROUPS.map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></div>}
        {s.mvp && <Thresholds key={`${s.id}-${s.ready_threshold}-${s.mastery_threshold}`} skill={s} onSaved={(m) => { setMsg(m); load(); }} />}
        <p className="mt-1 text-muted">Bài đang dùng: {s.lessons.length ? s.lessons.join(", ") : "chưa có"}</p>
        <div className="mt-1 flex flex-wrap items-center gap-1">Cần học trước:
          {s.prerequisites.length === 0 && <span className="text-muted">không</span>}
          {s.prerequisites.map((p) => <span key={p} className="inline-flex items-center gap-1 rounded-full border border-line px-2">
            {name.get(p) ?? p}
            {!s.seed_prerequisites.includes(p) && <button type="button" aria-label={`Gỡ tiên quyết ${p} của ${s.id}`} className="text-danger"
              onClick={() => run(() => api.adminRemovePrereq(s.id, p), "Đã gỡ tiên quyết.")}>×</button>}</span>)}
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          <label className="sr-only" htmlFor={`pre-${s.id}`}>Thêm tiên quyết cho {s.id}</label>
          <select id={`pre-${s.id}`} className={box} value={pre[s.id] ?? ""} onChange={(e) => setPre({ ...pre, [s.id]: e.target.value })}>
            <option value="">Thêm kỹ năng cần học trước…</option>
            {skills.filter((x) => x.id !== s.id && !s.prerequisites.includes(x.id)).map((x) => <option key={x.id} value={x.id}>{x.name} ({x.id})</option>)}
          </select>
          <Button variant="secondary" disabled={!pre[s.id]} onClick={() => run(() => api.adminAddPrereq(s.id, pre[s.id]), "Đã thêm tiên quyết.")}>Thêm</Button>
        </div>
      </li>)}</ul>
    </Card>

  </div>;
}

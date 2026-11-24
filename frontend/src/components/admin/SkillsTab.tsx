import { useEffect, useState } from "react";
import { api, type AdminLessonRow, type AdminSkill, type AdminSource } from "../../api";
import { Button } from "../ui/Button";
import { Badge, Card, CardTitle } from "../ui/Page";

// FR-ADM-18..22, FR-ADM-38 (Phúc 1A). Kỹ năng/cạnh/nguồn gốc của hệ thống chỉ xem: seed ghi lại mỗi lần khởi động.
// Kỹ năng của bài = kỹ năng các câu của bài (04 mục 6.5): đổi ở ô "Kỹ năng" trong form câu luyện tập.
const errMsg = (e: unknown) => (e as { message?: string }).message ?? "Có lỗi xảy ra, thử lại sau.";
const box = "min-h-10 rounded-lg border border-line bg-surface px-3";

export default function SkillsTab() {
  const [skills, setSkills] = useState<AdminSkill[] | null>(null);
  const [sources, setSources] = useState<AdminSource[]>([]);
  const [lessons, setLessons] = useState<AdminLessonRow[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [form, setForm] = useState({ slug: "", name: "", domain: "theory" });
  const [src, setSrc] = useState({ title: "", author: "", url: "" });
  const [link, setLink] = useState({ lesson: "", source: "", locator: "" });
  const [pre, setPre] = useState<Record<string, string>>({});
  const [q, setQ] = useState("");

  const load = () => {
    api.adminSkills().then(setSkills).catch((e) => setMsg(errMsg(e)));
    api.adminSources().then(setSources).catch(() => undefined);
    api.adminLessons().then(setLessons).catch(() => undefined);
  };
  useEffect(load, []);
  const run = async (fn: () => Promise<unknown>, ok: string) => {
    setMsg(null);
    try { await fn(); setMsg(ok); load(); } catch (e) { setMsg(errMsg(e)); }
  };
  if (!skills) return <p role="status" className="text-muted">{msg ?? "Đang tải…"}</p>;
  const own = lessons.filter((l) => l.id.startsWith("M-") || l.id.startsWith("AI-"));
  const name = new Map(skills.map((s) => [s.id, s.name]));
  const shown = skills.filter((s) => !q || `${s.id} ${s.name}`.toLowerCase().includes(q.toLowerCase()));

  return <div className="grid gap-4">
    {msg && <p role="status" className="rounded-lg bg-primary-soft p-2 text-sm">{msg}</p>}
    <Card className="grid gap-2 p-4">
      <CardTitle>Thêm kỹ năng</CardTitle>
      <div className="grid gap-2 sm:grid-cols-3">
        <label className="text-sm font-semibold">Mã (không dấu)<input className={`${box} mt-1 w-full`} placeholder="quang_ghep" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} /></label>
        <label className="text-sm font-semibold">Tên<input className={`${box} mt-1 w-full`} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        <label className="text-sm font-semibold">Miền<input className={`${box} mt-1 w-full`} value={form.domain} onChange={(e) => setForm({ ...form, domain: e.target.value })} /></label>
      </div>
      <p className="text-xs text-muted">Mã được thêm tiền tố “custom.”. Kỹ năng mới chưa có trong vector hệ gợi ý (ADR-008) cho tới khi nhóm thêm vào bảng ánh xạ.</p>
      <div><Button disabled={!form.slug.trim() || !form.name.trim()}
        onClick={() => run(() => api.adminCreateSkill(form).then(() => setForm({ slug: "", name: "", domain: "theory" })), "Đã thêm kỹ năng.")}>Thêm kỹ năng</Button></div>
    </Card>

    <Card className="grid gap-2 p-4">
      <CardTitle>Kỹ năng và tiên quyết ({skills.length})</CardTitle>
      <label htmlFor="skill-q" className="sr-only">Lọc kỹ năng</label>
      <input id="skill-q" className={box} placeholder="Lọc theo mã hoặc tên" value={q} onChange={(e) => setQ(e.target.value)} />
      <ul className="grid gap-2">{shown.map((s) => <li key={s.id} className="rounded-lg border border-line p-3 text-sm">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold">{s.name}</span><code className="text-xs text-muted">{s.id}</code>
          {s.seed ? <Badge tone="muted">Gốc</Badge> : <Badge>Tự thêm</Badge>}{!s.mvp && <Badge tone="warning">Ngoài hệ gợi ý</Badge>}
          {!s.seed && <Button variant="ghost" className="ml-auto" onClick={() => {
            if (window.confirm(`Xóa kỹ năng ${s.id}?`)) run(() => api.adminDeleteSkill(s.id), "Đã xóa kỹ năng.");
          }}>Xóa</Button>}
        </div>
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

    <Card className="grid gap-2 p-4">
      <CardTitle>Nguồn tài liệu ({sources.length})</CardTitle>
      <div className="grid gap-2 sm:grid-cols-3">
        <label className="text-sm font-semibold">Tên tài liệu<input className={`${box} mt-1 w-full`} value={src.title} onChange={(e) => setSrc({ ...src, title: e.target.value })} /></label>
        <label className="text-sm font-semibold">Tác giả<input className={`${box} mt-1 w-full`} value={src.author} onChange={(e) => setSrc({ ...src, author: e.target.value })} /></label>
        <label className="text-sm font-semibold">Liên kết<input className={`${box} mt-1 w-full`} placeholder="https://" value={src.url} onChange={(e) => setSrc({ ...src, url: e.target.value })} /></label>
      </div>
      <div><Button disabled={!src.title.trim()} onClick={() => run(() => api.adminCreateSource({ title: src.title, author: src.author || null, url: src.url || null })
        .then(() => setSrc({ title: "", author: "", url: "" })), "Đã thêm nguồn.")}>Thêm nguồn</Button></div>
      <div className="grid gap-2 rounded-lg border border-line p-3 sm:grid-cols-4">
        <label className="text-sm font-semibold">Bài (tự tạo hoặc AI)<select id="link-lesson" className={`${box} mt-1 w-full`} value={link.lesson} onChange={(e) => setLink({ ...link, lesson: e.target.value })}>
          <option value="">(chọn)</option>{own.map((l) => <option key={l.id} value={l.id}>{l.title}</option>)}</select></label>
        <label className="text-sm font-semibold">Nguồn<select id="link-source" className={`${box} mt-1 w-full`} value={link.source} onChange={(e) => setLink({ ...link, source: e.target.value })}>
          <option value="">(chọn)</option>{sources.map((w) => <option key={w.id} value={w.id}>{w.title}</option>)}</select></label>
        <label className="text-sm font-semibold">Vị trí<input className={`${box} mt-1 w-full`} placeholder="chương 2, trang 14" value={link.locator} onChange={(e) => setLink({ ...link, locator: e.target.value })} /></label>
        <div className="flex items-end"><Button variant="secondary" disabled={!link.lesson || !link.source}
          onClick={() => run(() => api.adminLinkSource(link.lesson, { source_id: link.source, locator: link.locator, note: null }), "Đã gắn nguồn vào bài.")}>Gắn vào bài</Button></div>
      </div>
      <p className="text-xs text-muted">Nguồn của bài gốc do curriculum_specs quản lý. Mỗi bài phải còn ít nhất một nguồn (nguyên tắc 11).</p>
      <ul className="grid gap-2">{sources.map((w) => <li key={w.id} className="rounded-lg border border-line p-2 text-sm">
        <p className="font-semibold">{w.title} {w.seed ? <Badge tone="muted">Gốc</Badge> : <Badge>Tự thêm</Badge>}</p>
        <p className="text-muted">{[w.author, w.url].filter(Boolean).join(" · ") || "chưa có tác giả/liên kết"}</p>
        {w.lessons.length > 0 && <ul className="mt-1 flex flex-wrap gap-1">{w.lessons.map((l) => <li key={l.id} className="inline-flex items-center gap-1 rounded-full border border-line px-2">
          {l.lesson_id} · {l.locator}
          {(l.lesson_id.startsWith("M-") || l.lesson_id.startsWith("AI-")) && <button type="button" aria-label={`Gỡ nguồn khỏi ${l.lesson_id}`} className="text-danger"
            onClick={() => run(() => api.adminUnlinkSource(l.id), "Đã gỡ nguồn.")}>×</button>}</li>)}</ul>}
      </li>)}</ul>
    </Card>
  </div>;
}

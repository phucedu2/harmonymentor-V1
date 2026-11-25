import { useEffect, useState } from "react";
import { api, type AdminCard, type AdminCardForm, type AdminCardList } from "../../api";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Page";

// FR-ADM-31..34 (Phúc 6A): soạn thẻ ôn bằng form, gắn được vào mọi bài. Thẻ gốc chỉ xem. Với các loại do Engine tính
// (dựng hợp âm, âm giai, quãng, số La Mã) người soạn không gõ đáp án: Music Engine ở máy chủ tính và trả về (nguyên tắc 1).
const KIND_VI: Record<string, string> = { recall: "Nhớ đáp án", self_check: "Ý mở (tự đánh giá)", build_chord: "Dựng hợp âm",
  build_scale: "Dựng âm giai", interval: "Gọi tên quãng", roman: "Số La Mã trong giọng" };
const SCALE_VI: Record<string, string> = { major: "Trưởng", natural_minor: "Thứ tự nhiên" };
const errMsg = (e: unknown) => (e as { message?: string }).message ?? "Có lỗi xảy ra, thử lại sau.";
const input = "mt-1 min-h-10 w-full rounded-lg border border-line bg-surface px-3";

function blank(skill: string): AdminCardForm {
  return { kind: "recall", front: "", back: "", expected: "", case_sensitive: true, skill_id: skill };
}

function CardForm({ initial, skills, onSave, onCancel, busy }: {
  initial: AdminCardForm; skills: string[]; onSave: (f: AdminCardForm) => void; onCancel: () => void; busy: boolean;
}) {
  const [f, setF] = useState<AdminCardForm>(initial);
  const [kw, setKw] = useState((initial.keywords ?? []).join(", "));
  const set = (patch: Partial<AdminCardForm>) => setF({ ...f, ...patch });
  const chk = (k: string) => (f.check as Record<string, string> | undefined)?.[k] ?? "";
  const setChk = (k: string, v: string) => set({ check: { ...(f.check ?? {}), [k]: v } });
  const submit = () => {
    const base = { kind: f.kind, front: f.front, skill_id: f.skill_id };
    const by: Record<string, Partial<AdminCardForm>> = {
      recall: { back: f.back, expected: f.expected, case_sensitive: f.case_sensitive },
      self_check: { back: f.back, keywords: kw.split(",").map((x) => x.trim()).filter(Boolean) },
      build_chord: { symbol: f.symbol }, build_scale: { tonic: f.tonic, scale_type: f.scale_type ?? "major" },
      interval: { check: { lower: chk("lower"), upper: chk("upper") } }, roman: { check: { key: chk("key"), chord: chk("chord") } },
    };
    onSave({ ...base, ...by[f.kind] } as AdminCardForm);
  };
  return <div className="grid gap-3 rounded-lg border border-primary/40 p-3">
    <div className="grid gap-2 sm:grid-cols-2">
      <label className="text-sm font-semibold">Loại thẻ
        <select id="card-kind" className={input} value={f.kind} onChange={(e) => set({ kind: e.target.value })}>
          {Object.entries(KIND_VI).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
      <label className="text-sm font-semibold">Kỹ năng
        <select id="card-skill" className={input} value={f.skill_id} onChange={(e) => set({ skill_id: e.target.value })}>
          {skills.map((s) => <option key={s} value={s}>{s}</option>)}</select></label>
    </div>
    <label className="text-sm font-semibold">Mặt trước (câu hỏi)
      <textarea rows={2} className={input} value={f.front} onChange={(e) => set({ front: e.target.value })} /></label>
    {(f.kind === "recall" || f.kind === "self_check") && <label className="text-sm font-semibold">Mặt sau (đáp án hiện sau khi lật)
      <textarea rows={2} className={input} value={f.back ?? ""} onChange={(e) => set({ back: e.target.value })} /></label>}
    {f.kind === "recall" && <div className="grid gap-2 sm:grid-cols-2">
      <label className="text-sm font-semibold">Chuỗi chấm đúng (để trống thì dùng mặt sau)
        <input className={input} value={f.expected ?? ""} onChange={(e) => set({ expected: e.target.value })} /></label>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.case_sensitive ?? true} onChange={(e) => set({ case_sensitive: e.target.checked })} />
        Phân biệt chữ hoa/thường (M3 khác m3)</label></div>}
    {f.kind === "self_check" && <label className="text-sm font-semibold">Từ khóa gợi ý (cách nhau bằng dấu phẩy, không bắt buộc)
      <input className={input} value={kw} onChange={(e) => setKw(e.target.value)} /></label>}
    {f.kind === "build_chord" && <label className="text-sm font-semibold">Ký hiệu hợp âm
      <input className={input} placeholder="Dm7" value={f.symbol ?? ""} onChange={(e) => set({ symbol: e.target.value })} /></label>}
    {f.kind === "build_scale" && <div className="grid gap-2 sm:grid-cols-2">
      <label className="text-sm font-semibold">Chủ âm<input className={input} placeholder="G" value={f.tonic ?? ""} onChange={(e) => set({ tonic: e.target.value })} /></label>
      <label className="text-sm font-semibold">Loại âm giai
        <select className={input} value={f.scale_type ?? "major"} onChange={(e) => set({ scale_type: e.target.value })}>
          {Object.entries(SCALE_VI).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label></div>}
    {f.kind === "interval" && <div className="grid gap-2 sm:grid-cols-2">
      <label className="text-sm font-semibold">Nốt dưới<input className={input} placeholder="C" value={chk("lower")} onChange={(e) => setChk("lower", e.target.value)} /></label>
      <label className="text-sm font-semibold">Nốt trên<input className={input} placeholder="E" value={chk("upper")} onChange={(e) => setChk("upper", e.target.value)} /></label></div>}
    {f.kind === "roman" && <div className="grid gap-2 sm:grid-cols-2">
      <label className="text-sm font-semibold">Giọng<input className={input} placeholder="C" value={chk("key")} onChange={(e) => setChk("key", e.target.value)} /></label>
      <label className="text-sm font-semibold">Hợp âm<input className={input} placeholder="Dm7" value={chk("chord")} onChange={(e) => setChk("chord", e.target.value)} /></label></div>}
    {!["recall", "self_check"].includes(f.kind) && <p className="text-xs text-muted">Đáp án do Music Engine tính. Đề phải nêu đúng ký hiệu bạn nhập ở trên.</p>}
    <div className="flex gap-2"><Button loading={busy} disabled={busy || !f.front.trim()} onClick={submit}>Lưu thẻ</Button>
      <Button variant="ghost" onClick={onCancel}>Hủy</Button></div>
  </div>;
}

export default function CardsPanel({ lessonId }: { lessonId: string }) {
  const [data, setData] = useState<AdminCardList | null>(null);
  const [editing, setEditing] = useState<string | "new" | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const load = () => api.adminCards(lessonId).then(setData).catch((e) => setMsg(errMsg(e)));
  useEffect(() => { load(); }, [lessonId]);
  const save = async (f: AdminCardForm) => {
    setBusy(true); setMsg(null);
    try {
      const r = editing === "new" ? await api.adminAddCard(lessonId, f) : await api.adminUpdateCard(editing!, f);
      const act = "activated_for" in r && r.activated_for ? ` Đã kích hoạt cho ${r.activated_for} người đã học xong bài.` : "";
      setMsg(`Đã lưu thẻ. Mặt sau: ${r.back}.${act}`); setEditing(null); await load();
    } catch (e) { setMsg(errMsg(e)); } finally { setBusy(false); }
  };
  const remove = async (c: AdminCard) => {
    if (!window.confirm("Xóa thẻ này? Thẻ biến khỏi hàng đợi ôn; lượt ôn cũ vẫn giữ.")) return;
    try { await api.adminDeleteCard(c.id); setMsg("Đã xóa thẻ."); await load(); } catch (e) { setMsg(errMsg(e)); }
  };
  if (!data) return <p role="status" className="text-sm text-muted">{msg ?? "Đang tải thẻ ôn…"}</p>;
  return <section className="grid gap-2" aria-label="Thẻ ôn">
    <h3 className="font-bold">Thẻ ôn ({data.cards.length})</h3>
    <p className="text-sm text-muted">Thẻ gốc của hệ thống chỉ xem (seed ghi lại mỗi lần khởi động). Thẻ bạn thêm sửa và xóa được, gắn được vào mọi bài.</p>
    {msg && <p role="status" className="rounded-lg bg-primary-soft p-2 text-sm">{msg}</p>}
    <ul className="grid gap-2">{data.cards.map((c) => <li key={c.id} className="rounded-lg border border-line p-2">
      {editing === c.id && c.form ? <CardForm initial={c.form} skills={data.skills} busy={busy} onSave={save} onCancel={() => setEditing(null)} />
        : <div className="flex flex-wrap items-center justify-between gap-2">
          <div><p>{c.front}</p><p className="text-xs text-muted">{c.editable ? <Badge>Tự soạn</Badge> : <Badge tone="muted">Gốc</Badge>}{" "}
            {c.skill_id} · đáp án: {c.back}</p></div>
          {c.editable && <div className="flex gap-1"><Button variant="ghost" aria-label={`Sửa thẻ ${c.id}`} onClick={() => setEditing(c.id)}>Sửa</Button>
            <Button variant="ghost" aria-label={`Xóa thẻ ${c.id}`} onClick={() => remove(c)}>Xóa thẻ</Button></div>}
        </div>}
    </li>)}</ul>
    {editing === "new" ? <CardForm initial={blank(data.skills[0] ?? "")} skills={data.skills} busy={busy} onSave={save} onCancel={() => setEditing(null)} />
      : <Button variant="secondary" onClick={() => setEditing("new")}>Thêm thẻ ôn</Button>}
  </section>;
}

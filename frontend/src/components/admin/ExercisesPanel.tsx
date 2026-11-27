import { useEffect, useState } from "react";
import { api, type AdminCheck, type AdminExercise, type AdminExerciseList, type AdminQuestion } from "../../api";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Page";

// FR-ADM-24..29 (Phúc 5A): soạn câu luyện tập bằng form. Đáp án do Music Engine tính ở máy chủ; frontend không tự tính
// nhạc lý (nguyên tắc 1), chỉ gửi đề + phần kiểm rồi hiện đáp án Engine trả về.
const KIND_VI: Record<string, string> = { mcq: "Trắc nghiệm", true_false: "Đúng/Sai", multi_select: "Chọn nhiều", short: "Tự luận ngắn",
  build_chord: "Dựng hợp âm", build_scale: "Dựng âm giai", open: "Tự luận mở" };
const LEVEL_VI: Record<string, string> = { nho: "Nhớ (dễ)", hieu: "Hiểu (vừa)", van_dung: "Vận dụng (khó)" };
const CHECK_VI: Record<string, string> = { "": "Không (tôi tự chọn đáp án)", interval: "Quãng giữa hai nốt", chord_tones: "Các nốt của hợp âm",
  chord_name: "Gọi tên hợp âm từ các nốt", roman: "Số La Mã trong giọng" };
const errMsg = (e: unknown) => (e as { message?: string }).message ?? "Có lỗi xảy ra, thử lại sau.";
const lines = (s: string) => s.split("\n").map((x) => x.trim()).filter(Boolean);
const input = "mt-1 min-h-10 w-full rounded-lg border border-line bg-surface px-3";

function blank(skill: string): AdminQuestion {
  return { kind: "mcq", level: "hieu", prompt: "", skill_id: skill, explanation: "", options: [], answer: "", check: null };
}

function CheckFields({ kinds, check, onChange }: { kinds: string[]; check: AdminCheck | null | undefined; onChange: (c: AdminCheck | null) => void }) {
  const type = check?.type ?? "";
  const field = (k: string, label: string, placeholder: string) => <label className="text-sm">{label}
    <input className={input} placeholder={placeholder} value={(check as Record<string, string> | null)?.[k] ?? ""}
      onChange={(e) => onChange({ ...(check as object), [k]: e.target.value } as AdminCheck)} /></label>;
  return <div className="grid gap-2 rounded-lg border border-line p-2">
    <label className="text-sm font-semibold">Phần kiểm cho Music Engine
      <select className={input} value={type} onChange={(e) => onChange(e.target.value ? { type: e.target.value } as AdminCheck : null)}>
        {kinds.map((k) => <option key={k} value={k}>{CHECK_VI[k]}</option>)}</select></label>
    {type === "interval" && <div className="grid gap-2 sm:grid-cols-2">{field("lower", "Nốt dưới", "C")}{field("upper", "Nốt trên", "E")}</div>}
    {type === "chord_tones" && field("symbol", "Ký hiệu hợp âm", "Dm7")}
    {type === "chord_name" && field("notes", "Các nốt (cách nhau bằng dấu cách)", "D F A C")}
    {type === "roman" && <div className="grid gap-2 sm:grid-cols-2">{field("key", "Giọng", "C")}{field("chord", "Hợp âm", "G7")}</div>}
    <p className="text-xs text-muted">Có phần kiểm thì Engine tự tính đáp án; đề phải nêu đúng ký hiệu này.</p>
  </div>;
}

function ExerciseForm({ initial, meta, onSave, onCancel, busy }: {
  initial: AdminQuestion; meta: AdminExerciseList; onSave: (q: AdminQuestion) => void; onCancel: () => void; busy: boolean;
}) {
  const [q, setQ] = useState<AdminQuestion>(initial);
  const [opts, setOpts] = useState((initial.options ?? []).join("\n"));
  const [rubric, setRubric] = useState((initial.rubric ?? []).join("\n"));
  const set = (patch: Partial<AdminQuestion>) => setQ({ ...q, ...patch });
  const options = q.kind === "true_false" ? ["Đúng", "Sai"] : lines(opts);
  const submit = () => {
    const base = { kind: q.kind, level: q.level, prompt: q.prompt, skill_id: q.skill_id, explanation: q.explanation };
    const byKind: Record<string, Partial<AdminQuestion>> = {
      mcq: { options, answer: q.answer, check: q.check ?? undefined },
      true_false: { answer: q.answer, check: q.check ?? undefined },
      multi_select: { options, answers: (q.answers ?? []).filter((a) => options.includes(a)), check: q.check ?? undefined },
      short: { check: q.check ?? undefined }, build_chord: { symbol: q.symbol }, build_scale: { tonic: q.tonic, scale_type: q.scale_type },
      open: { model_answer: q.model_answer, rubric: lines(rubric) },
    };
    onSave({ ...base, ...byKind[q.kind] } as AdminQuestion);
  };
  const checkKinds = q.kind === "short" ? ["interval", "chord_name", "roman"] : q.kind === "multi_select" ? ["", "chord_tones"]
    : ["", "interval", "chord_tones"];
  return <div className="grid gap-3 rounded-lg border border-primary/40 p-3">
    <div className="grid gap-2 sm:grid-cols-3">
      <label className="text-sm font-semibold">Loại câu<select className={input} value={q.kind} onChange={(e) => set({ kind: e.target.value, check: null })}>
        {meta.kinds.map((k) => <option key={k} value={k}>{KIND_VI[k] ?? k}</option>)}</select></label>
      <label className="text-sm font-semibold">Độ khó<select className={input} value={q.level} onChange={(e) => set({ level: e.target.value })}>
        {meta.levels.map((k) => <option key={k} value={k}>{LEVEL_VI[k] ?? k}</option>)}</select></label>
      <label className="text-sm font-semibold">Kỹ năng<select className={input} value={q.skill_id} onChange={(e) => set({ skill_id: e.target.value })}>
        {meta.skills.map((k) => <option key={k} value={k}>{k}</option>)}</select></label>
    </div>
    <label className="text-sm font-semibold">Đề bài<textarea className={input} rows={2} value={q.prompt} onChange={(e) => set({ prompt: e.target.value })} /></label>
    {(q.kind === "mcq" || q.kind === "multi_select") && <label className="text-sm font-semibold">Phương án (mỗi dòng một phương án)
      <textarea className={input} rows={4} value={opts} onChange={(e) => setOpts(e.target.value)} /></label>}
    {(q.kind === "mcq" || q.kind === "true_false") && <label className="text-sm font-semibold">Đáp án đúng
      <select id="ex-answer" className={input} value={q.answer ?? ""} onChange={(e) => set({ answer: e.target.value })}>
        <option value="">(chọn)</option>{options.map((o) => <option key={o} value={o}>{o}</option>)}</select></label>}
    {q.kind === "multi_select" && <fieldset className="text-sm"><legend className="font-semibold">Các đáp án đúng</legend>
      <div className="flex flex-wrap gap-3">{options.map((o) => <label key={o} className="flex items-center gap-1">
        <input type="checkbox" checked={(q.answers ?? []).includes(o)}
          onChange={(e) => set({ answers: e.target.checked ? [...(q.answers ?? []), o] : (q.answers ?? []).filter((a) => a !== o) })} />{o}</label>)}</div></fieldset>}
    {["mcq", "multi_select", "short"].includes(q.kind) && <CheckFields kinds={checkKinds} check={q.check} onChange={(c) => set({ check: c })} />}
    {q.kind === "build_chord" && <label className="text-sm font-semibold">Ký hiệu hợp âm Engine dựng
      <input className={input} placeholder="Ebm7b5" value={q.symbol ?? ""} onChange={(e) => set({ symbol: e.target.value })} /></label>}
    {q.kind === "build_scale" && <div className="grid gap-2 sm:grid-cols-2">
      <label className="text-sm font-semibold">Chủ âm<input className={input} placeholder="G" value={q.tonic ?? ""} onChange={(e) => set({ tonic: e.target.value })} /></label>
      <label className="text-sm font-semibold">Loại âm giai<select className={input} value={q.scale_type ?? "major"} onChange={(e) => set({ scale_type: e.target.value })}>
        <option value="major">Trưởng</option><option value="natural_minor">Thứ tự nhiên</option></select></label></div>}
    {q.kind === "open" && <>
      <label className="text-sm font-semibold">Đáp án mẫu<textarea className={input} rows={2} value={q.model_answer ?? ""} onChange={(e) => set({ model_answer: e.target.value })} /></label>
      <label className="text-sm font-semibold">Ý chấm (mỗi dòng một ý, 2–5 ý)<textarea className={input} rows={3} value={rubric} onChange={(e) => setRubric(e.target.value)} /></label></>}
    <label className="text-sm font-semibold">Lời giải (vì sao đáp án đúng)
      <textarea className={input} rows={2} value={q.explanation} placeholder="Câu có phần kiểm Engine thì bỏ trống được: Music Engine tự viết lời giải"
        onChange={(e) => set({ explanation: e.target.value })} /></label>
    <div className="flex flex-wrap gap-2">
      <Button loading={busy} disabled={busy || !q.prompt.trim()} onClick={submit}>Lưu và để Engine kiểm</Button>
      <Button variant="ghost" onClick={onCancel}>Hủy</Button></div>
  </div>;
}

function answerText(ex: AdminExercise) {
  const a = ex.engine_answer ?? ex.question?.answer ?? ex.question?.answers;
  return Array.isArray(a) ? a.join(" ") : a ?? "";
}

export default function ExercisesPanel({ lessonId }: { lessonId: string }) {
  const [data, setData] = useState<AdminExerciseList | null>(null);
  const [editing, setEditing] = useState<string | "new" | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const load = () => api.adminExercises(lessonId).then(setData).catch((e) => setMsg(errMsg(e)));
  useEffect(() => { load(); }, [lessonId]);
  const save = async (q: AdminQuestion) => {
    setBusy(true); setMsg(null);
    try {
      const r = editing === "new" ? await api.adminAddExercise(lessonId, q) : await api.adminUpdateExercise(editing!, q);
      setMsg(`Đã lưu câu (phiên bản ${r.version}). Đáp án theo Music Engine: ${answerText(r) || "(câu tự luận mở, chấm theo ý)"}.`);
      setEditing(null); await load();
    } catch (e) { setMsg(errMsg(e)); } finally { setBusy(false); }
  };
  const retire = async (ex: AdminExercise) => {
    if (!window.confirm("Bỏ câu này? Học sinh không thấy nữa; lượt làm cũ vẫn giữ.")) return;
    try { await api.adminRetireExercise(ex.id); setMsg("Đã bỏ câu."); await load(); } catch (e) { setMsg(errMsg(e)); }
  };
  if (!data) return <p role="status" className="text-sm text-muted">{msg ?? "Đang tải câu luyện tập…"}</p>;
  return <section className="grid gap-2" aria-label="Câu luyện tập">
    <h3 className="font-bold">Câu luyện tập ({data.exercises.length})</h3>
    {!data.editable && <p className="text-sm text-muted">Bài gốc của hệ thống: câu hỏi chỉ xem ở đây; đổi câu qua curriculum_specs để giữ lịch sử chấm (ADR-006).</p>}
    {msg && <p role="status" className="rounded-lg bg-primary-soft p-2 text-sm">{msg}</p>}
    <ul className="grid gap-2">{data.exercises.map((ex) => <li key={ex.id} className="rounded-lg border border-line p-2">
      {editing === ex.id && ex.question ? <ExerciseForm initial={ex.question} meta={data} busy={busy} onSave={save} onCancel={() => setEditing(null)} />
        : <div className="flex flex-wrap items-center justify-between gap-2">
          <div><p>{ex.question?.prompt ?? ex.prompt}</p>
            <p className="text-xs text-muted">{ex.question && <><Badge tone="muted">{KIND_VI[ex.question.kind] ?? ex.question.kind}</Badge>{" "}
              {LEVEL_VI[ex.question.level] ?? ex.question.level} · </>}{ex.skill_id} · phiên bản {ex.version}
              {answerText(ex) && ` · đáp án: ${answerText(ex)}`}</p></div>
          {data.editable && ex.question && <div className="flex gap-1">
            <Button variant="ghost" onClick={() => setEditing(ex.id)}>Sửa</Button>
            <Button variant="ghost" onClick={() => retire(ex)}>Bỏ câu</Button></div>}
        </div>}
    </li>)}</ul>
    {data.editable && (editing === "new"
      ? <ExerciseForm initial={blank(data.skills[0] ?? "")} meta={data} busy={busy} onSave={save} onCancel={() => setEditing(null)} />
      : <Button variant="secondary" onClick={() => setEditing("new")}>Thêm câu luyện tập</Button>)}
  </section>;
}

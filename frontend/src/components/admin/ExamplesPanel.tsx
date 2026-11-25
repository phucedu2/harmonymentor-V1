import { useState } from "react";
import { api } from "../../api";
import { Button } from "../ui/Button";

// FR-ADM-35..37 (Phúc 8A): thêm khối ví dụ hợp âm, âm giai (Engine tính nốt) và âm thanh (mp3/wav ≤ 5 MB, bắt buộc nguồn + giấy phép).
const errMsg = (e: unknown) => (e as { message?: string }).message ?? "Có lỗi xảy ra, thử lại sau.";
const input = "mt-1 min-h-10 w-full rounded-lg border border-line bg-surface px-3";
const SCALES: Record<string, string> = { major: "Trưởng", natural_minor: "Thứ tự nhiên", harmonic_minor: "Thứ hòa thanh",
  melodic_minor: "Thứ giai điệu", dorian: "Dorian", mixolydian: "Mixolydian" };

export default function ExamplesPanel({ lessonId, onAdded }: { lessonId: string; onAdded: () => void }) {
  const [kind, setKind] = useState<"" | "chord" | "scale" | "audio">("");
  const [f, setF] = useState({ title: "", symbol: "", tonic: "", scale_type: "major", source: "", license: "", note: "" });
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const set = (patch: Partial<typeof f>) => setF({ ...f, ...patch });
  const submit = async () => {
    setBusy(true); setMsg(null);
    try {
      if (kind === "chord") await api.adminAddChordExample(lessonId, { symbol: f.symbol, title: f.title, note: f.note });
      else if (kind === "scale") await api.adminAddScaleExample(lessonId, { tonic: f.tonic, scale_type: f.scale_type, title: f.title, note: f.note });
      else if (file) await api.adminAddAudioExample(lessonId, file, { title: f.title, source: f.source, license: f.license, note: f.note });
      setMsg("Đã thêm khối ví dụ."); setKind(""); setFile(null); setF({ ...f, title: "", symbol: "", tonic: "", note: "" }); onAdded();
    } catch (e) { setMsg(errMsg(e)); } finally { setBusy(false); }
  };
  if (!kind) return <div className="flex flex-wrap items-center gap-2" aria-label="Thêm ví dụ">
    <Button variant="secondary" onClick={() => setKind("chord")}>Thêm ví dụ hợp âm</Button>
    <Button variant="secondary" onClick={() => setKind("scale")}>Thêm ví dụ âm giai</Button>
    <Button variant="secondary" onClick={() => setKind("audio")}>Thêm ví dụ nghe (mp3/wav)</Button>
    {msg && <p role="status" className="text-sm">{msg}</p>}</div>;
  return <div className="grid gap-2 rounded-lg border border-line p-3">
    <label className="text-sm font-semibold">Tiêu đề{kind !== "audio" ? " (để trống thì máy đặt)" : ""}
      <input className={input} value={f.title} onChange={(e) => set({ title: e.target.value })} /></label>
    {kind === "chord" && <label className="text-sm font-semibold">Ký hiệu hợp âm (Music Engine tính các nốt)
      <input id="ex-symbol" className={input} placeholder="Cmaj7" value={f.symbol} onChange={(e) => set({ symbol: e.target.value })} /></label>}
    {kind === "scale" && <div className="grid gap-2 sm:grid-cols-2">
      <label className="text-sm font-semibold">Chủ âm<input id="ex-tonic" className={input} placeholder="E" value={f.tonic} onChange={(e) => set({ tonic: e.target.value })} /></label>
      <label className="text-sm font-semibold">Loại âm giai<select className={input} value={f.scale_type} onChange={(e) => set({ scale_type: e.target.value })}>
        {Object.entries(SCALES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label></div>}
    {kind === "audio" && <>
      <label className="text-sm font-semibold">File âm thanh (.mp3 hoặc .wav, tối đa 5 MB)
        <input id="ex-file" type="file" accept=".mp3,.wav,audio/mpeg,audio/wav" className={input} onChange={(e) => setFile(e.target.files?.[0] ?? null)} /></label>
      <div className="grid gap-2 sm:grid-cols-2">
        <label className="text-sm font-semibold">Nguồn (bắt buộc)<input id="ex-source" className={input} placeholder="Tự thu / tên tác giả, đường dẫn" value={f.source} onChange={(e) => set({ source: e.target.value })} /></label>
        <label className="text-sm font-semibold">Giấy phép (bắt buộc)<input id="ex-license" className={input} placeholder="CC0, CC BY 4.0, tự thu…" value={f.license} onChange={(e) => set({ license: e.target.value })} /></label></div></>}
    <label className="text-sm font-semibold">Ghi chú cho người học (không bắt buộc)
      <textarea rows={2} className={input} value={f.note} onChange={(e) => set({ note: e.target.value })} /></label>
    {msg && <p role="status" className="rounded-lg bg-primary-soft p-2 text-sm">{msg}</p>}
    <div className="flex gap-2"><Button loading={busy} disabled={busy || (kind === "audio" && (!file || !f.title.trim()))} onClick={submit}>Thêm khối</Button>
      <Button variant="ghost" onClick={() => { setKind(""); setMsg(null); }}>Hủy</Button></div>
  </div>;
}

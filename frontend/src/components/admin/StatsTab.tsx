import { useEffect, useState } from "react";
import { api, type AdminStats } from "../../api";
import { Card, CardTitle, Metric, ToggleGroup } from "../ui/Page";
import { BarList, LineChart } from "./Charts";

const pct = (v: number | null) => (v === null ? "—" : `${Math.round(v * 100)}%`);

export default function StatsTab() {
  const [days, setDays] = useState<"14" | "30" | "90">("30");
  const [data, setData] = useState<AdminStats | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => { setData(null); setFailed(false); api.adminStats(Number(days)).then(setData).catch(() => setFailed(true)); }, [days]);
  if (failed) return <p role="alert" className="text-danger">Chưa tải được thống kê.</p>;
  if (!data) return <p className="text-muted">Đang tải…</p>;
  const t = data.totals;
  const maxMastery = Math.max(1, ...data.mastery.map((m) => m.count));
  return <div className="grid gap-4">
    <ToggleGroup label="Khoảng thời gian" value={days} onChange={setDays}
      options={[{ value: "14", label: "14 ngày" }, { value: "30", label: "30 ngày" }, { value: "90", label: "90 ngày" }]} />
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <Metric value={t.learners} label="Người học" />
      <Metric value={t.active_last_7_days} label="Hoạt động 7 ngày" />
      <Metric value={pct(t.correct_rate)} label="Tỷ lệ đúng" />
      <Metric value={t.cards_due_now} label="Thẻ đến hạn" />
    </div>
    <Card className="p-4"><CardTitle>Hoạt động mỗi ngày</CardTitle><div className="mt-2"><LineChart data={data.timeline} /></div></Card>
    <Card className="p-4"><CardTitle>Phễu từng bài (bắt đầu → hoàn thành)</CardTitle><div className="mt-2">
      <BarList label="Phễu bài học" rows={data.funnel.map((f) => ({ label: f.title, value: f.completed, max: Math.max(1, f.started),
        note: `${f.completed}/${f.started} (${pct(f.completion_rate)})` }))} /></div></Card>
    <Card className="p-4"><CardTitle>Kỹ năng khó nhất (đúng ngay lần đầu)</CardTitle><div className="mt-2">
      <BarList label="Kỹ năng" color="#d97706" rows={data.skills.slice(0, 8).map((s) => ({ label: s.name, value: s.first_try_correct_rate, max: 1,
        note: `${pct(s.first_try_correct_rate)} · ${s.first_try_total} lượt` }))} /></div></Card>
    <Card className="p-4"><CardTitle>Phân bố mức thành thạo</CardTitle><div className="mt-2">
      <BarList label="Mastery" color="#16a34a" rows={data.mastery.map((m) => ({ label: m.label, value: m.count, max: maxMastery, note: String(m.count) }))} /></div></Card>
    {data.hardest_exercises.length > 0 && <Card className="p-4"><CardTitle>Câu hỏi khó nhất</CardTitle><div className="mt-2">
      <BarList label="Câu khó" color="#dc2626" rows={data.hardest_exercises.map((h) => ({ label: h.exercise_id, value: h.first_try_correct_rate, max: 1,
        note: `${pct(h.first_try_correct_rate)} · ${h.first_try_total} người` }))} /></div></Card>}
  </div>;
}

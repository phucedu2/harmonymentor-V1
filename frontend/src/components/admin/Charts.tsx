// Biểu đồ SVG thuần cho trang Quản trị. Không dùng thư viện để giữ bundle nhỏ; mọi số do backend tính.
import type { AdminStats } from "../../api";

const W = 640;

export function LineChart({ data }: { data: AdminStats["timeline"] }) {
  const H = 180, PAD = 28;
  const max = Math.max(1, ...data.map((d) => Math.max(d.attempts, d.reviews)));
  const x = (i: number) => PAD + (i * (W - PAD * 2)) / Math.max(1, data.length - 1);
  const y = (v: number) => H - PAD - (v / max) * (H - PAD * 2);
  const path = (pick: (d: AdminStats["timeline"][number]) => number) => data.map((d, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(pick(d)).toFixed(1)}`).join(" ");
  const total = data.reduce((s, d) => s + d.attempts + d.reviews, 0);
  return <figure>
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={`Lượt làm bài và ôn tập mỗi ngày, ${data.length} ngày gần nhất, tổng ${total} lượt`}>
      <line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} stroke="currentColor" opacity="0.25" />
      <text x={4} y={y(max) + 4} fontSize="11" fill="currentColor" opacity="0.7">{max}</text>
      <text x={PAD} y={H - 8} fontSize="11" fill="currentColor" opacity="0.7">{data[0]?.date.slice(5)}</text>
      <text x={W - PAD} y={H - 8} fontSize="11" textAnchor="end" fill="currentColor" opacity="0.7">{data[data.length - 1]?.date.slice(5)}</text>
      <path d={path((d) => d.attempts)} fill="none" stroke="#2563eb" strokeWidth="2" />
      <path d={path((d) => d.correct)} fill="none" stroke="#16a34a" strokeWidth="2" />
      <path d={path((d) => d.reviews)} fill="none" stroke="#d97706" strokeWidth="2" strokeDasharray="5 3" />
    </svg>
    <figcaption className="mt-1 flex flex-wrap gap-x-4 text-xs text-muted">
      <span><b style={{ color: "#2563eb" }}>―</b> Lượt làm bài</span>
      <span><b style={{ color: "#16a34a" }}>―</b> Lượt đúng</span>
      <span><b style={{ color: "#d97706" }}>- -</b> Lượt ôn thẻ</span>
    </figcaption>
  </figure>;
}

export type BarRow = { label: string; value: number; max: number; note: string };

export function BarList({ rows, label, color = "#2563eb" }: { rows: BarRow[]; label: string; color?: string }) {
  if (!rows.length) return <p className="text-sm text-muted">Chưa có dữ liệu.</p>;
  return <ul aria-label={label} className="grid gap-2">
    {rows.map((r) => <li key={r.label}>
      <div className="flex justify-between gap-2 text-sm"><span className="truncate">{r.label}</span><span className="shrink-0 text-muted">{r.note}</span></div>
      <svg viewBox="0 0 100 4" preserveAspectRatio="none" className="h-2 w-full" aria-hidden="true">
        <rect width="100" height="4" rx="1" fill="currentColor" opacity="0.12" />
        <rect width={r.max > 0 ? Math.min(100, (r.value / r.max) * 100) : 0} height="4" rx="1" fill={color} />
      </svg>
    </li>)}
  </ul>;
}

// Biểu đồ SVG thuần cho trang Quản trị. Không dùng thư viện để giữ bundle nhỏ; mọi số do backend tính.
// FE-025: màu lấy từ token theme (đổi theo sáng/tối và nhận diện) thay vì mã cứng #2563eb…; mã cứng
// cam #d97706 trên nền trắng chỉ 3,18:1 (chú thích chữ cần 4,5:1). Ba đường còn khác nét (liền, chấm, gạch)
// để người không phân biệt màu vẫn đọc được (WCAG 1.4.1).
const C = { attempts: "var(--color-primary)", correct: "var(--color-success)", reviews: "var(--color-warning)" };
import type { AdminStats } from "../../api";

const W = 640;

export function LineChart({ data }: { data: AdminStats["timeline"] }) {
  const H = 180, PAD = 28;
  const max = Math.max(1, ...data.map((d) => Math.max(d.attempts, d.reviews)));
  const x = (i: number) => PAD + (i * (W - PAD * 2)) / Math.max(1, data.length - 1);
  const y = (v: number) => H - PAD - (v / max) * (H - PAD * 2);
  const path = (pick: (d: AdminStats["timeline"][number]) => number) => data.map((d, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(pick(d)).toFixed(1)}`).join(" ");
  const total = data.reduce((s, d) => s + d.attempts + d.reviews, 0);
  // Nhãn trục viết bằng HTML chứ không bằng <text> trong SVG: SVG co theo bề ngang nên trên điện thoại
  // chữ 11 đơn vị chỉ còn khoảng 6 px, không đọc được.
  return <figure>
    <div className="flex justify-between text-xs text-muted"><span>Cao nhất: {max} lượt</span></div>
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={`Lượt làm bài và ôn tập mỗi ngày, ${data.length} ngày gần nhất, tổng ${total} lượt`}>
      <line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} stroke="currentColor" opacity="0.25" />
      <path d={path((d) => d.attempts)} fill="none" stroke={C.attempts} strokeWidth="2" />
      <path d={path((d) => d.correct)} fill="none" stroke={C.correct} strokeWidth="2.5" strokeDasharray="0.5 5" strokeLinecap="round" />
      <path d={path((d) => d.reviews)} fill="none" stroke={C.reviews} strokeWidth="2" strokeDasharray="6 4" />
    </svg>
    <div className="flex justify-between text-xs text-muted" aria-hidden="true"><span>{data[0]?.date.slice(5)}</span><span>{data[data.length - 1]?.date.slice(5)}</span></div>
    <figcaption className="mt-1 flex flex-wrap gap-x-4 text-xs text-muted">
      <span><b aria-hidden="true" style={{ color: C.attempts }}>―</b> Lượt làm bài</span>
      <span><b aria-hidden="true" style={{ color: C.correct }}>···</b> Lượt đúng</span>
      <span><b aria-hidden="true" style={{ color: C.reviews }}>- -</b> Lượt ôn thẻ</span>
    </figcaption>
  </figure>;
}

export type BarRow = { label: string; value: number; max: number; note: string };

export function BarList({ rows, label, color = "var(--color-primary)" }: { rows: BarRow[]; label: string; color?: string }) {
  if (!rows.length) return <p className="text-sm text-muted">Chưa có dữ liệu.</p>;
  return <ul aria-label={label} className="grid gap-2">
    {rows.map((r) => <li key={r.label}>
      <div className="flex justify-between gap-2 text-sm"><span className="min-w-0 truncate" title={r.label}>{r.label}</span><span className="shrink-0 text-muted">{r.note}</span></div>
      <svg viewBox="0 0 100 4" preserveAspectRatio="none" className="h-2 w-full" aria-hidden="true">
        <rect width="100" height="4" rx="1" fill="currentColor" opacity="0.12" />
        <rect width={r.max > 0 ? Math.min(100, (r.value / r.max) * 100) : 0} height="4" rx="1" fill={color} />
      </svg>
    </li>)}
  </ul>;
}

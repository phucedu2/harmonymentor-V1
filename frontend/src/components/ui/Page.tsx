// Khối giao diện dùng chung cho khu học (phuc-music Bước 3), thay các class CSS cũ trong styles.css.
import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";

export function PageHeading({ eyebrow, title, children }: { eyebrow: string; title: ReactNode; children?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-col gap-2 md:flex-row md:items-end md:justify-between md:gap-8">
      <div>
        <p className="text-xs font-semibold tracking-[0.14em] text-primary uppercase">{eyebrow}</p>
        <h1 className="mt-1 font-display text-3xl leading-tight font-semibold text-ink">{title}</h1>
      </div>
      {children && <div className="max-w-xl text-base leading-relaxed text-muted">{children}</div>}
    </header>
  );
}

export function Card({ className = "", ...rest }: HTMLAttributes<HTMLElement>) {
  return <article className={`rounded-2xl border border-line bg-surface p-5 shadow-[0_1px_2px_rgb(12_35_31/0.04)] ${className}`} {...rest} />;
}

export function Kicker({ children }: { children: ReactNode }) {
  return <p className="text-xs font-semibold tracking-[0.1em] text-primary uppercase">{children}</p>;
}

export function CardTitle({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <h2 className={`font-display text-xl font-semibold text-ink ${className}`}>{children}</h2>;
}

// Thanh tiến độ có nhãn chữ cho trình đọc màn hình, không chỉ dựa vào độ dài màu.
export function ProgressBar({ value, label, className = "" }: { value: number; label: string; className?: string }) {
  const pct = Math.max(0, Math.min(100, Math.round(value)));
  return (
    <div className={`h-2 overflow-hidden rounded-full bg-primary-soft ${className}`} role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct}>
      <span className="block h-full rounded-full bg-primary transition-[width]" style={{ width: `${pct}%` }} />
    </div>
  );
}

type BadgeTone = "primary" | "success" | "muted" | "warning";
const badgeTones: Record<BadgeTone, string> = {
  primary: "bg-primary-soft text-primary-strong",
  success: "bg-success-soft text-success",
  muted: "bg-bg text-muted border border-line",
  warning: "bg-warning-soft text-warning",
};

export function Badge({ tone = "primary", children, className = "" }: { tone?: BadgeTone; children: ReactNode; className?: string }) {
  return <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${badgeTones[tone]} ${className}`}>{children}</span>;
}

export function Metric({ value, label }: { value: ReactNode; label: string }) {
  return (
    <Card className="flex flex-col gap-1">
      <span className="font-display text-3xl font-semibold text-ink">{value}</span>
      <span className="text-sm text-muted">{label}</span>
    </Card>
  );
}

// Nhóm nút chọn một (mức độ, dạng bài, cách xem bài). Dùng aria-pressed để trình đọc màn hình biết nút đang bật.
export function ToggleGroup<T extends string>({ label, options, value, onChange, className = "" }: {
  label: string; options: { value: T; label: ReactNode }[]; value: T; onChange: (value: T) => void; className?: string;
}) {
  return (
    <div role="group" aria-label={label} className={`flex flex-wrap gap-2 ${className}`}>
      {options.map((option) => (
        <ChipButton key={option.value} pressed={value === option.value} onClick={() => onChange(option.value)}>{option.label}</ChipButton>
      ))}
    </div>
  );
}

export function ChipButton({ pressed, className = "", ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & { pressed: boolean }) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      className={`min-h-11 rounded-full border px-4 py-2 text-sm font-semibold transition-colors ${pressed ? "border-primary bg-primary text-white" : "border-line bg-surface text-ink hover:border-primary hover:text-primary"} ${className}`}
      {...rest}
    />
  );
}

// Kết quả chấm: luôn có biểu tượng + chữ "Chính xác"/"Chưa đúng", không chỉ đổi màu.
export function ResultBox({ correct, title, children }: { correct: boolean; title?: ReactNode; children?: ReactNode }) {
  return (
    <div role="status" className={`mt-3 rounded-xl border px-4 py-3 text-sm leading-relaxed ${correct ? "border-success/40 bg-success-soft text-ink" : "border-danger/40 bg-danger-soft text-ink"}`}>
      <p className={`font-semibold ${correct ? "text-success" : "text-danger"}`}><span aria-hidden="true">{correct ? "✓ " : "✗ "}</span>{title ?? (correct ? "Chính xác!" : "Chưa đúng.")}</p>
      {children && <div className="mt-1 space-y-1">{children}</div>}
    </div>
  );
}

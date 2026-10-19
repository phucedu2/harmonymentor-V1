import type { ReactNode } from "react";

type Tone = "danger" | "success" | "info";
const tones: Record<Tone, { box: string; icon: string }> = {
  danger: { box: "border-danger/40 bg-danger-soft text-danger", icon: "✗" },
  success: { box: "border-success/40 bg-success-soft text-success", icon: "✓" },
  info: { box: "border-primary/30 bg-primary-soft text-primary-strong", icon: "i" },
};

// Luôn có biểu tượng + chữ, không truyền thông tin chỉ bằng màu.
export function Alert({ tone = "info", children, action }: { tone?: Tone; children: ReactNode; action?: ReactNode }) {
  const t = tones[tone];
  return (
    <div role={tone === "danger" ? "alert" : "status"} className={`flex items-start gap-3 rounded-lg border px-4 py-3 text-sm ${t.box}`}>
      <span aria-hidden="true" className="font-bold">{t.icon}</span>
      <div className="flex-1">{children}</div>
      {action}
    </div>
  );
}

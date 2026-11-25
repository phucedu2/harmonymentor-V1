import { passwordRules, passwordStrength } from "../../../auth/authApi";

const BAR = ["bg-line", "bg-danger", "bg-warning", "bg-success"] as const;
const TEXT = ["text-muted", "text-danger", "text-warning", "text-success"] as const;

/** Thước đo độ mạnh + danh sách điều kiện (B3). Luôn có chữ đi kèm màu, không báo chỉ bằng màu. */
export function PasswordStrength({ password, email = "" }: { password: string; email?: string }) {
  const rules = passwordRules(password, email);
  const strength = passwordStrength(password, email);
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <div className="flex flex-1 gap-1" aria-hidden="true">
          {[1, 2, 3].map((step) => (
            <span key={step} className={`h-1.5 flex-1 rounded-full transition-colors ${strength.score >= step ? BAR[strength.score] : "bg-line"}`} />
          ))}
        </div>
        <span className={`min-w-10 text-right text-xs font-semibold ${TEXT[strength.score]}`} aria-live="polite">
          {strength.label && <><span className="sr-only">Độ mạnh mật khẩu: </span>{strength.label}</>}
        </span>
      </div>
      <ul className="space-y-0.5" aria-label="Điều kiện mật khẩu">
        {rules.map((r) => (
          <li key={r.label} className={r.ok ? "text-success" : "text-muted"}>
            <span aria-hidden="true">{r.ok ? "✓" : "○"}</span> {r.label}
            <span className="sr-only">{r.ok ? " (đã đạt)" : " (chưa đạt)"}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

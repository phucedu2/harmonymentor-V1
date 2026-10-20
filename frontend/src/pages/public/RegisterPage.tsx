import { useState, type ChangeEvent, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router";
import { useAuth } from "../../auth/AuthProvider";
import { passwordRules, safeNext } from "../../auth/authApi";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { AuthCard } from "./AuthCard";
import { authErrorMessage, fieldErrors } from "./authErrors";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function RegisterPage() {
  const { status, register } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = safeNext(params.get("next"));
  const [form, setForm] = useState({ display_name: "", email: "", password: "", confirm: "" });
  const [touched, setTouched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [serverFields, setServerFields] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  if (status === "authenticated" && !submitting) return <Navigate to={next} replace />;

  const rules = passwordRules(form.password);
  // Lỗi phía trình duyệt chỉ hiện sau lần bấm Đăng ký đầu tiên, tránh báo đỏ khi người dùng chưa gõ xong.
  const local: Record<string, string> = {};
  if (!form.display_name.trim()) local.display_name = "Hãy nhập tên hiển thị.";
  if (!EMAIL_RE.test(form.email.trim())) local.email = "Email chưa đúng định dạng.";
  if (!rules.every((r) => r.ok)) local.password = "Mật khẩu chưa đủ điều kiện bên dưới.";
  if (form.confirm !== form.password) local.confirm = "Hai mật khẩu chưa khớp.";
  const shown = { ...(touched ? local : {}), ...serverFields };

  const set = (key: keyof typeof form) => (e: ChangeEvent<HTMLInputElement>) => {
    setForm((f) => ({ ...f, [key]: e.target.value }));
    setServerFields((s) => { const { [key]: _removed, ...rest } = s; return rest; });
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setTouched(true);
    setError(null);
    if (Object.keys(local).length > 0) return;
    setSubmitting(true);
    try {
      await register({ display_name: form.display_name.trim(), email: form.email.trim(), password: form.password });
      navigate(next, { replace: true });
    } catch (err) {
      setError(authErrorMessage(err));
      setServerFields(fieldErrors(err));
      setSubmitting(false);
    }
  };

  return (
    <AuthCard
      title="Tạo tài khoản"
      subtitle="Miễn phí. Tiến độ học của bạn được lưu theo tài khoản."
      footer={<>Đã có tài khoản? <Link to={`/dang-nhap${params.get("next") ? `?next=${encodeURIComponent(next)}` : ""}`} className="font-medium text-primary hover:underline">Đăng nhập</Link></>}
    >
      <form onSubmit={submit} className="space-y-4" noValidate>
        {error && <Alert tone="danger">{error}</Alert>}
        <TextField label="Tên hiển thị" autoComplete="nickname" value={form.display_name} onChange={set("display_name")} error={shown.display_name} />
        <TextField label="Email" type="email" autoComplete="email" value={form.email} onChange={set("email")} error={shown.email} />
        <TextField
          label="Mật khẩu"
          type="password"
          autoComplete="new-password"
          value={form.password}
          onChange={set("password")}
          error={shown.password}
          hint={
            <ul className="space-y-0.5" aria-label="Điều kiện mật khẩu">
              {rules.map((r) => (
                <li key={r.label} className={r.ok ? "text-success" : "text-muted"}>
                  <span aria-hidden="true">{r.ok ? "✓" : "○"}</span> {r.label}
                  <span className="sr-only">{r.ok ? " (đã đạt)" : " (chưa đạt)"}</span>
                </li>
              ))}
            </ul>
          }
        />
        <TextField label="Nhập lại mật khẩu" type="password" autoComplete="new-password" value={form.confirm} onChange={set("confirm")} error={shown.confirm} />
        <Button type="submit" size="lg" className="w-full" loading={submitting}>Đăng ký</Button>
      </form>
    </AuthCard>
  );
}

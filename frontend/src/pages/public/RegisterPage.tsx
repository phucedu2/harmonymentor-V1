import { useState, type ChangeEvent, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router";
import { useAuth } from "../../auth/AuthProvider";
import { passwordRules, safeNext } from "../../auth/authApi";
import { Button } from "../../components/ui/Button";
import { PasswordField } from "../../components/ui/PasswordField";
import { TextField } from "../../components/ui/TextField";
import { AuthLayout } from "./auth/AuthLayout";
import { CheckInbox } from "./auth/CheckInbox";
import { FormError } from "./auth/FormError";
import { PasswordStrength } from "./auth/PasswordStrength";
import { authErrorMessage, fieldErrors } from "./authErrors";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function RegisterPage() {
  const { status, register } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = safeNext(params.get("next"));
  const [form, setForm] = useState({ display_name: "", email: "", password: "" });
  const [touched, setTouched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [serverFields, setServerFields] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [pendingEmail, setPendingEmail] = useState<string | null>(null);

  if (status === "authenticated" && !submitting) return <Navigate to={next} replace />;

  if (pendingEmail) {
    // 1A (ADR-040): email đã có tài khoản. Không nói thẳng điều đó; chủ email nhận thư hướng dẫn.
    return (
      <AuthLayout title="Kiểm tra hộp thư của bạn">
        <CheckInbox email={pendingEmail} body="Chúng tôi đã gửi thư tới địa chỉ này. Hãy mở thư và làm theo hướng dẫn để tiếp tục." />
      </AuthLayout>
    );
  }

  const rules = passwordRules(form.password, form.email);
  // Lỗi phía trình duyệt chỉ hiện sau lần bấm Đăng ký đầu tiên, tránh báo đỏ khi người dùng chưa gõ xong.
  const local: Record<string, string> = {};
  if (!form.display_name.trim()) local.display_name = "Hãy nhập tên bạn muốn hiển thị.";
  if (!EMAIL_RE.test(form.email.trim())) local.email = "Email chưa đúng định dạng, ví dụ ten@gmail.com.";
  if (!rules.every((r) => r.ok)) local.password = "Mật khẩu chưa đủ các điều kiện bên dưới.";
  const shown = { ...(touched ? local : {}), ...serverFields };

  const set = (key: keyof typeof form) => (e: ChangeEvent<HTMLInputElement>) => {
    setForm((f) => ({ ...f, [key]: e.target.value }));
    setServerFields((s) => { const { [key]: _removed, ...rest } = s; return rest; });
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setTouched(true);
    setError(null);
    if (Object.keys(local).length > 0) { setError("Bạn xem lại các ô được đánh dấu nhé."); return; }
    setSubmitting(true);
    try {
      const result = await register({ display_name: form.display_name.trim(), email: form.email.trim(), password: form.password });
      if ("status" in result) { setPendingEmail(form.email.trim()); setSubmitting(false); return; }
      // UC-06: người mới đăng ký được mời làm bài kiểm tra đầu vào (bỏ qua được), trừ khi đang đi tới trang khác.
      navigate(next === "/app" ? "/app/kiem-tra-dau-vao" : next, { replace: true });
    } catch (err) {
      setError(authErrorMessage(err));
      setServerFields(fieldErrors(err));
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Tạo tài khoản"
      subtitle="Miễn phí. Tiến độ học của bạn được lưu theo tài khoản."
      footer={<>Đã có tài khoản? <Link to={`/dang-nhap${params.get("next") ? `?next=${encodeURIComponent(next)}` : ""}`} className="font-medium text-primary hover:underline">Đăng nhập</Link></>}
    >
      <form onSubmit={submit} className="space-y-5" noValidate>
        <FormError message={error} />
        <TextField label="Tên hiển thị" autoComplete="nickname" autoFocus value={form.display_name} onChange={set("display_name")} error={shown.display_name} />
        <TextField label="Email" type="email" inputMode="email" autoComplete="email" autoCapitalize="none" spellCheck={false}
          value={form.email} onChange={set("email")} error={shown.email} />
        <PasswordField
          label="Mật khẩu"
          autoComplete="new-password"
          value={form.password}
          onChange={set("password")}
          error={shown.password}
          hint={<PasswordStrength password={form.password} email={form.email} />}
        />
        <Button type="submit" size="lg" className="w-full" loading={submitting}>Tạo tài khoản</Button>
        <p className="text-center text-xs text-muted">
          Khi tạo tài khoản, bạn đồng ý dùng HarmonyMentor cho việc học và để chúng tôi lưu tiến độ học của bạn.
          Chúng tôi không bao giờ hỏi mật khẩu qua email.
        </p>
      </form>
    </AuthLayout>
  );
}

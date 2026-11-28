import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { authApi, passwordRules, takeTokenFromHash } from "../../auth/authApi";
import { Button, ButtonLink } from "../../components/ui/Button";
import { PageLoader } from "../../components/ui/PageLoader";
import { PasswordField } from "../../components/ui/PasswordField";
import { ApiRequestError } from "../../lib/http";
import { AuthLayout } from "./auth/AuthLayout";
import { FormError } from "./auth/FormError";
import { PasswordStrength } from "./auth/PasswordStrength";
import { useNoReferrer } from "./auth/useNoReferrer";

type Phase = { kind: "checking" } | { kind: "invalid" } | { kind: "ready"; emailMasked: string };

/** B6: đọc token sau # rồi xóa khỏi thanh địa chỉ, hỏi máy chủ token còn dùng được không trước khi cho gõ mật khẩu. */
export default function ResetPasswordPage() {
  useNoReferrer();
  const navigate = useNavigate();
  const token = useRef<string | null>(null);
  const [phase, setPhase] = useState<Phase>({ kind: "checking" });
  const [password, setPassword] = useState("");
  const [touched, setTouched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | undefined>();
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // StrictMode chạy effect 2 lần; giữ token ở ref để lần sau không đọc lại hash đã xóa.
    if (token.current === null) token.current = takeTokenFromHash();
    if (!token.current) { setPhase({ kind: "invalid" }); return; }
    let alive = true;
    authApi.checkResetToken(token.current)
      .then((r) => { if (alive) setPhase({ kind: "ready", emailMasked: r.email_masked }); })
      .catch(() => { if (alive) setPhase({ kind: "invalid" }); });
    return () => { alive = false; };
  }, []);

  if (phase.kind === "checking") return <PageLoader label="Đang kiểm tra liên kết…" />;

  if (phase.kind === "invalid") {
    return (
      <AuthLayout title="Liên kết đã hết hạn hoặc đã được dùng">
        <div className="space-y-5" role="status">
          <p>Vì an toàn, mỗi liên kết đặt lại mật khẩu chỉ dùng được một lần và trong 30 phút. Bạn có thể xin một liên kết mới.</p>
          <ButtonLink to="/quen-mat-khau" size="lg" className="w-full">Gửi liên kết mới</ButtonLink>
          <ButtonLink to="/dang-nhap" variant="secondary" className="w-full">Quay lại đăng nhập</ButtonLink>
        </div>
      </AuthLayout>
    );
  }

  const rulesOk = passwordRules(password).every((r) => r.ok);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setTouched(true);
    setError(null);
    if (!rulesOk) { setFieldError("Mật khẩu chưa đủ các điều kiện bên dưới."); return; }
    setFieldError(undefined);
    setSubmitting(true);
    try {
      await authApi.resetPassword(token.current ?? "", password);
      navigate("/dang-nhap?da-dat-lai=1", { replace: true });
    } catch (err) {
      if (err instanceof ApiRequestError && err.code === "RESET_TOKEN_INVALID") { setPhase({ kind: "invalid" }); return; }
      const fields = err instanceof ApiRequestError ? err.fields : undefined;
      if (fields?.new_password) setFieldError(fields.new_password);
      else setError(err instanceof ApiRequestError ? err.message : "Có lỗi không mong muốn. Bạn thử lại nhé.");
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout title="Đặt mật khẩu mới" subtitle={<>Cho tài khoản <span className="font-medium text-ink">{phase.emailMasked}</span>.</>}>
      <form onSubmit={submit} className="space-y-5" noValidate>
        <FormError message={error} />
        <PasswordField
          label="Mật khẩu mới"
          autoComplete="new-password"
          autoFocus
          value={password}
          onChange={(e) => { setPassword(e.target.value); if (touched) setFieldError(undefined); }}
          error={fieldError}
          hint={<PasswordStrength password={password} />}
        />
        <p className="text-sm text-muted">Sau khi đổi, mọi thiết bị đang đăng nhập sẽ được đăng xuất để bảo vệ tài khoản.</p>
        <Button type="submit" size="lg" className="w-full" loading={submitting}>Lưu mật khẩu mới</Button>
      </form>
    </AuthLayout>
  );
}

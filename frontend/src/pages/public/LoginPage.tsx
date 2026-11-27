import { useEffect, useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router";
import { useAuth } from "../../auth/AuthProvider";
import { safeNext } from "../../auth/authApi";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { PasswordField } from "../../components/ui/PasswordField";
import { TextField } from "../../components/ui/TextField";
import { ApiRequestError } from "../../lib/http";
import { AuthLayout } from "./auth/AuthLayout";
import { FormError } from "./auth/FormError";
import { authErrorMessage } from "./authErrors";

export default function LoginPage() {
  const { status, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const next = safeNext(params.get("next"));
  const justReset = params.get("da-dat-lai") === "1";
  // Email truyền qua state điều hướng (không qua URL) để không nằm trong lịch sử hay log máy chủ.
  const [email, setEmail] = useState<string>((location.state as { email?: string } | null)?.email ?? "");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lockedFor, setLockedFor] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  // B4: đếm ngược theo Retry-After khi bị khóa vì sai quá nhiều lần.
  useEffect(() => {
    if (lockedFor <= 0) return;
    const timer = window.setTimeout(() => setLockedFor((s) => s - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [lockedFor]);

  if (status === "authenticated" && !submitting) return <Navigate to={next} replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email.trim() || !password) { setError("Hãy nhập email và mật khẩu."); return; }
    setSubmitting(true);
    try {
      await login(email.trim(), password, remember);
      navigate(next, { replace: true });
    } catch (err) {
      if (err instanceof ApiRequestError && err.code === "LOGIN_LOCKED") setLockedFor(err.retryAfterSeconds ?? 900);
      setError(authErrorMessage(err));
      setPassword("");
      setSubmitting(false);
    }
  };

  const nextQuery = params.get("next") ? `?next=${encodeURIComponent(next)}` : "";
  const minutes = Math.floor(lockedFor / 60);
  const seconds = String(lockedFor % 60).padStart(2, "0");

  return (
    <AuthLayout
      title="Đăng nhập"
      subtitle={params.get("next") ? "Bạn cần đăng nhập để mở trang này." : "Chào mừng bạn quay lại."}
      footer={<>Chưa có tài khoản? <Link to={`/dang-ky${nextQuery}`} className="font-medium text-primary hover:underline">Tạo tài khoản</Link></>}
    >
      <form onSubmit={submit} className="space-y-5" noValidate>
        {justReset && !error && <Alert tone="success">Đã đặt lại mật khẩu. Hãy đăng nhập bằng mật khẩu mới.</Alert>}
        <FormError message={error} />
        {lockedFor > 0 && (
          <p className="text-sm text-muted" aria-live="polite">Thử lại sau <span className="font-mono font-semibold text-ink">{minutes}:{seconds}</span></p>
        )}
        <TextField label="Email" type="email" inputMode="email" autoComplete="email" autoCapitalize="none" spellCheck={false}
          autoFocus required value={email} onChange={(e) => setEmail(e.target.value)} />
        <PasswordField
          label="Mật khẩu"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          labelAction={
            <Link to="/quen-mat-khau" state={{ email: email.trim() }} className="text-sm font-medium text-primary hover:underline">
              Quên mật khẩu?
            </Link>
          }
        />
        <label className="flex min-h-11 cursor-pointer items-center gap-3 text-sm">
          <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="size-5 accent-primary" />
          <span>Ghi nhớ đăng nhập trên thiết bị này<span className="block text-xs text-muted">Bỏ chọn nếu đây là máy dùng chung.</span></span>
        </label>
        <Button type="submit" size="lg" className="w-full" loading={submitting} disabled={lockedFor > 0}>Đăng nhập</Button>
      </form>
    </AuthLayout>
  );
}

import { useEffect, useState, type FormEvent } from "react";
import { Link, useLocation } from "react-router";
import { authApi } from "../../auth/authApi";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { ApiRequestError } from "../../lib/http";
import { AuthLayout } from "./auth/AuthLayout";
import { CheckInbox } from "./auth/CheckInbox";
import { FormError } from "./auth/FormError";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const RESEND_SECONDS = 60;

function friendly(err: unknown): string {
  if (err instanceof ApiRequestError && err.status === 429) {
    const minutes = Math.max(1, Math.ceil((err.retryAfterSeconds ?? 600) / 60));
    return `Bạn đã yêu cầu nhiều lần. Hãy thử lại sau khoảng ${minutes} phút.`;
  }
  if (err instanceof ApiRequestError) return err.message;
  return "Có lỗi không mong muốn. Bạn thử lại nhé.";
}

/** B5: một ô email → màn "Kiểm tra hộp thư". Máy chủ luôn trả cùng một câu, nên trang không biết email có tài khoản hay không. */
export default function ForgotPasswordPage() {
  const location = useLocation();
  const [email, setEmail] = useState<string>((location.state as { email?: string } | null)?.email ?? "");
  const [sentTo, setSentTo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | undefined>();
  const [submitting, setSubmitting] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [resent, setResent] = useState(false);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = window.setTimeout(() => setCooldown((s) => s - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [cooldown]);

  const send = async (address: string) => {
    await authApi.forgotPassword(address);
    setSentTo(address);
    setCooldown(RESEND_SECONDS);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    const address = email.trim();
    if (!EMAIL_RE.test(address)) { setFieldError("Email chưa đúng định dạng, ví dụ ten@gmail.com."); return; }
    setFieldError(undefined);
    setSubmitting(true);
    try { await send(address); } catch (err) { setError(friendly(err)); } finally { setSubmitting(false); }
  };

  const resend = async () => {
    if (!sentTo) return;
    setError(null);
    setResent(false);
    setSubmitting(true);
    try { await send(sentTo); setResent(true); } catch (err) { setError(friendly(err)); } finally { setSubmitting(false); }
  };

  if (sentTo) {
    return (
      <AuthLayout title="Kiểm tra hộp thư của bạn">
        <CheckInbox email={sentTo} body="Nếu email này có tài khoản HarmonyMentor, chúng tôi đã gửi một liên kết để bạn đặt mật khẩu mới. Liên kết dùng được trong 30 phút.">
          <FormError message={error} />
          {resent && !error && <p className="text-sm text-success" role="status">✓ Đã gửi lại liên kết mới.</p>}
          <Button variant="ghost" className="w-full" onClick={resend} loading={submitting} disabled={cooldown > 0}>
            {cooldown > 0 ? `Gửi lại sau ${cooldown} giây` : "Gửi lại liên kết"}
          </Button>
          <button type="button" className="w-full text-sm text-primary hover:underline" onClick={() => { setSentTo(null); setResent(false); }}>
            Dùng email khác
          </button>
        </CheckInbox>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Quên mật khẩu?"
      subtitle="Nhập email bạn dùng để đăng nhập. Chúng tôi sẽ gửi một liên kết để bạn đặt mật khẩu mới."
      footer={<>Nhớ ra rồi? <Link to="/dang-nhap" state={{ email: email.trim() }} className="font-medium text-primary hover:underline">Quay lại đăng nhập</Link></>}
    >
      <form onSubmit={submit} className="space-y-5" noValidate>
        <FormError message={error} />
        <TextField label="Email" type="email" inputMode="email" autoComplete="email" autoCapitalize="none" spellCheck={false}
          autoFocus value={email} onChange={(e) => setEmail(e.target.value)} error={fieldError} />
        <Button type="submit" size="lg" className="w-full" loading={submitting}>Gửi liên kết đặt lại</Button>
      </form>
    </AuthLayout>
  );
}

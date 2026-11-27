import { useState, type FormEvent } from "react";
import { useAuth } from "../../../auth/AuthProvider";
import { authApi, passwordRules } from "../../../auth/authApi";
import { Alert } from "../../../components/ui/Alert";
import { Button } from "../../../components/ui/Button";
import { PasswordField } from "../../../components/ui/PasswordField";
import { ApiRequestError, type User } from "../../../lib/http";
import { FormError } from "../../public/auth/FormError";
import { PasswordStrength } from "../../public/auth/PasswordStrength";
import { authErrorMessage } from "../../public/authErrors";

const DATE = new Intl.DateTimeFormat("vi-VN", { dateStyle: "long", timeStyle: "short" });

/** B7: đổi mật khẩu khi đang đăng nhập. Thành công thì máy chủ cấp phiên mới cho thiết bị này (ADR-040 A6). */
export function SecurityCard({ user, onChanged }: { user: User; onChanged: () => void }) {
  const { adoptSession } = useAuth();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [signOutOthers, setSignOutOthers] = useState(true);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setDone(null);
    const local: Record<string, string> = {};
    if (!current) local.current_password = "Hãy nhập mật khẩu hiện tại.";
    if (!passwordRules(next, user.email).every((r) => r.ok)) local.new_password = "Mật khẩu mới chưa đủ các điều kiện bên dưới.";
    setFields(local);
    if (Object.keys(local).length) return;
    setSubmitting(true);
    try {
      const session = await authApi.changePassword(current, next, signOutOthers);
      adoptSession(session);
      setCurrent("");
      setNext("");
      setDone(signOutOthers ? "Đã đổi mật khẩu. Các thiết bị khác đã được đăng xuất." : "Đã đổi mật khẩu.");
      onChanged();
    } catch (err) {
      if (err instanceof ApiRequestError && err.fields) setFields(err.fields);
      else setError(authErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const changedAt = user.password_changed_at ? DATE.format(new Date(user.password_changed_at)) : null;
  return (
    <section aria-labelledby="bao-mat" className="mt-6 rounded-xl border border-line bg-surface p-5">
      <h2 id="bao-mat" className="text-lg font-semibold">Bảo mật</h2>
      <p className="mt-1 text-sm text-muted">{changedAt ? `Mật khẩu đổi lần cuối: ${changedAt}.` : "Bạn chưa đổi mật khẩu kể từ khi tạo tài khoản."}</p>
      <form onSubmit={submit} className="mt-5 space-y-5" noValidate>
        {done && <Alert tone="success">{done}</Alert>}
        <FormError message={error} />
        <PasswordField label="Mật khẩu hiện tại" autoComplete="current-password" value={current}
          onChange={(e) => setCurrent(e.target.value)} error={fields.current_password} />
        <PasswordField label="Mật khẩu mới" autoComplete="new-password" value={next}
          onChange={(e) => setNext(e.target.value)} error={fields.new_password}
          hint={<PasswordStrength password={next} email={user.email} />} />
        <label className="flex min-h-11 cursor-pointer items-center gap-3 text-sm">
          <input type="checkbox" checked={signOutOthers} onChange={(e) => setSignOutOthers(e.target.checked)} className="size-5 accent-primary" />
          <span>Đăng xuất khỏi các thiết bị khác<span className="block text-xs text-muted">Nên bật nếu bạn nghi có người khác biết mật khẩu cũ.</span></span>
        </label>
        <Button type="submit" loading={submitting}>Đổi mật khẩu</Button>
      </form>
    </section>
  );
}

/** Banner nhắc xác minh email (A7, mức mềm: vẫn học bình thường). */
export function VerifyEmailBanner() {
  const [state, setState] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [message, setMessage] = useState("");
  const resend = async () => {
    setState("sending");
    try {
      const r = await authApi.resendVerification();
      setMessage(r.message);
      setState("sent");
    } catch (err) {
      setMessage(authErrorMessage(err));
      setState("error");
    }
  };
  return (
    <div className="mt-6">
      <Alert
        tone={state === "error" ? "danger" : "info"}
        action={state !== "sent" ? <Button variant="ghost" onClick={resend} loading={state === "sending"}>Gửi lại thư</Button> : undefined}
      >
        {state === "idle" || state === "sending"
          ? "Hãy xác minh email để luôn lấy lại được tài khoản khi quên mật khẩu. Mở thư “Verify your email” trong hộp thư của bạn."
          : message}
      </Alert>
    </div>
  );
}

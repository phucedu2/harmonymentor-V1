import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router";
import { useAuth } from "../../auth/AuthProvider";
import { safeNext } from "../../auth/authApi";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { AuthCard } from "./AuthCard";
import { authErrorMessage } from "./authErrors";

export default function LoginPage() {
  const { status, login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = safeNext(params.get("next"));
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === "authenticated" && !submitting) return <Navigate to={next} replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email.trim(), password);
      navigate(next, { replace: true });
    } catch (err) {
      setError(authErrorMessage(err));
      setSubmitting(false);
    }
  };

  return (
    <AuthCard
      title="Đăng nhập"
      subtitle={params.get("next") ? "Bạn cần đăng nhập để mở trang này." : "Chào mừng bạn quay lại."}
      footer={<>Chưa có tài khoản? <Link to={`/dang-ky${params.get("next") ? `?next=${encodeURIComponent(next)}` : ""}`} className="font-medium text-primary hover:underline">Đăng ký</Link></>}
    >
      <form onSubmit={submit} className="space-y-4" noValidate>
        {error && <Alert tone="danger">{error}</Alert>}
        <TextField label="Email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <TextField label="Mật khẩu" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        <Button type="submit" size="lg" className="w-full" loading={submitting} disabled={!email || !password}>Đăng nhập</Button>
      </form>
    </AuthCard>
  );
}

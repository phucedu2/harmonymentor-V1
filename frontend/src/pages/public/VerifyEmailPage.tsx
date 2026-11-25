import { useEffect, useRef, useState } from "react";
import { useAuth } from "../../auth/AuthProvider";
import { authApi, takeTokenFromHash } from "../../auth/authApi";
import { ButtonLink } from "../../components/ui/Button";
import { PageLoader } from "../../components/ui/PageLoader";
import { AuthLayout } from "./auth/AuthLayout";
import { useNoReferrer } from "./auth/useNoReferrer";

/** Mở từ liên kết trong thư "Verify your email" (A7). Dùng được cả khi chưa đăng nhập trên thiết bị này. */
export default function VerifyEmailPage() {
  useNoReferrer();
  const { status, user, setUser } = useAuth();
  const token = useRef<string | null>(null);
  // Gọi đúng một lần: liên kết dùng một lần, StrictMode chạy effect hai lần sẽ làm lần thứ hai báo "hết hạn".
  const request = useRef<Promise<unknown> | null>(null);
  const [result, setResult] = useState<"checking" | "ok" | "invalid">("checking");

  useEffect(() => {
    if (token.current === null) token.current = takeTokenFromHash();
    if (!token.current) { setResult("invalid"); return; }
    let alive = true;
    request.current ??= authApi.verifyEmail(token.current);
    request.current
      .then(() => { if (alive) setResult("ok"); })
      .catch(() => { if (alive) setResult("invalid"); });
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    if (result === "ok" && user && !user.email_verified) setUser({ ...user, email_verified: true });
  }, [result, user, setUser]);

  if (result === "checking") return <PageLoader label="Đang xác minh email…" />;
  const home = status === "authenticated" ? "/app" : "/dang-nhap";
  if (result === "ok") {
    return (
      <AuthLayout title="Đã xác minh email">
        <div className="space-y-5" role="status">
          <p>Cảm ơn bạn! Từ giờ bạn luôn lấy lại được tài khoản qua email này.</p>
          <ButtonLink to={home} size="lg" className="w-full">{status === "authenticated" ? "Tiếp tục học" : "Đăng nhập"}</ButtonLink>
        </div>
      </AuthLayout>
    );
  }
  return (
    <AuthLayout title="Liên kết đã hết hạn hoặc đã được dùng">
      <div className="space-y-5" role="status">
        <p>Liên kết xác minh chỉ dùng được một lần và trong 24 giờ. Bạn có thể gửi lại thư xác minh ở trang Hồ sơ.</p>
        <ButtonLink to={status === "authenticated" ? "/app/ho-so" : "/dang-nhap"} size="lg" className="w-full">
          {status === "authenticated" ? "Mở trang Hồ sơ" : "Đăng nhập"}
        </ButtonLink>
      </div>
    </AuthLayout>
  );
}

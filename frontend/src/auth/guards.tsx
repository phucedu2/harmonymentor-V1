import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { PageLoader } from "../components/ui/PageLoader";
import { ButtonLink } from "../components/ui/Button";
import { useAuth } from "./AuthProvider";

/** FR-VIS-07: chưa đăng nhập mà mở /app/* thì sang trang đăng nhập, nhớ trang định vào. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  const location = useLocation();
  if (status === "loading") return <PageLoader label="Đang kiểm tra đăng nhập…" />;
  if (status === "anonymous") {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/dang-nhap?next=${next}`} replace />;
  }
  return <>{children}</>;
}

/** FR-AUTH-09: người học vào /admin thấy thông báo 403. Backend vẫn tự chặn /admin/* bằng 403;
 *  đây chỉ là lớp giao diện, không thay được kiểm tra ở server. */
export function RequireAdmin({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user?.role !== "admin") {
    return (
      <section className="mx-auto max-w-lg py-16 text-center">
        <p className="font-mono text-sm text-muted">403</p>
        <h1 className="mt-2 text-2xl font-bold">Bạn không có quyền vào trang quản trị</h1>
        <p className="mt-3 text-muted">Trang này chỉ dành cho Quản trị viên. Nếu bạn cần quyền này, hãy liên hệ nhóm phát triển.</p>
        <ButtonLink to="/app" className="mt-6">Về trang tổng quan</ButtonLink>
      </section>
    );
  }
  return <>{children}</>;
}

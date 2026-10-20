import { Suspense, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router";
import { useAuth } from "../../auth/AuthProvider";
import { Button } from "../ui/Button";
import { PageLoader } from "../ui/PageLoader";
import { Logo } from "./Logo";

// Chỉ liệt kê màn đã có thật; Ôn tập, Mục tiêu, Tutor thêm vào khi Giai đoạn C–E xong.
const NAV = [
  { to: "/app", label: "Tổng quan", end: true },
  { to: "/app/hoc", label: "Học" },
  { to: "/app/luyen-tap", label: "Luyện tập" },
  { to: "/app/tien-do", label: "Tiến độ" },
  { to: "/app/composition", label: "Sáng tác" },
  { to: "/app/ho-so", label: "Hồ sơ" },
];

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `block whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? "bg-primary-soft text-primary-strong" : "text-muted hover:bg-bg hover:text-ink"
  }`;

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [leaving, setLeaving] = useState(false);

  // Rời /app trước rồi mới xóa phiên; làm ngược lại thì RequireAuth kịp chuyển sang /dang-nhap?next=…
  const signOut = async () => {
    setLeaving(true);
    navigate("/", { replace: true });
    await logout();
  };

  const nav = [...NAV, ...(user?.role === "admin" ? [{ to: "/admin", label: "Quản trị" }] : [])];

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      <a href="#noi-dung" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-2">
        Bỏ qua, tới nội dung chính
      </a>
      <aside className="border-b border-line bg-surface lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col lg:border-b-0 lg:border-r">
        <div className="flex items-center justify-between gap-3 px-4 py-3 lg:px-5 lg:py-5">
          <Logo to="/app" />
          <Button variant="ghost" className="lg:hidden" onClick={signOut} loading={leaving}>Đăng xuất</Button>
        </div>
        <nav aria-label="Điều hướng chính" className="overflow-x-auto px-3 pb-3 lg:flex-1 lg:px-3">
          <ul className="flex gap-1 lg:flex-col">
            {nav.map((item) => (
              <li key={item.to}><NavLink to={item.to} end={item.end} className={linkClass}>{item.label}</NavLink></li>
            ))}
          </ul>
        </nav>
        <div className="hidden border-t border-line p-4 lg:block">
          <p className="truncate text-sm font-semibold text-ink">{user?.display_name}</p>
          <p className="truncate text-xs text-muted">{user?.email}</p>
          <Button variant="secondary" className="mt-3 w-full" onClick={signOut} loading={leaving}>Đăng xuất</Button>
        </div>
      </aside>
      <main id="noi-dung" className="mx-auto w-full max-w-5xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <Suspense fallback={<PageLoader />}><Outlet /></Suspense>
      </main>
    </div>
  );
}

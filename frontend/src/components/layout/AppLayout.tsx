import { Suspense, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router";
import { useAuth } from "../../auth/AuthProvider";
import { PageLoader } from "../ui/PageLoader";
import { Logo } from "./Logo";

// Bố cục khung lấy từ v0.5.3-dev (thanh bên tối, mục đang mở nổi khối), logic giữ của main:
// NavLink theo route, RequireAuth ở App.tsx, đăng xuất về trang chủ.
// Chỉ liệt kê màn đã có thật; Ôn tập, Mục tiêu, Tutor thêm vào khi làm xong.
const NAV = [
  { to: "/app", label: "Tổng quan", end: true },
  { to: "/app/hoc", label: "Học" },
  { to: "/app/luyen-tap", label: "Luyện tập" },
  { to: "/app/tien-do", label: "Tiến độ" },
  { to: "/app/composition", label: "Sáng tác" },
  { to: "/app/ho-so", label: "Hồ sơ" },
];

// Phiên bản hiện ở chân thanh bên, giống v0.5.3 ghi "v0.5.3-dev" dưới logo.
const APP_VERSION = `v${__APP_VERSION__}`;

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex h-full items-center justify-center rounded-lg px-2 py-2 text-center text-xs font-medium leading-tight transition-colors lg:justify-start lg:px-3 lg:py-2.5 lg:text-left lg:text-sm ${
    isActive ? "bg-shell-raised text-shell-ink" : "text-shell-text hover:bg-shell-raised/60 hover:text-shell-ink"
  }`;

const signOutClass =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-shell-line px-3 py-2 text-sm font-semibold text-shell-text transition-colors hover:border-shell-muted hover:text-shell-ink disabled:opacity-50";

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
    <div className="min-h-screen lg:grid lg:grid-cols-[230px_1fr]">
      <a href="#noi-dung" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-2">
        Bỏ qua, tới nội dung chính
      </a>
      <aside className="bg-shell text-shell-text lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col lg:gap-7 lg:px-4 lg:py-6">
        <div className="flex items-center justify-between gap-3 px-4 pb-2 pt-3 lg:p-0">
          <Logo to="/app" inverted />
          <button type="button" className={`${signOutClass} lg:hidden`} onClick={signOut} disabled={leaving} aria-busy={leaving}>Đăng xuất</button>
        </div>
        <nav aria-label="Điều hướng chính" className="px-3 pb-3 lg:p-0">
          <ul className="grid grid-flow-col auto-cols-fr gap-1 lg:grid-flow-row lg:auto-cols-auto lg:gap-1.5">
            {nav.map((item) => (
              <li key={item.to}><NavLink to={item.to} end={item.end} className={linkClass}>{item.label}</NavLink></li>
            ))}
          </ul>
        </nav>
        <div className="hidden border-t border-shell-line pt-4 lg:mt-auto lg:block">
          <p className="truncate text-sm font-semibold text-shell-ink">{user?.display_name}</p>
          <p className="truncate text-xs text-shell-muted">{user?.email}</p>
          <button type="button" className={`${signOutClass} mt-3 w-full`} onClick={signOut} disabled={leaving} aria-busy={leaving}>Đăng xuất</button>
          <p className="mt-3 text-xs text-shell-muted">HarmonyMentor {APP_VERSION}</p>
        </div>
      </aside>
      <main id="noi-dung" className="mx-auto w-full max-w-5xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <Suspense fallback={<PageLoader />}><Outlet /></Suspense>
      </main>
    </div>
  );
}

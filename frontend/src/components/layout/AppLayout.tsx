import { Suspense, useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router";
import { useAuth } from "../../auth/AuthProvider";
import { PageLoader } from "../ui/PageLoader";
import { Logo } from "./Logo";
import FloatingTutorDrawer from "../learning/FloatingTutorDrawer";
import { ThemeToggle } from "../../theme/ThemeToggle";
import { AccountMenu } from "./AccountMenu";

// Bố cục khung lấy từ v0.5.3-dev (thanh bên tối, mục đang mở nổi khối), logic giữ của main:
// NavLink theo route, RequireAuth ở App.tsx, đăng xuất về trang chủ.
// Chỉ liệt kê màn đã có thật; Ôn tập, Mục tiêu, Tutor thêm vào khi làm xong.
const NAV = [
  { to: "/app", label: "Tổng quan", end: true },
  { to: "/app/hoc", label: "Học" },
  { to: "/app/luyen-tap", label: "Luyện tập" },
  { to: "/app/quiz", label: "Quiz kỹ năng" },
  { to: "/app/tien-do", label: "Tiến độ" },
  { to: "/app/composition", label: "Sáng tác" },
];
// "Hồ sơ" chuyển lên menu ảnh đại diện ở góc phải trên (ADR-029, 9A); trang /app/ho-so giữ nguyên.

// Phiên bản hiện ở chân thanh bên, giống v0.5.3 ghi "v0.5.3-dev" dưới logo.
const APP_VERSION = `v${__APP_VERSION__}`;

// FE-009: dưới lg menu là một dòng cuộn ngang dính đầu màn hình (không xuống dòng như "Quiz kỹ năng" 3 dòng trước đây).
// Không dùng thanh tab đáy vì đáy đã dành cho thanh "Bước tiếp" của bài học và thanh Phát của Harmony Lab.
const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex min-h-11 items-center whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium leading-tight transition-colors lg:min-h-0 lg:px-3 lg:py-2.5 ${
    isActive ? "bg-shell-raised text-shell-ink" : "text-shell-text hover:bg-shell-raised/60 hover:text-shell-ink"
  }`;

const toggleClass = "lg:size-9 border-shell-line text-shell-text hover:border-shell-muted hover:text-shell-ink";

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [leaving, setLeaving] = useState(false);
  const { pathname } = useLocation();
  const navRef = useRef<HTMLUListElement>(null);

  // Mục đang mở có thể nằm ngoài khung cuộn ngang trên điện thoại (vd Hồ sơ): kéo nó vào tầm nhìn.
  useEffect(() => {
    const active = navRef.current?.querySelector<HTMLElement>('[aria-current="page"]');
    if (!active || window.matchMedia("(min-width: 1024px)").matches) return;
    active.scrollIntoView({ block: "nearest", inline: "nearest" });
  }, [pathname]);

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
      <aside data-surface="dark" className="text-shell-text max-lg:contents lg:sticky lg:bg-shell lg:top-0 lg:flex lg:h-screen lg:flex-col lg:gap-7 lg:px-4 lg:py-6">
        <div className="flex items-center justify-between gap-3 bg-shell px-4 pb-2 pt-3 lg:bg-transparent lg:p-0">
          <Logo to="/app" inverted />
          <div className="flex items-center gap-2">
            <ThemeToggle className={toggleClass} />
            <div className="lg:hidden"><AccountMenu tone="dark" onSignOut={signOut} leaving={leaving} /></div>
          </div>
        </div>
        <nav aria-label="Điều hướng chính" className="sticky top-0 z-30 border-b border-shell-line bg-shell px-2 py-1.5 lg:static lg:border-0 lg:bg-transparent lg:p-0">
          <ul ref={navRef} className="flex gap-1 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden lg:grid lg:gap-1.5 lg:overflow-visible">
            {nav.map((item) => (
              <li key={item.to} className="shrink-0 lg:shrink"><NavLink to={item.to} end={item.end} className={linkClass}>{item.label}</NavLink></li>
            ))}
          </ul>
        </nav>
        <div className="hidden border-t border-shell-line pt-4 lg:mt-auto lg:block">
          <p className="text-xs text-shell-muted">HarmonyMentor {APP_VERSION}</p>
        </div>
      </aside>
      <div className="min-w-0">
        {/* Máy tính: thanh mỏng trên cùng chỉ chứa ảnh đại diện ở góc phải (điện thoại: ảnh nằm ở dòng logo). */}
        <div className="mx-auto hidden w-full max-w-5xl justify-end px-8 pt-5 lg:flex">
          <AccountMenu onSignOut={signOut} leaving={leaving} />
        </div>
        <main id="noi-dung" className="mx-auto w-full max-w-5xl px-4 py-6 max-md:pb-28 sm:px-6 lg:px-8 lg:pb-8 lg:pt-2">
          <Suspense fallback={<PageLoader />}><Outlet /></Suspense>
        </main>
      </div>
      <FloatingTutorDrawer />
    </div>
  );
}

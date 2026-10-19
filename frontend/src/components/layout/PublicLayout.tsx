import { Suspense } from "react";
import { Link, NavLink, Outlet } from "react-router";
import { useAuth } from "../../auth/AuthProvider";
import { ButtonLink } from "../ui/Button";
import { PageLoader } from "../ui/PageLoader";
import { Logo } from "./Logo";

export default function PublicLayout() {
  const { status } = useAuth();
  return (
    <div className="flex min-h-screen flex-col">
      <a href="#noi-dung" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-2">
        Bỏ qua, tới nội dung chính
      </a>
      <header className="border-b border-line bg-surface/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Logo />
          <nav aria-label="Điều hướng trang chủ" className="flex items-center gap-1 sm:gap-2">
            <Link to="/#chuong-trinh" className="hidden rounded-md px-3 py-2 text-sm text-muted hover:text-ink sm:block">Chương trình</Link>
            <Link to="/#tinh-nang" className="hidden rounded-md px-3 py-2 text-sm text-muted hover:text-ink sm:block">Tính năng</Link>
            {status === "authenticated" ? (
              <ButtonLink to="/app">Vào học</ButtonLink>
            ) : (
              <>
                <NavLink to="/dang-nhap" className="rounded-md px-3 py-2 text-sm font-medium text-ink hover:text-primary">Đăng nhập</NavLink>
                <ButtonLink to="/dang-ky" className="hidden sm:inline-flex">Đăng ký</ButtonLink>
              </>
            )}
          </nav>
        </div>
      </header>
      <main id="noi-dung" className="flex-1">
        <Suspense fallback={<PageLoader />}><Outlet /></Suspense>
      </main>
      <footer className="border-t border-line py-6 text-center text-sm text-muted">
        HarmonyMentor · Đồ án nhóm, học nhạc lý có AI Tutor · Ký hiệu nhạc theo chuẩn quốc tế
      </footer>
    </div>
  );
}

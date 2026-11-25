import { Suspense } from "react";
import { Link, NavLink, Outlet } from "react-router";
import { useAuth } from "../../auth/AuthProvider";
import { ButtonLink } from "../ui/Button";
import { PageLoader } from "../ui/PageLoader";
import { Logo } from "./Logo";
import { ThemeToggle } from "../../theme/ThemeToggle";
import { SiteFooter } from "../../pages/public/home/SiteFooter";

export default function PublicLayout() {
  const { status } = useAuth();
  return (
    <div className="flex min-h-screen flex-col">
      <a href="#noi-dung" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-2">
        Bỏ qua, tới nội dung chính
      </a>
      <header className="border-b border-line bg-surface/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-2 px-4 py-3 sm:gap-4 sm:px-6">
          <Logo />
          <nav aria-label="Điều hướng trang chủ" className="flex items-center gap-1 sm:gap-2">
            <Link to="/#lo-trinh" className="hidden rounded-md px-3 py-2 text-sm text-muted hover:text-ink sm:block">Lộ trình</Link>
            <Link to="/#chuong-trinh" className="hidden rounded-md px-3 py-2 text-sm text-muted hover:text-ink md:block">Chương trình</Link>
            <Link to="/#tinh-nang" className="hidden rounded-md px-3 py-2 text-sm text-muted hover:text-ink sm:block">Tính năng</Link>
            {status === "authenticated" ? (
              <ButtonLink to="/app">Vào học</ButtonLink>
            ) : (
              <>
                <NavLink to="/dang-nhap" className="whitespace-nowrap rounded-md px-2 py-2 text-sm font-medium text-ink hover:text-primary sm:px-3">Đăng nhập</NavLink>
                {/* max-sm:hidden thay cho "hidden sm:inline-flex": lớp inline-flex của nút đè lớp hidden nên "Đăng ký" vẫn hiện và xuống 2 dòng. */}
                <ButtonLink to="/dang-ky" className="max-sm:hidden">Đăng ký</ButtonLink>
              </>
            )}
            <ThemeToggle className="max-sm:size-10 sm:ml-1 border-line text-ink hover:border-primary hover:text-primary" />
          </nav>
        </div>
      </header>
      <main id="noi-dung" className="flex-1">
        <Suspense fallback={<PageLoader />}><Outlet /></Suspense>
      </main>
      <SiteFooter />
    </div>
  );
}

import { Link } from "react-router";
import { useAuth } from "../../../auth/AuthProvider";
import { Logo } from "../../../components/layout/Logo";
import { ThemeToggle } from "../../../theme/ThemeToggle";
import { footer } from "./copy";

type Item = { label: string; to: string; external?: boolean };

function Column({ title, items }: { title: string; items: Item[] }) {
  return (
    <nav aria-label={title}>
      <h2 className="text-sm font-semibold text-ink">{title}</h2>
      <ul className="mt-3 space-y-2 text-sm">
        {items.map((item) => (
          <li key={item.label}>
            {item.external ? (
              <a href={item.to} target="_blank" rel="noopener noreferrer" className="text-muted underline-offset-4 hover:text-primary hover:underline">
                {item.label}
              </a>
            ) : (
              <Link to={item.to} className="text-muted underline-offset-4 hover:text-primary hover:underline">
                {item.label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </nav>
  );
}

export function SiteFooter() {
  const { status } = useAuth();
  // Khách chưa đăng nhập bấm "Kiểm tra đầu vào" sẽ bị khu học đẩy về trang đăng nhập, nên đưa thẳng tới đăng ký.
  const placementTo = status === "authenticated" ? "/app/kiem-tra-dau-vao" : "/dang-ky";

  return (
    <footer className="border-t border-line bg-surface">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-[1.6fr_1fr_1fr_1fr]">
          <div>
            <Logo />
            <p className="mt-4 max-w-sm text-sm text-muted">{footer.about}</p>
          </div>

          <Column
            title="Học"
            items={[
              { label: "Lộ trình", to: "/#lo-trinh" },
              { label: "Chương trình học", to: "/#chuong-trinh" },
              { label: "Tính năng", to: "/#tinh-nang" },
              { label: "Kiểm tra đầu vào", to: placementTo },
            ]}
          />

          {/* Các trang sản phẩm đều cần đăng nhập, nên ở đây trỏ về phần giới thiệu tương ứng trên trang chủ. */}
          <Column
            title="Sản phẩm"
            items={[
              { label: "AI Tutor", to: "/#ai-tutor" },
              { label: "Harmony Lab", to: "/#harmony-lab" },
              { label: "Luyện tập", to: "/#hoc-va-lam" },
            ]}
          />

          <div>
            <h2 className="text-sm font-semibold text-ink">Về dự án</h2>
            <ul className="mt-3 space-y-2 text-sm text-muted">
              {footer.team.map((name) => <li key={name}>{name}</li>)}
            </ul>
            <ul className="mt-3 space-y-2 text-sm">
              <li>
                <a href={footer.github} target="_blank" rel="noopener noreferrer" className="text-muted underline-offset-4 hover:text-primary hover:underline">
                  Mã nguồn trên GitHub
                </a>
              </li>
              <li>
                <a href={`mailto:${footer.email}`} className="text-muted underline-offset-4 hover:text-primary hover:underline">
                  {footer.email}
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-10 flex flex-wrap items-center justify-between gap-4 border-t border-line pt-6 text-sm text-muted">
          <p>© {new Date().getFullYear()} HarmonyMentor · {footer.note} · Ký hiệu nhạc theo chuẩn quốc tế</p>
          <ThemeToggle className="border-line text-ink hover:border-primary hover:text-primary" />
        </div>
      </div>
    </footer>
  );
}

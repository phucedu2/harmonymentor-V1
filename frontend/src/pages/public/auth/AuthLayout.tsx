import { useEffect, type ReactNode } from "react";
import { HarmonyMentorLogo } from "../../../components/brand/HarmonyMentorLogo";
import "./auth.css";

type Props = { title: string; subtitle?: ReactNode; children: ReactNode; footer?: ReactNode };

/** Bố cục chung mọi trang tài khoản (B1): trái là bảng thương hiệu, phải là form. Dưới 768px chỉ còn form. */
export function AuthLayout({ title, subtitle, children, footer }: Props) {
  useEffect(() => {
    const previous = document.title;
    document.title = `${title} · Harmony Mentor`;
    return () => { document.title = previous; };
  }, [title]);

  return (
    <div className="grid min-h-[calc(100vh-4rem)] md:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <BrandPanel />
      <section className="flex items-start justify-center px-4 py-8 sm:px-8 sm:py-14 md:items-center">
        <div className="w-full max-w-md">
          <h1 className="text-2xl font-bold sm:text-3xl">{title}</h1>
          {subtitle && <p className="mt-2 text-muted">{subtitle}</p>}
          <div className="mt-7">{children}</div>
          {footer && <p className="mt-8 text-center text-sm text-muted">{footer}</p>}
        </div>
      </section>
    </div>
  );
}

function BrandPanel() {
  return (
    <aside className="relative hidden overflow-hidden bg-shell text-shell-text md:flex md:flex-col md:justify-center md:gap-12 md:p-10 lg:p-14" aria-hidden="true">
      {/* Đèn sân khấu: vệt sáng màu signature, nhịp chậm; tắt khi giảm chuyển động (auth.css). */}
      <div className="hm-auth-spot pointer-events-none absolute -right-24 top-1/3 size-96 rounded-full bg-signature/30 blur-3xl" />
      <div data-theme="dark" className="relative"><HarmonyMentorLogo variant="bieu-tuong" className="size-14" title="" /></div>
      <div className="relative max-w-md">
        <p className="font-display text-3xl leading-tight text-shell-ink lg:text-4xl">Học nhạc lý cùng gia sư.</p>
        <p className="mt-4 text-shell-muted">Từng bước từ nốt nhạc đầu tiên tới hợp âm, có bài luyện tập vừa sức và gia sư AI trả lời mọi lúc.</p>
      </div>
      <StaffArt />
    </aside>
  );
}

/** Khuông nhạc với bốn nốt I–IV–V–I trôi nhẹ; tắt chuyển động khi người dùng chọn giảm chuyển động. */
function StaffArt() {
  const lines = [0, 1, 2, 3, 4];
  return (
    <svg viewBox="0 0 400 160" className="relative w-full max-w-md" role="presentation">
      {lines.map((i) => (
        <line key={i} x1="0" x2="400" y1={50 + i * 14} y2={50 + i * 14} stroke="var(--color-shell-line)" strokeWidth="2" />
      ))}
      {[{ x: 70, y: 106 }, { x: 160, y: 85 }, { x: 250, y: 78 }, { x: 340, y: 106 }].map((n, i) => (
        <g key={n.x} className="hm-auth-note">
          <ellipse cx={n.x} cy={n.y} rx="11" ry="8" transform={`rotate(-20 ${n.x} ${n.y})`}
            fill={i % 2 === 0 ? "var(--color-signature)" : "var(--color-shell-text)"} />
          <line x1={n.x + 10} x2={n.x + 10} y1={n.y - 2} y2={n.y - 46} stroke="var(--color-shell-text)" strokeWidth="2.5" />
        </g>
      ))}
    </svg>
  );
}

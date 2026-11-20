import { Link } from "react-router";
import { HarmonyMentorLogo } from "../brand/HarmonyMentorLogo";

// inverted: dùng trên nền tối của khung khu học (bố cục v0.5.3); bật bản tối của logo chỉ trong vùng này (logo.css).
export function Logo({ to = "/", inverted = false }: { to?: string; inverted?: boolean }) {
  return (
    <Link
      to={to}
      className="inline-flex shrink-0 items-center rounded-md"
      aria-label="Harmony Mentor, về trang chủ"
      data-theme={inverted ? "dark" : undefined}
    >
      {/* Logo ngang cao 36px: dưới 28px chỉ được dùng biểu tượng (docs/thuong-hieu/BRAND_NOTE.md) */}
      <HarmonyMentorLogo className="h-9 w-auto" />
    </Link>
  );
}

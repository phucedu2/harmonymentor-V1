import { Link } from "react-router";
import { HarmonyMentorLogo } from "../brand/HarmonyMentorLogo";

export function Logo({ to = "/" }: { to?: string }) {
  return (
    <Link to={to} className="inline-flex shrink-0 items-center rounded-md" aria-label="Harmony Mentor, về trang chủ">
      {/* Logo ngang cao 36px: dưới 28px chỉ được dùng biểu tượng (docs/thuong-hieu/BRAND_NOTE.md) */}
      <HarmonyMentorLogo className="h-9 w-auto" />
    </Link>
  );
}

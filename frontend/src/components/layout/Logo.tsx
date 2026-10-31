import { Link } from "react-router";

// inverted: dùng trên nền tối của khung khu học (bố cục v0.5.3).
export function Logo({ to = "/", inverted = false }: { to?: string; inverted?: boolean }) {
  return (
    <Link to={to} className={`flex items-center gap-2.5 font-bold ${inverted ? "text-white" : "text-ink"}`} aria-label="HarmonyMentor, về trang chủ">
      <span className="grid size-9 place-items-center rounded-lg bg-primary font-mono text-lg text-white" aria-hidden="true">♪</span>
      <span className="text-lg tracking-tight">HarmonyMentor</span>
    </Link>
  );
}

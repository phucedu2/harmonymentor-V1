import { Link } from "react-router";

export function Logo({ to = "/" }: { to?: string }) {
  return (
    <Link to={to} className="flex items-center gap-2.5 font-bold text-ink" aria-label="HarmonyMentor, về trang chủ">
      <span className="grid size-9 place-items-center rounded-lg bg-primary font-mono text-lg text-white" aria-hidden="true">♪</span>
      <span className="text-lg tracking-tight">HarmonyMentor</span>
    </Link>
  );
}

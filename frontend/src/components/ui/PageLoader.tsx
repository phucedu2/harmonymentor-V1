import { Spinner } from "./Button";

export function PageLoader({ label = "Đang tải…" }: { label?: string }) {
  return (
    <div className="grid min-h-[50vh] place-items-center text-muted" role="status">
      <span className="flex items-center gap-3"><Spinner className="size-5 text-primary" />{label}</span>
    </div>
  );
}

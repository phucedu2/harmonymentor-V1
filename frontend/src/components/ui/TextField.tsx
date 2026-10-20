import { useId, type InputHTMLAttributes, type ReactNode } from "react";

type Props = InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string; hint?: ReactNode };

export function TextField({ label, error, hint, className = "", ...rest }: Props) {
  const id = useId();
  const describedBy = [error ? `${id}-error` : null, hint ? `${id}-hint` : null].filter(Boolean).join(" ") || undefined;
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-ink">{label}</label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`w-full rounded-lg border bg-surface px-3 py-2.5 text-base text-ink placeholder:text-muted/70 focus:outline-2 focus:outline-offset-0 focus:outline-primary ${error ? "border-danger" : "border-line"}`}
        {...rest}
      />
      {hint && <div id={`${id}-hint`} className="mt-1.5 text-sm text-muted">{hint}</div>}
      {error && <p id={`${id}-error`} className="mt-1.5 text-sm text-danger">✗ {error}</p>}
    </div>
  );
}

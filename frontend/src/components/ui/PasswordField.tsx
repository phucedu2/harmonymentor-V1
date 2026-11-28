import { useId, useState, type InputHTMLAttributes, type KeyboardEvent, type ReactNode } from "react";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label: string;
  error?: string;
  hint?: ReactNode;
  /** Thứ hiện cạnh nhãn, ví dụ liên kết "Quên mật khẩu?" (B4). */
  labelAction?: ReactNode;
};

/** Ô mật khẩu (B2): nút hiện/ẩn có aria-pressed, cảnh báo Caps Lock, lỗi nối bằng aria-describedby.
 *  Không có ô "nhập lại mật khẩu" vì người dùng tự kiểm bằng nút hiện mật khẩu (cách Google/Stripe làm). */
export function PasswordField({ label, error, hint, labelAction, className = "", onKeyUp, onKeyDown, onBlur, ...rest }: Props) {
  const id = useId();
  const [visible, setVisible] = useState(false);
  const [capsLock, setCapsLock] = useState(false);
  const describedBy = [error ? `${id}-error` : null, capsLock ? `${id}-caps` : null, hint ? `${id}-hint` : null]
    .filter(Boolean).join(" ") || undefined;
  const readCaps = (e: KeyboardEvent<HTMLInputElement>) => setCapsLock(e.getModifierState?.("CapsLock") ?? false);

  return (
    <div className={className}>
      <div className="mb-1.5 flex items-baseline justify-between gap-3">
        <label htmlFor={id} className="block text-sm font-medium text-ink">{label}</label>
        {labelAction}
      </div>
      <div className="relative">
        <input
          id={id}
          type={visible ? "text" : "password"}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck={false}
          className={`w-full rounded-lg border bg-surface py-2.5 pl-3 pr-20 text-base text-ink placeholder:text-muted/70 focus:outline-2 focus:outline-offset-0 focus:outline-primary ${error ? "border-danger" : "border-line"}`}
          onKeyUp={(e) => { readCaps(e); onKeyUp?.(e); }}
          onKeyDown={(e) => { readCaps(e); onKeyDown?.(e); }}
          onBlur={(e) => { setCapsLock(false); onBlur?.(e); }}
          {...rest}
        />
        <button
          type="button"
          aria-pressed={visible}
          aria-controls={id}
          onClick={() => setVisible((v) => !v)}
          className="absolute inset-y-1 right-1 min-w-11 rounded-md px-2.5 text-sm font-medium text-primary hover:bg-primary-soft focus-visible:outline-2 focus-visible:outline-primary"
        >
          {visible ? "Ẩn" : "Hiện"}<span className="sr-only"> mật khẩu</span>
        </button>
      </div>
      {capsLock && (
        <p id={`${id}-caps`} className="mt-1.5 text-sm text-warning" role="status">
          <span aria-hidden="true">⇪ </span>Phím Caps Lock đang bật.
        </p>
      )}
      {hint && <div id={`${id}-hint`} className="mt-1.5 text-sm text-muted">{hint}</div>}
      {error && <p id={`${id}-error`} className="mt-1.5 text-sm text-danger">✗ {error}</p>}
    </div>
  );
}

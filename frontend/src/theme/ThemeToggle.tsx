import { useEffect, useState } from "react";
import { applyTheme, readTheme, type Theme } from "./theme";

// Nút nhỏ đổi sáng/tối. Hai nơi dùng (header công khai, thanh bên khu học) đồng bộ qua sự kiện "hm-theme".
export function ThemeToggle({ className = "" }: { className?: string }) {
  const [theme, setTheme] = useState<Theme>(readTheme);
  useEffect(() => {
    const sync = (e: Event) => setTheme((e as CustomEvent<Theme>).detail);
    window.addEventListener("hm-theme", sync);
    return () => window.removeEventListener("hm-theme", sync);
  }, []);
  const dark = theme === "dark";
  return (
    <button
      type="button"
      className={`inline-grid size-11 shrink-0 place-items-center rounded-full border text-lg leading-none transition-colors ${className}`}
      aria-pressed={dark}
      aria-label={dark ? "Đang dùng giao diện tối. Bấm để chuyển sang sáng" : "Đang dùng giao diện sáng. Bấm để chuyển sang tối"}
      title={dark ? "Chuyển sang giao diện sáng" : "Chuyển sang giao diện tối"}
      onClick={() => applyTheme(dark ? "light" : "dark")}
    >
      <span aria-hidden="true">{dark ? "☀" : "☾"}</span>
    </button>
  );
}

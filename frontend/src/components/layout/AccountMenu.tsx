import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../../auth/AuthProvider";
import { AnimalAvatar, animalFor } from "../ui/AnimalAvatar";

// Góc phải trên cùng (ADR-029, 9A): ảnh đại diện mở menu nhỏ "Hồ sơ" và "Đăng xuất", dùng chung cho người học và Quản trị viên.
// Mẫu menu theo WAI-ARIA Menu Button: Enter/Space/↓ mở và vào mục đầu, ↑↓ chuyển mục, Esc đóng và trả focus về nút.
export function AccountMenu({ tone = "light", onSignOut, leaving }: { tone?: "light" | "dark"; onSignOut: () => void; leaving: boolean }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const wrap = useRef<HTMLDivElement>(null);
  const button = useRef<HTMLButtonElement>(null);
  const menuId = useId();

  const items = () => Array.from(wrap.current?.querySelectorAll<HTMLElement>('[role="menuitem"]') ?? []);
  useEffect(() => {
    if (!open) return;
    items()[0]?.focus();
    const away = (e: PointerEvent) => { if (!wrap.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("pointerdown", away);
    return () => document.removeEventListener("pointerdown", away);
  }, [open]);

  const close = (refocus = true) => { setOpen(false); if (refocus) button.current?.focus(); };
  const onMenuKey = (e: KeyboardEvent<HTMLDivElement>) => {
    const list = items();
    const i = list.indexOf(document.activeElement as HTMLElement);
    if (e.key === "Escape") { e.preventDefault(); close(); }
    else if (e.key === "ArrowDown") { e.preventDefault(); list[(i + 1) % list.length]?.focus(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); list[(i - 1 + list.length) % list.length]?.focus(); }
    else if (e.key === "Home") { e.preventDefault(); list[0]?.focus(); }
    else if (e.key === "End") { e.preventDefault(); list[list.length - 1]?.focus(); }
    else if (e.key === "Tab") setOpen(false);
  };

  if (!user) return null;
  const animal = animalFor(user);
  const ring = tone === "dark" ? "ring-shell-line hover:ring-shell-muted" : "ring-line hover:ring-primary";
  const item = "flex min-h-11 w-full items-center gap-2 rounded-lg px-3 text-left text-sm font-medium text-ink hover:bg-bg focus-visible:bg-bg focus-visible:outline-none disabled:opacity-50";

  return <div ref={wrap} className="relative">
    <button ref={button} type="button" aria-haspopup="menu" aria-expanded={open} aria-controls={open ? menuId : undefined}
      aria-label={`Tài khoản: ${user.display_name}`} title={user.display_name}
      onClick={() => setOpen((v) => !v)}
      onKeyDown={(e) => { if (e.key === "ArrowDown" && !open) { e.preventDefault(); setOpen(true); } }}
      className={`grid size-11 place-items-center rounded-full ring-2 transition-shadow ${ring}`}>
      <AnimalAvatar animal={animal} size={38} decorative />
    </button>
    {open && <div id={menuId} role="menu" aria-label="Tài khoản" onKeyDown={onMenuKey}
      className="absolute right-0 top-[calc(100%+0.5rem)] z-50 w-64 rounded-xl border border-line bg-surface p-2 text-ink shadow-2xl">
      <div className="flex items-center gap-3 border-b border-line px-2 pb-3 pt-1">
        <AnimalAvatar animal={animal} size={44} />
        <div className="min-w-0">
          <p className="truncate font-semibold">{user.display_name}</p>
          <p className="truncate text-xs text-muted">{user.email}</p>
          <p className="text-xs text-muted">{user.role === "admin" ? "Quản trị viên" : "Người học"}</p>
        </div>
      </div>
      <div className="mt-1 grid gap-0.5">
        <button type="button" role="menuitem" tabIndex={-1} className={item}
          onClick={() => { close(false); navigate("/app/ho-so"); }}>Hồ sơ</button>
        <button type="button" role="menuitem" tabIndex={-1} className={item} disabled={leaving} aria-busy={leaving}
          onClick={() => { close(false); onSignOut(); }}>Đăng xuất</button>
      </div>
    </div>}
  </div>;
}

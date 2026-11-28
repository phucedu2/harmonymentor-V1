import { useCallback, useEffect, useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type PointerEvent as ReactPointerEvent } from "react";

// Kéo-thả phần tử position: fixed (nút AI và khung AI Tutor). Vị trí lưu localStorage theo từng máy;
// null = vị trí mặc định trong CSS. Không thêm thư viện (quyết định 6A).
export type Pos = { x: number; y: number };

const MARGIN = 8;

function readPos(key: string): Pos | null {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const p = JSON.parse(raw) as Pos;
    return Number.isFinite(p.x) && Number.isFinite(p.y) ? p : null;
  } catch { return null; }
}

function writePos(key: string, pos: Pos | null) {
  try { if (pos) localStorage.setItem(key, JSON.stringify(pos)); else localStorage.removeItem(key); } catch { /* chế độ riêng tư: chỉ nhớ trong phiên */ }
}

// Giữ phần tử trong màn hình kể cả khi đổi cỡ cửa sổ hoặc xoay máy.
export function clampPos(pos: Pos, w: number, h: number): Pos {
  const maxX = Math.max(MARGIN, window.innerWidth - w - MARGIN);
  const maxY = Math.max(MARGIN, window.innerHeight - h - MARGIN);
  return { x: Math.min(Math.max(MARGIN, pos.x), maxX), y: Math.min(Math.max(MARGIN, pos.y), maxY) };
}

type Options = {
  key: string;
  // Thả ra thì dạt vào mép trái/phải gần nhất (nút tròn), để không nằm giữa nội dung.
  snapX?: boolean;
  enabled?: boolean;
};

export function useDraggable<T extends HTMLElement>({ key, snapX = false, enabled = true }: Options) {
  const ref = useRef<T>(null);
  const [pos, setPos] = useState<Pos | null>(() => readPos(key));
  const [dragging, setDragging] = useState(false);
  // moved = đã kéo quá ngưỡng; dùng để chặn onClick sinh ra sau khi thả.
  const drag = useRef<{ id: number; dx: number; dy: number; sx: number; sy: number; moved: boolean } | null>(null);
  const justDragged = useRef(false);
  const last = useRef<Pos | null>(null);

  const size = () => {
    const r = ref.current?.getBoundingClientRect();
    return { w: r?.width ?? 48, h: r?.height ?? 48 };
  };

  const commit = useCallback((next: Pos | null) => { setPos(next); writePos(key, next); }, [key]);

  useEffect(() => {
    if (!pos) return;
    const onResize = () => { const { w, h } = size(); setPos((p) => (p ? clampPos(p, w, h) : p)); };
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pos === null]);

  const onPointerDown = (e: ReactPointerEvent<HTMLElement>) => {
    if (!enabled || e.button !== 0 || !ref.current) return;
    // Bấm vào nút con trong thanh kéo (×, ↺) thì để nút đó nhận click, không bắt đầu kéo.
    const control = (e.target as Element).closest?.("button, a, input, textarea, select");
    if (control && control !== e.currentTarget) return;
    const r = ref.current.getBoundingClientRect();
    drag.current = { id: e.pointerId, dx: e.clientX - r.left, dy: e.clientY - r.top, sx: e.clientX, sy: e.clientY, moved: false };
    // Bắt con trỏ ngay khi nhấn: nút tròn chỉ 48 px, kéo nhanh là con trỏ rời nút trước khi kịp nhận pointermove.
    (e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId);
  };

  const onPointerMove = (e: ReactPointerEvent<HTMLElement>) => {
    const d = drag.current;
    if (!d || d.id !== e.pointerId) return;
    if (!d.moved) {
      if (Math.hypot(e.clientX - d.sx, e.clientY - d.sy) < 6) return;
      d.moved = true;
      setDragging(true);
    }
    const { w, h } = size();
    last.current = clampPos({ x: e.clientX - d.dx, y: e.clientY - d.dy }, w, h);
    setPos(last.current);
  };

  // pointercancel có thể mang tọa độ 0,0 nên dùng vị trí cuối cùng đã vẽ, không đọc từ sự kiện.
  const end = () => {
    const d = drag.current;
    drag.current = null;
    if (!d || !d.moved || !last.current) return;
    justDragged.current = true;
    setDragging(false);
    const { w, h } = size();
    let next = last.current;
    if (snapX) next = { ...next, x: next.x + w / 2 < window.innerWidth / 2 ? MARGIN + 4 : window.innerWidth - w - MARGIN - 4 };
    commit(clampPos(next, w, h));
  };

  // Bàn phím (WCAG 2.5.7: kéo phải có cách khác): mũi tên dịch 24 px, Shift = 96 px.
  const onKeyDown = (e: ReactKeyboardEvent<HTMLElement>) => {
    const step = e.shiftKey ? 96 : 24;
    const delta = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[e.key];
    if (!delta || !ref.current) return;
    e.preventDefault();
    const r = ref.current.getBoundingClientRect();
    commit(clampPos({ x: r.left + delta[0], y: r.top + delta[1] }, r.width, r.height));
  };

  // Gọi trong onClick: trả true nếu cú "click" này thật ra là kết thúc một lần kéo.
  const consumeDrag = () => { const v = justDragged.current; justDragged.current = false; return v; };

  const handlers = enabled ? { onPointerDown, onPointerMove, onPointerUp: end, onPointerCancel: end } : {};
  const style = pos && enabled ? { left: pos.x, top: pos.y, right: "auto", bottom: "auto" } : undefined;

  // place: đặt vị trí từ ngoài (đổi kích thước từ mép trái/trên phải dời góc trên trái); live = chưa ghi localStorage.
  const place = (next: Pos, live = false) => { if (live) setPos(next); else commit(next); };

  return { ref, pos: enabled ? pos : null, dragging, handlers, style, onKeyDown, consumeDrag, place, reset: () => commit(null) };
}

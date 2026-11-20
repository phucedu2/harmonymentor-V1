// FE-026: GSAP + ScrollTrigger + Lenis (~45 KB gzip) chỉ tải khi trang chủ cần, không nằm trong gói chung.
// Trước đây import tĩnh ở WowScenes nên mọi trang (/app, /admin…) đều phải tải. Tách cả HomePage (lazy route)
// đã thử ở đợt 4 và làm CLS/LCP trang chủ xấu đi, nên ở đây chỉ tách thư viện chuyển động: khung trang chủ vẫn
// vẽ ngay, hoạt ảnh gắn vào khi thư viện về. Hoạt ảnh mở trang (chữ tiêu đề trồi lên) chuyển sang CSS để không
// phụ thuộc lúc thư viện về (tránh chữ hiện rồi biến rồi hiện lại).
import { useEffect, useState, type RefObject } from "react";
import type { default as Gsap } from "gsap";
import type { ScrollTrigger as ST } from "gsap/ScrollTrigger";
import type { default as LenisT } from "lenis";

export type Motion = { gsap: typeof Gsap; ScrollTrigger: typeof ST; Lenis: typeof LenisT };

let pending: Promise<Motion> | null = null;
export function loadMotion(): Promise<Motion> {
  pending ??= Promise.all([import("gsap"), import("gsap/ScrollTrigger"), import("lenis")]).then(([g, s, l]) => {
    g.default.registerPlugin(s.ScrollTrigger);
    return { gsap: g.default, ScrollTrigger: s.ScrollTrigger, Lenis: l.default };
  });
  return pending;
}

/** Trả về thư viện chuyển động khi đã tải xong (null trước đó, hoặc khi enabled=false). */
export function useMotion(enabled = true): Motion | null {
  const [motion, setMotion] = useState<Motion | null>(null);
  useEffect(() => {
    if (!enabled) return;
    let alive = true;
    loadMotion().then((m) => { if (alive) setMotion(m); }).catch(() => { /* mạng lỗi: trang vẫn đủ nội dung, chỉ thiếu hoạt ảnh */ });
    return () => { alive = false; };
  }, [enabled]);
  return enabled ? motion : null;
}

/** Thay cho useGSAP: chạy fn trong gsap.context giới hạn ở scope, tự revert khi deps đổi hoặc rời trang. */
export function useMotionEffect(motion: Motion | null, scope: RefObject<Element | null>, fn: (m: Motion) => void | (() => void), deps: unknown[]) {
  useEffect(() => {
    if (!motion) return;
    const ctx = motion.gsap.context(() => fn(motion), scope.current ?? undefined);
    return () => ctx.revert();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [motion, ...deps]);
}

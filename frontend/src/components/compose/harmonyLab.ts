// Logic thuần của Harmony Lab (phuc-music Bước 4), tách riêng để test bằng Vitest.
// Mọi hợp âm lấy từ danh sách Music Engine trả về (`/composition/options`), không tự dựng tên hợp âm.
import type { ComposeOptions } from "../../api";

type KeyChords = ComposeOptions["keys"][number];

// Vòng mẫu I–vi–IV–V tính theo bậc (vị trí trong danh sách hợp âm của giọng), lặp lại khi lưới dài hơn 4 ô.
const STARTER_DEGREES = [0, 5, 3, 4];

export function chordsOfKey(options: ComposeOptions, key: string): KeyChords["chords"] {
  return options.keys.find((item) => item.key === key)?.chords ?? [];
}

export function starterProgression(options: ComposeOptions, key: string, bars: number): (string | null)[] {
  const chords = chordsOfKey(options, key);
  if (chords.length < 7) return Array.from({ length: bars }, () => null);
  return Array.from({ length: bars }, (_, i) => chords[STARTER_DEGREES[i % STARTER_DEGREES.length]].symbol);
}

/**
 * Đổi giọng: hợp âm trong giọng cũ chuyển sang hợp âm cùng bậc của giọng mới (ii của C là Dm → ii của G là Am).
 * Hợp âm ngoài giọng cũ giữ nguyên để người học tự quyết; phần phân tích sẽ báo nó lạ thế nào trong giọng mới.
 */
export function remapToKey(chords: (string | null)[], options: ComposeOptions, from: string, to: string): (string | null)[] {
  const before = chordsOfKey(options, from);
  const after = chordsOfKey(options, to);
  return chords.map((symbol) => {
    if (!symbol) return null;
    const degree = before.findIndex((chord) => chord.symbol === symbol);
    return degree >= 0 && after[degree] ? after[degree].symbol : symbol;
  });
}

/** Đổi số ô: thêm ô trống ở cuối hoặc cắt bớt ô cuối. */
export function resizeBars(chords: (string | null)[], bars: number): (string | null)[] {
  return Array.from({ length: bars }, (_, i) => chords[i] ?? null);
}

export const LEVEL_BADGE: Record<number, "success" | "primary" | "warning" | "muted"> = { 0: "success", 1: "primary", 2: "warning", 3: "warning" };

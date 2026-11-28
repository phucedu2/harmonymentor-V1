// Mọi var(--x) trong src phải có định nghĩa --x: trong một file CSS của src. Biến không tồn tại không báo lỗi:
// SVG tô đen, CSS bỏ qua thuộc tính (piano trang chủ đen kịt sau khi bỏ styles.css ở Bước 3).
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

const SRC = fileURLToPath(new URL("../src", import.meta.url));
const files = (readdirSync(SRC, { recursive: true }) as string[])
  .filter((f) => /\.(tsx?|css)$/.test(f))
  .map((f) => ({ name: f, text: readFileSync(join(SRC, f), "utf8") }));

it("không dùng biến CSS chưa định nghĩa", () => {
  const defined = new Set(files.filter((f) => f.name.endsWith(".css")).flatMap((f) => [...f.text.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1])));
  // Tên kết thúc bằng "-" là tên ghép lúc chạy (var(--color-note-${...})), bỏ qua.
  const missing = files.flatMap((f) =>
    [...f.text.matchAll(/var\((--[\w-]+)/g)].map((m) => m[1]).filter((v) => !v.endsWith("-") && !defined.has(v)).map((v) => `${f.name}: ${v}`),
  );
  expect(missing).toEqual([]);
});

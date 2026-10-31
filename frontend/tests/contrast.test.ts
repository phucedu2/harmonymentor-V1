// phuc-music Bước 3: đo tương phản WCAG 2.1 của token màu trong index.css (chữ thường cần ≥ 4,5:1).
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const css = readFileSync(new URL("../src/index.css", import.meta.url), "utf8");
const token = (name: string) => {
  const match = css.match(new RegExp(`--color-${name}:\\s*(#[0-9a-fA-F]{6})`));
  if (!match) throw new Error(`thiếu token ${name}`);
  return match[1];
};
const lum = (hex: string) => {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const ratio = (a: string, b: string) => { const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m); return (x + 0.05) / (y + 0.05); };

describe("tương phản bảng màu Đồng & Gỉ", () => {
  it.each([
    ["ink", "bg"], ["ink", "surface"], ["muted", "bg"], ["muted", "surface"], ["primary", "bg"], ["primary", "surface"],
    ["primary-strong", "primary-soft"], ["danger", "bg"], ["danger", "danger-soft"], ["success", "success-soft"],
    ["warning", "warning-soft"], ["shell-text", "shell"], ["shell-muted", "shell-raised"], ["signature", "shell"], ["brass", "shell"],
    ["ink", "signature"], ["ink", "brass"],
  ])("%s trên %s ≥ 4,5:1", (fg, bg) => {
    expect(ratio(token(fg), token(bg))).toBeGreaterThanOrEqual(4.5);
  });

  it("chữ trắng trên nút chính và nút báo sai ≥ 4,5:1", () => {
    expect(ratio("#ffffff", token("primary"))).toBeGreaterThanOrEqual(4.5);
    expect(ratio("#ffffff", token("danger"))).toBeGreaterThanOrEqual(4.5);
  });

  it("12 màu nốt đều đọc được chữ ink", () => {
    for (const note of ["c", "g", "d", "a", "e", "b", "fs", "db", "ab", "eb", "bb", "f"]) {
      expect(ratio(token("ink"), token(`note-${note}`))).toBeGreaterThanOrEqual(4.5);
    }
  });
});

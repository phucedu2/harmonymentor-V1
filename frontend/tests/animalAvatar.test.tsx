import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { ANIMALS, AnimalAvatar, animalFor } from "../src/components/ui/AnimalAvatar";

// ADR-029: bộ con vật ở giao diện phải khớp đúng danh sách máy chủ chấp nhận (backend/app/auth/avatars.py).
describe("Ảnh đại diện con vật", () => {
  it("khớp danh sách khóa của máy chủ", () => {
    const py = readFileSync(resolve(__dirname, "../../backend/app/auth/avatars.py"), "utf-8");
    const keys = [...(py.match(/AvatarKey = Literal\[([^\]]+)\]/)?.[1] ?? "").matchAll(/"([a-z_]+)"/g)].map((m) => m[1]);
    expect(keys).toEqual([...ANIMALS]);
  });

  it("dùng con máy chủ trả về, không có thì suy cố định từ id", () => {
    expect(animalFor({ id: "u1", avatar: "ech" })).toBe("ech");
    expect(animalFor({ id: "u1", avatar: "khung_long" })).toBe(animalFor({ id: "u1" }));
    expect(animalFor({ id: "abc" })).toBe(animalFor({ id: "abc" }));
  });

  it("có tên đọc cho trình đọc màn hình, ẩn khi chỉ để trang trí", () => {
    expect(renderToStaticMarkup(<AnimalAvatar animal="gau_truc" />)).toContain('aria-label="Ảnh đại diện: Gấu trúc"');
    expect(renderToStaticMarkup(<AnimalAvatar animal="gau_truc" decorative />)).toContain('aria-hidden="true"');
  });
});

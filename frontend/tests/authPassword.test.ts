import { describe, expect, it } from "vitest";
import { isCommonPassword, passwordRules, passwordStrength } from "../src/auth/authApi";

// ADR-040: điều kiện mật khẩu phía trình duyệt phải khớp backend (password_problem), thước đo độ mạnh tự viết.
describe("mật khẩu", () => {
  it("chặn mật khẩu phổ biến không phân biệt hoa thường", () => {
    expect(isCommonPassword("Password1")).toBe(true);
    expect(isCommonPassword("nhacly2026")).toBe(false);
  });

  it("chặn mật khẩu chứa phần trước @ của email hoặc tên sản phẩm", () => {
    const last = (pw: string, email = "") => passwordRules(pw, email).at(-1)!.ok;
    expect(last("phucnguyen99", "phucnguyen@gmail.com")).toBe(false);
    expect(last("toiHarmonyMentor1")).toBe(false);
    expect(last("giaiDieu2027", "phuc@gmail.com")).toBe(true);
  });

  it("thước đo: chưa đủ điều kiện là Yếu, dài và đa dạng là Mạnh", () => {
    expect(passwordStrength("")).toEqual({ score: 0, label: "" });
    expect(passwordStrength("abc").label).toBe("Yếu");
    expect(passwordStrength("abcd1234").label).toBe("Yếu"); // phổ biến
    expect(passwordStrength("nhacly2026").label).toBe("Khá");
    expect(passwordStrength("Hoc nhac 2026!").label).toBe("Mạnh");
    expect(passwordStrength("aaaa1111bbbb").score).toBeLessThan(3); // lặp ký tự bị trừ điểm
  });
});

// takeTokenFromHash cần DOM nên được kiểm ở E2E (e2e-live/mat-khau.live.ts: địa chỉ không còn #token).

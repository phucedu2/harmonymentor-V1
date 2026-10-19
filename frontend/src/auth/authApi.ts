import { http, httpPost, type AuthResponse, type User } from "../lib/http";

// Đường dẫn và hình dạng dữ liệu theo docs/decisions/ADR-004-hop-dong-xac-thuc.md.
export type RegisterInput = { email: string; password: string; display_name: string };
export type ProfilePatch = Partial<Pick<User, "display_name" | "preferred_instrument">>;

export const authApi = {
  register: (input: RegisterInput) => httpPost<AuthResponse>("/auth/register", input, { auth: false }),
  login: (email: string, password: string) => httpPost<AuthResponse>("/auth/login", { email, password }, { auth: false }),
  logout: () => httpPost<void>("/auth/logout", undefined, { auth: false }),
  me: () => http<User>("/me"),
  updateMe: (patch: ProfilePatch) => http<User>("/me", { method: "PATCH", body: JSON.stringify(patch) }),
};

/** Mật khẩu theo NFR-19; backend vẫn kiểm tra lại, đây chỉ để báo sớm cho người dùng. */
export function passwordRules(password: string) {
  return [
    { label: "Ít nhất 8 ký tự", ok: password.length >= 8 },
    { label: "Có ít nhất một chữ cái", ok: /\p{L}/u.test(password) },
    { label: "Có ít nhất một chữ số", ok: /\d/.test(password) },
  ];
}

/** Chỉ cho quay lại đường dẫn nội bộ, tránh ?next=https://trang-la.com (open redirect). */
export function safeNext(next: string | null): string {
  if (next && next.startsWith("/") && !next.startsWith("//") && !next.startsWith("/\\")) return next;
  return "/app";
}

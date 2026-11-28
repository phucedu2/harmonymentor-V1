import { http, httpPost, type AuthResponse, type User } from "../lib/http";
import commonPasswordsRaw from "./common-passwords.txt?raw";

// Đường dẫn và hình dạng dữ liệu theo docs/decisions/ADR-004-hop-dong-xac-thuc.md và ADR-040.
export type RegisterInput = { email: string; password: string; display_name: string };
export type ProfilePatch = Partial<Pick<User, "display_name" | "preferred_instrument">> & { avatar?: string | null };
/** 1A (ADR-040): email đã có tài khoản thì máy chủ trả 202 "kiểm tra hộp thư" thay vì báo lỗi lộ email. */
export type RegisterPending = { status: "check_email"; message: string };
export type RegisterResult = AuthResponse | RegisterPending;
export type Message = { message: string };

export const authApi = {
  register: (input: RegisterInput) => httpPost<RegisterResult>("/auth/register", input, { auth: false }),
  login: (email: string, password: string, remember = true) =>
    httpPost<AuthResponse>("/auth/login", { email, password, remember }, { auth: false }),
  logout: () => httpPost<void>("/auth/logout", undefined, { auth: false }),
  me: () => http<User>("/me"),
  updateMe: (patch: ProfilePatch) => http<User>("/me", { method: "PATCH", body: JSON.stringify(patch) }),
  forgotPassword: (email: string) => httpPost<Message>("/auth/forgot-password", { email }, { auth: false }),
  checkResetToken: (token: string) => httpPost<{ email_masked: string }>("/auth/reset-password/check", { token }, { auth: false }),
  resetPassword: (token: string, new_password: string) =>
    httpPost<Message>("/auth/reset-password", { token, new_password }, { auth: false }),
  changePassword: (current_password: string, new_password: string, sign_out_others: boolean) =>
    httpPost<AuthResponse>("/auth/change-password", { current_password, new_password, sign_out_others }),
  verifyEmail: (token: string) => httpPost<Message>("/auth/verify-email", { token }, { auth: false }),
  resendVerification: () => httpPost<Message>("/auth/resend-verification"),
};

export function isPending(result: RegisterResult): result is RegisterPending {
  return (result as RegisterPending).status === "check_email";
}

/** Danh sách 1.000 mật khẩu phổ biến, giống hệt file backend (pytest kiểm hai file khớp nhau). */
const COMMON_PASSWORDS = new Set(
  commonPasswordsRaw.split("\n").map((line) => line.trim()).filter((line) => line && !line.startsWith("#")),
);

export function isCommonPassword(password: string) {
  return COMMON_PASSWORDS.has(password.toLowerCase());
}

/** Mật khẩu theo NFR-19 + ADR-040; backend vẫn kiểm tra lại, đây chỉ để báo sớm cho người dùng. */
export function passwordRules(password: string, email = "") {
  const local = email.split("@")[0].trim().toLowerCase();
  const lowered = password.toLowerCase();
  return [
    { label: "Ít nhất 8 ký tự", ok: password.length >= 8 },
    { label: "Có ít nhất một chữ cái", ok: /\p{L}/u.test(password) },
    { label: "Có ít nhất một chữ số", ok: /\d/.test(password) },
    {
      label: "Không phải mật khẩu phổ biến, không chứa email hay tên HarmonyMentor",
      ok: password.length > 0 && !isCommonPassword(password) && !lowered.includes("harmonymentor")
        && !(local.length >= 4 && lowered.includes(local)),
    },
  ];
}

export type Strength = { score: 0 | 1 | 2 | 3; label: "" | "Yếu" | "Khá" | "Mạnh" };

/** Thước đo độ mạnh tự viết (5A, không thêm thư viện): độ dài, độ đa dạng ký tự, trừ điểm chuỗi lặp/liên tiếp.
 *  Chỉ để gợi ý; điều kiện bắt buộc vẫn là passwordRules. */
export function passwordStrength(password: string, email = ""): Strength {
  if (!password) return { score: 0, label: "" };
  if (!passwordRules(password, email).every((r) => r.ok)) return { score: 1, label: "Yếu" };
  let points = Math.min(password.length, 20) - 8; // 0..12 điểm cho độ dài trên 8
  const classes = [/[a-z]/, /[A-Z]/, /\d/, /[^\p{L}\d]/u].filter((re) => re.test(password)).length;
  points += (classes - 2) * 3;
  if (/(.)\1\1/.test(password)) points -= 3; // aaa, 111
  if (/(?:0123|1234|2345|3456|4567|5678|6789|abcd|bcde|qwer|asdf)/i.test(password)) points -= 3;
  if (points >= 7) return { score: 3, label: "Mạnh" };
  if (points >= 2) return { score: 2, label: "Khá" };
  return { score: 1, label: "Yếu" };
}

/** Chỉ cho quay lại đường dẫn nội bộ, tránh ?next=https://trang-la.com (open redirect). */
export function safeNext(next: string | null): string {
  if (next && next.startsWith("/") && !next.startsWith("//") && !next.startsWith("/\\")) return next;
  return "/app";
}

/** Lấy token sau dấu # (2A) rồi xóa khỏi thanh địa chỉ để không lọt vào lịch sử trình duyệt hay ảnh chụp màn hình. */
export function takeTokenFromHash(): string {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const token = params.get("token") ?? "";
  if (window.location.hash) window.history.replaceState(window.history.state, "", window.location.pathname);
  return token;
}

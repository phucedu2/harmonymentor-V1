// FE-028: test giao diện với BACKEND THẬT (đăng ký/đăng nhập, làm bài, ôn thẻ). Khác playwright.config.ts (backend bị chặn).
// Tự dựng: backend (CSDL SQLite mới, bản seed nội dung) + bản build qua vite preview có proxy /api sang backend đó.
// Chạy: npm run build && npm run e2e:live   (cần Python 3.11 + pip install -r ../backend/requirements.txt)
import { defineConfig, devices } from "@playwright/test";

const API = process.env.E2E_API_PORT || "8010";
const WEB = 4181;
// ADR-040: E2E_MAILPIT=1 bật test quên/đổi mật khẩu; thư đi vào Mailpit (SMTP 1025, web/API 8025).
// MAILPIT_BIN=đường-dẫn-file-mailpit thì tự chạy Mailpit; CI dùng service container nên không cần.
const MAIL = process.env.E2E_MAILPIT
  ? { EMAIL_BACKEND: "smtp", SMTP_HOST: "127.0.0.1", SMTP_PORT: "1025", FRONTEND_BASE_URL: `http://localhost:${WEB}` }
  : {};
// Mọi tài khoản thử đều đăng ký từ 127.0.0.1: nới giới hạn 10 lần/IP/giờ cho riêng lần chạy test.
const BACKEND_ENV = { ...process.env as Record<string, string>, ...MAIL, REGISTER_PER_IP_HOUR: "1000" };
export default defineConfig({
  testDir: "e2e-live",
  testMatch: "**/*.live.ts",
  workers: 1, // SQLite cho một người ghi một lúc; mỗi test dùng tài khoản riêng nên không phụ thuộc thứ tự
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  timeout: 60_000,
  reporter: process.env.CI ? [["list"], ["html", { open: "never", outputFolder: "playwright-report-live" }]] : "list",
  use: { baseURL: `http://localhost:${WEB}`, trace: "off", locale: "vi-VN" },
  projects: [{ name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } }],
  webServer: [
    ...(process.env.MAILPIT_BIN
      ? [{ command: `${process.env.MAILPIT_BIN} --smtp 127.0.0.1:1025 --listen 127.0.0.1:8025`, url: "http://127.0.0.1:8025/livez", timeout: 30_000, reuseExistingServer: true }]
      : []),
    { command: "node e2e-live/chay-backend.mjs", url: `http://127.0.0.1:${API}/api/v1/lessons`, timeout: 120_000, reuseExistingServer: false,
      env: BACKEND_ENV },
    { command: `npx vite preview --port ${WEB} --strictPort`, port: WEB, timeout: 60_000, reuseExistingServer: false,
      env: { ...process.env as Record<string, string>, API_PROXY: `http://127.0.0.1:${API}` } },
  ],
});

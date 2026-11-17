// FE-028: test giao diện với BACKEND THẬT (đăng ký/đăng nhập, làm bài, ôn thẻ). Khác playwright.config.ts (backend bị chặn).
// Tự dựng: backend (CSDL SQLite mới, bản seed nội dung) + bản build qua vite preview có proxy /api sang backend đó.
// Chạy: npm run build && npm run e2e:live   (cần Python 3.11 + pip install -r ../backend/requirements.txt)
import { defineConfig, devices } from "@playwright/test";

const API = process.env.E2E_API_PORT || "8010";
const WEB = 4181;
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
    { command: "node e2e-live/chay-backend.mjs", url: `http://127.0.0.1:${API}/api/v1/lessons`, timeout: 120_000, reuseExistingServer: false },
    { command: `npx vite preview --port ${WEB} --strictPort`, port: WEB, timeout: 60_000, reuseExistingServer: false,
      env: { ...process.env as Record<string, string>, API_PROXY: `http://127.0.0.1:${API}` } },
  ],
});

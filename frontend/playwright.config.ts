// FE-027: test giao diện bằng trình duyệt thật (Playwright), chạy trên bản build như người dùng thấy.
// Không cần backend: mọi /api bị chặn trong từng test (xem e2e/fixtures.ts) để kết quả không phụ thuộc dữ liệu.
// File test đặt đuôi .e2e.ts để Vitest (bắt *.test.ts / *.spec.ts) không chạy nhầm.
import { defineConfig, devices } from "@playwright/test";

const PORT = 4179;
export default defineConfig({
  testDir: "e2e",
  testMatch: "**/*.e2e.ts",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: { baseURL: `http://localhost:${PORT}`, trace: "off", locale: "vi-VN" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
    { name: "dien-thoai", use: { ...devices["Pixel 7"] } },
  ],
  // Bản build có sẵn (npm run build) được phục vụ bằng vite preview; CI build ở bước trước.
  webServer: { command: `npx vite preview --port ${PORT} --strictPort`, port: PORT, reuseExistingServer: !process.env.CI, timeout: 60_000 },
});

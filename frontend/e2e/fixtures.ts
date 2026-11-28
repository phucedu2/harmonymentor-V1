import { test as base, expect } from "@playwright/test";

// Chặn mọi gọi API: trang phải tự xử lý khi backend không trả lời (hiện thông báo, không văng lỗi JS).
// Lỗi JS chưa bắt (pageerror) làm test đỏ ở mọi trang.
export const test = base.extend<{ pageErrors: string[] }>({
  pageErrors: [async ({ page }, use) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.route("**/api/**", (route) => route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"backend tắt trong test giao diện"}' }));
    await use(errors);
    expect(errors, "lỗi JavaScript chưa bắt").toEqual([]);
  }, { auto: true }],
});
export { expect };

/** Số px trang rộng hơn khung nhìn (0 là không có cuộn ngang). */
export const horizontalOverflow = (page: import("@playwright/test").Page) =>
  page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);

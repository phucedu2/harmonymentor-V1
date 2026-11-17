import { expect, horizontalOverflow, test } from "./fixtures";

const PUBLIC_PAGES = [["Trang chủ", "/"], ["Đăng nhập", "/dang-nhap"], ["Đăng ký", "/dang-ky"], ["404", "/khong-co-trang-nay"]] as const;

for (const [name, url] of PUBLIC_PAGES) {
  test(`${name}: có tiêu đề h1 và không cuộn ngang`, async ({ page }) => {
    await page.goto(url);
    await expect(page.locator("h1").first()).toBeVisible();
    expect(await horizontalOverflow(page)).toBeLessThanOrEqual(0);
  });
}

test("Vào /app khi chưa đăng nhập thì chuyển về trang đăng nhập", async ({ page }) => {
  await page.goto("/app");
  await expect(page).toHaveURL(/\/dang-nhap/);
});

test("Ô nhập đăng nhập có nhãn đọc được", async ({ page }) => {
  await page.goto("/dang-nhap");
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Mật khẩu")).toBeVisible();
});

test("Nút sáng/tối đổi theme và nhớ sau khi tải lại (FE-014)", async ({ page }) => {
  await page.goto("/dang-nhap");
  const html = page.locator("html");
  const before = await html.getAttribute("data-theme");
  await page.getByRole("button", { name: /Bấm để chuyển sang/ }).first().click();
  const after = await html.getAttribute("data-theme");
  expect(after).not.toBe(before);
  await page.reload();
  await expect(html).toHaveAttribute("data-theme", after ?? "");
});

test("Nhận diện mặc định là Sân khấu, ?brand=dong-gi đổi về Đồng & Gỉ (ADR-026)", async ({ page }) => {
  await page.goto("/dang-nhap");
  await expect(page.locator("html")).toHaveAttribute("data-brand", "san-khau");
  await expect(page.locator('link[rel=icon][type="image/svg+xml"]')).toHaveAttribute("href", "/favicon-san-khau.svg");
  await page.goto("/dang-nhap?brand=dong-gi");
  await expect(page.locator("html")).not.toHaveAttribute("data-brand", /.+/);
});

test("Font Fraunces 600 không bị bộ chữ latin đè (FE-025: vỡ dấu tiếng Việt)", async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() => document.fonts.ready);
  const fullRange = await page.evaluate(() => [...document.fonts]
    .filter((f) => f.family.replace(/"/g, "") === "Fraunces" && f.style === "normal" && f.unicodeRange.toUpperCase().includes("U+0-10FFFF")).length);
  expect(fullRange).toBe(0);
});

test.describe("Giảm chuyển động", () => {
  test.use({ reducedMotion: "reduce" });
  test("Trang chủ không chạy hoạt ảnh nào và không tải GSAP (FE-024, FE-026)", async ({ page }) => {
    const scripts: string[] = [];
    page.on("request", (r) => { if (r.resourceType() === "script") scripts.push(r.url()); });
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    // Trừ vòng xoay "đang tải": đó là tín hiệu trạng thái cần thấy, không phải trang trí (WCAG 2.3.3 cho phép).
    const running = await page.evaluate(() => document.getAnimations().filter((a) => a.playState === "running" && (a as CSSAnimation).animationName !== "spin")
      .map((a) => `${(a as CSSAnimation).animationName} ${((a.effect as KeyframeEffect)?.target as HTMLElement)?.className}`));
    expect(running).toEqual([]);
    expect(scripts.some((u) => /ScrollTrigger|lenis/i.test(u))).toBe(false);
  });
});

test("Trang chủ cho phép chuyển động thì tải GSAP sau khi trang đã hiện (FE-026)", async ({ page }) => {
  const gsapLoaded = page.waitForRequest(/ScrollTrigger/);
  await page.goto("/");
  await expect(page.locator("h1").first()).toBeVisible();
  await gsapLoaded;
});

import { expect, test } from "./fixtures";

// Nút AI Tutor chỉ có trong khu /app (cần đăng nhập). Giả lập phiên bằng cách trả lời /auth/refresh và /auth/me.
test.describe("AI Tutor kéo được (FE-023)", () => {
  test.skip(({ isMobile }) => !!isMobile, "kéo chuột: chạy trên desktop; điện thoại cần thử tay");
  test("Kéo nút AI sang trái thì nút bám mép trái và nhớ vị trí", async ({ page }) => {
    const user = { id: "u1", email: "e2e@vd.vn", display_name: "E2E", role: "learner", preferred_instrument: null, goal_text: null };
    await page.route("**/api/v1/auth/refresh", (r) => r.fulfill({ json: { access_token: "t", token_type: "bearer", expires_in: 900, user } }));
    await page.route("**/api/v1/auth/me", (r) => r.fulfill({ json: user }));
    await page.addInitScript(() => { try { localStorage.setItem("hm.has-session", "1"); } catch { /* */ } });
    await page.goto("/app");
    const fab = page.getByRole("button", { name: "Mở AI Tutor" });
    await expect(fab).toBeVisible();
    const box = (await fab.boundingBox())!;
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(200, box.y, { steps: 8 });
    await page.mouse.up();
    const after = (await fab.boundingBox())!;
    expect(after.x).toBeLessThan(40);
    expect(await page.evaluate(() => localStorage.getItem("hm-ai-nut"))).not.toBeNull();
  });
});

// ADR-029: khung AI Tutor như cửa sổ thật (đổi cỡ, phóng to, nhớ cỡ) và menu ảnh đại diện ở góc phải trên.
test.describe("Cửa sổ AI Tutor và menu tài khoản (ADR-029)", () => {
  test.skip(({ isMobile }) => !!isMobile, "kéo chuột: chạy trên desktop");
  const user = { id: "u1", email: "e2e@vd.vn", display_name: "E2E", role: "learner", preferred_instrument: null, goal_text: null, avatar: "cu" };
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/auth/refresh", (r) => r.fulfill({ json: { access_token: "t", token_type: "bearer", expires_in: 900, user } }));
    await page.route("**/api/v1/auth/me", (r) => r.fulfill({ json: user }));
    await page.addInitScript(() => { try { localStorage.setItem("hm.has-session", "1"); } catch { /* */ } });
  });

  test("Kéo góc để đổi cỡ, nhớ cỡ, phóng to rồi thu về", async ({ page }) => {
    await page.goto("/app");
    await page.getByRole("button", { name: "Mở AI Tutor" }).click();
    const dialog = page.getByRole("dialog", { name: "AI Tutor" });
    const before = (await dialog.boundingBox())!;
    const corner = (await dialog.locator('[data-edge="nw"]').boundingBox())!;
    await page.mouse.move(corner.x + 9, corner.y + 9);   // góc bo tròn cắt mất vùng sát mép
    await page.mouse.down();
    await page.mouse.move(corner.x - 120, corner.y - 60, { steps: 8 });
    await page.mouse.up();
    const after = (await dialog.boundingBox())!;
    expect(after.width).toBeGreaterThan(before.width + 100);
    expect(Math.abs(after.x + after.width - (before.x + before.width))).toBeLessThan(3);   // mép phải đứng yên
    expect(await page.evaluate(() => localStorage.getItem("hm-ai-khung-co"))).not.toBeNull();

    await dialog.getByRole("button", { name: "Phóng to AI Tutor" }).click();
    const big = (await dialog.boundingBox())!;
    expect(big.width).toBeGreaterThan(page.viewportSize()!.width - 60);
    await dialog.getByRole("button", { name: "Thu khung AI Tutor về cỡ cũ" }).click();
    expect(Math.round((await dialog.boundingBox())!.width)).toBe(Math.round(after.width));

    await dialog.getByRole("button", { name: "Thu nhỏ AI Tutor" }).click();
    await expect(dialog.getByRole("textbox")).toHaveCount(0);
    await dialog.getByRole("button", { name: "Mở lại khung AI Tutor" }).click();
    await expect(dialog.getByRole("textbox")).toBeVisible();
  });

  test("Ảnh đại diện ở góc phải mở menu Hồ sơ và Đăng xuất", async ({ page }) => {
    await page.goto("/app");
    const avatar = page.getByRole("button", { name: "Tài khoản: E2E" });
    await expect(avatar).toBeVisible();
    const box = (await avatar.boundingBox())!;
    expect(box.x).toBeGreaterThan(page.viewportSize()!.width / 2);
    await expect(page.getByRole("link", { name: "Hồ sơ" })).toHaveCount(0);   // không còn ở thanh bên
    await avatar.click();
    const menu = page.getByRole("menu", { name: "Tài khoản" });
    await expect(menu.getByRole("menuitem", { name: "Hồ sơ" })).toBeFocused();
    await expect(menu.getByRole("menuitem", { name: "Đăng xuất" })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(menu).toHaveCount(0);
    await expect(avatar).toBeFocused();
    await avatar.click();
    await menu.getByRole("menuitem", { name: "Hồ sơ" }).click();
    await expect(page).toHaveURL(/\/app\/ho-so$/);
  });
});

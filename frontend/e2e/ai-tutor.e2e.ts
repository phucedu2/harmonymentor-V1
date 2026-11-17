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

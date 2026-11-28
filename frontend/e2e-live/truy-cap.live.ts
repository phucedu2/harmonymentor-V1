// ADR-040, C3 + D3: kiểm truy cập các trang tài khoản (axe-core, phím Tab, màn 375px) và chụp ảnh minh chứng.
// Ảnh chỉ ghi khi AUTH_ANH=<thư mục> (ví dụ ../docs/minh-chung/anh/tai-khoan), để chạy CI không sinh file.
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import path from "node:path";
import { dangKy, dangXuat } from "./giup";
import { lienKet, thuMoiNhat } from "./thu";

const ANH = process.env.AUTH_ANH;
test.skip(!process.env.E2E_MAILPIT, "cần Mailpit (đặt E2E_MAILPIT=1)");

const SIZES = [{ name: "may-tinh", width: 1440, height: 900 }, { name: "dien-thoai", width: 375, height: 812 }] as const;
const THEMES = ["light", "dark"] as const;

async function kiem(page: Page, label: string) {
  // Không lỗi axe mức nghiêm trọng/cao trên vùng nội dung trang tài khoản.
  const result = await new AxeBuilder({ page }).include("#noi-dung").withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
  const bad = result.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(bad.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`), label).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth), `${label} cuộn ngang`).toBeLessThanOrEqual(0);
}

async function chup(page: Page, name: string) {
  for (const theme of THEMES) {
    await page.evaluate((t) => { document.documentElement.dataset.theme = t; }, theme);
    for (const size of SIZES) {
      await page.setViewportSize({ width: size.width, height: size.height });
      await page.waitForTimeout(150);
      await kiem(page, `${name} ${theme} ${size.name}`);
      if (ANH) await page.screenshot({ path: path.join(ANH, `${name}-${theme === "light" ? "sang" : "toi"}-${size.name}.png`), fullPage: true });
    }
  }
  await page.setViewportSize({ width: SIZES[0].width, height: SIZES[0].height });
  await page.evaluate(() => { document.documentElement.dataset.theme = "light"; });
}

test("Các trang tài khoản: axe-core, 375px, ảnh sáng/tối", async ({ page }) => {
  test.setTimeout(180_000);
  await page.goto("/dang-nhap");
  await expect(page.getByRole("heading", { name: "Đăng nhập" })).toBeVisible();
  await chup(page, "01-dang-nhap");

  // Lỗi tổng nhận focus và có role=alert.
  await page.getByLabel("Email").fill("ai-do@example.test");
  await page.getByLabel("Mật khẩu", { exact: true }).fill("sai-mat-khau-1");
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.locator(":focus")).toContainText("Email hoặc mật khẩu chưa đúng");
  await chup(page, "02-dang-nhap-loi");

  await page.goto("/dang-ky");
  await page.getByLabel("Mật khẩu", { exact: true }).fill("Hoc nhac 2026");
  await chup(page, "03-dang-ky");

  await page.goto("/quen-mat-khau");
  await chup(page, "04-quen-mat-khau");
  await page.getByLabel("Email").fill("khach@example.test");
  await page.getByRole("button", { name: "Gửi liên kết đặt lại" }).click();
  await expect(page.getByRole("heading", { name: "Kiểm tra hộp thư của bạn" })).toBeVisible();
  await chup(page, "05-kiem-tra-hop-thu");

  await page.goto("/dat-lai-mat-khau#token=lien-ket-sai");
  await expect(page.getByRole("heading", { name: "Liên kết đã hết hạn hoặc đã được dùng" })).toBeVisible();
  await chup(page, "06-lien-ket-het-han");

  const user = await dangKy(page);
  await page.goto("/app/ho-so");
  await expect(page.getByRole("heading", { name: "Bảo mật" })).toBeVisible();
  await chup(page, "08-ho-so-bao-mat");
  await dangXuat(page);

  await page.goto("/quen-mat-khau");
  await page.getByLabel("Email").fill(user.email);
  await page.getByRole("button", { name: "Gửi liên kết đặt lại" }).click();
  const mail = await thuMoiNhat(user.email, "Reset your HarmonyMentor password");
  await page.goto(lienKet(mail.text, "/dat-lai-mat-khau"));
  await expect(page.getByRole("heading", { name: "Đặt mật khẩu mới" })).toBeVisible();
  await page.getByLabel("Mật khẩu mới").fill("giaiDieu2027");
  await chup(page, "07-dat-mat-khau-moi");

  if (ANH) {
    // Ảnh thư trong giao diện Mailpit (D3).
    await page.setViewportSize({ width: 1200, height: 900 });
    await page.goto(`${process.env.MAILPIT_URL || "http://127.0.0.1:8025"}/view/${mail.id}`);
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(ANH, "09-thu-dat-lai-mailpit.png"), fullPage: true });
  }
});

test("Đi hết form đăng nhập bằng phím Tab theo đúng thứ tự", async ({ page }) => {
  await page.goto("/dang-nhap");
  await expect(page.getByLabel("Email")).toBeFocused(); // focus tự vào ô đầu
  const order = ["Quên mật khẩu?", "Mật khẩu", "Hiện mật khẩu", "Ghi nhớ đăng nhập", "Đăng nhập"];
  for (const name of order) {
    await page.keyboard.press("Tab");
    const focused = await page.evaluate(() => {
      const el = document.activeElement as HTMLElement | null;
      const label = el?.id ? document.querySelector(`label[for="${el.id}"]`)?.textContent : null;
      return `${el?.textContent ?? ""} ${label ?? ""} ${el?.closest("label")?.textContent ?? ""}`;
    });
    expect(focused, `Tab tới ${name}`).toContain(name);
  }
});

// ADR-040, C2: đăng ký → đăng xuất → quên mật khẩu → mở thư qua Mailpit → đặt mật khẩu mới →
// mật khẩu mới vào được, mật khẩu cũ thì không → đổi mật khẩu trong Hồ sơ.
// Cần Mailpit chạy (playwright.live.config.ts tự bật khi có E2E_MAILPIT=1, CI dùng service container).
import { expect, test } from "@playwright/test";
import { dangKy, dangXuat, PASSWORD, taiKhoanMoi } from "./giup";
import { lienKet, thuMoiNhat } from "./thu";

const MOI = "giaiDieu2027";
const MOI_NUA = "hoaAm2028x";

test.skip(!process.env.E2E_MAILPIT, "cần Mailpit (đặt E2E_MAILPIT=1)");

async function dangNhap(page: import("@playwright/test").Page, email: string, password: string) {
  await page.goto("/dang-nhap");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Mật khẩu", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
}

test("Quên mật khẩu qua email rồi đổi mật khẩu trong Hồ sơ", async ({ page }) => {
  const user = taiKhoanMoi();
  await dangKy(page, user);
  // Thư xác minh email gửi ngay khi đăng ký (A7).
  const verify = await thuMoiNhat(user.email, "Verify your email");
  expect(verify.text).toContain("/xac-minh-email#token=");
  await dangXuat(page);

  // Đăng nhập → "Quên mật khẩu?" giữ email đã gõ.
  await page.goto("/dang-nhap");
  await page.getByLabel("Email").fill(user.email);
  await page.getByRole("link", { name: "Quên mật khẩu?" }).click();
  await expect(page).toHaveURL(/\/quen-mat-khau$/);
  await expect(page.getByLabel("Email")).toHaveValue(user.email);
  await page.getByRole("button", { name: "Gửi liên kết đặt lại" }).click();
  await expect(page.getByRole("heading", { name: "Kiểm tra hộp thư của bạn" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Gửi lại sau \d+ giây/ })).toBeDisabled();

  // Mở thư, bấm liên kết: token biến khỏi thanh địa chỉ ngay.
  const mail = await thuMoiNhat(user.email, "Reset your HarmonyMentor password");
  expect(mail.text).toContain("expires in 30 minutes");
  expect(mail.text).not.toContain(PASSWORD); // thư không bao giờ chứa mật khẩu
  const link = lienKet(mail.text, "/dat-lai-mat-khau");
  await page.goto(link);
  await expect(page.getByRole("heading", { name: "Đặt mật khẩu mới" })).toBeVisible();
  await expect(page).toHaveURL(/\/dat-lai-mat-khau$/);
  await expect(page.locator('meta[name="referrer"]')).toHaveAttribute("content", "no-referrer");
  await expect(page.getByText(/\*\*\*@example\.test/)).toBeVisible();
  await page.getByLabel("Mật khẩu mới").fill(MOI);
  await expect(page.getByText("Mạnh").or(page.getByText("Khá")).first()).toBeVisible();
  await page.getByRole("button", { name: "Lưu mật khẩu mới" }).click();
  await expect(page).toHaveURL(/\/dang-nhap\?da-dat-lai=1/);
  await expect(page.getByText("Đã đặt lại mật khẩu. Hãy đăng nhập bằng mật khẩu mới.")).toBeVisible();
  await thuMoiNhat(user.email, "Your password was changed");

  // Liên kết đã dùng thì hỏng.
  await page.goto(link);
  await expect(page.getByRole("heading", { name: "Liên kết đã hết hạn hoặc đã được dùng" })).toBeVisible();

  // Mật khẩu cũ hỏng, mật khẩu mới vào được.
  await dangNhap(page, user.email, PASSWORD);
  await expect(page.getByRole("alert")).toContainText("Email hoặc mật khẩu chưa đúng");
  await dangNhap(page, user.email, MOI);
  await expect(page).toHaveURL(/\/app$/);

  // Đổi mật khẩu trong Hồ sơ.
  await page.goto("/app/ho-so");
  await expect(page.getByRole("heading", { name: "Bảo mật" })).toBeVisible();
  await expect(page.getByText(/Mật khẩu đổi lần cuối:/)).toBeVisible();
  await page.getByLabel("Mật khẩu hiện tại").fill("sai-mat-khau-9");
  await page.getByLabel("Mật khẩu mới").fill(MOI_NUA);
  await page.getByRole("button", { name: "Đổi mật khẩu" }).click();
  await expect(page.getByText("✗ Mật khẩu hiện tại chưa đúng.")).toBeVisible();
  await page.getByLabel("Mật khẩu hiện tại").fill(MOI);
  await page.getByRole("button", { name: "Đổi mật khẩu" }).click();
  await expect(page.getByText("Đã đổi mật khẩu. Các thiết bị khác đã được đăng xuất.")).toBeVisible();
  // Phiên hiện tại vẫn dùng được sau khi đổi (máy chủ cấp phiên mới).
  await page.reload();
  await expect(page.getByRole("heading", { name: "Bảo mật" })).toBeVisible();
  await thuMoiNhat(user.email, "Your password was changed", 2);

  await dangXuat(page);
  await dangNhap(page, user.email, MOI_NUA);
  await expect(page).toHaveURL(/\/app$/);
});

test("Xác minh email từ liên kết trong thư, banner Hồ sơ biến mất", async ({ page }) => {
  const user = await dangKy(page);
  await page.goto("/app/ho-so");
  await expect(page.getByText(/Hãy xác minh email/)).toBeVisible();
  const mail = await thuMoiNhat(user.email, "Verify your email");
  await page.goto(lienKet(mail.text, "/xac-minh-email"));
  await expect(page.getByRole("heading", { name: "Đã xác minh email" })).toBeVisible();
  await page.goto("/app/ho-so");
  await expect(page.getByRole("heading", { name: "Bảo mật" })).toBeVisible();
  await expect(page.getByText(/Hãy xác minh email/)).toHaveCount(0);
});

test("Quên mật khẩu với email lạ: cùng màn hình, không có thư nào", async ({ page }) => {
  const email = `khong-co-${Date.now()}@example.test`;
  await page.goto("/quen-mat-khau");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Gửi liên kết đặt lại" }).click();
  await expect(page.getByRole("heading", { name: "Kiểm tra hộp thư của bạn" })).toBeVisible();
  await page.waitForTimeout(1500);
  const res = await fetch(`${process.env.MAILPIT_URL || "http://127.0.0.1:8025"}/api/v1/search?query=${encodeURIComponent(`to:"${email}"`)}`);
  expect(((await res.json()) as { messages: unknown[] }).messages).toHaveLength(0);
});

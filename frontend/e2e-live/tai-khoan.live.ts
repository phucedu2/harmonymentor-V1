import { expect, test } from "@playwright/test";
import { dangKy, PASSWORD, taiKhoanMoi } from "./giup";

test("Đăng ký xong vào Tổng quan, đăng xuất rồi đăng nhập lại", async ({ page }) => {
  const user = await dangKy(page);
  await expect(page.getByRole("heading", { name: `Chào ${user.name}` })).toBeVisible();

  await page.getByRole("button", { name: "Đăng xuất" }).click();
  await expect(page).not.toHaveURL(/\/app/);
  await page.goto("/app");
  await expect(page).toHaveURL(/\/dang-nhap/); // khu /app đóng lại sau khi đăng xuất

  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Mật khẩu").fill(PASSWORD);
  await page.locator("form button[type=submit]").click();
  await expect(page).toHaveURL(/\/app/);
  await expect(page.getByRole("heading", { name: `Chào ${user.name}` })).toBeVisible();
});

test("Sai mật khẩu: báo lỗi, ở lại trang đăng nhập, không vào được /app", async ({ page }) => {
  const user = taiKhoanMoi();
  await dangKy(page, user);
  await page.getByRole("button", { name: "Đăng xuất" }).click();

  await page.goto("/dang-nhap");
  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Mật khẩu").fill("sai-mat-khau-1");
  await page.locator("form button[type=submit]").click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page).toHaveURL(/\/dang-nhap/);
});

test("Tải lại trang vẫn giữ phiên đăng nhập (cookie refresh)", async ({ page }) => {
  const user = await dangKy(page);
  await page.reload();
  await expect(page).toHaveURL(/\/app$/);
  await expect(page.getByRole("heading", { name: `Chào ${user.name}` })).toBeVisible();
});

test("Đăng ký trùng email bị từ chối, không tạo phiên", async ({ page }) => {
  const user = await dangKy(page);
  await page.getByRole("button", { name: "Đăng xuất" }).click();
  await page.goto("/dang-ky");
  await page.getByLabel("Tên hiển thị").fill("Người trùng");
  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Mật khẩu", { exact: true }).fill(PASSWORD);
  await page.getByLabel("Nhập lại mật khẩu").fill(PASSWORD);
  await page.locator("form button[type=submit]").click();
  await expect(page.getByRole("alert").or(page.getByText(/đã được dùng|đã tồn tại|đã đăng ký/i)).first()).toBeVisible();
  await expect(page).toHaveURL(/\/dang-ky/);
});

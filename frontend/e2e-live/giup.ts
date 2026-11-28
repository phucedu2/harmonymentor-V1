import { expect, type Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export type DapAn = { title: string; exercises: { id: string; prompt: string; answer: string; choice: boolean; options: string[] }[]; cards: { front: string; answer: string }[] };
/** Đáp án đúng do chay-backend.mjs ghi từ curriculum_specs (nguồn của chính backend vừa chạy). */
export const dapAn = (lesson = "L01"): DapAn => JSON.parse(fs.readFileSync(path.join(os.tmpdir(), "hm-e2e-dap-an.json"), "utf8"))[lesson];

export const PASSWORD = "matkhau123";
export const taiKhoanMoi = () => ({ name: "Minh E2E", email: `e2e-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.test` });

/** Đăng ký qua giao diện; xong ở màn kiểm tra đầu vào rồi chọn "học từ Bài 1" để vào Tổng quan. */
export async function dangKy(page: Page, user = taiKhoanMoi()) {
  await page.goto("/dang-ky");
  await page.getByLabel("Tên hiển thị").fill(user.name);
  await page.getByLabel("Email").fill(user.email);
  // ADR-040: không còn ô "Nhập lại mật khẩu" (đã có nút hiện mật khẩu).
  await page.getByLabel("Mật khẩu", { exact: true }).fill(PASSWORD);
  await page.locator("form button[type=submit]").click();
  await expect(page).toHaveURL(/kiem-tra-dau-vao/);
  await page.getByRole("button", { name: /Chưa học/ }).click();
  await expect(page).toHaveURL(/\/app$/);
  return user;
}

export async function moBai1(page: Page) {
  await page.goto("/app/hoc");
  await page.getByRole("button", { name: /Học ngay/ }).click();
  await expect(page.getByText(/Bước 1\/\d+/)).toBeVisible();
}

// ADR-029: "Đăng xuất" nằm trong menu ảnh đại diện ở góc phải trên cùng.
export async function dangXuat(page: Page) {
  await page.getByRole("button", { name: /^Tài khoản/ }).click();
  await page.getByRole("menuitem", { name: "Đăng xuất" }).click();
}

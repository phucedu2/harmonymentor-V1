import { expect, test } from "@playwright/test";
import { dangKy, dapAn, moBai1 } from "./giup";

// Câu kiểm tra nhanh đầu tiên của Bài 1 nằm ở bước 9. Đề, đáp án và lựa chọn lấy từ chính backend vừa chạy.
async function denCauHoiDau(page: import("@playwright/test").Page) {
  await moBai1(page);
  for (let i = 1; i <= 8; i++) {
    await page.getByRole("button", { name: /Bước tiếp/ }).click();
    await expect(page.getByText(`Bước ${i + 1}/`)).toBeVisible();
  }
}

test("Làm câu trắc nghiệm: sai báo 'Chưa đúng', đúng báo 'Chính xác' và tiến độ được lưu", async ({ page }) => {
  const q = dapAn().exercises.find((e) => e.choice)!;
  const sai = q.options.find((o) => o !== q.answer)!;
  await dangKy(page);
  await denCauHoiDau(page);

  const lua = page.getByRole("group", { name: "Các lựa chọn" });
  await expect(page.getByText(q.prompt).first()).toBeVisible();
  await lua.getByRole("button", { name: sai, exact: true }).click();
  await page.getByRole("button", { name: "Kiểm tra", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Chưa đúng" })).toBeVisible();
  await expect(page.getByText("Đã đúng 0/")).toBeVisible();

  // Sau lần sai nút đổi tên thành "Kiểm tra lại"; nút "Kiểm tra nhanh" là phần luyện thêm, không tính điểm.
  await lua.getByRole("button", { name: q.answer, exact: true }).click();
  await page.getByRole("button", { name: "Kiểm tra lại", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Chính xác!" })).toBeVisible();
  await expect(page.getByText("Đã đúng 1/")).toBeVisible();

  // Tiến độ nằm ở máy chủ: tải lại trang và sang trang Tiến độ vẫn thấy.
  await page.reload();
  await expect(page.getByText("Đã đúng 1/")).toBeVisible();
  await page.goto("/app/tien-do");
  await expect(page.getByText(/Đúng 1\/\d+ câu/).first()).toBeVisible();
});

test("Câu hỏi bị chặn khi chưa chọn đáp án: nút Kiểm tra không gửi bài", async ({ page }) => {
  await dangKy(page);
  await denCauHoiDau(page);
  const gui = page.getByRole("button", { name: "Kiểm tra", exact: true });
  if (await gui.isEnabled()) {
    await gui.click();
    await expect(page.getByRole("status").filter({ hasText: /Chính xác/ })).toHaveCount(0);
  } else {
    await expect(gui).toBeDisabled();
  }
  await expect(page.getByText("Đã đúng 0/")).toBeVisible();
});

import { expect, test } from "@playwright/test";
import { dangKy, dapAn, moBai1 } from "./giup";

// Hoàn thành Bài 1 (12 câu đều đúng, qua giao diện "Xem cả bài") thì tạo 8 thẻ ôn; ôn đúng thẻ lên hộp 2, ôn sai về hộp 1.
test("Hoàn thành bài tạo thẻ ôn; ôn đúng lên hộp 2, ôn sai về hộp 1", async ({ page }) => {
  const bai = dapAn();
  await dangKy(page);
  await moBai1(page);
  await page.getByRole("button", { name: "Xem cả bài" }).click();

  for (const q of bai.exercises) {
    const the = page.locator("div.grid.gap-2").filter({ has: page.locator("b", { hasText: q.prompt }) }).last();
    await the.scrollIntoViewIfNeeded();
    if (q.choice) await the.getByRole("button", { name: q.answer, exact: true }).click();
    else await the.getByLabel(`Câu trả lời: ${q.prompt}`).fill(q.answer);
    await the.getByRole("button", { name: /^Kiểm tra/ }).click();
    await expect(the.getByText("Chính xác!")).toBeVisible();
  }
  const xong = page.getByRole("button", { name: "Hoàn thành và lên lịch ôn" });
  await xong.scrollIntoViewIfNeeded();
  await xong.click();
  await expect(page.getByText("Hoàn thành!").first()).toBeVisible();

  await page.goto("/app/tien-do");
  await expect(page.getByText("bài đã hoàn thành")).toBeVisible();
  const oNhap = page.getByRole("textbox", { name: /^Đáp án cho thẻ: / });
  await expect(oNhap.first()).toBeVisible(); // đợi danh sách thẻ tải xong rồi mới đếm
  expect(await oNhap.count()).toBeGreaterThanOrEqual(2);

  const nhan = async (i: number) => (await oNhap.nth(i).getAttribute("aria-label"))!.replace("Đáp án cho thẻ: ", "");
  const [truocDung, truocSai] = [await nhan(0), await nhan(1)];
  const dung = bai.cards.find((c) => c.front === truocDung)!;

  // Ôn đúng
  await oNhap.nth(0).fill(dung.answer);
  await page.getByRole("button", { name: "Kiểm tra", exact: true }).first().click();
  await expect(page.getByRole("status").filter({ hasText: "Nhớ đúng" })).toContainText("Thẻ lên hộp 2");
  await expect(page.getByRole("list").filter({ hasText: truocDung }).getByText("Hộp 2/5")).toBeVisible();

  // Ôn sai: thẻ thứ hai (nay đứng đầu danh sách nếu thẻ trước đã rời đi)
  const oSai = page.getByRole("textbox", { name: `Đáp án cho thẻ: ${truocSai}` });
  await oSai.fill("dap-an-sai-chac-chan");
  await oSai.locator("xpath=following-sibling::button").click();
  await expect(page.getByRole("status").filter({ hasText: "Chưa đúng" })).toContainText("Thẻ về hộp 1");
});

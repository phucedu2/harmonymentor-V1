// Demo 10/11: hai kịch bản trên giao diện thật (Playwright). Cách chạy: docs/giai-doan/demo-1011/BAO_CAO.md mục 4.
// Kịch bản 1: người mới bỏ placement → làm L01 → gợi ý L02 có lý do → bấm mở L02.
// Kịch bản 2: dựng G7 sai (G B D F#) → Music Engine bắt lỗi → "Giải thích lỗi này" → AI Tutor trả lời có trích dẫn.
const { chromium } = require('playwright');
const fs = require('fs');
const OUT = process.env.OUT, VID = process.env.VID;
const ANS = JSON.parse(fs.readFileSync(process.env.ANS, 'utf8'));
const log = (...a) => console.log('[e2e]', ...a);
async function answerLesson(p, lesson) {
  await p.getByRole('button', { name: 'Xem cả bài' }).click();
  await p.waitForTimeout(1200);
  for (const q of ANS[lesson]) {
    const card = p.locator('div.grid.gap-2').filter({ has: p.locator('b', { hasText: q.prompt }) }).last();
    await card.scrollIntoViewIfNeeded();
    if (q.choice) await card.getByRole('button', { name: q.answer, exact: true }).click();
    else await card.getByLabel(`Câu trả lời: ${q.prompt}`).fill(q.answer);
    await card.getByRole('button', { name: /^Kiểm tra/ }).click();
    await card.getByText('Chính xác!').waitFor({ timeout: 10000 });
  }
  const done = p.getByRole('button', { name: 'Hoàn thành và lên lịch ôn' });
  await done.scrollIntoViewIfNeeded();
  await done.click();
  await p.getByText('Hoàn thành!').first().waitFor({ timeout: 10000 });
}
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1280, height: 860 }, deviceScaleFactor: 2,
                                   recordVideo: { dir: VID, size: { width: 1280, height: 860 } } });
  const p = await ctx.newPage();
  const email = `demo1011-${Date.now()}@example.test`;
  // --- Kịch bản 1: Recommender ---
  await p.goto('http://localhost:5173/dang-ky');
  await p.getByLabel('Tên hiển thị').fill('Học sinh demo');
  await p.getByLabel('Email').fill(email);
  await p.getByLabel('Mật khẩu', { exact: true }).fill('matkhau123');
  await p.getByLabel('Nhập lại mật khẩu').fill('matkhau123');
  await p.getByRole('button', { name: /Đăng ký|Tạo tài khoản/ }).click();
  await p.waitForURL(/kiem-tra-dau-vao/, { timeout: 15000 });
  await p.getByRole('button', { name: 'Bỏ qua, học từ Bài 1' }).click();
  await p.waitForURL(/\/app$/);
  const rec = p.locator('[aria-labelledby="rec-title"]');
  await rec.getByText(/Bài nên học tiếp/).waitFor();
  await p.waitForTimeout(1500);
  await rec.scrollIntoViewIfNeeded();
  await p.screenshot({ path: `${OUT}/01-nguoi-moi-goi-y-ban-dau.png` });
  log('goi y ban dau:', (await rec.innerText()).replace(/\s+/g, ' ').slice(0, 300));
  await p.goto('http://localhost:5173/app/hoc?bai=L01');
  await p.waitForTimeout(1500);
  await answerLesson(p, 'L01');
  await p.screenshot({ path: `${OUT}/02-hoan-thanh-L01.png` });
  await p.goto('http://localhost:5173/app/tien-do').catch(() => {});
  await p.waitForTimeout(1500);
  await p.screenshot({ path: `${OUT}/03-tien-do-sau-L01.png`, fullPage: true });
  await p.goto('http://localhost:5173/app');
  await rec.getByText(/Bài nên học tiếp/).waitFor();
  await p.waitForTimeout(1500);
  const row = rec.locator('li').filter({ hasText: 'Bài 2.' }).first();
  await row.waitFor({ timeout: 10000 });
  await row.getByText('Vì sao gợi ý bài này?').click();
  await row.scrollIntoViewIfNeeded();
  await p.screenshot({ path: `${OUT}/04-goi-y-L02-co-ly-do.png` });
  log('goi y sau L01:', (await rec.innerText()).replace(/\s+/g, ' ').slice(0, 500));
  await row.getByRole('button', { name: /Mở bài/ }).click();
  await p.waitForURL(/bai=L02/, { timeout: 10000 });
  await p.waitForTimeout(2000);
  await p.screenshot({ path: `${OUT}/05-bam-goi-y-mo-L02.png` });
  log('mo bai:', p.url());
  // --- Kịch bản 2: AI Tutor giải thích lỗi ---
  await p.getByRole('button', { name: 'Xem cả bài' }).click();
  await p.waitForTimeout(1200);
  const g7 = ANS['L02'].find(q => q.prompt.startsWith('Dựng G7'));
  const card = p.locator('div.grid.gap-2').filter({ has: p.locator('b', { hasText: g7.prompt }) }).last();
  await card.scrollIntoViewIfNeeded();
  await card.getByLabel(`Câu trả lời: ${g7.prompt}`).fill('G B D F#');
  await card.getByRole('button', { name: /^Kiểm tra/ }).click();
  await card.getByText('Chưa đúng').waitFor({ timeout: 10000 });
  await p.screenshot({ path: `${OUT}/06-sai-G7-engine-bat-loi.png` });
  log('phan hoi engine:', (await card.innerText()).replace(/\s+/g, ' ').slice(0, 300));
  const t0 = Date.now();
  await card.getByRole('button', { name: 'Giải thích lỗi này' }).click();
  await p.getByText('Gợi ý mức 1/3').waitFor({ timeout: 45000 });
  await p.waitForTimeout(800);
  await p.screenshot({ path: `${OUT}/07-giai-thich-loi-muc-1.png` });
  const drawer = p.getByRole('dialog').first();
  log('giai thich (ms=' + (Date.now() - t0) + '):', (await drawer.innerText().catch(() => '')).replace(/\s+/g, ' ').slice(0, 900));
  await ctx.close();
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });

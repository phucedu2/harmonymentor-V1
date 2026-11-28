const { chromium } = require('playwright');
// Chụp vài bước Bài 1 có widget (quãng, hợp âm, piano) ở 1440px và 390px. Chạy: node ... <thư mục> <hậu tố>
const OUT = process.argv[2] || '.'; const TAG = process.argv[3] || 'sau';
const BASE = process.env.BASE_URL || 'http://localhost:5173';
(async () => {
  const b = await chromium.launch();
  for (const [w, h, size] of [[1440, 900, '1440'], [390, 844, '390']]) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    await p.goto(BASE + '/dang-ky'); await p.waitForTimeout(800);
    await p.getByLabel('Tên hiển thị').fill('Học viên thử');
    await p.getByLabel('Email').fill(`b1-${size}-${TAG}-${Date.now()}@vd.vn`);
    await p.getByLabel('Mật khẩu', { exact: true }).fill('MatKhau123!');
    await p.getByLabel('Nhập lại mật khẩu').fill('MatKhau123!');
    await p.getByRole('button', { name: 'Đăng ký' }).click(); await p.waitForTimeout(2000);
    await p.goto(BASE + '/app/hoc'); await p.waitForTimeout(1200);
    await p.locator('[data-lesson-id="L01"]').click(); await p.waitForTimeout(1500);
    for (const n of [4, 6, 7, 8]) {
      await p.getByText('Mục lục bài học').click(); await p.waitForTimeout(300);
      await p.locator('details ol li button').nth(n).click(); await p.waitForTimeout(1500);
      await p.screenshot({ path: `${OUT}/11-bai-1-buoc-${n + 1}-${size}-${TAG}.png`, fullPage: true });
    }
    await p.close();
  }
  await b.close();
})();

const { chromium } = require('playwright');
// Ảnh lộ trình Bước 2: trang Học theo Bảng 7. Chạy hai lần: backend thường và backend SHOW_DRAFT_CONTENT=1.
// Chạy: node scripts/phuc-music/luong_buoc2_lotrinh.cjs <thư mục ảnh> <hậu tố>
const OUT = process.argv[2] || '.';
const TAG = process.argv[3] || 'nguoi-hoc';
const BASE = process.env.BASE_URL || 'http://localhost:5173';
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
  await p.goto(BASE + '/dang-ky'); await p.waitForTimeout(1200);
  await p.getByLabel('Tên hiển thị').fill('Học viên thử');
  await p.getByLabel('Email').fill(`lo-${TAG}-${Date.now()}@vd.vn`);
  await p.getByLabel('Mật khẩu', { exact: true }).fill('MatKhau123!');
  await p.getByLabel('Nhập lại mật khẩu').fill('MatKhau123!');
  await p.getByRole('button', { name: 'Đăng ký' }).click(); await p.waitForTimeout(2500);
  await p.getByRole('link', { name: 'Học', exact: true }).first().click(); await p.waitForTimeout(1800);
  await p.screenshot({ path: `${OUT}/03-lo-trinh-${TAG}.png`, fullPage: true });
  console.log(TAG, (await p.locator('[data-lesson-id]').allInnerTexts()).map((t) => t.split('\n').slice(0, 3).join(' / ')).join('\n'));
  if (TAG === 'che-do-nhap') {
    await p.locator('[data-lesson-id]').first().click(); await p.waitForTimeout(2000);
    await p.getByRole('button', { name: 'Xem cả bài' }).click().catch(() => {}); await p.waitForTimeout(1200);
    const block = p.getByText('Dùng vào sáng tác').last();
    await block.scrollIntoViewIfNeeded(); await p.waitForTimeout(500);
    await p.screenshot({ path: `${OUT}/04-l01-dung-vao-sang-tac-${TAG}.png` });
  }
  await b.close();
})();

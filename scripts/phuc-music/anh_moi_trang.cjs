const { chromium } = require('playwright');
// Chụp mọi trang ở 1440px và 390px (Bước 3: ảnh trước/sau). Cần backend :8000 và frontend :5173.
// Chạy: node scripts/phuc-music/anh_moi_trang.cjs <thư mục ảnh> <truoc|sau>
const OUT = process.argv[2] || '.';
const TAG = process.argv[3] || 'sau';
const BASE = process.env.BASE_URL || 'http://localhost:5173';
(async () => {
  const b = await chromium.launch();
  for (const [w, h, size] of [[1440, 900, '1440'], [390, 844, '390']]) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    const shot = async (name) => { await p.waitForTimeout(900); await p.screenshot({ path: `${OUT}/${name}-${size}-${TAG}.png`, fullPage: true }); };
    await p.goto(BASE + '/'); await shot('01-trang-chu');
    await p.goto(BASE + '/dang-nhap'); await shot('02-dang-nhap');
    await p.goto(BASE + '/dang-ky'); await p.waitForTimeout(800); await shot('03-dang-ky');
    await p.getByLabel('Tên hiển thị').fill('Học viên thử');
    await p.getByLabel('Email').fill(`anh-${size}-${TAG}-${Date.now()}@vd.vn`);
    await p.getByLabel('Mật khẩu', { exact: true }).fill('MatKhau123!');
    await p.getByLabel('Nhập lại mật khẩu').fill('MatKhau123!');
    await p.getByRole('button', { name: 'Đăng ký' }).click(); await p.waitForTimeout(2500);
    await shot('04-tong-quan');
    await p.goto(BASE + '/app/hoc'); await shot('05-hoc');
    await p.locator('[data-lesson-id]').first().click(); await p.waitForTimeout(2000); await shot('06-bai-1');
    await p.goto(BASE + '/app/luyen-tap'); await p.waitForTimeout(1200);
    await p.getByLabel('Đáp án').fill('C C C'); await p.getByRole('button', { name: 'Kiểm tra' }).click(); await shot('07-luyen-tap');
    await p.goto(BASE + '/app/tien-do'); await shot('08-tien-do');
    await p.goto(BASE + '/app/composition'); await shot('09-sang-tac');
    await p.goto(BASE + '/app/ho-so'); await shot('10-ho-so');
    await p.close();
  }
  await b.close();
})();

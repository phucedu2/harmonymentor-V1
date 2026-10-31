const { chromium } = require('playwright');
// Luồng Bước 2 trang Luyện tập: đăng ký → Luyện tập → trả lời 1 câu sai, 1 câu đúng → lịch sử cập nhật.
// Cần backend :8000 và frontend :5173. Chạy: node scripts/phuc-music/luong_buoc2_luyentap.cjs <thư mục ảnh>
const OUT = process.argv[2] || '.';
const BASE = process.env.BASE_URL || 'http://localhost:5173';
(async () => {
  const b = await chromium.launch();
  for (const [w, h, t] of [[1440, 900, 'may-tinh'], [390, 844, 'dien-thoai']]) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    const requests = [];
    p.on('request', (r) => { if (r.url().includes('/practice/') || r.url().includes('/engine/grade')) requests.push(r.method() + ' ' + new URL(r.url()).pathname); });
    await p.goto(BASE + '/dang-ky'); await p.waitForTimeout(1200);
    await p.getByLabel('Tên hiển thị').fill('Học viên thử');
    await p.getByLabel('Email').fill(`lt-${t}-${Date.now()}@vd.vn`);
    await p.getByLabel('Mật khẩu', { exact: true }).fill('MatKhau123!');
    await p.getByLabel('Nhập lại mật khẩu').fill('MatKhau123!');
    await p.getByRole('button', { name: 'Đăng ký' }).click(); await p.waitForTimeout(2500);
    await p.getByRole('link', { name: 'Luyện tập', exact: true }).first().click(); await p.waitForTimeout(1800);
    await p.screenshot({ path: `${OUT}/01-luyen-tap-trong-${t}.png`, fullPage: true });
    // Câu hợp âm: gõ sai trước rồi gõ đáp án đúng do máy chủ trả về.
    const input = p.getByLabel('Đáp án');
    await input.fill('C C C'); await p.getByRole('button', { name: 'Kiểm tra' }).click(); await p.waitForTimeout(1500);
    const expected = (await p.locator('.result p b').first().textContent()) || '';
    await input.fill(expected); await p.getByRole('button', { name: 'Kiểm tra' }).click(); await p.waitForTimeout(1500);
    await p.screenshot({ path: `${OUT}/02-luyen-tap-co-lich-su-${t}.png`, fullPage: true });
    console.log(t, 'lịch sử:', (await p.locator('.practice-history').innerText()).replace(/\n/g, ' | '));
    console.log(t, 'request:', [...new Set(requests)].join(', '));
    await p.close();
  }
  await b.close();
})();

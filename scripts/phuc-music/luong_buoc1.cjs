const { chromium } = require('playwright');
// Kịch bản luồng Bước 1: trang chủ → đăng ký → đăng xuất → đăng nhập → khu học → làm 1 câu Bài 1 → xem cả bài → đăng xuất.
// Cần backend :8000 và frontend :5173 đang chạy. Chạy: node scripts/phuc-music/luong_buoc1.cjs <thư mục ảnh>
const OUT = process.argv[2] || '.';
const BASE = process.env.BASE_URL || 'http://localhost:5173';
(async () => {
  const b = await chromium.launch();
  for (const [w, h, t] of [[1440, 900, 'may-tinh'], [390, 844, 'dien-thoai']]) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    const shot = async (n) => p.screenshot({ path: `${OUT}/${n}-${t}.png` });
    const email = `luong-${t}-${Date.now()}@vd.vn`;
    await p.goto(BASE + '/'); await p.waitForTimeout(1500); await shot('01-trang-chu');
    await p.goto(BASE + '/app'); await p.waitForTimeout(1500);
    console.log(t, 'chưa đăng nhập vào /app ->', p.url());
    await p.goto(BASE + '/dang-ky'); await p.waitForTimeout(1200);
    await p.getByLabel('Tên hiển thị').fill('Học viên thử');
    await p.getByLabel('Email').fill(email);
    await p.getByLabel('Mật khẩu', { exact: true }).fill('MatKhau123!');
    await p.getByLabel('Nhập lại mật khẩu').fill('MatKhau123!');
    await shot('02-dang-ky');
    await p.getByRole('button', { name: 'Đăng ký' }).click(); await p.waitForTimeout(2500);
    console.log(t, 'sau đăng ký ->', p.url());
    await p.getByRole('button', { name: 'Đăng xuất' }).first().click(); await p.waitForTimeout(1500);
    console.log(t, 'sau đăng xuất lần 1 ->', p.url());
    await p.goto(BASE + '/dang-nhap'); await p.waitForTimeout(1200);
    await p.getByLabel('Email').fill(email);
    await p.getByLabel('Mật khẩu').fill('MatKhau123!');
    await shot('03-dang-nhap');
    await p.getByRole('button', { name: 'Đăng nhập' }).click(); await p.waitForTimeout(2500);
    console.log(t, 'sau đăng nhập ->', p.url());
    await shot('04-khu-hoc-tong-quan');
    await p.getByRole('link', { name: 'Học', exact: true }).click(); await p.waitForTimeout(1500);
    await shot('05-hoc');
    await p.getByRole('button', { name: /Bắt đầu học|Học ngay|Mở|Bắt đầu/ }).first().click().catch(async () => { await p.getByText('Từ bàn phím đến hợp âm ba nốt').first().click(); });
    await p.waitForTimeout(2500);
    await shot('06-bai-1-tung-buoc');
    await p.locator('summary', { hasText: 'Mục lục bài học' }).click(); await p.waitForTimeout(400);
    await p.locator('.step-index li button').nth(7).click(); await p.waitForTimeout(1200);
    await p.getByRole('button', { name: 'M3', exact: true }).first().click(); await p.waitForTimeout(400);
    const check = p.getByRole('button', { name: /Kiểm tra|Nộp|Trả lời/ }).first();
    if (await check.count()) { await check.click(); }
    await p.waitForTimeout(2000);
    await shot('07-bai-1-tra-loi-dung');
    console.log(t, 'kết quả câu:', (await p.locator('.result').first().textContent().catch(() => 'không thấy'))?.slice(0, 120));
    await p.getByRole('button', { name: 'Xem cả bài' }).click(); await p.waitForTimeout(1500);
    await shot('08-bai-1-xem-ca-bai');
    await p.getByRole('button', { name: 'Từng bước' }).click(); await p.waitForTimeout(500);
    await p.getByRole('button', { name: 'Đăng xuất' }).first().click(); await p.waitForTimeout(1500);
    console.log(t, 'sau đăng xuất ->', p.url());
    await shot('09-dang-xuat-ve-trang-chu');
    await p.close();
  }
  await b.close();
})();

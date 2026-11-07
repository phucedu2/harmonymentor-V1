// phuc-music Bước 4: chạy thử Harmony Lab như người mới, ở 1440px và 390px.
// Cần backend :8000 và frontend :5173. Dùng: node scripts/phuc-music/luong_buoc4_harmony_lab.cjs <thư mục ảnh>
// Mục tiêu A: dựng backing track (vòng mẫu + nhạc nền + phát lặp + lưu).
// Mục tiêu B: xin gợi ý cho ô 4, dùng một hợp âm lạ và đọc phân tích vì sao lạ.
const { chromium } = require('playwright');
const out = process.argv[2] || '.';

(async () => {
  const browser = await chromium.launch();
  for (const [w, h, size] of [[1440, 900, '1440'], [390, 844, '390']]) {
    const p = await browser.newPage({ viewport: { width: w, height: h } });
    const errors = [];
    p.on('pageerror', (e) => errors.push(String(e).slice(0, 200)));
    await p.goto('http://localhost:5173/dang-ky'); await p.waitForTimeout(800);
    await p.getByLabel('Tên hiển thị').fill('Người mới'); await p.getByLabel('Email').fill(`lab-${size}-${Date.now()}@vd.vn`);
    await p.getByLabel('Mật khẩu', { exact: true }).fill('MatKhau123!'); await p.getByLabel('Nhập lại mật khẩu').fill('MatKhau123!');
    await p.keyboard.press('Enter'); await p.waitForTimeout(2000);
    await p.goto('http://localhost:5173/app/composition'); await p.waitForTimeout(2000);
    await p.screenshot({ path: `${out}/01-harmony-lab-${size}.png`, fullPage: true });
    if (size === '390') await p.screenshot({ path: `${out}/01-harmony-lab-390-man-hinh-dau.png` });

    // A: chọn Bossa, phát lặp, tắt trống, lưu.
    await p.getByRole('button', { name: /^Bossa nova/ }).click();
    await p.getByRole('button', { name: /Phát/ }).first().click(); await p.waitForTimeout(1500);
    console.log(size, 'A đang phát:', await p.getByText('▶ đang phát').count() === 1);
    await p.getByRole('button', { name: 'Trống', exact: true }).click();
    console.log(size, 'A trống đã tắt:', await p.getByRole('button', { name: 'Trống', exact: true }).getAttribute('aria-pressed') === 'false');
    await p.getByRole('button', { name: /Dừng/ }).click();
    await p.getByRole('button', { name: /Lưu vòng này/ }).click(); await p.waitForTimeout(800);
    console.log(size, 'A đã lưu:', await p.getByText(/Đã lưu "/).count() === 1);

    // B: gợi ý cho ô 4 bằng bàn phím (Tab tới ô, Enter chọn), dùng ♭VII rồi đọc phân tích.
    const bar4 = p.getByRole('button', { name: /^Ô 4/ });
    await bar4.focus(); await p.keyboard.press('Enter');
    console.log(size, 'B ô 4 chọn bằng bàn phím:', await bar4.getAttribute('aria-pressed') === 'true');
    await p.getByRole('button', { name: /Gợi ý hợp âm thay/ }).click(); await p.waitForTimeout(1000);
    const suggestions = await p.locator('li b.font-mono').allInnerTexts();
    console.log(size, 'B gợi ý:', suggestions.join(' '));
    await p.screenshot({ path: `${out}/02-goi-y-o-4-${size}.png`, fullPage: true });
    await p.getByRole('button', { name: 'Dùng Bb cho ô 4' }).click(); await p.waitForTimeout(900);
    const summary = await p.locator('[aria-live=polite]').last().innerText();
    console.log(size, 'B phân tích:', summary);
    await p.screenshot({ path: `${out}/03-phan-tich-${size}.png`, fullPage: true });
    console.log(size, 'lỗi trang:', errors.length ? errors : 'không có');
    await p.close();
  }
  await browser.close();
})();

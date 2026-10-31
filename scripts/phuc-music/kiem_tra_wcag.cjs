const { chromium } = require('playwright');
const fs = require('fs');
// Kiểm tra WCAG 2.1 A/AA tự động bằng axe-core trên các trang chính, ở 1440px và 390px.
// Cần backend :8000, frontend :5173 và axe-core: AXE_PATH=<đường dẫn axe.min.js> node scripts/phuc-music/kiem_tra_wcag.cjs
const AXE = fs.readFileSync(process.env.AXE_PATH || require.resolve('axe-core/axe.min.js'), 'utf8');
const BASE = process.env.BASE_URL || 'http://localhost:5173';
async function audit(p, name) {
  await p.addScriptTag({ content: AXE });
  const res = await p.evaluate(async () => await window.axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } }));
  const v = res.violations.map((x) => `${x.id}(${x.impact}) x${x.nodes.length}: ${x.nodes.slice(0, 2).map((n) => n.target.join(' ')).join(' | ')}`);
  console.log(`${name}: ${v.length ? 'LỖI ' + v.join('; ') : 'đạt (0 vi phạm)'}`);
  return v.length;
}
(async () => {
  const b = await chromium.launch(); let total = 0;
  for (const [w, h, size] of [[1440, 900, '1440'], [390, 844, '390']]) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    const go = async (path, name) => { await p.goto(BASE + path); await p.waitForTimeout(1200); total += await audit(p, `${size} ${name}`); };
    await go('/', 'trang chủ'); await go('/dang-nhap', 'đăng nhập'); await go('/dang-ky', 'đăng ký');
    await p.getByLabel('Tên hiển thị').fill('Học viên thử');
    await p.getByLabel('Email').fill(`wcag-${size}-${Date.now()}@vd.vn`);
    await p.getByLabel('Mật khẩu', { exact: true }).fill('MatKhau123!');
    await p.getByLabel('Nhập lại mật khẩu').fill('MatKhau123!');
    await p.getByRole('button', { name: 'Đăng ký' }).click(); await p.waitForTimeout(2000);
    total += await audit(p, `${size} tổng quan`);
    await go('/app/hoc', 'học');
    await p.locator('[data-lesson-id="L01"]').click(); await p.waitForTimeout(1500);
    total += await audit(p, `${size} bài 1 mở đầu`);
    for (const n of [1, 6, 7, 9]) {
      await p.getByText('Mục lục bài học').click(); await p.waitForTimeout(300);
      await p.locator('details ol li button').nth(n).click(); await p.waitForTimeout(1500);
      total += await audit(p, `${size} bài 1 bước ${n + 1}`);
    }
    await go('/app/luyen-tap', 'luyện tập');
    await p.getByLabel('Đáp án').fill('C C C'); await p.getByRole('button', { name: 'Kiểm tra' }).click(); await p.waitForTimeout(1200);
    total += await audit(p, `${size} luyện tập sau khi chấm`);
    await go('/app/tien-do', 'tiến độ'); await go('/app/composition', 'sáng tác'); await go('/app/ho-so', 'hồ sơ');
    await p.close();
  }
  // Bàn phím: chỉ dùng Tab/Enter để mở Bài 1 và bấm một phím piano.
  const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
  await p.goto(BASE + '/dang-ky'); await p.waitForTimeout(800);
  await p.getByLabel('Tên hiển thị').fill('Bàn phím'); await p.getByLabel('Email').fill(`kb-${Date.now()}@vd.vn`);
  await p.getByLabel('Mật khẩu', { exact: true }).fill('MatKhau123!'); await p.getByLabel('Nhập lại mật khẩu').fill('MatKhau123!');
  await p.keyboard.press('Enter'); await p.waitForTimeout(2000);
  await p.goto(BASE + '/app/hoc'); await p.waitForTimeout(1200);
  await p.locator('[data-lesson-id="L01"]').focus(); await p.keyboard.press('Enter'); await p.waitForTimeout(1500);
  const opened = await p.getByRole('heading', { level: 1 }).innerText();
  // Sang bước 7 (khám phá quãng, có piano) bằng bàn phím: mở mục lục rồi Enter vào mục thứ 7.
  await p.locator('summary', { hasText: 'Mục lục bài học' }).focus(); await p.keyboard.press('Enter'); await p.waitForTimeout(300);
  await p.locator('details ol li button').nth(6).focus(); await p.keyboard.press('Enter'); await p.waitForTimeout(1500);
  let reached = '';
  for (let i = 0; i < 60 && !reached.startsWith('Phím'); i++) { await p.keyboard.press('Tab'); reached = await p.evaluate(() => document.activeElement?.getAttribute('aria-label') || ''); }
  await p.keyboard.press('Enter');
  const ring = await p.evaluate(() => getComputedStyle(document.activeElement).outlineStyle);
  console.log(`bàn phím: Enter mở "${opened}"; Tab tới "${reached}"; viền focus: ${ring}`);
  await b.close();
  console.log(`TỔNG vi phạm: ${total}`);
  process.exitCode = total ? 1 : 0;
})();

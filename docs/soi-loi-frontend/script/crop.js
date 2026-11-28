// Ảnh chi tiết từng lỗi, chụp cùng thao tác trên bản cũ (4174) và bản mới (4173).
const { chromium } = require('playwright');
const OUT = '/tmp/claude-0/soi/anh-loi';
require('fs').mkdirSync(OUT, { recursive: true });
(async () => {
  const b = await chromium.launch();
  for (const [tag, BASE] of [['truoc', 'http://localhost:4174'], ['sau', 'http://localhost:4173']]) {
    // FE-003: tiêu đề "Bấm một hợp âm, nghe và thấy nó" trên nền ngà
    let ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2, reducedMotion: 'reduce' });
    let p = await ctx.newPage(); await p.goto(BASE + '/', { waitUntil: 'networkidle' });
    await p.locator('#thu-title').scrollIntoViewIfNeeded(); await p.waitForTimeout(600);
    await p.locator('#thu-title').screenshot({ path: `${OUT}/FE-003_${tag}.png` });
    // FE-008 header 390
    await ctx.close();
    // Đăng nhập rồi FE-007 focus thanh bên
    ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
    p = await ctx.newPage(); const email = `k${Date.now()}@vd.vn`;
    await p.request.post(BASE + '/api/v1/auth/register', { data: { email, password: 'matkhau123', display_name: 'K' } });
    await p.goto(BASE + '/dang-nhap'); await p.fill('input[type=email]', email); await p.fill('input[type=password]', 'matkhau123'); await p.locator('form button[type=submit]').click(); await p.waitForURL(/\/app/);
    await p.goto(BASE + '/app', { waitUntil: 'networkidle' });
    await p.locator('aside a[href="/app/hoc"]').focus(); await p.keyboard.press('Tab'); await p.keyboard.press('Shift+Tab');
    await p.waitForTimeout(300);
    await p.screenshot({ path: `${OUT}/FE-007_${tag}.png`, clip: { x: 0, y: 0, width: 260, height: 330 } });
    await ctx.close();
  }
  await b.close();
})();

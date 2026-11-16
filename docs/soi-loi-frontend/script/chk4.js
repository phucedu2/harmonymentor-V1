const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await (await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 })).newPage();
  const BASE = process.argv[2]; const email = `c${Date.now()}@vd.vn`;
  await p.request.post(BASE + '/api/v1/auth/register', { data: { email, password: 'matkhau123', display_name: 'C' } });
  await p.goto(BASE + '/dang-nhap'); await p.fill('input[type=email]', email); await p.fill('input[type=password]', 'matkhau123'); await p.locator('form button[type=submit]').click(); await p.waitForURL(/\/app/);
  await p.goto(BASE + '/app/hoc', { waitUntil: 'networkidle' }); await p.locator('[data-lesson-id]').first().click(); await p.waitForTimeout(1200);
  for (let i = 0; i < 8; i++) { await p.getByRole('button', { name: /Bước tiếp/ }).click(); await p.waitForTimeout(1500); }
  const r = await p.evaluate(() => { const h = [...document.querySelectorAll('main article, main section article')].find(e => e.getBoundingClientRect().height > 50); return { scrollY: scrollY, firstContentTop: h ? Math.round(h.getBoundingClientRect().top) : null }; });
  console.log(BASE, JSON.stringify(r));
  await p.screenshot({ path: process.argv[3], type: 'jpeg', quality: 75 });
  await b.close();
})();

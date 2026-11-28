// Đi luồng thật theo 2 vai, chụp khung nhìn (không full-page) ở từng bước.
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://localhost:4173';
const OUT = process.argv[2]; fs.mkdirSync(OUT, { recursive: true });
const ROLE = process.argv[3] || 'vai1';
const [W, H] = ROLE === 'vai1' ? [390, 844] : [1440, 900];
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 2, hasTouch: W < 800, isMobile: W < 800 });
  const p = await ctx.newPage();
  const log = [];
  p.on('console', m => { if (['error','warning'].includes(m.type())) log.push(m.type() + ': ' + m.text().slice(0, 180)); });
  let k = 0; const shot = async (n) => { await p.waitForTimeout(500); await p.screenshot({ path: `${OUT}/${ROLE}_${String(++k).padStart(2,'0')}_${n}.jpg`, type: 'jpeg', quality: 75 }); };
  await p.goto(BASE + '/', { waitUntil: 'networkidle' }); await p.waitForTimeout(1500); await shot('trang-chu-hero');
  for (const y of [1, 2, 3, 4, 6, 8, 10]) { await p.mouse.wheel(0, H); await p.waitForTimeout(700); }
  await shot('trang-chu-giua');
  await p.goto(BASE + '/dang-ky'); await p.locator('form button[type=submit]').click(); await shot('dang-ky-loi-trong');
  const email = `${ROLE}${Date.now()}@vd.vn`;
  const inputs = p.locator('form input');
  await inputs.nth(0).fill(ROLE === 'vai1' ? 'Minh' : 'Lan'); await inputs.nth(1).fill(email); await inputs.nth(2).fill('matkhau123'); await inputs.nth(3).fill('matkhau123');
  await p.locator('form button[type=submit]').click(); await p.waitForURL(/kiem-tra-dau-vao/, { timeout: 15000 }); await shot('kiem-tra-dau-vao');
  if (ROLE === 'vai2') {
    await p.getByRole('button', { name: /Đã học một ít/ }).click(); await p.waitForTimeout(1200); await shot('kiem-tra-cau-1');
  }
  await p.goto(BASE + '/app'); await p.waitForLoadState('networkidle'); await shot('tong-quan');
  await p.goto(BASE + '/app/hoc'); await p.waitForLoadState('networkidle');
  await p.locator('[data-lesson-id]').first().click(); await p.waitForTimeout(1500); await shot('bai1-buoc1');
  for (let i = 2; i <= 6; i++) { await p.getByRole('button', { name: /Bước tiếp/ }).click(); await p.waitForTimeout(800); await shot('bai1-buoc' + i); }
  // tìm câu kiểm tra nhanh đầu tiên bằng mục lục
  await p.locator('summary', { hasText: 'Mục lục' }).click(); await shot('bai1-muc-luc');
  const item = p.locator('details ol button', { hasText: /Kiểm tra|Câu|kiểm tra/ }).first();
  if (await item.count()) { await item.click(); await p.waitForTimeout(800); await shot('bai1-cau-hoi'); }
  const ans = p.locator('main input[type=text], main input:not([type])').first();
  if (await ans.count()) { await ans.fill('X Y Z'); await ans.press('Enter'); await p.waitForTimeout(1200); await shot('bai1-tra-loi-sai'); }
  else { const opt = p.locator('main [role=radio], main button[aria-pressed]').first(); if (await opt.count()) { await opt.click(); await shot('bai1-chon'); } }
  await p.getByRole('button', { name: /^AI$|AI Tutor|Hỏi AI/ }).first().click().catch(()=>{}); await p.waitForTimeout(800); await shot('ai-drawer');
  const ta = p.locator('textarea, [role=dialog] input').first();
  if (await ta.count()) { await ta.fill('Hợp âm C gồm những nốt nào?'); await ta.press('Enter'); await p.waitForTimeout(3000); await shot('ai-tra-loi'); }
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  await p.goto(BASE + '/app/luyen-tap'); await p.waitForLoadState('networkidle');
  const pi = p.locator('main input').first(); await pi.fill('C E G#'); await p.getByRole('button', { name: 'Kiểm tra' }).click(); await p.waitForTimeout(1000); await shot('luyen-tap-sai');
  await p.goto(BASE + '/app/tien-do'); await p.waitForLoadState('networkidle'); await shot('tien-do');
  await p.goto(BASE + '/app/composition'); await p.waitForLoadState('networkidle'); await shot('composition');
  const t0 = Date.now(); await p.getByRole('button', { name: /Phát/ }).first().click(); await p.waitForTimeout(1500); await shot('composition-dang-phat');
  await p.locator('main').getByRole('button', { name: /^Dm/ }).first().click().catch(()=>{}); await p.waitForTimeout(800); await shot('composition-doi-hop-am');
  await p.goto(BASE + '/app/ho-so'); await shot('ho-so');
  await p.getByRole('button', { name: 'Đăng xuất' }).first().click(); await p.waitForTimeout(1200); await shot('dang-xuat');
  fs.writeFileSync(`${OUT}/${ROLE}_log.txt`, [...new Set(log)].join('\n'));
  await b.close();
})().catch(e => { console.error(e.message); process.exit(1); });

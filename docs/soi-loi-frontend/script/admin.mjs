// FE-025: soi trang Quản trị (axe + ảnh + tràn ngang) ở sáng/tối, desktop/điện thoại. Cần tài khoản admin cục bộ (app.seed_admin).
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import fs from 'fs';
const axeSrc = fs.readFileSync('/tmp/claude-0/tools/node_modules/axe-core/axe.min.js', 'utf8');
const BASE = process.env.BASE || 'http://localhost:4173', OUT = process.argv[2]; fs.mkdirSync(OUT, { recursive: true });
const EMAIL = process.env.ADMIN_EMAIL, PASS = process.env.ADMIN_PASSWORD;
const b = await chromium.launch(); const res = {};
const VIEWS = [
  ['thong-ke', async (p) => {}],
  ['bai-hoc', async (p) => { await p.getByRole('button', { name: 'Bài học', exact: true }).click(); await p.waitForTimeout(800); }],
  ['bai-hoc-sua', async (p) => { await p.getByRole('button', { name: 'Bài học', exact: true }).click(); await p.getByRole('button', { name: 'Sửa nội dung' }).first().click(); await p.waitForTimeout(800); await p.locator('li button[aria-expanded]').first().click(); await p.waitForTimeout(300); }],
  ['ai-soan-bai', async (p) => { await p.getByRole('button', { name: 'AI soạn bài' }).click(); await p.waitForTimeout(800); }],
  ['nguoi-dung', async (p) => { await p.getByRole('button', { name: 'Người dùng' }).click(); await p.waitForTimeout(800); }],
];
for (const [vw, vh, dev] of [[1440, 900, 'desktop'], [375, 812, 'mobile']]) {
  const ctx = await b.newContext({ viewport: { width: vw, height: vh } }); const p = await ctx.newPage();
  await p.goto(BASE + '/dang-nhap'); await p.fill('input[type=email]', EMAIL); await p.fill('input[type=password]', PASS);
  await p.locator('form button[type=submit]').click(); await p.waitForURL(/\/app/); await p.waitForTimeout(1500);
  for (const theme of ['light', 'dark']) for (const [name, act] of VIEWS) {
    await p.goto(BASE + '/admin', { waitUntil: 'networkidle' }); await p.evaluate((t) => { t === 'dark' ? localStorage.setItem('hm-theme', 'dark') : localStorage.removeItem('hm-theme'); }, theme);
    await p.reload({ waitUntil: 'networkidle' }); await p.waitForTimeout(600); await act(p);
    await p.evaluate(axeSrc);
    const r = await p.evaluate(async () => await window.axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice'] } }));
    const overflow = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    const small = await p.evaluate(() => [...document.querySelectorAll('main button, main input, main textarea, main select, main a')].filter(e => { const r = e.getBoundingClientRect(); return r.width && r.height && (r.height < 24 || r.width < 24); }).map(e => (e.getAttribute('aria-label') || e.textContent || e.tagName).trim().slice(0, 30) + ` ${Math.round(e.getBoundingClientRect().width)}x${Math.round(e.getBoundingClientRect().height)}`));
    res[`${dev}_${theme}_${name}`] = { overflow, small, axe: r.violations.map(v => ({ id: v.id, impact: v.impact, n: v.nodes.length, t: v.nodes.slice(0, 3).map(n => n.target.join(' ')), s: v.nodes[0]?.failureSummary?.slice(0, 160) })) };
    await p.screenshot({ path: `${OUT}/${dev}_${theme}_${name}.png`, fullPage: true });
  }
  await ctx.close();
}
fs.writeFileSync(`${OUT}/admin-audit.json`, JSON.stringify(res, null, 1));
for (const [k, v] of Object.entries(res)) console.log(k, 'tràn', v.overflow, 'axe', v.axe.map(a => `${a.id}(${a.n})`).join(',') || 0, 'nhỏ', v.small.length);
await b.close();

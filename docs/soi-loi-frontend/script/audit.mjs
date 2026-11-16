// Lighthouse (desktop + mobile) + axe-core cho các trang chính, cùng một hồ sơ trình duyệt đã đăng nhập.
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import lighthouse from '/tmp/claude-0/tools/node_modules/lighthouse/core/index.js';
import fs from 'fs';
const require = (await import('module')).createRequire(import.meta.url);
const axeSrc = fs.readFileSync('/tmp/claude-0/tools/node_modules/axe-core/axe.min.js', 'utf8');
const BASE = process.env.BASE || 'http://localhost:4173', OUT = process.argv[2]; fs.mkdirSync(OUT, { recursive: true });
const PAGES = [['trang-chu','/'],['dang-nhap','/dang-nhap'],['dang-ky','/dang-ky'],['tong-quan','/app'],['hoc','/app/hoc'],['luyen-tap','/app/luyen-tap'],['quiz','/app/quiz'],['tien-do','/app/tien-do'],['composition','/app/composition'],['ho-so','/app/ho-so'],['kiem-tra-dau-vao','/app/kiem-tra-dau-vao']];
const PORT = Number(process.env.PORT || 9333);
const dir = fs.mkdtempSync('/tmp/claude-0/prof-');
const ctx = await chromium.launchPersistentContext(dir, { args: ['--remote-debugging-port=' + PORT], viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();
const email = `audit${Date.now()}@vd.vn`;
await page.request.post(BASE + '/api/v1/auth/register', { data: { email, password: 'matkhau123', display_name: 'Audit' } });
const login = async () => {
  await page.goto(BASE + '/dang-nhap', { waitUntil: 'networkidle' });
  if (!page.url().includes('/dang-nhap')) return;
  await page.fill('input[type=email]', email); await page.fill('input[type=password]', 'matkhau123');
  await page.locator('form button[type=submit]').click(); await page.waitForURL(/\/app/);
};
const res = {};
for (const [name, url] of PAGES.filter(([n]) => !process.env.ONLY || process.env.ONLY.split(',').includes(n))) {
  res[name] = {};
  if (url.startsWith('/app')) await login();
  for (const scheme of ['light', 'dark']) {
    await page.emulateMedia({ colorScheme: scheme });
    // FE-014: "tối" là theme thật của app (localStorage hm-theme), đặt rồi tải lại trang.
    await page.goto(BASE + url, { waitUntil: 'networkidle' });
    await page.evaluate((s) => { try { if (s === 'dark') localStorage.setItem('hm-theme', 'dark'); else localStorage.removeItem('hm-theme'); } catch {} }, scheme);
    await page.reload({ waitUntil: 'networkidle' }); await page.waitForTimeout(1500);
    await page.evaluate(axeSrc);
    const r = await page.evaluate(async () => await window.axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice'] } }));
    res[name]['axe_' + scheme] = r.violations.map(v => ({ id: v.id, impact: v.impact, n: v.nodes.length, help: v.help, targets: v.nodes.slice(0,4).map(n => n.target.join(' ')), summary: v.nodes[0]?.failureSummary?.slice(0,200) }));
  }
  await page.evaluate(() => { try { localStorage.removeItem('hm-theme'); } catch {} }); // Lighthouse đo bản mặc định (sáng)
  for (const formFactor of ['desktop', 'mobile']) {
    if (url.startsWith('/app')) await login();
    const cfg = formFactor === 'desktop' ? (await import('/tmp/claude-0/tools/node_modules/lighthouse/core/config/desktop-config.js')).default : undefined;
    const r = await lighthouse(BASE + url, { port: PORT, output: 'json', logLevel: 'error', onlyCategories: ['performance','accessibility','best-practices'], disableStorageReset: true, formFactor, screenEmulation: formFactor==='mobile'? undefined : undefined }, cfg);
    const a = r.lhr.audits;
    res[name]['lh_' + formFactor] = { perf: Math.round(r.lhr.categories.performance.score*100), a11y: Math.round(r.lhr.categories.accessibility.score*100), bp: Math.round(r.lhr.categories['best-practices'].score*100), LCP: a['largest-contentful-paint'].numericValue|0, CLS: +a['cumulative-layout-shift'].numericValue.toFixed(3), TBT: a['total-blocking-time'].numericValue|0, FCP: a['first-contentful-paint'].numericValue|0, finalUrl: r.lhr.finalDisplayedUrl };
    console.log(name, formFactor, JSON.stringify(res[name]['lh_' + formFactor]));
  }
}
fs.writeFileSync(OUT + '/audit.json', JSON.stringify(res, null, 1));
await ctx.close();

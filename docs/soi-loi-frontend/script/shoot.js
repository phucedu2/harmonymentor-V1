// Chụp mọi trang × 5 kích thước × sáng/tối, ghi lỗi console + cuộn ngang + vùng chạm nhỏ.
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const BASE = process.env.BASE || 'http://localhost:4173';
const OUT = process.argv[2]; fs.mkdirSync(OUT, { recursive: true });
const SIZES = process.env.SIZES ? process.env.SIZES.split(',').map((s) => s.split('x').map(Number)) : [[1920,1080],[1440,900],[1280,800],[768,1024],[390,844]];
const PAGES = [
  ['trang-chu','/',false],['dang-nhap','/dang-nhap',false],['dang-ky','/dang-ky',false],['404','/khong-co',false],
  ['tong-quan','/app',true],['hoc','/app/hoc',true],['luyen-tap','/app/luyen-tap',true],['quiz','/app/quiz',true],
  ['tien-do','/app/tien-do',true],['composition','/app/composition',true],['ho-so','/app/ho-so',true],['kiem-tra-dau-vao','/app/kiem-tra-dau-vao',true],
];
const only = process.env.ONLY ? process.env.ONLY.split(',') : null;
(async () => {
  const browser = await chromium.launch();
  // EMAIL=… dùng tài khoản có sẵn tiến độ (ảnh slide); bỏ trống thì tạo tài khoản mới (soi lỗi trạng thái rỗng).
  const email = process.env.EMAIL || `soi${Date.now()}@vd.vn`, password = process.env.PASSWORD || 'matkhau123';
  if (!process.env.EMAIL) {
    const reg = await (await browser.newContext()).request.post(BASE + '/api/v1/auth/register', { data: { email, password, display_name: 'Minh (vai 1)' } });
    console.log('register', reg.status());
  }
  const report = [];
  for (const scheme of ['light','dark']) for (const [w,h] of SIZES) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: Number(process.env.DSF||2), colorScheme: scheme, hasTouch: w < 800, isMobile: w < 800 && w < 500 });
    // FE-014: "tối" giờ là theme thật của app (nút sáng/tối lưu localStorage), không chỉ prefers-color-scheme.
    if (scheme === 'dark') await ctx.addInitScript(() => { try { localStorage.setItem('hm-theme', 'dark'); } catch {} });
    const page = await ctx.newPage();
    let logs = [];
    page.on('console', m => { if (['error','warning'].includes(m.type())) logs.push(`${m.type()}: ${m.text().slice(0,200)}`); });
    page.on('pageerror', e => logs.push('pageerror: ' + e.message.slice(0,200)));
    let authed = false;
    for (const [name, url, auth] of PAGES) {
      if (only && !only.includes(name)) continue;
      if (auth && !authed) {
        await page.goto(BASE + '/dang-nhap'); await page.fill('input[type=email]', email); await page.fill('input[type=password]', password);
        await page.locator('form button[type=submit]').click(); await page.waitForURL(/\/app/, { timeout: 15000 }); authed = true;
      }
      logs = [];
      await page.goto(BASE + url, { waitUntil: 'networkidle' }).catch(()=>{});
      await page.waitForTimeout(1200);
      // cuộn hết trang để kích hoạt ScrollTrigger rồi về đầu
      await page.evaluate(async () => { for (let y=0; y<document.body.scrollHeight; y+=600) { window.scrollTo(0,y); await new Promise(r=>setTimeout(r,60)); } window.scrollTo(0,0); });
      await page.waitForTimeout(800);
      const m = await page.evaluate(() => {
        const sw = document.documentElement.scrollWidth, cw = document.documentElement.clientWidth;
        const small = [...document.querySelectorAll('a,button,input,select,[role=button],[role=tab]')].filter(e => { const r = e.getBoundingClientRect(); const s=getComputedStyle(e); return r.width>0 && r.height>0 && s.visibility!=='hidden' && (r.height<44 || r.width<44) && !e.closest('.sr-only'); }).map(e => `${e.tagName.toLowerCase()} "${(e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,30)}" ${Math.round(e.getBoundingClientRect().width)}x${Math.round(e.getBoundingClientRect().height)}`);
        return { hscroll: sw > cw ? sw - cw : 0, small: [...new Set(small)].slice(0,40), bg: getComputedStyle(document.body).backgroundColor };
      });
      const file = `${name}_${w}_${scheme}.jpg`;
      await page.screenshot({ path: path.join(OUT, file), fullPage: true, type: 'jpeg', quality: 72 });
      report.push({ name, w, scheme, ...m, logs: [...new Set(logs)] });
      console.log(file, 'hscroll', m.hscroll, 'small', m.small.length, 'logs', logs.length);
    }
    await ctx.close();
  }
  fs.writeFileSync(path.join(OUT, '_report.json'), JSON.stringify({ email, report }, null, 1));
  await browser.close();
})();

// Chụp 4 mockup của Top 3 thành PNG (gen_page.js tạo mockup.html trước)
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2 });
  await p.goto('file://' + __dirname + '/mockup.html'); await p.waitForTimeout(1500);
  const out = process.argv[2];
  for (const el of await p.$$('[data-shot]')) { const n = await el.getAttribute('data-shot'); await el.screenshot({ path: `${out}/mockup/${n}.png` }); }
  await b.close();
})();

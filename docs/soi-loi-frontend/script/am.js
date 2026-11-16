// Đo thời gian từ bấm Phát tới khi hết "Đang tải nhạc cụ" (mẫu âm sẵn sàng), lần đầu và lần hai; và bấm phím piano trong bài 1.
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const p = await (await b.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const email = `am${Date.now()}@vd.vn`;
  await p.request.post('http://localhost:4173/api/v1/auth/register', { data: { email, password: 'matkhau123', display_name: 'Am' } });
  await p.goto('http://localhost:4173/dang-nhap'); await p.fill('input[type=email]', email); await p.fill('input[type=password]', 'matkhau123');
  await p.locator('form button[type=submit]').click(); await p.waitForURL(/\/app/);
  await p.goto('http://localhost:4173/app/composition', { waitUntil: 'networkidle' });
  // FE-012: WAIT=ms giả lập người dùng đọc trang trước khi bấm Phát (tải trước chạy lúc rảnh).
  if (process.env.WAIT) { await p.waitForTimeout(Number(process.env.WAIT));
    console.log('file mẫu đã tải trước khi bấm:', await p.evaluate(() => performance.getEntriesByType('resource').filter(r => /\/samples\/.+\.(mp3|ogg|wav|m4a)/.test(r.name)).length)); }
  for (const run of [1, 2]) {
    const t0 = Date.now(); await p.getByRole('button', { name: /^▶ Phát$|Phát$/ }).first().click();
    try { await p.waitForSelector('text=Đang tải nhạc cụ', { timeout: 1500 }); await p.waitForSelector('text=Đang tải nhạc cụ', { state: 'detached', timeout: 60000 }); } catch {}
    console.log('composition lần', run, 'tới khi sẵn sàng (ms):', Date.now() - t0);
    await p.waitForTimeout(1500); await p.getByRole('button', { name: /Dừng/ }).first().click(); await p.waitForTimeout(500);
  }
  const bytes = await p.evaluate(() => performance.getEntriesByType('resource').filter(r => /\.(mp3|ogg|wav|m4a)/.test(r.name)).reduce((s, r) => s + (r.transferSize || r.encodedBodySize || 0), 0));
  const n = await p.evaluate(() => performance.getEntriesByType('resource').filter(r => /\.(mp3|ogg|wav|m4a)/.test(r.name)).length);
  console.log('mẫu âm tải:', n, 'file,', Math.round(bytes / 1024), 'KB');
  await b.close();
})();

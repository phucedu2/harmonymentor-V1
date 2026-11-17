// Xuất PNG + icon app + favicon.ico cho một bản màu (san-khau | giay-nhac) từ logo/<bản>/*.svg.
// Dùng Chromium của Playwright vì máy dựng không có cairosvg. Chạy từ gốc repo, sau san_khau.py:
//   node docs/thuong-hieu/_nguon/xuat_png_ban_mau.mjs giay-nhac
// Cần Playwright (đã có ở frontend/node_modules) và Pillow (python3) để gói favicon.ico.
import { createRequire } from 'module';
import fs from 'fs'; import path from 'path'; import { execFileSync } from 'child_process';
const require = createRequire(path.resolve('frontend/package.json'));
const { chromium } = require('@playwright/test');
const brand = process.argv[2]; if (!brand) throw new Error('thiếu tên bản màu');
const dir = `docs/thuong-hieu/logo/${brand}`, out = `${dir}/png`, pub = 'frontend/public';
fs.mkdirSync(out, { recursive: true });
const jobs = [];
for (const f of fs.readdirSync(dir).filter((f) => f.endsWith('.svg') && !f.startsWith('chuyen-dong'))) {
  const w = f.startsWith('ngang') || f.startsWith('wordmark') ? 2400 : 1024;
  jobs.push([path.join(dir, f), path.join(out, f.replace('.svg', '.png')), w]);
}
for (const [n, w] of [['icon-512', 512], ['icon-192', 192], ['apple-touch-icon', 180]]) jobs.push([path.join(dir, 'app-icon.svg'), path.join(pub, `${n}-${brand}.png`), w]);
const ico = [48, 32, 16].map((s) => [`${pub}/favicon-${brand}.svg`, `/tmp/fav-${brand}-${s}.png`, s]);
const b = await chromium.launch(); const p = await b.newPage();
for (const [src, dst, w] of [...jobs, ...ico]) {
  const svg = fs.readFileSync(src, 'utf8');
  const vb = svg.match(/viewBox="([^"]+)"/)[1].split(/\s+/).map(Number);
  const h = Math.round(w * vb[3] / vb[2]);
  await p.setViewportSize({ width: w, height: h });
  await p.setContent(`<style>html,body{margin:0;background:transparent}svg{display:block;width:${w}px;height:${h}px}</style>${svg}`);
  await p.screenshot({ path: dst, omitBackground: true });
}
await b.close();
execFileSync('python3', ['-c', `from PIL import Image
ims=[Image.open('/tmp/fav-${brand}-%d.png'%s).convert('RGBA') for s in (48,32,16)]
ims[0].save('${pub}/favicon-${brand}.ico', sizes=[(48,48),(32,32),(16,16)], append_images=ims[1:])`]);
console.log('xong', brand, jobs.length, 'png +', 'favicon.ico');

// Dựng toàn bộ bộ logo "Harmony Mentor" vào thư mục OUT.
// Chạy: FONT_DIR=./fonts OUT=../ node build.js   (xem README trong _nguon/)
const fs = require('fs');
const path = require('path');
const { S } = require('./symbols');
const { palette } = require('./palette');
const { svgDoc, lockupH, lockupV, wordmark, appIcon, faviconSvg, REDUCE } = require('./compose');
const { LOGOS, KIT } = require('./meta');

const OUT = process.env.OUT || path.join(__dirname, '..');
const w = (rel, s) => { const p = path.join(OUT, rel); fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(p, s); };
const BG = { light: '#F2F3EA', dark: '#081613', mono: '#FFFFFF', 'mono-inv': '#0C231F' };
const VI = { light: 'sang', dark: 'toi', mono: 'den', 'mono-inv': 'trang' };

const finals = Object.keys(LOGOS).filter((k) => LOGOS[k].kind !== 'cut');
const top3 = KIT;
const data = { logos: {}, sketches: {} };

// Phác thảo: cả 26 bản, bản sáng + bản 1 màu
for (const id of Object.keys(S)) {
  const m = LOGOS[id];
  const sk = {};
  for (const mode of ['light', 'mono']) {
    const c = palette(mode, { notes: m.notes });
    sk[mode] = svgDoc([0, 0, 100, 100], S[id](c), { title: `Phác thảo ${m.name}` });
    if (mode === 'light') w(`svg/phac-thao/${id}.svg`, svgDoc([0, 0, 100, 100], S[id](palette('light', { notes: m.notes })), { title: `Phác thảo ${m.name}`, bg: BG.light }));
  }
  data.sketches[id] = sk;
}

for (const id of finals) {
  const m = LOGOS[id];
  const d = { sym: {}, h: {}, v: {}, wm: {} };
  for (const mode of ['light', 'dark', 'mono', 'mono-inv']) {
    const mk = () => palette(mode, { notes: m.notes });
    const bg = mode.startsWith('mono') ? BG[mode] : null;
    const sym = svgDoc([0, 0, 100, 100], S[id](mk()), { bg, title: 'Harmony Mentor' });
    const H = lockupH(id, mk()), V = lockupV(id, mk()), WM = wordmark(id, mk());
    const hs = svgDoc(H.vb, H.inner, { bg }), vs = svgDoc(V.vb, V.inner, { bg }), ws = svgDoc(WM.vb, WM.inner, { bg });
    w(`svg/${id}/bieu-tuong-${VI[mode]}.svg`, sym);
    w(`svg/${id}/ngang-${VI[mode]}.svg`, hs);
    if (mode === 'light' || mode === 'dark') w(`svg/${id}/wordmark-${VI[mode]}.svg`, ws);
    if (top3.includes(id)) w(`svg/${id}/doc-${VI[mode]}.svg`, vs);
    d.sym[mode] = sym; d.h[mode] = hs; d.v[mode] = vs; d.wm[mode] = ws;
  }
  // Chuyển động ≤ 3 giây, chạy một lần khi tải; tắt khi người dùng bật "giảm chuyển động"
  const anim = (S[id].anim || '') + REDUCE;
  const A = lockupH(id, palette('light', { notes: m.notes }));
  w(`svg/${id}/chuyen-dong.svg`, svgDoc(A.vb, A.inner, { cls: 'play', style: anim, bg: BG.light }));
  w(`svg/${id}/chuyen-dong-bieu-tuong.svg`, svgDoc([0, 0, 100, 100], S[id](palette('light', { notes: m.notes })), { cls: 'play', style: anim }));
  d.anim = { css: S[id].anim || '', light: svgDoc([0, 0, 100, 100], S[id](palette('light', { notes: m.notes }))), dark: svgDoc([0, 0, 100, 100], S[id](palette('dark', { notes: m.notes }))) };
  const ic = appIcon(id, m);
  d.icon = svgDoc(ic.vb, ic.inner);
  w(`svg/${id}/app-icon.svg`, d.icon);
  d.favicon = faviconSvg(id, m);
  w(`svg/${id}/favicon.svg`, d.favicon);
  data.logos[id] = d;
}

fs.writeFileSync(path.join(__dirname, 'data.json'), JSON.stringify(data));
console.log('svg xong:', finals.length, 'logo,', Object.keys(S).length, 'phác thảo');

// Ghép biểu tượng + wordmark thành logo ngang/dọc, icon ứng dụng, favicon.
const { S } = require('./symbols');
const { W, CAP } = require('./wordmarks');
const { palette } = require('./palette');
const f = (n) => +n.toFixed(2);
const NS = 'xmlns="http://www.w3.org/2000/svg"';
const REDUCE = '@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}';

function svgDoc(vb, inner, { title, bg, cls = '', style = '', w, h } = {}) {
  const [x, y, ww, hh] = vb;
  const bgr = bg ? `<rect x="${f(x)}" y="${f(y)}" width="${f(ww)}" height="${f(hh)}" fill="${bg}"/>` : '';
  const st = style ? `<style>${style}</style>` : '';
  const size = w ? ` width="${w}" height="${h ?? f((w * hh) / ww)}"` : '';
  return `<svg ${NS} viewBox="${vb.map(f).join(' ')}"${size}${cls ? ` class="${cls}"` : ''} role="img" aria-label="${title || 'Harmony Mentor'}"><title>${title || 'Harmony Mentor'}</title>${st}${bgr}${inner}</svg>`;
}

const symbol = (id, c) => S[id](c);
const notesFor = (meta) => !!meta.notes;

function lockupH(id, c, pad = 6) {
  const wm = W[id](c), gap = 24, base = 50 + CAP / 2;
  const tx = 100 + gap - wm.bb.x;
  const inner = `<g class="sym">${symbol(id, c)}</g><g transform="translate(${f(tx)} ${f(base)})">${wm.svg}</g>`;
  const top = Math.min(0, base + wm.bb.y), bot = Math.max(100, base + wm.bb.y + wm.bb.h);
  return { inner, vb: [-pad, top - pad, 100 + gap + wm.bb.w + 2 * pad, bot - top + 2 * pad] };
}
function lockupV(id, c, pad = 6) {
  const wm = W[id](c), gap = 26;
  const base = 100 + gap - wm.bb.y;
  const width = Math.max(100, wm.bb.w);
  const sx = (width - 100) / 2, tx = (width - wm.bb.w) / 2 - wm.bb.x;
  const inner = `<g transform="translate(${f(sx)} 0)" class="sym">${symbol(id, c)}</g><g transform="translate(${f(tx)} ${f(base)})">${wm.svg}</g>`;
  return { inner, vb: [-pad, -pad, width + 2 * pad, base + wm.bb.y + wm.bb.h + 2 * pad] };
}
function wordmark(id, c, pad = 4) {
  const wm = W[id](c);
  return { inner: wm.svg, vb: [wm.bb.x - pad, wm.bb.y - pad, wm.bb.w + 2 * pad, wm.bb.h + 2 * pad] };
}
// Icon ứng dụng: nền sơn mài bo góc, biểu tượng bản tối. Logo vốn là ô (lỗ đục, cuộn) thì đặt thẳng.
function appIcon(id, meta) {
  if (meta.fullTile) {
    // Logo vốn là một ô sơn mài: cho ô đó phủ kín icon để favicon 16px không phí chỗ cho viền
    const c = palette('light', { notes: meta.notes });
    return { inner: `<clipPath id="${c.uid}-ic"><rect width="100" height="100" rx="22"/></clipPath><g clip-path="url(#${c.uid}-ic)"><rect width="100" height="100" fill="${c.lacquer}"/><g transform="translate(-5.56 -5.56) scale(1.1111)">${symbol(id, c)}</g></g>`, vb: [0, 0, 100, 100] };
  }
  if (meta.tile) {
    const c = palette('light', { notes: meta.notes });
    return { inner: `<rect width="100" height="100" rx="22" fill="#F2F3EA"/><g transform="translate(3 3) scale(.94)">${symbol(id, c)}</g>`, vb: [0, 0, 100, 100] };
  }
  const c = palette('dark', { notes: meta.notes });
  return { inner: `<rect width="100" height="100" rx="22" fill="#0C231F"/><g transform="translate(13 13) scale(.74)">${symbol(id, c)}</g>`, vb: [0, 0, 100, 100] };
}
// Favicon SVG tự đổi màu theo chế độ sáng/tối của trình duyệt (biến CSS bên trong file)
function faviconSvg(id, meta) {
  const keys = ['ink', 'deep', 'sig', 'brass', 'brassText', 'felt', 'tint', 'hole', 'soft', 'knock', 'lacquer', 'edge', 'text'];
  const L = palette('light'), D = palette('dark');
  const c = palette('light', { notes: meta.notes });
  for (const k of keys) c[k] = `var(--${k})`;
  const vars = (p) => keys.map((k) => `--${k}:${p[k]}`).join(';');
  const style = `svg{${vars(L)}}@media (prefers-color-scheme:dark){svg{${vars(D)}}}`;
  return svgDoc([0, 0, 100, 100], symbol(id, c), { style, title: 'Harmony Mentor' });
}

module.exports = { svgDoc, lockupH, lockupV, wordmark, appIcon, faviconSvg, symbol, REDUCE };

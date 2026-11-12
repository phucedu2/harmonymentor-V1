// Dàn chữ thành path bằng opentype.js (có kerning), để logo không phụ thuộc font cài trên máy.
const opentype = require('opentype.js');
const path = require('path');
const FONT_DIR = process.env.FONT_DIR || path.join(__dirname, 'fonts');
const cache = {};
const font = (name) => (cache[name] ||= opentype.loadSync(path.join(FONT_DIR, name)));
const f2 = (n) => +n.toFixed(2);

// Một ký tự, x là tâm theo chiều ngang, y là đường chân chữ.
function glyphPath(fontName, ch, x, y, size, fill) {
  const fo = font(fontName), g = fo.charToGlyph(ch);
  const adv = (g.advanceWidth / fo.unitsPerEm) * size;
  return `<path d="${g.getPath(x - adv / 2, y, size).toPathData(2)}" fill="${fill}"/>`;
}

// Dàn một chuỗi; styleFn(i, ch) trả kiểu riêng từng chữ (font, size, dy, fill, custom).
// i đếm chữ cái, bỏ qua dấu cách. Trả về các phần tử SVG và hộp bao.
function layout(text, styleFn) {
  let x = 0, i = 0, prev = null;
  const items = [];
  let minY = Infinity, maxY = -Infinity, minX = Infinity, maxX = -Infinity;
  const grow = (bb) => { minX = Math.min(minX, bb.x1); maxX = Math.max(maxX, bb.x2); minY = Math.min(minY, bb.y1); maxY = Math.max(maxY, bb.y2); };
  const marks = { spaces: [], letters: [] };
  for (const ch of text) {
    if (ch === ' ') {
      const s = styleFn(-1, ' ');
      const fo = font(s.font);
      const w = (fo.charToGlyph(' ').advanceWidth / fo.unitsPerEm) * s.size + (s.space || 0);
      marks.spaces.push({ x0: x, x1: x + w });
      x += w; prev = null; continue;
    }
    const s = styleFn(i, ch);
    const fo = font(s.font);
    const g = fo.charToGlyph(ch);
    if (prev && prev.font === s.font && !s.custom && !prev.custom) x += (fo.getKerningValue(prev.g, g) / fo.unitsPerEm) * s.size;
    const adv = (g.advanceWidth / fo.unitsPerEm) * s.size;
    const dy = s.dy || 0;
    if (s.custom) {
      const r = s.custom(x, dy, s.size, adv);
      items.push(r.svg); grow(r.bb);
      marks.letters.push({ i, ch, x, adv: r.adv ?? adv, size: s.size, dy });
      x += (r.adv ?? adv) + (s.tracking || 0);
    } else {
      const p = g.getPath(x, dy, s.size);
      const bb = p.getBoundingBox();
      items.push(`<path d="${p.toPathData(2)}" fill="${s.fill}"/>`);
      grow(bb);
      marks.letters.push({ i, ch, x, adv, size: s.size, dy, bb });
      x += adv + (s.tracking || 0);
    }
    prev = { font: s.font, g, custom: s.custom };
    i++;
  }
  return { svg: items.join(''), bb: { x: minX, y: minY, w: maxX - minX, h: maxY - minY }, advance: x, marks };
}

module.exports = { layout, glyphPath, font, f2 };

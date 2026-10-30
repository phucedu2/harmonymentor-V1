// Wordmark "Harmony Mentor" cho từng logo. Mọi chữ thành path, chỉ dùng 3 font gốc.
// Chỉ số i đếm chữ cái bỏ qua dấu cách: H0 a1 r2 m3 o4 n5 y6 M7 e8 n9 t10 o11 r12.
const { layout, glyphPath, font } = require('./type');
const { IS_BLACK } = require('./symbols');
const TEXT = 'Harmony Mentor';
const CAP = 30; // chiều cao chữ hoa chuẩn khi biểu tượng cao 100
const FR = (w, it = false) => `Fraunces${it ? '-Italic' : ''}-${w}.ttf`;
const SZ = { fr: CAP / 0.7, bvp: CAP / 0.74, plex: CAP / 0.698 };
const f = (n) => +n.toFixed(2);

const W = {};

// 1 Hai–Ba: độ đậm 13 chữ đi theo 13 phím liên tiếp C→C' (phím đen = đậm, phím trắng = mảnh)
W['hai-ba'] = (c) => layout(TEXT, (i) => ({ font: FR(IS_BLACK(i) ? 900 : 300), size: SZ.fr, fill: c.text }));

// 2 Đô giữa: chữ "o" đầu tiên màu đồng thau = chấm Đô giữa trong biểu tượng
W['do-giua'] = (c) => layout(TEXT, (i) => ({ font: 'BeVietnamPro-SemiBold.ttf', size: SZ.bvp, fill: i === 4 ? c.brassText : c.text }));

// 3 Quãng tám: chữ đứng trên một "sợi dây"; chấm đồng thau đặt đúng giữa dây,
// chỗ chạm nhẹ vào dây sẽ cho âm bồi quãng tám (harmonic) — gốc của chữ "Harmony".
W['quang-tam'] = (c) => {
  const r = layout(TEXT, () => ({ font: FR(600), size: SZ.fr, fill: c.text }));
  const y = SZ.fr * 0.36, x0 = r.bb.x, x1 = r.bb.x + r.bb.w;
  const extra = `<rect x="${f(x0)}" y="${f(y)}" width="${f(x1 - x0)}" height="${f(SZ.fr * 0.035)}" fill="${c.deep}"/>`
    + `<circle cx="${f((x0 + x1) / 2)}" cy="${f(y + SZ.fr * 0.0175)}" r="${f(SZ.fr * 0.085)}" fill="${c.brass}"/>`;
  return { ...r, svg: r.svg + extra, bb: { ...r.bb, h: y + SZ.fr * 0.11 - r.bb.y } };
};

// 4 m 4:3: chữ m trong "Harmony" được vẽ lại, hai vòm rộng 4 và 3 nửa cung (hợp âm trưởng)
W['m-43'] = (c) => layout(TEXT, (i) => ({
  font: 'BeVietnamPro-Medium.ttf', size: SZ.bvp, fill: c.text,
  custom: i === 3 ? (x, dy, size, adv) => {
    const sw = size * 0.105, xh = size * 0.54, ry = xh * 0.3;
    const a = x + size * 0.066 + sw / 2, span = size * (0.828 - 0.066) - sw;
    const xs = [a, a + (span * 4) / 7, a + span], ya = -xh + sw / 2 + ry;
    const d = `M${f(xs[0])} 0V${f(ya)}A${f((xs[1] - xs[0]) / 2)} ${f(ry)} 0 0 1 ${f(xs[1])} ${f(ya)}V0M${f(xs[1])} ${f(ya)}A${f((xs[2] - xs[1]) / 2)} ${f(ry)} 0 0 1 ${f(xs[2])} ${f(ya)}V0`;
    return { svg: `<path d="${d}" fill="none" stroke="${c.deep}" stroke-width="${f(sw)}"/>`, bb: { x1: x, x2: x + adv, y1: -xh, y2: 0 } };
  } : null,
}));

// 5 Hai búa: hai chữ là hai búa, dấu cách là sợi dây đồng chúng cùng gõ vào
W['hai-bua'] = (c) => {
  const r = layout(TEXT, () => ({ font: FR(700), size: SZ.fr, fill: c.text, space: SZ.fr * 0.12 }));
  const sp = r.marks.spaces[0], x = (sp.x0 + sp.x1) / 2;
  return { ...r, svg: r.svg + `<rect x="${f(x - SZ.fr * 0.022)}" y="${f(-CAP - SZ.fr * 0.14)}" width="${f(SZ.fr * 0.044)}" height="${f(CAP + SZ.fr * 0.36)}" fill="${c.brass}"/>`,
    bb: { ...r.bb, y: Math.min(r.bb.y, -CAP - SZ.fr * 0.14), h: r.bb.h + SZ.fr * 0.14 } };
};

// 6 Cần bẩy: "Harmony" hạ xuống, "Mentor" nâng lên, điểm tựa đồng thau nằm ở dấu cách
W['can-bay'] = (c) => {
  const k = SZ.bvp * 0.05;
  const r = layout(TEXT, (i) => ({ font: 'BeVietnamPro-Bold.ttf', size: SZ.bvp, fill: c.text, dy: i < 0 ? 0 : i < 7 ? k : -k, space: SZ.bvp * 0.1 }));
  const sp = r.marks.spaces[0], x = (sp.x0 + sp.x1) / 2, t = SZ.bvp * 0.2;
  return { ...r, svg: r.svg + `<path d="M${f(x)} ${f(-t * 0.2)}L${f(x - t * 0.6)} ${f(t * 0.85)}H${f(x + t * 0.6)}Z" fill="${c.brass}"/>` };
};

// 7 Bàn tay: số ngón tay 1-3-5 nhỏ phía trên chữ, như thầy ghi số ngón lên bản nhạc
W['ban-tay'] = (c) => {
  const r = layout(TEXT, () => ({ font: FR(600), size: SZ.fr, fill: c.text }));
  const marks = { 0: '1', 3: '3', 6: '5', 7: '1', 9: '3', 12: '5' };
  let extra = '';
  const ny = -CAP - SZ.fr * 0.12;
  for (const L of r.marks.letters) if (marks[L.i]) extra += glyphPath('IBMPlexMono-SemiBold.ttf', marks[L.i], L.x + L.adv / 2, ny, SZ.fr * 0.3, c.brassText);
  return { ...r, svg: r.svg + extra, bb: { ...r.bb, y: ny - SZ.fr * 0.22, h: r.bb.h + (r.bb.y - (ny - SZ.fr * 0.22)) } };
};

// 8 Lỗ đục: chữ máy (Plex Mono) như cột lỗ trên cuộn giấy; hai chữ "o" thành lỗ đục dọc
W['lo-duc'] = (c) => layout(TEXT, (i) => ({
  font: 'IBMPlexMono-SemiBold.ttf', size: SZ.plex, fill: c.text,
  custom: i === 4 || i === 11 ? (x, dy, size, adv) => {
    const sw = size * 0.095, xh = size * 0.528, w = adv * 0.6;
    const cx = x + adv / 2;
    return { svg: `<rect x="${f(cx - w / 2 + sw / 2)}" y="${f(-xh + sw / 2)}" width="${f(w - sw)}" height="${f(xh - sw)}" rx="${f((w - sw) / 2)}" fill="none" stroke="${c.text}" stroke-width="${f(sw)}"/>`,
      bb: { x1: x, x2: x + adv, y1: -xh, y2: 0 } };
  } : null,
}));

// 9 Đường cong: mỗi chữ nhỏ hơn chữ trước 2^(-1/12) (một nửa cung). 13 chữ = 12 bước = đúng một quãng tám:
// chữ "r" cuối cao bằng đúng một nửa chữ "H" đầu, giống dây đàn ngắn dần.
W['duong-cong'] = (c) => layout(TEXT, (i) => ({ font: FR(700), size: SZ.fr * 1.25 * Math.pow(2, -Math.max(i, 0) / 12), fill: c.text, tracking: -0.5 }));

// 10 Cuộn tiến trình: chữ máy, dấu cách thay bằng ba lỗ đục của một hợp âm
W['cuon-tien-trinh'] = (c) => {
  const r = layout(TEXT, () => ({ font: 'IBMPlexMono-Medium.ttf', size: SZ.plex, fill: c.text, space: SZ.plex * 0.12 }));
  const sp = r.marks.spaces[0], x = (sp.x0 + sp.x1) / 2, w = SZ.plex * 0.075;
  const h = [CAP * 0.62, CAP * 0.62, CAP * 0.62], dx = [-w * 1.6, 0, w * 1.6], col = c.note ? [c.note(0), c.note(4), c.note(7)] : [c.brass, c.brass, c.brass];
  const extra = dx.map((d, k) => `<rect x="${f(x + d - w / 2)}" y="${f(-CAP * 0.62 - (k === 1 ? CAP * 0.2 : 0))}" width="${f(w)}" height="${f(h[k])}" rx="${f(w / 2)}" fill="${col[k]}"/>`).join('');
  return { ...r, svg: r.svg + extra };
};

// 11 Op-art: chữ đậm bị "cắt" bởi các khe theo nhịp 2–3 phím đen
W['op-art'] = (c) => {
  const r = layout(TEXT, () => ({ font: FR(900), size: SZ.fr, fill: c.text }));
  const unit = SZ.fr * 0.5, gw = SZ.fr * 0.055;
  let gaps = '';
  for (let o = 0; o * 7 * unit < r.advance + unit; o++) for (const u of [0.9, 2.1, 3.85, 5.0, 6.15]) {
    const x = r.bb.x + (u + o * 7) * unit - unit * 0.4;
    gaps += `<rect x="${f(x)}" y="${f(r.bb.y - 2)}" width="${f(gw)}" height="${f(r.bb.h + 4)}" fill="#000"/>`;
  }
  const id = `${c.uid}-op`;
  return { ...r, svg: `<mask id="${id}" maskUnits="userSpaceOnUse" x="${f(r.bb.x - 5)}" y="${f(r.bb.y - 5)}" width="${f(r.bb.w + 10)}" height="${f(r.bb.h + 10)}"><rect x="${f(r.bb.x - 5)}" y="${f(r.bb.y - 5)}" width="${f(r.bb.w + 10)}" height="${f(r.bb.h + 10)}" fill="#fff"/>${gaps}</mask><g mask="url(#${id})">${r.svg}</g>` };
};

// 12 Kandinsky: "Harmony" mảnh như dây, "Mentor" đậm như búa
W['kandinsky'] = (c) => layout(TEXT, (i) => ({ font: i >= 0 && i < 7 ? 'BeVietnamPro-Light.ttf' : 'BeVietnamPro-ExtraBold.ttf', size: SZ.bvp, fill: c.text }));

module.exports = { W, CAP, SZ, TEXT };

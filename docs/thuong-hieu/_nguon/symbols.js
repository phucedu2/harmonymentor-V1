// Các biểu tượng (symbol) vẽ trong khung 100×100.
// Mỗi hàm nhận bảng màu c và trả về chuỗi phần tử SVG.
// Toạ độ tính bằng công thức (vị trí phím đen thật, tỉ lệ dây 2^(-n/12)…) để hình học đúng nhạc lý.
const { glyphPath } = require('./type');

const f = (n) => +n.toFixed(2);
const rect = (x, y, w, h, fill, extra = '') => `<rect x="${f(x)}" y="${f(y)}" width="${f(w)}" height="${f(h)}" fill="${fill}" ${extra}/>`;
const circ = (cx, cy, r, fill, extra = '') => `<circle cx="${f(cx)}" cy="${f(cy)}" r="${f(r)}" fill="${fill}" ${extra}/>`;
const pathEl = (d, attrs) => `<path d="${d}" ${attrs}/>`;

// Tâm phím đen trong 1 quãng tám, đơn vị = bề rộng phím trắng (C# D# | F# G# A#).
// Nhóm 2 lệch nhẹ ra hai bên, nhóm 3 phím giữa nằm chính giữa G–A, giống đàn thật.
const BLACK = [0.9, 2.1, 3.85, 5.0, 6.15];
const IS_BLACK = (s) => [1, 3, 6, 8, 10].includes(((s % 12) + 12) % 12);

const S = {};

// ───── LÃNH THỔ A · Mã nhóm 2–3 phím đen ─────

// A1 Hai–Ba: 5 phím đen của một quãng tám. Nhóm 2 thành H, nhóm 3 thành m.
S['hai-ba'] = (c) => {
  const s = 14.75, w = 0.58 * s, off = 50 - ((BLACK[0] + BLACK[4]) / 2) * s, top = 20, bot = 80;
  const x = BLACK.map((u) => u * s + off);
  const r = (x[3] - x[2]) / 2, ya = top + w / 2 + r;
  const m = `M${f(x[2])} ${bot}V${f(ya)}A${f(r)} ${f(r)} 0 0 1 ${f(x[3])} ${f(ya)}V${bot}M${f(x[3])} ${f(ya)}A${f(r)} ${f(r)} 0 0 1 ${f(x[4])} ${f(ya)}V${bot}`;
  return [
    `<g class="k k1">${rect(x[0] - w / 2, top, w, bot - top, c.ink)}</g>`,
    `<g class="k k2">${rect(x[1] - w / 2, top, w, bot - top, c.ink)}</g>`,
    `<g class="bar">${rect(x[0] + w / 2 - 0.3, 43.5, x[1] - x[0] - w + 0.6, 13, c.brass)}</g>`,
    `<g class="k k3">${pathEl(m, `fill="none" stroke="${c.ink}" stroke-width="${w}"`)}</g>`,
  ].join('');
};
S['hai-ba'].anim = `
.play .k{animation:hm-dip .34s ease-in-out both}
.play .k1{animation-delay:.1s}.play .k2{animation-delay:.32s}.play .k3{animation-delay:.6s}
.play .bar{transform-box:fill-box;transform-origin:left center;animation:hm-grow .6s 1.05s cubic-bezier(.2,.8,.2,1) both}
@keyframes hm-dip{0%,100%{transform:translateY(0)}45%{transform:translateY(4px)}}
@keyframes hm-grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}`;

// A2 Mã vạch quãng tám (bị loại: dễ thành dải phím clip-art)
S['ma-vach'] = (c) => {
  let out = '', x = 12;
  for (let s = 0; s < 13; s++) {
    const b = IS_BLACK(s), w = b ? 7 : 2.2;
    out += rect(x, 18, w, 58, b ? c.ink : c.deep);
    x += w + 3.1;
  }
  return out + rect(12, 82, 2.2, 8, c.brass) + rect(x - 5.3, 82, 2.2, 8, c.brass);
};

// A3 Op-art: nhóm 2–3 lặp hai quãng tám, nén giãn theo hàng tạo khối cầu (Bridget Riley)
S['op-art'] = (c) => {
  let out = '';
  const rows = 10, a = 0.62;
  for (let r = 0; r < rows; r++) {
    const k = 1 - Math.pow((r - (rows - 1) / 2) / (rows / 2), 2);
    const y = 6 + r * 9.1, h = 7.4;
    const W = (t) => t - (a * k * Math.sin(2 * Math.PI * t)) / (2 * Math.PI);
    const D = (t) => 1 - a * k * Math.cos(2 * Math.PI * t);
    let row = '';
    for (let o = 0; o < 2; o++) for (const u of BLACK) {
      const cx = 5 + 90 * W((u + o * 7 + 0.43) / 14.86);
      const bw = 3.3 * D((u + o * 7 + 0.43) / 14.86);
      row += rect(cx - bw / 2, y, bw, h, r === 5 ? c.deep : c.ink);
    }
    out += `<g class="row" style="animation-delay:${(r * 0.12).toFixed(2)}s">${row}</g>`;
  }
  return out;
};
S['op-art'].anim = `
.play .row{animation:hm-fade .5s ease-out both}
@keyframes hm-fade{from{opacity:0;transform:translateX(-3px)}to{opacity:1;transform:none}}`;

// A4 Đô giữa: nhóm 2 phím đen + chấm đồng thau đúng phím C bên trái
S['do-giua'] = (c) => {
  const s = 26, off = 11, bw = 15, top = 12, bot = 90;
  const keys = [0, 1, 2].map((k) => rect(off + k * s, top, s, bot - top, c.knock, `rx="0" stroke="${c.deep}" stroke-width="3"`)).join('');
  return [
    `<clipPath id="${c.uid}-k"><rect x="${off}" y="${top}" width="${3 * s}" height="${bot - top}" rx="5"/></clipPath>`,
    `<g clip-path="url(#${c.uid}-k)">${keys}`,
    rect(off + 0.92 * s - bw / 2, top - 2, bw, 50, c.ink, 'rx="2"'),
    rect(off + 2.08 * s - bw / 2, top - 2, bw, 50, c.ink, 'rx="2"'),
    `</g>`,
    rect(off, top, 3 * s, bot - top, 'none', `rx="5" stroke="${c.deep}" stroke-width="4"`),
    `<g class="dot">${circ(off + 0.5 * s, 76, 7.5, c.brass)}</g>`,
  ].join('');
};
S['do-giua'].anim = `
.play .dot{transform-box:fill-box;transform-origin:center;animation:hm-drop 1.1s cubic-bezier(.3,1.4,.5,1) both}
@keyframes hm-drop{0%{transform:translateY(-58px);opacity:0}35%{opacity:1}70%{transform:translateY(0) scale(1.18,.84)}100%{transform:none}}`;

// A5 Hm dùng chung cọc (bị loại: chỉ còn 4 phím, sai sự thật 2–3)
S['hm-chung'] = (c) => {
  const w = 12, xs = [16, 38, 62, 84], r = 11;
  const ya = 20 + w / 2 + r;
  return rect(xs[0] - w / 2, 20, w, 60, c.ink) + rect(xs[0], 45, xs[1] - xs[0], 10, c.brass)
    + pathEl(`M${xs[1]} 80V${ya}A${r} ${r} 0 0 1 ${xs[2]} ${ya}V80M${xs[2]} ${ya}A${r} ${r} 0 0 1 ${xs[3]} ${ya}V80`, `fill="none" stroke="${c.ink}" stroke-width="${w}"`);
};

// ───── LÃNH THỔ B · Dây đàn và độ dài dây ─────

// B1 Đường cong dây: 13 dây một quãng tám, dài 2^(-n/12). Dây cuối dài đúng một nửa dây đầu.
// Đường bao các đầu dây chính là đường cong hông đàn grand.
S['duong-cong'] = (c) => {
  const top = 15, L0 = 74, x0 = 13, dx = 74 / 12;
  let out = rect(8, 8, 84, 7, c.ink);
  for (let i = 0; i <= 12; i++) {
    const L = L0 * Math.pow(2, -i / 12);
    out += `<g class="str" style="animation-delay:${(i * 0.09).toFixed(2)}s">${rect(x0 + i * dx - 1.4, top, 2.8, L, c.note ? c.note(i) : c.deep)}</g>`;
  }
  const pts = [];
  for (let k = 0; k <= 60; k++) {
    const i = (k / 60) * 12;
    pts.push(`${f(x0 + i * dx)} ${f(top + L0 * Math.pow(2, -i / 12) + 5)}`);
  }
  out += pathEl(`M8.6 15V${f(top + L0 + 5)}L${pts.join('L')}L${f(91.4)} ${f(top + L0 / 2 + 5)}V15`, `fill="none" stroke="${c.ink}" stroke-width="3.6" stroke-linejoin="round"`);
  return out;
};
S['duong-cong'].anim = `
.play .str{transform-box:fill-box;transform-origin:top;animation:hm-drawy .5s cubic-bezier(.2,.8,.2,1) both}
@keyframes hm-drawy{from{transform:scaleY(0)}to{transform:none}}`;

// B2 H quãng tám: chân trái dài gấp đôi chân phải (2:1 = quãng tám), gạch ngang là búa đồng thau
S['quang-tam'] = (c) => {
  const w = 10;
  return [
    `<g class="s1">${rect(22 - w / 2, 15, w, 74, c.ink)}</g>`,
    `<g class="s2">${rect(74 - w / 2, 52, w, 37, c.ink)}</g>`,
    circ(22, 12, 6, 'none', `stroke="${c.deep}" stroke-width="3.2"`),
    circ(74, 49, 6, 'none', `stroke="${c.deep}" stroke-width="3.2"`),
    `<g class="ham">${rect(22 + w / 2 - 0.3, 63, 52 - w + 0.6, 11, c.brass)}</g>`,
  ].join('');
};
S['quang-tam'].anim = `
.play .ham{animation:hm-strike .7s cubic-bezier(.3,1.3,.5,1) both}
.play .s1,.play .s2{transform-box:fill-box;transform-origin:center;animation:hm-vib .5s .55s linear both}
@keyframes hm-strike{from{transform:translateY(22px);opacity:0}to{transform:none;opacity:1}}
@keyframes hm-vib{0%,100%{transform:none}20%{transform:scaleX(1.22)}40%{transform:scaleX(.9)}60%{transform:scaleX(1.1)}80%{transform:scaleX(.97)}}`;

// B3 Mặt kẻ Xenakis (bị loại: không đọc được ở 16px)
S['xenakis'] = (c) => {
  let out = '';
  for (let i = 0; i <= 16; i++) {
    const t = i / 16;
    const x1 = 10 + 80 * t, y1 = 12 + 26 * Math.sin(Math.PI * t);
    const x2 = 90 - 80 * Math.pow(t, 1.4), y2 = 88 - 20 * Math.sin(Math.PI * t);
    out += `<line x1="${f(x1)}" y1="${f(y1)}" x2="${f(x2)}" y2="${f(y2)}" stroke="${i === 8 ? c.brass : c.deep}" stroke-width="1.8"/>`;
  }
  return out;
};

// B4 Nắp đàn mở (bị loại: thành bóng đàn grand clip-art)
S['nap-dan'] = (c) => pathEl('M8 72H92V80H8Z', `fill="${c.ink}"`) + pathEl('M14 70L88 30', `stroke="${c.ink}" stroke-width="6" stroke-linecap="round"`) + pathEl('M62 72L58 45', `stroke="${c.brass}" stroke-width="4"`) + rect(12, 80, 6, 12, c.ink) + rect(82, 80, 6, 12, c.ink);

// B5 Đơn huyền 6:4:3 (bị loại: giống biểu đồ cột / thanh âm lượng)
S['don-huyen'] = (c) => rect(8, 86, 84, 4, c.ink) + rect(18, 14, 12, 72, c.deep) + rect(44, 38, 12, 48, c.deep) + rect(70, 50, 12, 36, c.brass);

// ───── LÃNH THỔ C · Cuộn giấy pianola ─────

// C1 Cuộn đục chữ HM (bị loại: gần "gam pixel" đã có)
S['cuon-hm'] = (c) => {
  const H = ['10001', '10001', '11111', '10001', '10001'];
  const M = ['10001', '11011', '10101', '10001', '10001'];
  let out = rect(4, 18, 92, 64, c.tint, 'rx="6"');
  [H, M].forEach((g, gi) => g.forEach((row, ry) => [...row].forEach((b, rx) => {
    if (b === '1') out += rect(10 + gi * 44 + rx * 7.6, 24 + ry * 10.6, 5.2, 8, c.hole, 'rx="2.6"');
  })));
  return out;
};

// C2 Cuộn tiến trình I–IV–V–I: 13 cột C…C', mỗi hàng là một hợp âm thật
S['cuon-tien-trinh'] = (c) => {
  const chords = [[0, 4, 7], [5, 9, 12], [2, 7, 11], [0, 4, 7, 12]];
  const rows = [[12, 18], [33, 14], [50, 14], [67, 22]];
  let holes = '';
  chords.forEach((ch, i) => ch.forEach((n) => {
    holes += rect(13.4 + n * 6 - 2.3, rows[i][0], 4.6, rows[i][1], c.holeNote ? c.holeNote(n) : c.hole, 'rx="2.3"');
  }));
  return `<clipPath id="${c.uid}-cl"><rect x="5" y="5" width="90" height="90" rx="9"/></clipPath>`
    + rect(5, 5, 90, 90, c.lacquer, 'rx="9"')
    + `<g clip-path="url(#${c.uid}-cl)"><g class="roll">${holes}</g></g>`
    + rect(5, 5, 90, 90, 'none', `rx="9" stroke="${c.edge}" stroke-width="2"`);
};
S['cuon-tien-trinh'].anim = `
.play .roll{animation:hm-roll 2.4s cubic-bezier(.3,.1,.3,1) both}
@keyframes hm-roll{from{transform:translateY(-88px)}to{transform:none}}`;

// C3 H lỗ đục: hai lỗ dài (C và C', quãng tám) + hai lỗ ngắn ở cột E và G → hợp âm Đô trưởng
S['lo-duc'] = (c) => {
  const col = (n) => 27.5 + (n * 45) / 12;
  const holes = rect(col(0) - 6, 17, 12, 66, c.hole, 'rx="6"') + rect(col(12) - 6, 17, 12, 66, c.hole, 'rx="6"')
    + rect(col(4) - 4.5, 42, 9, 16, c.hole, 'rx="4.5"') + rect(col(7) - 4.5, 42, 9, 16, c.hole, 'rx="4.5"');
  return `<clipPath id="${c.uid}-cl"><rect x="7" y="7" width="86" height="86" rx="12"/></clipPath>`
    + rect(7, 7, 86, 86, c.tint, 'rx="12"')
    + `<g clip-path="url(#${c.uid}-cl)"><g class="roll">${holes}</g></g>`;
};
S['lo-duc'].anim = `
.play .roll{animation:hm-roll2 1.8s cubic-bezier(.25,.1,.25,1) both}
@keyframes hm-roll2{from{transform:translateY(-86px)}to{transform:none}}`;

// C4 Thanh đọc (bị loại: thành hàng chấm vô nghĩa ở cỡ nhỏ)
S['thanh-doc'] = (c) => {
  let out = rect(6, 40, 88, 20, c.ink, 'rx="10"');
  for (let i = 0; i < 9; i++) out += circ(15 + i * 8.75, 50, 2.8, i === 4 ? c.brass : c.bg);
  return out;
};

// ───── LÃNH THỔ D · Khoảng cách phím của hợp âm ─────

// D1 m 4:3: chữ m có hai vòm rộng 4 và 3 nửa cung = hợp âm trưởng. Chuyển động: đổi sang 3:4 (thứ).
const mPath = (a, b) => {
  const x0 = 12, s = 11, xs = [x0, x0 + a * s, x0 + (a + b) * s];
  const ry = 15, ya = 37;
  return `M${xs[0]} 80V${ya}A${f((xs[1] - xs[0]) / 2)} ${ry} 0 0 1 ${f(xs[1])} ${ya}V80M${f(xs[1])} ${ya}A${f((xs[2] - xs[1]) / 2)} ${ry} 0 0 1 ${f(xs[2])} ${ya}V80`;
};
S['m-43'] = (c) => {
  let dots = '';
  for (let i = 0; i <= 7; i++) dots += circ(12 + i * 11, 92, [0, 4, 7].includes(i) ? 3.3 : 2, [0, 4, 7].includes(i) ? c.brass : c.soft, `class="${i === 4 ? 'maj' : i === 3 ? 'minx' : ''}"`);
  dots += circ(12 + 3 * 11, 92, 3.3, c.brass, 'class="min" opacity="0"');
  return `<g class="maj">${pathEl(mPath(4, 3), `fill="none" stroke="${c.deep}" stroke-width="11"`)}</g>`
    + `<g class="min" opacity="0">${pathEl(mPath(3, 4), `fill="none" stroke="${c.deep}" stroke-width="11"`)}</g>` + dots;
};
S['m-43'].anim = `
.play .maj{animation:hm-out 2.8s ease-in-out both}
.play .min{animation:hm-in 2.8s ease-in-out both}
@keyframes hm-out{0%,20%{opacity:1}40%,60%{opacity:0}80%,100%{opacity:1}}
@keyframes hm-in{0%,20%{opacity:0}40%,60%{opacity:1}80%,100%{opacity:0}}`;

// D2 Bàn tay quãng tám 1⌒5 (bị loại: thành cầu vồng/cây cầu)
S['ban-tay-8'] = (c) => pathEl('M18 74A32 32 0 0 1 82 74', `fill="none" stroke="${c.deep}" stroke-width="9" stroke-linecap="round"`)
  + glyphPath('IBMPlexMono-SemiBold.ttf', '1', 18, 92, 22, c.ink) + glyphPath('IBMPlexMono-SemiBold.ttf', '5', 82, 92, 22, c.ink);

// D3 Treatise (bị loại: quá trừu tượng, không kể được piano)
S['treatise'] = (c) => rect(6, 56, 88, 9, c.ink) + circ(34, 34, 13, 'none', `stroke="${c.deep}" stroke-width="5"`) + rect(64, 22, 4, 34, c.brass) + glyphPath('IBMPlexMono-Medium.ttf', '3', 80, 90, 18, c.deep);

// ───── LÃNH THỔ E · Cơ cấu action, búa, bàn đạp ─────

// E1 Cần bẩy: phím là cái bập bênh; ấn nhẹ đầu trước, búa bay lên chạm dây
S['can-bay'] = (c) => `
${rect(10, 12, 80, 4.5, c.ink)}
<g class="act">
  ${pathEl('M9 76L83 60', `stroke="${c.ink}" stroke-width="10" stroke-linecap="round"`)}
  ${rect(64.3, 40, 4, 22, c.ink)}
  ${circ(66.3, 30, 11, c.deep)}
</g>
${circ(12, 59, 5.5, c.sig, 'class="tip"')}
${pathEl('M44 69L33 90H55Z', `fill="${c.brass}"`)}`;
S['can-bay'].anim = `
.play .act{transform-box:view-box;transform-origin:44px 69px;animation:hm-lever 1.6s ease-in-out both}
.play .tip{animation:hm-press 1.6s ease-in-out both}
@keyframes hm-lever{0%{transform:rotate(-12deg)}35%,70%{transform:rotate(0)}100%{transform:rotate(0)}}
@keyframes hm-press{0%{transform:translateY(-14px)}35%{transform:none}}`;

// E2 H hai búa: hai búa đàn quay đầu vào nhau, chạm một sợi dây đồng ở giữa
S['hai-bua'] = (c) => `
${rect(48.7, 6, 2.6, 88, c.brass)}
<g class="hl">${rect(13, 14, 13, 72, c.ink)}${rect(26, 46, 12, 8, c.ink)}${rect(36, 38, 10.5, 24, c.deep, 'rx="4"')}</g>
<g class="hr">${rect(74, 14, 13, 72, c.ink)}${rect(62, 46, 12, 8, c.ink)}${rect(53.5, 38, 10.5, 24, c.deep, 'rx="4"')}</g>`;
S['hai-bua'].anim = `
.play .hl{animation:hm-hl 1.1s cubic-bezier(.4,1.6,.5,1) both}
.play .hr{animation:hm-hr 1.1s cubic-bezier(.4,1.6,.5,1) both}
@keyframes hm-hl{0%{transform:translateX(-9px)}100%{transform:none}}
@keyframes hm-hr{0%{transform:translateX(9px)}100%{transform:none}}`;

// E3 Ba bàn đạp (bị loại: nhìn thành âm thoa/đinh ba, âm thoa nằm trong danh sách cấm)
S['ba-ban-dap'] = (c) => rect(26, 10, 48, 18, c.ink, 'rx="4"') + rect(30, 28, 8, 50, c.ink) + rect(46, 28, 8, 46, c.ink) + rect(62, 28, 8, 56, c.ink)
  + rect(24, 76, 20, 7, c.ink, 'rx="3"') + rect(40, 72, 20, 7, c.ink, 'rx="3"') + rect(56, 82, 22, 8, c.brass, 'rx="3"');

// E4 Kandinsky: điểm (búa), đường (dây), mặt (phím) theo "Point and Line to Plane"
S['kandinsky'] = (c) => `
${pathEl('M66 94H95V60Z', `fill="${c.brass}"`)}
${rect(70, 16, 9, 38, c.ink)}
<line x1="6" y1="84" x2="94" y2="10" stroke="${c.ink}" stroke-width="2.6"/>
<g class="ham">${circ(36, 40, 23, c.sig)}</g>
${rect(14, 78, 9, 9, c.felt)}`;
S['kandinsky'].anim = `
.play .ham{animation:hm-k 1.4s cubic-bezier(.3,1.5,.5,1) both}
@keyframes hm-k{0%{transform:translate(-14px,18px)}100%{transform:none}}`;

// E5 Búa chạm dây (bị loại: nhìn thành kẹo mút/đinh ghim)
S['bua-day'] = (c) => rect(8, 22, 84, 4, c.ink) + circ(50, 40, 13, c.deep) + rect(47, 52, 6, 38, c.ink);

// ───── LÃNH THỔ F · Ngón tay đánh số 1–5 ─────

// F1 Số ngón trên phím (bị loại: giống nút/huy hiệu chung chung)
S['so-ngon'] = (c) => rect(32, 34, 36, 58, c.ink, 'rx="5"') + glyphPath('IBMPlexMono-SemiBold.ttf', '1', 50, 27, 26, c.brassText);

// F2 1·3·5 (bị loại: quá gần ý "hợp âm C-E-G" đã có)
S['mot-ba-nam'] = (c) => glyphPath('IBMPlexMono-SemiBold.ttf', '1', 17, 64, 36, c.ink) + circ(33.5, 52, 3, c.brass)
  + glyphPath('IBMPlexMono-SemiBold.ttf', '3', 50, 64, 36, c.ink) + circ(66.5, 52, 3, c.brass) + glyphPath('IBMPlexMono-SemiBold.ttf', '5', 83, 64, 36, c.ink);

// F3 Bàn tay 5 ngón đặt trên phím; ngón 1-3-5 (màu đậm) đang bấm hợp âm ba
S['ban-tay'] = (c) => {
  const fingers = [[30, 24], [47, 13], [64, 22], [81, 36]];
  let out = rect(6, 88, 88, 3.5, c.ink);
  out += `<g class="f135">${rect(11, 47, 13, 39, c.deep, 'rx="6.5" transform="rotate(-16 17.5 86)"')}</g>`;
  fingers.forEach(([x, top], i) => {
    const n = i + 2, press = n % 2 === 1;
    out += `<g class="${press ? 'f135' : ''}">${rect(x, top, 13, 86 - top, press ? c.deep : c.sig, 'rx="6.5"')}</g>`;
  });
  [[1, 16, 80.5], [2, 36.5, 80.5], [3, 53.5, 80.5], [4, 70.5, 80.5], [5, 87.5, 80.5]].forEach(([n, x, y]) => {
    out += glyphPath('IBMPlexMono-Bold.ttf', String(n), x, y, 9.5, c.knock);
  });
  return out;
};
S['ban-tay'].anim = `
.play .f135{animation:hm-dip2 1.2s ease-in-out both}
@keyframes hm-dip2{0%,100%{transform:none}30%,60%{transform:translateY(3.5px)}}`;

// F4 Vòng bút chì của thầy (bị loại: thành huy hiệu số 3)
S['vong-but'] = (c) => circ(50, 50, 34, 'none', `stroke="${c.brass}" stroke-width="5"`) + glyphPath('IBMPlexMono-SemiBold.ttf', '3', 50, 66, 46, c.ink);

module.exports = { S, BLACK, IS_BLACK };

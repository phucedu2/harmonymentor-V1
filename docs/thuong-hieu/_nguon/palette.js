// Bảng màu "Đồng & Gỉ" v1.0, chỉ dùng màu trong họ và sắc độ trung gian của nó.
const NOTE = { 0: '#3CC3AB', 7: '#28BFD2', 2: '#58B5ED', 9: '#8AA8F7', 4: '#B49AED', 11: '#D48FD1', 6: '#E78AAA', 1: '#ED8C80', 8: '#E3975A', 3: '#CAA647', 10: '#A4B558', 5: '#73C07F' };
const note = (n) => NOTE[((n % 12) + 12) % 12];
let uidN = 0;
function palette(mode, opt = {}) {
  const base = {
    light: { bg: '#F2F3EA', ink: '#0C231F', deep: '#006D61', sig: '#45C2AB', brass: '#E0A53E', brassText: '#7C5502', felt: '#B4343B', tint: '#E8BA70', hole: '#0C231F', soft: '#9AB0AC', knock: '#F2F3EA', lacquer: '#0C231F', edge: '#0C231F', text: '#0C231F' },
    dark: { bg: '#081613', ink: '#F2F3EA', deep: '#45C2AB', sig: '#7DD6C2', brass: '#E8B458', brassText: '#E8B458', felt: '#EF7E7C', tint: '#D5A149', hole: '#081613', soft: '#4F625F', knock: '#081613', lacquer: '#101F1C', edge: '#45C2AB', text: '#F2F3EA' },
  };
  let c;
  if (mode === 'mono' || mode === 'mono-inv') {
    const fg = mode === 'mono' ? '#0C231F' : '#F2F3EA', bg = mode === 'mono' ? '#FFFFFF' : '#0C231F';
    c = { bg, ink: fg, deep: fg, sig: fg, brass: fg, brassText: fg, felt: fg, tint: fg, hole: bg, soft: fg, knock: bg, lacquer: fg, edge: fg, text: fg };
  } else {
    c = { ...base[mode] };
    // Màu 12 nốt chỉ dành cho bản "táo bạo" (Phúc chọn 2B ngày 27/10/2026)
    if (opt.notes) { c.note = note; c.holeNote = note; }
  }
  c.mode = mode;
  c.uid = `hm${(uidN++).toString(36)}`;
  return c;
}
module.exports = { palette, note, NOTE };

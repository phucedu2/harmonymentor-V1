import { normalizePitchClass } from "./audio/musicUtils";

// Bàn phím 2 quãng tám chỉ để HIỂN THỊ (tô màu theo lớp cao độ), dùng ở trang chủ.
// Không dùng phím đàn để nhập đáp án, vì phím đàn không cho biết tên nốt (G# hay Ab).
// FE-021: đọc tên nốt bằng cùng hàm normalizePitchClass của VirtualPiano (một chỗ hiểu "Bbb", "Fx", "♯"),
// thay cho bộ phân tích riêng trước đây. Giữ SVG riêng vì trang chủ cần diện mạo cũ (quyết định 4A)
// và không cần âm thanh/bấm phím như VirtualPiano.
const PCS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const WHITE = [0, 2, 4, 5, 7, 9, 11];
const BLACK_AFTER: Record<number, number> = { 0: 1, 2: 3, 5: 6, 7: 8, 9: 10 };
const toPc = (name: string) => PCS.indexOf(normalizePitchClass(name));

// active: tô màu chính để minh họa (trang chủ), khác good/bad vốn mang nghĩa đúng/sai.
export default function Piano({ good = [], bad = [], active = [], label = "Bàn phím piano" }: { good?: string[]; bad?: string[]; active?: string[]; label?: string }) {
  const goodPc = new Set(good.map(toPc));
  const badPc = new Set(bad.map(toPc));
  const activePc = new Set(active.map(toPc));
  // Token của @theme trong index.css. Biến SVG trỏ tới biến CSS không tồn tại sẽ tô đen toàn bộ phím.
  const color = (pc: number, black: boolean) =>
    goodPc.has(pc) ? "var(--color-success)" : badPc.has(pc) ? "var(--color-danger)" : activePc.has(pc) ? "var(--color-primary)" : black ? "var(--color-ink)" : "var(--color-surface)";
  const whites = [0, 1].flatMap((o) => WHITE.map((pc) => ({ pc, o })));
  const W = 28;
  // data-force-light: phím trắng/đen giữ màu thật ở chế độ tối (giống VirtualPiano), nếu không surface/ink sẽ lật ngược.
  return (
    <svg data-force-light className="piano" viewBox={`0 0 ${whites.length * W} 110`} role="img" aria-label={label}>
      {whites.map(({ pc, o }, i) => (
        <rect key={`w${o}${pc}`} x={i * W} y={0} width={W} height={110} fill={color(pc, false)} stroke="var(--color-line)" />
      ))}
      {whites.map(({ pc, o }, i) =>
        BLACK_AFTER[pc] !== undefined ? (
          <rect key={`b${o}${pc}`} x={i * W + W * 0.65} y={0} width={W * 0.7} height={68} rx={2}
            fill={color(BLACK_AFTER[pc], true)} stroke="var(--color-line)" />
        ) : null,
      )}
    </svg>
  );
}

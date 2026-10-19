// Bàn phím 2 quãng tám chỉ để HIỂN THỊ (tô màu theo lớp cao độ).
// Không dùng phím đàn để nhập đáp án, vì phím đàn không cho biết tên nốt (G# hay Ab).
const NATURAL_PC: Record<string, number> = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };

export function pitchClass(name: string): number | null {
  const m = /^([A-Ga-g])(##|bb|#|b|x)?/.exec(name.trim());
  if (!m) return null;
  const acc = { "##": 2, x: 2, "#": 1, b: -1, bb: -2 }[m[2] ?? ""] ?? 0;
  return (((NATURAL_PC[m[1].toUpperCase()] + acc) % 12) + 12) % 12;
}

const WHITE = [0, 2, 4, 5, 7, 9, 11];
const BLACK_AFTER: Record<number, number> = { 0: 1, 2: 3, 5: 6, 7: 8, 9: 10 };

// active: tô màu chính để minh họa (trang chủ), khác good/bad vốn mang nghĩa đúng/sai.
export default function Piano({ good = [], bad = [], active = [], label = "Bàn phím piano" }: { good?: string[]; bad?: string[]; active?: string[]; label?: string }) {
  const goodPc = new Set(good.map(pitchClass));
  const badPc = new Set(bad.map(pitchClass));
  const activePc = new Set(active.map(pitchClass));
  const color = (pc: number, black: boolean) =>
    goodPc.has(pc) ? "var(--good)" : badPc.has(pc) ? "var(--bad)" : activePc.has(pc) ? "var(--accent)" : black ? "var(--key-black)" : "var(--key-white)";
  const whites = [0, 1].flatMap((o) => WHITE.map((pc) => ({ pc, o })));
  const W = 28;
  return (
    <svg className="piano" viewBox={`0 0 ${whites.length * W} 110`} role="img" aria-label={label}>
      {whites.map(({ pc, o }, i) => (
        <rect key={`w${o}${pc}`} x={i * W} y={0} width={W} height={110} fill={color(pc, false)} stroke="var(--line)" />
      ))}
      {whites.map(({ pc, o }, i) =>
        BLACK_AFTER[pc] !== undefined ? (
          <rect key={`b${o}${pc}`} x={i * W + W * 0.65} y={0} width={W * 0.7} height={68} rx={2}
            fill={color(BLACK_AFTER[pc], true)} stroke="var(--line)" />
        ) : null,
      )}
    </svg>
  );
}

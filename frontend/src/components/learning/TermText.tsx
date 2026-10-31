// Chú giải thuật ngữ lần đầu xuất hiện trong bài (phuc-music Bước 3, nguyên tắc cho người mới).
// Lời giải nghĩa là nhãn giao diện, Đạt/Astra duyệt lại; âm thanh luôn lấy nốt từ Music Engine
// (transpose cho quãng, inspectChord cho hợp âm), frontend không tự tính nốt (nguyên tắc bất biến 1).
import { Fragment, useState, type ReactNode } from "react";
import { api } from "../../api";
import { audioEngine } from "../../audio/AudioEngine";
import { midiToScientific, pitchClassesToAscendingNotes, scientificToMidi } from "../../audio/musicUtils";

type Sound = { kind: "interval"; code: string } | { kind: "chord"; symbol: string };
export type GlossaryTerm = { id: string; pattern: RegExp; label: string; definition: string; sound?: Sound };

// Thứ tự quan trọng: cụm dài ("quãng tám", "hợp âm trưởng") đứng trước cụm ngắn để khớp đúng.
export const TERMS: GlossaryTerm[] = [
  { id: "half-step", pattern: /nửa cung/i, label: "Nửa cung", definition: "Khoảng cách nhỏ nhất giữa hai phím đàn kề nhau (tính cả phím đen). Ví dụ E–F, hoặc C với phím đen ngay bên phải nó.", sound: { kind: "interval", code: "m2" } },
  { id: "octave", pattern: /quãng tám/i, label: "Quãng tám", definition: "Hai nốt cùng tên, nốt trên cao gấp đôi nốt dưới, cách nhau 12 nửa cung. Ví dụ C4 lên C5.", sound: { kind: "interval", code: "P8" } },
  { id: "major-triad", pattern: /hợp âm trưởng/i, label: "Hợp âm trưởng", definition: "Ba nốt: nốt gốc, quãng 3 trưởng (M3) và quãng 5 đúng (P5) tính từ nốt gốc. Thường được mô tả là nghe sáng.", sound: { kind: "chord", symbol: "C" } },
  { id: "minor-triad", pattern: /hợp âm thứ/i, label: "Hợp âm thứ", definition: "Ba nốt: nốt gốc, quãng 3 thứ (m3) và quãng 5 đúng (P5). Thường được mô tả là nghe tối hơn hợp âm trưởng.", sound: { kind: "chord", symbol: "Cm" } },
  { id: "dim-triad", pattern: /hợp âm giảm/i, label: "Hợp âm giảm", definition: "Ba nốt: nốt gốc, quãng 3 thứ (m3) và quãng 5 giảm (d5). Nghe căng, hay muốn đi tiếp.", sound: { kind: "chord", symbol: "Cdim" } },
  { id: "aug-triad", pattern: /hợp âm tăng/i, label: "Hợp âm tăng", definition: "Ba nốt: nốt gốc, quãng 3 trưởng (M3) và quãng 5 tăng (A5).", sound: { kind: "chord", symbol: "Caug" } },
  { id: "M3", pattern: /\bM3\b/, label: "M3 · quãng 3 trưởng", definition: "Quãng gồm ba tên chữ cái (ví dụ C–D–E) và rộng 4 nửa cung.", sound: { kind: "interval", code: "M3" } },
  { id: "m3", pattern: /\bm3\b/, label: "m3 · quãng 3 thứ", definition: "Quãng gồm ba tên chữ cái và rộng 3 nửa cung, hẹp hơn M3 một nửa cung.", sound: { kind: "interval", code: "m3" } },
  { id: "P5", pattern: /\bP5\b/, label: "P5 · quãng 5 đúng", definition: "Quãng gồm năm tên chữ cái (ví dụ C–G) và rộng 7 nửa cung.", sound: { kind: "interval", code: "P5" } },
  { id: "d5", pattern: /\bd5\b/, label: "d5 · quãng 5 giảm", definition: "Quãng gồm năm tên chữ cái nhưng chỉ rộng 6 nửa cung, hẹp hơn P5 một nửa cung.", sound: { kind: "interval", code: "d5" } },
];

/** Gán mỗi thuật ngữ cho khối đầu tiên chứa nó, theo thứ tự khối trong bài. */
export function firstAppearances(blocks: { id: string; texts: string[] }[]): Map<string, Set<string>> {
  const result = new Map<string, Set<string>>();
  const seen = new Set<string>();
  for (const block of blocks) {
    const text = block.texts.join("\n");
    for (const term of TERMS) {
      if (seen.has(term.id) || !term.pattern.test(text)) continue;
      seen.add(term.id);
      if (!result.has(block.id)) result.set(block.id, new Set());
      result.get(block.id)!.add(term.id);
    }
  }
  return result;
}

/**
 * Chú giải lần xuất hiện đầu của các thuật ngữ trong `terms` (mỗi thuật ngữ một lần trong cả khối).
 * Là hàm thuần gọi trong lúc khối cha render, KHÔNG phải component: nếu đặt việc đánh dấu `claimed`
 * trong render của component con thì React StrictMode render hai lần, lần hai thấy thuật ngữ đã bị
 * "nhận" và bỏ mất chú giải. Khối cha tạo `claimed` mới mỗi lần render nên gọi lại bao nhiêu lần cũng ra cùng kết quả.
 */
export function annotateTerms(text: string, terms: Set<string> | undefined, claimed: Set<string>): ReactNode {
  if (!terms || terms.size === 0) return text;
  const parts: ReactNode[] = [];
  let rest = text;
  let guard = 0;
  while (rest && guard++ < TERMS.length) {
    let best: { term: GlossaryTerm; index: number; length: number } | null = null;
    for (const term of TERMS) {
      if (!terms.has(term.id) || claimed.has(term.id)) continue;
      const match = term.pattern.exec(rest);
      if (match && (best === null || match.index < best.index)) best = { term, index: match.index, length: match[0].length };
    }
    if (!best) break;
    claimed.add(best.term.id);
    parts.push(<Fragment key={parts.length}>{rest.slice(0, best.index)}</Fragment>);
    parts.push(<Term key={parts.length} term={best.term}>{rest.slice(best.index, best.index + best.length)}</Term>);
    rest = rest.slice(best.index + best.length);
  }
  if (parts.length === 0) return text;
  parts.push(<Fragment key={parts.length}>{rest}</Fragment>);
  return <>{parts}</>;
}

async function playSound(sound: Sound) {
  if (sound.kind === "interval") {
    const { note } = await api.transpose("C4", sound.code);
    // Engine có thể trả tên như B#4; chuyển qua MIDI để Tone phát đúng cao độ, giữ tên chuẩn cho hiển thị.
    const midi = scientificToMidi(note);
    await audioEngine.playChord(["C4", midi === null ? note : midiToScientific(midi)], "2n");
    return;
  }
  const chord = await api.inspectChord(sound.symbol);
  await audioEngine.playChord(pitchClassesToAscendingNotes(chord.notes, 4), "2n");
}

// Trên điện thoại khung giải nghĩa nổi cố định ngay trên thanh "Bước tiếp" để không tràn mép phải màn hình.
function Term({ term, children }: { term: GlossaryTerm; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState(false);
  const id = `thuat-ngu-${term.id}`;
  return <span className="relative inline" onKeyDown={(event) => { if (event.key === "Escape") setOpen(false); }}>
    <button type="button" aria-expanded={open} aria-controls={id} onClick={() => setOpen((value) => !value)}
      className="inline cursor-help rounded-sm border-b-2 border-dotted border-primary px-0.5 font-semibold text-primary-strong hover:bg-primary-soft">
      {children}
    </button>
    {open && <span id={id} role="note" className="fixed inset-x-4 bottom-24 z-30 grid gap-2 sm:absolute sm:inset-x-auto sm:bottom-auto sm:top-[calc(100%+6px)] sm:left-0 sm:w-72 rounded-xl border border-shell-line bg-shell p-3 text-left text-sm font-normal text-shell-text shadow-xl">
      <b className="text-shell-ink">{term.label}</b>
      <span>{term.definition}</span>
      {term.sound && <button type="button" className="min-h-11 rounded-lg bg-primary px-3 font-semibold text-white hover:bg-primary-strong"
        onClick={() => { setError(false); void playSound(term.sound!).catch(() => setError(true)); }}><span aria-hidden="true">▶</span> Nghe ví dụ</button>}
      {error && <span className="text-[#ffb4b0]">Chưa phát được âm thanh. Hãy thử lại.</span>}
      <button type="button" className="min-h-11 justify-self-end px-2 text-sm text-shell-muted underline" onClick={() => setOpen(false)}>Đóng</button>
    </span>}
  </span>;
}

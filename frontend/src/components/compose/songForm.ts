// Thao tác thuần trên form bài hát (thêm/xóa/kéo đổi thứ tự/sửa đoạn), tách khỏi giao diện để test bằng Vitest.
// Luật nghiệp vụ thật (chuyển đoạn, đột biến, năng lượng) vẫn do backend quyết; ở đây chỉ sửa danh sách đoạn.
import type { FormSection, ProgressionSlot, SectionType, SongForm, SongLength } from "../../audio/band/types";

export const MAX_SONG_BARS = 160;
export const BAR_CHOICES = [2, 4, 8, 12, 16];

export const SECTION_VI: Record<SectionType, string> = {
  intro: "Intro", verse: "Verse", pre: "Pre-Chorus", chorus: "Chorus", post: "Post-Chorus", bridge: "Bridge",
  breakdown: "Breakdown", solo: "Solo", outro: "Outro",
};
// Màu khối theo loại đoạn: dùng bảng màu nốt (nền nhạt, chữ đậm đạt tương phản AA), không dùng đồng thau làm chữ.
export const SECTION_COLOR: Record<SectionType, string> = {
  intro: "var(--color-note-c)", verse: "var(--color-note-g)", pre: "var(--color-note-ab)", chorus: "var(--color-note-fs)",
  post: "var(--color-note-b)", bridge: "var(--color-note-a)", breakdown: "var(--color-note-eb)", solo: "var(--color-note-d)",
  outro: "var(--color-note-f)",
};
// Tên viết tắt cho đoạn quá hẹp (điện thoại, đoạn 4 ô): giữ số thứ tự/"cuối" để vẫn phân biệt Chorus 1, Chorus cuối.
const SHORT: Record<SectionType, string> = {
  intro: "Intro", verse: "V", pre: "Pre", chorus: "Ch", post: "Post", bridge: "Br", breakdown: "Bd", solo: "Solo", outro: "Out",
};
export function shortLabel(type: SectionType, label: string): string {
  const tail = label.match(/\s(\d+|cuối)$/)?.[1];
  return tail ? `${SHORT[type]} ${tail}` : SHORT[type];
}

export const LENGTH_VI: Record<SongLength, string> = { short: "Ngắn", medium: "Vừa", full: "Đầy đủ" };
export const TRANSITION_VI: Record<string, string> = {
  auto: "Tự chọn theo phong cách", none: "Nối thẳng", fill_small: "Fill nhỏ", fill_big: "Fill tom lớn",
  snare_build: "Snare dồn", drop_bar: "Drop (im 2 phách)", stop_time: "Stop-time", pickup: "Nhát mồi",
  riser: "Riser", reverse_cymbal: "Cymbal ngược",
};
export const FEEL_VI: Record<string, string> = { auto: "Tự chọn", normal: "Bình thường", half: "Half-time", double: "Double-time" };
export const ENDING_VI: Record<string, string> = {
  auto: "Theo phong cách", fade: "Nhỏ dần", ritardando_fermata: "Chậm dần + ngân", big_hit: "Một nhát đồng loạt",
  tag_x3: "Tag ii–V × 3",
};
// Mặc định khi thêm đoạn mới: vòng hợp âm và năng lượng hợp vai trò của đoạn (sổ tay mục A).
const DEFAULTS: Record<SectionType, { bars: number; progression: ProgressionSlot; energy: number }> = {
  intro: { bars: 4, progression: "A", energy: 1 }, verse: { bars: 8, progression: "A", energy: 2 },
  pre: { bars: 4, progression: "A", energy: 3 }, chorus: { bars: 8, progression: "B", energy: 4 },
  post: { bars: 4, progression: "B", energy: 3 }, bridge: { bars: 8, progression: "C", energy: 3 },
  breakdown: { bars: 4, progression: "A", energy: 1 }, solo: { bars: 8, progression: "A", energy: 4 },
  outro: { bars: 4, progression: "A", energy: 2 },
};

export const totalBars = (sections: FormSection[]) => sections.reduce((n, s) => n + s.bars, 0);

const newId = (sections: FormSection[]) => {
  let i = sections.length + 1;
  while (sections.some((s) => s.id === `s${i}`)) i += 1;
  return `s${i}`;
};

/** Thêm đoạn sau vị trí `after` (−1 = đầu bài). Không vượt giới hạn 160 ô. */
export function addSection(sections: FormSection[], type: SectionType, after: number): FormSection[] {
  const d = DEFAULTS[type];
  if (totalBars(sections) + d.bars > MAX_SONG_BARS) return sections;
  const s: FormSection = { id: newId(sections), type, label: null, bars: d.bars, progression: d.progression,
    energy: d.energy, feel: "auto", hook: true, transition: "auto", seed: null };
  const out = [...sections];
  out.splice(after + 1, 0, s);
  return out;
}

export function removeSection(sections: FormSection[], index: number): FormSection[] {
  if (sections.length <= 1) return sections;
  return sections.filter((_, i) => i !== index);
}

/** Kéo đoạn từ vị trí `from` tới `to` (cả kéo thả và phím mũi tên dùng chung). */
export function moveSection(sections: FormSection[], from: number, to: number): FormSection[] {
  if (from === to || from < 0 || to < 0 || from >= sections.length || to >= sections.length) return sections;
  const out = [...sections];
  const [s] = out.splice(from, 1);
  out.splice(to, 0, s);
  return out;
}

/** Sửa một đoạn; đổi số ô bị chặn để tổng không quá 160. */
export function patchSection(sections: FormSection[], index: number, patch: Partial<FormSection>): FormSection[] {
  const out = sections.map((s, i) => (i === index ? { ...s, ...patch } : s));
  return totalBars(out) > MAX_SONG_BARS ? sections : out;
}

/** Số ô gợi ý cho một đoạn: bội số độ dài vòng (QĐ 7A) cộng các lựa chọn chuẩn 2/4/8/12/16. */
export function barOptions(cycle: number): number[] {
  const set = new Set(BAR_CHOICES);
  for (let k = 1; k * cycle <= 16; k += 1) set.add(k * cycle);
  return [...set].sort((a, b) => a - b);
}

/** Form để gửi lưu: vòng A luôn lấy từ lưới hợp âm của dự án (QĐ 1A); vòng trống gửi null. */
export function formForSave(form: SongForm, a: (string | null)[]): SongForm {
  const clean = (p: (string | null)[] | null) => (p && p.some(Boolean) ? p : null);
  return { ...form, progressions: { A: a, B: clean(form.progressions.B), C: clean(form.progressions.C) } };
}

export function emptyForm(a: (string | null)[], length: SongLength = "medium"): SongForm {
  return { length, hook: true, modulate: { enabled: false, semitones: 1 }, ending: "auto", progressions: { A: a, B: null, C: null } };
}

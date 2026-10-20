/**
 * Runtime lesson prose/questions live in backend/app/content/curriculum_specs.py.
 * This frontend module only contains reusable presentation configuration for
 * interactive lesson widgets. It intentionally does not duplicate curriculum text.
 */

export const REVIEW_INTERVALS_DAYS = [1, 3, 7, 14, 30] as const;

export type RootKeyOption = {
  label: string;
  spellings: string[];
  defaultSpelling: string;
};

export const ROOT_KEY_OPTIONS: RootKeyOption[] = [
  { label: "C", spellings: ["C"], defaultSpelling: "C" },
  { label: "C#/Db", spellings: ["C#", "Db"], defaultSpelling: "Db" },
  { label: "D", spellings: ["D"], defaultSpelling: "D" },
  { label: "D#/Eb", spellings: ["D#", "Eb"], defaultSpelling: "Eb" },
  { label: "E", spellings: ["E"], defaultSpelling: "E" },
  { label: "F", spellings: ["F"], defaultSpelling: "F" },
  { label: "F#/Gb", spellings: ["F#", "Gb"], defaultSpelling: "F#" },
  { label: "G", spellings: ["G"], defaultSpelling: "G" },
  { label: "G#/Ab", spellings: ["G#", "Ab"], defaultSpelling: "Ab" },
  { label: "A", spellings: ["A"], defaultSpelling: "A" },
  { label: "A#/Bb", spellings: ["A#", "Bb"], defaultSpelling: "Bb" },
  { label: "B", spellings: ["B"], defaultSpelling: "B" },
];

export type KeyOverviewCard = { symbol: string; label: string };
export type KeyOverviewTier = { id: string; title: string; note: string; keys: KeyOverviewCard[] };

export const TRIAD_KEY_TIERS: KeyOverviewTier[] = [
  {
    id: "tier-1",
    title: "Cấp 1 · Chỉ dùng phím trắng",
    note: "Bắt đầu ở đây để nhìn rõ cấu trúc mà chưa phải xử lý dấu hóa.",
    keys: [
      { symbol: "C", label: "C major" }, { symbol: "Dm", label: "D minor" },
      { symbol: "Em", label: "E minor" }, { symbol: "F", label: "F major" },
      { symbol: "G", label: "G major" }, { symbol: "Am", label: "A minor" },
    ],
  },
  {
    id: "tier-2",
    title: "Cấp 2 · Bắt đầu có phím đen",
    note: "Mỗi hợp âm bắt đầu yêu cầu ít nhất một dấu hóa hoặc một phím đen.",
    keys: [
      { symbol: "D", label: "D major" }, { symbol: "E", label: "E major" },
      { symbol: "A", label: "A major" }, { symbol: "Cm", label: "C minor" },
      { symbol: "Fm", label: "F minor" }, { symbol: "Gm", label: "G minor" },
      { symbol: "Bb", label: "Bb major" }, { symbol: "Eb", label: "Eb major" },
    ],
  },
  {
    id: "tier-3",
    title: "Cấp 3 · Nhiều dấu hóa, tên đồng âm",
    note: "Phần còn lại để đủ 12 giọng trưởng + 12 giọng thứ. Hãy ưu tiên hiểu nguyên lý trước khi học thuộc.",
    keys: [
      { symbol: "Db", label: "Db major" }, { symbol: "F#", label: "F# major" },
      { symbol: "Ab", label: "Ab major" }, { symbol: "B", label: "B major" },
      { symbol: "C#m", label: "C# minor" }, { symbol: "Ebm", label: "Eb minor" },
      { symbol: "F#m", label: "F# minor" }, { symbol: "G#m", label: "G# minor" },
      { symbol: "Bbm", label: "Bb minor" }, { symbol: "Bm", label: "B minor" },
    ],
  },
];

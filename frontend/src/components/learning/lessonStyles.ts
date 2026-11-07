// Lớp Tailwind dùng chung cho bài học và các widget nhạc (phuc-music Bước 3), thay cho styles.css cũ.
// Gom ở một chỗ để mọi khối trong bài cùng nhịp chữ, khoảng cách và màu "Đồng & Gỉ".

// Khối nội dung: tiêu đề, đoạn văn và danh sách bên trong được định dạng bằng biến thể [&_x].
export const block =
  "rounded-2xl border border-line bg-surface p-5 text-ink leading-relaxed " +
  "[&_h3]:mt-1 [&_h3]:mb-2 [&_h3]:font-display [&_h3]:text-xl [&_h3]:font-semibold [&_h3]:leading-snug " +
  "[&_p]:my-2 [&_ul]:my-2 [&_ul]:list-disc [&_ul]:space-y-1 [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5";

// Biến thể màu theo loại khối (nền nhạt, viền đậm hơn một chút); chữ luôn là ink nên tương phản không đổi.
export const blockTone = {
  summary: "border-primary/30 bg-primary-soft/50",
  callout: "border-brass/60 bg-warning-soft/60",
  interactive: "border-dashed border-primary/40",
  piano: "bg-bg",
  audio: "bg-bg",
  explorer: "border-primary/25",
  checkpoint: "border-primary/40 bg-primary-soft/30 shadow-[inset_4px_0_0_var(--color-primary)]",
  compose: "border-signature bg-surface shadow-[inset_4px_0_0_var(--color-signature)]",
} as const;

export const kicker = "block text-xs font-semibold tracking-[0.1em] text-primary uppercase";
export const muted = "text-muted";
export const hint = "text-sm text-muted";

export const input =
  "min-h-11 w-full rounded-lg border border-line bg-surface px-3 text-base text-ink placeholder:text-muted";

// Nút chọn trong widget (nốt gốc, loại quãng, đáp án trắc nghiệm): trạng thái chọn có cả màu lẫn aria-pressed.
export function choice(selected: boolean, extra = "") {
  return `min-h-11 rounded-lg border px-3 py-2 text-left text-sm font-semibold transition-colors ${
    selected ? "border-primary bg-primary-soft text-primary-strong" : "border-line bg-surface text-ink hover:border-primary"
  } ${extra}`;
}

// Liên kết dạng chữ (quay lại, đi tới câu chưa đúng).
export const textButton = "inline-flex min-h-11 items-center text-left font-semibold text-primary underline-offset-4 hover:underline";

export const resultGood = "mt-3 rounded-xl border border-success/40 bg-success-soft px-4 py-3 text-sm text-ink";
export const resultBad = "mt-3 rounded-xl border border-danger/40 bg-danger-soft px-4 py-3 text-sm text-ink";
export const explanation = "mt-2 border-t border-dashed border-current pt-2";

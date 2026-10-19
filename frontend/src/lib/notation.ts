// Chỉ đổi cách HIỂN THỊ ký hiệu (b → ♭, # → ♯); không tính nhạc lý ở frontend.
// Ký tự đầu là tên nốt nên giữ nguyên ("Bb" → "B♭", "Bbb" → "B♭♭", "Ebm7b5" → "E♭m7♭5").
export function prettyNote(text: string): string {
  if (!text) return text;
  return text[0] + text.slice(1).replace(/b/g, "♭").replace(/#/g, "♯");
}

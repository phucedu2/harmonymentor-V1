/** Ghép chuỗi hiển thị vòng hợp âm từ ký hiệu do Music Engine trả về (frontend không tự tính nhạc lý). */
export function progressionLabelSuffix(prompt: string): string {
  const parts = prompt.split("=");
  return parts.length > 1 ? parts.slice(1).join("=").trim() : "";
}

export function progressionText(symbols: string[], suffix: string): string {
  const chords = symbols.join(" → ");
  return suffix ? `${chords}  =  ${suffix}` : chords;
}

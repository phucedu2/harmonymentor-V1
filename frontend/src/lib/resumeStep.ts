// RS-17: đổi máy hoặc xóa dữ liệu trình duyệt thì vị trí bước lưu ở localStorage mất, người học bị đưa về Bước 1
// dù đã làm đúng nhiều câu. Hàm này đoán bước nên mở lại từ tiến độ do máy chủ lưu: bước có câu hỏi đầu tiên
// chưa đúng; chưa đúng câu nào hoặc đã đúng hết thì giữ Bước 1 (không đoán bừa).
export function resumeStepIndex(stepExerciseIds: (string | undefined)[], correct: ReadonlySet<string>): number {
  const anyCorrect = stepExerciseIds.some((id) => id !== undefined && correct.has(id));
  if (!anyCorrect) return 0;
  const index = stepExerciseIds.findIndex((id) => id !== undefined && !correct.has(id));
  return index < 0 ? 0 : index;
}

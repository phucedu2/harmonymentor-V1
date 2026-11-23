// Logic thuần của màn duyệt bản nháp AI (ADR-033), tách ra để test bằng Vitest.
import type { AiFlag, AiQuestion } from "../api";

/** Số cờ duyệt chưa tick "Đã đối chiếu": còn > 0 thì chưa xuất bản được. */
export const unackedCount = (flags: AiFlag[] | undefined, acked: string[] | undefined) =>
  (flags ?? []).filter((f) => !(acked ?? []).includes(f.id)).length;

/** Xóa khối `index` (đếm từ 0): câu gắn khối đó mất chỗ gắn và phải duyệt lại, câu gắn khối sau dời số thứ tự. */
export function remapAfterBlockRemoved(questions: AiQuestion[], index: number): AiQuestion[] {
  const removed = index + 1;
  return questions.map((q) => {
    if (typeof q.block_ref !== "number") return q;
    if (q.block_ref === removed) return { ...q, block_ref: null, reviewed: false };
    return q.block_ref > removed ? { ...q, block_ref: q.block_ref - 1 } : q;
  });
}

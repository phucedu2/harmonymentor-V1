import { describe, expect, it } from "vitest";
import type { AiFlag, AiQuestion } from "../api";
import { remapAfterBlockRemoved, unackedCount } from "./aiDraftReview";

const q = (block_ref: number | null | undefined): AiQuestion =>
  ({ kind: "mcq", prompt: "p", skill_id: "s", explanation: "", page: 1, block_ref, reviewed: true });
const f = (id: string): AiFlag => ({ id, type: "verbatim", label: "x", where: "block:1", detail: "d" });

describe("duyệt bản nháp AI (ADR-033)", () => {
  it("xóa khối 2: câu khối 2 mất chỗ gắn và cần duyệt lại, câu khối 3 thành khối 2", () => {
    const out = remapAfterBlockRemoved([q(1), q(2), q(3), q(undefined)], 1);
    expect(out.map((x) => x.block_ref)).toEqual([1, null, 2, undefined]);
    expect(out[1].reviewed).toBe(false);
    expect(out[0].reviewed).toBe(true);
  });
  it("đếm cờ chưa đối chiếu; mã cờ cũ không còn thì không tính", () => {
    expect(unackedCount([f("a"), f("b")], ["a", "zzz"])).toBe(1);
    expect(unackedCount(undefined, undefined)).toBe(0);
  });
});

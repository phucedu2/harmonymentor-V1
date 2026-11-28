import { describe, expect, it } from "vitest";
import type { AiFlag, AiQuestion } from "../api";
import { ratePct, remapAfterBlockRemoved, unackedCount } from "./aiDraftReview";

const q = (block_ref: number | null | undefined): AiQuestion =>
  ({ kind: "mcq", prompt: "p", skill_id: "s", explanation: "", page: 1, block_ref, reviewed: true });
const f = (id: string): AiFlag => ({ id, type: "verbatim", label: "x", where: "block:1", detail: "d" });

describe("duyệt bản nháp AI (ADR-039)", () => {
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

describe("ratePct (ADR-042)", () => {
  it("làm tròn phần trăm và hiện gạch khi chưa có mẫu số", () => {
    expect(ratePct(0.756)).toBe("76%");
    expect(ratePct(0)).toBe("0%");
    expect(ratePct(null)).toBe("—");
    expect(ratePct(undefined)).toBe("—");
    expect(ratePct(Number.NaN)).toBe("—");
  });
});

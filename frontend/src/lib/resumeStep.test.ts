import { describe, expect, it } from "vitest";
import { resumeStepIndex } from "./resumeStep";

describe("resumeStepIndex (RS-17)", () => {
  const ids = ["a", undefined, "b", undefined, "c"];
  it("mở lại ở bước có câu đầu tiên chưa đúng", () => {
    expect(resumeStepIndex(ids, new Set(["a"]))).toBe(2);
    expect(resumeStepIndex(ids, new Set(["a", "b"]))).toBe(4);
  });
  it("chưa đúng câu nào hoặc đúng hết thì về Bước 1", () => {
    expect(resumeStepIndex(ids, new Set())).toBe(0);
    expect(resumeStepIndex(ids, new Set(["a", "b", "c"]))).toBe(0);
  });
});

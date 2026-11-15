import { describe, expect, it } from "vitest";
import { progressionText, progressionLabelSuffix } from "./progressionText";

describe("progressionText (G1)", () => {
  it("nối ký hiệu hợp âm do máy chủ trả về, giữ nhãn chức năng sau dấu =", () => {
    expect(progressionText(["Gm7", "C7", "Fmaj7"], "T → PD")).toBe("Gm7 → C7 → Fmaj7  =  T → PD");
    expect(progressionText(["Gm7", "C7"], "")).toBe("Gm7 → C7");
  });
  it("lấy phần nhãn sau dấu = từ đề gốc của bài", () => {
    expect(progressionLabelSuffix("Cmaj7 → Dm7 → G7 → Cmaj7  =  T → PD → D → T")).toBe("T → PD → D → T");
    expect(progressionLabelSuffix("Dm7 → G7 → Cmaj7")).toBe("");
  });
});

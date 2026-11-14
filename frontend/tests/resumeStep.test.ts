// RS-17: đổi máy (không có vị trí đã lưu) thì mở bài tới câu chưa làm đúng đầu tiên.
import { describe, expect, it } from "vitest";
import { resumeStep } from "../src/components/learning/LessonRunner";

const steps = [
  { id: "intro" }, { id: "B01" }, { id: "CP1", exerciseId: "Q1" }, { id: "B02" },
  { id: "CP2", exerciseId: "Q2" }, { id: "quiz" }, { id: "finish" },
];

describe("resumeStep", () => {
  it("chưa làm câu nào thì mở Bước 1", () => {
    expect(resumeStep(steps, new Set())).toBe(0);
  });
  it("mở tới checkpoint chưa đúng đầu tiên", () => {
    expect(resumeStep(steps, new Set(["Q1"]))).toBe(4);
  });
  it("checkpoint đúng hết thì mở phần kiểm tra cuối bài", () => {
    expect(resumeStep(steps, new Set(["Q1", "Q2"]))).toBe(5);
  });
});

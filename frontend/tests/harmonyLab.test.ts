// phuc-music Bước 4: logic lưới của Harmony Lab (không cần Tone.js hay trình duyệt).
// Lịch phát cũ (buildSchedule) đã thay bằng bộ phối khí backend + humanize, test ở band.test.ts (02/11).
import { describe, expect, it } from "vitest";
import type { ComposeOptions } from "../src/api";
import { remapToKey, resizeBars, starterProgression } from "../src/components/compose/harmonyLab";

// Bảng hợp âm giống dữ liệu /composition/options trả về cho C và G (Music Engine dựng).
const options = {
  keys: [
    { key: "C", chords: ["C", "Dm", "Em", "F", "G", "Am", "Bdim"].map((symbol) => ({ symbol, numeral: "" })) },
    { key: "G", chords: ["G", "Am", "Bm", "C", "D", "Em", "F#dim"].map((symbol) => ({ symbol, numeral: "" })) },
  ],
} as unknown as ComposeOptions;

describe("lưới hợp âm", () => {
  it("vòng mẫu I–vi–IV–V lấy từ danh sách hợp âm của giọng, lặp khi lưới dài hơn", () => {
    expect(starterProgression(options, "C", 6)).toEqual(["C", "Am", "F", "G", "C", "Am"]);
  });
  it("đổi giọng giữ bậc, hợp âm ngoài giọng giữ nguyên", () => {
    expect(remapToKey(["C", "Dm", "Ab", null], options, "C", "G")).toEqual(["G", "Am", "Ab", null]);
  });
  it("đổi số ô: thêm ô trống hoặc cắt ô cuối", () => {
    expect(resizeBars(["C", "F"], 4)).toEqual(["C", "F", null, null]);
    expect(resizeBars(["C", "F", "G"], 2)).toEqual(["C", "F"]);
  });
});

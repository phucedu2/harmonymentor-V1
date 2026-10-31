// phuc-music Bước 4: lịch phát và logic lưới của Harmony Lab (không cần Tone.js hay trình duyệt).
import { describe, expect, it } from "vitest";
import type { ComposeOptions, ComposeStyle, ComposeVoicing } from "../src/api";
import { beatToTransport, buildSchedule } from "../src/audio/trackSchedule";
import { remapToKey, resizeBars, starterProgression } from "../src/components/compose/harmonyLab";

const p = (name: string, midi: number) => ({ name, midi });
const C: ComposeVoicing = { symbol: "C", notes: ["C", "E", "G"], pitches: [p("C4", 60), p("E4", 64), p("G4", 67)], bass: { root: p("C2", 36), fifth: p("G2", 43) } };
const style: ComposeStyle = {
  id: "pop", label: "Pop", description: "", default_bpm: 100, swing: 0,
  drums: [{ drum: "kick", beat: 0, velocity: 110 }, { drum: "snare", beat: 1, velocity: 95 }],
  bass: [{ beat: 0, beats: 2, tone: "root" }, { beat: 2, beats: 2, tone: "fifth" }],
  chords: [{ beat: 0, beats: 4 }],
};
// Bảng hợp âm giống dữ liệu /composition/options trả về cho C và G (Music Engine dựng).
const options = {
  keys: [
    { key: "C", chords: ["C", "Dm", "Em", "F", "G", "Am", "Bdim"].map((symbol) => ({ symbol, numeral: "" })) },
    { key: "G", chords: ["G", "Am", "Bm", "C", "D", "Em", "F#dim"].map((symbol) => ({ symbol, numeral: "" })) },
  ],
} as unknown as ComposeOptions;

describe("lịch phát backing track", () => {
  it("trống chạy cả ô trống, hợp âm và bass chỉ ở ô có hợp âm, dùng số MIDI từ Engine", () => {
    const events = buildSchedule([C, null], style);
    expect(events.filter((e) => e.channel === "drums").map((e) => e.beat)).toEqual([0, 1, 4, 5]);
    expect(events.filter((e) => e.channel === "chords")).toEqual([{ channel: "chords", beat: 0, beats: 4, midi: [60, 64, 67] }]);
    expect(events.filter((e) => e.channel === "bass").map((e) => e.midi)).toEqual([[36], [43]]);
  });

  it("đổi phách sang thời gian nhạc ô:phách:móc kép", () => {
    expect(beatToTransport(0)).toBe("0:0:0");
    expect(beatToTransport(5.5)).toBe("1:1:2");
    expect(beatToTransport(16)).toBe("4:0:0");
  });
});

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

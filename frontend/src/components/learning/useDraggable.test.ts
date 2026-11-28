import { afterEach, describe, expect, it, vi } from "vitest";
import { clampPos } from "./useDraggable";

// FE-023: nút/khung AI Tutor kéo đi đâu cũng phải còn nằm trong màn hình (cả khi xoay máy, thu nhỏ cửa sổ).
describe("clampPos", () => {
  afterEach(() => vi.unstubAllGlobals());
  const screen = (w: number, h: number) => vi.stubGlobal("window", { innerWidth: w, innerHeight: h });

  it("giữ nguyên vị trí nằm trong màn hình", () => {
    screen(1440, 900);
    expect(clampPos({ x: 300, y: 200 }, 56, 56)).toEqual({ x: 300, y: 200 });
  });

  it("kéo lố ra ngoài thì kẹp lại, chừa lề 8 px", () => {
    screen(390, 844);
    expect(clampPos({ x: -50, y: -20 }, 48, 48)).toEqual({ x: 8, y: 8 });
    expect(clampPos({ x: 999, y: 999 }, 48, 48)).toEqual({ x: 390 - 48 - 8, y: 844 - 48 - 8 });
  });

  it("khung to hơn màn hình thì dính lề trên-trái, không ra số âm", () => {
    screen(320, 300);
    expect(clampPos({ x: 100, y: 100 }, 380, 500)).toEqual({ x: 8, y: 8 });
  });
});

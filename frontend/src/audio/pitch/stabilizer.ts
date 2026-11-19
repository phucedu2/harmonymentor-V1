// ADR-031: biến dòng tần số (mỗi khung ~40 ms) thành sự kiện "đã chơi một nốt".
// Vì sao cần: lúc mới gảy đàn cao độ dao động, và một nốt ngân dài không được tính nhiều lần.
// Chỉ nhóm khung theo nửa cung để biết "cùng một nốt"; tên nốt vẫn do Music Engine đặt.

export type StableNote = { hz: number; frames: number };

/** Số thứ tự nửa cung gần nhất so với A4 = 440 Hz (chỉ để so hai khung có cùng nốt không). */
export function semitoneBucket(hz: number): number {
  return Math.round(12 * Math.log2(hz / 440));
}

export class NoteStabilizer {
  private bucket: number | null = null;
  private run: number[] = [];
  private emitted = false;
  private silentFrames = 0;

  /** holdFrames: số khung liên tiếp cùng nốt mới tính (5 × 40 ms = 200 ms). releaseFrames: số khung im để nhận lại cùng nốt. */
  constructor(private holdFrames = 5, private releaseFrames = 3) {}

  reset() { this.bucket = null; this.run = []; this.emitted = false; this.silentFrames = 0; }

  /** Đưa vào tần số của một khung (null = im lặng/không rõ). Trả nốt vừa ổn định, hoặc null. */
  push(hz: number | null): StableNote | null {
    if (hz === null) {
      this.silentFrames += 1;
      if (this.silentFrames >= this.releaseFrames) { this.bucket = null; this.run = []; this.emitted = false; }
      return null;
    }
    this.silentFrames = 0;
    const b = semitoneBucket(hz);
    if (b !== this.bucket) { this.bucket = b; this.run = []; this.emitted = false; }
    this.run.push(hz);
    if (this.emitted || this.run.length < this.holdFrames) return null;
    this.emitted = true;
    // Trung vị bỏ được khung lệch lúc vừa gảy.
    const sorted = [...this.run].sort((x, y) => x - y);
    return { hz: sorted[Math.floor(sorted.length / 2)], frames: this.run.length };
  }
}

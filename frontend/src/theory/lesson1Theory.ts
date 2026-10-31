// Phần khám phá Bài 1: quãng và hợp âm ba nốt trên 12 nốt gốc.
// Không tự tính nhạc lý ở đây (nguyên tắc bất biến số 1): tên nốt, quãng tám ASPN và MIDI đều lấy từ
// GET /api/v1/music/lesson1/{root} của Music Engine. File này chỉ giữ nhãn hiển thị và bộ nhớ đệm.
import { useEffect, useState } from "react";
import { api, type Lesson1Theory, type Lesson1Triad, type Lesson1Interval } from "../api";

export type IntervalCode = "M3" | "m3" | "P5" | "d5" | "A5";
export type TriadQuality = "major" | "minor" | "diminished" | "augmented";

// Nhãn tiếng Việt chỉ để đọc; số nửa cung, nốt, công thức đến từ Engine.
export const INTERVAL_LABELS: Record<IntervalCode, string> = {
  M3: "Quãng 3 trưởng",
  m3: "Quãng 3 thứ",
  P5: "Quãng 5 đúng",
  d5: "Quãng 5 giảm",
  A5: "Quãng 5 tăng",
};

export const TRIAD_LABELS: Record<TriadQuality, string> = {
  major: "Major · Trưởng",
  minor: "Minor · Thứ",
  diminished: "Diminished · Giảm",
  augmented: "Augmented · Tăng",
};

export const LESSON1_INTERVAL_CODES: IntervalCode[] = ["M3", "m3", "P5", "d5"];
export const LESSON1_TRIAD_QUALITIES: TriadQuality[] = ["major", "minor", "diminished", "augmented"];

// Mỗi nốt gốc chỉ hỏi máy chủ một lần trong phiên; 17 cách viết nốt gốc nên bộ đệm rất nhỏ.
const cache = new Map<string, Promise<Lesson1Theory>>();

export function fetchLesson1Theory(root: string): Promise<Lesson1Theory> {
  let pending = cache.get(root);
  if (!pending) {
    pending = api.lesson1Theory(root);
    // Lỗi mạng không được nằm lại trong bộ đệm, để lần sau thử lại.
    pending.catch(() => cache.delete(root));
    cache.set(root, pending);
  }
  return pending;
}

export function clearLesson1TheoryCache() {
  cache.clear();
}

export type Lesson1TheoryState =
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: Lesson1Theory; error: null }
  | { status: "error"; data: null; error: string };

export function useLesson1Theory(root: string): Lesson1TheoryState {
  const [state, setState] = useState<Lesson1TheoryState>({ status: "loading", data: null, error: null });
  useEffect(() => {
    let alive = true;
    setState({ status: "loading", data: null, error: null });
    fetchLesson1Theory(root)
      .then((data) => { if (alive) setState({ status: "ready", data, error: null }); })
      .catch((err: { message?: string }) => {
        if (alive) setState({ status: "error", data: null, error: err?.message ?? "Không tải được dữ liệu nhạc lý" });
      });
    return () => { alive = false; };
  }, [root]);
  return state;
}

export function intervalOf(data: Lesson1Theory, code: IntervalCode): Lesson1Interval {
  const found = data.intervals.find((item) => item.code === code);
  if (!found) throw new Error(`Máy chủ không trả quãng ${code}`);
  return found;
}

export function triadOf(data: Lesson1Theory, quality: TriadQuality): Lesson1Triad {
  const found = data.triads.find((item) => item.quality === quality);
  if (!found) throw new Error(`Máy chủ không trả hợp âm ${quality}`);
  return found;
}

// Tên ASPN để vẽ khuông và phát âm thanh, ví dụ ["G#4", "B#4", "D#5"].
export const pitchNames = (item: { pitches: { name: string }[] }) => item.pitches.map((pitch) => pitch.name);

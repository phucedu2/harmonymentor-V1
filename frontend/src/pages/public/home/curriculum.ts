// Gom dữ liệu bài học từ API thành các con số dùng cho trang chủ.
// FR-VIS-02: không viết cứng danh sách bài; mọi số liệu ở đây đều suy ra từ GET /lessons.
import type { LessonSummary } from "../../../api";

export type Module = {
  /** Tên chặng, lấy nguyên từ trường `track` của API. */
  track: string;
  lessons: LessonSummary[];
  lessonCount: number;
  blockCount: number;
  exerciseCount: number;
  reviewItemCount: number;
  /** Thời lượng ước tính, phút (xem uocLuongPhut). */
  minutes: number;
  /** Câu "Xong chặng này bạn sẽ…", ghép từ mục tiêu thật của các bài trong chặng. */
  outcome: string;
};

/**
 * Thời lượng ước tính của một chặng: 1,5 phút cho mỗi phần lý thuyết + 1 phút cho mỗi câu hỏi,
 * làm tròn lên bội số của 5 phút. Đây là ƯỚC LƯỢNG để người đọc hình dung, không phải số đo thật
 * từ người học; công thức ghi ở đây để nhóm sửa một chỗ.
 */
export const PHUT_MOI_PHAN_LY_THUYET = 1.5;
export const PHUT_MOI_CAU_HOI = 1;
export const LAM_TRON_PHUT = 5;

export function uocLuongPhut(blockCount: number, exerciseCount: number): number {
  const raw = blockCount * PHUT_MOI_PHAN_LY_THUYET + exerciseCount * PHUT_MOI_CAU_HOI;
  return Math.max(LAM_TRON_PHUT, Math.round(raw / LAM_TRON_PHUT) * LAM_TRON_PHUT);
}

/** Bỏ dấu chấm cuối và viết thường chữ đầu, để ghép mục tiêu vào giữa một câu. */
function noiTiep(objective: string): string {
  const s = objective.trim().replace(/\.$/, "");
  return s.charAt(0).toLocaleLowerCase("vi") + s.slice(1);
}

/** Ghép mục tiêu đầu tiên của từng bài trong chặng thành một câu (4A: không viết tay). */
function ghepMucTieu(lessons: LessonSummary[]): string {
  const parts = lessons.map((l) => l.objectives[0]).filter(Boolean).map(noiTiep);
  if (parts.length === 0) return "";
  if (parts.length === 1) return parts[0] + ".";
  return parts.slice(0, -1).join("; ") + " và " + parts[parts.length - 1] + ".";
}

/**
 * Nhóm bài theo `track`, giữ đúng thứ tự `order` của API.
 * Bài do AI soạn (`ai_generated`) không hiện ở trang chủ.
 */
export function buildModules(lessons: LessonSummary[]): Module[] {
  const visible = [...lessons].filter((l) => !l.ai_generated).sort((a, b) => a.order - b.order);
  const order: string[] = [];
  const byTrack = new Map<string, LessonSummary[]>();
  for (const lesson of visible) {
    if (!byTrack.has(lesson.track)) {
      byTrack.set(lesson.track, []);
      order.push(lesson.track);
    }
    byTrack.get(lesson.track)!.push(lesson);
  }
  return order.map((track) => {
    const items = byTrack.get(track)!;
    const sum = (pick: (l: LessonSummary) => number) => items.reduce((t, l) => t + pick(l), 0);
    const blockCount = sum((l) => l.block_count);
    const exerciseCount = sum((l) => l.exercise_count);
    return {
      track,
      lessons: items,
      lessonCount: items.length,
      blockCount,
      exerciseCount,
      reviewItemCount: sum((l) => l.review_item_count),
      minutes: uocLuongPhut(blockCount, exerciseCount),
      outcome: ghepMucTieu(items),
    };
  });
}

/** Bài chưa đủ nội dung để học: không có phần lý thuyết hoặc không có câu hỏi nào. */
export function dangSoan(lesson: LessonSummary): boolean {
  return lesson.block_count === 0 || lesson.exercise_count === 0;
}

/** Tên tiếng Việt của từng dạng câu hỏi (trường `kind` của API). */
export const TEN_DANG_CAU: Record<string, string> = {
  mcq: "Trắc nghiệm",
  build: "Dựng trên piano",
  active_recall: "Nhớ lại",
  context: "Theo ngữ cảnh",
  applied: "Áp dụng",
  open_rubric: "Tự luận",
};

/** Ký hiệu ngắn hiện trong huy hiệu dạng câu hỏi. */
export const KY_HIEU_DANG_CAU: Record<string, string> = {
  mcq: "ABC",
  build: "♪",
  active_recall: "↺",
  context: "§",
  applied: "→",
  open_rubric: "✎",
};

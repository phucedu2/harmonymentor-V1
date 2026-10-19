// Backend contracts. Music theory remains deterministic on the server; frontend is presentation/input only.
import { http } from "./lib/http";

export type EngineError = { code: string; message: string; details?: Record<string, unknown> };
// ApiRequestError (lib/http.ts) thỏa kiểu này, nên các trang cũ đọc lỗi như trước.
export type ApiError = { code: string; message?: string };

export type GradeResult = {
  correct: boolean;
  expected: string | string[];
  errors: { code: string; message_vi: string; proposed: boolean }[];
  primary_error: string | null;
  message_vi: string;
  engine_version: string;
  convention_id: string | null;
  convention_verified?: boolean;
};

export type LessonSummary = {
  id: string;
  order: number;
  track: string;
  title: string;
  status: string;
  objectives: string[];
  block_count: number;
  exercise_count: number;
  review_item_count: number;
};

export type LessonBlock = { id: string; position: number; block_type: string; payload: Record<string, unknown> };
export type LessonExercise = {
  id: string;
  version_id: string;
  version: number;
  position: number;
  kind: string;
  prompt: string;
  options?: string[] | null;
  grading_strategy: string;
  skill_id: string;
};
export type ReviewItem = { id: string; mode: string; front: string; back: string; skill_id: string };
export type SourceRef = { source_id: string; title: string; author?: string | null; locator: string; note?: string | null; url?: string | null };
export type LessonDetail = LessonSummary & {
  blocks: LessonBlock[];
  exercises: LessonExercise[];
  review_items: ReviewItem[];
  sources: SourceRef[];
};

export type ChordInspection = {
  symbol: string;
  quality: string;
  formula: string[];
  notes: string[];
  bass?: string | null;
  inversion: number;
  verified: boolean;
  context?: { key: string; roman?: string | null; function?: string | null } | null;
};

export type LessonLearningProgress = {
  lesson_id: string;
  order: number;
  title: string;
  track: string;
  status: string;
  started_at?: string | null;
  completed_at?: string | null;
  exercise_count: number;
  attempted_exercises: number;
  correct_exercises: number;
  attempt_count: number;
  correct_attempt_count: number;
  practice_progress_percent: number;
  attempted_exercise_ids: string[];
  correct_exercise_ids: string[];
};

export type LearningOverview = {
  user_id: string;
  total_lessons: number;
  started_lessons: number;
  completed_lessons: number;
  due_reviews: number;
  upcoming_reviews: number;
  lessons: LessonLearningProgress[];
};

export type StartLessonResult = {
  lesson_id: string;
  user_id: string;
  status: string;
  started_at: string;
  completed_at?: string | null;
};

export type AttemptResult = {
  attempt_id: string;
  user_id: string;
  exercise_version_id: string;
  correct: boolean;
  score: number;
  primary_error?: string | null;
  feedback?: string | null;
  errors: { code: string; detail: Record<string, unknown> }[];
};

export type CompleteLessonResult = {
  lesson_id: string;
  user_id: string;
  status: string;
  completed_at: string;
  activated_review_items: number;
  first_review_due_at?: string | null;
};

export type ReviewState = {
  review_item_id: string;
  lesson_id: string;
  front: string;
  mode: string;
  skill_id: string;
  stage: number;
  interval_days: number;
  due_at: string;
  status: string;
};

export type ReviewAnswerResult = {
  review_attempt_id: string;
  review_item_id: string;
  correct: boolean;
  rating_applied: string;
  next_stage: number;
  interval_days: number;
  next_due_at: string;
  feedback?: string | null;
};

// Mọi request đi qua lib/http.ts để có access token và lỗi chuẩn SRS 7.4.
const engineCall = <T,>(path: string, init?: RequestInit) => http<T>("/engine" + path, init, { auth: false });
const apiCall = <T,>(path: string, init?: RequestInit) => http<T>(path, init);
const enginePost = <T,>(path: string, data: unknown) => engineCall<T>(path, { method: "POST", body: JSON.stringify(data) });
const apiPost = <T,>(path: string, data: unknown) => apiCall<T>(path, { method: "POST", body: JSON.stringify(data) });

export const api = {
  // Legacy Practice routes retained during migration.
  transpose: (note: string, interval: string) =>
    engineCall<{ note: string }>(`/transpose?note=${encodeURIComponent(note)}&interval=${encodeURIComponent(interval)}`),
  diatonic: (tonic: string, sevenths: boolean) =>
    engineCall<{ degree: number; numeral: string; chord: string; convention_verified: boolean }[]>(
      `/diatonic/${encodeURIComponent(tonic)}?sevenths=${sevenths}`,
    ),
  gradeBuildChord: (symbol: string, answer: string[], grading_mode = "strict_spelling") =>
    enginePost<GradeResult>("/grade/build-chord", { symbol, answer, grading_mode }),
  gradeIdentifyInterval: (lower: string, upper: string, answer: string) =>
    enginePost<GradeResult>("/grade/identify-interval", { lower, upper, answer }),
  gradeBuildScale: (tonic: string, scale_type: string, answer: string[]) =>
    enginePost<GradeResult>("/grade/build-scale", { tonic, scale_type, answer }),
  gradeRoman: (key: string, chord: string, answer: string) =>
    enginePost<GradeResult>("/grade/roman-numeral", { key, chord, answer }),

  // Phase 0.4B source-grounded learning contract.
  listLessons: () => apiCall<LessonSummary[]>("/lessons"),
  getLesson: (lessonId: string) => apiCall<LessonDetail>(`/lessons/${encodeURIComponent(lessonId)}`),
  // user_id không còn gửi từ client (N3): backend lấy từ token (ADR-004).
  startLesson: (lessonId: string) =>
    apiPost<StartLessonResult>(`/lessons/${encodeURIComponent(lessonId)}/start`, {}),
  learningOverview: () => apiCall<LearningOverview>("/learning/overview"),
  inspectChord: (symbol: string, key?: string) =>
    apiCall<ChordInspection>(`/music/chords/inspect?symbol=${encodeURIComponent(symbol)}${key ? `&key=${encodeURIComponent(key)}` : ""}`),
  submitAttempt: (exerciseVersionId: string, answer: unknown) =>
    apiPost<AttemptResult>("/attempts", { exercise_version_id: exerciseVersionId, answer }),
  completeLesson: (lessonId: string) =>
    apiPost<CompleteLessonResult>(`/lessons/${encodeURIComponent(lessonId)}/complete`, {}),
  dueReviews: (includeFuture = false) =>
    apiCall<ReviewState[]>(`/review/due?include_future=${includeFuture}`),
  answerReview: (reviewItemId: string, answer: unknown, rating = "auto") =>
    apiPost<ReviewAnswerResult>(`/review/${encodeURIComponent(reviewItemId)}/answer`, { answer, rating }),
};

// Tách chuỗi người học gõ ("G B D F#" hoặc "G, B, D, F#") thành danh sách nốt.
export const splitNotes = (text: string) => text.split(/[\s,;]+/).filter(Boolean);

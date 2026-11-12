// Backend contracts. Music theory remains deterministic on the server; frontend is presentation/input only.
import { http } from "./lib/http";
import type { Arrangement, SongForm } from "./audio/band/types";

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
  /** GĐ5: liên kết học thêm ngoài app (sách mở miễn phí); có thể thiếu khi backend cũ. */
  external_resources?: ExternalResource[];
};
export type ExternalResource = { title: string; source: string; url: string; language: string; free: boolean; why_vi: string; draft?: boolean };

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
  // Backend chỉ gửi lời giải khi đã đúng hoặc sau 2 lần sai.
  explanation?: string | null;
  wrong_attempts: number;
};

export type InputMethod = "text" | "choice" | "piano";

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
  leitner_box: number;
  self_check: boolean;
  back?: string | null;
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
  leitner_box: number;
};

// Phần khám phá Bài 1, sinh bởi Music Engine (GET /music/lesson1/{root}).
export type PitchWithOctave = { name: string; midi: number };
export type Lesson1Interval = { code: string; semitones: number; upper: string; pitches: PitchWithOctave[] };
export type Lesson1Triad = {
  quality: string; symbol: string; formula: string[]; interval_formula: string[]; notes: string[]; pitches: PitchWithOctave[];
};
export type Lesson1Theory = {
  root: string; root_octave: number; letter_frame: string[]; intervals: Lesson1Interval[]; triads: Lesson1Triad[];
};

// Luyện tập (phuc-music Bước 2): máy chủ chấm bằng Music Engine và ghi lịch sử theo token.
export type PracticeKind = "chord" | "interval" | "scale" | "roman";
export type PracticeLevel = "de" | "vua" | "kho";
export type PracticeAttemptResult = {
  id: string; kind: PracticeKind; correct: boolean; expected: string | string[]; message_vi: string;
  primary_error: string | null; errors: { code: string; message_vi: string }[]; convention_verified: boolean | null;
};
export type PracticeHistoryItem = {
  id: string; kind: PracticeKind; level: PracticeLevel | null; question: Record<string, string>;
  answer: string | string[]; correct: boolean; primary_error: string | null; created_at: string;
};
export type PracticeHistory = { items: PracticeHistoryItem[]; stats: { kind: PracticeKind; attempts: number; correct: number }[] };

// Harmony Lab (phuc-music Bước 4, FR-17/18): hợp âm, gợi ý và phân tích do backend + Music Engine trả về.
// Phong cách nền (ADR-012 đề xuất): mẫu nhịp nằm ở backend (style pack), giao diện chỉ cần tên, mô tả, tempo.
export type ComposeStyle = {
  id: string; label: string; description: string; default_bpm: number; bpm_range: [number, number]; swing: number;
  instruments: { keys: string; bass: string; guitar: string };
};
export type ComposeOptions = {
  keys: { key: string; chords: { symbol: string; numeral: string }[] }[];
  styles: ComposeStyle[];
  levels: { level: number; label: string }[];
  tempo: { min: number; max: number };
  bars: { min: number; max: number };
  song?: { version: number; max_bars: number; lengths: string[]; section_types: { id: string; label: string }[];
    transitions: string[]; endings: string[] };
};
export type ComposeCandidate = {
  rule: string; rule_label: string; level: number; level_label: string; symbol: string; label: string;
  reason_vi: string; notes: string[];
};
export type ComposeAnalysis = {
  key: string; level: number; level_label: string; summary_vi: string;
  bars: { bar: number; symbol: string | null; level: number | null; rule: string | null; label: string | null; reason_vi: string | null }[];
  warnings: { code: string; bar: number; message_vi: string }[];
};
export type ComposeVoicing = {
  symbol: string; notes: string[]; pitches: PitchWithOctave[]; bass: { root: PitchWithOctave; fifth: PitchWithOctave };
};
export type ComposeMix = Partial<Record<"chords" | "bass" | "guitar" | "drums" | "hook", { volume: number; muted: boolean }>>;
export type ComposeProjectInput = {
  name: string; key: string; tempo_bpm: number; bars: number; style: string; chords: (string | null)[];
  seed: number; energy: number; mix: ComposeMix | null;
  /** Có = dự án ở chế độ Bài hát (ADR-013 đề xuất); null = Vòng lặp như cũ. */
  form?: SongForm | null;
};
export type ComposeProject = ComposeProjectInput & {
  id: string; time_signature: string; updated_at: string; arrangement_version: number; arrangement_outdated: boolean;
};
export type ComposeProjectSummary = { id: string; name: string; key: string; bars: number; style: string; updated_at: string; mode?: "song" | "loop" };

// Mọi request đi qua lib/http.ts để có access token và lỗi chuẩn SRS 7.4.
const engineCall = <T,>(path: string, init?: RequestInit) => http<T>("/engine" + path, init, { auth: false });
const apiCall = <T,>(path: string, init?: RequestInit) => http<T>(path, init);
const enginePost = <T,>(path: string, data: unknown) => engineCall<T>(path, { method: "POST", body: JSON.stringify(data) });
const apiPost = <T,>(path: string, data: unknown) => apiCall<T>(path, { method: "POST", body: JSON.stringify(data) });

// Pipeline AI GĐ1: mastery và bài kiểm tra đầu vào (UC-06).
export type MasteryLevel = "not_assessed" | "learning" | "weak" | "ready" | "mastered";
export type SkillMastery = {
  skill_id: string; name: string; srs_code: string; group_code: string;
  assessed: boolean; score: number | null; attempts_count: number; level: MasteryLevel;
  ready_threshold: number; mastery_threshold: number;
};
export type PlacementQuestion = {
  exercise_id: string; exercise_version_id: string; skill_id: string; kind: string; prompt: string; options?: string[] | null;
};
export type PlacementStatus = "not_started" | "completed" | "skipped";
export type Placement = { status: PlacementStatus; questions: PlacementQuestion[] };
// Pipeline AI GĐ2: gợi ý bài học (04 mục 6.5) và mục tiêu học.
export type RecReasonCode = "content" | "mastery" | "due" | "cf" | "foundation" | "route";
export type RecLesson = {
  lesson_id: string; order: number; title: string; score: number;
  components: { content: number; mastery: number; due: number; cf: number | null };
  reason_code: RecReasonCode; reason: string; badge: string; skills: string[]; label?: string | null;
};
export type Recommendations = {
  generated_at: string; log_id: string; mode: "full" | "cold_start" | "fallback"; weights_mode: "full" | "cold";
  cf_source: "real" | "synthetic" | "none"; fallback_reason: "no_assessed_dims" | "no_valid_neighbors" | "cf_disabled" | null;
  neighbors_count: number; content_source: "embedding" | "none"; draft_descriptions: boolean;
  few_eligible: boolean;
  route_fallback?: boolean;
  continue: { lesson_id: string; order: number; title: string; status: "started" }[];
  next: RecLesson[]; review: RecLesson[];
};
export type Goal = { goal_text: string | null; embedded: boolean; embedding_model: string | null };
export type Quiz = { skill_id: string; requested: number; available: number; questions: (PlacementQuestion & { lesson_id: string })[] };
export type PlacementSubmitResult = { status: "completed"; results: { skill_id: string; correct: boolean; score: number }[] };

// Pipeline AI GĐ3: AI Tutor (04 mục 3.3, Bảng 13). Nhãn "đã kiểm" do máy chủ quyết, giao diện chỉ hiển thị.
export type ChatIntent = "concept" | "explain_error" | "quiz" | "study_advice" | "composition" | "out_of_scope"
  | "greeting" | "help";
// Bộ định tuyến 4 luồng (ADR-017): A từ bài học, B ngoài bài học (Music Engine hoặc "không biết"), C ngoài phạm vi,
// D hướng dẫn sử dụng, G chào hỏi. Nhãn nguồn do máy chủ đặt.
export type ChatFlow = "A" | "B" | "C" | "D" | "G";
export type ChatCitation = { lesson_id: string; block_id: string; title: string; lesson_title: string };
export type EngineClaim = {
  tool: string; args: Record<string, string>; claimed: string; engine: string | null;
  status: "verified" | "contradicted" | "unsupported"; origin: string;
};
export type ChatReply = {
  message_id: number; session_id: string; reply: string; citations: ChatCitation[]; engine_claims: EngineClaim[];
  verified: boolean; verified_label: string | null; intent: ChatIntent; hint_level: number;
  status: "ok" | "failed" | "fallback"; suggested_actions: string[]; fallback_reason: string | null;
  retrieval_method: string | null; quota_remaining_today: number; attempt_id?: string | null; next_hint_level?: number | null;
  flow?: ChatFlow | null; source_label?: string | null;
  suggested_lesson?: { lesson_id: string; title: string } | null; help_page?: { path: string; title: string } | null;
};
export type ChatContext = { page?: string; lesson_id?: string; block_id?: string };

// --- Quản trị (ADR-023) ---
export type AdminEngineReport = { checked: number; verified: number; unsupported: number; contradicted: EngineClaim[] };
export type AdminLessonRow = { id: string; order: number; track: string; title: string; status: string; hidden: boolean;
  block_count: number; exercise_count: number; edited_blocks: number; draft_blocks: number };
export type AdminBlock = { id: string; position: number; block_type: string; payload: Record<string, unknown>;
  base_payload: Record<string, unknown>; edited: boolean; draft_revision_id: string | null; engine: AdminEngineReport };
export type AdminLessonDetail = { lesson: AdminLessonRow; objectives: string[]; blocks: AdminBlock[];
  exercises: { id: string; version: number; skill_id: string; kind: string; prompt: string; status: string }[] };
export type AdminRevision = { id: string; status: string; note: string | null; created_by: string | null; created_at: string;
  published_at: string | null; payload: Record<string, unknown> };
export type AdminUser = { id: string; email: string; display_name: string | null; role: string; is_active: boolean; created_at: string;
  lessons_completed: number; attempts: number; last_activity: string | null };
export type AdminStats = {
  days: number;
  totals: { learners: number; new_learners: number; active_last_7_days: number; attempts: number; correct_rate: number | null;
    lessons_completed: number; reviews: number; cards_due_now: number };
  timeline: { date: string; attempts: number; correct: number; reviews: number }[];
  funnel: { lesson_id: string; title: string; status: string; started: number; completed: number; completion_rate: number | null }[];
  skills: { skill_id: string; name: string; first_try_total: number; first_try_correct_rate: number }[];
  hardest_exercises: { exercise_id: string; first_try_total: number; first_try_correct_rate: number }[];
  mastery: { label: string; count: number }[];
};
export type AdminAudit = { id: number; actor_id: string | null; action: string; target_type: string; target_id: string; created_at: string };

export const api = {
  adminLessons: () => apiCall<AdminLessonRow[]>("/admin/lessons"),
  adminLesson: (id: string) => apiCall<AdminLessonDetail>(`/admin/lessons/${encodeURIComponent(id)}`),
  adminSaveDraft: (lessonId: string, blockId: string, payload: Record<string, unknown>, note?: string) =>
    apiCall<{ revision_id: string; engine: AdminEngineReport }>(`/admin/lessons/${encodeURIComponent(lessonId)}/blocks/${encodeURIComponent(blockId)}`,
      { method: "PUT", body: JSON.stringify({ payload, note: note || null }) }),
  adminPublish: (revisionId: string, acknowledge: boolean) =>
    apiPost<{ revision_id: string; engine: AdminEngineReport }>(`/admin/revisions/${encodeURIComponent(revisionId)}/publish`, { acknowledge_engine_flags: acknowledge }),
  adminHistory: (lessonId: string, blockId: string) =>
    apiCall<AdminRevision[]>(`/admin/lessons/${encodeURIComponent(lessonId)}/blocks/${encodeURIComponent(blockId)}/history`),
  adminRestore: (lessonId: string, blockId: string, revisionId: string | null) =>
    apiPost<{ revision_id: string }>(`/admin/lessons/${encodeURIComponent(lessonId)}/blocks/${encodeURIComponent(blockId)}/restore`, { revision_id: revisionId }),
  adminVisibility: (lessonId: string, hidden: boolean) =>
    apiPost<{ id: string; hidden: boolean }>(`/admin/lessons/${encodeURIComponent(lessonId)}/visibility`, { hidden }),
  adminUsers: (q = "") => apiCall<{ total: number; items: AdminUser[] }>(`/admin/users?q=${encodeURIComponent(q)}`),
  adminSetActive: (id: string, isActive: boolean) =>
    apiCall<{ id: string; is_active: boolean }>(`/admin/users/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify({ is_active: isActive }) }),
  adminStats: (days = 30) => apiCall<AdminStats>(`/admin/stats?days=${days}`),
  adminAudit: () => apiCall<AdminAudit[]>("/admin/audit?limit=30"),
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

  practiceAttempt: (kind: PracticeKind, level: PracticeLevel, question: Record<string, string>, answer: string | string[],
    input: "text" | "piano" = "text") =>
    apiPost<PracticeAttemptResult>("/practice/attempts", { kind, level, question, answer, input }),
  practiceHistory: (limit = 20) => apiCall<PracticeHistory>(`/practice/history?limit=${limit}`),

  composeOptions: () => apiCall<ComposeOptions>("/composition/options"),
  composeSuggest: (key: string, chords: (string | null)[], index: number, max_level = 3) =>
    apiPost<{ candidates: ComposeCandidate[]; ranked_by: string; ai_used: boolean }>("/composition/suggestions", { key, chords, index, max_level }),
  composeVoicings: (chords: string[]) => apiPost<Record<string, ComposeVoicing>>("/composition/voicings", { chords }),
  composeAnalyze: (key: string, chords: (string | null)[]) => apiPost<ComposeAnalysis>("/composition/analyze", { key, chords }),
  composeArrangement: (body: { key: string; style: string; chords: (string | null)[]; seed: number; energy: number; bpm: number }) =>
    apiPost<Arrangement>("/composition/arrangement", body),
  composeSong: (body: { key: string; style: string; seed: number; energy: number; bpm: number; form: SongForm }) =>
    apiPost<Arrangement>("/composition/song", body),
  listProjects: () => apiCall<ComposeProjectSummary[]>("/projects"),
  getProject: (id: string) => apiCall<ComposeProject>(`/projects/${encodeURIComponent(id)}`),
  createProject: (data: ComposeProjectInput) => apiPost<ComposeProject>("/projects", data),
  updateProject: (id: string, data: ComposeProjectInput) =>
    apiCall<ComposeProject>(`/projects/${encodeURIComponent(id)}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteProject: (id: string) => apiCall<void>(`/projects/${encodeURIComponent(id)}`, { method: "DELETE" }),

  // Phase 0.4B source-grounded learning contract.
  listLessons: () => apiCall<LessonSummary[]>("/lessons"),
  getLesson: (lessonId: string) => apiCall<LessonDetail>(`/lessons/${encodeURIComponent(lessonId)}`),
  // user_id không còn gửi từ client (N3): backend lấy từ token (ADR-004).
  startLesson: (lessonId: string) =>
    apiPost<StartLessonResult>(`/lessons/${encodeURIComponent(lessonId)}/start`, {}),
  learningOverview: () => apiCall<LearningOverview>("/learning/overview"),
  lesson1Theory: (root: string) => apiCall<Lesson1Theory>(`/music/lesson1/${encodeURIComponent(root)}`),
  inspectChord: (symbol: string, key?: string) =>
    apiCall<ChordInspection>(`/music/chords/inspect?symbol=${encodeURIComponent(symbol)}${key ? `&key=${encodeURIComponent(key)}` : ""}`),
  submitAttempt: (exerciseVersionId: string, answer: unknown, inputMethod: InputMethod = "text") =>
    apiPost<AttemptResult>("/attempts", { exercise_version_id: exerciseVersionId, answer, input_method: inputMethod }),
  completeLesson: (lessonId: string) =>
    apiPost<CompleteLessonResult>(`/lessons/${encodeURIComponent(lessonId)}/complete`, {}),
  dueReviews: (includeFuture = false) =>
    apiCall<ReviewState[]>(`/review/due?include_future=${includeFuture}`),
  myMastery: () => apiCall<{ skill_group_map_version: string; skills: SkillMastery[] }>("/me/mastery"),
  quiz: (skillId: string, n = 10) => apiCall<Quiz>(`/practice/quiz?skill_id=${encodeURIComponent(skillId)}&n=${n}`),
  placement: () => apiCall<Placement>("/placement"),
  submitPlacement: (answers: { exercise_version_id: string; answer: unknown }[], confirmRetake = false) =>
    apiPost<PlacementSubmitResult>("/placement/submit", { answers, confirm_retake: confirmRetake }),
  skipPlacement: () => apiPost<Placement>("/placement/skip", {}),
  recommend: (k = 5) => apiCall<Recommendations>(`/recommend?k=${k}`),
  clickRecommendation: (logId: string, lessonId: string) =>
    apiPost<void>(`/recommend/${encodeURIComponent(logId)}/click`, { lesson_id: lessonId }),
  myGoal: () => apiCall<Goal>("/me/goal"),
  chatMessage: (message: string, sessionId: string | null, context?: ChatContext) =>
    apiPost<ChatReply>("/chat/message", { message, session_id: sessionId, context }),
  explainAttempt: (attemptId: string, sessionId: string | null, hintLevel?: number) =>
    apiPost<ChatReply>("/chat/explain-attempt", { attempt_id: attemptId, session_id: sessionId, hint_level: hintLevel }),
  rateChatMessage: (messageId: number, stars: number) =>
    apiPost<void>(`/chat/messages/${messageId}/rating`, { stars }),
  setGoal: (goalText: string) => apiCall<Goal>("/me/goal", { method: "PUT", body: JSON.stringify({ goal_text: goalText }) }),
  answerReview: (reviewItemId: string, answer: unknown, rating = "auto") =>
    apiPost<ReviewAnswerResult>(`/review/${encodeURIComponent(reviewItemId)}/answer`, { answer, rating }),
};

// Tách chuỗi người học gõ ("G B D F#", "G, B, D, F#" hoặc "G-B-D-F#") thành danh sách nốt.
export const splitNotes = (text: string) => text.split(/[\s,;–—-]+/).filter(Boolean);

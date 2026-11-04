// Kênh sự kiện nhỏ giữa thẻ câu hỏi và khung AI Tutor: thẻ câu hỏi không cần biết khung chat nằm đâu.
export const TUTOR_EXPLAIN_EVENT = "hm:tutor-explain";

export type TutorExplainDetail = { attemptId: string; prompt: string };

export function requestExplain(detail: TutorExplainDetail) {
  window.dispatchEvent(new CustomEvent<TutorExplainDetail>(TUTOR_EXPLAIN_EVENT, { detail }));
}

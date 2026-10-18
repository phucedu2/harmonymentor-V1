/**
 * DEPRECATED after Phase 0.4B.
 *
 * The 48 quiz + 64 flashcard source-audited bank moved to:
 *   backend/app/content/curriculum_specs.py
 * and a reviewable JSON snapshot is kept at:
 *   content/curriculum/lesson_specs.json
 *
 * Runtime Learn reads the backend Content Service. Keeping a second editable curriculum copy in
 * the frontend caused provenance drift, so this file intentionally contains no lesson bank.
 */

export const REVIEW_INTERVALS_DAYS = [1, 3, 7, 14, 30] as const;

/** Cách cuộn theo cài đặt "giảm chuyển động" của hệ điều hành.
 *  Vì sao cần: scrollIntoView({behavior:"smooth"}) không tự tôn trọng prefers-reduced-motion,
 *  người dễ chóng mặt vẫn bị cuộn trượt dài nếu mỗi chỗ gọi quên kiểm tra. */
export function scrollBehavior(): ScrollBehavior {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
}

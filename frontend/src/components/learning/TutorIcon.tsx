// Biểu tượng AI Tutor (ADR-029, 12B): bong bóng hội thoại chứa hai nốt móc đơn nối vạch và một tia sáng nhỏ (AI).
// Nét đơn sắc theo currentColor nên đổi màu theo theme, đọc rõ ở 20–32 px.
export function TutorIcon({ size = 28, className = "" }: { size?: number; className?: string }) {
  return <svg viewBox="0 0 32 32" width={size} height={size} className={className} aria-hidden="true" fill="none">
    <path d="M7 4.5h18a3.5 3.5 0 0 1 3.5 3.5v11.5a3.5 3.5 0 0 1-3.5 3.5H15l-6.2 5v-5H7a3.5 3.5 0 0 1-3.5-3.5V8A3.5 3.5 0 0 1 7 4.5z"
      fill="currentColor" fillOpacity="0.16" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    <path d="M13.2 17.6V10.4l7.6-1.5v7.3" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M13.2 10.4l7.6-1.5" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    <ellipse cx="11.2" cy="17.9" rx="2.5" ry="1.8" transform="rotate(-20 11.2 17.9)" fill="currentColor" />
    <ellipse cx="18.8" cy="16.6" rx="2.5" ry="1.8" transform="rotate(-20 18.8 16.6)" fill="currentColor" />
    <path d="M25 11.2l.75 1.6 1.6.75-1.6.75-.75 1.6-.75-1.6-1.6-.75 1.6-.75z" fill="currentColor" />
  </svg>;
}

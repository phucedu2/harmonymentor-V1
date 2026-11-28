import { useEffect, useRef, useState } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import { api, type LessonSummary } from "../../../api";

/** Danh sách bài công khai; dùng chung một khóa nên các mục của trang chủ chỉ gọi API một lần. */
export function usePublicLessons() {
  return useQuery({ queryKey: ["lessons", "public"], queryFn: api.listLessons, staleTime: 5 * 60_000 });
}

/** true khi phần tử sắp vào khung nhìn; dùng để hoãn các lần gọi API không cần ngay. */
export function useNearViewport(ref: React.RefObject<Element | null>, margin = "400px") {
  const [near, setNear] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (near || !el) return;
    if (typeof IntersectionObserver === "undefined") { setNear(true); return; }
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) { setNear(true); io.disconnect(); }
    }, { rootMargin: margin });
    io.observe(el);
    return () => io.disconnect();
  }, [ref, near, margin]);
  return near;
}

/**
 * Các dạng câu hỏi của từng bài. API danh sách không có trường này nên phải mở từng bài
 * (GET /lessons/{id}, công khai); chỉ gọi khi mục chương trình sắp hiện ra, kết quả giữ trong cache.
 */
export function useLessonKinds(lessons: LessonSummary[], enabled: boolean) {
  const results = useQueries({
    queries: lessons.map((lesson) => ({
      queryKey: ["lesson", lesson.id, "public"],
      queryFn: () => api.getLesson(lesson.id),
      enabled,
      staleTime: 30 * 60_000,
    })),
  });
  const byLesson: Record<string, string[]> = {};
  lessons.forEach((lesson, i) => {
    const data = results[i]?.data;
    if (data) byLesson[lesson.id] = [...new Set(data.exercises.map((e) => e.kind))];
  });
  return byLesson;
}

/** Ref + cờ "đã gần khung nhìn", gộp lại cho gọn ở phía gọi. */
export function useLazySection<T extends Element>() {
  const ref = useRef<T>(null);
  return [ref, useNearViewport(ref)] as const;
}

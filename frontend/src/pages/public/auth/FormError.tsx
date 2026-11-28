import { useEffect, useRef } from "react";
import { Alert } from "../../../components/ui/Alert";

/** Lỗi tổng ở đầu form (B2): role="alert" (trong Alert) và nhận focus để trình đọc màn hình đọc ngay. */
export function FormError({ message }: { message: string | null }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => { if (message) ref.current?.focus(); }, [message]);
  if (!message) return null;
  return (
    <div ref={ref} tabIndex={-1} className="rounded-lg focus:outline-2 focus:outline-offset-2 focus:outline-danger">
      <Alert tone="danger">{message}</Alert>
    </div>
  );
}

import type { ReactNode } from "react";
import { ButtonLink } from "../../../components/ui/Button";

/** Màn "Kiểm tra hộp thư" dùng chung cho quên mật khẩu và đăng ký bằng email đã có (B5). */
export function CheckInbox({ email, body, children }: { email: string; body: string; children?: ReactNode }) {
  return (
    <div className="space-y-5" role="status">
      <div className="grid size-14 place-items-center rounded-2xl bg-primary-soft text-2xl text-primary-strong" aria-hidden="true">✉</div>
      <p>{body}</p>
      <p className="rounded-lg border border-line bg-surface px-4 py-3 font-medium break-all">{email}</p>
      <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
        <li>Thư có thể mất một hai phút mới tới.</li>
        <li>Không thấy thư? Hãy xem cả mục Thư rác hoặc Quảng cáo.</li>
      </ul>
      {children}
      <ButtonLink to="/dang-nhap" variant="secondary" className="w-full">Quay lại đăng nhập</ButtonLink>
    </div>
  );
}

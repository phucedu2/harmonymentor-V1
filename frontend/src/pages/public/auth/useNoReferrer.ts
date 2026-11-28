import { useEffect } from "react";

/** B6: trang có token trong địa chỉ không gửi Referer cho bất kỳ liên kết/ảnh nào (phòng thêm, token đã nằm sau #). */
export function useNoReferrer() {
  useEffect(() => {
    const meta = document.createElement("meta");
    meta.name = "referrer";
    meta.content = "no-referrer";
    document.head.appendChild(meta);
    return () => { meta.remove(); };
  }, []);
}

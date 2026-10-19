import { ApiRequestError } from "../../lib/http";

/** Đổi mã lỗi của ADR-004 thành câu tiếng Việt cho người học. */
export function authErrorMessage(error: unknown): string {
  if (!(error instanceof ApiRequestError)) return "Có lỗi không mong muốn. Bạn thử lại nhé.";
  switch (error.code) {
    case "INVALID_CREDENTIALS":
      return "Email hoặc mật khẩu chưa đúng.";
    case "LOGIN_LOCKED": {
      const minutes = error.retryAfterSeconds ? Math.ceil(error.retryAfterSeconds / 60) : 15;
      return `Bạn đã nhập sai quá 5 lần. Hãy thử lại sau khoảng ${minutes} phút.`;
    }
    case "EMAIL_TAKEN":
      return "Email này đã có tài khoản. Bạn đăng nhập nhé.";
    case "VALIDATION_ERROR":
      return "Thông tin chưa hợp lệ, bạn xem lại các ô được đánh dấu.";
    default:
      if (error.status === 404) return "Máy chủ chưa bật chức năng đăng nhập. Hãy báo nhóm backend.";
      return error.message;
  }
}

export function fieldErrors(error: unknown): Record<string, string> {
  return error instanceof ApiRequestError && error.fields ? error.fields : {};
}

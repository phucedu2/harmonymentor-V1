// FE-014: chọn sáng/tối. Mặc định luôn là "Đồng & Gỉ" sáng (yêu cầu giữ theme gốc làm mặc định),
// chỉ đổi khi người dùng bấm nút; lựa chọn lưu trong localStorage để lần sau mở lại vẫn giữ.
export type Theme = "light" | "dark";
export const THEME_KEY = "hm-theme";

export function readTheme(): Theme {
  try {
    return localStorage.getItem(THEME_KEY) === "dark" ? "dark" : "light";
  } catch {
    return "light"; // Trình duyệt chặn bộ nhớ (chế độ ẩn danh nghiêm ngặt) thì dùng mặc định.
  }
}

export function applyTheme(theme: Theme) {
  const root = document.documentElement;
  if (theme === "dark") root.dataset.theme = "dark";
  else delete root.dataset.theme;
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* không lưu được thì vẫn đổi trong phiên này */
  }
  window.dispatchEvent(new CustomEvent<Theme>("hm-theme", { detail: theme }));
}

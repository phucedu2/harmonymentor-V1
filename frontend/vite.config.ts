import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Phương án nhận diện (src/theme/brands.css): san-khau (mặc định từ 17/11/2026, nhóm chọn) | dong-gi | giay-nhac.
// index.html đọc %VITE_BRAND%; đặt mặc định ở đây để không cần file .env. Về bảng cũ: VITE_BRAND=dong-gi.
process.env.VITE_BRAND ??= "san-khau";

// Gọi /api sẽ được chuyển sang backend FastAPI (uvicorn chạy ở cổng 8000).
// Cùng origin nên cookie refresh token (ADR-004) đi kèm mà không cần CORS credentials.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // API_PROXY cho phép trỏ sang backend ở cổng khác (vd 8001) khi cổng 8000 đang bị một bản cũ chiếm.
  server: { proxy: { "/api": process.env.API_PROXY ?? "http://127.0.0.1:8000" } },
});

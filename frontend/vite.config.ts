import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Gọi /api sẽ được chuyển sang backend FastAPI (uvicorn chạy ở cổng 8000).
// Cùng origin nên cookie refresh token (ADR-004) đi kèm mà không cần CORS credentials.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});

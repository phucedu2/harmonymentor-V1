import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Gọi /api sẽ được chuyển sang backend FastAPI (uvicorn chạy ở cổng 8000).
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});

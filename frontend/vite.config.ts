import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { readFileSync } from "node:fs";

// Phiên bản hiện trong khung khu học lấy từ package.json, để không phải sửa tay ở nhiều nơi.
const pkg = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf8")) as { version: string };

// Gọi /api sẽ được chuyển sang backend FastAPI (uvicorn chạy ở cổng 8000).
// Cùng origin nên cookie refresh token (ADR-004) đi kèm mà không cần CORS credentials.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  define: { __APP_VERSION__: JSON.stringify(pkg.version) },
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});

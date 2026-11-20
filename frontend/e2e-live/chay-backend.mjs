// Khởi động backend thật cho test giao diện (FE-028): CSDL SQLite mới tinh trong thư mục tạm, nội dung bài học
// được backend tự seed khi chạy, AI tắt (không gọi Gemini). Ghi đáp án đúng ra file để test làm bài đến khi chấm đúng.
// Chạy giống nhau trên Windows/Linux/CI: PYTHON=python3 (mặc định python trên Windows).
import { spawn, execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const backend = path.resolve(here, "../../backend");
const script = path.resolve(here, "../../scripts/e2e/dap_an_giao_dien.py");
const py = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
const port = process.env.E2E_API_PORT || "8010";
const db = path.join(os.tmpdir(), "hm-e2e-live.db");
const answers = path.join(os.tmpdir(), "hm-e2e-dap-an.json");

for (const f of [db, `${db}-wal`, `${db}-shm`]) fs.rmSync(f, { force: true });
const env = { ...process.env, DATABASE_URL: `sqlite:///${db.replace(/\\/g, "/")}`, AI_ENABLED: "0", PYTHONUTF8: "1" };
fs.writeFileSync(answers, execFileSync(py, [script], { cwd: backend, env, encoding: "utf8" }));

const child = spawn(py, ["-m", "uvicorn", "app.main:app", "--port", port], { cwd: backend, env, stdio: "inherit" });
for (const sig of ["SIGINT", "SIGTERM"]) process.on(sig, () => { child.kill(); process.exit(0); });
child.on("exit", (code) => process.exit(code ?? 0));

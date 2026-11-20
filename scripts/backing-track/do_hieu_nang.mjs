// Đo hiệu năng phát trực tiếp (không phải thu offline): thời gian tải mẫu lần đầu (không cache) và lần hai (Cache Storage),
// CPU luồng chính trong 10 giây phát, số lỗi console. Chạy khi backend :8000 và `npm run dev` :5173 đang chạy.
//   node scripts/backing-track/do_hieu_nang.mjs [--style pop] [--lite]
import { createRequire } from "node:module";
const { chromium } = createRequire(import.meta.url)("playwright");
const arg = (n, d) => { const i = process.argv.indexOf(n); return i > 0 ? process.argv[i + 1] : d; };
const styles = (arg("--style", "pop,jazz,rock,funk")).split(",");
const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
const ctx = await browser.newContext();
const page = await ctx.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
await page.goto("http://localhost:5173/dev/nghe-thu.html");
await page.waitForFunction(() => window.__Tone);
const cdp = await ctx.newCDPSession(page);
await cdp.send("Performance.enable");
const metric = async () => Object.fromEntries((await cdp.send("Performance.getMetrics")).metrics.map((m) => [m.name, m.value]));
const out = [];
for (const style of styles) {
  const arr = await page.evaluate(async (style) => (await fetch("/api/v1/composition/arrangement", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key: "C", style, chords: ["C", "G", "Am", "F"], seed: 1, energy: 3 }) })).json(), style);
  const load = await page.evaluate(async (arr) => {
    const P = await import("/src/audio/band/player.ts");
    const T = await import("/src/audio/band/types.ts");
    const t0 = performance.now();
    await window.__Tone.start();
    await P.bandPlayer.play({ arrangement: arr, bpm: arr.bpm, seed: 1, loop: true, mix: T.DEFAULT_MIX, onBar: () => {}, onEnd: () => {} });
    return { ms: Math.round(performance.now() - t0), mode: P.bandPlayer.mode };
  }, arr);
  const m0 = await metric();
  await page.waitForTimeout(10000);
  const m1 = await metric();
  await page.evaluate(async () => (await import("/src/audio/band/player.ts")).bandPlayer.stop());
  const cpu = (m1.TaskDuration - m0.TaskDuration) / (m1.Timestamp - m0.Timestamp);
  out.push({ style, load_ms: load.ms, mode: load.mode, main_thread_cpu_pct: Math.round(cpu * 1000) / 10, heap_mb: Math.round(m1.JSHeapUsedSize / 1e6) });
}
console.log(JSON.stringify({ results: out, console_errors: errors }, null, 1));
await browser.close();

// Thu WAV trước/sau cho 9 phong cách × 2 vòng hợp âm (Playwright + trang nội bộ frontend/dev/nghe-thu.html).
// Chạy: backend `uvicorn app.main:app --port 8000` + frontend `npm run dev`, rồi
//   node scripts/backing-track/thu_nghe_thu.mjs [--out docs/backing-track/nghe-thu] [--wav-dir /tmp/wav]
// WAV gốc để ở --wav-dir (không đưa vào git vì nặng); bản .ogg chất lượng cao đưa vào docs để nghe trên trang so sánh.
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

// Playwright cài sẵn toàn cục trên máy chạy (không thêm vào package.json của frontend).
const { chromium } = createRequire(import.meta.url)("playwright");

const arg = (name, dflt) => { const i = process.argv.indexOf(name); return i > 0 ? process.argv[i + 1] : dflt; };
const OUT = arg("--out", "docs/backing-track/nghe-thu");
const WAV = arg("--wav-dir", "/tmp/backing-wav");
const URL = arg("--url", "http://localhost:5173/dev/nghe-thu.html");
const SECONDS = Number(arg("--seconds", "32"));
mkdirSync(OUT, { recursive: true });
mkdirSync(WAV, { recursive: true });

const STYLES = ["pop", "ballad", "bossa", "lofi", "jazz", "rock", "indie", "funk", "rnb"];
// Phong cách mới chưa có bản "trước": so với mẫu cũ gần nhất (ghi rõ trên trang so sánh).
const OLD_OF = { pop: "pop", ballad: "ballad", bossa: "bossa", lofi: "lofi", jazz: "lofi", rock: "pop", indie: "pop", funk: "pop", rnb: "lofi" };
const LOOPS = { "C-G-Am-F": ["C", "G", "Am", "F"], "Dm7-G7-Cmaj7-A7": ["Dm7", "G7", "Cmaj7", "A7"] };

// Đo khách quan bằng ffmpeg: độ to tích hợp (LUFS, EBU R128), đỉnh thật (dBTP), số mẫu chạm trần |x| ≥ 0,999 (vỡ tiếng).
function loudness(wavPath) {
  const res = execFileSync("sh", ["-c", `ffmpeg -hide_banner -nostats -i "${wavPath}" -af ebur128=peak=true -f null - 2>&1`], { encoding: "utf8" });
  const I = Number([...res.matchAll(/I:\s+(-?[\d.]+) LUFS/g)].pop()?.[1]);
  const TP = Number([...res.matchAll(/Peak:\s+(-?[\d.]+) dBFS/g)].pop()?.[1]);
  const buf = readFileSync(wavPath);
  let clipped = 0;
  for (let i = 44; i + 1 < buf.length; i += 2) if (Math.abs(buf.readInt16LE(i)) >= 32735) clipped += 1;
  return { lufs: I, true_peak_dbtp: TP, clipped_samples: clipped };
}

const browser = await chromium.launch();
const page = await browser.newPage();
page.on("console", (m) => { if (m.type() === "error") console.error("console:", m.text()); });
await page.goto(URL);
await page.waitForFunction(() => typeof window.renderAfter === "function");
const results = [];
for (const style of STYLES) {
  for (const [loopName, chords] of Object.entries(LOOPS)) {
    const seed = 1, energy = 2;
    const after = await page.evaluate(([s, c, sd, e, sec]) => window.renderAfter(s, c, sd, e, null, sec), [style, chords, seed, energy, SECONDS]);
    const before = await page.evaluate(([s, c, b, sec]) => window.renderBefore(s, c, b, sec), [OLD_OF[style], chords, after.bpm, after.seconds]);
    const m = {};
    for (const [kind, r] of [["truoc", before], ["sau", after]]) {
      const base = `${style}_${loopName}_${kind}`;
      const wavPath = join(WAV, `${base}.wav`);
      writeFileSync(wavPath, Buffer.from(r.wav, "base64"));
      m[kind] = loudness(wavPath);
      execFileSync("ffmpeg", ["-v", "error", "-y", "-i", wavPath, "-c:a", "libvorbis", "-q:a", "4", join(OUT, `${base}.ogg`)]);
    }
    results.push({ style, loop: loopName, bpm: after.bpm, seconds: after.seconds, load_ms: Math.round(after.loadMs),
      render_ms: Math.round(after.renderMs), colors: after.colors.map((c) => c.played), old_style: OLD_OF[style], before: m.truoc, after: m.sau });
    console.log(style, loopName, `bpm ${after.bpm}`, `render ${Math.round(after.renderMs)} ms`, JSON.stringify(m));
  }
}
writeFileSync(join(OUT, "ket-qua-thu.json"), JSON.stringify({ date: new Date().toISOString(), seconds: SECONDS, results }, null, 1));
await browser.close();

// Thu trọn bài (chế độ Bài hát, ADR-013 đề xuất) cho 9 phong cách + 1 bài có vòng A/B và chuyển giọng.
// Đo độ to từng đoạn (LUFS tích hợp EBU R128), đỉnh thật cả bài, và đường độ to ngắn hạn (S, 3 s) để vẽ biểu đồ
// năng lượng thiết kế ↔ đo được. Claude không nghe được: "đạt kỹ thuật" = các số đo này + test; "đạt tai" = nghe mù.
// Chạy: backend `uvicorn app.main:app --port 8000` + frontend `npm run dev`, rồi
//   node scripts/backing-track/thu_bai_hat.mjs [--out docs/backing-track/bai-hat] [--wav-dir /tmp/song-wav] [--length medium]
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const { chromium } = createRequire(import.meta.url)("playwright");

const arg = (name, dflt) => { const i = process.argv.indexOf(name); return i > 0 ? process.argv[i + 1] : dflt; };
const OUT = arg("--out", "docs/backing-track/bai-hat");
const WAV = arg("--wav-dir", "/tmp/song-wav");
const URL = arg("--url", "http://localhost:5173/dev/nghe-thu.html");
const LENGTH = arg("--length", "medium");
const ONLY = arg("--only", "");
mkdirSync(OUT, { recursive: true });
mkdirSync(WAV, { recursive: true });

const POP = ["C", "G", "Am", "F"];
const JAZZ = ["Dm7", "G7", "Cmaj7", "A7"];
const SONGS = [
  ...["pop", "ballad", "rock", "indie", "funk"].map((s) => ({ name: s, style: s, progressions: { A: POP, B: null, C: null } })),
  ...["jazz", "bossa", "lofi", "rnb"].map((s) => ({ name: s, style: s, progressions: { A: JAZZ, B: null, C: null } })),
  // Bài có vòng A (verse) và B (chorus) riêng, bật chuyển giọng ở điệp khúc cuối (QĐ 5A, mặc định tắt).
  { name: "pop-AB-chuyen-giong", style: "pop", length: "full", modulate: true,
    progressions: { A: ["Am", "F", "C", "G"], B: ["F", "G", "C", "Am"], C: null } },
].filter((s) => !ONLY || ONLY.split(",").includes(s.name));

const ff = (args) => execFileSync("sh", ["-c", `ffmpeg -hide_banner -nostats ${args} 2>&1`], { encoding: "utf8", maxBuffer: 64 << 20 });
const integrated = (out) => Number([...out.matchAll(/I:\s+(-?[\d.]+) LUFS/g)].pop()?.[1]);

function measure(wavPath, sections) {
  const whole = ff(`-i "${wavPath}" -af ebur128=peak=true -f null -`);
  const tp = Number([...whole.matchAll(/Peak:\s+(-?[\d.]+) dBFS/g)].pop()?.[1]);
  // Đường độ to ngắn hạn mỗi 0,5 s (ebur128 in mỗi 0,1 s; lấy mẫu thưa cho biểu đồ).
  const curve = [];
  for (const m of whole.matchAll(/t:\s*([\d.]+)\s+TARGET.*?S:\s*(-?[\d.]+|-inf)/g)) {
    const t = Number(m[1]);
    if (Math.abs(t * 2 - Math.round(t * 2)) < 0.05 && m[2] !== "-inf") curve.push([Math.round(t * 10) / 10, Number(m[2])]);
  }
  const per = sections.map((s) => {
    const out = ff(`-i "${wavPath}" -af "atrim=start=${s.start.toFixed(3)}:end=${s.end.toFixed(3)},ebur128" -f null -`);
    return { ...s, lufs: integrated(out) };
  });
  const buf = readFileSync(wavPath);
  let clipped = 0;
  for (let i = 44; i + 1 < buf.length; i += 2) if (Math.abs(buf.readInt16LE(i)) >= 32735) clipped += 1;
  return { lufs: integrated(whole), true_peak_dbtp: tp, clipped_samples: clipped, sections: per, curve };
}

const browser = await chromium.launch();
const page = await browser.newPage();
page.on("console", (m) => { if (m.type() === "error") console.error("console:", m.text()); });
await page.goto(URL);
await page.waitForFunction(() => typeof window.renderSong === "function");
const results = [];
for (const song of SONGS) {
  const seed = 1, energy = 2;
  const r = await page.evaluate(([s, p, l, sd, e, mod]) => window.renderSong(s, p, l, sd, e, mod),
    [song.style, song.progressions, song.length ?? LENGTH, seed, energy, !!song.modulate]);
  const wavPath = join(WAV, `${song.name}.wav`);
  writeFileSync(wavPath, Buffer.from(r.wav, "base64"));
  const m = measure(wavPath, r.sections);
  execFileSync("ffmpeg", ["-v", "error", "-y", "-i", wavPath, "-c:a", "libvorbis", "-q:a", "4", join(OUT, `${song.name}.ogg`)]);
  const v = m.sections.filter((s) => s.type === "verse").map((s) => s.lufs);
  const c = m.sections.filter((s) => s.type === "chorus").map((s) => s.lufs);
  const avg = (a) => a.reduce((x, y) => x + y, 0) / a.length;
  const chorusMinusVerse = v.length && c.length ? avg(c) - avg(v) : null;
  results.push({ name: song.name, style: song.style, length: song.length ?? LENGTH, progressions: song.progressions,
    modulate: !!song.modulate, bpm: r.bpm, seconds: r.seconds, total_bars: r.total_bars, render_ms: Math.round(r.renderMs),
    load_ms: Math.round(r.loadMs), ending: r.ending, surprises: r.surprises, chorus_minus_verse_lu: chorusMinusVerse, ...m });
  console.log(song.name, `${r.total_bars} ô`, `${r.seconds.toFixed(1)} s`, `render ${Math.round(r.renderMs)} ms`,
    `I ${m.lufs} LUFS`, `TP ${m.true_peak_dbtp}`, `C−V ${chorusMinusVerse?.toFixed(2)} LU`,
    m.sections.map((s) => `${s.label}:${s.lufs}`).join(" "));
}
writeFileSync(join(OUT, "ket-qua-bai-hat.json"), JSON.stringify({ date: new Date().toISOString(), results }, null, 1));
await browser.close();

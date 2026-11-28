// ADR-039: đo độ chính xác nghe nốt khi có tạp âm, chạy ĐÚNG đường xử lý của trình duyệt (pipeline.ts + model JSON).
// Dữ liệu do scripts/ai/pitch/luong_thu_on.py sinh (luồng thu thử có tạp âm tổng hợp, nốt từ bản thu giữ riêng).
//   npx vite-node scripts/danh_gia_micro.ts -- --data /tmp/luong_on --model public/models/pitch_mlp.json \
//       --pipeline robust --detector hybrid --out /tmp/ketqua.json
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { parseModel } from "../src/audio/pitch/features";
import { makeDetector, type DetectorKind } from "../src/audio/pitch/micListener";
import { highpass, LEGACY, MicPipeline, ROBUST, type PipelineConfig } from "../src/audio/pitch/pipeline";

type Note = { t0: number; t1: number; midi: number; inst: string };
type Stream = { name: string; file: string; sr: number; kind: string; snr: number | null; notes: Note[] };
type Score = { notes: number; correct: number; octaveOk: number; wrong: number; missed: number; extra: number; ghost: number; seconds: number; latency: number[] };

const arg = (k: string, d: string) => { const i = process.argv.indexOf(`--${k}`); return i >= 0 ? process.argv[i + 1] : d; };
const FRAME = 2048, TICK = 0.04, TAIL = 0.3;

const midiOf = (hz: number) => Math.round(69 + 12 * Math.log2(hz / 440));

function runStream(s: Stream, x: Float32Array, cfg: PipelineConfig, detector: ReturnType<typeof makeDetector>) {
  const y = cfg.hpf ? highpass(x, s.sr) : x;
  const pipe = new MicPipeline(detector, cfg);
  const hop = Math.round(TICK * s.sr);
  const out: { t: number; hz: number }[] = [];
  let ticks = 0;
  const t0 = performance.now();
  for (let pos = FRAME; pos <= y.length; pos += hop) {
    const r = pipe.push(y.subarray(pos - FRAME, pos), s.sr);
    ticks += 1;
    if (r.note) out.push({ t: pos / s.sr, hz: r.note.hz });
  }
  return { out, ms: (performance.now() - t0) / ticks, seconds: y.length / s.sr };
}

function score(s: Stream, out: { t: number; hz: number }[], seconds: number): Score {
  const sc: Score = { notes: s.notes.length, correct: 0, octaveOk: 0, wrong: 0, missed: 0, extra: 0, ghost: 0, seconds, latency: [] };
  const used = new Set<number>();
  for (const n of s.notes) {
    const inside = out.map((e, i) => ({ e, i })).filter(({ e }) => e.t >= n.t0 && e.t <= n.t1 + TAIL);
    inside.forEach(({ i }) => used.add(i));
    if (!inside.length) { sc.missed += 1; continue; }
    const first = inside[0].e;
    const m = midiOf(first.hz);
    if (m % 12 === n.midi % 12) { sc.correct += 1; sc.latency.push(first.t - n.t0); if (m === n.midi) sc.octaveOk += 1; } else sc.wrong += 1;
    sc.extra += inside.length - 1;
  }
  sc.ghost = out.filter((_, i) => !used.has(i)).length;
  return sc;
}

const sum = (a: Score[]) => a.reduce((t, x) => ({ notes: t.notes + x.notes, correct: t.correct + x.correct, octaveOk: t.octaveOk + x.octaveOk, wrong: t.wrong + x.wrong,
  missed: t.missed + x.missed, extra: t.extra + x.extra, ghost: t.ghost + x.ghost, seconds: t.seconds + x.seconds, latency: [...t.latency, ...x.latency] }),
  { notes: 0, correct: 0, octaveOk: 0, wrong: 0, missed: 0, extra: 0, ghost: 0, seconds: 0, latency: [] } as Score);

const pct = (a: number, b: number) => (b ? `${((100 * a) / b).toFixed(1)}%` : "–");

async function main() {
  const dir = arg("data", "/tmp/luong_on");
  const cfgName = arg("pipeline", "robust");
  const cfg: PipelineConfig = cfgName === "legacy" ? LEGACY : cfgName === "robust" ? ROBUST : { ...ROBUST, ...JSON.parse(cfgName) };
  const kind = arg("detector", "hybrid") as DetectorKind;
  const model = parseModel(JSON.parse(readFileSync(arg("model", "public/models/pitch_mlp.json"), "utf8")));
  const detector = makeDetector(kind, model);
  const streams: Stream[] = JSON.parse(readFileSync(join(dir, "chi_muc.json"), "utf8"));
  const groups = new Map<string, Score[]>();
  let msTotal = 0, msN = 0;
  for (const s of streams) {
    const buf = readFileSync(join(dir, s.file));
    const x = new Float32Array(buf.buffer, buf.byteOffset, buf.byteLength / 4);
    const { out, ms } = runStream(s, x, cfg, detector);
    msTotal += ms; msN += 1;
    const key = s.name.startsWith("chi_on") ? `chỉ ồn | ${s.kind} | ${s.snr} dB` : `${s.kind} | ${s.snr === null ? "sạch" : `${s.snr} dB`}`;
    const arr = groups.get(key) ?? [];
    arr.push(score(s, out, x.length / s.sr));
    groups.set(key, arr);
  }
  const rows = [...groups].map(([key, a]) => ({ key, s: sum(a) }));
  const lines = ["| Tình huống | Số nốt | Đúng tên nốt | Đúng cả quãng tám | Sai | Bỏ sót | Nốt ma / số nốt | Độ trễ TB |", "|---|---|---|---|---|---|---|---|"];
  const lat = (l: number[]) => (l.length ? `${Math.round((1000 * l.reduce((p, c) => p + c, 0)) / l.length)} ms` : "–");
  for (const { key, s } of rows) {
    if (key.startsWith("chỉ ồn")) lines.push(`| ${key} | 0 | – | – | – | – | ${s.ghost} nốt ma / ${(s.seconds / 60).toFixed(1)} phút = ${(s.ghost / (s.seconds / 60)).toFixed(1)}/phút | – |`);
    else lines.push(`| ${key} | ${s.notes} | ${pct(s.correct, s.notes)} | ${pct(s.octaveOk, s.notes)} | ${pct(s.wrong, s.notes)} | ${pct(s.missed, s.notes)} | ${pct(s.extra + s.ghost, s.notes)} | ${lat(s.latency)} |`);
  }
  // Tổng hợp theo mục tiêu của Phúc: SNR ≥ 6 dB (mọi loại tạp âm), và riêng 0 dB.
  const pick = (f: (key: string) => boolean) => sum(rows.filter((r) => f(r.key)).map((r) => r.s));
  const ge6 = pick((k) => !k.startsWith("chỉ ồn") && /\| (20|12|6) dB$/.test(k));
  const zero = pick((k) => !k.startsWith("chỉ ồn") && /\| 0 dB$/.test(k));
  const clean = pick((k) => k.endsWith("| sạch"));
  const nao = pick((k) => k.startsWith("chỉ ồn"));
  lines.push("", "| Tổng hợp | Số nốt | Đúng tên nốt | Nốt ma / số nốt | Nốt ma khi chỉ có ồn |", "|---|---|---|---|---|");
  lines.push(`| Sạch (chưa thêm tạp âm, gồm piano ảo qua loa) | ${clean.notes} | ${pct(clean.correct, clean.notes)} | ${pct(clean.extra + clean.ghost, clean.notes)} | |`);
  lines.push(`| **SNR ≥ 6 dB** (mục tiêu) | ${ge6.notes} | **${pct(ge6.correct, ge6.notes)}** | **${pct(ge6.extra + ge6.ghost, ge6.notes)}** | |`);
  lines.push(`| SNR 0 dB (rất ồn, ngoài mục tiêu) | ${zero.notes} | ${pct(zero.correct, zero.notes)} | ${pct(zero.extra + zero.ghost, zero.notes)} | |`);
  lines.push(`| Chỉ có tạp âm (${(nao.seconds / 60).toFixed(1)} phút) | 0 | | | ${nao.ghost} nốt = ${(nao.ghost / (nao.seconds / 60)).toFixed(1)}/phút |`);
  lines.push("", `Thời gian xử lý trung bình: ${(msTotal / msN).toFixed(1)} ms/khung (ngân sách 40 ms; một lõi CPU Node, chưa phải trình duyệt).`);
  console.log(`Pipeline: ${cfgName} ${JSON.stringify(cfg)}, bộ nhận diện: ${kind}\n`);
  console.log(lines.join("\n"));
  const o = arg("out", "");
  if (o) writeFileSync(o, JSON.stringify({ pipeline: cfgName, cfg, detector: kind, rows: rows.map((r) => ({ key: r.key, ...r.s, latency: undefined })),
    ge6: { ...ge6, latency: undefined }, clean: { ...clean, latency: undefined }, zero: { ...zero, latency: undefined }, noiseOnly: { ...nao, latency: undefined }, msPerFrame: msTotal / msN }, null, 1));
}

void main();

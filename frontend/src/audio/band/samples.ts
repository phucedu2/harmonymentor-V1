// Tải mẫu âm thanh lười (chỉ khi bấm Phát), theo phong cách đang chọn, có tiến độ % và cache.
// Mẫu nằm ở /samples (frontend/public/samples, dựng bằng scripts/samples/build_samples.py, ghi công ở CREDITS.md).
// Cache Storage giữ file nén giữa các lần mở trang; bộ nhớ RAM chỉ giữ bản đã giải nén của nhạc cụ đang dùng.
import * as Tone from "tone";

export type SampleZone = { file: string; midi: number | null; cents: number; layer: number; rr: number; seconds: number };
export type InstrumentManifest = {
  label: string; layers: number; lite_layers: number[];
  source: { name: string; author: string; license: string; license_url: string; repo: string; commit: string };
  pieces: Record<string, SampleZone[]>;
};
export type SampleManifest = { instruments: Record<string, InstrumentManifest> };

const BASE = "/samples/";
const CACHE = "hm-samples-v1";

let manifestPromise: Promise<SampleManifest> | null = null;
const decoded = new Map<string, Tone.ToneAudioBuffer>();

export function loadManifest(): Promise<SampleManifest> {
  manifestPromise ??= fetch(BASE + "manifest.json").then((r) => {
    if (!r.ok) throw new Error(`manifest ${r.status}`);
    return r.json() as Promise<SampleManifest>;
  }).catch((e) => { manifestPromise = null; throw e; });
  return manifestPromise;
}

/** Điện thoại / máy yếu (QĐ 9A): ít lớp lực hơn để đỡ RAM. Laptop Chrome dùng bản đầy đủ. */
export function preferLite(): boolean {
  if (typeof navigator === "undefined") return false;
  const mem = (navigator as Navigator & { deviceMemory?: number }).deviceMemory;
  return /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent) || (mem !== undefined && mem <= 4);
}

/** Các vùng sẽ dùng: bản nhẹ chỉ giữ `lite_layers`. */
export function zonesFor(inst: InstrumentManifest, lite: boolean): Record<string, SampleZone[]> {
  if (!lite) return inst.pieces;
  const keep = new Set(inst.lite_layers);
  return Object.fromEntries(Object.entries(inst.pieces).map(([k, zones]) => [k, zones.filter((z) => keep.has(z.layer))]));
}

// FE-012: tải trước (chỉ tải file nén vào Cache Storage, chưa giải nén) khi trình duyệt rảnh. Bấm Phát lần đầu
// trước đây chờ ~4 s chỉ để tải 221 file; tải trước xong thì Phát chỉ còn bước giải nén.
const warming = new Map<string, Promise<void>>();

async function fetchCached(url: string): Promise<ArrayBuffer> {
  await warming.get(url)?.catch(() => undefined); // đang tải trước thì chờ nó, khỏi tải trùng
  let cache: Cache | null = null;
  try {
    cache = typeof caches !== "undefined" ? await caches.open(CACHE) : null;
    const hit = await cache?.match(url);
    if (hit) return await hit.arrayBuffer();
  } catch { cache = null; /* trình duyệt chặn Cache Storage (ẩn danh): tải thẳng */ }
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url} ${res.status}`);
  if (cache) { try { await cache.put(url, res.clone()); } catch { /* đầy bộ nhớ: bỏ qua cache */ } }
  return res.arrayBuffer();
}

export type LoadProgress = { loaded: number; total: number };

/** Tải và giải nén mọi mẫu của các nhạc cụ; gọi lại nhiều lần không tải trùng. */
export async function loadInstruments(keys: string[], lite: boolean, onProgress?: (p: LoadProgress) => void): Promise<void> {
  const manifest = await loadManifest();
  const files = new Set<string>();
  for (const key of keys) {
    const inst = manifest.instruments[key];
    if (!inst) throw new Error(`Thiếu nhạc cụ ${key} trong manifest`);
    for (const zones of Object.values(zonesFor(inst, lite))) for (const z of zones) files.add(z.file);
  }
  const todo = [...files].filter((f) => !decoded.has(f));
  const total = files.size;
  let loaded = total - todo.length;
  onProgress?.({ loaded, total });
  const ctx = Tone.getContext();
  // 6 luồng song song: đủ nhanh, không làm nghẽn mạng của trang.
  const queue = [...todo];
  const worker = async () => {
    for (let f = queue.shift(); f; f = queue.shift()) {
      const data = await fetchCached(BASE + f);
      const audio = await ctx.decodeAudioData(data);
      decoded.set(f, new Tone.ToneAudioBuffer(audio));
      loaded += 1;
      onProgress?.({ loaded, total });
    }
  };
  await Promise.all(Array.from({ length: 6 }, worker));
}

export function bufferFor(file: string): Tone.ToneAudioBuffer | undefined {
  return decoded.get(file);
}

/** Nhạc cụ cần cho một phong cách (để tải phong cách đang chọn trước). */
export function instrumentsFor(tracks: { keys: string; bass: string }, withGuitar: boolean): string[] {
  const list = new Set<string>([tracks.keys, tracks.bass, "drums", "perc"]);
  if (withGuitar) { list.add("guitar"); list.add("guitar_mute"); }
  return [...list];
}

/** Mạng tiết kiệm dữ liệu hoặc 2G: không tự tải ~10 MB khi người dùng chưa bấm Phát. */
function shouldSkipPrefetch(): boolean {
  const conn = (navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } }).connection;
  return Boolean(conn?.saveData) || /(^|-)2g$/.test(conn?.effectiveType ?? "");
}

async function warmOne(url: string): Promise<void> {
  if (typeof caches === "undefined") return;
  const cache = await caches.open(CACHE);
  if (await cache.match(url)) return;
  const res = await fetch(url);
  if (res.ok) await cache.put(url, res);
}

/**
 * Tải trước file mẫu của các nhạc cụ vào Cache Storage, 2 luồng (nhường mạng cho trang).
 * Không tạo AudioContext, không giải nén; lỗi thì bỏ qua vì lúc bấm Phát vẫn tải lại như cũ.
 */
export async function prefetchInstruments(keys: string[], lite: boolean, signal?: AbortSignal): Promise<number> {
  if (shouldSkipPrefetch()) return 0;
  const manifest = await loadManifest();
  const files = new Set<string>();
  for (const key of keys) {
    const inst = manifest.instruments[key];
    if (inst) for (const zones of Object.values(zonesFor(inst, lite))) for (const z of zones) files.add(z.file);
  }
  const queue = [...files].filter((f) => !decoded.has(f) && !warming.has(BASE + f));
  let done = 0;
  const worker = async () => {
    for (let f = queue.shift(); f && !signal?.aborted; f = queue.shift()) {
      const url = BASE + f;
      const job = warmOne(url).catch(() => undefined);
      warming.set(url, job);
      await job;
      done += 1;
    }
  };
  await Promise.all([worker(), worker()]);
  return done;
}

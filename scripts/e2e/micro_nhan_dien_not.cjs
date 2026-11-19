// ADR-030: thử "Đàn bằng micro" trên giao diện thật (Playwright), không cần micro thật.
// Thay getUserMedia bằng luồng âm thanh phát MẪU PIANO THU THẬT (Salamander, /samples/piano), nên cả chuỗi
// micro → AnalyserNode → YIN → ổn định nốt → Engine đặt tên → chấm đều chạy như trên máy người học.
// Chạy: backend :8000 + vite :5173, rồi  OUT=thu-muc-anh node scripts/e2e/micro_nhan_dien_not.cjs
const { chromium } = require('playwright');
const OUT = process.env.OUT || '.';
const BASE = process.env.BASE || 'http://localhost:5173';
const log = (...a) => console.log('[micro]', ...a);

const FAKE_MIC = `(() => {
  const ctx = new AudioContext();
  const dest = ctx.createMediaStreamDestination();
  let zones = null;
  const buffers = new Map();
  async function load() {
    if (zones) return;
    const m = await (await fetch('/samples/manifest.json')).json();
    zones = m.instruments.piano.pieces.notes.filter((z) => z.layer === 1 && z.rr === 1);
  }
  async function buf(file) {
    if (!buffers.has(file)) buffers.set(file, await ctx.decodeAudioData(await (await fetch('/samples/' + file)).arrayBuffer()));
    return buffers.get(file);
  }
  // Phát lần lượt các nốt (số MIDI), mỗi nốt 0,8 s, nghỉ 0,35 s, như người học rải hợp âm.
  window.__hmPlay = async (midis, gain = 0.8) => {
    await load(); await ctx.resume();
    let t = ctx.currentTime + 0.1;
    for (const midi of midis) {
      const z = zones.reduce((a, b) => Math.abs(b.midi - midi) < Math.abs(a.midi - midi) ? b : a);
      const src = ctx.createBufferSource();
      src.buffer = await buf(z.file);
      src.playbackRate.value = Math.pow(2, (midi - z.midi - z.cents / 100) / 12);
      const g = ctx.createGain(); g.gain.value = gain;
      g.gain.setValueAtTime(gain, t + 0.7); g.gain.linearRampToValueAtTime(0, t + 0.8);
      src.connect(g).connect(dest); src.start(t); src.stop(t + 0.85);
      t += 1.15;
    }
    return (t - ctx.currentTime) * 1000;
  };
  // Mỗi lần mở micro trả một bản sao, vì tắt micro sẽ dừng track (giống micro thật).
  navigator.mediaDevices.getUserMedia = async () => new MediaStream(dest.stream.getAudioTracks().map((t) => t.clone()));
})();`;

const NAMES = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
// Chỉ để kịch bản biết phải "đàn" phím nào: lấy nốt từ Engine rồi xếp lên từ quãng tám 4.
function midisFrom(notes) {
  let prev = -1;
  return notes.map((n) => {
    const m = n.match(/^([A-G])(#{1,2}|b{1,2})?/);
    const pc = (NAMES[m[1]] + (!m[2] ? 0 : m[2].startsWith('#') ? m[2].length : -m[2].length) + 12) % 12;
    let midi = 60 + pc;
    while (midi <= prev) midi += 12;
    prev = midi; return midi;
  });
}

async function run(viewport, tag) {
  const b = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ viewport, deviceScaleFactor: 2 });
  await ctx.addInitScript(FAKE_MIC);
  const p = await ctx.newPage();
  const email = `micro-${tag}-${Date.now()}@example.test`;
  await p.goto(`${BASE}/dang-ky`);
  await p.getByLabel('Tên hiển thị').fill('Học sinh đàn thử');
  await p.getByLabel('Email').fill(email);
  await p.getByLabel('Mật khẩu', { exact: true }).fill('matkhau123');
  await p.getByLabel('Nhập lại mật khẩu').fill('matkhau123');
  await p.getByRole('button', { name: /Đăng ký|Tạo tài khoản/ }).click();
  await p.waitForURL(/kiem-tra-dau-vao|\/app/, { timeout: 15000 });
  await p.goto(`${BASE}/app/luyen-tap`);
  await p.getByRole('button', { name: 'Đàn bằng micro' }).click();
  const card = p.locator('p.text-xl').first();
  const symbol = (await card.locator('span.font-mono').innerText()).trim();
  const chord = await (await p.request.get(`${BASE}/api/v1/engine/chord/${encodeURIComponent(symbol)}`)).json();
  const midis = midisFrom(chord.notes);
  log(tag, 'de:', symbol, chord.notes.join(' '), '-> phat MIDI', midis.join(' '));
  await p.getByRole('button', { name: /Bật micro/ }).click();
  await p.getByRole('button', { name: /Tắt micro/ }).waitFor();
  // Lượt 1: đàn sai nốt cuối (lệch nửa cung) để thấy máy chấm sai.
  const wrong = [...midis.slice(0, -1), midis[midis.length - 1] + 1];
  let ms = await p.evaluate((m) => window.__hmPlay(m), wrong);
  await p.waitForTimeout(ms * 0.55);
  await p.screenshot({ path: `${OUT}/${tag}-01-dang-nghe.png` });
  await p.waitForTimeout(ms * 0.45 + 600);
  const heardWrong = await p.getByText(/^Đã chọn:/).innerText();
  log(tag, 'nghe (sai):', heardWrong);
  await p.getByRole('button', { name: 'Kiểm tra' }).click();
  await p.getByText('Đáp án đúng:').waitFor({ timeout: 10000 });
  await p.screenshot({ path: `${OUT}/${tag}-02-sai.png`, fullPage: true });
  // Lượt 2: câu khác, đàn đúng.
  await p.getByRole('button', { name: 'Câu khác' }).click();
  const symbol2 = (await p.locator('p.text-xl span.font-mono').first().innerText()).trim();
  const chord2 = await (await p.request.get(`${BASE}/api/v1/engine/chord/${encodeURIComponent(symbol2)}`)).json();
  const midis2 = midisFrom(chord2.notes);
  log(tag, 'de 2:', symbol2, chord2.notes.join(' '), '-> phat MIDI', midis2.join(' '));
  await p.getByRole('button', { name: /Bật micro/ }).click();
  ms = await p.evaluate((m) => window.__hmPlay(m), midis2);
  await p.waitForTimeout(ms + 600);
  log(tag, 'nghe (dung):', await p.getByText(/^Đã chọn:/).innerText());
  await p.getByRole('button', { name: 'Kiểm tra' }).click();
  await p.getByText(/Đúng cao độ/).waitFor({ timeout: 10000 });
  await p.screenshot({ path: `${OUT}/${tag}-03-dung.png`, fullPage: true });
  log(tag, 'ket qua:', (await p.getByText(/Đúng cao độ/).innerText()).slice(0, 120));
  await b.close();
}

(async () => {
  await run({ width: 1280, height: 900 }, 'may-tinh');
  await run({ width: 390, height: 844 }, 'dien-thoai');
})().catch((e) => { console.error(e); process.exit(1); });

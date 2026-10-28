// HM-001: chụp khuông L01 và ghi nốt thật mà nút "Nghe" gửi cho Tone. node chup.mjs <truoc|sau> <thư mục ảnh>
import { chromium } from "/opt/node22/lib/node_modules/playwright/index.mjs";
const [tag, out] = process.argv.slice(2);
const browser = await chromium.launch();
const log = (...a) => console.log(...a);
for (const [dev, viewport] of [["may-tinh", { width: 1280, height: 900 }], ["dien-thoai", { width: 390, height: 844 }]]) {
  const ctx = await browser.newContext({ viewport, baseURL: "http://localhost:5173" });
  const page = await ctx.newPage();
  page.on("console", (m) => { if (m.type() === "error") log(dev, "console.error:", m.text().slice(0, 160)); });
  await page.request.post("/api/v1/auth/register", { data: { email: `hm001-${tag}-${dev}-${Date.now()}@example.com`, password: "MatKhau-HM001-2026", display_name: "HM001" } });
  await page.goto("/app/hoc");
  await page.getByText("Học ngay").first().click();
  await page.getByText("Mục lục bài học").click();
  await page.getByRole("button", { name: /Khám phá M3, m3, P5 và d5/ }).waitFor();
  // Bắt nốt gửi cho Tone: thay playChord của cùng module AudioEngine mà app đang dùng (Vite dev).
  await page.evaluate(async () => {
    const m = await import("/src/audio/AudioEngine.ts");
    window.__played = [];
    m.audioEngine.playChord = async (notes) => { window.__played.push(notes); };
  });
  const midiOf = (n) => { const x = n.match(/^([A-G])(#?)(-?\d+)$/); const pc = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 }[x[1]] + (x[2] ? 1 : 0); return 12 * (+x[3] + 1) + pc; };
  const pickRoot = async (block, label, spelling) => {
    await block.locator(".root-selector-grid button", { hasText: new RegExp(`^${label.replace("/", "\\/")}$`) }).click();
    if (label.includes("/")) await block.locator(".enharmonic-choice button", { hasText: new RegExp(`^${spelling}$`) }).click();
  };
  const lastPlayed = async () => (await page.evaluate(() => window.__played.at(-1))) ?? [];

  await page.getByRole("button", { name: /Khám phá M3, m3, P5 và d5/ }).click();
  let block = page.locator("article.explorer-block").first();
  for (const [label, sp, code] of [["G#/Ab", "G#", "M3"], ["G#/Ab", "Ab", "m3"], ["F", "F", "d5"], ["C", "C", "M3"], ["D", "D", "m3"], ["G", "G", "P5"]]) {
    await pickRoot(block, label, sp);
    await block.locator(".interval-choice-row button").filter({ has: page.locator("b", { hasText: new RegExp(`^${code}$`) }) }).click();
    await page.waitForTimeout(300);
    await block.locator("button.audio-button").click();
    const played = await lastPlayed();
    log(`${tag} ${dev} quãng ${sp} ${code}: nhãn "${await block.locator(".notation-example-label").textContent()}" | gửi Tone ${played.join(" ")} = MIDI ${played.map(midiOf).join(",")}`);
    if (["G#", "Ab", "F"].includes(sp)) await block.locator(".notation-shell").screenshot({ path: `${out}/${tag}-${dev}-quang-${sp.replace("#", "s")}-${code}.png` });
  }
  if (!(await page.getByRole("button", { name: /So sánh chất lượng hợp âm/ }).isVisible())) await page.getByText("Mục lục bài học").click();
  await page.getByRole("button", { name: /So sánh chất lượng hợp âm/ }).click();
  block = page.locator("article.explorer-block").first();
  for (const [label, sp] of [["G#/Ab", "G#"], ["G#/Ab", "Ab"], ["F", "F"], ["E", "E"]]) {
    await pickRoot(block, label, sp);
    await page.waitForTimeout(300);
    await block.locator(".notation-shell").screenshot({ path: `${out}/${tag}-${dev}-hop-am-${sp.replace("#", "s")}.png` });
  }
  if (!(await page.getByRole("button", { name: /Nghe sự thay đổi/ }).isVisible())) await page.getByText("Mục lục bài học").click();
  await page.getByRole("button", { name: /Nghe sự thay đổi/ }).click();
  block = page.locator("article.explorer-block").first();
  for (const [label, sp] of [["G#/Ab", "G#"], ["G#/Ab", "Ab"], ["F", "F"], ["E", "E"]]) {
    await pickRoot(block, label, sp);
    for (const btn of await block.locator("button.audio-button").all()) {
      await btn.click();
      const played = await lastPlayed();
      log(`${tag} ${dev} nghe ${(await btn.textContent()).replace("▶ ", "")}: gửi Tone ${played.join(" ")} = MIDI ${played.map(midiOf).join(",")}`);
    }
  }
  await ctx.close();
}
await browser.close();

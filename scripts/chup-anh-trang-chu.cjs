// Chụp ảnh thật của khu học cho các ô "Tính năng" ở trang chủ (frontend/public/home/<id>-<sáng|tối>.webp).
// Cách chạy (backend + vite đang chạy, AI_ENABLED tùy máy):
//   cd backend && python ../scripts/e2e/dap_an_demo_1011.py > /tmp/dap_an.json
//   ANS=/tmp/dap_an.json OUT=frontend/public/home node scripts/chup-anh-trang-chu.cjs
// Tài khoản dùng để chụp là tài khoản thử tạo ngay lúc chạy, không phải tài khoản thật của nhóm.
const { chromium } = require("playwright");
const fs = require("fs");

const BASE = process.env.BASE ?? "http://127.0.0.1:5173";
const OUT = process.env.OUT ?? "frontend/public/home";
const ANS = JSON.parse(fs.readFileSync(process.env.ANS, "utf8"));
const MAX_H = 760;          // Cắt bớt phần quá dài để ảnh không cao lênh khênh.
const dims = {};            // id -> [rộng, cao] theo pixel ảnh; ghi ra shots.ts cho FeatureBento.
const log = (...a) => console.log("[anh]", ...a);

async function hoanThanhBai(p, lesson) {
  await p.getByRole("button", { name: "Xem cả bài" }).click();
  await p.waitForTimeout(1000);
  for (const q of ANS[lesson]) {
    const card = p.locator("div.grid.gap-2").filter({ has: p.locator("b", { hasText: q.prompt }) }).last();
    await card.scrollIntoViewIfNeeded();
    if (q.choice) await card.getByRole("button", { name: q.answer, exact: true }).click();
    else await card.getByLabel(`Câu trả lời: ${q.prompt}`).fill(q.answer);
    await card.getByRole("button", { name: /^Kiểm tra/ }).click();
    await card.getByText("Chính xác!").waitFor({ timeout: 15000 });
  }
  const done = p.getByRole("button", { name: "Hoàn thành và lên lịch ôn" });
  await done.scrollIntoViewIfNeeded();
  await done.click();
  await p.getByText("Hoàn thành!").first().waitFor({ timeout: 15000 });
}

/** Chụp đúng vùng của phần tử (cắt bớt nếu quá cao) rồi ghi WebP; nhớ kích thước thật để đặt width/height. */
async function chup(p, id, theme, target, maxH = MAX_H) {
  const box = await target.boundingBox();
  const clip = {
    x: Math.max(0, box.x),
    y: Math.max(0, box.y),
    width: Math.min(box.width, 1280 - Math.max(0, box.x)),
    height: Math.min(box.height, maxH),
  };
  await p.screenshot({ path: `${OUT}/${id}-${theme}.webp`, type: "webp", quality: 82, clip });
  dims[id] = [Math.round(clip.width * 2), Math.round(clip.height * 2)];
  log(id, theme, dims[id].join("x"));
}

async function datTheme(p, theme) {
  await p.evaluate((t) => {
    localStorage.setItem("hm-theme", t);
    if (t === "dark") document.documentElement.dataset.theme = "dark";
    else delete document.documentElement.dataset.theme;
  }, theme);
  await p.waitForTimeout(300);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2, reducedMotion: "reduce" });
  const p = await ctx.newPage();

  // Tài khoản thử, chỉ sống trong lần chạy này.
  const email = `hocsinh.thu${Date.now()}@vidu.test`;
  await p.goto(`${BASE}/dang-ky`);
  await p.getByLabel("Tên hiển thị").fill("Học sinh thử");
  await p.getByLabel("Email").fill(email);
  await p.getByLabel("Mật khẩu", { exact: true }).fill("matkhau123");
  await p.getByLabel("Nhập lại mật khẩu").fill("matkhau123");
  await p.getByRole("button", { name: /Đăng ký|Tạo tài khoản/ }).click();
  await p.waitForURL(/kiem-tra-dau-vao/, { timeout: 20000 });

  for (const theme of ["light", "dark"]) {
    await datTheme(p, theme);
    await p.waitForTimeout(400);
    await chup(p, "kiem-tra-dau-vao", theme, p.locator("main"), 420);
  }
  await p.getByRole("button", { name: "Chưa học, bắt đầu từ Bài 1" }).click();
  await p.waitForURL(/\/app$/, { timeout: 20000 });

  // Bài học: câu trắc nghiệm và câu dựng hợp âm trên piano, cùng lời giải khi sai.
  await p.goto(`${BASE}/app/hoc?bai=L01`);
  await p.getByRole("button", { name: "Xem cả bài" }).click();
  await p.waitForTimeout(1200);
  const mcq = ANS.L01.find((q) => q.choice);
  const theMcq = p.locator("div.grid.gap-2").filter({ has: p.locator("b", { hasText: mcq.prompt }) }).last();
  const build = ANS.L01.find((q) => !q.choice);
  const theBuild = p.locator("div.grid.gap-2").filter({ has: p.locator("b", { hasText: build.prompt }) }).last();

  for (const theme of ["light", "dark"]) {
    await datTheme(p, theme);
    await theMcq.scrollIntoViewIfNeeded();
    await p.waitForTimeout(400);
    await chup(p, "hoc-va-lam", theme, theMcq);
    await theBuild.scrollIntoViewIfNeeded();
    await p.waitForTimeout(400);
    await chup(p, "dung-hop-am", theme, theBuild);
  }

  // Lời giải: trả lời sai hai lần một câu dựng hợp âm để web hiện lời giải.
  for (let i = 0; i < 2; i++) {
    await theBuild.getByLabel(`Câu trả lời: ${build.prompt}`).fill("C E G#");
    await theBuild.getByRole("button", { name: /^Kiểm tra/ }).click();
    await p.waitForTimeout(900);
  }
  for (const theme of ["light", "dark"]) {
    await datTheme(p, theme);
    await theBuild.scrollIntoViewIfNeeded();
    await p.waitForTimeout(400);
    await chup(p, "loi-giai", theme, theBuild);
  }

  // Hoàn thành L01 để có thẻ ôn và mức thành thạo thật.
  await p.goto(`${BASE}/app/hoc?bai=L01`);
  await p.waitForTimeout(1200);
  await hoanThanhBai(p, "L01");

  await p.goto(`${BASE}/app/tien-do`);
  await p.waitForTimeout(1500);
  for (const theme of ["light", "dark"]) {
    await datTheme(p, theme);
    await p.evaluate(() => window.scrollTo(0, 0));
    await p.waitForTimeout(400);
    await chup(p, "on-tap", theme, p.locator("main"), 700);
    // Mức thành thạo từng kỹ năng nằm ở thẻ "Kỹ năng của bạn", thấp hơn trên trang.
    const kyNang = p.locator("div").filter({ has: p.getByText("Kỹ năng của bạn", { exact: true }) }).last();
    await kyNang.scrollIntoViewIfNeeded();
    await p.waitForTimeout(400);
    await chup(p, "tien-do", theme, kyNang, 620);
  }

  // Harmony Lab.
  await p.goto(`${BASE}/app/composition`);
  await p.waitForTimeout(2500);
  for (const theme of ["light", "dark"]) {
    await datTheme(p, theme);
    await p.evaluate(() => window.scrollTo(0, 0));
    await p.waitForTimeout(500);
    await chup(p, "harmony-lab", theme, p.locator("main"));
  }

  // AI Tutor: hỏi một câu nhạc lý và chờ câu trả lời có trích dẫn.
  await p.goto(`${BASE}/app/hoc?bai=L01`);
  await p.waitForTimeout(1500);
  await p.getByRole("button", { name: "Mở AI Tutor" }).click();
  const hop = p.getByRole("dialog", { name: "AI Tutor" });
  await hop.getByRole("textbox").fill("Hợp âm C trưởng gồm những nốt nào?");
  await hop.getByRole("textbox").press("Enter");
  await p.waitForTimeout(6000);
  for (const theme of ["light", "dark"]) {
    await datTheme(p, theme);
    await p.waitForTimeout(500);
    await chup(p, "ai-tutor", theme, hop);
  }

  // Kích thước ảnh ghi ra mã nguồn để thẻ <img> có width/height đúng, trang không bị giật bố cục khi ảnh về.
  const ts = "// Tệp này do scripts/chup-anh-trang-chu.cjs sinh ra cùng lúc với ảnh trong public/home. Đừng sửa tay.\n"
    + "export const SHOT_SIZE: Record<string, [number, number]> = " + JSON.stringify(dims, null, 2) + ";\n";
  fs.writeFileSync("frontend/src/pages/public/home/shots.ts", ts);
  await b.close();
  log("xong");
})().catch((e) => { console.error(e); process.exit(1); });

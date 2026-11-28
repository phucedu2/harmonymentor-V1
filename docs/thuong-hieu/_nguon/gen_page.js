// Sinh trang xem trước (Artifact) và trang mockup để chụp PNG.
const fs = require('fs');
const path = require('path');
const { S } = require('./symbols');
const { CRITERIA, INTRO, TERRITORIES, LOGOS, TOP3 } = require('./meta');
const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'data.json'), 'utf8'));
const OUT = process.env.OUT || path.join(__dirname, '..');
const PAGE = process.env.PAGE || path.join(__dirname, 'preview.html');
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const sum = (a) => a.reduce((x, y) => x + y, 0);
const TAG = 'Học nhạc lý cùng gia sư';
const finals = Object.keys(LOGOS).filter((k) => LOGOS[k].kind !== 'cut');
const cuts = Object.keys(LOGOS).filter((k) => LOGOS[k].kind === 'cut');
const T = Object.fromEntries(TERRITORIES.map((t) => [t.code, t]));

// Thu nhỏ SVG gốc trong khung có kích thước cố định
const sized = (svg, cls = '') => svg.replace('<svg ', `<svg class="${cls}" preserveAspectRatio="xMidYMid meet" `);
const animCss = finals.map((id) => (S[id].anim || '').replace(/\.play /g, `[data-logo="${id}"].play `)).join('\n');

function mockups(id) {
  const d = data.logos[id], m = LOGOS[id];
  return `
<div class="mk-grid">
  <figure class="mk" data-shot="${id}-header-sang">
    <div class="mk-head light"><span class="mk-logo">${sized(d.h.light)}</span><nav><span>Học</span><span>Luyện tập</span><span>Chẩn đoán</span><span>Sáng tác</span><span>Chơi nhạc</span></nav><b class="mk-cta">Bắt đầu học</b></div>
    <div class="mk-head dark"><span class="mk-logo">${sized(d.h.dark)}</span><nav><span>Học</span><span>Luyện tập</span><span>Chẩn đoán</span><span>Sáng tác</span><span>Chơi nhạc</span></nav><b class="mk-cta">Bắt đầu học</b></div>
    <figcaption>Thanh đầu trang web, sáng và tối (logo cao 36px)</figcaption>
  </figure>
  <figure class="mk" data-shot="${id}-tab">
    <div class="mk-tabs light"><div class="tab on"><span class="fav">${sized(d.icon)}</span>Harmony Mentor · ${TAG}</div><div class="tab">Tài liệu lớp 11</div></div>
    <div class="mk-tabs dark"><div class="tab on"><span class="fav">${sized(d.icon)}</span>Harmony Mentor · ${TAG}</div><div class="tab">Tài liệu lớp 11</div></div>
    <figcaption>Tab trình duyệt, favicon đúng 16px</figcaption>
  </figure>
  <figure class="mk" data-shot="${id}-slide">
    <div class="mk-slide"><span class="mk-v">${sized(d.v.dark)}</span><p class="mk-sub">Nền tảng học nhạc lý thích ứng có gia sư AI</p><p class="mk-foot"><span>Đồ án nhóm · Thắng · Phúc · Đạt</span><span>04/12/2026</span></p></div>
    <figcaption>Slide bìa 16:9</figcaption>
  </figure>
  <figure class="mk" data-shot="${id}-sticker">
    <div class="mk-stick-wrap"><div class="mk-stick"><span class="st-sym">${sized(d.sym.light)}</span><span class="st-wm">${sized(d.wm.light)}</span><span class="st-tag">${TAG}</span></div></div>
    <figcaption>Sticker cắt tròn (đường kính 6 cm)</figcaption>
  </figure>
</div>`;
}

function scoreRow(id) {
  const m = LOGOS[id];
  return `<tr><th scope="row">${esc(m.name)}<small>${m.kind === 'main' ? 'Dùng ngay' : m.kind === 'bold' ? 'Táo bạo' : 'Bị loại'}</small></th>${m.s.map((v) => `<td class="sc s${v}">${v}</td>`).join('')}<td class="tot">${sum(m.s)}</td></tr>`;
}

function card(id) {
  const d = data.logos[id], m = LOGOS[id];
  return `
<article class="card" id="logo-${id}" data-id="${id}">
  <button class="stage" type="button" data-open="${id}" aria-label="Phóng to ${esc(m.name)}">
    <span class="v v-light">${sized(d.h.light)}</span><span class="v v-dark">${sized(d.h.dark)}</span><span class="v v-mono">${sized(d.h.mono)}</span><span class="v v-tiny"><span class="t16">${sized(d.icon)}</span><span class="t32">${sized(d.icon)}</span><span class="t16 lt">${sized(d.sym.light)}</span></span>
  </button>
  <div class="card-body">
    <div class="card-top"><h3>${esc(m.name)}</h3><span class="pill ${m.kind}">${m.kind === 'main' ? 'Dùng ngay' : 'Táo bạo'}</span><span class="score">${sum(m.s)}<small>/35</small></span></div>
    <p class="terr">Lãnh thổ ${m.t} · ${esc(T[m.t].name)}</p>
    <p>${esc(m.story)}</p>
    <div class="card-act"><button type="button" class="btn-sm" data-play="${id}">Phát chuyển động</button><span class="anim-slot" data-logo="${id}">${sized(d.anim.light, 'an-l')}${sized(d.anim.dark, 'an-d')}</span><button type="button" class="btn-sm ghost" data-open="${id}">Xem chi tiết</button></div>
  </div>
</article>`;
}

function detail(id) {
  const d = data.logos[id], m = LOGOS[id];
  return `
<template id="tpl-${id}">
  <div class="dl-head"><div><p class="eyebrow">Lãnh thổ ${m.t} · ${esc(T[m.t].name)}</p><h2>${esc(m.name)}</h2></div><span class="score big">${sum(m.s)}<small>/35</small></span></div>
  <div class="dl-grid">
    <div class="dl-big light" data-logo="${id}">${sized(d.anim.light)}</div>
    <div class="dl-big dark" data-logo="${id}">${sized(d.anim.dark)}</div>
    <div class="dl-big mono">${sized(d.sym.mono)}</div>
  </div>
  <div class="dl-row"><div class="dl-lock light">${sized(d.h.light)}</div><div class="dl-lock dark">${sized(d.h.dark)}</div></div>
  <div class="dl-small"><span>Ở cỡ thật:</span><span class="t16">${sized(d.icon)}</span><span class="t32">${sized(d.icon)}</span><span class="t48">${sized(d.icon)}</span><span class="t16 lt">${sized(d.sym.light)}</span><span class="t32 lt">${sized(d.sym.light)}</span><span class="t16 dk">${sized(d.sym.dark)}</span><span class="t32 dk">${sized(d.sym.dark)}</span><span class="squint">${sized(d.sym.light)}</span><small>(ô cuối: thử nheo mắt)</small></div>
  <dl class="dl-text">
    <dt>Câu chuyện</dt><dd>${esc(m.story)}</dd>
    <dt>Chữ phá cách</dt><dd>${esc(m.twist)}</dd>
    <dt>Chuyển động</dt><dd>${esc(m.motion)} <button type="button" class="btn-sm" data-replay>Phát lại</button></dd>
    <dt>Cảm hứng</dt><dd>${esc(T[m.t].ref)}</dd>
  </dl>
  <table class="sc-mini"><tr>${CRITERIA.map((c, i) => `<th scope="col">${c}</th>`).join('')}</tr><tr>${m.s.map((v) => `<td class="sc s${v}">${v}</td>`).join('')}</tr></table>
  <p class="path">File: <code>logo-di/svg/${id}/</code></p>
</template>`;
}

const top3Html = TOP3.map((t) => {
  const d = data.logos[t.id], m = LOGOS[t.id];
  return `
<section class="t3" id="hang-${t.rank}">
  <div class="t3-head"><span class="rank">${t.rank}</span><div><h3>${esc(m.name)}</h3><p class="terr">${sum(m.s)}/35 điểm · Lãnh thổ ${m.t}</p></div></div>
  <p class="t3-why">${esc(t.why)}</p>
  <div class="t3-kit">
    <div class="kit light"><span class="kit-h">${sized(d.h.light)}</span></div>
    <div class="kit dark"><span class="kit-h">${sized(d.h.dark)}</span></div>
    <div class="kit light"><span class="kit-v">${sized(d.v.light)}</span></div>
    <div class="kit dark"><span class="kit-v">${sized(d.v.dark)}</span></div>
    <div class="kit mono"><span class="kit-h">${sized(d.h.mono)}</span></div>
    <div class="kit icons"><span class="ic96">${sized(d.icon)}</span><span class="ic48">${sized(d.icon)}</span><span class="t32">${sized(d.icon)}</span><span class="t16">${sized(d.icon)}</span><small>App icon 96 · 48 · 32 · 16</small></div>
  </div>
  ${mockups(t.id)}
  <details class="files"><summary>Các file trong bộ này</summary>
    <ul>
      <li><code>svg/${t.id}/</code> ngang, dọc, biểu tượng (sáng, tối, đen, trắng), wordmark, app-icon.svg, favicon.svg, chuyen-dong.svg</li>
      <li><code>png/${t.id}/</code> icon-16…1024, ngang 600/1200/2400px, dọc 800px, biểu tượng 1024px</li>
      <li><code>favicon/${t.id}/</code> favicon.ico (16/32/48), favicon.svg tự đổi sáng/tối, apple-touch-icon.png (180), icon-192, icon-512, site.webmanifest</li>
      <li><code>react/${t.id}/Logo.tsx</code> và <code>logo.css</code> (biến <code>--hm-logo-*</code>, prop <code>variant</code> và <code>animate</code>)</li>
      <li><code>mockup/${t.id}-*.png</code> bốn ảnh mockup trên</li>
    </ul>
  </details>
</section>`;
}).join('');

const contrast = [
  ['Chữ sơn mài #0C231F', 'nền ngà #F2F3EA', '14,72 : 1', 'Đạt AAA'],
  ['Chữ ngà #F2F3EA', 'nền tối #081613', '16,56 : 1', 'Đạt AAA'],
  ['Chữ gỉ đậm #006D61 (chữ m của bản m 4:3)', 'nền ngà #F2F3EA', '5,59 : 1', 'Đạt AA'],
  ['Chữ gỉ #45C2AB (chữ m, bản tối)', 'nền tối #081613', '8,42 : 1', 'Đạt AAA'],
  ['Chữ đồng đậm #7C5502 (chữ o, số ngón)', 'nền ngà #F2F3EA', '5,95 : 1', 'Đạt AA'],
  ['Chữ đồng #E8B458 (bản tối)', 'nền tối #081613', '9,78 : 1', 'Đạt AAA'],
  ['Chi tiết đồng thau #E0A53E (không phải chữ)', 'nền ngà #F2F3EA', '1,95 : 1', 'Chỉ trang trí: hình vẫn đọc được khi bỏ màu này (xem bản 1 màu)'],
  ['Chi tiết đồng thau #E0A53E', 'nền sơn mài #0C231F', '7,54 : 1', 'Đạt (vì thế icon app dùng nền sơn mài)'],
];

const html = `<title>Logo Harmony Mentor</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,500;9..144,700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Bố cục: một cột đọc + lưới logo; dùng chính bảng màu Đồng & Gỉ của app */
:root{
  --bg:#F2F3EA;--surface:#FAFBF5;--raised:#FEFFFC;--fg:#0C231F;--muted:#48615C;--line:#D2D8CD;
  --primary:#006D61;--on-primary:#FCFCF8;--sig:#45C2AB;--brass:#E0A53E;--brass-ink:#7C5502;--felt:#B4343B;
  --stage-light:#F2F3EA;--stage-dark:#081613;--stage-mono:#FFFFFF;--ok:#21763C;
  --f-display:"Fraunces",Georgia,serif;--f-body:"Be Vietnam Pro",system-ui,sans-serif;--f-mono:"IBM Plex Mono",ui-monospace,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#081613;--surface:#101F1C;--raised:#182926;--fg:#EAEAE1;--muted:#ADB4A7;--line:#2C3F3B;--primary:#5BC7B1;--on-primary:#041A17;--brass-ink:#EBBC63;--ok:#76CF8A;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#081613;--surface:#101F1C;--raised:#182926;--fg:#EAEAE1;--muted:#ADB4A7;--line:#2C3F3B;--primary:#5BC7B1;--on-primary:#041A17;--brass-ink:#EBBC63;--ok:#76CF8A;color-scheme:dark}
*{box-sizing:border-box}[hidden]{display:none!important}
body{background:var(--bg);color:var(--fg);font:15px/1.6 var(--f-body);margin:0}
.wrap{max-width:1180px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:20px 64px}
h1,h2,h3{font-family:var(--f-display);font-weight:700;line-height:1.15;text-wrap:balance;margin:0}
h1{font-size:clamp(30px,5vw,46px)}h2{font-size:clamp(22px,3vw,30px)}h3{font-size:19px}
p{margin:0}code{font-family:var(--f-mono);font-size:.88em}
.eyebrow,.terr{font-family:var(--f-mono);font-size:12px;letter-spacing:.04em;color:var(--muted)}
.bar{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bg);border-bottom:1px solid var(--line)}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--bg)}
.bar-in{max-width:1180px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:10px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.bar-in .tabs{display:flex;gap:4px}.bar-in .tabs a{font-weight:600;text-decoration:none;color:var(--muted);padding:6px 12px;border-radius:999px}
.bar-in .tabs a[aria-current="page"]{background:var(--fg);color:var(--bg)}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;margin-left:auto}
.seg button{font:600 13px var(--f-body);border:0;background:transparent;color:var(--fg);padding:6px 12px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--primary);color:var(--on-primary)}
button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #C9690C;outline-offset:2px}
.hero{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:32px;align-items:end;padding-block:28px 12px}
.hero p{color:var(--muted);max-width:62ch;margin-top:12px}
.hero-mark{background:var(--stage-dark);border-radius:6px;padding:22px;display:grid;place-items:center}
.hero-mark svg{width:100%;height:auto;max-height:120px}
section{margin-top:44px}
.sec-head{display:flex;gap:16px;align-items:baseline;justify-content:space-between;flex-wrap:wrap;margin-bottom:16px;border-top:2px solid var(--fg);padding-top:12px}
.sec-head p{color:var(--muted);max-width:70ch}
.why{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
.why p{max-width:60ch}
.terrs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.terr-c{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:16px;display:grid;gap:8px;align-content:start}
.terr-c .code{font:700 13px var(--f-mono);color:var(--primary)}
.terr-c dl{display:grid;grid-template-columns:auto 1fr;gap:4px 10px;margin:0;font-size:14px}
.terr-c dt{font-weight:600;color:var(--muted)}.terr-c dd{margin:0}
.ref{font-size:13.5px;color:var(--muted);border-left:3px solid var(--brass);padding-left:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}
.grid-label{font:600 13px var(--f-mono);letter-spacing:.06em;color:var(--muted);margin:20px 0 10px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:6px;overflow:hidden;display:flex;flex-direction:column}
.stage{all:unset;cursor:zoom-in;display:grid;place-items:center;height:150px;padding:18px 22px;background:var(--stage-light)}
.stage .v{display:none;width:100%;height:100%}.stage .v svg{width:100%;height:100%}
[data-bg="light"] .stage{background:var(--stage-light)}[data-bg="light"] .v-light{display:block}
[data-bg="dark"] .stage{background:var(--stage-dark)}[data-bg="dark"] .v-dark{display:block}
[data-bg="mono"] .stage{background:var(--stage-mono)}[data-bg="mono"] .v-mono{display:block}
[data-bg="tiny"] .stage{background:var(--stage-light)}[data-bg="tiny"] .v-tiny{display:flex;gap:14px;align-items:center;justify-content:center}
.t16,.t32,.t48{display:inline-block;flex:none}.t16 svg{width:16px;height:16px;display:block}.t32 svg{width:32px;height:32px;display:block}.t48 svg{width:48px;height:48px;display:block}
.card-body{padding:14px 16px 16px;display:grid;gap:8px;flex:1;align-content:start}
.card-body>p:not(.terr){font-size:14px}
.card-top{display:flex;gap:8px;align-items:center}.card-top h3{margin-right:auto}
.pill{font:600 11px var(--f-mono);letter-spacing:.05em;padding:3px 8px;border-radius:999px;border:1px solid currentColor}
.pill.main{color:var(--primary)}.pill.bold{color:var(--brass-ink)}
.score{font:600 18px var(--f-mono);font-variant-numeric:tabular-nums}.score small{font-size:11px;color:var(--muted)}.score.big{font-size:28px}
.card-act{display:flex;gap:8px;align-items:center;margin-top:4px}
.btn-sm{font:600 13px var(--f-body);border:1px solid var(--primary);background:var(--primary);color:var(--on-primary);padding:5px 12px;border-radius:999px;cursor:pointer}
.btn-sm.ghost{background:transparent;color:var(--primary);margin-left:auto}
.anim-slot svg{width:34px;height:34px;display:block}.anim-slot .an-d{display:none}
.anim-slot{border-radius:6px;background:var(--stage-light);padding:2px}
[data-bg="dark"] .anim-slot{background:var(--stage-dark)}[data-bg="dark"] .anim-slot .an-l{display:none}[data-bg="dark"] .anim-slot .an-d{display:block}
.cuts summary{cursor:pointer;font-weight:600;padding:12px 0}
.cut-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px}
.cut{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:12px;display:grid;gap:6px;align-content:start}
.cut .pair{display:flex;gap:8px}.cut .pair span{flex:1;aspect-ratio:1;max-width:100%;border-radius:4px;overflow:hidden}
.cut .pair .l{background:var(--stage-light)}.cut .pair .m{background:#fff}.cut .pair svg{width:100%;height:100%;display:block}
.cut p{font-size:13.5px}.cut .x{font:600 12px var(--f-mono);color:var(--felt)}
:root[data-theme="dark"] .cut .x{color:#EF7E7C}
.tbl{overflow-x:auto;border:1px solid var(--line);border-radius:6px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
thead th{font:600 12px var(--f-body);color:var(--muted);vertical-align:bottom}
tbody th small{display:block;font:500 11px var(--f-mono);color:var(--muted)}
td.sc,td.tot{text-align:center;font-family:var(--f-mono)}td.tot{font-weight:700}
.sc.s5{background:color-mix(in srgb,var(--sig) 38%,transparent)}.sc.s4{background:color-mix(in srgb,var(--sig) 20%,transparent)}
.sc.s2,.sc.s1{color:var(--muted)}
.sep th,.sep td{border-top:2px solid var(--fg)}
.note{font-size:13.5px;color:var(--muted);margin-top:8px;max-width:80ch}
/* Top 3 */
.t3{border-top:2px solid var(--fg);padding-top:16px}
.t3-head{display:flex;gap:14px;align-items:center}
.rank{font:700 44px/1 var(--f-display);color:var(--brass-ink)}
.t3-why{max-width:75ch;margin:10px 0 16px}
.t3-kit{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.kit{border-radius:6px;display:grid;place-items:center;padding:18px;min-height:130px;border:1px solid var(--line)}
.kit.light{background:var(--stage-light)}.kit.dark{background:var(--stage-dark)}.kit.mono{background:#fff}
.kit.icons{background:var(--surface);display:flex;gap:12px;align-items:center;justify-content:center;flex-wrap:wrap}
.kit.icons small{width:100%;text-align:center;color:var(--muted)}
.kit-h svg{width:100%;max-width:300px;height:auto;display:block}.kit-v svg{height:110px;width:auto;display:block;max-width:100%}
.ic96 svg{width:96px;height:96px;display:block}.ic48 svg{width:48px;height:48px;display:block}
.mk-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:14px}
.mk{margin:0;display:grid;gap:6px;align-content:start}
.mk figcaption{font-size:13px;color:var(--muted)}
.mk-head{display:flex;align-items:center;gap:16px;padding:12px 16px;border-radius:6px;font-size:13px;overflow:hidden}
.mk-head.light{background:#FAFBF5;color:#0C231F;border:1px solid #D2D8CD}.mk-head.dark{background:#101F1C;color:#EAEAE1;border:1px solid #2C3F3B;margin-top:6px}
.mk-logo svg{height:36px;width:auto;display:block}
.mk-head nav{display:flex;gap:12px;margin-left:auto;white-space:nowrap;overflow:hidden}
.mk-cta{background:#006D61;color:#FCFCF8;padding:6px 12px;border-radius:999px;font-weight:600;white-space:nowrap}
.mk-head.dark .mk-cta{background:#5BC7B1;color:#041A17}
.mk-tabs{display:flex;gap:2px;padding:8px 8px 0;border-radius:6px 6px 0 0;font:12px system-ui,sans-serif}
.mk-tabs.light{background:#DEE3DA}.mk-tabs.dark{background:#1C2B28;margin-top:6px}
.tab{display:flex;align-items:center;gap:8px;padding:8px 12px;border-radius:8px 8px 0 0;color:#48615C;max-width:62%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mk-tabs.light .tab.on{background:#FEFFFC;color:#0C231F}.mk-tabs.dark .tab{color:#ADB4A7}.mk-tabs.dark .tab.on{background:#2C3F3B;color:#EAEAE1}
.fav svg{width:16px;height:16px;display:block}
.mk-slide{aspect-ratio:16/9;max-width:100%;background:#0C231F;color:#EAEAE1;border-radius:6px;padding:6% 7%;display:grid;grid-template-rows:1fr auto auto;gap:8px;align-items:center;justify-items:center}
.mk-v svg{height:min(130px,22vw);width:auto;display:block;max-width:100%}
.mk-sub{font-family:var(--f-display);font-size:clamp(13px,1.8vw,19px);text-align:center}
.mk-foot{display:flex;justify-content:space-between;width:100%;font:11px var(--f-mono);color:#ADB4A7;border-top:1px solid #2C3F3B;padding-top:8px}
.mk-stick-wrap{display:grid;place-items:center;padding:18px;background:repeating-linear-gradient(45deg,#D2D8CD 0 2px,transparent 2px 12px);border-radius:6px}
.mk-stick{width:min(270px,72vw);height:min(270px,72vw);flex:none;overflow:hidden;border-radius:50%;background:#F2F3EA;border:9px solid #FEFFFC;box-shadow:0 6px 18px rgba(12,35,31,.28);display:grid;place-items:center;align-content:center;gap:6px;padding:10%}
.st-sym svg{width:72px;height:72px;display:block}.st-wm svg{width:160px;height:auto;display:block;max-width:100%}.st-tag{font:500 10.5px var(--f-mono);color:#48615C;white-space:nowrap}
.files{margin-top:12px}.files summary{cursor:pointer;font-weight:600}.files li{margin:4px 0}
/* Hộp phóng to */
.ov{position:fixed;inset:0;z-index:20;background:color-mix(in srgb,var(--bg) 70%,transparent);backdrop-filter:blur(3px);display:grid;place-items:start center;overflow:auto;padding:calc(20px + env(safe-area-inset-top,0px)) max(12px,env(safe-area-inset-right,0px)) 24px max(12px,env(safe-area-inset-left,0px))}
.dl{background:var(--raised);border:1px solid var(--line);border-radius:8px;max-width:960px;width:100%;padding:20px;display:grid;gap:16px;box-shadow:0 12px 40px rgba(0,0,0,.25)}
.dl-close{justify-self:end;font:600 13px var(--f-body);background:transparent;border:1px solid var(--line);color:var(--fg);border-radius:999px;padding:5px 12px;cursor:pointer}
.dl-head{display:flex;justify-content:space-between;align-items:end;gap:12px}
.dl-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.dl-big{border-radius:6px;aspect-ratio:1;max-width:100%;padding:12%}.dl-big svg{width:100%;height:100%;display:block}
.dl-big.light,.dl-lock.light{background:var(--stage-light)}.dl-big.dark,.dl-lock.dark{background:var(--stage-dark)}.dl-big.mono{background:#fff}
.dl-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}.dl-lock{border-radius:6px;padding:16px}.dl-lock svg{width:100%;height:auto;display:block}
.dl-small{display:flex;gap:12px;align-items:center;flex-wrap:wrap;font-size:13px;color:var(--muted)}
.dl-small .lt{background:var(--stage-light);padding:3px}.dl-small .dk{background:var(--stage-dark);padding:3px}
.squint svg{width:48px;height:48px;display:block;filter:blur(2.4px);background:var(--stage-light)}
.dl-text{display:grid;grid-template-columns:auto minmax(0,1fr);gap:8px 16px;margin:0}.dl-text dt{font-weight:600;color:var(--muted)}.dl-text dd{margin:0;max-width:72ch}
.sc-mini{font-size:12px}.sc-mini th{font-weight:500;color:var(--muted)}
.path{font-size:13px;color:var(--muted)}
${animCss}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
@media (max-width:820px){.hero,.why,.terrs,.t3-kit,.mk-grid,.dl-grid{grid-template-columns:minmax(0,1fr)}.dl-row{grid-template-columns:1fr}.mk-head nav{display:none}.seg{margin-left:0}}
</style>

<div class="bar"><div class="bar-in">
  <nav class="tabs" aria-label="Trang"><a href="#tong-quan" data-view="tong-quan">12 logo</a><a href="#top-3" data-view="top-3">Top 3</a></nav>
  <div class="seg" role="group" aria-label="Nền xem logo">
    <button type="button" data-bgset="light" aria-pressed="true">Nền sáng</button><button type="button" data-bgset="dark" aria-pressed="false">Nền tối</button><button type="button" data-bgset="mono" aria-pressed="false">1 màu</button><button type="button" data-bgset="tiny" aria-pressed="false">16px</button>
  </div>
</div></div>

<main class="wrap" id="app" data-bg="light">
<div data-page="tong-quan">
  <header class="hero">
    <div><p class="eyebrow">Harmony Mentor · nhận diện · bản đề xuất 27/10/2026</p><h1>Mỗi logo là một sự thật của cây đàn piano</h1>
    <p>26 phác thảo SVG từ 6 lãnh thổ sáng tạo, lọc còn 12 bản: 8 bản dùng được ngay làm logo chính và 4 bản táo bạo kiểu triển lãm. Bấm vào logo để phóng to, dùng nút trên cùng để đổi nền, xem bản 1 màu hoặc xem ở 16px. Nhóm chọn xong thì mình mới đưa vào repo.</p></div>
    <div class="hero-mark">${sized(data.logos['hai-ba'].h.dark)}</div>
  </header>

  <section aria-labelledby="h-why">
    <div class="sec-head"><h2 id="h-why">Vì sao logo âm nhạc hay nhàm</h2></div>
    <div class="why">${INTRO.why.map((p) => `<p>${esc(p)}</p>`).join('')}</div>
  </section>

  <section aria-labelledby="h-terr">
    <div class="sec-head"><h2 id="h-terr">6 lãnh thổ sáng tạo</h2><p>Mỗi lãnh thổ gắn với một tác phẩm có thật, một câu chuyện piano, và một rủi ro cần tránh.</p></div>
    <div class="terrs">${TERRITORIES.map((t) => `<div class="terr-c"><span class="code">${t.code}</span><h3>${esc(t.name)}</h3><p class="ref">${esc(t.ref)}</p><p>${esc(t.story)}</p><dl><dt>Điểm dị</dt><dd>${esc(t.odd)}</dd><dt>Lớp ẩn</dt><dd>${esc(t.hidden)}</dd><dt>Rủi ro</dt><dd>${esc(t.risk)}</dd></dl></div>`).join('')}</div>
  </section>

  <section aria-labelledby="h-12">
    <div class="sec-head"><h2 id="h-12">12 logo hoàn thiện</h2><p>Điểm là tổng 7 tiêu chí, mỗi tiêu chí 1–5. Đây là đánh giá của người thiết kế, chưa thử với người dùng thật.</p></div>
    <p class="grid-label">DÙNG ĐƯỢC NGAY LÀM LOGO CHÍNH · 8</p>
    <div class="grid">${finals.filter((id) => LOGOS[id].kind === 'main').map(card).join('')}</div>
    <p class="grid-label">TÁO BẠO KIỂU TRIỂN LÃM · 4 (được dùng 12 màu nốt)</p>
    <div class="grid">${finals.filter((id) => LOGOS[id].kind === 'bold').map(card).join('')}</div>
  </section>

  <section aria-labelledby="h-score">
    <div class="sec-head"><h2 id="h-score">Bảng điểm 26 phác thảo</h2></div>
    <div class="tbl"><table><thead><tr><th scope="col">Phác thảo</th>${CRITERIA.map((c) => `<th scope="col">${c}</th>`).join('')}<th scope="col">Tổng</th></tr></thead>
    <tbody>${[...finals].sort((a, b) => sum(LOGOS[b].s) - sum(LOGOS[a].s)).map(scoreRow).join('')}${cuts.sort((a, b) => sum(LOGOS[b].s) - sum(LOGOS[a].s)).map((id, i) => scoreRow(id).replace('<tr>', i === 0 ? '<tr class="sep">' : '<tr>')).join('')}</tbody></table></div>
    <p class="note">Cách test cho từng bản: nheo mắt (làm mờ 2,4px), in 1 màu đen/trắng, favicon 16 và 32px, đặt trên nền tối, và in nhỏ trên slide. Bản giữ lại đều có tổng từ 25 điểm, bản bị loại đều dưới 23 hoặc dính danh sách cấm.</p>
  </section>

  <section aria-labelledby="h-cut">
    <details class="cuts"><summary id="h-cut">14 phác thảo bị loại và lý do</summary>
      <div class="cut-grid">${cuts.map((id) => `<div class="cut"><div class="pair"><span class="l">${data.sketches[id].light}</span><span class="m">${data.sketches[id].mono}</span></div><h3>${esc(LOGOS[id].name)}</h3><span class="x">LOẠI · ${sum(LOGOS[id].s)}/35 · Lãnh thổ ${LOGOS[id].t}</span><p>${esc(LOGOS[id].why)}</p></div>`).join('')}</div>
    </details>
  </section>

  <section aria-labelledby="h-wcag">
    <div class="sec-head"><h2 id="h-wcag">Độ tương phản của wordmark (WCAG 2.1)</h2><p>Tính bằng công thức độ sáng tương đối của WCAG từ mã HEX.</p></div>
    <div class="tbl"><table><thead><tr><th scope="col">Màu</th><th scope="col">Trên nền</th><th scope="col">Tỉ số</th><th scope="col">Kết quả</th></tr></thead><tbody>${contrast.map((r) => `<tr>${r.map((x) => `<td>${esc(x)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>
  </section>
</div>

<div data-page="top-3" hidden>
  <header class="hero"><div><p class="eyebrow">Đề xuất cho vị trí logo chính</p><h1>Top 3 và bộ file đầy đủ</h1><p>Mỗi bản có logo ngang và dọc, icon app, favicon, PNG nhiều cỡ, component React và 4 mockup. Xếp hạng theo điểm và theo độ phù hợp với người mới học.</p></div>
  <div class="hero-mark">${sized(data.logos['do-giua'].icon)}</div></header>
  ${top3Html}
</div>
</main>
${finals.map(detail).join('')}
<div class="ov" id="ov" hidden><div class="dl" role="dialog" aria-modal="true" aria-labelledby="dl-title"><button type="button" class="dl-close" id="dl-close">Đóng</button><div id="dl-body"></div></div></div>

<script>
(function(){
  var app=document.getElementById('app');
  function setBg(v){app.setAttribute('data-bg',v);document.querySelectorAll('[data-bgset]').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.bgset===v))});try{localStorage.setItem('hm-bg',v)}catch(e){}}
  document.querySelectorAll('[data-bgset]').forEach(function(b){b.addEventListener('click',function(){setBg(b.dataset.bgset)})});
  try{var s=localStorage.getItem('hm-bg');if(s)setBg(s)}catch(e){}
  function play(el){el.classList.remove('play');void el.getBoundingClientRect();el.classList.add('play')}
  document.querySelectorAll('[data-play]').forEach(function(b){b.addEventListener('click',function(){play(document.querySelector('.anim-slot[data-logo="'+b.dataset.play+'"]'))})});
  var ov=document.getElementById('ov'),body=document.getElementById('dl-body'),last=null;
  function open(id){last=document.activeElement;body.innerHTML=document.getElementById('tpl-'+id).innerHTML;body.querySelector('h2').id='dl-title';ov.hidden=false;
    body.querySelectorAll('.dl-big[data-logo]').forEach(play);
    var r=body.querySelector('[data-replay]');if(r)r.addEventListener('click',function(){body.querySelectorAll('.dl-big[data-logo]').forEach(play)});
    document.getElementById('dl-close').focus()}
  function close(){ov.hidden=true;body.innerHTML='';if(last)last.focus()}
  document.querySelectorAll('[data-open]').forEach(function(b){b.addEventListener('click',function(){open(b.dataset.open)})});
  document.getElementById('dl-close').addEventListener('click',close);
  ov.addEventListener('click',function(e){if(e.target===ov)close()});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!ov.hidden)close()});
  function route(){var v=location.hash==='#top-3'?'top-3':'tong-quan';document.querySelectorAll('[data-page]').forEach(function(p){p.hidden=p.dataset.page!==v});
    document.querySelectorAll('[data-view]').forEach(function(a){if(a.dataset.view===v)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')})}
  window.addEventListener('hashchange',function(){route();window.scrollTo(0,0)});route();
})();
</script>
`;
fs.writeFileSync(PAGE, html);

// Trang mockup riêng để chụp PNG (mỗi khung một ảnh)
const mk = `<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600&family=Fraunces:opsz,wght@9..144,500&family=IBM+Plex+Mono:wght@400;500&display=swap">`
  + html.match(/<style>[\s\S]*?<\/style>/)[0] + `<body style="background:#F2F3EA;margin:0"><main class="wrap" style="max-width:1100px">${TOP3.map((t) => mockups(t.id)).join('')}</main></body>`;
fs.writeFileSync(path.join(__dirname, 'mockup.html'), mk);
console.log('trang xong', (html.length / 1e6).toFixed(2), 'MB');

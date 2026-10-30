// Sinh component React Logo.tsx (Tailwind v4, màu qua biến --hm-logo-*) cho Top 3.
const fs = require('fs');
const path = require('path');
const { S } = require('./symbols');
const { palette } = require('./palette');
const { lockupH, lockupV } = require('./compose');
const { LOGOS, KIT } = require('./meta');
const TOP3 = KIT.map((id) => ({ id }));
const OUT = process.env.OUT || path.join(__dirname, '..');

const KEYS = ['ink', 'deep', 'sig', 'brass', 'brassText', 'felt', 'tint', 'hole', 'soft', 'knock', 'lacquer', 'edge', 'text'];
const cssName = (k) => `--hm-logo-${k.replace(/[A-Z]/g, (m) => '-' + m.toLowerCase())}`;

function cssPalette(notes) {
  const L = palette('light', { notes });
  const c = { ...L, uid: '__UID__' };
  for (const k of KEYS) c[k] = `var(${cssName(k)}, ${L[k]})`;
  return c;
}
// Đổi thuộc tính SVG sang JSX
function toJsx(s) {
  return s
    .replace(/\s(stroke|fill|clip|font|stop|text|dominant|vector)-([a-z]+)(?:-([a-z]+))?=/g, (m, a, b, c2) => ` ${a}${b[0].toUpperCase()}${b.slice(1)}${c2 ? c2[0].toUpperCase() + c2.slice(1) : ''}=`)
    .replace(/\sclass="/g, ' className="')
    .replace(/id="__UID__-([a-z]+)"/g, 'id={`${uid}-$1`}')
    .replace(/"url\(#__UID__-([a-z]+)\)"/g, '{`url(#${uid}-$1)`}')
    .replace(/maskUnits/g, 'maskUnits');
}
const vb = (a) => a.map((n) => +n.toFixed(2)).join(' ');

function css() {
  const L = palette('light'), D = palette('dark');
  const block = (p) => KEYS.map((k) => `  ${cssName(k)}: ${p[k]};`).join('\n');
  const anims = TOP3.map((t) => (S[t.id].anim || '').replace(/\.play /g, `.hm-logo.play[data-logo="${t.id}"] `)).join('\n');
  return `/* Màu logo Harmony Mentor — dán cạnh tokens.css. Logo đổi màu theo chế độ sáng/tối giống phần còn lại của app. */
:root {
${block(L)}
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
${block(D).replace(/^/gm, '  ')}
  }
}
:root[data-theme="dark"] {
${block(D)}
}
/* Chuyển động (thêm prop animate). Tắt hẳn khi người dùng bật "giảm chuyển động". */
${anims}
@media (prefers-reduced-motion: reduce) { .hm-logo * { animation: none !important; } }
`;
}

function tsx(id) {
  const m = LOGOS[id];
  const H = lockupH(id, cssPalette(m.notes)), V = lockupV(id, cssPalette(m.notes));
  const sym = S[id](cssPalette(m.notes));
  return `// Logo Harmony Mentor — phương án "${m.name}". File sinh tự động từ _nguon/gen_react.js, đừng sửa tay.
// Dùng: <Logo className="h-9 w-auto" />  ·  <Logo variant="bieu-tuong" className="size-8" />  ·  <Logo animate />
// Màu lấy từ biến --hm-logo-* trong logo.css, nên tự đổi theo chế độ sáng/tối.
import { useId } from "react";

type LogoProps = {
  variant?: "ngang" | "doc" | "bieu-tuong";
  animate?: boolean;
  title?: string;
  className?: string;
};

const VIEWBOX = { ngang: "${vb(H.vb)}", doc: "${vb(V.vb)}", "bieu-tuong": "0 0 100 100" } as const;

export function Logo({ variant = "ngang", animate = false, title = "Harmony Mentor", className }: LogoProps) {
  // id riêng cho clipPath/mask khi có nhiều logo trên cùng trang
  const uid = "hm" + useId().replace(/[^a-zA-Z0-9]/g, "");
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={VIEWBOX[variant]}
      role="img"
      aria-label={title}
      data-logo="${id}"
      className={["hm-logo", animate ? "play" : "", className ?? ""].join(" ").trim()}
    >
      <title>{title}</title>
      {variant === "ngang" && (<>${toJsx(H.inner)}</>)}
      {variant === "doc" && (<>${toJsx(V.inner)}</>)}
      {variant === "bieu-tuong" && (<>${toJsx(sym)}</>)}
    </svg>
  );
}
`;
}

// REPO_OUT=<thư mục>: sinh đúng hai file đang dùng trong app (frontend/src/components/brand/) cho bản nhóm chọn.
// Khác bản đề xuất: tên hàm HarmonyMentorLogo, tự import logo.css, và KHÔNG đổi màu theo prefers-color-scheme
// vì app chưa có chế độ tối (ADR-007).
if (process.env.REPO_OUT) {
  const { CHOSEN } = require('./meta');
  const t = tsx(CHOSEN)
    .replace(/^\/\/ Logo Harmony Mentor — .*$/m, `// Logo chính thức Harmony Mentor "${LOGOS[CHOSEN].name}" (ADR-007). File sinh từ docs/thuong-hieu/_nguon/gen_react.js (REPO_OUT), đừng sửa tay.`)
    .replace('export function Logo(', 'export function HarmonyMentorLogo(')
    .replace(/<Logo /g, '<HarmonyMentorLogo ')
    .replace('import { useId } from "react";', 'import { useId } from "react";\nimport "./logo.css";');
  let c = css()
    .replace(/@media \(prefers-color-scheme: dark\) \{\n  :root:not\(\[data-theme="light"\]\) \{\n[\s\S]*?\n  \}\n\}\n/, '')
    .replace(/^\/\* Màu logo Harmony Mentor — .*\*\/$/m, '/* Màu logo Harmony Mentor (ADR-007).\n   App chưa có chế độ tối, nên logo KHÔNG tự đổi theo prefers-color-scheme (chữ ngà sẽ chìm trên nền sáng).\n   Khi app làm chế độ tối bằng <html data-theme="dark">, khối bên dưới tự áp dụng. */');
  c = c.split('\n').filter((l) => (!l.includes('data-logo=') || l.includes(`data-logo="${CHOSEN}"`)) && (!l.startsWith('@keyframes') || (S[CHOSEN].anim || '').includes(l))).join('\n').replace(/\n{3,}/g, '\n');
  fs.mkdirSync(process.env.REPO_OUT, { recursive: true });
  fs.writeFileSync(path.join(process.env.REPO_OUT, 'HarmonyMentorLogo.tsx'), t);
  fs.writeFileSync(path.join(process.env.REPO_OUT, 'logo.css'), c);
  console.log('đã sinh file cho app:', CHOSEN);
  process.exit(0);
}

for (const t of TOP3) {
  const dir = path.join(OUT, 'react', t.id);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'Logo.tsx'), tsx(t.id));
  fs.writeFileSync(path.join(dir, 'logo.css'), css());
}
console.log('react xong');

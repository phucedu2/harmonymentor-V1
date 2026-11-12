const fs = require('fs');
const { S } = require('./symbols');
const { palette } = require('./palette');
const ids = Object.keys(S);
const sym = (id, mode, opt) => { const c = palette(mode, opt); return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">${S[id](c)}</svg>`; };
let h = `<html><body style="margin:0;font:12px sans-serif;background:#ccc"><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:8px">`;
for (const id of ids) {
  const notes = ['duong-cong','cuon-tien-trinh'].includes(id);
  h += `<div style="background:#fff;padding:6px"><b>${id}</b><div style="display:flex;gap:6px;align-items:end">
  <div style="background:#F2F3EA;width:120px;height:120px">${sym(id,'light',{notes})}</div>
  <div style="background:#081613;width:120px;height:120px">${sym(id,'dark',{notes})}</div>
  <div style="background:#fff;width:60px;height:60px">${sym(id,'mono')}</div>
  <div style="background:#F2F3EA;width:32px;height:32px">${sym(id,'light',{notes})}</div>
  <div style="background:#F2F3EA;width:16px;height:16px">${sym(id,'light',{notes})}</div>
  <div style="background:#F2F3EA;width:60px;height:60px;filter:blur(2.5px)">${sym(id,'light',{notes})}</div></div></div>`;
}
fs.writeFileSync('sheet.html', h + '</div></body></html>');

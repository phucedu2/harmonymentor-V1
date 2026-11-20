import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import fs from 'fs';
const B='http://localhost:4173', O='/tmp/claude-0/d4/brand'; fs.mkdirSync(O,{recursive:true});
const axeSrc=fs.readFileSync('/tmp/claude-0/tools/node_modules/axe-core/axe.min.js','utf8');
const br=await chromium.launch(); const res={};
const ctx=await br.newContext({viewport:{width:1440,height:900},deviceScaleFactor:1});
const p=await ctx.newPage();
const email=`br${Date.now()}@vd.vn`;
await p.request.post(B+'/api/v1/auth/register',{data:{email,password:'matkhau123',display_name:'Brand'}});
await p.goto(B+'/dang-nhap');await p.fill('input[type=email]',email);await p.fill('input[type=password]','matkhau123');
await p.locator('form button[type=submit]').click();await p.waitForURL(/\/app/);
const pages=[['trang-chu','/'],['tong-quan','/app'],['hoc','/app/hoc'],['composition','/app/composition'],['luyen-tap','/app/luyen-tap']];
for (const brand of ['dong-gi','san-khau','giay-nhac']) for (const theme of ['light','dark']) for (const [n,u] of pages) {
  await p.goto(B+u+'?brand='+brand,{waitUntil:'networkidle'});
  await p.evaluate(t=>{t==='dark'?localStorage.setItem('hm-theme','dark'):localStorage.removeItem('hm-theme')},theme);
  await p.reload({waitUntil:'networkidle'}); await p.waitForTimeout(1200);
  await p.screenshot({path:`${O}/${brand}_${theme}_${n}.jpg`,quality:80,type:'jpeg'});
  await p.evaluate(axeSrc);
  const r=await p.evaluate(async()=>(await window.axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})).violations.map(v=>v.id+':'+v.nodes.length+':'+v.nodes.slice(0,2).map(x=>x.target.join(' ')).join('|')));
  res[`${brand}/${theme}/${n}`]=r; console.log(brand,theme,n,JSON.stringify(r));
}
// 390 px sáng
await ctx.close(); const c2=await br.newContext({viewport:{width:390,height:844},deviceScaleFactor:1}); const q=await c2.newPage();
for (const brand of ['dong-gi','san-khau','giay-nhac']) { await q.goto(B+'/?brand='+brand,{waitUntil:'networkidle'}); await q.waitForTimeout(1200); await q.screenshot({path:`${O}/${brand}_light_trang-chu-390.jpg`,quality:80,type:'jpeg'}); }
fs.writeFileSync(O+'/axe.json',JSON.stringify(res,null,1)); await br.close();

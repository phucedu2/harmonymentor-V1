#!/usr/bin/env bash
# Dựng lại toàn bộ thư mục logo-di từ đầu
set -e
cd "$(dirname "$0")"
[ -f fonts/Fraunces-600.ttf ] || bash fetch_fonts.sh
OUT=.. node build.js
node -e "const {LOGOS,TOP3}=require('./meta');require('fs').writeFileSync('ids.json',JSON.stringify({finals:Object.keys(LOGOS).filter(k=>LOGOS[k].kind!=='cut'),top3:require('./meta').KIT}))"
python3 export_png.py ..
OUT=.. node gen_react.js
PAGE=../xem-truoc.html node gen_page.js
mkdir -p ../mockup && node shots.js ..

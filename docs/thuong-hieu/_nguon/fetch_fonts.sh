#!/usr/bin/env bash
# Tải 3 font gốc (giấy phép SIL OFL) từ kho Google Fonts trên GitHub vào ./fonts
set -e
cd "$(dirname "$0")"; mkdir -p fonts; B=https://raw.githubusercontent.com/google/fonts/main/ofl
curl -sSL -o fonts/Fraunces.ttf "$B/fraunces/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf"
curl -sSL -o fonts/Fraunces-Italic.ttf "$B/fraunces/Fraunces-Italic%5BSOFT,WONK,opsz,wght%5D.ttf"
for w in Light Regular Medium SemiBold Bold ExtraBold; do curl -sSL -o fonts/BeVietnamPro-$w.ttf "$B/bevietnampro/BeVietnamPro-$w.ttf"; done
for w in Regular Medium SemiBold Bold; do curl -sSL -o fonts/IBMPlexMono-$w.ttf "$B/ibmplexmono/IBMPlexMono-$w.ttf"; done
python3 make_instances.py

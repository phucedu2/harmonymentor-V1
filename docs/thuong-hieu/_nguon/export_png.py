# Xuất PNG/ICO từ SVG đã dựng. Chạy: python3 export_png.py <thư mục logo-di>
import sys, os, re, io, json
import cairosvg
from PIL import Image
OUT = sys.argv[1]
meta = json.load(open(os.path.join(os.path.dirname(__file__), 'ids.json')))
def png(svg_path, dst, width=None, height=None, bg=None):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    cairosvg.svg2png(url=svg_path, write_to=dst, output_width=width, output_height=height, background_color=bg)
def square_icon(svg_path):
    # apple-touch-icon: iOS tự bo góc, nên bỏ bo góc và lấp kín nền
    s = open(svg_path).read()
    return re.sub(r'<rect width="100" height="100" rx="22"', '<rect width="100" height="100" rx="0"', s, count=1)
for id in meta['finals']:
    sv = f'{OUT}/svg/{id}'
    for n in (16, 32):
        png(f'{sv}/app-icon.svg', f'{OUT}/png/{id}/favicon-{n}.png', n, n)
    png(f'{sv}/bieu-tuong-sang.svg', f'{OUT}/png/{id}/bieu-tuong-sang-512.png', 512, 512)
    png(f'{sv}/ngang-sang.svg', f'{OUT}/png/{id}/ngang-sang-1200.png', 1200)
for id in meta['top3']:
    sv = f'{OUT}/svg/{id}'; pd = f'{OUT}/png/{id}'; fd = f'{OUT}/favicon/{id}'
    for n in (16, 32, 48, 64, 128, 192, 256, 512, 1024):
        png(f'{sv}/app-icon.svg', f'{pd}/icon-{n}.png', n, n)
    for mode in ('sang', 'toi', 'den', 'trang'):
        for wd in (600, 1200, 2400):
            png(f'{sv}/ngang-{mode}.svg', f'{pd}/ngang-{mode}-{wd}.png', wd)
        png(f'{sv}/doc-{mode}.svg', f'{pd}/doc-{mode}-800.png', 800)
        png(f'{sv}/bieu-tuong-{mode}.svg', f'{pd}/bieu-tuong-{mode}-1024.png', 1024, 1024)
    os.makedirs(fd, exist_ok=True)
    sq = square_icon(f'{sv}/app-icon.svg')
    cairosvg.svg2png(bytestring=sq.encode(), write_to=f'{fd}/apple-touch-icon.png', output_width=180, output_height=180)
    for n in (192, 512):
        png(f'{sv}/app-icon.svg', f'{fd}/icon-{n}.png', n, n)
    imgs = [Image.open(io.BytesIO(cairosvg.svg2png(url=f'{sv}/app-icon.svg', output_width=n, output_height=n))) for n in (16, 32, 48)]
    imgs[2].save(f'{fd}/favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)], append_images=imgs[:2])
    open(f'{fd}/favicon.svg', 'w').write(open(f'{sv}/favicon.svg').read())
print('png xong')

# Fraunces là font biến thiên; cắt ra các bản tĩnh (opsz 96, SOFT 50, WONK 0) để opentype.js đọc được.
import os
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
for ital in ('', '-Italic'):
    for w in (300, 400, 500, 600, 700, 800, 900):
        f = TTFont(os.path.join(D, f'Fraunces{ital}.ttf'))
        instantiateVariableFont(f, {'wght': w, 'opsz': 96, 'SOFT': 50, 'WONK': 0}).save(os.path.join(D, f'Fraunces{ital}-{w}.ttf'))

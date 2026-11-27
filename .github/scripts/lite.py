"""Lite build (smaller download for older phones): every picture over 512 px in godot/assets is halved (a quarter of
the memory and download), and godot/lite.cfg makes the game start on LOW graphics. Run on a copy of the project in CI.
usage: python3 lite.py <godot dir>"""
import os, sys
from PIL import Image
G = sys.argv[1]; KEEP = ('livery_digits.png', 'minimap.png', 'icon.png'); n = 0; saved = 0
for root, _, files in os.walk(os.path.join(G, 'assets')):
    for f in files:
        if not f.lower().endswith(('.png', '.jpg', '.jpeg')) or f in KEEP: continue
        p = os.path.join(root, f); im = Image.open(p)
        if max(im.size) <= 512: continue
        b = os.path.getsize(p); im = im.resize((max(1, im.size[0] // 2), max(1, im.size[1] // 2)), Image.LANCZOS)
        if f.lower().endswith('.png'): im.save(p, optimize=True)
        else: im.convert('RGB').save(p, quality=88)
        n += 1; saved += b - os.path.getsize(p)
open(os.path.join(G, 'lite.cfg'), 'w').write('[lite]\nlevel=0\n')
print('lite: %d pictures halved, %.1f MB smaller on disk' % (n, saved / 1048576))

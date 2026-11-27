"""Livery pictures (RGBA, transparent where the paint shows): Porto 'Aurelia Parcel' sides, Vela taxi doors and roof sign.
python3 livery_tex.py <out dir>"""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp'
F = '/usr/share/fonts/opentype/inter/'
TEAL, AMBER, INK = (18, 122, 134, 255), (240, 169, 46, 255), (43, 58, 64, 255)

def crs(pts, n=24):
    P = np.array(pts, float); P = np.vstack([P[0], P, P[-1]]); out = []
    for i in range(1, len(P) - 2):
        for t in np.linspace(0, 1, n, endpoint=False):
            p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2]); return out

def spaced(dr, xy, txt, font, fill, track, anchor_right=False):
    w = sum(dr.textlength(c, font=font) for c in txt) + track * (len(txt) - 1); x, y = xy
    if anchor_right: x -= w
    for c in txt: dr.text((x, y), c, font=font, fill=fill, anchor='ls'); x += dr.textlength(c, font=font) + track

def porto():
    S0, S1, Z0, Z1, k = 2.0, 5.10, 0.76, 1.62, 640
    W, Hh = int((S1 - S0) * k), int((Z1 - Z0) * k)
    px = lambda s, z: ((s - S0) * k, (Z1 - z) * k)
    g = Image.new('RGBA', (W, Hh), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    top = crs([(2.0, 0.765), (3.2, 0.80), (4.3, 0.92), (5.11, 1.12)]); bot = crs([(5.115, 0.92), (4.3, 0.79), (3.2, 0.755), (2.0, 0.75)])
    d.polygon([px(*p) for p in top + bot], fill=TEAL)
    d.line([px(*p) for p in crs([(2.6, 0.83), (3.6, 0.87), (4.5, 0.99), (5.115, 1.18)])], fill=AMBER, width=int(0.025 * k), joint='curve')
    cx, cy = px(2.20, 1.29); r = 0.07 * k; d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=AMBER)
    big = ImageFont.truetype(F + 'Inter-Black.otf', int(0.27 * k)); small = ImageFont.truetype(F + 'Inter-Bold.otf', int(0.12 * k))
    for side, gl in (('L', g), ('R', g.transpose(Image.FLIP_LEFT_RIGHT))):
        im = gl.copy(); dr = ImageDraw.Draw(im)
        x1, yb = px(2.34, 1.20); x2, yb2 = px(2.36, 1.00)
        if side == 'L': spaced(dr, (x1, yb), 'AURELIA', big, TEAL, 0.01 * k); spaced(dr, (x2, yb2), 'PARCEL · SAME DAY', small, INK, 0.035 * k)
        else:
            xa = W - x1; xb = W - x2
            spaced(dr, (xa, yb), 'AURELIA', big, TEAL, 0.01 * k, True); spaced(dr, (xb, yb2), 'PARCEL · SAME DAY', small, INK, 0.035 * k, True)
        im.save(f'{OUT}/porto_livery_{side}.png')
    return (S0, S1, Z0, Z1)

def taxi():
    # door band: checker (two rows) under the feature line, AURELIA TAXI on the front door, fleet number on the rear door
    S0, S1, Z0, Z1, k = 1.40, 3.42, 0.44, 0.84, 640
    W, Hh = int((S1 - S0) * k), int((Z1 - Z0) * k)
    px = lambda s, z: ((s - S0) * k, (Z1 - z) * k)
    line = [(1.42, 0.828), (2.4, 0.845), (3.40, 0.865)]
    zf = lambda x: line[0][1] + (x - line[0][0]) * (line[2][1] - line[0][1]) / (line[2][0] - line[0][0]) - 0.035
    big = ImageFont.truetype(F + 'Inter-Black.otf', int(0.085 * k)); small = ImageFont.truetype(F + 'Inter-Bold.otf', int(0.05 * k))
    for side in ('L', 'R'):
        im = Image.new('RGBA', (W, Hh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        n = 0; x = 1.44; w = 0.06
        while x + w <= 3.36:
            if not (2.40 < x + w / 2 < 2.48):
                for row in (0, 1):
                    if (n + row) % 2 == 0:
                        z0 = zf(x) - row * 0.045; z1 = zf(x + w) - row * 0.045
                        d.polygon([px(x, z0), px(x + w, z1), px(x + w, z1 - 0.045), px(x, z0 - 0.045)], fill=(17, 18, 20, 255))
            x += w; n += 1
        if side == 'R': im = im.transpose(Image.FLIP_LEFT_RIGHT); d = ImageDraw.Draw(im); mx = lambda s: W - (s - S0) * k
        else: mx = lambda s: (s - S0) * k
        for s_c, txt, f, z_ in ((1.92, 'AURELIA TAXI', big, 0.58), (2.95, 'T·104', big, 0.58), (1.92, 'day and night · all over the island', small, 0.50)):
            d.text((mx(s_c), (Z1 - z_) * k), txt, font=f, fill=(17, 17, 17, 255) if f is big else (58, 44, 6, 255), anchor='ms')
        im.save(f'{OUT}/taxi_doors_{side}.png')
    # roof sign faces: lit cream with TAXI
    im = Image.new('RGBA', (512, 160), (255, 243, 196, 255)); d = ImageDraw.Draw(im)
    d.text((256, 82), 'TAXI', font=ImageFont.truetype(F + 'Inter-Black.otf', 118), fill=(17, 17, 17, 255), anchor='mm'); im.save(f'{OUT}/taxi_sign.png')
    return (S0, S1, Z0, Z1)

if __name__ == '__main__':
    print(porto(), taxi())

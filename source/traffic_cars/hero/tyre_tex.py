"""Tyre textures for the traffic cars: tyre_basecolor.png and tyre_normal.png (1024 x 1024, OpenGL/glTF normal convention).

UV layout (shared with tyre_detail.py):
  V 0.00-0.50  sidewall: V runs from the bead (0.02) to the shoulder (0.48); U = SIDE_REP repeats round the tyre
  V 0.50-1.00  tread:    V runs across the width (0.52 inner edge -> 0.98 outer edge); U = PITCHES / TEX_PITCHES repeats
The geometric circumferential grooves sit at TREAD_GROOVES (fraction of the half width); the map adds the lateral
shoulder slots, rib sipes, a centre sipe line, sidewall lettering, a rib line and shoulder serrations.
Run: python3 tyre_tex.py [outdir]"""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

N = 1024
TEX_PITCHES = 4                      # tread pitches across one texture width
TREAD_GROOVES = (-0.44, 0.44)        # x of the modelled grooves (x = w / half tread width)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
SIDE_M = (0.85, 0.105)               # metres covered by the sidewall band (half circumference, radial height)
TREAD_M = (0.52, 0.150)              # metres covered by the tread band (4 pitches, tread width)

def blur(a, s): return ndimage.gaussian_filter(a, s, mode='wrap')

def tread_height():
    """Height in metres (0 = tread face, negative = cut in), 512 rows x N cols; row 0 = V 0.50 (inner edge)."""
    h, w = N // 2, N
    v = (np.arange(h) + 0.5) / h; x = -1 + 2 * (v - 0.04) / 0.92          # band row -> x across the tread
    u = (np.arange(w) + 0.5) / w * TEX_PITCHES                           # in pitches
    U, X = np.meshgrid(u, x)
    H = np.zeros((h, w))
    ax = np.abs(X)
    # shoulder slots: open at the shoulder, run in to |x| = 0.58, swept slightly
    ph = (U + 0.10 * (ax - 0.58)) % 1.0
    slot = (np.abs(ph - 0.5) < 0.085) & (ax > 0.58)
    H[slot] = -0.0065
    # a sipe through the middle of each shoulder block, closed at the outer end
    ph2 = (U + 0.10 * (ax - 0.58) + 0.5) % 1.0
    H[(np.abs(ph2 - 0.5) < 0.018) & (ax > 0.62) & (ax < 0.93)] = -0.004
    # middle ribs (between the modelled grooves and the slots): short angled sipes from each groove
    for g in TREAD_GROOVES:
        side = np.sign(g); d = (X - g) * side                             # distance outward from the groove
        ph3 = (U * 2 + 0.9 * d) % 1.0
        H[(np.abs(ph3 - 0.5) < 0.04) & (d > 0.10) & (d < 0.17)] = -0.004
    # centre rib: a shallow straight sipe line plus diagonal sipes
    H[np.abs(X) < 0.018] = np.minimum(H[np.abs(X) < 0.018], -0.003)
    ph4 = (U * 2 + 1.6 * X) % 1.0
    H[(np.abs(ph4 - 0.5) < 0.035) & (np.abs(X) < 0.36) & (np.abs(X) > 0.04)] = -0.0035
    # the modelled grooves and the band edges stay flat in the map
    for g in TREAD_GROOVES: H[np.abs(X - g) < 0.10] = 0
    H[ax > 1.0] = 0
    H = blur(H, (1.6, 2.4))
    return H

def sidewall_height():
    """Height in metres (+ = raised), 512 rows x N cols; row 0 = V 0.0 (bead side)."""
    h, w = N // 2, N
    t = (np.arange(h) + 0.5) / h; t = (t - 0.04) / 0.92                    # 0 bead .. 1 shoulder
    H = np.zeros((h, w))
    T = np.repeat(t[:, None], w, 1)
    # thin raised circumferential ribs
    for c, wd in ((0.20, 0.010), (0.72, 0.008), (0.76, 0.008)):
        H += 0.0004 * np.exp(-((T - c) / wd) ** 2)
    # shoulder serrations: radial ribs that fade towards the sidewall
    uu = np.arange(w)[None, :]
    ser = (np.abs(((uu % 10) - 5)) < 2).astype(float) * np.clip((T - 0.82) / 0.08, 0, 1) * (T < 1.0)
    H += 0.0006 * ser
    # lettering (raised 0.6 mm): drawn straight, the UV mapping bends it round the wheel
    img = Image.new('L', (w, h), 0); dr = ImageDraw.Draw(img)
    big = ImageFont.truetype(FONT, 92); small = ImageFont.truetype(FONT, 40)
    def text(s, f, cx, ct):
        bb = dr.textbbox((0, 0), s, font=f); tw, th = bb[2] - bb[0], bb[3] - bb[1]
        dr.text((cx - tw / 2 - bb[0], ct * h - th / 2 - bb[1]), s, font=f, fill=255)
    text('AURELIA', big, w * 0.30, 0.47)
    text('TOURING', small, w * 0.66, 0.40); text('225/45 R17 91W', small, w * 0.66, 0.54)
    text('M+S', small, w * 0.90, 0.47)
    L = np.asarray(img.filter(ImageFilter.GaussianBlur(1.3)), float)[::-1] / 255.0   # rows run bead->shoulder, letters stand on the bead side
    H += 0.0006 * L
    return H, L

def normals(H, mx, my):
    """H rows = increasing V (image will be flipped so V goes up). mx, my = metres per pixel along U and V."""
    dHdu = (np.roll(H, -1, 1) - np.roll(H, 1, 1)) / (2 * mx)
    dHdv = np.zeros_like(H); dHdv[1:-1] = (H[2:] - H[:-2]) / (2 * my)
    n = np.stack([-dHdu, -dHdv, np.ones_like(H)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n

def main(out):
    Ht = tread_height(); Hs, L = sidewall_height()
    ns = normals(Hs, SIDE_M[0] / N, SIDE_M[1] / (N // 2))
    nt = normals(Ht, TREAD_M[0] / N, TREAD_M[1] / (N // 2))
    n = np.concatenate([ns, nt], 0)[::-1]                                  # image row 0 = V 1.0
    Image.fromarray(np.uint8(np.clip((n * 0.5 + 0.5) * 255 + 0.5, 0, 255))).save(os.path.join(out, 'tyre_normal.png'))
    # base colour (sRGB): rubber black, tread face a touch lighter and dusty, cut-ins darker, letters matte grey
    lin = np.full((N, N), 0.028)
    side = np.full((N // 2, N), 0.026) + 0.022 * L
    tread = 0.034 + 0.10 * np.clip(Ht, -0.006, 0) / 0.006 * 0.12
    rng = np.random.default_rng(7); tread = tread * (1 + 0.08 * blur(rng.standard_normal(tread.shape), 2))
    lin = np.concatenate([side, tread], 0)[::-1]
    srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(np.clip(lin, 0, 1), 1 / 2.4) - 0.055)
    Image.fromarray(np.uint8(np.clip(srgb * 255 + 0.5, 0, 255))).convert('RGB').save(os.path.join(out, 'tyre_basecolor.png'))
    print('tyre textures ->', out)

if __name__ == '__main__': main(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__)))

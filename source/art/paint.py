"""Painterly finish for concept renders: Kuwahara (oil-paint) smoothing, edge accents, warm/teal grade, soft vignette."""
import numpy as np
from PIL import Image, ImageFilter


def box(a, r):
    """Mean over a (2r+1)^2 window via summed-area tables (edge padded)."""
    p = np.pad(a, ((r + 1, r), (r + 1, r)) + ((0, 0),) * (a.ndim - 2), mode='edge')
    c = p.cumsum(0).cumsum(1); k = 2 * r + 1
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def kuwahara(img, r=3):
    a = img.astype(np.float32); l = a.mean(2)
    m = box(a, r); s = box(l * l, r) - box(l, r) ** 2
    H, W = l.shape; best = None; bv = None
    for dy in (-r, r):
        for dx in (-r, r):
            ys = slice(max(0, dy), H + min(0, dy)); yd = slice(max(0, -dy), H + min(0, -dy)); xs = slice(max(0, dx), W + min(0, dx)); xd = slice(max(0, -dx), W + min(0, -dx))
            mm = np.empty_like(a); vv = np.full((H, W), 1e9, np.float32); mm[:] = a
            mm[yd, xd] = m[ys, xs]; vv[yd, xd] = s[ys, xs]
            if best is None: best, bv = mm, vv
            else:
                sel = vv < bv; best[sel] = mm[sel]; bv = np.minimum(bv, vv)
    return best


def finish(src, dst, r=2, night=False):
    im = Image.open(src).convert('RGB'); a = np.asarray(im, np.float32) / 255.0
    k = kuwahara(a, r)
    e = np.asarray(im.convert('L').filter(ImageFilter.FIND_EDGES), np.float32) / 255.0
    k = k * (1 - np.clip(e[..., None] * 0.25, 0, 0.1))                                  # gentle ink on strong edges
    l = k.mean(2, keepdims=True)
    if not night: warm, cool = np.array([1.05, 1.01, 0.94]), np.array([0.97, 1.0, 1.05])
    else: warm, cool = np.array([1.08, 0.98, 0.86]), np.array([0.85, 0.95, 1.12])
    t = np.clip((l - 0.2) / 0.6, 0, 1); k = k * (cool * (1 - t) + warm * t)
    k = np.clip(k * 1.04, 0, 1); k = (k - 0.5) * 1.05 + 0.5; k = np.clip(k, 0, 1)
    H, W = l.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]; v = 1 - 0.12 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.4
    k = k * v[..., None]
    rng = np.random.default_rng(1); k = k + (rng.random((H, W, 1)) - 0.5) * 0.018           # fine paper grain
    Image.fromarray((np.clip(k, 0, 1) * 255).astype(np.uint8)).save(dst, quality=93)


if __name__ == '__main__':
    import sys, glob, os
    for f in sorted(glob.glob(sys.argv[1] + '/*.png')):
        out = f.replace('.png', '_paint.jpg'); finish(f, out, 2, 'night' in f); print(out)

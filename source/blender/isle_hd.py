"""Texture up-resolution for Aurelia Island: every 512 px photo map is rebuilt at 1024 px. Colour maps are enlarged with Lanczos,
sharpened, and given new fine grain synthesised at full resolution (tileable FFT noise driven by the photo's own luminance), and
normal maps are rebuilt by combining the enlarged photo normal with a normal derived from that fine grain, so close-up surfaces
carry real high-frequency detail instead of blur. Results are cached in photo/hd/."""
import os
import numpy as np
from PIL import Image, ImageFilter
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photo')
HD = os.path.join(D, 'hd'); os.makedirs(HD, exist_ok=True)
SIZE = 1024
SIZES = {'Color': 2048, 'NormalGL': 1024, 'Roughness': 1024}


def _noise(n, beta, seed):
    r = np.random.default_rng(seed).normal(size=(n, n)); fx = np.fft.fftfreq(n)[:, None]; fy = np.fft.fftfreq(n)[None, :]
    f = np.hypot(fx, fy); f[0, 0] = 1; a = np.fft.ifft2(np.fft.fft2(r) / f ** beta).real; a -= a.mean(); return a / (np.abs(a).max() + 1e-9)


def _grain(seed, n=SIZE):
    """Tileable fine grain: two octaves of high-frequency noise (sub-millimetre speckle and small pits)."""
    return 0.65 * _noise(n, 0.35, seed) + 0.35 * _noise(n, 0.8, seed + 1)


def upres(name, kind, arr):
    """arr: float RGBA (h, w, 4) in 0..1, row 0 at the top (as decoded). Returns the 1024 version, same convention."""
    S_ = SIZES.get(kind, SIZE); f = os.path.join(HD, '%s_%s_%d.npy' % (name, kind, S_))
    if os.path.exists(f): return np.load(f).astype(float) / 255.0
    h, w = arr.shape[:2]; W2, H2 = S_, int(round(S_ * h / w))
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    big = np.asarray(im.resize((W2, H2), Image.LANCZOS), float) / 255.0
    seed = sum(map(ord, name)) % 997; g = _grain(seed, S_)[:H2, :W2]
    if kind == 'Color':
        rgb = Image.fromarray((big[..., :3] * 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(radius=1.6 * S_ / 1024, percent=75, threshold=2))
        rgb = np.asarray(rgb, float) / 255.0; lum = rgb.mean(2, keepdims=True)
        out = np.clip(rgb * (1.0 + 0.16 * g[..., None] * (0.55 + 0.9 * lum)), 0, 1)                     # grain stronger on lit parts, like real aggregate
        big = np.dstack([out, big[..., 3]])
    elif kind == 'NormalGL':
        n = big[..., :3] * 2 - 1; gy, gx = np.gradient(g * 0.9)
        dn = np.dstack([-gx * 6.0, gy * 6.0, np.ones_like(gx)]); dn /= np.linalg.norm(dn, axis=2, keepdims=True)
        t = n + np.dstack([dn[..., 0], dn[..., 1], np.zeros_like(gx)]); t[..., 2] = n[..., 2]; t /= np.linalg.norm(t, axis=2, keepdims=True)   # whiteout-style blend
        big = np.dstack([t * 0.5 + 0.5, big[..., 3]])
    elif kind == 'Roughness':
        big = np.dstack([np.clip(big[..., :3] + 0.05 * g[..., None], 0, 1), big[..., 3]])
    np.save(f, (np.clip(big, 0, 1) * 255).astype(np.uint8)); return big

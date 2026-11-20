"""Ground textures for Aurelia Island, one per kind of ground (1024 px, tiling). Each returns (rgb float array, height array)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from isle_lib import fft_noise
N = 1024


def _strokes(seed, n, lmin, lmax, spread, base, lo, hi, width=1, blur=0.6):
    r = np.random.default_rng(seed); im = Image.new('L', (N, N), base); d = ImageDraw.Draw(im)
    x = r.uniform(0, N, n); y = r.uniform(0, N, n); a = r.normal(np.pi / 2, spread, n) if spread < 3 else r.uniform(0, np.pi, n); ln = r.uniform(lmin, lmax, n); v = r.uniform(lo, hi, n)
    dx = np.cos(a) * ln; dy = np.sin(a) * ln
    for i in range(n):
        for ox in (0, -N):
            for oy in (0, -N): d.line([(x[i] + ox, y[i] + oy), (x[i] + ox + dx[i], y[i] + oy + dy[i])], fill=int(v[i]), width=width)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(blur)), float) / 255.0


def grass():
    s = _strokes(1, 70000, 5, 13, 0.55, 150, 95, 235); n1 = fft_noise(N, 1.6, 101); n2 = fft_noise(N, 0.9, 102)
    l = np.clip(s * (0.86 + 0.3 * (n1 - 0.5)) + 0.12 * (n2 - 0.5), 0, 1) * 1.62; cl = np.clip((fft_noise(N, 2.0, 103) - 0.6) * 5, 0, 1)
    return np.clip(np.dstack([l * (1 + 0.05 * cl), l * (1 + 0.02 * cl), l * (0.92 - 0.1 * cl)]), 0, 1), s


def forest():
    s = _strokes(2, 42000, 7, 18, 9, 120, 60, 215); tw = _strokes(3, 500, 30, 80, 9, 255, 70, 120, 2, 0.4); n1 = fft_noise(N, 1.5, 111)
    l = np.clip(s * np.minimum(tw + 0.15, 1) * (0.85 + 0.35 * (n1 - 0.5)), 0, 1) * 2.0; moss = np.clip((fft_noise(N, 1.9, 112) - 0.52) * 5, 0, 1)
    return np.clip(np.dstack([l * (1.0 - 0.25 * moss), l * (0.86 + 0.1 * moss), l * (0.66 - 0.1 * moss)]), 0, 1), s * tw


def field():
    v, u = np.mgrid[0:N, 0:N] / N; n1 = fft_noise(N, 1.2, 121); n2 = fft_noise(N, 0.3, 122)
    ridge = np.sin(2 * np.pi * (16 * u + 0.06 * (n1 - 0.5))) * 0.5 + 0.5; tuft = np.clip(np.sin(2 * np.pi * 40 * v + 9 * n1) * 0.5 + 0.5, 0, 1) * ridge
    l = 0.72 + 0.24 * ridge ** 1.5 + 0.1 * tuft + 0.12 * (n2 - 0.5)
    return np.clip(np.dstack([l, l, l * 0.94]), 0, 1), ridge


def rock():
    v, u = np.mgrid[0:N, 0:N] / N; w = fft_noise(N, 1.7, 131); n2 = fft_noise(N, 0.6, 132); n3 = fft_noise(N, 1.9, 133)
    strata = np.sin(2 * np.pi * (9 * v + 1.6 * w)) * 0.5 + 0.5; crack = (np.abs(n3 - 0.5) < 0.008) | (np.abs(fft_noise(N, 1.8, 134) - 0.5) < 0.006)
    l = 0.74 + 0.2 * strata + 0.2 * (n2 - 0.5) + 0.12 * (w - 0.5); l[crack] -= 0.3
    return np.clip(np.dstack([l, l * 0.985, l * 0.96]), 0, 1), l


def boulder():
    """Weathered stone for boulders and outcrops: lichen patches and cracks, no bedding stripes."""
    n1 = fft_noise(N, 1.6, 161); n2 = fft_noise(N, 0.7, 162); n3 = fft_noise(N, 1.9, 163); crack = (np.abs(n3 - 0.5) < 0.006) | (np.abs(fft_noise(N, 1.8, 164) - 0.5) < 0.005)
    l = 0.72 + 0.22 * (n1 - 0.5) + 0.14 * (n2 - 0.5); l[crack] -= 0.28; lich = np.clip((fft_noise(N, 1.5, 165) - 0.6) * 4, 0, 1)
    return np.clip(np.dstack([l * (1 + 0.06 * lich), l * (1 + 0.1 * lich), l * (0.97 - 0.12 * lich)]), 0, 1), l


def grunge():
    """Weathered paint and concrete: fine grain, soft blotches, rain streaks running down (v is up on walls), pits."""
    v, u = np.mgrid[0:N, 0:N] / N; n1 = fft_noise(N, 1.8, 171); n2 = fft_noise(N, 0.8, 172); n3 = fft_noise(N, 0.3, 173)
    st = np.repeat(fft_noise(N, 1.2, 174)[:1, :], N, 0) * (0.6 + 0.4 * fft_noise(N, 1.6, 175)); pits = fft_noise(N, 0.05, 176) > 0.82
    l = 0.9 + 0.08 * (n1 - 0.5) + 0.07 * (n2 - 0.5) + 0.04 * (n3 - 0.5) - 0.09 * np.clip(st - 0.55, 0, 1) * 2; l[pits] -= 0.08
    return np.dstack([l, l * 0.995, l * 0.985]), 0.5 * n2 + 0.5 * n3 - 0.6 * pits


def decal_atlas():
    """Road decals, 2 x 2 cells, RGBA: crack network, repair patch, oil stain, manhole cover. Row 0 at the bottom."""
    from PIL import Image, ImageDraw, ImageFilter
    S = 512; out = np.zeros((2 * S, 2 * S, 4)); r = np.random.default_rng(7)
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)                                  # cracks: branching random walks
    for k in range(5):
        x, y = r.uniform(60, 450), r.uniform(60, 450); a = r.uniform(0, 6.28)
        for _ in range(70):
            a += r.normal(0, 0.45); nx, ny = x + 7 * np.cos(a), y + 7 * np.sin(a); d.line([(x, y), (nx, ny)], fill=255, width=int(r.integers(2, 5))); x, y = np.clip(nx, 20, 492), np.clip(ny, 20, 492)
            if r.random() < 0.08: bx, by, ba = x, y, a + r.choice([-1.2, 1.2])
            if r.random() < 0.06: d.line([(x, y), (x + 30 * np.cos(a + 1.3), y + 30 * np.sin(a + 1.3))], fill=200, width=2)
    a_ = np.asarray(im.filter(ImageFilter.GaussianBlur(0.8)), float) / 255; cell = np.zeros((S, S, 4)); cell[..., :3] = 0.03; cell[..., 3] = np.clip(a_ * 1.4, 0, 0.92); out[S:, :S] = cell[::-1]
    yy, xx = np.mgrid[0:S, 0:S] / S                                                          # patch: darker newer tarmac with a sealed edge
    m = (np.abs(xx - 0.5) < 0.42) & (np.abs(yy - 0.5) < 0.3); edge = m & ~((np.abs(xx - 0.5) < 0.4) & (np.abs(yy - 0.5) < 0.28)); n = fft_noise(S, 1.4, 177)
    cell = np.zeros((S, S, 4)); cell[..., :3] = (0.05 + 0.03 * n)[..., None]; cell[..., 3] = np.where(edge, 0.95, np.where(m, 0.72, 0)); out[S:, S:] = cell[::-1]
    rr = np.hypot(xx - 0.5, (yy - 0.5) * 1.3) + 0.08 * (fft_noise(S, 1.2, 178) - 0.5)        # oil stain
    cell = np.zeros((S, S, 4)); cell[..., :3] = 0.015; cell[..., 3] = np.clip((0.4 - rr) / 0.25, 0, 1) ** 1.2 * 0.75; out[:S, :S] = cell[::-1]
    rr = np.hypot(xx - 0.5, yy - 0.5); ring = (rr < 0.4) & (rr > 0.36); grid = (rr < 0.36) & (((xx * 20).astype(int) + (yy * 20).astype(int)) % 2 == 0)   # manhole
    cell = np.zeros((S, S, 4)); cell[..., :3] = np.where(ring[..., None], 0.18, np.where(grid[..., None], 0.08, 0.12)); cell[..., 3] = (rr < 0.4) * 1.0; out[:S, S:] = cell[::-1]
    return out


def sand():
    v, u = np.mgrid[0:N, 0:N] / N; w = fft_noise(N, 1.6, 141); sp = fft_noise(N, 0.1, 142)
    rip = np.sin(2 * np.pi * (26 * v + 2.2 * w)) * 0.5 + 0.5; l = 0.84 + 0.1 * rip ** 2 + 0.08 * (sp - 0.5) + 0.06 * (fft_noise(N, 1.2, 143) - 0.5)
    peb = (fft_noise(N, 0.7, 144) > 0.74); l[peb] -= 0.14
    return np.clip(np.dstack([l, l * 0.98, l * 0.93]), 0, 1), rip


def pave():
    yy, xx = np.mgrid[0:N, 0:N]; s = 128; row = yy // s; xo = (xx + (row % 2) * (s // 2)) % N; cx = xo // s
    h = ((row * 7919 + cx * 104729) * 2654435761 % 1000) / 1000.0; joint = ((yy % s) < 4) | ((xo % s) < 4)
    l = 0.8 + 0.14 * h + 0.1 * (fft_noise(N, 0.5, 151) - 0.5) + 0.08 * (fft_noise(N, 1.7, 152) - 0.5); l[joint] = 0.5
    stain = np.clip((fft_noise(N, 2.1, 153) - 0.63) * 5, 0, 1); l -= 0.1 * stain
    return np.clip(np.dstack([l, l, l * 0.985]), 0, 1), np.where(joint, 0.0, 1.0)

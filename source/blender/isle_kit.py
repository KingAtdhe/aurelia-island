"""Aurelia Island building kit: one trim sheet (strips that tile along their length, with shading and wear drawn in)
and the helpers that map kit pieces onto it. Strips are greyscale so one sheet serves every colour through vertex tint."""
import numpy as np
from isle_lib import fft_noise
N = 1024; M_PER_TILE = 2.56
# name: (first row, last row) in pixels from the bottom of the sheet
STRIPS = dict(cornice=(0, 160), ashlar=(160, 320), stone=(320, 400), course=(400, 464), frame=(464, 512), louvre=(512, 640), metal=(640, 704), plank=(704, 832))


def trim_sheet():
    L = np.full((N, N), 0.8); Hh = np.zeros((N, N)); u = np.arange(N)[None, :]; n1 = fft_noise(N, 1.2, 201); n2 = fft_noise(N, 0.5, 202); streak = np.repeat(fft_noise(N, 1.0, 203)[:1, :], N, 0)

    def rows(name): a, b = STRIPS[name]; return slice(a, b), (np.arange(a, b) - a)[:, None] / (b - a)
    # cornice: fillet, dentil course, cyma, top fillet (lit from above: tops bright, undersides dark)
    sl, v = rows('cornice'); prof = np.where(v < 0.12, 0.25, np.where(v < 0.42, 0.45, np.where(v < 0.5, 0.62, np.where(v < 0.86, 0.62 + 0.3 * np.sin((v - 0.5) / 0.36 * np.pi / 2), 1.0))))
    hh = prof * np.ones((1, N)); dent = (v > 0.14) & (v < 0.42) & ((u % 32) < 20); hh = np.where((v > 0.14) & (v < 0.42), np.where(dent, 0.62, 0.3), hh)
    g = np.gradient(hh, axis=0) * 60; L[sl] = np.clip(0.80 - 0.28 * np.clip(g, -1, 1) - 0.22 * ((v > 0.14) & (v < 0.42) & ~dent) - 0.1 * (v < 0.1), 0.2, 1); Hh[sl] = hh
    # ashlar: staggered blocks with drafted margins, darker and dirtier toward the ground
    sl, v = rows('ashlar'); yy = np.arange(160)[:, None]; row = yy // 80; xo = (u + (row % 2) * 64) % N; joint = ((yy % 80) < 5) | ((xo % 128) < 5); hsh = (((row * 131 + xo // 128 * 977) * 2654435761) % 1000) / 1000.0
    L[sl] = np.where(joint, 0.42, 0.72 + 0.16 * hsh) * (0.72 + 0.28 * v); Hh[sl] = np.where(joint, 0.0, 0.8 + 0.2 * hsh)
    # dressed stone for sills, lintels and casings: light top edge, shadow under the lower edge
    sl, v = rows('stone'); L[sl] = 0.84 + 0.1 * (v > 0.88) - 0.2 * (v < 0.1) - 0.05 * (np.abs(v - 0.5) < 0.03); Hh[sl] = np.where(v < 0.1, 0.3, np.where(v > 0.88, 0.9, 0.7))
    sl, v = rows('course'); hh = np.where(v < 0.25, 0.4, np.where(v < 0.7, 0.85, 0.6)) * np.ones((1, N)); L[sl] = 0.82 - 0.25 * (v < 0.25) + 0.08 * (v > 0.7); Hh[sl] = hh
    sl, v = rows('frame'); L[sl] = 0.92 - 0.18 * ((v < 0.12) | (v > 0.9)) - 0.06 * (np.abs(v - 0.5) < 0.05); Hh[sl] = np.where((v < 0.12) | (v > 0.9), 0.3, 0.8)
    sl, v = rows('louvre'); ph = (np.arange(128)[:, None] % 16) / 16.0; L[sl] = (0.45 + 0.5 * ph) * np.ones((1, N)); L[sl][(np.arange(128) % 16 < 2)] = 0.18; Hh[sl] = ph * np.ones((1, N))
    sl, v = rows('metal'); L[sl] = 0.8 + 0.08 * (streak[sl] - 0.5) - 0.2 * ((v < 0.08) | (v > 0.92)); Hh[sl] = 0.6
    sl, v = rows('plank'); pk = (u % 96); L[sl] = np.where(pk < 4, 0.35, 0.74 + 0.12 * ((u // 96) % 3) / 2) * np.ones((128, 1)); Hh[sl] = np.where(pk < 4, 0.0, 0.8) * np.ones((128, 1))
    wear = 0.9 + 0.16 * (n1 - 0.5) + 0.1 * (n2 - 0.5) + 0.12 * (streak - 0.5); L = np.clip(L * wear, 0, 1)
    return np.dstack([L, L, L * 0.985]), Hh + 0.08 * n2


def strip_uv(strip, length, n):
    """UVs for n quads (corners a, b along the length; d, c across) of the given lengths in metres."""
    a, b = STRIPS[strip]; v0 = (a + 1.5) / N; v1 = (b - 1.5) / N; length = np.broadcast_to(np.asarray(length, float), (n,)); u0 = np.random.default_rng(int(a) + n).uniform(0, 1, n); u1 = u0 + length / M_PER_TILE
    return np.stack([np.c_[u0, np.full(n, v0)], np.c_[u1, np.full(n, v0)], np.c_[u1, np.full(n, v1)], np.c_[u0, np.full(n, v1)]], 1)

"""Painted tree atlas (alpha cut-out) and crossed-card tree meshes for Aurelia Island."""
import numpy as np
import isle_lib as L
from isle_lib import fft_noise

N = 512
YY, XX = np.mgrid[0:N, 0:N]; XX = (XX + .5) / N; YY = (YY + .5) / N
BROWN = np.array([0.30, 0.21, 0.14])


def _finish(C, A):
    m = A > 0.5
    if m.any(): C[~m] = C[m].mean(0)          # bleed colour under the cut-out so mipmaps do not darken the edges
    return np.dstack([np.clip(C, 0, 1), A])


def seg_dist(a, b):
    ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay
    t = np.clip(((XX - ax) * dx + (YY - ay) * dy) / (dx * dx + dy * dy), 0, 1)
    return np.hypot(XX - ax - dx * t, YY - ay - dy * t), t


def pine(seed, tiers=9, width=0.44, snow=False):
    n1 = fft_noise(N, 1.5, seed); n2 = fft_noise(N, 0.55, seed + 1); n3 = fft_noise(N, 1.0, seed + 2); nh = fft_noise(N, 1.8, seed + 5)
    C = np.zeros((N, N, 3)); A = np.zeros((N, N)); ax = np.abs(XX - 0.5 - 0.012 * np.sin(YY * 9 + seed))
    tr = (ax < 0.022) & (YY < 0.34); C[tr] = BROWN * (0.75 + 0.5 * n1[tr, None]); A[tr] = 1
    t = (YY - 0.11) / 0.88; ph = np.clip(t, 0, 1) * tiers; saw = 1 - (ph % 1)
    w = (1 - np.clip(t, 0, 1)) ** 0.82 * width * (0.5 + 0.5 * saw ** 1.3) + 0.012
    edge = w * (0.80 + 0.55 * (n1 - 0.5))
    m = (ax < edge) & (t > 0) & (t < 1) & ~((ax > edge * 0.45) & (nh > 0.6))
    inner = ax / np.maximum(edge, 1e-3)
    lum = 0.42 + 0.42 * inner * saw + 0.32 * (n2 - 0.5) + 0.22 * np.clip(t, 0, 1) + 0.18 * (n3 - 0.5)
    col = np.array([0.15, 0.34, 0.17])[None, None, :] * (0.5 + lum)[..., None]
    if snow:
        sw = np.clip((0.62 - saw) * 3.2 + (n3 - 0.5) * 1.2, 0, 1)[..., None]; col = col * (1 - sw) + np.array([0.93, 0.95, 0.98]) * sw * (0.85 + 0.15 * n1[..., None])
    C[m] = col[m]; A[m] = 1
    return _finish(C, A)


def crown(seed, cx, cy, rx, ry, nclump, rmin, rmax, base, trunk=BROWN, hole=0.70, trunk_top=0.5, tw=0.03, ticks=False, branches=True):
    r = np.random.default_rng(seed); n1 = fft_noise(N, 1.3, seed); n2 = fft_noise(N, 0.6, seed + 1)
    C = np.zeros((N, N, 3)); A = np.zeros((N, N)); ax = np.abs(XX - 0.5)
    tr = (ax < tw * (1.25 - YY * 1.1)) & (YY < trunk_top); tc = trunk * (0.75 + 0.5 * n1[..., None])
    if ticks: tc = np.where(((n2 > 0.6) & (np.sin(YY * 160) > 0.3))[..., None], np.array([0.12, 0.12, 0.12]), tc)
    C[tr] = tc[tr]; A[tr] = 1
    if branches:
        for bx, by in ((0.5 - rx * 0.55, cy - ry * 0.1), (0.5 + rx * 0.5, cy), (0.5 - rx * 0.15, cy + ry * 0.3)):
            d, t = seg_dist((0.5, trunk_top - 0.14), (bx, by)); m = d < 0.011 * (1.2 - t); C[m] = tc[m]; A[m] = 1
    cl = []
    for _ in range(nclump):
        a = r.uniform(0, 2 * np.pi); q = r.uniform(0, 1) ** 0.6
        cl.append((cy + ry * q * np.sin(a) * 0.86, cx + rx * q * np.cos(a) * 0.86, r.uniform(rmin, rmax), r.uniform(0.82, 1.15)))
    for yc, xc, rr, tint in sorted(cl):
        d = np.hypot(XX - xc, YY - yc); m = d < rr * (0.82 + 0.5 * (n1 - 0.5))
        light = np.clip(0.5 + 0.6 * ((YY - yc) - 0.55 * (XX - xc)) / rr, 0, 1)
        col = base[None, None, :] * tint * (0.42 + 0.85 * light + 0.25 * (n2 - 0.5))[..., None]
        C[m] = col[m]; A[m] = 1
    en = np.hypot((XX - cx) / rx, (YY - cy) / ry)
    nh = fft_noise(N, 1.8, seed + 5); A[(nh > hole - 0.06) & (en > 0.42) & ~tr] = 0
    return _finish(C, A)


def palm(seed):
    r = np.random.default_rng(seed); n1 = fft_noise(N, 1.2, seed)
    C = np.zeros((N, N, 3)); A = np.zeros((N, N))
    tx = 0.5 + 0.07 * np.sin(YY * 2.4); m = (np.abs(XX - tx) < 0.02 - 0.006 * YY) & (YY < 0.74)
    C[m] = (np.array([0.42, 0.34, 0.24])[None, :] * (0.7 + 0.35 * (np.sin(YY[m] * 150) > 0)[:, None] + 0.2 * n1[m, None])); A[m] = 1
    top = np.array([0.5 + 0.07 * np.sin(0.74 * 2.4), 0.74])
    for k, ang in enumerate(np.linspace(-1.75, 1.75, 11) + r.uniform(-0.1, 0.1, 11)):
        Ln = r.uniform(0.36, 0.46); s = np.linspace(0, 1, 70)
        px = top[0] + Ln * np.sin(ang) * s; py = top[1] + Ln * (np.cos(ang) * s * 0.75 - 0.85 * s * s * (0.25 + 0.6 * abs(np.sin(ang))))
        best = np.full((N, N), 9.0); bs = np.zeros((N, N))
        for q in range(0, 70, 2):
            d = np.hypot(XX - px[q], YY - py[q]); u = d < best; best = np.where(u, d, best); bs = np.where(u, s[q], bs)
        wd = 0.052 * np.sin(np.pi * np.clip(bs, 0.02, 1)) ** 0.55 * (0.55 + 0.45 * (np.sin(bs * 85 + k) > -0.35))
        m = best < wd; shade = 0.55 + 0.5 * (1 - best / np.maximum(wd, 1e-4)) * 0.6 + 0.3 * (n1 - 0.5) + 0.12 * (k % 2)
        col = np.array([0.24, 0.47, 0.18])[None, None, :] * shade[..., None]; C[m] = col[m]; A[m] = 1
    return _finish(C, A)


def top_conifer(seed):
    n1 = fft_noise(N, 1.3, seed); n2 = fft_noise(N, 0.6, seed + 1)
    rr = np.hypot(XX - .5, YY - .5); ang = np.arctan2(YY - .5, XX - .5)
    edge = 0.46 * (0.72 + 0.28 * np.cos(ang * 9 + 6 * n1)) * (0.85 + 0.3 * (n1 - .5))
    m = (rr < edge) & ~((rr > edge * 0.55) & (n2 > 0.66))
    lum = 0.5 + 0.55 * (rr / np.maximum(edge, 1e-3)) * (0.6 + 0.4 * np.cos(ang * 9 + 6 * n1)) + 0.3 * (n2 - .5)
    C = np.array([0.15, 0.34, 0.17])[None, None, :] * (0.45 + lum)[..., None] * np.ones((N, N, 1)); A = m.astype(float)
    return _finish(C, A)


def atlas():
    cells = [pine(11, 9, 0.44), pine(23, 7, 0.36), crown(31, .5, .62, .44, .34, 52, .06, .13, np.array([0.24, 0.46, 0.18])), pine(47, 8, 0.42, snow=True),
             crown(53, .5, .60, .27, .36, 70, .035, .075, np.array([0.42, 0.56, 0.22]), trunk=np.array([0.86, 0.85, 0.80]), hole=0.6, trunk_top=0.86, tw=0.016, ticks=True, branches=False),
             palm(61), top_conifer(71), crown(83, .5, .5, .46, .46, 60, .07, .13, np.array([0.26, 0.48, 0.19]), hole=0.74, trunk_top=0.0, branches=False)]
    A = np.zeros((2 * N, 4 * N, 4))
    for k, c in enumerate(cells): A[(k // 4) * N:(k // 4 + 1) * N, (k % 4) * N:(k % 4 + 1) * N] = c
    A[..., :3] = np.clip(A[..., :3] * 1.6 + 0.02, 0, 1)
    return A


def emit(C, mat):
    """C.cards rows: x, y, z, height, width, side cell, top cell, top height fraction, r, g, b"""
    T = np.array(C.cards, float); n = len(T)
    if not n: return
    r = np.random.default_rng(5); a = r.uniform(0, np.pi, n)
    x, y, z, h, w = T[:, 0], T[:, 1], T[:, 2], T[:, 3], T[:, 4]; cell = T[:, 5].astype(int); top = T[:, 6].astype(int); kt = T[:, 7]; tint = T[:, 8:11]
    e = 0.006
    def uvs(c):
        u0 = (c % 4) / 4 + e; u1 = (c % 4 + 1) / 4 - e; v0 = (c // 4) / 2 + e; v1 = (c // 4 + 1) / 2 - e
        return np.stack([np.c_[u0, v0], np.c_[u1, v0], np.c_[u1, v1], np.c_[u0, v1]], 1)          # (n, 4, 2)
    V = []; U = []; Nn = []
    for da in (0.0, np.pi / 2):
        dx = np.cos(a + da) * w / 2; dy = np.sin(a + da) * w / 2
        q = np.stack([np.c_[x - dx, y - dy, z], np.c_[x + dx, y + dy, z], np.c_[x + dx, y + dy, z + h], np.c_[x - dx, y - dy, z + h]], 1)
        nn = np.stack([np.c_[-dx, -dy, w * 1.6], np.c_[dx, dy, w * 1.6], np.c_[dx * .6, dy * .6, w * 1.9], np.c_[-dx * .6, -dy * .6, w * 1.9]], 1)
        V.append(q); U.append(uvs(cell)); Nn.append(nn)
    d1x = np.cos(a) * w * 0.48; d1y = np.sin(a) * w * 0.48; d2x = -d1y; d2y = d1x; zt = z + h * kt
    V.append(np.stack([np.c_[x - d1x - d2x, y - d1y - d2y, zt], np.c_[x + d1x - d2x, y + d1y - d2y, zt], np.c_[x + d1x + d2x, y + d1y + d2y, zt], np.c_[x - d1x + d2x, y - d1y + d2y, zt]], 1))
    U.append(uvs(top)); Nn.append(np.tile(np.array([0, 0, 1.0]), (n, 4, 1)))
    V = np.concatenate(V, 0).reshape(-1, 3); U = np.concatenate(U, 0).reshape(-1, 2); Nn = np.concatenate(Nn, 0).reshape(-1, 3)
    Nn /= np.linalg.norm(Nn, axis=1)[:, None]
    q = np.arange(3 * n) * 4; F = np.vstack([np.c_[q, q + 1, q + 2], np.c_[q, q + 2, q + 3]])
    Cc = np.repeat(np.tile(tint, (3, 1)), 4, axis=0)
    L.make_chunked('TreeCards', V, F, Cc, U, mat, True, normals=Nn)


def render_material(mat):
    """After the game exports: make the card material light up from both sides in Cycles (leaves are translucent)."""
    import bpy
    for o in bpy.data.objects:
        if o.name.startswith('TreeCards') or o.name.startswith('GrassCards'): o.visible_shadow = False
        if o.name.startswith('COL_'): o.hide_render = True
    nt = mat.node_tree; b = nt.nodes['Principled BSDF']; out = nt.nodes['Material Output']; col = nt.nodes['Mix'].outputs[2]; rnd = nt.nodes['Math'].outputs[0]
    for l in list(b.inputs['Alpha'].links): nt.links.remove(l)
    b.inputs['Alpha'].default_value = 1.0
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent'); nt.links.new(col, tl.inputs['Color'])
    m1 = nt.nodes.new('ShaderNodeMixShader'); m1.inputs[0].default_value = 0.45; nt.links.new(b.outputs[0], m1.inputs[1]); nt.links.new(tl.outputs[0], m1.inputs[2])
    tp = nt.nodes.new('ShaderNodeBsdfTransparent'); m2 = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(rnd, m2.inputs[0]); nt.links.new(tp.outputs[0], m2.inputs[1]); nt.links.new(m1.outputs[0], m2.inputs[2]); nt.links.new(m2.outputs[0], out.inputs['Surface'])

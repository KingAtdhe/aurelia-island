"""Aurelia Island flora: modelled trees and plants (real trunks, limbs and leaf sprays), their textures and detail levels.
Every species is built at real size with its base at the origin; the map places them as instances."""
import math
import numpy as np

UP = np.array([0, 0, 1.0])


def unit(v):
    v = np.asarray(v, float); return v / max(np.linalg.norm(v), 1e-9)


class MB:
    """Mesh buffer with colours, UVs and shading normals."""
    def __init__(s): s.V = []; s.F = []; s.C = []; s.U = []; s.N = []; s.n = 0

    def add(s, V, F, C, U, N):
        V = np.asarray(V, float); C = np.asarray(C, float)
        if C.ndim == 1: C = np.tile(C, (len(V), 1))
        s.V.append(V); s.F.append(np.asarray(F, np.int64) + s.n); s.C.append(C); s.U.append(np.asarray(U, float)); s.N.append(np.asarray(N, float)); s.n += len(V)

    def arrays(s):
        if not s.V: return None
        N = np.vstack(s.N); N /= np.maximum(np.linalg.norm(N, axis=1), 1e-9)[:, None]
        return np.vstack(s.V), np.vstack(s.F), np.vstack(s.C), np.vstack(s.U), N

    def tris(s): return sum(len(f) for f in s.F)


# ------------------------------------------------------------------ geometry helpers
def tube(mb, P, R, n, col, urep=2.0, vlen=1.6):
    P = np.asarray(P, float); k = len(P); R = np.broadcast_to(np.asarray(R, float), (k,))
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    a = np.cross(T[0], UP)
    if np.linalg.norm(a) < 1e-3: a = np.array([1.0, 0, 0])
    ang = np.arange(n + 1) * 2 * np.pi / n; V = []; N = []; U = []; s = 0.0
    col = np.asarray(col, float); C = []
    for i in range(k):
        a = a - T[i] * np.dot(a, T[i]); a /= np.linalg.norm(a); b = np.cross(T[i], a)
        if i: s += np.linalg.norm(P[i] - P[i - 1])
        ring = np.cos(ang)[:, None] * a + np.sin(ang)[:, None] * b
        V.append(P[i] + ring * R[i]); N.append(ring); U.append(np.c_[ang / (2 * np.pi) * urep, np.full(n + 1, s / vlen)])
        C.append(np.tile(col if col.ndim == 1 else col[i], (n + 1, 1)))
    F = []
    for i in range(k - 1):
        j = np.arange(n); a0 = i * (n + 1) + j; b0 = a0 + n + 1
        F.append(np.c_[a0, a0 + 1, b0 + 1]); F.append(np.c_[a0, b0 + 1, b0])
    mb.add(np.vstack(V), np.vstack(F), np.vstack(C), np.vstack(U), np.vstack(N))


CELLS = {'spray': (0.0, 0.0), 'broad': (0.5, 0.0), 'birch': (0.0, 0.5), 'frond': (0.5, 0.5)}


def card(mb, base, d, w, L, W, cell, col, centre=None, droop=0.0, segs=2, lift=0.35, tip=None, fold=0.0):
    """Leaf spray: a strip running from `base` along `d`, `W` wide across `w`, sagging by `droop` at the tip."""
    base = np.asarray(base, float); d = unit(d); w = unit(w); t = np.linspace(0, 1, segs + 1)
    cen = base + d * L * t[:, None] - UP * droop * (t ** 2)[:, None]
    u0, v0 = CELLS[cell]; e = 0.004
    if fold:                                              # three verts across, the middle (rib) raised: a shallow V
        nrm = unit(np.cross(d, w)); V = np.vstack([cen - w * W / 2 - nrm * fold, cen, cen + w * W / 2 - nrm * fold]); m = segs + 1
        U = np.vstack([np.c_[np.full(m, u0 + e), v0 + e + (0.5 - 2 * e) * t], np.c_[np.full(m, u0 + 0.25), v0 + e + (0.5 - 2 * e) * t], np.c_[np.full(m, u0 + 0.5 - e), v0 + e + (0.5 - 2 * e) * t]])
        i = np.arange(segs); F = np.vstack([np.c_[i, m + i, m + i + 1], np.c_[i, m + i + 1, i + 1], np.c_[m + i, 2 * m + i, 2 * m + i + 1], np.c_[m + i, 2 * m + i + 1, m + i + 1]])
    else:
        V = np.vstack([cen - w * W / 2, cen + w * W / 2]); m = segs + 1
        U = np.vstack([np.c_[np.full(m, u0 + e), v0 + e + (0.5 - 2 * e) * t], np.c_[np.full(m, u0 + 0.5 - e), v0 + e + (0.5 - 2 * e) * t]])
        i = np.arange(segs); F = np.vstack([np.c_[i, m + i, m + i + 1], np.c_[i, m + i + 1, i + 1]])
    if centre is None: N = np.tile(UP, (len(V), 1))
    else:
        N = V - np.asarray(centre, float); N /= np.maximum(np.linalg.norm(N, axis=1), 1e-6)[:, None]; N = N * (1 - lift) + UP * lift
    C = np.tile(np.asarray(col, float), (len(V), 1))
    if tip is not None:
        tt = np.tile(t, len(V) // m)[:, None]; C = C * (1 - tt) + np.asarray(tip, float) * tt
    mb.add(V, F, C, U, N)


def perp(d):
    a = np.cross(d, UP)
    return unit(a) if np.linalg.norm(a) > 1e-3 else np.array([1.0, 0, 0])


def bend_path(p0, d, L, k, r, curl=0.25, rise=0.0):
    """Polyline of k+1 points starting at p0 along d, wandering a little and curving up by `rise`."""
    P = [np.asarray(p0, float)]; d = unit(d)
    for i in range(k):
        d = unit(d + r.normal(0, curl, 3) * (1, 1, 0.5) + UP * rise); P.append(P[-1] + d * L / k)
    return np.array(P), d


BARK = np.array([0.115, 0.075, 0.048]); BARK_D = np.array([0.06, 0.042, 0.03]); GREEN_CORE = np.array([0.035, 0.07, 0.035])


# ------------------------------------------------------------------ species
def spruce(seed, lod=0, snow=False, hgt=19.0, spread=1.0):
    r = np.random.default_rng(seed); bark = MB(); leaf = MB()
    lean = r.normal(0, 0.012, 2); zs = np.array([0, 0.35, 1.2, 4, 8, 12, 16, hgt - 0.4]); rad = np.array([0.46, 0.34, 0.29, 0.25, 0.19, 0.13, 0.06, 0.015])
    P = np.c_[lean[0] * zs + 0.05 * np.sin(zs * 0.5 + seed), lean[1] * zs, zs]
    tube(bark, P, rad, 8 if lod == 0 else 5, BARK)
    z0 = 2.0 + r.uniform(0, 0.8); span = hgt - 0.9 - z0
    core_z = np.linspace(z0 + 0.6, hgt - 1.5, 6); core_r = 0.24 * (0.4 + 3.4 * (1 - (core_z - z0) / span) ** 0.9) * spread
    tube(bark, np.c_[np.interp(core_z, zs, P[:, 0]), np.interp(core_z, zs, P[:, 1]), core_z], core_r, 7 if lod == 0 else 5, GREEN_CORE, urep=1, vlen=3)
    dz = 0.62 if lod == 0 else 1.9; nb = 7 if lod == 0 else 4; k = 0
    col = np.array([0.74, 0.96, 0.7]); tipc = np.array([0.95, 1.0, 0.85])
    z = z0; wob = r.uniform(0, 6.28, 3)
    while z < hgt - 1.2:
        t = (z - z0) / span; cx = np.interp(z, zs, P[:, 0]); cy = np.interp(z, zs, P[:, 1])
        irr = 1.0 + 0.16 * math.sin(z * 0.9 + wob[0]) + 0.1 * math.sin(z * 2.3 + wob[1])            # some whorls fuller than others: no perfect cone
        Lb = (0.6 + 4.4 * (1 - t) ** 0.8) * spread * irr * (1.0 if lod == 0 else 1.15)
        for j in range(nb):
            if lod == 0 and r.random() < 0.18: continue                                                    # gaps where a bough is missing
            az = k * 2.39996 + j * 2 * np.pi / nb + r.uniform(-0.4, 0.4); L_ = Lb * r.uniform(0.62, 1.18)
            el = -0.2 - 0.42 * (1 - t) + r.uniform(-0.16, 0.16)
            d = np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)]); w = np.array([-math.sin(az), math.cos(az), 0])
            base = np.array([cx, cy, z + r.uniform(-0.2, 0.2)]); cen = np.array([cx, cy, z - 1.5]); c_ = col * r.uniform(0.8, 1.1)
            card(leaf, base, d, w, L_, L_ * (0.62 if lod == 0 else 0.9), 'spray', c_, cen, droop=(0.16 if lod == 0 else -0.1) * L_, segs=3 if lod == 0 else 1, lift=0.5, tip=tipc * c_ / col, fold=0.07 * L_ if lod == 0 else 0.0)
            if snow:                                               # snow lying along the top of the bough
                q0 = base + UP * 0.07; q1 = base + d * L_ * 0.55 + UP * (0.09 + 0.05 * L_); q2 = base + d * L_ * 0.93 + UP * (0.06 + 0.10 * L_); ws = L_ * 0.2
                bark.add(np.array([q0 - w * ws * 0.6, q0 + w * ws * 0.6, q1 - w * ws, q1 + w * ws, q2]), [(0, 1, 3), (0, 3, 2), (2, 3, 4)], np.array([1.0, 1.0, 1.0]), np.zeros((5, 2)) + 0.5, np.tile(UP, (5, 1)))
            if lod == 0:
                dn = unit(np.cross(d, w)); dn = dn if dn[2] < 0 else -dn
                card(leaf, base - dn * L_ * 0.08, d, dn, L_ * 0.95, L_ * 0.66, 'spray', c_ * 0.8, cen, droop=-0.06 * L_, segs=2, lift=0.3)
        if lod == 0 and t < 0.85:                                                                          # short sprays between the whorls fill the layered look
            for j in range(3):
                az = r.uniform(0, 6.28); L2 = Lb * r.uniform(0.35, 0.6); zz = z + dz * r.uniform(0.3, 0.7)
                d = np.array([math.cos(az) * 0.9, math.sin(az) * 0.9, -0.3]); w = np.array([-math.sin(az), math.cos(az), 0])
                card(leaf, np.array([cx, cy, zz]), d, w, L2, L2 * 0.7, 'spray', col * r.uniform(0.7, 0.95), np.array([cx, cy, zz - 1.5]), droop=0.1 * L2, segs=2, lift=0.45)
        z += dz * (1 - 0.35 * t) * r.uniform(0.8, 1.2); k += 1
    top = np.array([P[-1, 0], P[-1, 1], hgt - 2.3])
    for a in (0.3, 0.3 + np.pi / 3, 0.3 + 2 * np.pi / 3)[: 3 if lod == 0 else 2]:
        card(leaf, top, UP, (math.cos(a), math.sin(a), 0), 3.1, 1.7, 'spray', col, top - UP * 3, segs=1, lift=0.2)
    return bark, leaf, hgt


def pine(seed, lod=0):
    """Tall bare-trunked pine with an open, layered crown."""
    r = np.random.default_rng(seed); bark = MB(); leaf = MB(); hgt = 17.0
    zs = np.linspace(0, hgt - 1.2, 8); bx = 0.5 * np.sin(zs * 0.21 + seed) + 0.03 * zs; by = 0.35 * np.sin(zs * 0.17 + 2 * seed)
    P = np.c_[bx, by, zs]; rad = np.interp(zs, [0, 0.5, 3, hgt], [0.42, 0.3, 0.25, 0.07])
    warm = np.array([0.26, 0.115, 0.055]); colr = np.array([BARK * (1 - t_) + warm * t_ for t_ in np.clip((zs - 5) / 6, 0, 1)])
    tube(bark, P, rad, 8 if lod == 0 else 5, colr)
    col = np.array([0.6, 0.82, 0.55]); nl = 12 if lod == 0 else 6
    for k in range(nl):
        z = hgt * (0.5 + 0.44 * k / (nl - 1)) + r.uniform(-0.3, 0.3); t = (z / hgt - 0.5) / 0.44
        p0 = np.array([np.interp(z, zs, bx), np.interp(z, zs, by), z]); az = k * 2.39996 + r.uniform(-0.3, 0.3)
        L_ = (1.4 + 3.4 * math.sin(np.pi * (0.25 + 0.7 * t))) * r.uniform(0.85, 1.15) if k < nl - 1 else 0.9
        d0 = np.array([math.cos(az), math.sin(az), 0.25])
        Pb, dl = bend_path(p0, d0, L_, 3, r, 0.12, 0.16); rb = np.interp(z, zs, rad) * 0.5
        if lod == 0: tube(bark, Pb, [rb, rb * 0.7, rb * 0.45, rb * 0.2], 4, warm * 0.8)
        tips = [Pb[-1]] + ([Pb[2] + perp(dl) * r.uniform(-1, 1) * 0.9, Pb[-1] + dl * 0.5 + perp(dl) * r.uniform(-1, 1)] if lod == 0 and L_ > 1.6 else [])
        for q in tips:
            cen = q - UP * 1.8; s_ = r.uniform(3.4, 4.6) * (1.0 if lod == 0 else 1.4); a0 = r.uniform(0, np.pi); c_ = col * r.uniform(0.8, 1.1)
            for a in (a0, a0 + 2.1, a0 + 4.2):
                w = np.array([math.cos(a), math.sin(a), 0]); dd = np.array([-math.sin(a), math.cos(a), 0.15])
                card(leaf, q - dd * s_ * 0.5 + UP * 0.1, dd, w, s_, s_ * 0.8, 'spray', c_, cen, droop=0.25, segs=2 if lod == 0 else 1, lift=0.55)
            if lod == 0: card(leaf, q - UP * 0.9, UP, (math.cos(a0), math.sin(a0), 0), s_ * 0.6, s_ * 0.9, 'spray', c_ * 0.85, cen, segs=1, lift=0.3)
    return bark, leaf, hgt


def broadleaf(seed, lod=0, hgt=13.0, wide=1.0, leafcol=(0.72, 0.9, 0.5), cell='broad', trunk=BARK, fork=0.30):
    r = np.random.default_rng(seed); bark = MB(); leaf = MB()
    zf = hgt * fork * r.uniform(0.9, 1.1); cen = np.array([0, 0, hgt * 0.66]); leafcol = np.asarray(leafcol, float)
    P0 = np.array([[0, 0, 0], [0.02, 0, 0.4], [0.05, 0.03, zf * 0.5], [0.1, -0.04, zf]]); tube(bark, P0, [0.50, 0.36, 0.31, 0.27], 8 if lod == 0 else 5, trunk)
    tips = []

    def grow(p, d, L, rad, depth):
        k = 3 if depth > 1 else 2
        P, d1 = bend_path(p, d, L, k, r, 0.13, 0.10)
        if lod == 0 or depth >= 3: tube(bark, P, np.linspace(rad, rad * 0.55, k + 1), {3: 6, 2: 5, 1: 3}[depth] if lod == 0 else 4, trunk * (0.9 if depth < 3 else 1))
        if depth == 1: tips.append((P[-1], d1)); tips.append((P[1], d1)); return
        for j in range(3 if depth == 3 else (3 if r.random() < 0.5 else 2)):
            az = r.uniform(0, 2 * np.pi); sp = r.uniform(0.45, 0.85) * wide
            a = perp(d1); b = np.cross(d1, a); dn = unit(d1 + (a * math.cos(az) + b * math.sin(az)) * sp + UP * 0.12)
            grow(P[-1] if j else P[-1], dn, L * r.uniform(0.62, 0.8), rad * 0.55, depth - 1)
    for j in range(4):
        az = j * np.pi / 2 + r.uniform(-0.5, 0.5); d = unit([math.cos(az) * 0.75 * wide, math.sin(az) * 0.75 * wide, 1.0])
        grow(P0[-1], d, hgt * 0.27, 0.2, 3)
    grow(P0[-1], unit([0.05, 0.02, 1]), hgt * 0.3, 0.2, 3)
    R_ = hgt * 0.36 * wide
    pts = [(p + d * 0.4, d) for p, d in tips]
    for _ in range(26 if lod == 0 else 0):                                  # outer shell so the crown reads as one mass
        v = unit(r.normal(0, 1, 3) * (1, 1, 0.75) + (0, 0, 0.25)); pts.append((cen + v * R_ * (1, 1, 0.78) * r.uniform(0.82, 1.0), v))
    if lod: pts = pts[::4]
    for p, d in pts:
        out = unit(p - cen); s_ = r.uniform(2.1, 3.0) * (1.0 if lod == 0 else 2.2) * hgt / 13; c_ = leafcol * r.uniform(0.72, 1.12) * (0.75 + 0.3 * np.clip((p[2] - cen[2]) / R_ + 0.5, 0, 1))
        w = perp(out); upc = unit(np.cross(out, w)); upc = upc if upc[2] > 0 else -upc
        dd = unit(upc * 0.8 + out * 0.5 + r.normal(0, 0.25, 3))
        card(leaf, p - dd * s_ * 0.45, dd, w, s_, s_, cell, c_, cen, droop=0.35 * s_ * 0.3, segs=2 if lod == 0 else 1, lift=0.3)
        if lod == 0: card(leaf, p - out * s_ * 0.35, out, unit(np.cross(out, w) + r.normal(0, 0.3, 3)), s_ * 0.9, s_ * 0.9, cell, c_ * 0.85, cen, segs=1, lift=0.3)
    return bark, leaf, hgt


def birch(seed, lod=0):
    r = np.random.default_rng(seed); bark = MB(); leaf = MB(); hgt = 14.0
    zs = np.linspace(0, hgt, 9); bx = 0.25 * np.sin(zs * 0.3 + seed); by = 0.2 * np.sin(zs * 0.23 + seed * 2)
    white = np.array([1.0, 1.0, 0.95]); colr = np.array([white * (0.35 if (i == 0) else r.uniform(0.82, 1.05)) for i in range(9)])
    tube(bark, np.c_[bx, by, zs], np.interp(zs, [0, 0.6, hgt], [0.26, 0.17, 0.02]), 7 if lod == 0 else 5, colr, urep=1, vlen=0.9)
    cen = np.array([0, 0, hgt * 0.62]); col = np.array([0.88, 1.0, 0.42]); nb = 16 if lod == 0 else 7
    for k in range(nb):
        z = hgt * (0.33 + 0.6 * k / nb); p0 = np.array([np.interp(z, zs, bx), np.interp(z, zs, by), z]); az = k * 2.39996
        L_ = (1.2 + 2.3 * math.sin(np.pi * (0.15 + 0.8 * k / nb))) * r.uniform(0.85, 1.15)
        Pb, dl = bend_path(p0, [math.cos(az), math.sin(az), 0.9], L_, 3, r, 0.1, 0.02)
        if lod == 0: tube(bark, Pb, [0.05, 0.035, 0.022, 0.01], 3, BARK_D * 1.2)
        for q in (Pb[1], Pb[2], Pb[3]) if lod == 0 else (Pb[2],):
            a = r.uniform(0, np.pi); w = np.array([math.cos(a), math.sin(a), 0]); s_ = r.uniform(1.7, 2.4) * (1 if lod == 0 else 1.7)
            card(leaf, q + UP * 0.25, -UP + r.normal(0, 0.15, 3), w, s_, s_ * 0.9, 'birch', col * r.uniform(0.78, 1.1), cen, segs=1, lift=0.35)
            if lod == 0: card(leaf, q + UP * 0.2, unit(dl * (1, 1, 0) + (0, 0, -0.5)), perp(dl), s_ * 0.9, s_ * 0.8, 'birch', col * r.uniform(0.7, 1.0), cen, segs=1, lift=0.45)
    return bark, leaf, hgt


def palm(seed, lod=0):
    r = np.random.default_rng(seed); bark = MB(); leaf = MB(); hgt = 10.5; ht = hgt - 2.2
    k = 15 if lod == 0 else 6; t = np.linspace(0, 1, k); lean = r.uniform(0.6, 1.5); a = r.uniform(0, 6.28)
    P = np.c_[math.cos(a) * lean * t ** 1.8, math.sin(a) * lean * t ** 1.8, ht * t]
    rad = (0.30 - 0.12 * t) * (1 + 0.07 * (np.arange(k) % 2)) + 0.12 * np.exp(-t * 14)
    tc = np.array([0.30, 0.235, 0.165]); tube(bark, P, rad, 8 if lod == 0 else 5, np.array([tc * (0.8 + 0.25 * (i % 2)) for i in range(k)]), urep=2, vlen=1.2)
    top = P[-1]; s_, n_ = (7, 5) if lod == 0 else (5, 3)
    bark.add(*_blob(top + UP * 0.15, 0.36, 0.36, 0.5, s_, n_), np.array([0.5, 0.52, 0.28]))
    col = np.array([0.85, 1.0, 0.5]); nf = 17 if lod == 0 else 9
    for j in range(nf):
        az = j * 2.39996 + r.uniform(-0.2, 0.2); tier = j / nf; el = 1.15 - 1.5 * tier + r.uniform(-0.12, 0.12); L_ = r.uniform(3.6, 4.6)
        d = np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)]); w = np.array([-math.sin(az), math.cos(az), 0])
        card(leaf, top + UP * 0.35, d, w, L_, 2.1, 'frond', col * r.uniform(0.75, 1.1) * (0.8 + 0.25 * (1 - tier)), top + UP * 0.2, droop=L_ * (0.30 + 0.40 * tier), segs=5 if lod == 0 else 2, lift=0.45, fold=0.22)
    if lod == 0:
        for j in range(4): bark.add(*_blob(top + (0.28 * math.cos(j * 1.6), 0.28 * math.sin(j * 1.6), -0.12), 0.13, 0.13, 0.15, 5, 3), np.array([0.25, 0.2, 0.1]))
    return bark, leaf, hgt


def _blob(c, rx, ry, rz, nu, nv):
    V = []; U = []
    for i in range(nv + 1):
        ph = -np.pi / 2 + np.pi * i / nv
        for j in range(nu + 1):
            th = 2 * np.pi * j / nu; V.append((math.cos(ph) * math.cos(th), math.cos(ph) * math.sin(th), math.sin(ph))); U.append((j / nu, i / nv))
    V = np.array(V); F = []
    for i in range(nv):
        for j in range(nu):
            a = i * (nu + 1) + j; b = a + nu + 1; F += [(a, a + 1, b + 1), (a, b + 1, b)]
    return V * (rx, ry, rz) + np.asarray(c, float), np.array(F), None, np.array(U), V


MB_add = MB.add
def _add(s, V, F, C, U, N, col=None):                                       # allow mb.add(*_blob(...), colour)
    if C is None: C = col
    MB_add(s, V, F, C, U, N)
MB.add = _add


def cypress(seed, lod=0):
    r = np.random.default_rng(seed); bark = MB(); leaf = MB(); hgt = 14.0
    tube(bark, [(0, 0, 0), (0, 0, 0.5), (0, 0, 1.8)], [0.3, 0.2, 0.17], 6 if lod == 0 else 4, BARK)
    zs = np.linspace(1.1, hgt, 9); t = (zs - 1.1) / (hgt - 1.1); rr = 1.05 * np.sin(np.pi * np.clip(t * 0.93 + 0.06, 0, 1)) ** 0.62 * (1 - 0.35 * t) + 0.02
    tube(bark, np.c_[0.1 * np.sin(zs * 0.4), 0 * zs, zs], rr * (1 + r.uniform(-0.08, 0.08, 9)), 9 if lod == 0 else 6, np.array([0.055, 0.105, 0.05]), urep=1, vlen=3)
    col = np.array([0.42, 0.62, 0.40])
    for k in range(64 if lod == 0 else 0):
        z = 1.2 + (hgt - 2.6) * (k + r.random()) / 64; az = k * 2.39996; rad = np.interp(z, zs, rr) * 0.8
        p = np.array([math.cos(az) * rad, math.sin(az) * rad, z]); out = np.array([math.cos(az), math.sin(az), 0])
        card(leaf, p, unit(UP + out * 0.22), np.array([-math.sin(az), math.cos(az), 0]), r.uniform(1.7, 2.4), r.uniform(1.0, 1.3), 'spray', col * r.uniform(0.75, 1.1), (0, 0, z - 1), segs=1, lift=0.3)
    return bark, leaf, hgt


def bush(seed, lod=0):
    r = np.random.default_rng(seed); bark = MB(); leaf = MB(); cen = np.array([0, 0, 0.2]); col = np.array([0.62, 0.82, 0.42])
    for k in range(9 if lod == 0 else 4):
        az = k * 2.39996; el = r.uniform(0.35, 1.25); d = np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)])
        card(leaf, (0, 0, 0.05), d, (-math.sin(az), math.cos(az), 0), r.uniform(1.3, 1.9), r.uniform(1.4, 1.9), 'broad', col * r.uniform(0.7, 1.1), cen, droop=0.25, segs=2 if lod == 0 else 1, lift=0.4)
    return bark, leaf, 1.6


def cactus(seed, lod=0):
    r = np.random.default_rng(seed); bark = MB(); leaf = MB(); hgt = 5.6; g = np.array([0.22, 0.36, 0.16]); n = 12 if lod == 0 else 6

    def column(P, rad):
        P = np.asarray(P, float); k = len(P); T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]; a = np.array([1.0, 0, 0]); V = []; N = []; U = []; C = []
        ang = np.arange(n + 1) * 2 * np.pi / n; rib = 1 + 0.13 * (np.arange(n + 1) % 2) * (lod == 0)
        for i in range(k):
            a = a - T[i] * np.dot(a, T[i]); a /= np.linalg.norm(a); b = np.cross(T[i], a); ring = np.cos(ang)[:, None] * a + np.sin(ang)[:, None] * b
            V.append(P[i] + ring * (rad[i] * rib)[:, None]); N.append(ring); U.append(np.c_[ang / 6.28, np.full(n + 1, i * 0.3)]); C.append(np.outer(0.72 + 0.4 * (np.arange(n + 1) % 2), g))
        F = []
        for i in range(k - 1):
            j = np.arange(n); a0 = i * (n + 1) + j; b0 = a0 + n + 1; F += [np.c_[a0, a0 + 1, b0 + 1], np.c_[a0, b0 + 1, b0]]
        bark.add(np.vstack(V), np.vstack(F), np.vstack(C), np.vstack(U), np.vstack(N))
    column([(0, 0, -0.2), (0, 0, 1), (0, 0, hgt - 0.5), (0, 0, hgt - 0.12), (0, 0, hgt)], [0.38, 0.42, 0.40, 0.26, 0.02])
    for sgn, zb in ((1, hgt * r.uniform(0.34, 0.48)), (-1, hgt * r.uniform(0.42, 0.6))):
        az = r.uniform(0, np.pi); dx, dy = math.cos(az) * sgn, math.sin(az) * sgn; top = zb + hgt * r.uniform(0.22, 0.36)
        column([(dx * 0.3, dy * 0.3, zb), (dx * 0.95, dy * 0.95, zb + 0.05), (dx * 1.3, dy * 1.3, zb + 0.45), (dx * 1.32, dy * 1.32, top - 0.15), (dx * 1.32, dy * 1.32, top)], [0.2, 0.25, 0.26, 0.24, 0.02])
    return bark, leaf, hgt


def grass(seed, lod=0, tall=False, flower=None):
    """Clump of real blades (painted, no texture): many thin curved blades, soft olive colours that sit on the ground's own green,
    normals turned toward the sky so the clump is lit like the ground under it."""
    r = np.random.default_rng(seed); b = MB(); nbl = (64 if not tall else 44) if lod == 0 else 14
    base = np.array([0.045, 0.075, 0.025]); tipc = np.array([0.13, 0.19, 0.06]) if not tall else np.array([0.2, 0.21, 0.09])
    for k in range(nbl):
        az = r.uniform(0, 6.28); L_ = (r.uniform(0.16, 0.42) if not tall else r.uniform(0.55, 1.05)) * (1 if lod == 0 else 1.1)
        wd = r.uniform(0.012, 0.024) * (1 if lod == 0 else 2.6) * (1.3 if tall else 1)
        o = np.array([r.normal(0, 0.26), r.normal(0, 0.26), -0.03]); out = np.array([math.cos(az), math.sin(az), 0]); w = np.array([-out[1], out[0], 0]); lean = r.uniform(0.05, 0.4)
        p1 = o + UP * L_ * 0.4 + out * L_ * lean * 0.12; p2 = o + UP * L_ * 0.75 + out * L_ * lean * 0.45; p3 = o + UP * L_ * 0.95 + out * L_ * lean
        V = np.array([o - w * wd, o + w * wd, p1 - w * wd * 0.85, p1 + w * wd * 0.85, p2 - w * wd * 0.5, p2 + w * wd * 0.5, p3]); c_ = r.uniform(0.82, 1.12)
        m = (base + tipc) / 2; C = np.array([base, base, m * 0.9, m * 0.9, (m + tipc) / 2, (m + tipc) / 2, tipc]) * c_
        N = np.tile(unit(UP * 0.95 + out * 0.12), (7, 1))
        b.add(V, [(0, 1, 3), (0, 3, 2), (2, 3, 5), (2, 5, 4), (4, 5, 6)], C, np.zeros((7, 2)), N)
        if flower is not None and k % 5 == 0 and lod == 0:
            c = p3 + UP * 0.04; a = np.arange(5) * 2 * np.pi / 5; Vf = np.vstack([[c], c + np.c_[np.cos(a), np.sin(a), 0.25 * np.ones(5)] * 0.06])
            b.add(Vf, [(0, 1 + i, 1 + (i + 1) % 5) for i in range(5)], np.vstack([[np.array([0.9, 0.75, 0.15])], np.tile(flower, (5, 1))]), np.zeros((6, 2)), np.tile(UP, (6, 1)))
    return b, None, 1.0


def rock(seed, lod=0, squash=0.7, tall=False, tint=(0.20, 0.185, 0.165)):
    """Boulder: a subdivided icosahedron pushed around by layered noise, with flattened bedding planes."""
    r = np.random.default_rng(seed); t = (1 + 5 ** 0.5) / 2
    V = np.array([(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)], float)
    F = np.array([(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)])
    V /= np.linalg.norm(V, axis=1)[:, None]
    for _ in range(2 if lod == 0 else 1):
        cache = {}; V = list(V); nf = []
        def mid(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache: m = unit(V[a] + V[b]); cache[key] = len(V); V.append(m)
            return cache[key]
        for a, b, c in F:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a); nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        V = np.array(V); F = np.array(nf)
    dirs = r.normal(0, 1, (13, 3)); dirs /= np.linalg.norm(dirs, axis=1)[:, None]; S = V.copy()
    for d in dirs:                                                         # cut flat facets
        lim = r.uniform(0.36, 0.72); h = S @ d; S = S - np.outer(np.maximum(h - lim, 0) * 0.92, d)
    f1 = r.normal(0, 1, (4, 3)) * 1.6; ph = r.uniform(0, 6.28, 4)
    S = S * (1 + 0.05 * sum(np.sin(V @ f + p) for f, p in zip(f1, ph)))[:, None]
    S = S * ((1.0, r.uniform(0.7, 1.0), squash) if not tall else (0.55, 0.5, 1.9)); S[:, 2] += 0.25 * squash if not tall else 1.2
    Vf = S[F].reshape(-1, 3); Ff = np.arange(len(Vf)).reshape(-1, 3)
    fn = np.cross(S[F[:, 1]] - S[F[:, 0]], S[F[:, 2]] - S[F[:, 0]]); fn /= np.linalg.norm(fn, axis=1)[:, None]
    vn = np.zeros_like(S); np.add.at(vn, F.ravel(), np.repeat(fn, 3, 0)); vn /= np.linalg.norm(vn, axis=1)[:, None]
    N = 0.85 * np.repeat(fn, 3, 0) + 0.15 * vn[F].reshape(-1, 3)
    an = np.abs(np.repeat(fn, 3, 0)); U = np.where((an[:, 2:3] > an[:, 0:1]) & (an[:, 2:3] > an[:, 1:2]), Vf[:, :2], np.where(an[:, 0:1] > an[:, 1:2], Vf[:, 1:], Vf[:, ::2])) * 1.4
    shade = (0.8 + 0.28 * np.clip(N[:, 2], -0.3, 1))[:, None] * np.asarray(tint)
    b = MB(); b.add(Vf, Ff, shade, U, N)
    return b, None, 1.0


def _rock_hq(**kw):
    import isle_wild_hq as W; return W.rock_mb(**kw)                      # art sheet 07 boulders


# name: (builder, kwargs, kind)   kind: tree (bark + leaves), painted (vertex colours), rock
SPECIES = {
    'spruce': (spruce, dict(seed=3), 'tree'), 'spruce_b': (spruce, dict(seed=8, hgt=16.0, spread=1.22), 'tree'), 'pine': (pine, dict(seed=5), 'tree'),
    'spruce_snow': (spruce, dict(seed=4, snow=True), 'tree'),
    'oak': (broadleaf, dict(seed=7), 'tree'), 'oak_b': (broadleaf, dict(seed=12, hgt=11.0, wide=1.2, leafcol=(0.8, 0.86, 0.42), fork=0.26), 'tree'),
    'fruit': (broadleaf, dict(seed=21, hgt=5.2, wide=1.25, leafcol=(0.7, 0.95, 0.45), fork=0.3), 'tree'),
    'birch': (birch, dict(seed=9), 'tree'), 'palm': (palm, dict(seed=6), 'tree'), 'palm_b': (palm, dict(seed=15), 'tree'), 'cypress': (cypress, dict(seed=2), 'tree'),
    'bush': (bush, dict(seed=1), 'tree'), 'cactus': (cactus, dict(seed=3), 'painted'), 'cactus_b': (cactus, dict(seed=10), 'painted'),
    'grass': (grass, dict(seed=1), 'painted'), 'grass_tall': (grass, dict(seed=2, tall=True), 'painted'),
    'flowers_red': (grass, dict(seed=3, flower=np.array([0.85, 0.12, 0.08])), 'painted'), 'flowers_white': (grass, dict(seed=4, flower=np.array([0.95, 0.93, 0.85])), 'painted'),
    'flowers_violet': (grass, dict(seed=5, flower=np.array([0.5, 0.25, 0.75])), 'painted'),
    'rock': (_rock_hq, dict(seed=1), 'rock'), 'rock_b': (_rock_hq, dict(seed=2, squash=0.5), 'rock'), 'rock_c': (_rock_hq, dict(seed=5, squash=0.95), 'rock'), 'sandstone': (_rock_hq, dict(seed=7, squash=0.8, tint=(0.52, 0.29, 0.16), strata=0.8), 'rock'), 'sandstone_spire': (_rock_hq, dict(seed=3, tall=True, tint=(0.54, 0.30, 0.17)), 'rock'),
}
# impostor atlas cell (old card index) -> species choices
CARD_SPECIES = {0: ('spruce',), 1: ('spruce_b', 'pine'), 2: ('oak', 'oak_b'), 3: ('spruce_snow',), 4: ('birch',), 5: ('palm', 'palm_b')}


# ------------------------------------------------------------------ textures
def leaf_atlas(N=512):
    """2 x 2 atlas of leaf sprays, alpha cut-out. Returns float RGBA with row 0 at the bottom."""
    from PIL import Image, ImageDraw
    S = N * 2; out = np.zeros((2 * N, 2 * N, 4))

    def finish(im):
        a = np.asarray(im.resize((N, N), Image.LANCZOS), float)[::-1] / 255.0; m = a[..., 3] > 0.4
        if m.any(): a[~m, :3] = a[m, :3].mean(0)
        return a

    def P(u, v): return (u * S, (1 - v) * S)

    # --- conifer spray
    r = np.random.default_rng(1); im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def needles(p0, p1, ln, dens, wd):
        p0 = np.array(p0); p1 = np.array(p1); ax = p1 - p0; L_ = np.linalg.norm(ax); ax /= L_; nr = np.array([-ax[1], ax[0]])
        for s in np.arange(0, L_, dens):
            for sg in (-1, 1):
                q = p0 + ax * s; e = q + (ax * 0.75 + nr * sg * r.uniform(0.5, 0.95)) * ln * r.uniform(0.7, 1.1) * (1 - 0.4 * s / L_)
                g = r.uniform(0.75, 1.25); col = (int(86 * g + 30 * s / L_), int(150 * g + 34 * s / L_), int(76 * g), 255)
                d.line([P(*q), P(*e)], fill=col, width=wd)
    for t in np.linspace(0.05, 0.93, 15):
        env = (1 - t) ** 0.55 * (0.4 + 0.6 * min(1, t * 6)); L_ = 0.44 * env
        for sg in (-1, 1):
            p0 = np.array([0.5, 0.02 + 0.95 * t]); p1 = p0 + np.array([sg * 0.84, 0.54]) * L_ * r.uniform(0.85, 1.1)
            needles(p0, p1, 0.05, 0.011, 5); d.line([P(*p0), P(*p1)], fill=(58, 42, 28, 255), width=5)
            for u in (0.4, 0.7):
                q0 = p0 + (p1 - p0) * u; needles(q0, q0 + np.array([sg * 0.3, 0.9]) * L_ * 0.4, 0.04, 0.012, 4); needles(q0, q0 + np.array([sg * 1.0, 0.1]) * L_ * 0.32, 0.04, 0.012, 4)
    needles((0.5, 0.02), (0.5, 0.99), 0.05, 0.01, 5); d.line([P(0.5, 0), P(0.5, 0.9)], fill=(62, 45, 30, 255), width=9)
    import os as _os2
    _f3 = _os2.path.join(_os2.path.dirname(_os2.path.abspath(__file__)), 'photo', 'Leaf003_%s.raw')
    if _os2.path.exists(_f3 % 'Color'):                                      # photographed feathery frond (ambientCG Leaf003, CC0) layered over the needles
        cc = np.fromfile(_f3 % 'Color', np.uint8).reshape(512, 512, 4)[:, :256, :3]; oo = np.fromfile(_f3 % 'Opacity', np.uint8).reshape(512, 512, 4)[:, :256, 0]
        ys, xs = np.where(oo > 128); cc = cc[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(float); oo = oo[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        g_ = cc.mean(2, keepdims=True); cc = np.clip(g_ / max(g_[oo > 128].mean(), 1.0) * np.array([52, 84, 46]), 0, 255)
        FR = Image.fromarray(np.dstack([cc, oo]).astype(np.uint8), 'RGBA').rotate(180, expand=True)
        for t in np.linspace(0.06, 0.92, 22):
            env = (1 - t) ** 0.55 * (0.4 + 0.6 * min(1, t * 6)); L_ = 0.44 * env
            for sg in (-1, 1):
                ang = math.atan2(0.54, sg * 0.84) + r.uniform(-0.15, 0.15); ln = L_ * S * r.uniform(0.7, 0.95)
                st = FR.resize((max(4, int(ln * 0.45)), max(6, int(ln))), Image.LANCZOS)
                arr = np.asarray(st, float); arr[..., :3] *= r.uniform(0.8, 1.15); st = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGBA').rotate(math.degrees(ang) - 90, expand=True, resample=Image.BICUBIC)
                c0 = np.array([0.5, 0.02 + 0.95 * t]) + np.array([math.cos(ang), math.sin(ang)]) * L_ * 0.45; cp = P(*c0)
                im.alpha_composite(st, (int(cp[0] - st.width / 2), int(cp[1] - st.height / 2)))
    out[N:, :N] = 0; out[:N, :N] = finish(im)

    # --- broadleaf cluster
    import os as _os
    _src = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'photo', 'Leaf001_%s.raw')
    STAMP = None
    if _os.path.exists(_src % 'Color'):                                      # photographed leaf (ambientCG Leaf001, CC0) used as the stamp
        cc = np.fromfile(_src % 'Color', np.uint8).reshape(512, 512, 4)[:, :256, :3]; oo = np.fromfile(_src % 'Opacity', np.uint8).reshape(512, 512, 4)[:, :256, 0]
        ys, xs = np.where(oo > 128); cc = cc[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; oo = oo[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        STAMP = Image.fromarray(np.dstack([cc, oo]).astype(np.uint8), 'RGBA').rotate(180, expand=True)   # stem at the bottom -> leaf points +y

    def leafshape(c, ang, ln, wd, col, vein=True):
        if STAMP is not None:
            h_ = max(4, int(ln * S)); w_ = max(3, int(wd * S * 1.15)); st = STAMP.resize((w_, h_), Image.LANCZOS)
            arr = np.asarray(st, float); g_ = np.array(col[:3]) / np.array([136, 192, 80]); arr[..., :3] = np.clip(arr[..., :3] * g_ * np.array([0.95, 1.0, 0.85]), 0, 255)
            st = Image.fromarray(arr.astype(np.uint8), 'RGBA').rotate(math.degrees(ang) - 90, expand=True, resample=Image.BICUBIC)
            ax = np.array([math.cos(ang), math.sin(ang)]); cen = np.asarray(P(*(c + ax * ln * 0.5)))
            im.alpha_composite(st, (int(cen[0] - st.width / 2), int(cen[1] - st.height / 2))); return
        ax = np.array([math.cos(ang), math.sin(ang)]); nr = np.array([-ax[1], ax[0]]); pts = []
        for s in np.linspace(0, 1, 9): pts.append(c + ax * ln * s + nr * wd * math.sin(np.pi * s ** 0.8) * 0.5)
        for s in np.linspace(1, 0, 9): pts.append(c + ax * ln * s - nr * wd * math.sin(np.pi * s ** 0.8) * 0.5)
        d.polygon([P(*p) for p in pts], fill=col)
        if vein: d.line([P(*c), P(*(c + ax * ln * 0.92))], fill=tuple(int(v * 0.72) for v in col[:3]) + (255,), width=3)
    r = np.random.default_rng(2); im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    twigs = [((0.5, 0.0), (0.5, 0.92))] + [((0.5, 0.1 + 0.13 * k), (0.5 + sg * (0.40 - 0.035 * k), 0.34 + 0.115 * k)) for k in range(6) for sg in (-1, 1)]
    for layer, shade in ((0, 0.6), (1, 0.82), (2, 1.0)):
        for a_, b_ in twigs:
            a_ = np.array(a_); b_ = np.array(b_)
            if layer == 1: d.line([P(*a_), P(*b_)], fill=(70, 52, 34, 255), width=7)
            for s in np.linspace(0.12, 1.0, 9):
                q = a_ + (b_ - a_) * s + r.normal(0, 0.012, 2); base_ang = math.atan2(b_[1] - a_[1], b_[0] - a_[0])
                for sg in (-1, 1):
                    g = r.uniform(0.8, 1.2) * shade
                    leafshape(q, base_ang + sg * r.uniform(0.5, 1.25), r.uniform(0.085, 0.125), r.uniform(0.05, 0.07), (int(136 * g), int(192 * g), int(80 * g), 255), layer > 0)
    out[:N, N:] = finish(im)

    # --- birch: hanging twigs with small leaves (twig base at the bottom of the cell)
    r = np.random.default_rng(3); im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k in range(9):
        x0 = 0.5 + (k - 4) * 0.02; x1 = 0.5 + (k - 4) * 0.108 + r.uniform(-0.02, 0.02); ln = r.uniform(0.72, 0.97); pts = [np.array([x0 + (x1 - x0) * s ** 0.6, 0.01 + ln * s]) for s in np.linspace(0, 1, 16)]
        d.line([P(*p) for p in pts], fill=(64, 48, 36, 255), width=4)
        for p in pts[1:]:
            for sg in (-1, 1):
                g = r.uniform(0.8, 1.2); leafshape(p + r.normal(0, 0.008, 2), np.pi / 2 + sg * r.uniform(0.5, 1.5), r.uniform(0.05, 0.07), r.uniform(0.04, 0.052), (int(150 * g), int(186 * g), int(70 * g), 255), False)
    out[N:, :N] = finish(im)

    # --- palm frond
    r = np.random.default_rng(4); im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for t in np.linspace(0.04, 0.985, 46):
        env = math.sin(np.pi * min(1, t * 0.9 + 0.08)) ** 0.5 * 0.47
        for sg in (-1, 1):
            p0 = np.array([0.5, t]); p1 = p0 + np.array([sg * 0.93, 0.36]) * env * r.uniform(0.86, 1.05); nr = np.array([0.0, 0.016])
            g = r.uniform(0.8, 1.2); d.polygon([P(*(p0 - nr)), P(*(p0 + nr)), P(*p1)], fill=(int(128 * g), int(188 * g), int(76 * g), 255))
    d.line([P(0.5, 0), P(0.5, 0.99)], fill=(120, 132, 60, 255), width=10)
    out[N:, N:] = finish(im)
    out[..., 3] = (out[..., 3] > 0.4).astype(float)
    return out


def bark_height(n=512):
    from isle_lib import fft_noise
    v, u = np.mgrid[0:n, 0:n] / n; warp = fft_noise(n, 1.6, 71); fine = fft_noise(n, 0.7, 72)
    ridge = np.abs(np.sin(np.pi * (9 * u + 1.3 * warp + 0.25 * np.sin(2 * np.pi * v * 2)))) ** 0.55
    crack = (np.abs(fft_noise(n, 1.9, 73) - 0.5) < 0.012) * 0.35
    return np.clip(0.42 + 0.5 * ridge + 0.16 * (fine - 0.5) - crack, 0, 1)


# ------------------------------------------------------------------ Blender objects
def make_object(name, parts):
    """parts: list of (MB, material). One mesh, one material slot per part."""
    import bpy
    Vs = []; Fs = []; Cs = []; Us = []; Ns = []; mi = []; off = 0; mats = []
    for mb, mat in parts:
        if mb is None or not mb.V: continue
        V, F, C, U, N = mb.arrays(); Vs.append(V); Fs.append(F + off); Cs.append(C); Us.append(U); Ns.append(N); mi.append(np.full(len(F), len(mats))); mats.append(mat); off += len(V)
    V = np.vstack(Vs); F = np.vstack(Fs); C = np.vstack(Cs); U = np.vstack(Us); N = np.vstack(Ns); mi = np.concatenate(mi)
    me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co', V.astype(np.float32).ravel())
    me.loops.add(len(F) * 3); me.loops.foreach_set('vertex_index', F.astype(np.int32).ravel()); me.polygons.add(len(F))
    me.polygons.foreach_set('loop_start', np.arange(len(F), dtype=np.int32) * 3); me.polygons.foreach_set('loop_total', np.full(len(F), 3, np.int32))
    for m in mats: me.materials.append(m)
    me.polygons.foreach_set('material_index', mi.astype(np.int32)); me.update(calc_edges=True)
    me.polygons.foreach_set('use_smooth', np.ones(len(F), bool))
    li = F.astype(np.int32).ravel()
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER'); ca.data.foreach_set('color', np.c_[np.clip(C[li], 0, 1), np.ones(len(li))].astype(np.float32).ravel())
    uv = me.uv_layers.new(name='UVMap'); uv.data.foreach_set('uv', U[li].astype(np.float32).ravel())
    me.normals_split_custom_set_from_vertices([tuple(v) for v in N])
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


# Art sheet 04 (approved 19 Nov 2026): these species are built by isle_trees_hq. Map name -> (HQ species, kwargs override, kind).
# LOD0 in the map is the game-weight version (lod=2), LOD1 the far one; the hero version (lod=0) is for renders only.
HQMAP = {'spruce': ('spruce', dict(seed=6, hgt=19.0)), 'spruce_b': ('spruce', dict(seed=11, hgt=16.0)), 'pine': ('spruce', dict(seed=14, hgt=17.0)),
         'oak': ('oak', dict(seed=2)), 'oak_b': ('oak', dict(seed=21)), 'plane': ('plane', dict(seed=1)), 'plane_b': ('plane', dict(seed=33)),
         'birch': ('birch', dict(seed=3)), 'fruit': ('olive', dict(seed=4)), 'olive': ('olive', dict(seed=4)),
         'palm': ('date_palm', dict(seed=8)), 'palm_b': ('stone_pine', dict(seed=5)), 'cypress': ('cypress', dict(seed=7)),
         'bush': ('laurel', {}), 'oleander': ('oleander', {}), 'hedge': ('hedge', {}), 'fern': ('fern', {}),
         'cactus': ('prickly_pear', {}), 'cactus_b': ('agave', {}),
         'grass': ('grass_hq', {}), 'grass_tall': ('grass_hq', dict(seed=26, size=1.15, n=6)),
         'flowers_red': ('flowers_hq', {}), 'flowers_white': ('flowers_hq', dict(seed=27)), 'flowers_violet': ('flowers_hq', dict(seed=28))}


def _hq_mats(mats):
    """Leaf atlas and bark materials of art sheet 04, created once and kept in `mats`."""
    if 'leafhq' in mats: return
    import isle_lib as L, flora_atlas_hq as FA
    mats['leafhq'] = L.new_mat('LeavesHQ', 1.0, image=L.make_image('leaf_atlas_hq', FA.atlas()[::-1].copy()), vcol=True, double=True, cutout=True)
    try: mats['leafhq'].node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.12
    except Exception: pass
    for k in ('rough', 'plane', 'birch', 'palm', 'olive'):
        c, h = FA.bark(k); mats['bark_' + k] = L.new_mat('Bark_' + k, 0.88, image=L.make_image('bark_' + k, c[::-1].copy()), vcol=True, normal=L.nmap('bark_n_' + k, h[::-1].copy(), 6.0))


def _build_hq(name, mats):
    import isle_trees_hq as TH
    hs, kw = HQMAP[name]; fn, kw0, bk = TH.SPECIES[hs]; kw = dict(kw0, **kw); _hq_mats(mats); e = {}
    for lod, gl in ((0, 2), (1, 1)):
        b, l, h = fn(lod=gl, **kw); parts = []
        if b is not None and b.V: parts.append((b, mats['bark_' + bk] if bk else mats['painted']))
        if l is not None and l.V: parts.append((l, mats['leafhq']))
        e['lod%d' % lod] = make_object('FLORA_%s_LOD%d' % (name, lod), parts); e['t%d' % lod] = (b.tris() if b is not None else 0) + (l.tris() if l is not None else 0)
    e['h'] = h; e['kind'] = 'tree' if bk else 'painted'
    return e


def build_library(mats, names=None):
    """mats: dict(bark=, leaf=, painted=, rock=). Returns {species: dict(h=, lod0=obj, lod1=obj, tris=(n0, n1))}."""
    lib = {}
    for name in list(SPECIES) + [k for k in HQMAP if k not in SPECIES]:
        if names and name not in names: continue
        if name in HQMAP: lib[name] = _build_hq(name, mats); continue
        fn, kw, kind = SPECIES[name]
        e = {}
        for lod in (0, 1):
            a, b, h = fn(lod=lod, **kw)
            parts = [(a, mats['bark']), (b, mats['leaf'])] if kind == 'tree' else [(a, mats['painted' if kind == 'painted' else 'rock'])]
            e['lod%d' % lod] = make_object('FLORA_%s_LOD%d' % (name, lod), parts); e['t%d' % lod] = a.tris() + (b.tris() if b is not None else 0)
        e['h'] = h; e['kind'] = kind; lib[name] = e
    return lib

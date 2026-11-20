"""Art sheet 04 plant library: branching trees with real limbs and painted twig sprays, palms, shrubs, ground cover and desert plants.
Each species is built at real size, base at the origin, as (bark MB, leaf MB, height). Uses the MB / tube / make_object helpers of isle_flora."""
import math
import numpy as np
import flora_atlas_hq as FA
from isle_flora import MB, tube, unit, perp, UP

# ------------------------------------------------------------------ cards
def card(mb, base, up, side, h, w, cell, col, centre=None, bend=0.0, segs=2, lift=0.3, mirror=False):
    """Twig spray card: rises from `base` along `up` (length h), `w` wide along `side`, sagging by `bend` toward the tip."""
    base = np.asarray(base, float); up = unit(up); side = unit(side); t = np.linspace(0, 1, segs + 1)
    nrm = unit(np.cross(side, up)); cen = base + up * h * t[:, None] + nrm * (bend * h * t ** 2)[:, None] - UP * (abs(bend) * 0.5 * h * t ** 2)[:, None]
    u0, v0, u1, v1 = FA.cell_uv(cell)
    if mirror: u0, u1 = u1, u0
    V = np.vstack([cen - side * w / 2, cen + side * w / 2]); m = segs + 1
    U = np.vstack([np.c_[np.full(m, u0), v0 + (v1 - v0) * t], np.c_[np.full(m, u1), v0 + (v1 - v0) * t]])
    i = np.arange(segs); F = np.vstack([np.c_[i, m + i, m + i + 1], np.c_[i, m + i + 1, i + 1]])
    if centre is None: N = np.tile(nrm * 0.4 + UP * 0.6, (len(V), 1))
    else:
        N = V - np.asarray(centre, float); N /= np.maximum(np.linalg.norm(N, axis=1), 1e-6)[:, None]; N = N * (1 - lift) + UP * lift
    mb.add(V, F, np.tile(np.asarray(col, float), (len(V), 1)), U, N)


def strip(mb, P, side, w, cell, col, centre=None, lift=0.3, mirror=False, half=False, flipv=False):
    """Card following a polyline P (e.g. a palm frond): UV v runs along it. half: the strip lies on one side of P only."""
    P = np.asarray(P, float); m = len(P); t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; t /= t[-1]
    W = np.broadcast_to(np.asarray(w, float), (m,)); side = np.asarray(side, float)
    if side.ndim == 1: side = np.tile(side, (m, 1))
    u0, v0, u1, v1 = FA.cell_uv(cell)
    if mirror: u0, u1 = u1, u0
    if flipv: v0, v1 = v1, v0
    L = P if half else P - side * W[:, None] / 2; R = P + side * W[:, None] if half else P + side * W[:, None] / 2
    V = np.vstack([L, R]); U = np.vstack([np.c_[np.full(m, u0), v0 + (v1 - v0) * t], np.c_[np.full(m, u1), v0 + (v1 - v0) * t]])
    i = np.arange(m - 1); F = np.vstack([np.c_[i, m + i, m + i + 1], np.c_[i, m + i + 1, i + 1]])
    if centre is None: N = np.tile(UP, (len(V), 1))
    else:
        N = V - np.asarray(centre, float); N /= np.maximum(np.linalg.norm(N, axis=1), 1e-6)[:, None]; N = N * (1 - lift) + UP * lift
    mb.add(V, F, np.tile(np.asarray(col, float), (len(V), 1)), U, N)


# ------------------------------------------------------------------ branching
class Sp:
    def __init__(s, **k): s.__dict__.update(k)


def grow(T, r, p, d, L, rad, depth, sp, tips, lod):
    """One limb: a bent tapered tube, then children spread along it. Terminal limbs record twig anchors in `tips`."""
    k = max(2, int(3 + depth * 1.5)) if lod == 0 else (max(2, int(2 + depth * 0.8)) if lod == 2 else 2)
    P = [np.asarray(p, float)]; dd = unit(d)
    for i in range(k):
        t = (i + 1) / k
        dd = unit(dd + r.normal(0, sp.wob, 3) * (1, 1, 0.5) + UP * sp.photo[depth] - UP * sp.droop[depth] * t)
        P.append(P[-1] + dd * L / k)
    P = np.array(P); R = np.linspace(rad, rad * sp.taper, k + 1)
    seg = (12, 10, 7, 5, 4)[min(4, sp.levels - depth)] if lod == 0 else max(3, (8, 6, 4, 3, 3)[min(4, sp.levels - depth)] // 1)
    if lod == 0 or (lod == 2 and rad > 0.025) or rad > 0.06: tube(T.bark, P, R, seg, sp.barkcol, urep=max(1, round(rad * 6)), vlen=max(0.6, rad * 4))
    if depth == 0:
        for f in sp.twig_at: tips.append((P[int(f * k)], dd, rad))
        return
    nch = sp.nch[depth] if lod == 0 else (max(2, sp.nch[depth] - (1 if depth == 1 else 0) - (1 if depth == 2 and sp.nch[depth] > 4 else 0)) if lod == 2 else max(1, int(sp.nch[depth] * 0.6)))
    for j in range(nch):
        f = sp.start[depth] + (1 - sp.start[depth]) * (j + r.uniform(0.2, 0.8)) / nch; idx = f * k; i0 = min(int(idx), k - 1)
        q = P[i0] + (P[i0 + 1] - P[i0]) * (idx - i0); dpar = unit(P[i0 + 1] - P[i0])
        az = j * 2.39996 + r.uniform(-0.4, 0.4); a = perp(dpar); b = np.cross(dpar, a)
        sd = a * math.cos(az) + b * math.sin(az); ang = sp.ang[depth] * r.uniform(0.8, 1.2)
        dn = unit(dpar * math.cos(ang) + sd * math.sin(ang))
        ln = L * sp.lr[depth] * r.uniform(0.8, 1.15) * (sp.shape(f) if sp.shape else 1.0)
        grow(T, r, q, dn, ln, max(0.012, rad * sp.rr * (1.0 - 0.35 * f)), depth - 1, sp, tips, lod)
    if sp.apex and depth == sp.levels:                                              # leader continues
        grow(T, r, P[-1], dd, L * 0.5, rad * sp.taper, depth - 1, sp, tips, lod)


def foliage(T, r, tips, sp, cen, lod):
    """Twig sprays at the limb ends: two crossed cards per twig, each turned to face out of the crown."""
    step = 1 if lod in (0, 2) else 3
    if lod == 2: tips = [t for i, t in enumerate(tips) if i % len(sp.twig_at) == len(sp.twig_at) - 1 or i % 2 == 0]
    for p, d, rad in tips[::step]:
        out = unit(p - cen + r.normal(0, 0.2, 3)); s_ = sp.leaf * r.uniform(0.8, 1.2) * {0: 1.0, 2: 1.45, 1: 1.8}[lod]
        hgt_f = np.clip((p[2] - cen[2]) / max(sp.crown_r, 1) * 0.5 + 0.5, 0, 1)
        col = np.asarray(sp.leafcol) * r.uniform(0.85, 1.1) * (0.82 + 0.25 * hgt_f)          # inner and lower sprays darker
        up = unit(d * 0.6 + out * 0.6 + UP * sp.leafup + r.normal(0, 0.25, 3)); side = unit(np.cross(up, out) + r.normal(0, 0.3, 3))
        cell = sp.cell if not isinstance(sp.cell, tuple) else sp.cell[int(r.integers(len(sp.cell)))]
        card(T.leaf, p - up * s_ * 0.15, up, side, s_, s_ * sp.aspect, cell, col, cen, bend=sp.bend, segs=2 if lod == 0 else 1, lift=0.25, mirror=r.random() < 0.5)
        if lod == 2 and sp.cross and r.random() < 0.5:
            card(T.leaf, p - up * s_ * 0.1, unit(up + out * 0.3), unit(np.cross(up, side)), s_ * 0.9, s_ * sp.aspect * 0.9, cell, col * 0.92, cen, segs=1, lift=0.25, mirror=r.random() < 0.5)
        if lod == 0 and sp.cross:
            side2 = unit(np.cross(up, side)); card(T.leaf, p - up * s_ * 0.1, unit(up + out * 0.3), side2, s_ * 0.92, s_ * sp.aspect * 0.9, cell, col * 0.92, cen, bend=sp.bend, segs=2, lift=0.25, mirror=r.random() < 0.5)


class Tree:
    def __init__(s): s.bark = MB(); s.leaf = MB()


def deciduous(seed, lod, sp):
    r = np.random.default_rng(seed); T = Tree(); tips = []
    stems = sp.stems if hasattr(sp, 'stems') else 1
    for st in range(stems):
        lean = unit(np.array([math.cos(st * 2.1 + seed), math.sin(st * 2.1 + seed), 0]) * sp.lean + UP)
        P = [np.zeros(3)]; dd = lean
        for i in range(6):
            dd = unit(dd + r.normal(0, sp.trunk_wob, 3) * (1, 1, 0.3)); P.append(P[-1] + dd * sp.trunk / 6)
        P = np.array(P); R = np.interp(np.linspace(0, 1, 7), [0, 0.08, 1], [sp.rad * 1.45, sp.rad, sp.rad * 0.78])
        tube(T.bark, P, R, {0: 14, 2: 9}.get(lod, 7), sp.barkcol, urep=max(1, round(sp.rad * 5)), vlen=max(1.0, sp.rad * 3))
        for j in range(sp.limbs):
            az = j * 2 * math.pi / sp.limbs + r.uniform(-0.4, 0.4) + st; f = sp.limb_z[0] + (sp.limb_z[1] - sp.limb_z[0]) * r.random()
            idx = f * 6; i0 = min(int(idx), 5); q = P[i0] + (P[i0 + 1] - P[i0]) * (idx - i0)
            d = unit(np.array([math.cos(az), math.sin(az), 0]) * math.sin(sp.limb_ang) + UP * math.cos(sp.limb_ang))
            grow(T, r, q, d, sp.limb_len * r.uniform(0.85, 1.15), sp.rad * 0.55, sp.levels, sp, tips, lod)
        if sp.apex: grow(T, r, P[-1], unit(dd + UP), sp.limb_len * 0.9, sp.rad * 0.6, sp.levels, sp, tips, lod)
    ps = np.array([t[0] for t in tips]); cen = np.r_[ps[:, :2].mean(0), ps[:, 2].mean()]; sp.crown_r = float(np.ptp(ps[:, 2]) / 2 + 0.1)
    foliage(T, r, tips, sp, cen, lod)
    h = float(max(np.vstack(T.leaf.V)[:, 2].max(), np.vstack(T.bark.V)[:, 2].max()))
    return T.bark, T.leaf, h


# ------------------------------------------------------------------ species presets
BARK_ROUGH = np.array([1.0, 1.0, 1.0])

def plane(seed=1, lod=0):            # London plane: clear trunk, upswept scaffold limbs, big rounded crown (city avenues)
    sp = Sp(trunk=4.2, rad=0.42, lean=0.04, trunk_wob=0.04, limbs=4, limb_z=(0.75, 1.0), limb_ang=0.62, limb_len=5.2, levels=3, apex=True,
            nch={3: 5, 2: 4, 1: 4}, ang={3: 0.75, 2: 0.8, 1: 0.9}, lr={3: 0.62, 2: 0.6, 1: 0.55}, start={3: 0.25, 2: 0.3, 1: 0.35}, rr=0.55, taper=0.6,
            wob=0.12, photo={3: 0.06, 2: 0.04, 1: 0.0, 0: 0.0}, droop={3: 0.02, 2: 0.06, 1: 0.1, 0: 0.15}, shape=None, twig_at=(0.5, 1.0),
            leaf=1.9, aspect=0.95, leafcol=(1.0, 1.0, 1.0), leafup=0.3, cell='plane', cross=True, bend=0.12, barkcol=(1, 1, 1))
    return deciduous(seed, lod, sp)


def oak(seed=2, lod=0):              # field oak: short stout trunk, crooked wide limbs, broad dome
    sp = Sp(trunk=2.6, rad=0.62, lean=0.06, trunk_wob=0.06, limbs=5, limb_z=(0.7, 1.0), limb_ang=1.0, limb_len=5.6, levels=3, apex=True,
            nch={3: 5, 2: 4, 1: 4}, ang={3: 0.85, 2: 0.85, 1: 0.95}, lr={3: 0.6, 2: 0.6, 1: 0.55}, start={3: 0.2, 2: 0.25, 1: 0.3}, rr=0.55, taper=0.55,
            wob=0.22, photo={3: 0.1, 2: 0.06, 1: 0.03, 0: 0.0}, droop={3: 0.05, 2: 0.04, 1: 0.06, 0: 0.1}, shape=None, twig_at=(0.5, 1.0),
            leaf=1.7, aspect=1.0, leafcol=(1.2, 1.2, 1.15), leafup=0.35, cell='oak', cross=True, bend=0.1, barkcol=(1, 1, 1))
    return deciduous(seed, lod, sp)


def birch(seed=3, lod=0):            # silver birch: slender white stem, light airy crown with hanging twigs
    sp = Sp(trunk=7.5, rad=0.2, lean=0.08, trunk_wob=0.03, limbs=9, limb_z=(0.35, 1.0), limb_ang=0.75, limb_len=3.4, levels=2, apex=True,
            nch={2: 5, 1: 5}, ang={2: 0.7, 1: 0.9}, lr={2: 0.62, 1: 0.6}, start={2: 0.2, 1: 0.3}, rr=0.5, taper=0.5,
            wob=0.1, photo={2: 0.08, 1: 0.0, 0: 0.0}, droop={2: 0.05, 1: 0.35, 0: 0.5}, shape=None, twig_at=(0.4, 0.8, 1.0),
            leaf=1.25, aspect=0.75, leafcol=(1.0, 1.0, 1.0), leafup=-0.4, cell='birch', cross=True, bend=0.25, barkcol=(1, 1, 1))
    return deciduous(seed, lod, sp)


def olive(seed=4, lod=0):            # olive: three twisted stems from one gnarled base, silver-grey open crown (farms, hills)
    sp = Sp(stems=3, trunk=1.8, rad=0.22, lean=0.45, trunk_wob=0.2, limbs=2, limb_z=(0.6, 1.0), limb_ang=0.75, limb_len=2.6, levels=3, apex=False,
            nch={3: 3, 2: 3, 1: 3}, ang={3: 0.85, 2: 0.9, 1: 0.95}, lr={3: 0.62, 2: 0.6, 1: 0.6}, start={3: 0.2, 2: 0.25, 1: 0.3}, rr=0.6, taper=0.55,
            wob=0.25, photo={3: 0.08, 2: 0.03, 1: 0.0, 0: 0.0}, droop={3: 0.02, 2: 0.05, 1: 0.12, 0: 0.15}, shape=None, twig_at=(0.6, 1.0),
            leaf=1.0, aspect=0.9, leafcol=(1.15, 1.15, 1.15), leafup=0.3, cell='olive', cross=True, bend=0.08, barkcol=(1, 1, 1))
    return deciduous(seed, lod, sp)


def stone_pine(seed=5, lod=0):       # umbrella pine: tall bare curved trunk, flat-topped spreading canopy of needle tufts (coast, parks)
    r = np.random.default_rng(seed); T = Tree(); tips = []
    P = [np.zeros(3)]; dd = unit([0.18, 0.05, 1])
    for i in range(8): dd = unit(dd + r.normal(0, 0.05, 3) * (1, 1, 0.2) - np.array([0.03, 0, 0])); P.append(P[-1] + dd * 1.05)
    P = np.array(P); tube(T.bark, P, np.interp(np.linspace(0, 1, 9), [0, 0.06, 1], [0.6, 0.42, 0.28]), 14 if lod == 0 else 7, (1, 1, 1), urep=2, vlen=1.2)
    sp = Sp(levels=3, nch={3: 3, 2: 3, 1: 4}, ang={3: 0.75, 2: 0.7, 1: 0.8}, lr={3: 0.6, 2: 0.6, 1: 0.5}, start={3: 0.35, 2: 0.4, 1: 0.4}, rr=0.6, taper=0.55,
            wob=0.12, photo={3: 0.0, 2: 0.08, 1: 0.12, 0: 0.15}, droop={3: 0.18, 2: 0.0, 1: 0.0, 0: 0.0}, shape=None, twig_at=(0.5, 1.0), apex=False, barkcol=(1, 1, 1))
    for j in range(5):
        az = j * 2 * math.pi / 5 + r.uniform(-0.3, 0.3); d = unit([math.cos(az), math.sin(az), 0.9])
        grow(T, r, P[-1 - (j % 2)], d, 4.6 * r.uniform(0.85, 1.1), 0.22, 3, sp, tips, lod)
    ps = np.array([t[0] for t in tips]); cen = np.r_[ps[:, :2].mean(0), ps[:, 2].mean() - 1.5]
    for p, d, rad in tips[::{0: 1, 2: 1}.get(lod, 3)]:                                # tufts stand up out of the flat top
        s_ = r.uniform(1.5, 2.1) * {0: 1.0, 2: 1.7}.get(lod, 1.8); col = np.array([1.0, 1.0, 1.0]) * r.uniform(0.82, 1.1)
        for k in range(2 if lod == 0 else 1):
            a = r.uniform(0, math.pi); side = np.array([math.cos(a), math.sin(a), 0]); up = unit(UP + r.normal(0, 0.25, 3) + (p - cen) * np.array([1, 1, 0]) * 0.04)
            card(T.leaf, p - up * s_ * 0.3, up, side, s_, s_ * 1.3, 'pinetuft', col, cen, segs=1, lift=0.5)
    h = float(np.vstack(T.leaf.V)[:, 2].max()); return T.bark, T.leaf, h


def spruce(seed=6, lod=0, hgt=19.0):  # Norway spruce: straight leader, whorls of drooping branches with upturned tips (mountains)
    r = np.random.default_rng(seed); T = Tree(); zs = np.linspace(0, hgt, 10)
    tube(T.bark, np.c_[np.zeros(10), np.zeros(10), zs], np.interp(zs, [0, 1, hgt], [0.42, 0.3, 0.03]), 12 if lod == 0 else 6, (1, 1, 1), urep=2, vlen=1.2)
    cen = np.array([0, 0, hgt * 0.45]); nwh = {0: int(hgt / 0.42), 2: int(hgt / 0.62)}.get(lod, int(hgt / 1.3))
    for w in range(nwh):
        z = 1.4 + (hgt - 1.6) * w / nwh; t = (z - 1.4) / (hgt - 1.4); Lb = (0.45 + 5.0 * (1 - t) ** 0.95) * r.uniform(0.85, 1.1)
        nb = 5 if lod == 0 else 4
        for b in range(nb):
            az = b * 2 * math.pi / nb + w * 0.9 + r.uniform(-0.2, 0.2); d0 = np.array([math.cos(az), math.sin(az), 0.0])
            P = [np.array([0, 0, z])]; dd = unit(d0 + UP * 0.25)
            for i in range(4): dd = unit(dd - UP * (0.22 * (1 - t) if i < 3 else -0.25)); P.append(P[-1] + dd * Lb / 4)
            P = np.array(P)
            if lod == 0: tube(T.bark, P, np.linspace(0.05 + 0.06 * (1 - t), 0.012, 5), 4, (0.8, 0.8, 0.8))
            side = unit(np.cross(UP, d0)); g = r.uniform(0.95, 1.15) * (1.15 + 0.3 * t); col = np.array([1.0, 1.0, 1.0]) * g
            strip(T.leaf, P, unit(side + UP * r.uniform(-0.25, 0.25)), max(1.1, Lb * 1.0) * (1.15 if lod == 2 else 1.0), 'spruce', col, cen, lift=0.45, flipv=True)                      # the branch's spray, flat
            if lod in (0, 2) and Lb > 1.2:
                strip(T.leaf, P - UP * 0.1, unit(side * 0.35 - UP), max(0.7, Lb * 0.7), 'spruce', col * 0.85, cen, lift=0.45, flipv=True)   # hanging side shoots
    for k in range({0: 40, 2: 18}.get(lod, 8)):                                                # upper crown: sprays round the leader fill the comb-like top
        nk_ = {0: 40, 2: 18}.get(lod, 8); t = 0.45 + 0.5 * k / nk_; z = hgt * t; az = k * 2.39996; o = np.array([math.cos(az), math.sin(az), 0])
        rr_ = (1 - t) * 5.0 * 0.55; s_ = 1.0 + 2.6 * (1 - t)
        card(T.leaf, np.array([0, 0, z]) + o * rr_ * 0.3, unit(o + UP * 0.35 - UP * 0.4 * (1 - t)), unit(np.cross(UP, o)), s_ * 1.3, s_ * 1.1, 'spruce', np.array([1.0, 1.0, 1.0]) * r.uniform(0.95, 1.12), cen, segs=2, bend=-0.15, lift=0.45)
    for k in range(3 if lod == 0 else 1):                                                 # leader tuft
        a = k * math.pi / 3; card(T.leaf, [0, 0, hgt - 1.6], UP, [math.cos(a), math.sin(a), 0], 1.8, 1.1, 'spruce', np.array([1.05, 1.08, 1.0]), cen, segs=1)
    return T.bark, T.leaf, hgt


def cypress(seed=7, lod=0, hgt=14.0):  # Italian cypress: tight flame-shaped column of upright sprays (villages, roadsides)
    r = np.random.default_rng(seed); T = Tree(); zs = np.linspace(0, hgt * 0.92, 8)
    tube(T.bark, np.c_[np.zeros(8), np.zeros(8), zs], np.interp(zs, [0, hgt], [0.26, 0.04]), 10 if lod == 0 else 6, (1, 1, 1), urep=1, vlen=1.0)
    cen = np.array([0, 0, hgt * 0.5]); n = {0: 620, 2: 200}.get(lod, 110)
    for k in range(n):
        t = r.uniform(0.04, 0.97); z = hgt * t; rad = 1.55 * math.sin(math.pi * min(1, t * 1.03) ** 0.7) * (1 - 0.3 * t) * r.uniform(0.7, 1.0)
        az = k * 2.39996; o = np.array([math.cos(az), math.sin(az), 0]); p = np.array([0, 0, z]) + o * rad * 0.6
        s_ = r.uniform(1.3, 1.9) * {0: 1.0, 2: 1.35}.get(lod, 1.8); up = unit(UP * 1.6 + o * 0.5 + r.normal(0, 0.15, 3)); side = unit(np.cross(up, o))
        col = np.array([1.0, 1.0, 1.0]) * r.uniform(0.9, 1.15) * (1.05 + 0.35 * t)
        card(T.leaf, p - up * s_ * 0.3, up, side, s_, s_ * 0.8, 'cypress', col, cen, segs=1, lift=0.15)
    return T.bark, T.leaf, hgt


def date_palm(seed=8, lod=0, hgt=10.0):  # date palm: scaly trunk with leaf-base scars, a full head of arching feather fronds (marina, coast)
    r = np.random.default_rng(seed); T = Tree(); n = 10
    zs = np.linspace(0, hgt, n); bx = 0.5 * (zs / hgt) ** 2 + 0.05 * np.sin(zs); P = np.c_[bx, np.zeros(n), zs]
    tube(T.bark, P, np.interp(zs, [0, 0.5, hgt], [0.5, 0.38, 0.34]), 14 if lod == 0 else 7, (1, 1, 1), urep=2, vlen=2.5)
    top = P[-1]; cen = top + np.array([0, 0, 0.5]); nf = {0: 40, 2: 26}.get(lod, 14)
    for f in range(nf):
        az = f * 2.39996; el = r.uniform(-0.6, 1.1) if f > 4 else 1.3; o = np.array([math.cos(az), math.sin(az), 0]); L = r.uniform(3.6, 4.6)
        Q = [top + UP * 0.2]; dd = unit(o * math.cos(el) + UP * math.sin(el))
        for i in range(8): dd = unit(dd - UP * 0.09 * (1 + i / 4)); Q.append(Q[-1] + dd * L / 8)
        Q = np.array(Q); side = unit(np.cross(UP, o)); w = np.r_[np.linspace(0.25, 1.25, 4), np.linspace(1.15, 0.4, 5)][:len(Q)]
        sd = np.array([unit(side - UP * 0.35) for _ in Q]); sd2 = np.array([unit(-side - UP * 0.35) for _ in Q])
        col = np.array([1.0, 1.0, 1.0]) * r.uniform(0.82, 1.1)
        strip(T.leaf, Q, sd, w, 'pinna', col, cen, lift=0.4, half=True); strip(T.leaf, Q, sd2, w, 'pinna', col * 0.95, cen, lift=0.4, half=True, mirror=True)
        if lod == 0: tube(T.bark, Q[:4], np.linspace(0.07, 0.03, 4), 4, (0.95, 0.85, 0.6))
    if lod == 0:                                                                       # skirt of dead fronds
        for f in range(10):
            az = f * 0.63 + 0.3; o = np.array([math.cos(az), math.sin(az), 0]); Q = np.array([top - UP * 0.4, top - UP * 0.4 + o * 0.9 - UP * 1.6, top - UP * 0.4 + o * 1.3 - UP * 3.0])
            strip(T.leaf, Q, unit(np.cross(UP, o)), [0.3, 0.8, 0.5], 'pinna', np.array([0.62, 0.48, 0.3]), cen, lift=0.2, half=True)
    for k in range(6 if lod == 0 else 0):                                              # date clusters
        az = k * 1.05; q = top + np.array([math.cos(az) * 0.5, math.sin(az) * 0.5, -0.3])
        tube(T.bark, [q, q + np.array([math.cos(az) * 0.4, math.sin(az) * 0.4, -0.7])], [0.14, 0.2], 6, (1.3, 0.8, 0.3))
    h = float(np.vstack(T.leaf.V)[:, 2].max()); return T.bark, T.leaf, h


def unit_rows(A): return A / np.maximum(np.linalg.norm(A, axis=1), 1e-9)[:, None]


# ------------------------------------------------------------------ shrubs, ground cover
def shrub(seed=9, lod=0, cell='oleander', size=2.2, n=70, col=(1, 1, 1)):
    r = np.random.default_rng(seed); T = Tree(); cen = np.array([0, 0, size * 0.45])
    for k in range(5): tube(T.bark, [[0, 0, 0], [r.normal(0, 0.3), r.normal(0, 0.3), size * 0.6]], [0.05, 0.02], 4, (0.6, 0.5, 0.4))
    for k in range({0: n, 2: n // 2}.get(lod, n // 4)):
        v = unit(r.normal(0, 1, 3) * (1, 1, 0.7) + UP * 0.5); p = cen + v * size * 0.42 * r.uniform(0.5, 1.0) * np.array([1, 1, 0.9])
        up = unit(v + UP * 0.6 + r.normal(0, 0.2, 3)); side = unit(np.cross(up, v) + r.normal(0, 0.3, 3)); s_ = size * r.uniform(0.38, 0.55) * (1 if lod == 0 else 1.6)
        card(T.leaf, p - up * s_ * 0.4, up, side, s_, s_ * 0.85, cell, np.asarray(col) * r.uniform(0.78, 1.1) * (0.75 + 0.3 * v[2]), cen, segs=1, lift=0.3)
    return T.bark, T.leaf, size


def hedge(seed=10, lod=0, L=3.0, W=1.0, H=1.3):
    """Clipped boxwood hedge block: a dense skin of small twig cards over a box shape."""
    r = np.random.default_rng(seed); T = Tree(); cen = np.array([0, 0, H * 0.4]); n = {0: int(L * W * 70), 2: int(L * W * 30)}.get(lod, int(L * W * 12))
    for k in range(n):
        face = r.integers(5)
        if face == 0: p = np.array([r.uniform(-L / 2, L / 2), r.uniform(-W / 2, W / 2), H]); o = UP
        else:
            sx = (1, -1, 0, 0)[face - 1]; sy = (0, 0, 1, -1)[face - 1]; o = np.array([sx, sy, 0.0])
            p = np.array([sx * L / 2 if sx else r.uniform(-L / 2, L / 2), sy * W / 2 if sy else r.uniform(-W / 2, W / 2), r.uniform(0.05, H)])
        p = p + o * r.uniform(-0.08, 0.02); up = unit(o + r.normal(0, 0.5, 3)); side = unit(np.cross(up, o + r.normal(0, 0.3, 3))); s_ = r.uniform(0.35, 0.5) * (1 if lod == 0 else 2)
        card(T.leaf, p - up * s_ * 0.5, up, side, s_, s_, 'box', np.array([1, 1, 1.0]) * r.uniform(0.78, 1.1), p - o, segs=1, lift=0.1)
    return T.bark, T.leaf, H


def ground_clump(seed=11, lod=0, cell='fern', n=9, size=0.9, arch=0.35, col=(1, 1, 1)):
    r = np.random.default_rng(seed); T = Tree()
    for k in range({0: n, 2: max(3, n // 2)}.get(lod, max(2, n // 3))):
        az = k * 2 * math.pi / n + r.uniform(-0.2, 0.2); o = np.array([math.cos(az), math.sin(az), 0]); up = unit(UP + o * r.uniform(0.3, 0.9)); s_ = size * r.uniform(0.8, 1.15)
        card(T.leaf, o * 0.05, up, unit(np.cross(UP, o)), s_, s_ * 0.9, cell, np.asarray(col) * r.uniform(0.8, 1.1), [0, 0, -0.5], bend=arch, segs=3 if lod == 0 else 1, lift=0.5)
    return None, T.leaf, size


def agave(seed=12, lod=0):
    """Agave rosette: thick tapered leaves with a dark spine tip, real geometry."""
    r = np.random.default_rng(seed); T = Tree(); n = 26 if lod == 0 else 12
    for k in range(n):
        az = k * 2.39996; el = 0.35 + 1.0 * (1 - k / n) ** 1.2; L = 1.25 * (0.55 + 0.45 * k / n) * r.uniform(0.9, 1.1); o = np.array([math.cos(az), math.sin(az), 0])
        P = [np.array([0, 0, 0.12]) + o * 0.05]; dd = unit(o * math.cos(el) + UP * math.sin(el))
        for i in range(5): dd = unit(dd - UP * 0.05 * i); P.append(P[-1] + dd * L / 5)
        P = np.array(P); R = np.linspace(0.11, 0.012, 6)
        tube(T.bark, P, R, 5 if lod == 0 else 3, np.array([0.13, 0.25, 0.2]) * r.uniform(0.85, 1.1))
        if lod == 0: tube(T.bark, [P[-1], P[-1] + dd * 0.08], [0.012, 0.002], 3, (0.18, 0.12, 0.08))
    return T.bark, None, 1.0


def prickly_pear(seed=13, lod=0):
    """Opuntia: chains of flat oval pads (squashed lathe discs) with yellow flowers on the top pads."""
    r = np.random.default_rng(seed); T = Tree()
    def pad(c, a_up, yaw, s):
        k = 10 if lod == 0 else 6; t = np.linspace(0, 2 * np.pi, k + 1)
        ring = np.c_[np.cos(t) * 0.36 * s, np.zeros(k + 1), np.sin(t) * 0.5 * s]
        c_, s_ = math.cos(yaw), math.sin(yaw); Rz = np.array([[c_, -s_, 0], [s_, c_, 0], [0, 0, 1]])
        for th in (-0.06, 0.06):
            pass
        P = np.array([c - Rz @ np.array([0, 0.07 * s, 0]), c + Rz @ np.array([0, 0.07 * s, 0])])
        V = np.vstack([c + (Rz @ ring.T).T + Rz @ np.array([0, sg * 0.06 * s, 0]) for sg in (-1, 1)] + [P])
        m = k + 1; F = []
        for i in range(k):
            F += [(i, i + 1, m + i + 1), (i, m + i + 1, m + i), (2 * m, i + 1, i), (2 * m + 1, m + i, m + i + 1)]
        ny = Rz @ np.array([0, 1.0, 0]); N = V - c; N /= np.maximum(np.linalg.norm(N, axis=1), 1e-6)[:, None]
        sgn = np.sign(((V - c) @ ny))[:, None]; sgn[sgn == 0] = 1; N = unit_rows(N * 0.35 + ny * sgn * 0.8)
        T.bark.add(V, np.array(F), np.tile(np.array([0.1, 0.2, 0.05]) * r.uniform(0.85, 1.1), (len(V), 1)), np.c_[V[:, 0], V[:, 2]], N)
        return c + np.array([0, 0, 0.55 * s])
    tops = []
    for b in range(3):
        c = np.array([r.normal(0, 0.25), r.normal(0, 0.25), 0.5]); yaw = r.uniform(0, 3)
        for lvl in range(3):
            top = pad(c, 0, yaw, r.uniform(0.75, 1.0)); yaw += r.uniform(-1.2, 1.2); c = top + np.array([r.normal(0, 0.2), r.normal(0, 0.2), 0.36])
        tops.append(top)
    if lod == 0:
        for t in tops: tube(T.bark, [t, t + UP * 0.12], [0.07, 0.1], 6, (1.0, 0.82, 0.2))
    return T.bark, None, 2.0


def log(seed=14, lod=0, L=4.5):
    r = np.random.default_rng(seed); T = Tree(); P = np.c_[np.linspace(-L / 2, L / 2, 6), 0.05 * np.sin(np.arange(6)), np.full(6, 0.3)]
    tube(T.bark, P, np.linspace(0.32, 0.24, 6), 10 if lod == 0 else 6, (0.8, 0.75, 0.6), urep=2, vlen=1.2)
    tube(T.bark, [P[2], P[2] + np.array([0.4, 0.9, 0.4])], [0.09, 0.03], 5, (0.8, 0.75, 0.6))
    return T.bark, None, 0.6


# name: (fn, kwargs, bark texture, leaf?)
SPECIES = {
    'plane': (plane, {}, 'plane'), 'oak': (oak, {}, 'rough'), 'birch': (birch, {}, 'birch'), 'olive': (olive, {}, 'olive'),
    'stone_pine': (stone_pine, {}, 'rough'), 'spruce': (spruce, {}, 'rough'), 'cypress': (cypress, {}, 'rough'), 'date_palm': (date_palm, {}, 'palm'),
    'oleander': (shrub, dict(seed=9, cell='oleander', size=2.4), 'olive'), 'laurel': (shrub, dict(seed=15, cell='laurel', size=1.8, n=55), 'olive'),
    'hedge': (hedge, {}, 'olive'), 'fern': (ground_clump, dict(seed=11, cell='fern', n=11, size=1.1), None),
    'grass_hq': (ground_clump, dict(seed=16, cell='grass', n=5, size=0.8, arch=0.05), None), 'flowers_hq': (ground_clump, dict(seed=17, cell='flowers', n=5, size=0.75, arch=0.05), None),
    'agave': (agave, {}, None), 'prickly_pear': (prickly_pear, {}, None), 'log': (log, {}, 'rough'),
}

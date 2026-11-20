"""Art sheet 05: Aurelia countryside, village and farms. Warm Adriatic farm country: limestone and lime-washed walls, terracotta roofs,
green and blue shutters, timber barns on stone bases, galvanised silos, dry-stone walls, vines and olive groves.
Every piece faces +X, origin on the ground at the middle of the footprint, built with the street kit (isle_props / isle_houses)."""
import math
import numpy as np
import bmesh
import isle_props as P
import isle_houses as HS
from isle_props import bbox, lathe, sweep, prism
from isle_houses import Frame, walls, window, door, gable_roof, chimney

# vertex colours are linear (they multiply the photo textures): saturated values here, not sRGB picks
LIME = (0.92, 0.9, 0.84); STONE = (1.0, 0.72, 0.4); TERRA = (0.75, 0.24, 0.1); SAGE = (0.12, 0.24, 0.15); BLUE = (0.06, 0.17, 0.38)
TIMBER = (0.2, 0.1, 0.05); IRON = (0.04, 0.04, 0.045); LEAF = (0.05, 0.12, 0.02); GERANIUM = (0.8, 0.03, 0.04)


def fronts(W, D):
    return [(Frame((D / 2, 0, 0), (0, 1, 0), (1, 0, 0)), W), (Frame((-D / 2, 0, 0), (0, -1, 0), (-1, 0, 0)), W),
            (Frame((0, W / 2, 0), (-1, 0, 0), (0, 1, 0)), D), (Frame((0, -W / 2, 0), (1, 0, 0), (0, -1, 0)), D)]


def arch(K, M, F, uc, z0, w, h, col=STONE, depth=0.06):
    """Stone arch: jamb blocks and a ring of voussoirs with a keystone round a round-headed opening (spring at z0 + h - w/2)."""
    r = w / 2; zs = z0 + h - r
    for sg in (-1, 1):
        for q in range(int((zs - z0) / 0.36)):
            zz = z0 + q * 0.36; lw = 0.42 if q % 2 else 0.3; u0 = uc + sg * r if sg > 0 else uc - r - lw
            K.obj(F.box(u0 if sg > 0 else u0, (u0 + lw) if sg > 0 else uc - r, -0.02, depth, zz, zz + 0.34), M['ashlar'], col, 'box', 1.0, 0.015, 2)
    n = 11
    for k in range(n):
        a0 = math.pi * k / n; a1 = math.pi * (k + 1) / n; ro = r + (0.5 if k == n // 2 else 0.36)
        pts = [(math.cos(a0) * r, math.sin(a0) * r), (math.cos(a0) * ro, math.sin(a0) * ro), (math.cos(a1) * ro, math.sin(a1) * ro), (math.cos(a1) * r, math.sin(a1) * r)]
        bm = bmesh.new(); vs = []
        for nn in (-0.02, depth):
            for (x, z) in pts: vs.append(bm.verts.new(tuple(F.w(uc + x, nn, zs + z))))
        for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)): bm.faces.new([vs[i] for i in f])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); K.obj(bm, M['ashlar'], tuple(np.asarray(col) * (0.94 + 0.08 * (k % 3) / 2)), 'box', 1.0, 0.01, 1, smooth=False)


def plank_door(K, M, F, uc, z0, w, h, col=TIMBER, round_top=False):
    """Boarded door set back in its opening, with iron strap hinges; round_top fills the arch head."""
    nb = max(3, int(w / 0.16)); r = w / 2; zs = z0 + h - r
    for i in range(nb):
        u0 = uc - w / 2 + i * w / nb; u1 = u0 + w / nb - 0.012; um = (u0 + u1) / 2 - uc
        top = zs + math.sqrt(max(0.0, r * r - um * um)) if round_top else z0 + h
        K.obj(F.box(u0, u1, -0.2, -0.15, z0, top), M['wood'], tuple(np.asarray(col) * (0.9 + 0.2 * ((i * 7) % 3) / 2)), 'box', 1.0, 0.004, 1)
    for zz in (z0 + 0.4, z0 + h * 0.62):
        K.obj(F.box(uc - w / 2 + 0.05, uc + w * 0.2, -0.15, -0.13, zz, zz + 0.07), M['iron'], IRON)


def pot(K, M, x, y, z, s=1.0, flower=GERANIUM):
    K.obj(lathe([(0.0, 0.0), (0.13 * s, 0.0), (0.18 * s, 0.26 * s), (0.2 * s, 0.3 * s), (0.0, 0.3 * s)], 12, x, y, z), M['paint'], (0.72, 0.36, 0.22), 'cyl', 1.0)
    rng = np.random.default_rng(int(abs(x * 100 + y * 37)) % 997)
    for k in range(9):
        a = rng.uniform(0, 6.28); rr = rng.uniform(0, 0.15) * s
        K.obj(lathe([(0.0, -0.05), (0.06, 0.0), (0.0, 0.06)], 6, x + rr * math.cos(a), y + rr * math.sin(a), z + 0.34 * s + rng.uniform(0, 0.1) * s), M['concrete'], tuple(np.asarray(LEAF) * 1.4))
        if k % 2 == 0: K.obj(lathe([(0.0, 0.0), (0.035, 0.02), (0.0, 0.05)], 6, x + rr * math.cos(a), y + rr * math.sin(a), z + 0.42 * s + rng.uniform(0, 0.08) * s), M['smooth'], flower)


def vine_canopy(K, M, x0, x1, y0, y1, z, dens=1.0, seed=3):
    """Grape vine over a pergola: leafy clumps on top of the beams, a few hanging bunches."""
    rng = np.random.default_rng(seed); n = int((x1 - x0) * (y1 - y0) * 9 * dens)
    for k in range(n):
        x = rng.uniform(x0, x1); y = rng.uniform(y0, y1); s = rng.uniform(0.12, 0.22); g = rng.uniform(0.75, 1.2)
        K.obj(lathe([(0.0, -s * 0.5), (s, -s * 0.2), (s * 0.9, s * 0.3), (0.0, s * 0.6)], 6, x, y, z + rng.uniform(0, 0.15)), M['concrete'], tuple(np.asarray(LEAF) * g * 1.4))
    for k in range(int(n / 12)):
        x = rng.uniform(x0, x1); y = rng.uniform(y0, y1)
        K.obj(lathe([(0.0, 0.0), (0.06, 0.06), (0.05, 0.16), (0.0, 0.22)], 6, x, y, z - 0.25), M['plastic'], (0.28, 0.12, 0.3))


def pergola(K, M, x0, x1, y0, y1, z, col=TIMBER, vine=True):
    for (x, y) in ((x0, y0), (x0, y1), (x1, y0), (x1, y1)):
        K.obj(bbox(x, y, z / 2, 0.16, 0.16, z), M['wood'], col, 'box', 1.0, 0.012, 2)
    for y in (y0, y1): K.obj(bbox((x0 + x1) / 2, y, z + 0.08, x1 - x0 + 0.5, 0.12, 0.18), M['wood'], col, 'box', 1.0, 0.01, 1)
    for yy in np.arange(y0 + 0.1, y1 + 0.01, 0.55): K.obj(bbox((x0 + x1) / 2, yy, z + 0.24, x1 - x0 + 0.7, 0.08, 0.12), M['wood'], col, 'box', 1.0, 0.008, 1)
    if vine: vine_canopy(K, M, x0 - 0.3, x1 + 0.3, y0, y1, z + 0.32)


# ------------------------------------------------------------------ 1 stone farmhouse
def farmhouse(K, M):
    """Two-storey limestone farmhouse: arched cart door, outside stone stair to a first-floor door, vine pergola, terracotta roof."""
    W, D, z0, fh = 13.0, 8.0, 0.35, 3.1; zt = z0 + 2 * fh
    HS.plinth(K, M, W, D, 0.35)
    for k, (F, Ln) in enumerate(fronts(W, D)):
        holes = []; items = []
        if k == 0:
            items = [('arch', -3.6, z0, 2.4, 3.0), ('door', 2.2, z0, 1.1, 2.2), ('win', -0.4, z0 + 0.95, 1.0, 1.35), ('win', 4.6, z0 + 0.95, 1.0, 1.35),
                     ('win', -3.6, z0 + fh + 0.85, 1.0, 1.45), ('win', -0.4, z0 + fh + 0.85, 1.0, 1.45), ('win', 4.6, z0 + fh + 0.85, 1.0, 1.45)]
        elif k == 1: items = [('win', u, z0 + zz, 0.9, 1.3) for u in (-4, 0, 4) for zz in (1.0, fh + 0.85)]
        elif k == 2: items = [('win', 0, z0 + fh + 0.85, 0.9, 1.3)]
        else: items = [('door', -1.2, z0 + fh, 1.0, 2.15), ('win', 2.0, z0 + 1.0, 0.8, 1.1)]
        for it in items: holes.append((it[1] - it[3] / 2, it[1] + it[3] / 2, it[2], it[2] + it[4]))
        walls(K, M, F, Ln + (0.0 if k < 2 else -0.56), z0, zt, holes, STONE, mat=M['ashlar'], uvs=2.2)
        for it in items:
            if it[0] == 'arch': arch(K, M, F, it[1], it[2], it[3], it[4]); plank_door(K, M, F, it[1], it[2], it[3], it[4], round_top=True)
            elif it[0] == 'door': door(K, M, F, it[1], it[2], it[3], it[4], col=(0.3, 0.4, 0.33), canopy=False)
            else: window(K, M, F, it[1], it[2], it[3], it[4], SAGE, trim=(0.9, 0.86, 0.78))
    K.obj(bbox(0, 0, zt - 0.1, D - 0.3, W - 0.3, 0.2), M['ashlar'], STONE)
    for (sx, sy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):                                 # big corner quoins
        for q in range(int((zt - z0) / 0.55)):
            zz = z0 + q * 0.55; lw = 0.55 if q % 2 else 0.35
            K.obj(bbox(sx * (D / 2 + 0.02) - sx * lw / 2, sy * (W / 2 + 0.02) - sy * 0.17, zz + 0.26, lw, 0.34, 0.5), M['ashlar'], (0.98, 0.92, 0.8), 'box', 1.0, 0.02, 2)
    gable_roof(K, M, W, D, zt, 2.2, TERRA, STONE, ov=0.5, gmat=M['ashlar'])
    chimney(K, M, -D * 0.2, -W * 0.3, zt + 0.9, zt + 3.2)
    # outside stair along the -y gable end, up to the first-floor door
    F = Frame((0, -W / 2, 0), (1, 0, 0), (0, -1, 0)); nst = 17; run = 0.32
    for i in range(nst):
        u = 3.4 - i * run; zz = z0 + (i + 1) * fh / nst
        K.obj(F.box(u - run, u, 0.0, 1.15, z0 - 0.3, zz), M['ashlar'], tuple(np.asarray(STONE) * 0.96), 'box', 1.0, 0.012, 1)
    K.obj(F.box(-2.4, -0.25, 0.0, 1.3, z0 - 0.3, z0 + fh), M['ashlar'], STONE, 'box', 1.0, 0.012, 1)                         # landing
    pts = [tuple(F.w(3.4, 1.2, z0 + 0.95)), tuple(F.w(-0.25, 1.2, z0 + fh + 0.95)), tuple(F.w(-2.4, 1.2, z0 + fh + 0.95))]
    K.obj(sweep(pts, 0.03, 6), M['iron'], IRON)
    for u in np.linspace(-2.3, 3.3, 15):
        zz = z0 + fh if u < -0.25 else z0 + (3.4 - u) / run * fh / nst
        K.obj(sweep([tuple(F.w(u, 1.2, zz)), tuple(F.w(u, 1.2, zz + 0.95))], 0.012, 5), M['iron'], IRON)
    pergola(K, M, D / 2 + 0.3, D / 2 + 3.0, -2.0, 6.2, 2.6)
    K.obj(bbox(D / 2 + 1.6, 2.2, 0.75, 0.9, 2.2, 0.06), M['wood'], (0.6, 0.45, 0.3), 'box', 1.0, 0.01, 1)               # table under the vine
    for yy in (1.4, 3.0): K.obj(bbox(D / 2 + 1.6, yy, 0.37, 0.12, 0.12, 0.74), M['wood'], (0.6, 0.45, 0.3))
    for x, y in ((D / 2 + 0.25, 1.2), (D / 2 + 0.25, 3.3), (D / 2 + 0.3, -2.6), (D / 2 + 0.3, -4.6)): pot(K, M, x, y, 0.0, 1.4)


# ------------------------------------------------------------------ 2 village row
def village_row(K, M):
    """Three narrow terraced houses stepping in height: ochre, rose and pale blue lime-wash, balconies, flower boxes."""
    houses = [(-6.0, 5.2, 3, (0.88, 0.58, 0.22), SAGE, 2.0), (-0.6, 5.6, 2, (0.9, 0.52, 0.45), BLUE, 1.9), (4.9, 5.4, 3, (0.55, 0.7, 0.8), (0.3, 0.12, 0.05), 2.1)]
    D = 9.0
    for yc, Wd, fl, col, sh, rise in houses:
        z0 = 0.3; fh = 3.0; zt = z0 + fl * fh
        for k, (F0, Ln) in enumerate(fronts(Wd, D)):
            F = Frame(F0.o + np.array([0, yc, 0]), F0.u, F0.n); holes = []; items = []
            if k in (0, 1):
                for f in range(fl):
                    zb = z0 + f * fh
                    for uu in (-Wd / 4, Wd / 4):
                        if k == 0 and f == 0 and uu < 0: items.append(('door', uu, zb, 1.1, 2.3)); holes.append((uu - 0.55, uu + 0.55, zb, zb + 2.3)); continue
                        h = 2.2 if (k == 0 and f == 1) else 1.4; zz = zb + (0.2 if h > 2 else 0.95)
                        items.append(('win', uu, zz, 0.95, h)); holes.append((uu - 0.475, uu + 0.475, zz, zz + h))
            walls(K, M, F, Ln + (0.0 if k < 2 else -0.56), z0, zt, holes, col, mat=M['plaster2'])
            for it in items:
                if it[0] == 'door': door(K, M, F, it[1], it[2], it[3], it[4], col=np.asarray(sh) * 0.8, canopy=False)
                else: window(K, M, F, it[1], it[2], it[3], it[4], sh)
            if k == 0:
                K.obj(F.box(-Ln / 2, Ln / 2, -0.02, 0.04, z0 + fh - 0.14, z0 + fh), M['stone'], (0.96, 0.94, 0.88), 'box', 1.2, 0.006, 1)
                zb = z0 + fh                                                                     # balcony on the first floor
                K.obj(F.box(-Wd / 2 + 0.3, Wd / 2 - 0.3, 0.0, 0.85, zb - 0.1, zb + 0.02), M['stone'], (0.95, 0.93, 0.88), 'box', 1.0, 0.012, 2)
                for uu in np.linspace(-Wd / 2 + 0.35, Wd / 2 - 0.35, 18): K.obj(sweep([tuple(F.w(uu, 0.82, zb)), tuple(F.w(uu, 0.82, zb + 1.0))], 0.012, 5), M['iron'], IRON)
                K.obj(sweep([tuple(F.w(-Wd / 2 + 0.3, 0.02, zb + 1.0)), tuple(F.w(-Wd / 2 + 0.3, 0.84, zb + 1.0)), tuple(F.w(Wd / 2 - 0.3, 0.84, zb + 1.0)), tuple(F.w(Wd / 2 - 0.3, 0.02, zb + 1.0))], 0.025, 6), M['iron'], IRON)
                for uu in (-Wd / 2 + 0.8, Wd / 2 - 0.8): p = F.w(uu, 0.55, zb + 0.02); pot(K, M, p[0], p[1], p[2], 1.1)
                if fl > 2:
                    for uu in (-Wd / 4, Wd / 4):                                                    # flower boxes on the second floor
                        p0 = F.w(uu, 0.12, z0 + 2 * fh + 0.88); K.obj(F.box(uu - 0.5, uu + 0.5, 0.0, 0.24, z0 + 2 * fh + 0.7, z0 + 2 * fh + 0.9), M['pwood'], np.asarray(sh) * 0.9, 'box', 1.0, 0.008, 1)
                        for j in range(6): p = F.w(uu - 0.42 + j * 0.17, 0.12, z0 + 2 * fh + 0.95); K.obj(lathe([(0.0, -0.04), (0.08, 0.02), (0.0, 0.1)], 6, *p), M['plastic'], LEAF); K.obj(lathe([(0.0, 0.0), (0.035, 0.02), (0.0, 0.05)], 6, p[0], p[1], p[2] + 0.07), M['smooth'], GERANIUM)
        K.obj(bbox(0, yc, zt - 0.1, D - 0.3, Wd - 0.3, 0.2), M['plaster2'], col)
        Kp = P.Part(); gable_roof(Kp, M, Wd, D, zt, rise, TERRA, col, ov=0.35, gmat=M['plaster2'])
        for it in Kp.objs:
            if it[0] == 'raw':
                _, Pq, *rest = it; K.objs.append(('raw', Pq + np.array([0, yc, 0]), *rest)); continue
            o = it[0]; o.data.transform(__import__('mathutils').Matrix.Translation((0, yc, 0))); K.objs.append(it)
        chimney(K, M, -D * 0.2, yc + Wd * 0.25, zt + rise * 0.5, zt + rise + 0.7)


# ------------------------------------------------------------------ 3 cottage
def cottage(K, M, wall=LIME, shut=BLUE):
    """Lime-washed single-storey cottage, blue shutters, front pergola with a bench and pots, low terracotta roof."""
    W, D, z0, fh = 10.0, 6.5, 0.3, 3.0; zt = z0 + fh; LIME_, BLUE_ = wall, shut
    HS.plinth(K, M, W, D, 0.3)
    for k, (F, Ln) in enumerate(fronts(W, D)):
        items = [('door', 0.0, z0, 1.0, 2.2), ('win', -3.0, z0 + 0.9, 1.0, 1.3), ('win', 3.0, z0 + 0.9, 1.0, 1.3)] if k == 0 else ([('win', u, z0 + 0.9, 0.9, 1.2) for u in (-2.6, 2.6)] if k == 1 else [('win', 0, z0 + 0.95, 0.7, 0.9)])
        holes = [(it[1] - it[3] / 2, it[1] + it[3] / 2, it[2], it[2] + it[4]) for it in items]
        walls(K, M, F, Ln + (0.0 if k < 2 else -0.56), z0, zt, holes, LIME_, mat=M['plaster'])
        for it in items:
            if it[0] == 'door': door(K, M, F, it[1], it[2], it[3], it[4], col=BLUE_, canopy=False)
            else: window(K, M, F, it[1], it[2], it[3], it[4], BLUE_, trim=(0.97, 0.97, 0.95))
        K.obj(F.box(-Ln / 2, Ln / 2, -0.01, 0.04, z0, z0 + 0.5), M['plaster'], (0.55, 0.62, 0.7))                    # painted skirting
    K.obj(bbox(0, 0, zt - 0.1, D - 0.3, W - 0.3, 0.2), M['plaster'], LIME_)
    gable_roof(K, M, W, D, zt, 1.9, TERRA, LIME_, ov=0.4)
    chimney(K, M, -D * 0.15, W * 0.33, zt + 0.8, zt + 2.6)
    pergola(K, M, D / 2 + 0.3, D / 2 + 2.6, -4.2, 4.2, 2.5, col=(0.62, 0.55, 0.46))
    K.obj(bbox(D / 2 + 0.6, -2.4, 0.45, 0.45, 1.8, 0.06), M['wood'], (0.6, 0.45, 0.3), 'box', 1.0, 0.01, 1)
    K.obj(bbox(D / 2 + 0.4, -2.4, 0.75, 0.06, 1.8, 0.5), M['wood'], (0.6, 0.45, 0.3), 'box', 1.0, 0.01, 1)
    for yy in (-3.2, -1.6): K.obj(bbox(D / 2 + 0.6, yy, 0.22, 0.4, 0.08, 0.44), M['wood'], (0.6, 0.45, 0.3))
    for y in (1.2, 1.7, 2.3, 3.9): pot(K, M, D / 2 + 0.35, y, 0.0, 1.0 + 0.3 * (y % 1))


# ------------------------------------------------------------------ 4 timber barn
def barn(K, M):
    """Timber-clad barn on a fieldstone base: big sliding doors, hayloft door with a hoist beam, ridge cupola, lean-to."""
    W, D, h = 16.0, 10.0, 5.6; col = (0.4, 0.07, 0.04)
    K.obj(bbox(0, 0, 0.6, D + 0.1, W + 0.1, 1.2), M['brick4'], (0.95, 0.92, 0.88), 'box', 1.6, 0.02, 2)
    for k, (F, Ln) in enumerate(fronts(W, D)):
        nb = int(Ln / 0.22)
        for i in range(nb):
            u0 = -Ln / 2 + i * Ln / nb
            if k == 0 and abs(u0 + Ln / nb / 2) < 2.0: continue
            K.obj(F.box(u0, u0 + Ln / nb - 0.015, -0.02, 0.02, 1.2, h), M['wood'], tuple(np.asarray(col) * (0.9 + 0.2 * ((i * 5) % 4) / 3)), 'box', 1.0, 0.0)
        if k == 0:
            for sg in (-1, 1):                                                                     # sliding doors with X bracing
                u0, u1 = (-4.0, -0.05) if sg < 0 else (0.05, 4.0)
                K.obj(F.box(u0, u1, 0.02, 0.1, 0.0, 4.4), M['wood'], tuple(np.asarray(col) * 0.92), 'box', 1.0, 0.006, 1)
                for (a, b) in (((u0, 0.2), (u1, 4.2)), ((u0, 4.2), (u1, 0.2))):
                    K.obj(HS._board_any(F.w(a[0], 0.1, a[1]), F.w(b[0], 0.1, b[1]), F.n, 0.05, 0.16), M['pwood'], (0.95, 0.94, 0.9))
                for (a, b, z) in ((u0, u1, 0.1), (u0, u1, 4.25), (u0, u0 + 0.16, 0), (u1 - 0.16, u1, 0)):
                    K.obj(F.box(a, b, 0.1, 0.15, z if z else 0.0, (z + 0.16) if z else 4.4), M['pwood'], (0.95, 0.94, 0.9))
            K.obj(F.box(-4.2, 4.2, 0.0, 0.25, 4.55, 4.7), M['iron'], IRON)                             # door track
            K.obj(F.box(-1.0, 1.0, 0.02, 0.1, 5.9, 7.6), M['wood'], tuple(np.asarray(col) * 0.85), 'box', 1.0, 0.006, 1)       # hayloft door in the gable
            K.obj(F.box(-0.12, 0.12, 0.0, 1.6, 8.3, 8.55), M['wood'], (0.4, 0.3, 0.2), 'box', 1.0, 0.01, 1)                    # hoist beam
            K.obj(sweep([tuple(F.w(0, 1.45, 8.3)), tuple(F.w(0, 1.45, 6.6))], 0.012, 4), M['iron'], (0.6, 0.55, 0.45))
        if k == 1:
            for u in (-4.5, 0, 4.5): K.obj(F.box(u - 0.5, u + 0.5, 0.02, 0.06, 2.6, 3.4), M['pwood'], (0.95, 0.94, 0.9))
    rise = 4.2; K.obj(bbox(0, 0, h - 0.1, D - 0.2, W - 0.2, 0.2), M['wood'], col)
    Kp = P.Part(); gable_roof(Kp, M, W, D, h, rise, (0.55, 0.57, 0.58), col, ov=0.5, roofmat=M['corr'], gmat=M['wood'], ruvs=1.0, trim=(0.95, 0.94, 0.9), ridge_along='x')
    K.objs.extend(Kp.objs)
    zr = h + rise                                                                                  # cupola vent on the ridge
    K.obj(bbox(0, 0, zr + 0.5, 1.4, 1.4, 1.2), M['wood'], (0.95, 0.94, 0.9), 'box', 1.0, 0.01, 1)
    for u in np.linspace(-0.5, 0.5, 6): K.obj(bbox(0.71, u, zr + 0.55, 0.04, 0.12, 0.8), M['wood'], (0.3, 0.25, 0.2))
    K.obj(lathe([(1.15, 0.0), (0.0, 0.8)], 4, 0, 0, zr + 1.1, a0=math.pi / 4, a1=math.pi / 4 + 2 * math.pi), M['corr'], (0.5, 0.52, 0.53), smooth=False)
    K.obj(sweep([(0, 0, zr + 1.9), (0, 0, zr + 2.6)], 0.02, 5), M['iron'], IRON); K.obj(prism([(0, 0), (0.5, 0.1), (0.5, 0.25), (0, 0.18)], -0.01, 0.01, axis='y', at=0), M['iron'], IRON) if False else None
    K.obj(bbox(0.25, 0, zr + 2.45, 0.6, 0.02, 0.22), M['iron'], IRON)                                 # weather vane
    lean = prism([(-D / 2, 4.2), (-D / 2 - 4.0, 2.7), (-D / 2 - 4.0, 2.55), (-D / 2, 4.05)], -W / 2 + 1, W / 2 - 4, axis='x')    # open lean-to at the back
    for v in lean.verts: a, b, c = v.co; v.co = (b, a, c)
    K.obj(lean, M['corr'], (0.42, 0.07, 0.03), 'box', 1.0, 0.0, smooth=False)
    for yy in np.linspace(-W / 2 + 1.2, W / 2 - 4.2, 4): K.obj(bbox(-D / 2 - 3.8, yy, 1.3, 0.18, 0.18, 2.6), M['wood'], (0.4, 0.3, 0.2))


# ------------------------------------------------------------------ 5 hay shed with bales
def bale_square(K, M, x, y, z, yaw=0.0, col=(0.75, 0.55, 0.2)):
    K.obj(bbox(x, y, z + 0.2, 1.0, 0.48, 0.4, yaw), M['fabric'], col, 'box', 3.0, 0.0)
    for o in (-0.25, 0.25):
        c, s = math.cos(yaw), math.sin(yaw); K.obj(bbox(x + c * o, y + s * o, z + 0.2, 0.02, 0.5, 0.42, yaw), M['plastic'], (0.2, 0.35, 0.6))


def bale_round(K, M, x, y, yaw=0.0, wrapped=False):
    bm = lathe([(0.0, -0.6), (0.7, -0.6), (0.78, -0.5), (0.8, 0.0), (0.78, 0.5), (0.7, 0.6), (0.0, 0.6)], 20)
    c, s = math.cos(yaw), math.sin(yaw)
    for v in bm.verts: a, b, h = v.co; v.co = (x + c * h - s * a, y + s * h + c * a, 0.78 + b)
    K.obj(bm, M['smooth'] if wrapped else M['fabric'], (0.82, 0.83, 0.8) if wrapped else (0.7, 0.5, 0.18), 'cyl', 1.0 if wrapped else 3.0)


def hay_shed(K, M):
    """Open-sided pole shed with a corrugated roof, stacked square bales inside, round bales outside."""
    W, D, h = 12.0, 7.0, 5.0
    for x in (-D / 2, D / 2):
        for y in np.linspace(-W / 2, W / 2, 4): K.obj(bbox(x, y, h / 2, 0.22, 0.22, h), M['wood'], (0.42, 0.32, 0.22), 'box', 1.0, 0.01, 1)
    for x in (-D / 2, D / 2): K.obj(bbox(x, 0, h + 0.1, 0.22, W + 0.4, 0.25), M['wood'], (0.42, 0.32, 0.22), 'box', 1.0, 0.01, 1)
    for y in np.linspace(-W / 2, W / 2, 4): K.obj(sweep([(-D / 2, y, h + 0.2), (0, y, h + 1.3), (D / 2, y, h + 0.2)], 0.09, 6), M['wood'], (0.42, 0.32, 0.22))
    for sg in (-1, 1):
        sl = prism([(0, h + 1.42), (sg * (D / 2 + 0.6), h + 0.22), (sg * (D / 2 + 0.6), h + 0.16), (0, h + 1.36)], -W / 2 - 0.4, W / 2 + 0.4, axis='x')
        for v in sl.verts: a, b, c = v.co; v.co = (b, a, c)
        K.obj(sl, M['corr'], (0.42, 0.07, 0.03), 'box', 1.0, 0.0, smooth=False)
    for lvl in range(5):                                                                        # stack, stepping back toward the top
        for i in range(20 - 2 * lvl):
            for j in range(5 if lvl < 3 else 4):
                bale_square(K, M, -2.6 + j * 1.05 + lvl * 0.2, -W / 2 + 0.9 + i * 0.5 + lvl * 0.5, lvl * 0.42)
    for k, (x, y) in enumerate(((D / 2 + 2.0, -4.0), (D / 2 + 2.2, -2.2), (D / 2 + 3.6, -3.1), (D / 2 + 2.4, 3.2))): bale_round(K, M, x, y, 0.3 * k, wrapped=k >= 3)


# ------------------------------------------------------------------ 6 grain silos
def silos(K, M):
    """Two galvanised grain silos with conical roofs, a caged ladder, a catwalk and an auger into a feed shed."""
    for (x, y, r, hh) in ((0.0, -3.0, 2.4, 9.0), (0.0, 2.6, 2.0, 7.5)):
        K.obj(lathe([(r + 0.25, 0.0), (r + 0.25, 0.4), (0.0, 0.4)], 24, x, y, 0), M['concrete'], (0.8, 0.78, 0.74), 'cyl', 1.0)
        K.obj(lathe([(r, 0.4), (r, hh)], 32, x, y, 0, close_top=False, close_bottom=False), M['corr'], (0.82, 0.84, 0.85), 'cyl', 0.6, smooth=True)
        for z in np.arange(1.2, hh, 1.1): K.obj(lathe([(r + 0.02, z), (r + 0.05, z + 0.02), (r + 0.02, z + 0.05)], 32, x, y, 0), M['galv'], (0.7, 0.72, 0.74))
        K.obj(lathe([(r + 0.15, hh), (r + 0.1, hh + 0.1), (0.45, hh + r * 0.62), (0.45, hh + r * 0.62 + 0.4), (0.0, hh + r * 0.62 + 0.5)], 32, x, y, 0), M['galv'], (0.78, 0.8, 0.82), 'cyl', 1.0)
        for sg in (-1, 1): K.obj(sweep([(x + r + 0.3, y + sg * 0.25, 0.4), (x + r + 0.3, y + sg * 0.25, hh + 0.6)], 0.025, 5), M['galv'], (0.7, 0.72, 0.74))
        for z in np.arange(0.7, hh + 0.5, 0.3): K.obj(sweep([(x + r + 0.3, y - 0.25, z), (x + r + 0.3, y + 0.25, z)], 0.015, 4), M['galv'], (0.7, 0.72, 0.74))
        for z in np.arange(2.4, hh, 0.9): K.obj(lathe([(0.45, -0.02), (0.47, 0.0), (0.45, 0.02)], 10, x + r + 0.3, y, z, a0=-math.pi / 2, a1=math.pi / 2), M['galv'], (0.7, 0.72, 0.74))     # ladder cage hoops
    K.obj(sweep([(0.0, -3.0, 9.6), (0.0, 2.6, 8.1)], 0.04, 5), M['galv'], (0.7, 0.72, 0.74))
    K.obj(bbox(0, -0.2, 8.85, 0.6, 1.6, 0.06), M['galv'], (0.6, 0.62, 0.64))
    K.obj(sweep([(1.6, -3.0, 0.8), (5.4, -3.0, 5.6), (6.2, -3.0, 5.2)], 0.15, 10), M['galv'], (0.7, 0.72, 0.74))             # auger
    Kp = P.Part(); W_, D_, h_ = 6.0, 5.0, 4.0
    for k, (F, Ln) in enumerate(fronts(W_, D_)):
        holes = [(-1.4, 1.4, 0.0, 3.2)] if k == 0 else []
        walls(Kp, M, F, Ln + (0.0 if k < 2 else -0.3), 0.0, h_, holes, (0.85, 0.86, 0.84), t=0.15, mat=M['corr'], uvs=1.0)
        if k == 0:
            for sg in (-1, 1): Kp.obj(F.box(sg * 1.4 - 0.08, sg * 1.4 + 0.08, 0.0, 0.1, 0.0, 3.3), M['paint'], (0.6, 0.62, 0.62))
            Kp.obj(F.box(-1.48, 1.48, 0.0, 0.1, 3.2, 3.36), M['paint'], (0.6, 0.62, 0.62))
            Kp.obj(F.box(-1.4, 1.4, -0.6, -0.55, 0.0, 3.2), M['smooth'], (0.05, 0.045, 0.04))
    Kp.obj(bbox(0, 0, h_ - 0.05, D_ - 0.2, W_ - 0.2, 0.1), M['corr'], (0.85, 0.86, 0.84))
    gable_roof(Kp, M, W_, D_, h_, 1.4, (0.55, 0.12, 0.05), (0.85, 0.86, 0.84), ov=0.35, roofmat=M['corr'], gmat=M['corr'], ruvs=1.0)
    for it in Kp.objs:
        if it[0] == 'raw':
            _, Pq, *rest = it; K.objs.append(('raw', Pq + np.array([6.5, -3.0, 0]), *rest)); continue
        it[0].data.transform(__import__('mathutils').Matrix.Translation((6.5, -3.0, 0))); K.objs.append(it)


# ------------------------------------------------------------------ 7 winery cellar
def winery(K, M):
    """Stone wine cellar half dug into the slope: three arched bays, oak barrels, a basket press, a carved name board."""
    W, D, h = 14.0, 8.0, 4.4; z0 = 0.3
    HS.plinth(K, M, W, D, 0.3)
    for k, (F, Ln) in enumerate(fronts(W, D)):
        items = [('arch', u, z0, 2.2, 3.4) for u in (-4.2, 0.0, 4.2)] if k == 0 else ([('win', u, z0 + 1.6, 0.6, 0.9) for u in (-3, 3)] if k == 1 else [])
        holes = [(it[1] - it[3] / 2, it[1] + it[3] / 2, it[2], it[2] + it[4]) for it in items]
        walls(K, M, F, Ln + (0.0 if k < 2 else -0.56), z0, h, holes, (0.92, 0.84, 0.7), mat=M['ashlar'], uvs=2.0)
        for it in items:
            if it[0] == 'arch':
                arch(K, M, F, it[1], it[2], it[3], it[4], (0.95, 0.88, 0.74))
                if it[1] != 0.0: plank_door(K, M, F, it[1], it[2], it[3], it[4], (0.35, 0.22, 0.14), round_top=True)
                else:
                    K.obj(F.box(it[1] - 1.1, it[1] + 1.1, -0.29, -0.27, it[2], it[2] + it[4]), M['smooth'], (0.06, 0.05, 0.04))
                    for r_ in range(2):                                                         # barrels racked inside the open bay
                        for c_ in range(3): p = F.w(it[1] - 0.7 + c_ * 0.7, -0.6, it[2] + 0.38 + r_ * 0.66); K.obj(_barrel(p, F.n), M['wood'], (0.45, 0.28, 0.16), 'cyl', 1.0)
            else: window(K, M, F, it[1], it[2], it[3], it[4], None, trim=(0.4, 0.3, 0.2))
    K.obj(bbox(0, 0, h - 0.1, D - 0.3, W - 0.3, 0.2), M['ashlar'], (0.92, 0.84, 0.7))
    gable_roof(K, M, W, D, h, 1.8, TERRA, (0.92, 0.84, 0.7), ov=0.45, gmat=M['ashlar'])
    F = fronts(W, D)[0][0]
    K.obj(F.box(-2.4, 2.4, 0.0, 0.08, h - 0.55, h - 0.05), M['wood'], (0.35, 0.22, 0.14), 'box', 1.0, 0.01, 1)          # name board (carved letters = sign atlas cell)
    K.obj(F.box(-2.2, 2.2, 0.08, 0.1, h - 0.48, h - 0.12), M['sign'], (1, 1, 1), 'sign', 1.0, sign=P.sign_cell_uv_frame(F, 8, 0.0, h - 0.3, 4.4, 0.36))
    for i, (x, y) in enumerate(((D / 2 + 1.0, -6.4), (D / 2 + 1.0, -5.5), (D / 2 + 1.9, -6.0), (D / 2 + 1.1, 6.2))):
        K.obj(_barrel((x, y, 0.45), np.array([0, 0, 1.0]), stand=True), M['wood'], (0.48, 0.3, 0.17), 'cyl', 1.0)
    px, py = D / 2 + 2.2, 4.4                                                                    # basket press
    K.obj(lathe([(0.0, 0.0), (0.75, 0.0), (0.75, 0.25), (0.0, 0.25)], 16, px, py, 0), M['wood'], (0.4, 0.26, 0.16), 'cyl', 1.0)
    for k in range(16): a = k * math.pi / 8; K.obj(bbox(px + 0.55 * math.cos(a), py + 0.55 * math.sin(a), 0.75, 0.06, 0.06, 1.0), M['wood'], (0.5, 0.33, 0.2))
    for z in (0.4, 1.1): K.obj(lathe([(0.56, z), (0.6, z + 0.02), (0.56, z + 0.05)], 16, px, py, 0), M['iron'], IRON)
    K.obj(lathe([(0.06, 0.25), (0.06, 2.0)], 8, px, py, 0), M['iron'], IRON); K.obj(bbox(px, py, 1.75, 0.08, 1.4, 0.08), M['iron'], IRON)


def _barrel(c, axis, stand=False, L=0.8, r=0.33):
    axis = np.asarray(axis, float); axis = axis / np.linalg.norm(axis)
    bm = lathe([(0.0, -L / 2), (r * 0.85, -L / 2), (r, -L * 0.2), (r * 1.03, 0.0), (r, L * 0.2), (r * 0.85, L / 2), (0.0, L / 2)], 16)
    z = np.array([0, 0, 1.0]); v_ = np.cross(z, axis); s = np.linalg.norm(v_); cth = float(np.dot(z, axis))
    if s < 1e-6: R = np.eye(3) * (1 if cth > 0 else -1)
    else:
        vx = np.array([[0, -v_[2], v_[1]], [v_[2], 0, -v_[0]], [-v_[1], v_[0], 0]]); R = np.eye(3) + vx + vx @ vx * ((1 - cth) / s ** 2)
    for v in bm.verts: v.co = tuple(np.asarray(c) + R @ np.asarray(v.co[:]))
    return bm


# ------------------------------------------------------------------ 8 tractor and trailer
def tractor(K, M):
    """Vintage farm tractor (big ribbed rear wheels, narrow front axle, rounded bonnet, exhaust stack, pan seat) with a tipping trailer."""
    RED = (0.55, 0.03, 0.015); CRM = (0.85, 0.76, 0.52)
    def wheel(x, y, r, w, lugs):
        t = lathe([(r * 0.62, -w / 2), (r * 0.95, -w / 2), (r, -w * 0.3), (r, w * 0.3), (r * 0.95, w / 2), (r * 0.62, w / 2)], 28, close_top=False, close_bottom=False)
        for v in t.verts: a, b, h = v.co; v.co = (x + a, y + h, r + b)
        K.obj(t, M['concrete'], (0.035, 0.035, 0.035), 'cyl', 1.0)
        for k in range(lugs):                                                                    # chevron tread lugs
            a = k * 2 * math.pi / lugs
            for sg in (-1, 1):
                p0 = (x + (r + 0.03) * math.cos(a), y + sg * w * 0.05, r + (r + 0.03) * math.sin(a)); p1 = (x + (r + 0.03) * math.cos(a + 0.12), y + sg * w * 0.48, r + (r + 0.03) * math.sin(a + 0.12))
                K.obj(sweep([p0, p1], 0.035, 4), M['concrete'], (0.04, 0.04, 0.04))
        hub = lathe([(0.0, -w * 0.32), (r * 0.62, -w * 0.32), (r * 0.62, -w * 0.22), (r * 0.25, -w * 0.15), (r * 0.18, w * 0.05), (0.0, w * 0.1)], 20)
        sgn = 1 if y > 0 else -1
        for v in hub.verts: a, b, h = v.co; v.co = (x + a, y + sgn * h, r + b)
        K.obj(hub, M['paint'], CRM, 'cyl', 1.0)
    wheel(-0.9, 0.85, 0.75, 0.42, 22); wheel(-0.9, -0.85, 0.75, 0.42, 22); wheel(1.45, 0.62, 0.38, 0.16, 0); wheel(1.45, -0.62, 0.38, 0.16, 0)
    K.obj(bbox(0.35, 0, 0.75, 2.6, 0.55, 0.5), M['paint'], (0.25, 0.25, 0.26), 'box', 1.0, 0.04, 2)                  # chassis / engine block
    K.obj(bbox(1.45, 0, 0.38, 0.12, 1.25, 0.1), M['paint'], (0.25, 0.25, 0.26))
    bon = prism([(-0.2, 0.95), (1.85, 0.95), (1.95, 1.05), (1.95, 1.45), (1.7, 1.6), (-0.2, 1.6)], -0.36, 0.36, axis='y')
    K.obj(bon, M['paint'], RED, 'box', 1.0, 0.06, 3)
    for x in np.linspace(0.2, 1.4, 7): K.obj(bbox(x, 0.37, 1.2, 0.04, 0.02, 0.32), M['iron'], (0.2, 0.2, 0.2))
    K.obj(bbox(1.97, 0, 1.25, 0.04, 0.6, 0.45), M['iron'], (0.15, 0.15, 0.15)); K.obj(bbox(1.99, 0, 1.25, 0.02, 0.5, 0.36), M['galv'], (0.6, 0.6, 0.6))
    for sg in (-1, 1): K.obj(lathe([(0.0, 0.0), (0.08, 0.0), (0.09, 0.05), (0.0, 0.07)], 12, 1.98, sg * 0.25, 1.5), M['lens'], (1.0, 0.95, 0.8))
    K.obj(sweep([(1.2, 0.2, 1.6), (1.2, 0.2, 2.5), (1.22, 0.2, 2.55)], 0.05, 8), M['iron'], (0.12, 0.12, 0.12))
    K.obj(sweep([(1.6, -0.15, 1.6), (1.6, -0.15, 1.85)], 0.07, 8), M['galv'], (0.7, 0.7, 0.7))           # air cleaner
    for sg in (-1, 1):                                                                            # fenders over the rear wheels
        fe = lathe([(0.82, -0.25), (0.82, 0.25)], 16, a0=0.15, a1=math.pi - 0.15, close_top=False, close_bottom=False)
        bmesh.ops.solidify(fe, geom=fe.faces[:], thickness=0.03)
        for v in fe.verts: a, b, h = v.co; v.co = (-0.9 + a, sg * 0.85 + h, 0.75 + b)
        K.obj(fe, M['paint'], RED, 'box', 1.0)
    K.obj(sweep([(-0.6, 0, 0.9), (-0.9, 0, 1.3), (-1.05, 0, 1.4)], 0.04, 6), M['iron'], (0.2, 0.2, 0.2))
    K.obj(lathe([(0.0, 0.0), (0.24, 0.0), (0.26, 0.06), (0.22, 0.1), (0.0, 0.08)], 14, -1.1, 0, 1.4), M['paint'], (0.2, 0.2, 0.2))     # pan seat
    K.obj(sweep([(0.1, 0, 1.6), (-0.35, 0, 2.05)], 0.025, 6), M['iron'], (0.12, 0.12, 0.12))
    K.obj(lathe([(0.2, -0.02), (0.22, 0.0), (0.2, 0.02)], 18, -0.37, 0, 2.06), M['plastic'], (0.08, 0.08, 0.08))
    for y in (-0.25, 0.25): K.obj(sweep([(-1.4, y, 0.6), (-2.1, y * 0.4, 0.55)], 0.04, 6), M['paint'], (0.25, 0.25, 0.26))          # drawbar
    tx = -4.4                                                                                      # tipping trailer
    for y in (-1.0, 1.0):
        t = lathe([(0.2, -0.12), (0.4, -0.12), (0.42, 0.0), (0.4, 0.12), (0.2, 0.12)], 20, close_top=False, close_bottom=False)
        for v in t.verts: a, b, h = v.co; v.co = (tx + a, y + h, 0.42 + b)
        K.obj(t, M['concrete'], (0.035, 0.035, 0.035), 'cyl', 1.0)
        hb = lathe([(0.0, -0.13), (0.22, -0.13), (0.22, 0.13), (0.0, 0.13)], 14)
        for v in hb.verts: a, b, h = v.co; v.co = (tx + a, y + h, 0.42 + b)
        K.obj(hb, M['paint'], CRM, 'cyl', 1.0)
    K.obj(bbox(tx, 0, 0.75, 3.4, 2.0, 0.1), M['paint'], (0.25, 0.25, 0.26))
    for (cx, cy, sx, sy) in ((tx, 0.98, 3.4, 0.06), (tx, -0.98, 3.4, 0.06), (tx + 1.68, 0, 0.06, 2.0), (tx - 1.68, 0, 0.06, 2.0)):
        K.obj(bbox(cx, cy, 1.15, sx, sy, 0.7), M['wood'], (0.1, 0.2, 0.08), 'box', 1.0, 0.01, 1)
    for k in range(18):                                                                           # a load of melons
        rng = np.random.default_rng(k); K.obj(lathe([(0.0, -0.13), (0.15, -0.06), (0.16, 0.0), (0.15, 0.06), (0.0, 0.13)], 10, tx + rng.uniform(-1.4, 1.4), rng.uniform(-0.75, 0.75), 1.0 + rng.uniform(0, 0.2)), M['smooth'], (0.04, 0.14, 0.03))
    K.obj(sweep([(tx + 1.7, 0, 0.75), (-2.1, 0, 0.55)], 0.05, 6), M['paint'], (0.25, 0.25, 0.26))


# ------------------------------------------------------------------ 9 walls, fences and gate
def walls_fences(K, M):
    """Dry-stone field wall, timber post-and-rail fence, and a five-bar farm gate hung between stone piers."""
    rng = np.random.default_rng(5)
    for row in range(5):                                                                          # dry-stone wall along y from -8 to 0
        y = -5.0
        while y < -0.6:
            l = rng.uniform(0.35, 0.7); hh = rng.uniform(0.2, 0.3); w = 0.7 - row * 0.07
            K.obj(bbox(rng.uniform(-0.04, 0.04), y + l / 2, row * 0.24 + hh / 2, w, l - 0.02, hh, rng.uniform(-0.05, 0.05)), M['brick4'], tuple(np.array([0.95, 0.92, 0.85]) * rng.uniform(0.75, 1.05)), 'box', 1.2, 0.04, 2)
            y += l
    y = -5.0
    while y < -0.6:                                                                               # coping stones on edge
        l = rng.uniform(0.14, 0.22); K.obj(bbox(0, y + l / 2, 1.38, 0.38, l - 0.015, 0.34, rng.uniform(-0.1, 0.1)), M['brick4'], tuple(np.array([0.9, 0.88, 0.82]) * rng.uniform(0.75, 1.0)), 'box', 1.2, 0.03, 1); y += l
    for k in range(18):                                                                           # moss and grass at the foot
        K.obj(lathe([(0.0, 0.0), (0.12, 0.03), (0.0, 0.14)], 6, rng.uniform(-0.45, 0.45), rng.uniform(-5, -1), 0.0), M['plastic'], (0.2, 0.32, 0.1))
    for x0 in (0.0,):                                                                              # stone gate piers and gate
        for y in (-0.2, 3.6):
            K.obj(bbox(x0, y, 0.85, 0.6, 0.6, 1.7), M['ashlar'], STONE, 'box', 1.0, 0.02, 2); K.obj(lathe([(0.42, 0.0), (0.42, 0.1), (0.0, 0.3)], 4, x0, y, 1.7, a0=math.pi / 4, a1=math.pi / 4 + 2 * math.pi), M['ashlar'], STONE, smooth=False)
        for z in np.linspace(0.25, 1.15, 5): K.obj(bbox(x0, 1.7, z, 0.07, 3.3, 0.09), M['pwood'], (0.9, 0.88, 0.82), 'box', 1.0, 0.008, 1)
        for y in (0.1, 3.3): K.obj(bbox(x0, y, 0.7, 0.08, 0.12, 1.2), M['pwood'], (0.9, 0.88, 0.82), 'box', 1.0, 0.008, 1)
        K.obj(HS._board_any((x0 + 0.05, 0.15, 0.25), (x0 + 0.05, 3.25, 1.15), (1, 0, 0), 0.06, 0.1), M['pwood'], (0.9, 0.88, 0.82))
    for k in range(4):                                                                            # post-and-rail fence from y = 4 onward, slightly crooked
        y = 4.0 + k * 2.2; tilt = rng.uniform(-0.05, 0.05)
        K.obj(bbox(rng.uniform(-0.05, 0.05), y, 0.65, 0.16, 0.16, 1.3, tilt), M['wood'], (0.5, 0.42, 0.33), 'box', 1.0, 0.02, 2)
        if k < 3:
            for z in (0.5, 1.0): K.obj(sweep([(0.1, y, z + rng.uniform(-0.03, 0.03)), (0.1, y + 2.2, z + rng.uniform(-0.03, 0.03))], 0.06, 6), M['wood'], (0.55, 0.47, 0.37))


# ------------------------------------------------------------------ 10 hay bales
def hay_field(K, M):
    """Harvested field corner: rows of round bales (some wrapped in white film), a square-bale stack and a bale fork."""
    rng = np.random.default_rng(11)
    for k in range(9):
        x = -3.0 + (k % 3) * 2.6 + rng.uniform(-0.3, 0.3); y = -3.0 + (k // 3) * 2.6 + rng.uniform(-0.3, 0.3)
        bale_round(K, M, x, y, rng.uniform(-0.4, 0.4), wrapped=(k in (2, 5, 6)))
    for lvl in range(3):
        for i in range(4 - lvl):
            for j in range(2): bale_square(K, M, 4.0 + j * 0.52, -1.5 + i * 1.05 + lvl * 0.52, lvl * 0.42, math.pi / 2)
    K.obj(sweep([(3.6, 2.4, 0.05), (3.4, 2.5, 1.4)], 0.02, 5), M['wood'], (0.6, 0.5, 0.35))
    for o in (-0.06, 0.0, 0.06): K.obj(sweep([(3.6 + o, 2.4, 0.05), (3.7 + o, 2.3, -0.25)], 0.008, 4), M['iron'], IRON)


# ------------------------------------------------------------------ 11 vineyard
def vineyard(K, M):
    """Four vine rows on chestnut posts and wires: twisted trunks, leafy canopy along the fruiting wire, purple bunches."""
    rng = np.random.default_rng(13)
    for r_ in range(4):
        x = -3.0 + r_ * 2.0
        for k in range(9):
            y = -8.0 + k * 2.0
            K.obj(bbox(x, y, 0.9, 0.09, 0.09, 1.8, rng.uniform(-0.03, 0.03)), M['wood'], (0.45, 0.38, 0.3), 'box', 1.0, 0.01, 1)
        for z in (0.8, 1.25, 1.65): K.obj(sweep([(x, -8.0, z), (x, 8.0, z)], 0.006, 4), M['galv'], (0.6, 0.6, 0.6))
        for k in range(16):
            y = -7.5 + k * 1.0
            K.obj(sweep([(x, y, 0.0), (x + rng.uniform(-0.06, 0.06), y + rng.uniform(-0.08, 0.08), 0.45), (x, y + 0.05, 0.8)], 0.04, 6), M['wood'], (0.35, 0.27, 0.2))
            for j in range(2 if P.LOD else 5):                                                    # canopy clumps (far copy: fewer, larger)
                s = rng.uniform(0.2, 0.32); g = rng.uniform(0.75, 1.2)
                K.obj(lathe([(0.0, -s * 0.5), (s, -s * 0.2), (s * 0.9, s * 0.3), (0.0, s * 0.6)], 6, x + rng.uniform(-0.25, 0.25), y + rng.uniform(-0.5, 0.5), 0.85 + rng.uniform(0, 0.85)), M['concrete'], tuple(np.asarray(LEAF) * g * np.array([1.6, 1.5, 1.3])))
            for j in range(2):
                K.obj(lathe([(0.0, 0.0), (0.06, 0.05), (0.05, 0.14), (0.0, 0.2)], 6, x + rng.choice([-0.22, 0.22]), y + rng.uniform(-0.4, 0.4), 0.72), M['plastic'], (0.25, 0.08, 0.22))


# ------------------------------------------------------------------ 12 roadside farm stand
def farm_stand(K, M):
    """Timber produce stall: striped awning, crates of oranges, lemons, tomatoes and melons, a chalkboard and an old scale."""
    W = 3.6
    for (x, y) in ((-0.6, -W / 2), (-0.6, W / 2), (0.8, -W / 2), (0.8, W / 2)): K.obj(bbox(x, y, 1.25, 0.1, 0.1, 2.5), M['wood'], (0.55, 0.42, 0.28), 'box', 1.0, 0.01, 1)
    K.obj(bbox(0.55, 0, 0.85, 0.7, W + 0.1, 0.06), M['wood'], (0.65, 0.5, 0.33), 'box', 1.0, 0.01, 1)
    K.obj(bbox(0.9, 0, 0.43, 0.04, W + 0.1, 0.84), M['wood'], (0.6, 0.45, 0.3), 'box', 1.0, 0.0)
    for k in range(10):                                                                           # striped awning sloping to the front
        y0 = -W / 2 - 0.2 + k * (W + 0.4) / 10; aw = prism([(-0.7, 2.5), (1.5, 2.05), (1.5, 2.02), (-0.7, 2.47)], y0, y0 + (W + 0.4) / 10, axis='x')
        for v in aw.verts: a, b, c = v.co; v.co = (b, a, c)
        K.obj(aw, M['fabric'], (0.92, 0.9, 0.84) if k % 2 else (0.05, 0.2, 0.1), 'box', 1.0, 0.0, smooth=False)
    for k in range(10): y0 = -W / 2 - 0.2 + (k + 0.5) * (W + 0.4) / 10; K.obj(prism([(0, 0), (0.18, 0), (0.09, -0.18)], -0.005, 0.005, axis='y'), M['fabric'], (0.92, 0.9, 0.84) if k % 2 else (0.05, 0.2, 0.1)) if False else K.obj(bbox(1.5, y0, 1.94, 0.02, (W + 0.4) / 10 - 0.02, 0.16), M['fabric'], (0.92, 0.9, 0.84) if k % 2 else (0.05, 0.2, 0.1))
    fruits = [((0.9, 0.22, 0.01), 0.045), ((0.95, 0.7, 0.04), 0.04), ((0.6, 0.02, 0.01), 0.045), ((0.1, 0.25, 0.03), 0.1), ((0.18, 0.02, 0.1), 0.035)]
    rng = np.random.default_rng(17)
    for i, (col, r) in enumerate(fruits):                                                         # crates on the counter
        y = -W / 2 + 0.4 + i * 0.7; K.obj(bbox(0.55, y, 0.98, 0.5, 0.6, 0.2), M['wood'], (0.75, 0.6, 0.4), 'box', 1.0, 0.006, 1)
        n = int(0.4 * 0.5 / (r * r * 4))
        for k in range(min(n, 40)): K.obj(lathe([(0.0, -r), (r, 0.0), (0.0, r)], 8, 0.55 + rng.uniform(-0.2, 0.2), y + rng.uniform(-0.25, 0.25), 1.08 + r + rng.uniform(0, 0.06)), M['smooth'], tuple(np.asarray(col) * rng.uniform(0.85, 1.1)))
    for i in range(3):                                                                            # crates stacked on the ground in front
        K.obj(bbox(1.4, -1.0 + i * 0.7, 0.15, 0.5, 0.6, 0.3), M['wood'], (0.75, 0.6, 0.4), 'box', 1.0, 0.006, 1)
        for k in range(14): K.obj(lathe([(0.0, -0.05), (0.05, 0.0), (0.0, 0.05)], 8, 1.4 + rng.uniform(-0.2, 0.2), -1.0 + i * 0.7 + rng.uniform(-0.25, 0.25), 0.33), M['smooth'], fruits[i][0])
    K.obj(bbox(2.0, 1.4, 0.55, 0.06, 0.6, 0.8, 0.3), M['paint'], (0.12, 0.13, 0.12), 'box', 1.0, 0.01, 1)                  # chalkboard on an easel
    K.obj(bbox(2.03, 1.4, 0.6, 0.02, 0.5, 0.6, 0.3), M['sign'], (1, 1, 1), 'sign', 1.0, sign=P.sign_cell_uv(9, 2.03, 1.4, 0.5, 0.6, True)) if False else None
    K.obj(lathe([(0.0, 0.0), (0.12, 0.0), (0.1, 0.25), (0.18, 0.28), (0.18, 0.3), (0.0, 0.3)], 12, 0.5, 1.5, 0.88), M['iron'], (0.2, 0.35, 0.3))   # scale


ITEMS = dict(cottage_b=(lambda K, M: cottage(K, M, (0.9, 0.66, 0.36), SAGE), 6.5), farmhouse=(farmhouse, 10.0), village_row=(village_row, 13.0), cottage=(cottage, 6.5), barn_hq=(barn, 12.0), hay_shed=(hay_shed, 6.5),
             silos=(silos, 11.0), winery_hq=(winery, 7.0), tractor=(tractor, 2.6), walls_fences=(walls_fences, 1.8), hay_field=(hay_field, 1.6),
             vineyard=(vineyard, 1.8), farm_stand=(farm_stand, 2.5))


# footprint (W along y, D along x) for the map's foundations and collision, as isle_houses.FOOT
FOOT = dict(cottage=(10.0, 6.5), cottage_b=(10.0, 6.5), farmhouse=(13.5, 8.5), village_row=(16.6, 9.0), barn_hq=(16.0, 10.0), winery_hq=(14.0, 8.0))


def register():
    for k, (fn, h) in ITEMS.items(): P.PROPS[k] = (fn, {}); P.HEIGHT[k] = h

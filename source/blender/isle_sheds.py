"""Farm and harbour buildings for Aurelia Island, modelled like the houses: a red timber barn with sliding doors and hay loft,
a stone winery, a corrugated-steel harbour warehouse with roller doors and a loading canopy, and painted fishermen's huts.
Front faces +X, origin on the ground at the middle of the footprint (sizes match the map's footprints)."""
import math
import numpy as np
import isle_props as P
import isle_houses as HS
from isle_houses import Frame, walls, window, door, gable_roof, chimney
from isle_props import bbox, lathe, sweep, prism


def fronts(W, D):
    return [(Frame((D / 2, 0, 0), (0, 1, 0), (1, 0, 0)), W), (Frame((-D / 2, 0, 0), (0, -1, 0), (-1, 0, 0)), W),
            (Frame((0, W / 2, 0), (-1, 0, 0), (0, 1, 0)), D), (Frame((0, -W / 2, 0), (1, 0, 0), (0, -1, 0)), D)]


def sliding_door(K, M, F, uc, z0, w, h, col, trim=(0.95, 0.94, 0.9)):
    """Two timber leaves on a top rail, white edge boards and X bracing."""
    for sg in (-1, 1):
        u0, u1 = (uc - w / 2, uc) if sg < 0 else (uc, uc + w / 2)
        K.obj(F.box(u0, u1, 0.0, 0.06, z0, z0 + h), M['planks'], col, 'boxv', 1.6, 0.008, 1)
        for (a, b, c, d) in ((u0, u0 + 0.14, z0, z0 + h), (u1 - 0.14, u1, z0, z0 + h), (u0, u1, z0, z0 + 0.14), (u0, u1, z0 + h - 0.14, z0 + h), (u0, u1, z0 + h / 2 - 0.07, z0 + h / 2 + 0.07)):
            K.obj(F.box(a, b, 0.06, 0.1, c, d), M['pwood'], trim, 'box', 1.0, 0.008, 1)
        for (za, zb) in ((z0, z0 + h / 2), (z0 + h / 2, z0 + h)):
            p0 = F.w(u0 + 0.1, 0.08, za + 0.1); p1 = F.w(u1 - 0.1, 0.08, zb - 0.1); q0 = F.w(u0 + 0.1, 0.08, zb - 0.1); q1 = F.w(u1 - 0.1, 0.08, za + 0.1)
            for a, b in ((p0, p1), (q0, q1)): K.obj(HS._board_any(a, b, F.n, 0.04, 0.12), M['pwood'], trim, 'box', 1.0)
    K.obj(F.box(uc - w - 0.3, uc + w + 0.3, 0.12, 0.2, z0 + h + 0.05, z0 + h + 0.16), M['galv'], (0.55, 0.56, 0.58), 'box', 1.0, 0.01, 1)   # rail


def roller_door(K, M, F, uc, z0, w, h, col=(0.72, 0.74, 0.76)):
    K.obj(F.box(uc - w / 2, uc + w / 2, -0.12, -0.08, z0, z0 + h), M['corr'], col, 'boxv', 1.6)       # ribs run across a roller door
    for sg in (-1, 1): K.obj(F.box(uc + sg * (w / 2 + 0.06) - 0.06, uc + sg * (w / 2 + 0.06) + 0.06, -0.2, 0.06, z0, z0 + h + 0.1), M['galv'], (0.55, 0.57, 0.6), 'box', 1.0, 0.01, 1)
    K.obj(F.box(uc - w / 2 - 0.12, uc + w / 2 + 0.12, -0.05, 0.38, z0 + h + 0.05, z0 + h + 0.6), M['galv'], (0.6, 0.62, 0.65), 'box', 1.0, 0.02, 2)   # drum housing
    for sg in (-1, 1): K.obj(lathe([(0.12, 0), (0.12, 1.0), (0.13, 1.02), (0.0, 1.04)], 12, *F.w(uc + sg * (w / 2 + 0.35), 0.35, 0)[:2]), M['paint'], (0.95, 0.75, 0.15), 'cyl', 0.5)   # bollards


def barn(K, M, W=20.0, D=11.0, h=6.0, rise=4.5, col=(0.62, 0.17, 0.12)):
    K.obj(bbox(0, 0, 0.2, D + 0.1, W + 0.1, 0.8), M['concrete'], (0.85, 0.85, 0.83), 'box', 1.6, 0.015, 2)
    z0 = 0.55
    for k, (F, Ln) in enumerate(fronts(W, D)):
        holes = []; L2 = Ln if k < 2 else Ln - 0.5
        if k == 0: holes += [(-2.5, 2.5, z0, z0 + 4.2), (-1.0, 1.0, z0 + 4.8, z0 + 5.8)]
        nw = int(Ln / 4.5)
        for i in range(nw):
            uc = -Ln / 2 + (i + 0.5) * Ln / nw
            if abs(uc) < 3.4 and k == 0: continue
            holes.append((uc - 0.45, uc + 0.45, z0 + 2.4, z0 + 3.3))
        walls(K, M, F, L2, z0, z0 + h, holes, col, 0.2, M['planks'], 'boxv', 3.2)
        for (a, b, c, d) in holes:
            if d - c < 1.2: window(K, M, F, (a + b) / 2, c, b - a, d - c, None, (0.95, 0.94, 0.9), 0.2)
        if k == 0:
            sliding_door(K, M, F, 0.0, z0, 5.0, 4.2, col * np.array([0.95, 1, 1]))
            K.obj(F.box(-1.0, 1.0, -0.12, -0.08, z0 + 4.8, z0 + 5.8), M['planks'], np.asarray(col) * 0.8, 'boxv', 1.6)        # hay loft door
            K.obj(sweep([tuple(F.w(0, 0.0, z0 + 6.4)), tuple(F.w(0, 1.2, z0 + 6.4)), tuple(F.w(0, 1.2, z0 + 6.0))], 0.06, 8), M['iron'], (0.25, 0.25, 0.27))   # hay hoist beam
        for (sx, sy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)): K.obj(bbox(sx * (D / 2 - 0.05), sy * (W / 2 - 0.05), z0 + h / 2, 0.22, 0.22, h), M['pwood'], (0.95, 0.94, 0.9), 'box', 1.0, 0.01, 1)
    K.obj(bbox(0, 0, z0 + h - 0.1, D - 0.3, W - 0.3, 0.2), M['planks'], col)
    gable_roof(K, M, W, D, z0 + h, rise, (0.62, 0.64, 0.66), col, 0.6, 0.12, 'y', M['corr'], M['planks'], 'boxv', 2.4, (0.95, 0.94, 0.9))
    for yy in (-W * 0.25, W * 0.25):                                                          # roof ventilators
        K.obj(lathe([(0.35, 0), (0.35, 0.5), (0.5, 0.55), (0.0, 0.85)], 12, 0, yy, z0 + h + rise - 0.1), M['galv'], (0.7, 0.72, 0.74), 'cyl', 1.0, 0.0)


def winery(K, M, W=24.0, D=12.0, h=6.5, rise=5.0):
    K.obj(bbox(0, 0, 0.25, D + 0.12, W + 0.12, 0.9), M['stone'], (0.78, 0.74, 0.68), 'box', 1.6, 0.015, 2)
    z0 = 0.6; col = (0.88, 0.8, 0.68)
    for k, (F, Ln) in enumerate(fronts(W, D)):
        holes = []; items = []; L2 = Ln if k < 2 else Ln - 0.8; nw = int(Ln / 3.2)
        for f in range(2):
            for i in range(nw):
                uc = -Ln / 2 + (i + 0.5) * Ln / nw
                if k == 0 and f == 1 and i == nw // 2: continue
                if k == 0 and f == 0 and i == nw // 2: holes.append((uc - 1.2, uc + 1.2, z0, z0 + 3.0)); items.append(('door', uc)); continue
                zb = z0 + 0.9 + f * 3.1; holes.append((uc - 0.5, uc + 0.5, zb, zb + 1.5)); items.append(('win', uc, zb))
        walls(K, M, F, L2, z0, z0 + h, holes, col, 0.4, M['stone'], 'box', 1.6)
        for it in items:
            if it[0] == 'door':
                for sg in (-1, 1): K.obj(F.box(it[1] + sg * 0.6 - 0.6, it[1] + sg * 0.6 + 0.6, -0.3, -0.24, z0, z0 + 3.0), M['planks'], (0.55, 0.36, 0.22), 'boxv', 1.6, 0.008, 1)
                K.obj(F.box(it[1] - 1.5, it[1] + 1.5, -0.02, 0.12, z0 + 3.0, z0 + 3.45), M['stone'], (0.95, 0.92, 0.85), 'box', 1.2, 0.015, 2)
            else: window(K, M, F, it[1], it[2], 1.0, 1.5, (0.42, 0.28, 0.18), (0.88, 0.86, 0.8), 0.4)
    for (sx, sy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        for q in range(int(h / 0.55)):
            zz = z0 + q * 0.55; lw = 0.55 if q % 2 else 0.32
            K.obj(bbox(sx * (D / 2 + 0.015) - sx * lw / 2, sy * (W / 2 + 0.015) - sy * 0.16, zz + 0.25, lw, 0.32, 0.5), M['stone'], (0.95, 0.9, 0.82), 'box', 1.0, 0.0, 1)
    K.obj(bbox(0, 0, z0 + h - 0.1, D - 0.6, W - 0.6, 0.2), M['stone'], col)
    gable_roof(K, M, W, D, z0 + h, rise, (0.8, 0.42, 0.28), col, 0.55, 0.2, 'y', None, M['stone'], 'box', 1.7)
    chimney(K, M, -D * 0.2, -W * 0.3, z0 + h + rise * 0.4, z0 + h + rise + 0.9)
    for yy in np.linspace(-W / 2 + 2, W / 2 - 2, 5):                                          # barrels by the front wall
        K.obj(lathe([(0.0, 0), (0.33, 0), (0.38, 0.2), (0.4, 0.45), (0.38, 0.7), (0.33, 0.9), (0.0, 0.9)], 16, D / 2 + 0.7, yy if abs(yy) > 2 else yy + 3.5, 0), M['planks'], (0.75, 0.5, 0.3), 'cylv', 1.2, 0.0)
        for zz in (0.15, 0.75): K.obj(lathe([(0.37, zz), (0.37, zz + 0.05)], 16, D / 2 + 0.7, yy if abs(yy) > 2 else yy + 3.5, 0, close_top=False, close_bottom=False), M['iron'], (0.3, 0.3, 0.3))


def warehouse(K, M, W=38.0, D=30.0, h=9.3, rise=3.2):
    K.obj(bbox(0, 0, 0.15, D + 0.1, W + 0.1, 0.7), M['concrete'], (0.85, 0.85, 0.83), 'box', 2.0, 0.015, 2)
    z0 = 0.5; col = (0.62, 0.68, 0.72)
    for k, (F, Ln) in enumerate(fronts(W, D)):
        holes = []; L2 = Ln if k < 2 else Ln - 0.5; rd = []
        if k == 0:
            for uc in (-11.0, 0.0, 11.0): holes.append((uc - 2.6, uc + 2.6, z0, z0 + 5.2)); rd.append(uc)
            holes.append((5.0, 6.0, z0, z0 + 2.2))
        nst = int(Ln / 3.0)
        for i in range(nst):                                                                  # clerestory window strip
            uc = -Ln / 2 + (i + 0.5) * Ln / nst; holes.append((uc - 1.1, uc + 1.1, z0 + 6.3, z0 + 7.5))
        K.obj(F.box(-L2 / 2, L2 / 2, -0.3, 0.02, z0, z0 + 1.4) if k else F.box(-L2 / 2, -13.7, -0.3, 0.02, z0, z0 + 1.4), M['concrete'], (0.8, 0.8, 0.78), 'box', 2.0, 0.012, 1)
        walls(K, M, F, L2, z0, z0 + h, holes, col, 0.25, M['corr'], 'box', 2.6)
        for (a, b, c, d) in holes:
            if d - c < 1.5: window(K, M, F, (a + b) / 2, c, b - a, d - c, None, (0.55, 0.57, 0.6), 0.25)
        for uc in rd: roller_door(K, M, F, uc, z0, 5.2, 5.2)
        if k == 0:
            door(K, M, F, 5.5, z0, 1.0, 2.2, (0.2, 0.35, 0.55), canopy=False)
            K.obj(F.box(-15, 15, 0.0, 3.2, z0 + 5.9, z0 + 6.1), M['corr'], (0.66, 0.68, 0.7), 'roof', 1.4, 0.01, 1)        # loading canopy
            for uu in np.linspace(-14, 14, 6): K.obj(sweep([tuple(F.w(uu, 0.05, z0 + 7.4)), tuple(F.w(uu, 3.1, z0 + 6.1))], 0.04, 6), M['galv'], (0.6, 0.62, 0.65))
            K.obj(F.box(-14.5, -7.5, 0.0, 1.8, 0, z0 + 0.7), M['concrete'], (0.75, 0.75, 0.73), 'box', 2.0, 0.02, 2)     # dock
        for (a, b) in ((-Ln / 2, -Ln / 2 + 0.25), (Ln / 2 - 0.25, Ln / 2)): K.obj(F.box(a, b, 0.0, 0.06, z0, z0 + h), M['galv'], (0.5, 0.52, 0.55))
    K.obj(bbox(0, 0, z0 + h - 0.1, D - 0.6, W - 0.6, 0.2), M['concrete'], col)
    gable_roof(K, M, W, D, z0 + h, rise, (0.58, 0.6, 0.62), col, 0.5, 0.15, 'y', M['corr'], M['corr'], 'box', 2.6, (0.55, 0.57, 0.6))
    for yy in np.linspace(-W / 2 + 4, W / 2 - 4, 5):                                          # roof-light strips
        for sg in (-1, 1): K.obj(bbox(sg * D * 0.22, yy, z0 + h + rise * 0.56 + 0.1, 3.0, 1.6, 0.06), M['winglass'], (1, 1, 1))


def hut(K, M, W=6.0, D=6.0, h=3.5, rise=1.6, wall=(0.95, 0.95, 0.92), roof=(0.7, 0.16, 0.12)):
    for (sx, sy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)): K.obj(bbox(sx * (D / 2 - 0.3), sy * (W / 2 - 0.3), 0.2, 0.25, 0.25, 0.8), M['concrete'], (0.7, 0.7, 0.68))   # piers
    K.obj(bbox(0, 0, 0.5, D, W, 0.15), M['planks'], (0.6, 0.5, 0.4), 'box', 1.6, 0.008, 1)
    z0 = 0.58
    for k, (F, Ln) in enumerate(fronts(W, D)):
        holes = []
        if k == 0: holes.append((-1.6, -0.6, z0, z0 + 2.1))
        if k in (0, 2, 3): holes.append((0.6, 1.6, z0 + 1.0, z0 + 2.0))
        walls(K, M, F, Ln if k < 2 else Ln - 0.24, z0, z0 + h - 0.5, holes, wall, 0.12, M['boards'], 'box', 1.2)
        for (a, b, c, d) in holes:
            if c > z0: window(K, M, F, (a + b) / 2, c, b - a, d - c, (np.asarray(roof) * 0.9).tolist(), (0.95, 0.95, 0.92), 0.12)
            else: door(K, M, F, (a + b) / 2, c, 1.0, 2.1, tuple(np.asarray(roof) * 0.9), canopy=False)
        for (sx, sy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)): K.obj(bbox(sx * (D / 2 - 0.02), sy * (W / 2 - 0.02), z0 + (h - 0.5) / 2, 0.12, 0.12, h - 0.5), M['pwood'], (0.95, 0.94, 0.9), 'box', 1.0, 0.008, 1)
    K.obj(bbox(0, 0, z0 + h - 0.6, D - 0.2, W - 0.2, 0.15), M['boards'], wall)
    gable_roof(K, M, W, D, z0 + h - 0.5, rise, roof, wall, 0.35, 0.1, 'y', M['corr'], M['boards'], 'box', 1.2)
    for yy in (-1.2, 0.0, 1.2): K.obj(lathe([(0.0, 0), (0.25, 0), (0.25, 0.4), (0.0, 0.4)], 12, D / 2 + 0.8, yy, 0.0), M['wood'], (0.75, 0.6, 0.45), 'cylv', 0.8)   # crates / buoys? (fish barrels)


DESIGNS = {
    'barn': (barn, {}), 'winery': (winery, {}), 'warehouse': (warehouse, {}),
    'hut_red': (hut, dict(roof=(0.7, 0.16, 0.12))), 'hut_blue': (hut, dict(roof=(0.18, 0.32, 0.6), wall=(0.92, 0.9, 0.84))),
}
HEIGHT = dict(barn=11.5, winery=12.5, warehouse=13.5, hut_red=5.5, hut_blue=5.5)


def register():
    for k, (fn, kw) in DESIGNS.items():
        P.PROPS[k] = (lambda K, M, fn=fn, kw=kw: fn(K, M, **kw), {}); P.HEIGHT[k] = HEIGHT[k]

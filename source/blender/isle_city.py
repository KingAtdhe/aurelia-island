"""City blocks for Aurelia Island, modelled like the houses: a stone-clad ground floor of shopfronts (glazing with mullions and transoms,
recessed doors, fascia with a name panel, fabric awnings, pilasters), upper floors in brick, painted render or concrete with framed windows,
stone sills and lintels, French balconies, floor bands, a moulded cornice and parapet with coping, and a flat roof with plant:
stair housing, air-conditioning units with fans and a water tank. Built per building at its real footprint (not instanced) and
emitted as the near (HD) version of the 200 m tile it stands in; the existing far version stays for distance."""
import math
import numpy as np
import isle_props as P
from isle_houses import Frame, walls
from isle_props import bbox, lathe, prism, poly_round

STYLES = ('brick', 'plaster', 'modern', 'artdeco', 'loft')
WALLC = {'brick': [(0.95, 0.88, 0.85), (0.85, 0.72, 0.66), (1.0, 0.95, 0.9), (0.78, 0.62, 0.55), (0.92, 0.8, 0.7)],
         'plaster': [(0.97, 0.86, 0.66), (0.93, 0.74, 0.6), (0.82, 0.88, 0.92), (0.86, 0.92, 0.82), (0.98, 0.93, 0.82), (0.9, 0.66, 0.55), (0.95, 0.82, 0.86), (0.8, 0.86, 0.78), (0.99, 0.96, 0.9)],
         'modern': [(0.9, 0.9, 0.88), (0.78, 0.78, 0.76), (0.62, 0.64, 0.66), (0.86, 0.82, 0.76)], 'artdeco': [(0.95, 0.92, 0.85), (0.88, 0.86, 0.82), (0.96, 0.88, 0.78)], 'loft': [(0.7, 0.55, 0.5), (0.62, 0.5, 0.46), (0.55, 0.42, 0.38)]}
AWN = [(0.62, 0.12, 0.1), (0.15, 0.32, 0.22), (0.16, 0.24, 0.42), (0.3, 0.3, 0.32), (0.75, 0.55, 0.2)]


def fronts(W, D):
    return [(Frame((D / 2, 0, 0), (0, 1, 0), (1, 0, 0)), W), (Frame((-D / 2, 0, 0), (0, -1, 0), (-1, 0, 0)), W),
            (Frame((0, W / 2, 0), (-1, 0, 0), (0, 1, 0)), D), (Frame((0, -W / 2, 0), (1, 0, 0), (0, -1, 0)), D)]


def cwindow(K, M, F, uc, z0, w, h, frame, t, stone=(0.93, 0.91, 0.86), lintel=True, mull=True):
    a, b = uc - w / 2, uc + w / 2; fr = 0.08; inset = -0.14
    K.obj(F.rect(a, b, inset - 0.04, z0, z0 + h), M['smooth'], frame, smooth=False)                                   # frame (shows as a ring round the pane)
    K.obj(F.rect(a + fr, b - fr, inset - 0.025, z0 + fr, z0 + h - fr), M['winglass'], (1, 1, 1), smooth=False)
    if mull: K.obj(F.fin(uc - 0.03, uc + 0.03, inset - 0.025, inset + 0.0, z0 + fr, z0 + h - fr), M['smooth'], frame, smooth=False)
    K.obj(F.box(a - 0.07, b + 0.07, -0.16, 0.07, z0 - 0.08, z0, back=False), M['stone'], stone, 'box', 1.2, smooth=False)
    if lintel: K.obj(F.box(a - 0.1, b + 0.1, -0.02, 0.03, z0 + h, z0 + h + 0.22, back=False), M['stone'], stone, 'box', 1.2, smooth=False)


def shopfront(K, M, F, a, b, gf, rng, door):
    """Glazed shop bay between u=a and u=b, ground floor height gf."""
    w = b - a; uc = (a + b) / 2; z0 = 0.15; zt = gf - 0.95
    frame = (0.16, 0.17, 0.18) if rng.random() < 0.6 else (0.85, 0.84, 0.8)
    segs = [(a, uc - 0.6), (uc + 0.6, b)] if door else [(a, b)]
    for s0, s1 in segs:
        K.obj(F.box(s0, s1, -0.32, -0.12, 0.0, z0 + 0.45), M['stone'], (0.7, 0.68, 0.66), 'box', 1.2)          # stall riser
        K.obj(F.box(s0, s1, -0.3, -0.28, z0 + 0.45, zt), M['winglass'], (1, 1, 1))
        n = max(1, int((s1 - s0) / 1.3))
        for i in range(n + 1): u = s0 + (s1 - s0) * i / n; K.obj(F.fin(u - 0.04, u + 0.04, -0.3, -0.2, z0 + 0.45, zt), M['smooth'], frame, smooth=False)
        for zz in (z0 + 0.45, zt - 0.6): K.obj(F.box(s0, s1, -0.3, -0.2, zz - 0.04, zz + 0.04), M['smooth'], frame)
    K.obj(F.box(a, b, -0.3, -0.2, zt - 0.04, zt + 0.04), M['smooth'], frame)
    if door:                                                                                  # glazed door set back in a lined recess
        K.obj(F.box(uc - 0.6, uc + 0.6, -0.34, -0.3, 0.0, zt), M['smooth'], frame)
        K.obj(F.box(uc - 0.5, uc + 0.5, -0.3, -0.29, 0.1, z0 + 2.2), M['winglass'], (1, 1, 1))
        K.obj(F.box(uc - 0.5, uc + 0.5, -0.3, -0.28, z0 + 2.3, zt - 0.08), M['winglass'], (1, 1, 1))
        K.obj(F.box(uc - 0.6, uc + 0.6, -0.34, 0.0, -0.02, 0.06), M['stone'], (0.85, 0.83, 0.8), 'box', 1.2)
        K.obj(sweep_handle(F, uc + 0.35, -0.28, z0 + 1.05), M['galv'], (0.85, 0.85, 0.85))
    K.obj(F.box(a - 0.05, b + 0.05, -0.05, 0.12, zt + 0.05, gf - 0.25), M['pwood'], AWN[rng.integers(len(AWN))] if rng.random() < 0.5 else (0.2, 0.21, 0.23), 'box', 1.0)   # fascia
    sw = min(w * 0.7, 3.2)
    K.obj(F.box(uc - sw / 2, uc + sw / 2, 0.12, 0.14, zt + 0.15, gf - 0.35), M['shops'], (1, 1, 1), 'sign', 1.0,
          sign=P.sign_cell_uv_frame(F, int(rng.integers(16)), uc, (zt + gf - 0.2) / 2, sw, gf - 0.5 - zt))
    if rng.random() < 0.55:                                                                  # fabric awning on two arms
        col = AWN[rng.integers(len(AWN))]; aw = prism([(0.14, zt + 0.02), (1.25, zt - 0.55), (1.25, zt - 0.72), (0.14, zt - 0.08)], a + 0.1, b - 0.1, axis='x')
        for v in aw.verts: x_, y_, z_ = v.co; p = F.w(x_, y_, z_); v.co = tuple(p)
        K.obj(aw, M['fabric'], col, 'box', 0.8)
        for u in (a + 0.25, b - 0.25): K.obj(P.sweep([tuple(F.w(u, 0.1, zt - 0.7)), tuple(F.w(u, 1.2, zt - 0.62))], 0.02, 5), M['iron'], (0.2, 0.2, 0.2))


def sweep_handle(F, u, n, z):
    return P.sweep([tuple(F.w(u, n - 0.02, z - 0.35)), tuple(F.w(u, n + 0.06, z - 0.3)), tuple(F.w(u, n + 0.06, z + 0.3)), tuple(F.w(u, n - 0.02, z + 0.35))], 0.014, 6)


def cornice(K, M, F, Ln, z, col, depth=0.45):
    prof = [(0.0, 0.0), (0.12, 0.05), (0.16, 0.18), (0.3, 0.25), (depth, 0.38), (depth, 0.5), (0.0, 0.5)]
    bm = prism([(n, zz) for n, zz in prof], -Ln / 2 - depth, Ln / 2 + depth, axis='x')
    for v in bm.verts: u_, n_, z_ = v.co; v.co = tuple(F.w(u_, n_, z + z_))
    K.obj(bm, M['stone'], col, 'box', 1.4, 0.0)


def roof_plant(K, M, W, D, zt, rng):
    K.obj(bbox(0, 0, zt + 0.05, D - 0.6, W - 0.6, 0.1), M['concrete'], (0.55, 0.55, 0.54), 'box', 3.0)                 # roof membrane
    sx, sy = rng.uniform(-D / 4, D / 4), rng.uniform(-W / 4, W / 4)
    K.obj(bbox(sx, sy, zt + 1.6, 4.0, 3.2, 3.2), M['concrete'], (0.85, 0.85, 0.83), 'box', 2.0, 0.02, 1)                # stair / lift housing
    K.obj(bbox(sx + 2.02, sy, zt + 1.2, 0.06, 1.0, 2.1), M['galv'], (0.4, 0.42, 0.45))
    for k in range(int(rng.integers(2, 5))):                                                 # air-conditioning units
        x, y = rng.uniform(-D / 2 + 3, D / 2 - 3), rng.uniform(-W / 2 + 3, W / 2 - 3)
        if abs(x - sx) < 4 and abs(y - sy) < 4: continue
        K.obj(bbox(x, y, zt + 0.75, 1.8, 1.2, 1.2), M['galv'], (0.8, 0.82, 0.84), 'box', 1.0, 0.02, 1)
        K.obj(lathe([(0.45, 0), (0.45, 0.05), (0.0, 0.06)], 16, x, y, zt + 1.35), M['iron'], (0.15, 0.15, 0.16))
    if rng.random() < 0.5:                                                                   # water tank on legs
        x, y = rng.uniform(-D / 2 + 3, D / 2 - 3), rng.uniform(-W / 2 + 3, W / 2 - 3)
        for dx, dy in ((-0.8, -0.8), (0.8, -0.8), (-0.8, 0.8), (0.8, 0.8)): K.obj(bbox(x + dx, y + dy, zt + 1.0, 0.14, 0.14, 2.0), M['galv'], (0.5, 0.5, 0.5))
        K.obj(lathe([(1.2, 0), (1.2, 2.2), (0.9, 2.6), (0.0, 2.8)], 16, x, y, zt + 2.0), M['planks'], (0.7, 0.55, 0.42), 'cylv', 2.0)


def building(K, M, W, D, h, style, rng):
    gf = 4.6; nfl = max(2, int(round((h - gf) / 3.3)) + 1); fh = (h - gf) / (nfl - 1)
    wc = WALLC[style][rng.integers(len(WALLC[style]))]; frame = [(0.92, 0.91, 0.88), (0.22, 0.23, 0.25), (0.25, 0.35, 0.3), (0.45, 0.28, 0.2), (0.3, 0.36, 0.48)][int(rng.integers(5))]
    bk = [M[k] for k in ('brick', 'brick2', 'brick3', 'brick4', 'brickg') if k in M]
    wmat = {'brick': bk[int(rng.integers(len(bk)))], 'plaster': (M['plaster'] if rng.random() < 0.5 or 'plaster2' not in M else M['plaster2']), 'modern': M['concrete2'], 'artdeco': M['ashlar'], 'loft': bk[int(rng.integers(len(bk)))]}[style]
    if wmat is not M['brick'] and style in ('brick', 'loft'): wc = tuple(min(1.0, 0.25 + v * 0.8) for v in wc)       # the photo carries its own colour
    wuv = 2.0 if style in ('brick', 'loft') else 2.8
    bay = {'modern': 1.6, 'artdeco': 3.0, 'loft': 4.2}.get(style, 3.4); french = style == 'plaster' and rng.random() < 0.6
    if style == 'loft': frame = (0.12, 0.12, 0.13)
    for k, (F, Ln) in enumerate(fronts(W, D)):
        L2 = Ln if k < 2 else Ln - 0.7
        # ground floor: stone cladding with shop bays
        ns = max(1, int(L2 / 5.4)); gh = []
        for i in range(ns):
            a = -L2 / 2 + L2 * i / ns + 0.45; b = -L2 / 2 + L2 * (i + 1) / ns - 0.45; gh.append((a, b, 0.0, gf - 0.25))
        walls(K, M, F, L2, 0.0, gf, gh, (0.82, 0.8, 0.76), 0.35, M['ashlar'], 'box', 1.6)
        for i, (a, b, _, _) in enumerate(gh): shopfront(K, M, F, a, b, gf, rng, door=(i % 2 == 0))
        K.obj(F.box(-L2 / 2 - 0.05, L2 / 2 + 0.05, -0.02, 0.12, gf - 0.12, gf + 0.12), M['stone'], (0.9, 0.88, 0.84), 'box', 1.4)   # band over the shops
        # upper floors
        holes = []; items = []
        if style == 'modern':
            for f in range(nfl - 1):
                zb = gf + f * fh + 0.9; holes.append((-L2 / 2 + 0.6, L2 / 2 - 0.6, zb, zb + fh - 1.2)); items.append(('ribbon', zb, fh - 1.2))
        else:
            nw = max(1, int(L2 / bay))
            for f in range(nfl - 1):
                zb = gf + f * fh + 0.85
                for i in range(nw):
                    uc = -L2 / 2 + (i + 0.5) * L2 / nw; ww = {'brick': 1.3, 'artdeco': 1.5, 'loft': 2.6}.get(style, 1.15); wh = min(2.0 if style != 'loft' else 2.3, fh - 1.0 if style == 'loft' else fh - 1.25)
                    holes.append((uc - ww / 2, uc + ww / 2, zb, zb + wh)); items.append(('win', uc, zb, ww, wh, f))
        walls(K, M, F, L2, gf, h, holes, wc, 0.3, wmat, 'box', wuv)
        for it in items:
            if it[0] == 'win' and style == 'loft':                                          # steel factory window: grid of small panes, brick soldier course over it
                a, b, z, hh = it[1] - it[3] / 2, it[1] + it[3] / 2, it[2], it[4]
                K.obj(F.rect(a, b, -0.2, z, z + hh), M['winglass'], (1, 1, 1), smooth=False)
                for u in np.linspace(a, b, 5): K.obj(F.fin(u - 0.03, u + 0.03, -0.2, -0.14, z, z + hh), M['iron'], frame, smooth=False)
                for zz in np.linspace(z, z + hh, 5): K.obj(F.box(a, b, -0.2, -0.14, zz - 0.03, zz + 0.03), M['iron'], frame, smooth=False)
                K.obj(F.box(a - 0.1, b + 0.1, -0.02, 0.03, z + hh, z + hh + 0.3, back=False), M['brick'], (0.55, 0.42, 0.38), 'boxv', 1.0, smooth=False)
                K.obj(F.box(a - 0.06, b + 0.06, -0.14, 0.05, z - 0.08, z, back=False), M['concrete'], (0.8, 0.8, 0.78), smooth=False)
            elif it[0] == 'win':
                cwindow(K, M, F, it[1], it[2], it[3], it[4], frame, 0.3, lintel=style == 'brick' or rng.random() < 0.3)
                if style == 'artdeco': K.obj(F.box(it[1] - it[3] / 2, it[1] + it[3] / 2, -0.06, 0.0, it[2] - 0.95, it[2] - 0.1, back=False), M['smooth'], (0.2, 0.22, 0.26), smooth=False)   # dark spandrel panel
                if french and it[5] % 2 == 0:                                                 # French balcony rail
                    a, b = it[1] - it[3] / 2 - 0.1, it[1] + it[3] / 2 + 0.1; z = it[2]
                    K.obj(F.box(a, b, 0.0, 0.32, z - 0.12, z), M['stone'], (0.93, 0.91, 0.86), 'box', 1.2)
                    for u in np.linspace(a + 0.05, b - 0.05, 6): K.obj(F.box(u - 0.012, u + 0.012, 0.27, 0.3, z, z + 0.95), M['iron'], (0.15, 0.15, 0.16))
                    K.obj(F.box(a, b, 0.25, 0.32, z + 0.93, z + 0.98), M['iron'], (0.15, 0.15, 0.16))
            else:
                zb, hh = it[1], it[2]; a, b = -L2 / 2 + 0.6, L2 / 2 - 0.6
                K.obj(F.box(a, b, -0.24, -0.23, zb, zb + hh), M['winglass'], (1, 1, 1))
                n = int((b - a) / bay)
                for i in range(n + 1): u = a + (b - a) * i / n; K.obj(F.fin(u - 0.04, u + 0.04, -0.24, -0.12, zb, zb + hh), M['galv'], (0.55, 0.57, 0.6), smooth=False)
                K.obj(F.box(a, b, -0.24, -0.12, zb - 0.04, zb + 0.04), M['galv'], (0.55, 0.57, 0.6))
        if style == 'artdeco':                                                                # full-height piers between the window columns
            nw = max(1, int(L2 / bay))
            for i in range(nw + 1):
                u = -L2 / 2 + i * L2 / nw; K.obj(F.box(u - 0.28, u + 0.28, 0.0, 0.3, gf, h + 0.9, back=False), M['ashlar'], (0.96, 0.94, 0.88), 'box', 2.2, smooth=False)
        if style not in ('modern', 'artdeco'):
            for f in range(1, nfl - 1): K.obj(F.box(-L2 / 2, L2 / 2, -0.02, 0.06, gf + f * fh - 0.06, gf + f * fh + 0.06), M['stone'], (0.93, 0.91, 0.86), 'box', 1.4)
        cornice(K, M, F, L2 if k < 2 else D - 0.7, h, (0.93, 0.91, 0.86) if style != 'modern' else (0.8, 0.8, 0.78), 0.45 if style != 'modern' else 0.2)
        K.obj(F.box(-L2 / 2, L2 / 2, -0.3, 0.0, h + 0.5, h + 1.3), wmat, wc, 'box', wuv)        # parapet
        K.obj(F.box(-L2 / 2 - 0.05, L2 / 2 + 0.05, -0.35, 0.05, h + 1.3, h + 1.42), M['stone'], (0.9, 0.88, 0.85), 'box', 1.4)   # coping
    if style == 'plaster':
        for (sx, sy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)): K.obj(bbox(sx * (D / 2 - 0.15), sy * (W / 2 - 0.15), (gf + h) / 2, 0.5, 0.5, h - gf), M['stone'], (0.93, 0.91, 0.86), 'box', 1.4)
    K.obj(bbox(0, 0, h + 0.25, D - 0.5, W - 0.5, 0.5), M['concrete'], (0.6, 0.6, 0.6))
    roof_plant(K, M, W, D, h + 0.5, rng)
    signage(K, M, W, D, h, rng)
    utilities(K, M, W, D, h, rng)


def tower_base(K, M, W, D, rng):
    """Street level of a glass tower: stone plinth band, an entrance portal with a steel-and-glass canopy, revolving door, planters."""
    for k, (F, Ln) in enumerate(fronts(W, D)):
        K.obj(F.box(-Ln / 2 - 0.1, Ln / 2 + 0.1, -0.05, 0.25, 0.0, 0.7, back=False), M['ashlar'], (0.75, 0.74, 0.72), 'box', 1.6)
    F, Ln = fronts(W, D)[0]
    K.obj(F.box(-4.2, 4.2, 0.0, 0.5, 0.0, 6.2, back=False), M['stone'], (0.88, 0.87, 0.84), 'box', 2.0)            # portal surround
    K.obj(F.box(-3.6, 3.6, 0.5, 0.52, 0.2, 5.6), M['winglass'], (1, 1, 1))
    K.obj(F.box(-4.5, 4.5, 0.4, 5.4, 5.7, 5.9), M['galv'], (0.45, 0.47, 0.5), 'box', 2.0)                                 # canopy
    K.obj(F.box(-4.3, 4.3, 0.6, 5.2, 5.9, 5.94), M['winglass'], (1, 1, 1))
    for u in (-4.0, 4.0): K.obj(P.sweep([tuple(F.w(u, 5.0, 5.7)), tuple(F.w(u, 0.6, 7.6))], 0.05, 8), M['galv'], (0.6, 0.62, 0.65))
    c = F.w(0, 1.6, 0); K.obj(lathe([(1.3, 0.0), (1.3, 2.6), (0.0, 2.6)], 24, c[0], c[1], 0.25, close_bottom=False), M['winglass'], (1, 1, 1))   # revolving door drum
    K.obj(lathe([(1.38, 2.6), (1.38, 2.9), (0.0, 2.9)], 24, c[0], c[1], 0.25, close_bottom=False), M['galv'], (0.55, 0.57, 0.6))
    K.obj(F.box(-1.3, 1.3, 1.0, 2.2, 0.0, 0.25), M['stone'], (0.8, 0.8, 0.78), 'box', 1.5)
    for u in (-7.0, 7.0):                                                                     # planters
        K.obj(F.box(u - 1.2, u + 1.2, 0.6, 2.4, 0.0, 0.8), M['stone'], (0.8, 0.79, 0.76), 'box', 1.5)
        K.obj(F.box(u - 1.05, u + 1.05, 0.75, 2.25, 0.8, 0.82), M['concrete'], (0.35, 0.28, 0.2))


def tower_crown(K, M, W, D, rng):
    """Crown on a glass tower's top: a screen of vertical aluminium fins round the plant level, a lit band and a mast."""
    hgt = 7.0
    for k, (F, Ln) in enumerate(fronts(W, D)):
        n = int(Ln / 1.3)
        for i in range(n + 1):
            u = -Ln / 2 + i * Ln / n; K.obj(F.fin(u - 0.06, u + 0.06, -0.1, 0.35, 0.0, hgt), M['galv'], (0.82, 0.84, 0.87), smooth=False)
        K.obj(F.box(-Ln / 2, Ln / 2, -0.1, 0.4, hgt, hgt + 0.5, back=False), M['galv'], (0.7, 0.72, 0.75), smooth=False)
        K.obj(F.rect(-Ln / 2, Ln / 2, 0.36, 0.2, 0.5), M['lens'], (0.85, 0.92, 1.0), smooth=False)
    K.obj(lathe([(0.5, 0.0), (0.25, 14.0), (0.06, 22.0), (0.0, 22.2)], 8, 0, 0, hgt), M['galv'], (0.85, 0.85, 0.88), 'cyl', 3.0)
    K.obj(lathe([(0.18, 0), (0.18, 0.3), (0.0, 0.32)], 8, 0, 0, hgt + 22.0), M['lens'], (1.0, 0.2, 0.15))


def signage(K, M, W, D, h, rng):
    """Projecting neon blade sign at a front corner and, on some roofs, a billboard on a steel frame."""
    F, Ln = fronts(W, D)[0]
    if rng.random() < 0.6:
        u = Ln / 2 - 1.2 * rng.uniform(0.8, 1.6); z0 = 5.4; hh = min(9.0, h - 6.0)
        if hh > 3.0:
            cell = int(rng.integers(8)); G = __import__('isle_houses').Frame(F.w(u, 0.0, 0), F.n, -F.u)     # blade faces along the street
            K.obj(G.box(0.15, 1.35, -0.18, 0.18, z0, z0 + hh), M['smooth'], (0.12, 0.12, 0.13), 'box', 1.0)
            for sgn in (1, -1):
                Gs = __import__('isle_houses').Frame(F.w(u, 0.0, 0), F.n * sgn, -F.u * sgn) if sgn > 0 else __import__('isle_houses').Frame(F.w(u, 0.0, 0), -F.n, F.u)
            for nn in (0.19, -0.19):
                K.obj(G.box(0.25, 1.25, nn - 0.01, nn + 0.01, z0 + 0.15, z0 + hh - 0.15), M['neon'], (1, 1, 1), 'sign', 1.0, sign=P.ad_uv_frame(G, cell, 0.75, z0 + hh / 2, 1.0, hh - 0.3) if nn > 0 else _ad_back(G, cell, z0, hh))
            for z in (z0 + 0.6, z0 + hh - 0.6): K.obj(F.box(u - 0.06, u + 0.06, 0.0, 0.2, z - 0.05, z + 0.05), M['galv'], (0.5, 0.5, 0.5))
    if rng.random() < 0.35 and h > 12:
        bw = min(12.0, Ln * 0.5); bh = bw * 0.42; cx = rng.uniform(-Ln / 2 + bw / 2 + 1, Ln / 2 - bw / 2 - 1); zb = h + 1.5
        Fb = __import__('isle_houses').Frame(F.w(0, -1.5, 0), F.u, F.n)
        for u in (cx - bw * 0.35, cx + bw * 0.35):
            K.obj(Fb.box(u - 0.1, u + 0.1, -1.6, -1.4, zb - 1.5, zb + bh), M['galv'], (0.45, 0.47, 0.5))
            K.obj(P.sweep([tuple(Fb.w(u, -1.5, zb + bh * 0.7)), tuple(Fb.w(u, -3.2, zb - 1.4))], 0.05, 6), M['galv'], (0.45, 0.47, 0.5))
        K.obj(Fb.box(cx - bw / 2 - 0.15, cx + bw / 2 + 0.15, -1.25, -1.1, zb - 0.15, zb + bh + 0.15), M['smooth'], (0.15, 0.15, 0.16))
        K.obj(Fb.box(cx - bw / 2, cx + bw / 2, -1.1, -1.05, zb, zb + bh), M['ads'], (1, 1, 1), 'sign', 1.0, sign=P.ad_uv_frame(Fb, int(rng.integers(8)), cx, zb + bh / 2, bw, bh))
        for u in np.linspace(cx - bw / 2 + 0.6, cx + bw / 2 - 0.6, 4): K.obj(P.sweep([tuple(Fb.w(u, -1.05, zb + bh + 0.1)), tuple(Fb.w(u, -0.4, zb + bh + 0.4))], 0.04, 5), M['iron'], (0.2, 0.2, 0.2))


def utilities(K, M, W, D, h, rng):
    """Drainpipes at the front corners and window air-conditioning units on the side and rear walls."""
    F, Ln = fronts(W, D)[0]
    for s in (-1, 1):
        u = s * (Ln / 2 - 0.35)
        K.obj(P.sweep([tuple(F.w(u, 0.18, 0.3)), tuple(F.w(u, 0.18, h + 0.2)), tuple(F.w(u, -0.3, h + 0.5))], 0.06, 8), M['galv'], (0.42, 0.44, 0.46))
        for z in np.arange(3.0, h, 3.2): K.obj(F.box(u - 0.09, u + 0.09, 0.0, 0.2, z, z + 0.06), M['galv'], (0.4, 0.4, 0.42))
    for F, Ln in fronts(W, D)[1:]:
        for _ in range(int(rng.integers(2, 7))):
            u = rng.uniform(-Ln / 2 + 2, Ln / 2 - 2); z = 4.0 + 3.3 * int(rng.integers(0, max(1, int((h - 5) / 3.3))))
            K.obj(F.box(u - 0.4, u + 0.4, 0.0, 0.5, z, z + 0.55), M['smooth'], (0.86, 0.86, 0.84), 'box', 1.0, 0.02, 1)
            K.obj(F.box(u - 0.3, u + 0.3, 0.5, 0.52, z + 0.08, z + 0.47), M['iron'], (0.25, 0.25, 0.27))
            K.obj(F.box(u - 0.42, u - 0.32, 0.0, 0.45, z - 0.12, z), M['galv'], (0.4, 0.4, 0.42))


def _ad_back(G, cell, z0, hh):
    import isle_houses as HS
    Gb = HS.Frame(G.o, -G.u, -G.n)
    return P.ad_uv_frame(Gb, cell, -0.75, z0 + hh / 2, 1.0, hh - 0.3)

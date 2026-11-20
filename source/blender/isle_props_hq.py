"""Aurelia street furniture family (art sheet 03): cast iron in Marina green with brass details for the old town,
plus a few modern pieces. Each prop is modelled facing +X at the origin, standing on z = 0, like the rest of the kit."""
import math
import numpy as np
import bmesh
import isle_props as P
from isle_props import bbox, lathe, sweep, prism

GREEN = (0.012, 0.045, 0.03); GREEN2 = (0.02, 0.06, 0.04); BRASS = (0.78, 0.6, 0.28); IRON = (0.07, 0.07, 0.075)
STONE = (0.88, 0.85, 0.79); WOOD = (0.62, 0.42, 0.26); GLASSW = (0.95, 0.93, 0.85)
SCOOT = (0.93, 0.93, 0.9)                      # scooter paint: tinted per instance


def ring(K, M, r, z, t, col=BRASS, mat='galv', seg=24, x=0, y=0):
    K.obj(lathe([(r - t, z), (r, z + t * 0.3), (r, z + t), (r - t, z + t * 1.3)], seg, x, y, 0), M[mat], col, 'cyl', 1.0)


def lantern(K, M, x, y, z, s=1.0):
    """Hexagonal glass lantern with a domed cap, finial and a bottom bowl."""
    K.obj(lathe([(0.0, 0.0), (0.09 * s, 0.0), (0.12 * s, 0.06 * s), (0.17 * s, 0.1 * s)], 6, x, y, z), M['smooth'], GREEN, 'cyl', 1.0)
    K.obj(lathe([(0.17 * s, 0.1 * s), (0.22 * s, 0.48 * s), (0.0, 0.48 * s)], 6, x, y, z, close_bottom=False), M['lens'], GLASSW, 'cyl', 1.0)
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        K.obj(sweep([(x + 0.17 * s * math.cos(a), y + 0.17 * s * math.sin(a), z + 0.1 * s), (x + 0.225 * s * math.cos(a), y + 0.225 * s * math.sin(a), z + 0.5 * s)], 0.012 * s, 4), M['smooth'], GREEN)
    K.obj(lathe([(0.27 * s, 0.48 * s), (0.27 * s, 0.53 * s), (0.18 * s, 0.62 * s), (0.06 * s, 0.7 * s), (0.04 * s, 0.78 * s), (0.0, 0.84 * s)], 6, x, y, z), M['smooth'], GREEN, 'cyl', 1.0)
    K.obj(lathe([(0.0, 0.84 * s), (0.035 * s, 0.86 * s), (0.0, 0.95 * s)], 8, x, y, z), M['galv'], BRASS)


def lamp_heritage(K, M):
    """Fluted cast-iron column on a moulded base, scroll double arm, two lanterns."""
    K.obj(lathe([(0.0, 0.0), (0.32, 0.0), (0.32, 0.12), (0.26, 0.2), (0.26, 0.55), (0.2, 0.62), (0.2, 0.9), (0.15, 1.0), (0.0, 1.0)], 8, 0, 0, 0), M['smooth'], GREEN, 'cyl', 1.0, 0.0)
    ring(K, M, 0.27, 0.56, 0.05)
    shaft = lathe([(0.11, 0.98), (0.09, 3.2), (0.075, 4.2)], 16, 0, 0, 0, close_bottom=False, close_top=False)
    K.obj(shaft, M['smooth'], GREEN, 'cyl', 1.0)
    for k in range(8):                                                                              # flutes
        a = k * math.pi / 4; c, s = math.cos(a), math.sin(a)
        K.obj(sweep([(0.1 * c, 0.1 * s, 1.05), (0.083 * c, 0.083 * s, 3.1)], 0.018, 4), M['smooth'], GREEN2)
    K.obj(lathe([(0.075, 4.2), (0.14, 4.3), (0.14, 4.38), (0.08, 4.45), (0.06, 4.6)], 12, 0, 0, 0), M['smooth'], GREEN, 'cyl', 1.0)
    ring(K, M, 0.12, 4.22, 0.04)
    for sg in (-1, 1):                                                                              # scroll arms
        pts = [(0, 0, 4.5)]
        for t in np.linspace(0, 1, 9): pts.append((sg * (0.08 + 0.72 * t), 0, 4.5 + 0.38 * math.sin(t * math.pi * 0.9) + 0.08 * t))
        K.obj(sweep(pts, 0.035, 6), M['smooth'], GREEN)
        cx = sg * 0.42; cz = 4.38
        sc = [(cx + 0.14 * math.cos(a) * sg, 0, cz + 0.14 * math.sin(a)) for a in np.linspace(0.3, 5.2, 16)]
        K.obj(sweep(sc, 0.018, 5), M['smooth'], GREEN)
        K.obj(sweep([(sg * 0.8, 0, 4.96), (sg * 0.8, 0, 4.86)], 0.03, 6), M['smooth'], GREEN)
        lantern(K, M, sg * 0.8, 0, 4.86 - 0.9, 1.0) if False else lantern(K, M, sg * 0.8, 0, 3.98, 1.0)
    lantern(K, M, 0, 0, 4.6, 0.85)


def litter_bin_hq(K, M):
    K.obj(lathe([(0.0, 0.0), (0.26, 0.0), (0.26, 0.06), (0.22, 0.1), (0.24, 0.8), (0.27, 0.84), (0.27, 0.9), (0.0, 0.9)], 20, 0, 0, 0), M['smooth'], GREEN, 'cyl', 1.0)
    for k in range(16):
        a = k * math.pi / 8; c, s = math.cos(a), math.sin(a)
        K.obj(sweep([(0.235 * c, 0.235 * s, 0.14), (0.245 * c, 0.245 * s, 0.76)], 0.016, 4), M['smooth'], GREEN2)
    ring(K, M, 0.245, 0.62, 0.035); ring(K, M, 0.245, 0.24, 0.035)
    K.obj(lathe([(0.27, 0.9), (0.24, 0.98), (0.12, 1.04), (0.06, 1.08), (0.0, 1.12)], 20, 0, 0, 0), M['smooth'], GREEN, 'cyl', 1.0)
    K.obj(bbox(0.2, 0, 0.98, 0.14, 0.3, 0.1), M['iron'], IRON)                                        # flap opening
    K.obj(lathe([(0.0, 1.12), (0.03, 1.13), (0.0, 1.18)], 8, 0, 0, 0), M['galv'], BRASS)


def bollard_hq(K, M):
    K.obj(lathe([(0.0, 0.0), (0.13, 0.0), (0.13, 0.08), (0.1, 0.14), (0.085, 0.7), (0.1, 0.76), (0.1, 0.82), (0.07, 0.88), (0.0, 0.98)], 16, 0, 0, 0), M['smooth'], GREEN, 'cyl', 1.0)
    ring(K, M, 0.095, 0.62, 0.03)


def bench_hq(K, M):
    for y in (-0.85, 0.85):                                                                         # cast-iron scrolled ends
        ys = [y - 0.03, y + 0.03]
        prof = [(0.3, 0.0), (0.22, 0.42), (-0.05, 0.42), (-0.22, 0.85), (-0.28, 0.88)]
        K.obj(sweep([(x, y, z) for x, z in prof], 0.03, 6), M['smooth'], GREEN)
        K.obj(sweep([(-0.22, y, 0.0), (-0.12, y, 0.42)], 0.03, 6), M['smooth'], GREEN)
        arm = [(0.3, y, 0.42)] + [(0.28 + 0.08 * math.cos(a), y, 0.64 + 0.08 * math.sin(a)) for a in np.linspace(-1.2, 3.6, 10)]
        K.obj(sweep([(0.22, y, 0.42), (0.26, y, 0.62)], 0.025, 5), M['smooth'], GREEN); K.obj(sweep(arm, 0.02, 5), M['smooth'], GREEN)
        K.obj(sweep([(0.26, y, 0.66), (-0.05, y, 0.66)], 0.022, 5), M['smooth'], GREEN)
    for k in range(5): K.obj(bbox(0.22 - k * 0.075, 0, 0.44, 0.06, 1.9, 0.035), M['wood'], WOOD, 'box', 1.0, 0.008, 1)
    for k in range(4):
        t = k / 3; K.obj(bbox(-0.08 - 0.13 * t, 0, 0.55 + 0.27 * t, 0.035, 1.9, 0.07, 0), M['wood'], WOOD, 'box', 1.0, 0.008, 1)


def bus_shelter_hq(K, M):
    """Steel-and-glass shelter: green frame, curved glass roof, lit advert panel, bench and a route post."""
    L_, D_ = 4.2, 1.6
    for (x, y) in ((-D_ / 2, -L_ / 2), (-D_ / 2, L_ / 2), (D_ / 2 - 0.1, -L_ / 2), (D_ / 2 - 0.1, L_ / 2), (-D_ / 2, 0)):
        K.obj(bbox(x, y, 1.25, 0.08, 0.08, 2.5), M['smooth'], GREEN)
    roof = []
    for k in range(9):
        t = k / 8; x = -D_ / 2 - 0.2 + (D_ + 0.6) * t; z = 2.5 + 0.18 * math.sin(t * math.pi)
        roof.append((x, z))
    rb = prism([(x, z) for x, z in roof] + [(x, z + 0.04) for x, z in reversed(roof)], -L_ / 2 - 0.15, L_ / 2 + 0.15, axis='x')
    for v in rb.verts: X_, U_, Z_ = v.co; v.co = (U_, X_, Z_)
    K.obj(rb, M['glass'], (0.85, 0.92, 0.95))
    K.obj(bbox(0.0, -L_ / 2 - 0.15, 2.5, D_ + 0.6, 0.08, 0.16), M['smooth'], GREEN); K.obj(bbox(0.0, L_ / 2 + 0.15, 2.5, D_ + 0.6, 0.08, 0.16), M['smooth'], GREEN)
    K.obj(bbox(-D_ / 2, 0, 1.3, 0.02, L_ - 0.1, 2.2), M['glass'], (0.85, 0.92, 0.95))                  # back glass
    K.obj(bbox(0.0, -L_ / 2, 1.3, D_ - 0.2, 0.02, 2.2), M['glass'], (0.85, 0.92, 0.95))
    K.obj(bbox(0.0, L_ / 2, 1.35, D_ - 0.1, 0.12, 2.3), M['smooth'], GREEN)                             # advert box
    K.obj(bbox(0.0, L_ / 2 - 0.07, 1.35, D_ - 0.3, 0.02, 2.0), M['ads'], (1, 1, 1), 'sign', 1.0, sign=P.ad_uv_frame(__import__('isle_houses').Frame((0, L_ / 2 - 0.08, 0), (1, 0, 0), (0, -1, 0)), 2, 0.0, 1.35, D_ - 0.3, 2.0))
    for k in range(4): K.obj(bbox(-D_ / 2 + 0.25, -1.4 + k * 0.38, 0.47, 0.3, 0.33, 0.04), M['galv'], (0.75, 0.77, 0.8))   # perch seats
    K.obj(bbox(-D_ / 2 + 0.3, 0, 0.4, 0.06, 1.6, 0.06), M['smooth'], GREEN)
    K.obj(bbox(D_ / 2 + 0.6, -L_ / 2 - 0.6, 1.6, 0.08, 0.08, 3.2), M['smooth'], GREEN)                    # route post with sign
    K.obj(bbox(D_ / 2 + 0.6, -L_ / 2 - 0.6, 3.0, 0.06, 0.5, 0.5), M['smooth'], (0.12, 0.3, 0.6))
    K.obj(bbox(D_ / 2 + 0.63, -L_ / 2 - 0.6, 3.0, 0.02, 0.36, 0.36), M['smooth'], (0.95, 0.95, 0.95))


def kiosk_hq(K, M):
    """Octagonal news kiosk: green panels, magazine racks behind glass, a domed roof with a finial and a name band."""
    r = 1.1
    K.obj(lathe([(0.0, 0.0), (r + 0.05, 0.0), (r + 0.05, 0.15), (r, 0.18)], 8, 0, 0, 0, a0=math.pi / 8, a1=math.pi / 8 + 2 * math.pi), M['stone'], STONE, 'cyl', 1.0)
    K.obj(lathe([(r, 0.18), (r, 1.0), (r - 0.02, 1.02)], 8, 0, 0, 0, a0=math.pi / 8, a1=math.pi / 8 + 2 * math.pi, close_bottom=False), M['smooth'], GREEN, 'cyl', 1.0)
    K.obj(lathe([(r - 0.04, 1.02), (r - 0.04, 2.3)], 8, 0, 0, 0, a0=math.pi / 8, a1=math.pi / 8 + 2 * math.pi, close_bottom=False, close_top=False), M['winglass'], (1, 1, 1), 'cyl', 1.0)
    rng = np.random.default_rng(4)
    for k in range(8):                                                                              # magazine racks behind the glass
        a = k * math.pi / 4 + math.pi / 8; c, s = math.cos(a), math.sin(a)
        for row in range(3):
            for j in range(3):
                t = (j - 1) * 0.22; px, py = (r - 0.12) * c - t * s, (r - 0.12) * s + t * c
                K.obj(bbox(px, py, 1.25 + row * 0.33, 0.02, 0.18, 0.26, a), M['smooth'], tuple(rng.uniform(0.2, 0.95, 3)))
        K.obj(sweep([((r - 0.02) * math.cos(a - math.pi / 8), (r - 0.02) * math.sin(a - math.pi / 8), 1.0), ((r - 0.02) * math.cos(a - math.pi / 8), (r - 0.02) * math.sin(a - math.pi / 8), 2.3)], 0.03, 5), M['smooth'], GREEN)
    K.obj(lathe([(r + 0.12, 2.3), (r + 0.12, 2.62), (r + 0.18, 2.66)], 8, 0, 0, 0, a0=math.pi / 8, a1=math.pi / 8 + 2 * math.pi), M['smooth'], GREEN, 'cyl', 1.0)
    K.obj(lathe([(r + 0.18, 2.66), (r * 0.9, 2.95), (r * 0.55, 3.3), (0.12, 3.55), (0.0, 3.6)], 16, 0, 0, 0), M['smooth'], GREEN2, 'cyl', 1.0)
    K.obj(lathe([(0.0, 3.55), (0.06, 3.6), (0.0, 3.95)], 8, 0, 0, 0), M['galv'], BRASS)
    ring(K, M, r + 0.13, 2.62, 0.04, seg=8)
    import isle_houses as HS
    for k in range(8):                                                                              # name band
        a = k * math.pi / 4; F = HS.Frame((math.cos(a) * (r + 0.13), math.sin(a) * (r + 0.13), 0), (-math.sin(a), math.cos(a), 0), (math.cos(a), math.sin(a), 0))
        K.obj(F.box(-0.36, 0.36, 0.0, 0.01, 2.36, 2.58), M['shops'], (1, 1, 1), 'sign', 1.0, sign=P.sign_cell_uv_frame(F, 15, 0.0, 2.47, 0.72, 0.22))


def postbox_hq(K, M):
    K.obj(lathe([(0.0, 0.0), (0.26, 0.0), (0.26, 0.1), (0.22, 0.14), (0.22, 1.25), (0.26, 1.3), (0.26, 1.36), (0.2, 1.46), (0.08, 1.52), (0.0, 1.54)], 20, 0, 0, 0), M['smooth'], (0.82, 0.38, 0.0), 'cyl', 1.0)
    K.obj(bbox(0.21, 0, 1.12, 0.06, 0.24, 0.04), M['iron'], IRON); K.obj(bbox(0.215, 0, 0.75, 0.02, 0.22, 0.3), M['smooth'], (0.85, 0.62, 0.1))
    ring(K, M, 0.225, 1.25, 0.03)
    K.obj(lathe([(0.0, 1.52), (0.05, 1.56), (0.0, 1.62)], 8, 0, 0, 0), M['galv'], BRASS)


def planter_hq(K, M):
    K.obj(lathe([(0.0, 0.0), (0.3, 0.0), (0.3, 0.08), (0.18, 0.14), (0.16, 0.3), (0.3, 0.38), (0.62, 0.62), (0.72, 0.72), (0.72, 0.8), (0.64, 0.8), (0.0, 0.72)], 24, 0, 0, 0), M['stone'], STONE, 'cyl', 1.0)
    rng = np.random.default_rng(6)
    K.obj(lathe([(0.0, 0.7), (0.62, 0.74), (0.0, 0.78)], 16, 0, 0, 0), M['concrete'], (0.25, 0.18, 0.12))                    # soil
    far = bool(P.LOD); nl, cs = (36, 1.9) if far else (160, 1.0)                                       # far copy: fewer, larger clumps
    if far: K.obj(lathe([(0.0, 0.78), (0.3, 0.8), (0.37, 1.0), (0.36, 1.2), (0.25, 1.38), (0.0, 1.44)], 8, 0, 0, 0), M['plastic'], (0.04, 0.1, 0.025))
    for k in range(nl):                                                                              # boxwood ball made of leaf clumps
        u, v = rng.uniform(-1, 1), rng.uniform(0, 2 * math.pi); s_ = math.sqrt(1 - u * u)
        px, py, pz = 0.4 * s_ * math.cos(v), 0.4 * s_ * math.sin(v), 1.12 + 0.34 * u
        if pz < 0.8: continue
        g = rng.uniform(0.7, 1.15)
        K.obj(lathe([(0.0, -0.06 * cs), (0.05 * cs, -0.035 * cs), (0.065 * cs, 0.0), (0.05 * cs, 0.035 * cs), (0.0, 0.06 * cs)], 6, px, py, pz), M['plastic'], (0.05 * g, 0.13 * g, 0.03 * g))
    for k in range(0 if far else 26):
        a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(0.35, 0.66)
        c = [(0.9, 0.15, 0.25), (0.98, 0.78, 0.15), (0.98, 0.98, 0.95), (0.65, 0.3, 0.8), (1.0, 0.5, 0.2)][int(rng.integers(5))]
        K.obj(lathe([(0.0, 0.0), (0.06, 0.03), (0.0, 0.07)], 6, rr * math.cos(a), rr * math.sin(a), 0.78 + (0.66 - rr) * 0.5), M['smooth'], c)


def cafe_hq(K, M):
    """Bistro set: round marble-top table on a cast-iron foot, two rattan chairs, market umbrella with a valance."""
    K.obj(lathe([(0.0, 0.0), (0.28, 0.0), (0.25, 0.04), (0.04, 0.1), (0.035, 0.7), (0.05, 0.72)], 16, 0, 0, 0), M['smooth'], IRON, 'cyl', 1.0)
    K.obj(lathe([(0.0, 0.72), (0.34, 0.72), (0.34, 0.76), (0.0, 0.76)], 24, 0, 0, 0), M['stone'], (0.95, 0.94, 0.92), 'cyl', 1.0)
    for a in (0.0, math.pi):
        cx, cy = 0.62 * math.cos(a), 0.62 * math.sin(a); ca, sa = math.cos(a), math.sin(a)
        K.obj(lathe([(0.0, 0.44), (0.22, 0.44), (0.22, 0.49), (0.0, 0.49)], 14, cx, cy, 0), M['wood'], (0.72, 0.56, 0.36), 'cyl', 1.0)
        for (dx, dy) in ((0.15, 0.15), (0.15, -0.15), (-0.15, 0.15), (-0.15, -0.15)): K.obj(sweep([(cx + dx, cy + dy, 0.0), (cx + dx * 0.9, cy + dy * 0.9, 0.45)], 0.015, 4), M['wood'], (0.55, 0.4, 0.25))
        back = [(cx + ca * 0.2 + sa * 0.2 * math.cos(t), cy + sa * 0.2 - ca * 0.2 * math.cos(t), 0.5 + 0.38 * math.sin(t)) for t in np.linspace(0, math.pi, 12)]
        K.obj(sweep(back, 0.02, 5), M['wood'], (0.72, 0.56, 0.36))
        for t in np.linspace(0.3, 2.8, 5): K.obj(sweep([(cx + ca * 0.2 + sa * 0.2 * math.cos(t), cy + sa * 0.2 - ca * 0.2 * math.cos(t), 0.5), (cx + ca * 0.2 + sa * 0.2 * math.cos(t), cy + sa * 0.2 - ca * 0.2 * math.cos(t), 0.5 + 0.38 * math.sin(t))], 0.008, 4), M['wood'], (0.66, 0.5, 0.32))
    K.obj(lathe([(0.025, 0.76), (0.025, 2.5), (0.0, 2.52)], 8, 0, 0, 0), M['wood'], (0.5, 0.36, 0.22), 'cyl', 1.0)
    K.obj(lathe([(1.45, 2.05), (0.6, 2.38), (0.05, 2.5), (0.0, 2.5)], 8, 0, 0, 0), M['fabric'], (0.92, 0.9, 0.84), 'cyl', 1.0, smooth=False)
    for k in range(8):
        a0, a1 = k * math.pi / 4, (k + 1) * math.pi / 4
        val = prism([(0, 0), (0, -0.18), (0.01, -0.18), (0.01, 0)], 0, 1, axis='x')
        p0 = np.array([1.45 * math.cos(a0), 1.45 * math.sin(a0)]); p1 = np.array([1.45 * math.cos(a1), 1.45 * math.sin(a1)])
        for v in val.verts:
            t, u, z = v.co; q = p0 + (p1 - p0) * t; v.co = (q[0], q[1], 2.05 + z)
        K.obj(val, M['fabric'], (0.12, 0.24, 0.18), 'box', 1.0)
    K.obj(lathe([(0.0, 2.5), (0.04, 2.52), (0.0, 2.62)], 8, 0, 0, 0), M['galv'], BRASS)


def scooter_hq(K, M):
    """Retro step-through scooter: curved leg shield, rounded rear body, saddle, round headlight, chrome trim."""
    def disc(x, r, w):
        bm = lathe([(0.0, -w), (r * 0.62, -w), (r, -w * 0.6), (r, w * 0.6), (r * 0.62, w), (0.0, w)], 18)
        for v in bm.verts: a, b, c = v.co; v.co = (x + a, c, 0.0 + b)
        return bm
    for x, r in ((0.62, 0.2), (-0.58, 0.2)):
        t = lathe([(0.0, -0.06), (0.14, -0.065), (0.2, -0.05), (0.2, 0.05), (0.14, 0.065), (0.0, 0.06)], 18)
        for v in t.verts: a, b, c = v.co; v.co = (x + a, c, 0.2 + b)
        K.obj(t, M['plastic'], (0.06, 0.06, 0.06), 'box', 0.5)
        h = lathe([(0.0, -0.07), (0.1, -0.07), (0.1, 0.07), (0.0, 0.07)], 12)
        for v in h.verts: a, b, c = v.co; v.co = (x + a, c, 0.2 + b)
        K.obj(h, M['galv'], (0.8, 0.8, 0.82))
    body = [(-0.85, 0.32), (-0.8, 0.55), (-0.55, 0.72), (-0.2, 0.74), (0.05, 0.62), (0.05, 0.38), (-0.2, 0.32)]
    bm = prism(body, -0.2, 0.2, axis='x')
    for v in bm.verts: X_, U_, Z_ = v.co; v.co = (U_, X_ * (0.7 + 0.3 * min(1, max(0, (Z_ - 0.32) / 0.4))), Z_)
    K.obj(bm, M['smooth'], SCOOT, 'box', 1.0, 0.05, 2)
    K.obj(bbox(0.25, 0, 0.3, 0.6, 0.32, 0.06), M['smooth'], SCOOT, 'box', 1.0, 0.02, 1)          # floorboard
    sh = prism([(0.5, 0.3), (0.62, 0.3), (0.66, 1.05), (0.58, 1.08), (0.5, 0.9)], -0.22, 0.22, axis='x')
    for v in sh.verts: X_, U_, Z_ = v.co; v.co = (U_, X_ * (1 - 0.25 * (Z_ - 0.3)), Z_)
    K.obj(sh, M['smooth'], SCOOT, 'box', 1.0, 0.03, 2)
    K.obj(sweep([(0.62, 0, 0.25), (0.66, 0, 0.75), (0.66, 0, 1.1)], 0.03, 6), M['galv'], (0.8, 0.8, 0.82))
    K.obj(bbox(0.66, 0, 1.12, 0.08, 0.66, 0.04), M['galv'], (0.8, 0.8, 0.82))
    hl = lathe([(0.0, 0.0), (0.08, 0.0), (0.09, 0.05), (0.0, 0.07)], 12)
    for v in hl.verts: a, b, c = v.co; v.co = (0.72 + c, a, 1.14 + b * 1.0 - 0.0)
    K.obj(lathe([(0.0, 0.0), (0.085, 0.0), (0.085, 0.08), (0.0, 0.1)], 12, 0.7, 0, 1.08), M['smooth'], SCOOT)
    K.obj(bbox(0.79, 0, 1.12, 0.02, 0.12, 0.12), M['lens'], (1.0, 0.96, 0.85))
    K.obj(bbox(-0.35, 0, 0.8, 0.62, 0.3, 0.1), M['plastic'], (0.35, 0.2, 0.12), 'box', 1.0, 0.03, 2)         # saddle
    K.obj(bbox(-0.86, 0, 0.62, 0.04, 0.12, 0.06), M['lens'], (0.8, 0.08, 0.05))
    K.obj(sweep([(-0.65, 0, 0.88), (-0.9, 0, 0.88)], 0.012, 5), M['galv'], (0.8, 0.8, 0.82))


def totem_hq(K, M):
    """City map totem: slim green frame, lit map panel both sides, Aurelia crest on top."""
    K.obj(bbox(0, 0, 1.1, 0.16, 0.9, 2.2), M['smooth'], GREEN, 'box', 1.0, 0.03, 2)
    import isle_houses as HS
    for sg in (1, -1):
        F = HS.Frame((sg * 0.081, 0, 0), (0, sg, 0), (sg, 0, 0))
        K.obj(F.box(-0.36, 0.36, 0.0, 0.005, 0.5, 1.95), M['smooth'], (0.93, 0.91, 0.84))                    # map panel: streets, park, sea
        K.obj(F.box(-0.36, 0.36, 0.005, 0.01, 0.5, 0.85), M['smooth'], (0.35, 0.6, 0.8))
        K.obj(F.box(-0.2, 0.05, 0.005, 0.01, 1.3, 1.6), M['smooth'], (0.5, 0.72, 0.42))
        for z in (1.05, 1.25, 1.7): K.obj(F.box(-0.33, 0.33, 0.01, 0.014, z, z + 0.03), M['smooth'], (0.98, 0.98, 0.98))
        for u in (-0.25, 0.1, 0.27): K.obj(F.box(u, u + 0.03, 0.01, 0.014, 0.88, 1.9), M['smooth'], (0.98, 0.98, 0.98))
        K.obj(F.box(0.12, 0.18, 0.014, 0.018, 1.36, 1.42), M['lens'], (0.9, 0.15, 0.1))                          # you are here
        K.obj(F.box(-0.36, 0.36, 0.005, 0.012, 1.95, 2.18), M['smooth'], (0.075, 0.16, 0.12))
    K.obj(bbox(0, 0, 2.28, 0.2, 0.96, 0.08), M['galv'], BRASS)
    K.obj(lathe([(0.0, 0.0), (0.16, 0.0), (0.16, 0.05), (0.0, 0.06)], 14, 0, 0, 2.32), M['galv'], BRASS)


def fountain_hq(K, M):
    """Cast-iron drinking fountain with a lion-head spout and stone basin."""
    K.obj(lathe([(0.0, 0.0), (0.4, 0.0), (0.4, 0.12), (0.34, 0.16)], 8, 0, 0, 0), M['stone'], STONE, 'cyl', 1.0)
    K.obj(lathe([(0.12, 0.16), (0.1, 0.95), (0.16, 1.05), (0.16, 1.12), (0.1, 1.2), (0.11, 1.45), (0.06, 1.55), (0.0, 1.62)], 12, 0, 0, 0), M['smooth'], GREEN, 'cyl', 1.0)
    K.obj(lathe([(0.0, 0.62), (0.32, 0.64), (0.36, 0.76), (0.3, 0.76), (0.0, 0.7)], 16, 0.25, 0, 0), M['stone'], STONE, 'cyl', 1.0)
    K.obj(lathe([(0.0, 0.0), (0.07, 0.02), (0.07, 0.08), (0.0, 0.1)], 10, 0.16, 0, 1.1), M['galv'], BRASS)
    K.obj(sweep([(0.2, 0, 1.13), (0.32, 0, 1.12), (0.34, 0, 1.06)], 0.012, 5), M['galv'], BRASS)
    ring(K, M, 0.12, 1.4, 0.03)


HQ = dict(lamp_city=(lamp_heritage, 5.6), bin=(litter_bin_hq, 1.2), bollard=(bollard_hq, 1.0), bench=(bench_hq, 0.9), shelter=(bus_shelter_hq, 3.2),
          kiosk=(kiosk_hq, 4.0), mailbox=(postbox_hq, 1.6), planter=(planter_hq, 1.4), cafe=(cafe_hq, 2.6), scooter=(scooter_hq, 1.2),
          phonebooth=(totem_hq, 2.4), fountain=(fountain_hq, 1.6))


def register():
    """Registered as <name>_hq next to the grey steel kit, which the modern core (glass towers) and the roads outside town keep."""
    for k, (fn, h) in HQ.items(): P.PROPS[k + '_hq'] = (fn, {}); P.HEIGHT[k + '_hq'] = h


def core(x, y):
    """Same downtown weight the city generator uses to place the glass towers."""
    return math.exp(-((x / 330) ** 2 + ((y + 20) / 240) ** 2))


def oldtown(x, y):
    """Old-town streets: inside the city but outside the glass-tower core."""
    return abs(x) < 720 and -360 < y < 360 and core(x, y) < 0.5


SWAP = ('bin', 'bench', 'shelter', 'kiosk', 'mailbox', 'planter', 'cafe', 'scooter', 'phonebooth', 'bollard', 'fountain')


def apply(KIT):
    """Swap kit placements in the old town for the art-sheet 03 family. Street lamps are swapped where they are placed (their light moves too)."""
    n = 0
    for i, it in enumerate(KIT):
        if it[0] in SWAP and oldtown(it[1], it[2]): KIT[i] = (it[0] + '_hq',) + tuple(it[1:]); n += 1
    return n

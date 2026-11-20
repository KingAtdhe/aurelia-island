"""Landmarks of Aurelia Island, modelled like the houses and props: village church, lighthouse, windmill tower, country fuel station,
stadium bowl and harbour quay furniture. Each builds into a Part in its own frame (front +X, origin on the ground) and is placed with
isle_arch.emit_model."""
import math
import numpy as np
import bmesh
import isle_props as P
from isle_props import bbox, lathe, sweep, prism, poly_round
from isle_houses import Frame, walls, gable_roof, door
from isle_city import fronts


def octa_spire(K, M, x, y, z0, r, h, col):
    K.obj(lathe([(r, 0.0), (r * 0.9, 0.25), (0.0, h)], 8, x, y, z0, close_bottom=True), M['roof'], col, 'roof', 1.2, 0.0, smooth=False)
    K.obj(lathe([(0.06, 0), (0.06, 1.8), (0.0, 1.85)], 8, x, y, z0 + h - 0.1), M['iron'], (0.25, 0.22, 0.18))
    K.obj(bbox(x, y, z0 + h + 1.25, 0.08, 0.7, 0.08), M['iron'], (0.25, 0.22, 0.18))                          # cross arm


def church(K, M):
    W, D, h = 9.0, 16.0, 7.5; stone = (0.86, 0.82, 0.74)
    K.obj(bbox(0, 0, 0.15, D + 0.4, W + 0.4, 0.7), M['ashlar'], (0.8, 0.78, 0.74), 'box', 1.6)
    for k, (F, Ln) in enumerate(fronts(W, D)):
        holes = []
        if k >= 2:                                                                            # tall nave windows between buttresses
            for i in range(4): uc = -Ln / 2 + (i + 0.5) * Ln / 4; holes.append((uc - 0.55, uc + 0.55, 2.2, 6.0))
        if k == 1: holes.append((-1.0, 1.0, 3.0, 6.2))                                        # east window
        walls(K, M, F, Ln if k < 2 else Ln - 1.2, 0.5, h, holes, stone, 0.6, M['ashlar'], 'box', 1.8)
        for (a, b, c, d) in holes:
            uc = (a + b) / 2; K.obj(F.box(a, b, -0.45, -0.42, c, d), M['winglass'], (0.55, 0.62, 0.8))
            for zz in np.linspace(c + 0.6, d - 0.4, 4): K.obj(F.box(a, b, -0.42, -0.38, zz - 0.02, zz + 0.02), M['iron'], (0.2, 0.2, 0.2))
            K.obj(F.box(uc - 0.02, uc + 0.02, -0.42, -0.38, c, d), M['iron'], (0.2, 0.2, 0.2))
            arch = prism([(a - 0.12, d), (b + 0.12, d), (uc, d + 0.75)], -0.02, 0.12, axis='x')
            for v in arch.verts: u_, n_, z_ = v.co[1], v.co[0], v.co[2]; v.co = tuple(F.w(u_, n_, z_))
            K.obj(arch, M['stone'], (0.92, 0.9, 0.85), 'box', 1.2)                            # pointed hood over each window
            K.obj(F.box(a - 0.1, b + 0.1, -0.1, 0.12, c - 0.12, c), M['stone'], (0.92, 0.9, 0.85), 'box', 1.2)
        if k >= 2:
            for i in range(5):                                                                # stepped buttresses
                u = -Ln / 2 + 0.6 + i * (Ln - 1.2) / 4
                K.obj(F.box(u - 0.35, u + 0.35, 0.0, 0.9, 0.5, 4.5), M['ashlar'], stone, 'box', 1.6)
                K.obj(F.box(u - 0.3, u + 0.3, 0.0, 0.55, 4.5, 6.8), M['ashlar'], stone, 'box', 1.6)
    gable_roof(K, M, W, D, h, 5.2, (0.42, 0.44, 0.48), stone, 0.4, 0.2, 'x', None, M['ashlar'], 'box', 1.4)
    # tower at the west (+X) end
    tx = D / 2 + 2.7; T = 5.4; th = 21.0
    K.obj(bbox(tx, 0, th / 2 + 0.3, T, T, th), M['ashlar'], (0.84, 0.8, 0.72), 'box', 1.8)
    for z in (7.0, 14.0): K.obj(bbox(tx, 0, z, T + 0.25, T + 0.25, 0.3), M['stone'], (0.93, 0.9, 0.84), 'box', 1.4)
    for k in range(4):                                                                        # belfry louvres and clock faces
        a = k * math.pi / 2; c, s = math.cos(a), math.sin(a); F = Frame((tx + c * T / 2, s * T / 2, 0), (-s, c, 0), (c, s, 0))
        K.obj(F.box(-0.9, 0.9, -0.15, 0.02, 15.5, 19.2), M['planks'], (0.3, 0.25, 0.2), 'boxv', 1.0)
        for zz in np.linspace(15.8, 18.9, 8): K.obj(F.box(-0.85, 0.85, 0.0, 0.08, zz, zz + 0.12), M['pwood'], (0.35, 0.28, 0.22))
        arch = prism([(-1.05, 19.2), (1.05, 19.2), (0.0, 20.2)], 0.0, 0.1, axis='x')
        for v in arch.verts: u_, n_, z_ = v.co[1], v.co[0], v.co[2]; v.co = tuple(F.w(u_, n_, z_))
        K.obj(arch, M['stone'], (0.93, 0.9, 0.84), 'box', 1.2)
        cf = lathe([(0.0, 0.0), (0.95, 0.0), (1.05, 0.06), (1.05, 0.12), (0.0, 0.12)], 24)
        for v in cf.verts: x_, y_, z_ = v.co; p = F.w(x_, z_ + 0.02, 11.2 + y_); v.co = tuple(p)
        K.obj(cf, M['smooth'], (0.95, 0.94, 0.9))
        K.obj(F.box(-0.04, 0.04, 0.14, 0.18, 11.2, 11.95), M['iron'], (0.1, 0.1, 0.1)); K.obj(F.box(0.0, 0.55, 0.14, 0.18, 11.16, 11.24), M['iron'], (0.1, 0.1, 0.1))
    F = Frame((tx + T / 2, 0, 0), (0, 1, 0), (1, 0, 0))
    K.obj(F.box(-1.1, 1.1, -0.1, 0.05, 0.3, 3.3), M['planks'], (0.45, 0.28, 0.16), 'boxv', 1.2)                # west door
    arch = prism([(-1.4, 3.3), (1.4, 3.3), (0.0, 4.5)], 0.0, 0.15, axis='x')
    for v in arch.verts: u_, n_, z_ = v.co[1], v.co[0], v.co[2]; v.co = tuple(F.w(u_, n_, z_))
    K.obj(arch, M['stone'], (0.93, 0.9, 0.84), 'box', 1.2)
    for zz in (0.0, 0.18): K.obj(F.box(-1.8, 1.8, 0.0, 0.9 - zz * 2, zz, zz + 0.18), M['stone'], (0.88, 0.86, 0.82), 'box', 1.2)
    for k in range(4):                                                                        # pinnacles
        a = k * math.pi / 2 + math.pi / 4; px, py = tx + math.cos(a) * T * 0.62, math.sin(a) * T * 0.62
        K.obj(lathe([(0.3, 0), (0.3, 1.2), (0.0, 2.6)], 8, px, py, th + 0.3), M['ashlar'], (0.84, 0.8, 0.72), 'cyl', 1.0)
    octa_spire(K, M, tx, 0, th + 0.3, T * 0.55, 11.0, (0.42, 0.44, 0.48))
    # apse at the east (-X) end
    ap = lathe([(3.6, 0.5), (3.6, h)], 16, -D / 2, 0, 0, close_top=False, close_bottom=False, a0=math.pi / 2, a1=1.5 * math.pi)
    bmesh.ops.solidify(ap, geom=ap.faces[:], thickness=0.5); K.obj(ap, M['ashlar'], stone, 'box', 1.8)
    K.obj(lathe([(3.9, h), (0.0, h + 3.2)], 16, -D / 2, 0, 0, a0=math.pi / 2, a1=1.5 * math.pi), M['roof'], (0.42, 0.44, 0.48), 'roof', 1.4)


def lighthouse(K, M):
    prof = [(5.0, 0.0), (5.0, 1.2), (4.6, 1.5)] + [(4.4 - 1.5 * t, 1.5 + 28 * t) for t in np.linspace(0, 1, 8)]
    for k in range(5):                                                                        # tapered tower, red and white bands
        z0, z1 = 1.5 + 28 * k / 5, 1.5 + 28 * (k + 1) / 5; r0, r1 = 4.4 - 1.5 * k / 5, 4.4 - 1.5 * (k + 1) / 5
        K.obj(lathe([(r0, z0), (r1, z1)], 28, close_top=False, close_bottom=False), M['plaster'], (0.97, 0.96, 0.93) if k % 2 == 0 else (0.75, 0.12, 0.1), 'cyl', 2.4)
    K.obj(lathe([(5.2, 0.0), (5.2, 1.5), (4.5, 1.6), (0.0, 1.6)], 28), M['ashlar'], (0.78, 0.76, 0.72), 'cyl', 1.6)
    for k in range(6):                                                                        # small windows up the tower
        a = k * 2.1; z = 6 + k * 4; r = 4.4 - 1.5 * (z - 1.5) / 28
        K.obj(bbox(r * math.cos(a), r * math.sin(a), z, 0.3, 0.7, 1.1, a), M['winglass'], (1, 1, 1))
    zt = 29.5
    K.obj(lathe([(2.9, zt), (3.9, zt + 0.25), (3.9, zt + 0.55), (0.0, zt + 0.55)], 28), M['concrete'], (0.85, 0.85, 0.83), 'cyl', 1.5)   # gallery deck
    for a in np.linspace(0, 2 * np.pi, 36, endpoint=False): K.obj(bbox(3.8 * math.cos(a), 3.8 * math.sin(a), zt + 1.05, 0.05, 0.05, 1.0), M['iron'], (0.15, 0.15, 0.16))
    K.obj(lathe([(3.85, zt + 1.5), (3.85, zt + 1.58)], 28, close_top=False, close_bottom=False), M['iron'], (0.15, 0.15, 0.16))
    K.obj(lathe([(2.2, zt + 0.55), (2.2, zt + 1.4)], 16, close_top=False), M['iron'], (0.15, 0.15, 0.16))
    K.obj(lathe([(2.0, zt + 1.4), (2.0, zt + 4.2)], 16, close_top=False, close_bottom=False), M['winglass'], (1, 1, 1))     # lantern glazing
    for a in np.linspace(0, 2 * np.pi, 8, endpoint=False): K.obj(bbox(2.05 * math.cos(a), 2.05 * math.sin(a), zt + 2.8, 0.1, 0.1, 2.8, a), M['iron'], (0.12, 0.12, 0.13))
    K.obj(lathe([(0.45, zt + 1.6), (0.6, zt + 2.6), (0.45, zt + 3.6), (0.0, zt + 3.7)], 12), M['lens'], (1.0, 0.95, 0.75))           # the light
    K.obj(lathe([(2.4, zt + 4.2), (2.2, zt + 4.6), (1.2, zt + 5.4), (0.2, zt + 5.8), (0.0, zt + 5.8)], 16), M['paint'], (0.7, 0.1, 0.08), 'cyl', 1.2)
    K.obj(lathe([(0.25, zt + 5.8), (0.35, zt + 6.1), (0.0, zt + 6.45)], 10), M['galv'], (0.6, 0.6, 0.6))
    F = Frame((4.6, 0, 0), (0, 1, 0), (1, 0, 0)); K.obj(F.box(-0.6, 0.6, -0.1, 0.25, 1.6, 3.8), M['pwood'], (0.15, 0.3, 0.45))   # door
    K.obj(F.box(-0.9, 0.9, 0.0, 0.6, 3.8, 4.05), M['concrete'], (0.85, 0.85, 0.83))


def windmill_tower(K, M):
    prof = [(4.4, 0.0), (4.3, 1.0)] + [(4.2 - 1.4 * t, 1.0 + 15 * t) for t in np.linspace(0, 1, 6)]
    K.obj(lathe([(4.6, 0.0), (4.6, 1.0), (4.3, 1.1), (0.0, 1.1)], 24), M['ashlar'], (0.78, 0.76, 0.72), 'cyl', 1.6)
    K.obj(lathe(prof, 24, close_top=False, close_bottom=False), M['plaster'], (0.97, 0.95, 0.9), 'cyl', 2.4)
    K.obj(lathe([(3.0, 16.0), (3.2, 16.3), (3.2, 16.6), (0.0, 16.6)], 24), M['pwood'], (0.4, 0.3, 0.22))       # curb ring
    cap = lathe([(3.2, 16.6), (3.0, 18.0), (2.2, 19.6), (1.0, 20.4), (0.0, 20.6)], 16)
    for v in cap.verts: v.co.x *= 1.25                                                       # boat-shaped cap
    K.obj(cap, M['planks'], (0.55, 0.38, 0.26), 'cylv', 1.0)
    for k, z in enumerate((2.0, 7.0, 11.5)):
        a = k * 1.9 + 0.4; r = 4.2 - 1.4 * (z - 1) / 15
        K.obj(bbox(r * math.cos(a), r * math.sin(a), z + 0.6, 0.35, 0.8, 1.2, a), M['winglass'], (1, 1, 1))
        K.obj(bbox((r + 0.1) * math.cos(a), (r + 0.1) * math.sin(a), z, 0.4, 1.1, 0.12, a), M['stone'], (0.9, 0.88, 0.84))
    F = Frame((4.2, 0, 0), (0, 1, 0), (1, 0, 0)); K.obj(F.box(-0.7, 0.7, -0.15, 0.15, 1.1, 3.4), M['planks'], (0.45, 0.3, 0.18), 'boxv', 1.2)
    K.obj(F.box(-0.9, 0.9, 0.0, 0.3, 3.4, 3.7), M['stone'], (0.9, 0.88, 0.84))


def windmill_sails(K, M):
    """Four lattice sails on stocks, centred on the hub, in the x-z plane (the game spins them about local z)."""
    for k in range(4):
        a = k * math.pi / 2 + 0.3; d = np.array([math.cos(a), 0, math.sin(a)]); e = np.array([-d[2], 0, d[0]])
        K.obj(sweep([tuple(d * 0.4), tuple(d * 13.0)], 0.16, 6), M['planks'], (0.5, 0.36, 0.24), 'cylv', 1.0)
        for t in np.linspace(3.0, 12.8, 9):                                                    # bars
            p0 = d * t; p1 = d * t + e * 2.4; K.obj(sweep([tuple(p0), tuple(p1)], 0.04, 4), M['planks'], (0.75, 0.62, 0.48))
        for o in (0.0, 1.2, 2.4): K.obj(sweep([tuple(d * 3 + e * o), tuple(d * 12.8 + e * o)], 0.035, 4), M['planks'], (0.75, 0.62, 0.48))
        cl = bmesh.new(); q = [d * 3.2 + e * 0.1, d * 12.6 + e * 0.1, d * 12.6 + e * 2.3, d * 3.2 + e * 2.3]
        cl.faces.new([cl.verts.new(tuple(v + np.array([0, -0.05, 0]))) for v in q]); K.obj(cl, M['fabric'], (0.92, 0.88, 0.78), smooth=False)
        cl2 = bmesh.new(); cl2.faces.new([cl2.verts.new(tuple(v + np.array([0, -0.05, 0]))) for v in q[::-1]]); K.obj(cl2, M['fabric'], (0.92, 0.88, 0.78), smooth=False)
    K.obj(lathe([(0.5, -0.6), (0.6, 0.2), (0.0, 0.3)], 12), M['iron'], (0.2, 0.2, 0.2))


def fuel_station(K, M, rng):
    """Canopy over two pump islands (front of the forecourt at +X toward the road) and a glazed kiosk behind."""
    for a in (-5.0, 5.0):
        for b in (-3.0, 3.0): K.obj(bbox(b + 1.0, a, 2.6, 0.45, 0.45, 5.2), M['galv'], (0.85, 0.86, 0.88), 'box', 1.0, 0.02, 2)
    K.obj(bbox(1.0, 0, 5.55, 11.0, 19.0, 0.7), M['smooth'], (0.12, 0.42, 0.3), 'box', 3.0, 0.03, 2)           # canopy fascia
    K.obj(bbox(1.0, 0, 5.2, 10.6, 18.6, 0.04), M['smooth'], (0.95, 0.95, 0.93))
    for a in (-6.0, 0.0, 6.0):
        for b in (-1.5, 3.5): K.obj(bbox(b + 1.0, a, 5.17, 1.6, 0.8, 0.03), M['lens'], (1.0, 0.98, 0.92))       # downlights
    for a in (-5.0, 5.0):                                                                    # pump islands
        K.obj(bbox(1.0, a, 0.12, 7.0, 1.4, 0.24), M['concrete'], (0.85, 0.85, 0.83), 'box', 1.5, 0.02, 2)
        for b in (-1.8, 1.8):
            x = b + 1.0; K.obj(bbox(x, a, 1.1, 0.7, 1.0, 1.75), M['smooth'], (0.93, 0.93, 0.9), 'box', 1.0, 0.03, 2)
            K.obj(bbox(x, a, 1.75, 0.72, 1.02, 0.35), M['smooth'], (0.12, 0.42, 0.3), 'box', 1.0, 0.02, 1)
            for sg in (-1, 1):
                K.obj(bbox(x + sg * 0.36, a, 1.35, 0.02, 0.5, 0.35), M['winglass'], (1, 1, 1))
                K.obj(sweep([(x + sg * 0.37, a - 0.3, 1.3), (x + sg * 0.6, a - 0.3, 0.6), (x + sg * 0.5, a - 0.3, 0.3)], 0.025, 5), M['iron'], (0.1, 0.1, 0.1))
                K.obj(bbox(x + sg * 0.4, a + 0.3, 1.05, 0.12, 0.08, 0.3), M['iron'], (0.1, 0.1, 0.1))
        for b in (-3.4, 3.4): K.obj(lathe([(0.1, 0), (0.1, 0.9), (0.0, 0.95)], 10, b + 1.0, a), M['paint'], (0.95, 0.75, 0.15))
    # kiosk
    kx = -9.5; KW, KD, kh = 16.0, 7.0, 4.2
    K.obj(bbox(kx, 0, 0.1, KD + 0.4, KW + 0.4, 0.2), M['concrete'], (0.8, 0.8, 0.78))
    for k, (F0, Ln) in enumerate(fronts(KW, KD)):
        F = Frame(F0.o + np.array([kx, 0, 0]), F0.u, F0.n); holes = []
        if k == 0: holes = [(-7.4, 7.4, 0.3, 3.0)]
        walls(K, M, F, Ln if k < 2 else Ln - 0.5, 0.2, kh, holes, (0.95, 0.95, 0.93), 0.25, M['concrete2'], 'box', 2.6)
        if k == 0:
            K.obj(F.box(-7.4, 7.4, -0.2, -0.18, 0.3, 3.0), M['winglass'], (1, 1, 1))
            for u in np.linspace(-7.4, 7.4, 8): K.obj(F.fin(u - 0.04, u + 0.04, -0.2, -0.1, 0.3, 3.0), M['galv'], (0.6, 0.62, 0.65), smooth=False)
            K.obj(F.box(-8.2, 8.2, 0.0, 0.25, kh - 0.9, kh + 0.3), M['smooth'], (0.12, 0.42, 0.3), 'box', 2.0)
            K.obj(F.box(-2.5, 2.5, 0.25, 0.27, kh - 0.75, kh + 0.15), M['shops'], (1, 1, 1), 'sign', 1.0, sign=P.sign_cell_uv_frame(F, 13, 0.0, kh - 0.3, 5.0, 0.9))
    K.obj(bbox(kx, 0, kh + 0.15, KD, KW, 0.3), M['concrete'], (0.6, 0.6, 0.6))
    # price totem
    F = Frame((6.5, -9.0, 0), (0, 1, 0), (1, 0, 0))
    K.obj(F.box(-0.8, 0.8, -0.3, 0.3, 0.0, 6.5), M['smooth'], (0.12, 0.42, 0.3), 'box', 2.0, 0.03, 2)
    for k, z in enumerate((3.4, 4.2, 5.0)): K.obj(F.box(-0.65, 0.65, 0.3, 0.32, z, z + 0.6), M['sign'], (1, 1, 1), 'sign', 1.0, sign=P.sign_cell_uv_frame(F, 14, 0.0, z + 0.3, 1.3, 0.6))
    K.obj(F.box(-0.7, 0.7, 0.3, 0.33, 5.75, 6.4), M['shops'], (1, 1, 1), 'sign', 1.0, sign=P.sign_cell_uv_frame(F, 13, 0.0, 6.07, 1.4, 0.65))


def stadium(K, M, a=105.0, b=84.0):
    """Oval bowl: outer facade with piers, stepped seating in coloured blocks, a cantilevered roof ring with ribs, four floodlight masts."""
    seg = 72; ang = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    def ring(prof, mat, col, uv='box', uvs=3.0, colf=None):
        bm = bmesh.new(); R = []
        for (k, z) in prof:
            R.append([bm.verts.new((a * k * math.cos(t), b * k * math.sin(t), z)) for t in ang])
        for r0, r1 in zip(R[:-1], R[1:]):
            for i in range(seg): bm.faces.new((r0[i], r0[(i + 1) % seg], r1[(i + 1) % seg], r1[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); K.obj(bm, mat, col, uv, uvs, smooth=False)
    ring([(1.0, -2.0), (1.0, 25.0)], M['concrete2'], (0.92, 0.92, 0.9), 'box', 4.0)
    for i in range(0, seg, 2):                                                               # facade piers
        t = ang[i]; K.obj(bbox(a * 1.012 * math.cos(t), b * 1.012 * math.sin(t), 12.5, 1.2, 1.6, 27.0, t), M['concrete'], (0.85, 0.85, 0.83), 'box', 3.0)
    for i in range(1, seg, 2):
        t = ang[i]; K.obj(bbox(a * 1.003 * math.cos(t), b * 1.003 * math.sin(t), 12.0, 0.2, 4.0, 18.0, t), M['winglass'], (1, 1, 1))
    steps = 26; prof = [(0.97, 23.0)]
    for s in range(steps):                                                                   # stepped seating, one tier per row
        k0 = 0.97 - (0.97 - 0.62) * s / steps; k1 = 0.97 - (0.97 - 0.62) * (s + 1) / steps; z = 23.0 - 21.5 * s / steps; z1 = 23.0 - 21.5 * (s + 1) / steps
        prof += [(k1 + 0.0001, z), (k1, z1)]
    bm = bmesh.new(); R = []
    for (k, z) in prof: R.append([bm.verts.new((a * k * math.cos(t), b * k * math.sin(t), z)) for t in ang])
    blocks = [(0.18, 0.36, 0.66), (0.75, 0.15, 0.12), (0.92, 0.92, 0.9), (0.18, 0.36, 0.66)]
    for j, (r0, r1) in enumerate(zip(R[:-1], R[1:])):
        for i in range(seg): bm.faces.new((r0[i], r0[(i + 1) % seg], r1[(i + 1) % seg], r1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.normal_update(); c = f.calc_center_median(); n = f.normal
        if abs(n.z) > 0.5: want = n.z > 0
        else: want = (n.x * -c.x / a / a + n.y * -c.y / b / b) > 0
        if not want: f.normal_flip()
    seats = bm; P_ = None
    for blk in range(4):                                                                     # split seats into coloured quarters
        b2 = seats.copy(); rm = [f for f in b2.faces if int(((math.atan2(f.calc_center_median().y / b, f.calc_center_median().x / a) + math.pi) / (math.pi / 6))) % 4 != blk]
        bmesh.ops.delete(b2, geom=rm, context='FACES'); K.obj(b2, M['plastic'], blocks[blk], 'box', 1.0, smooth=False)
    seats.free()
    ring([(0.6, 1.4), (0.6, 0.5), (0.0, 0.5)], M['concrete'], (0.7, 0.7, 0.68))
    pitch = bmesh.new(); pv = [pitch.verts.new((sx * 52.0, sy * 34.0, 0.62)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]; pitch.faces.new(pv)
    K.obj(pitch, M['plaster'], (0.36, 0.62, 0.3), 'box', 9.0, smooth=False)
    for k in range(-5, 6):
        st = bmesh.new(); sv = [st.verts.new((k * 9.4 + sx * 2.35, sy * 34.0, 0.63)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]; st.faces.new(sv)
        if k % 2 == 0: K.obj(st, M['plaster'], (0.42, 0.7, 0.34), 'box', 9.0, smooth=False)
    for (x0, y0, x1, y1) in ((-52, -34, 52, -33.85), (-52, 33.85, 52, 34), (-52, -34, -51.85, 34), (51.85, -34, 52, 34), (-0.08, -34, 0.08, 34)):
        ln = bmesh.new(); lv = [ln.verts.new(v) for v in ((x0, y0, 0.64), (x1, y0, 0.64), (x1, y1, 0.64), (x0, y1, 0.64))]; ln.faces.new(lv); K.obj(ln, M['smooth'], (0.95, 0.95, 0.95), smooth=False)
    ring([(1.03, 25.0), (1.05, 27.5), (0.78, 29.5), (0.74, 28.8), (1.0, 25.6)], M['galv'], (0.92, 0.93, 0.95), 'box', 4.0)   # roof ring
    for i in range(0, seg, 3):                                                               # roof ribs
        t = ang[i]; p0 = (a * 1.04 * math.cos(t), b * 1.04 * math.sin(t), 27.6); p1 = (a * 0.76 * math.cos(t), b * 0.76 * math.sin(t), 29.6)
        K.obj(sweep([p0, p1], 0.25, 6), M['galv'], (0.75, 0.77, 0.8))
    for k in range(4):                                                                       # floodlight masts
        t = k * math.pi / 2 + math.pi / 4; px, py = a * 1.05 * math.cos(t), b * 1.05 * math.sin(t)
        K.obj(lathe([(1.1, 0.0), (0.6, 50.0), (0.55, 52.0)], 12, px, py), M['galv'], (0.8, 0.82, 0.85), 'cyl', 3.0)
        F = Frame((px, py, 0), (-math.sin(t), math.cos(t), 0), (-math.cos(t), -math.sin(t), 0))
        K.obj(F.box(-3.6, 3.6, -0.6, 0.4, 50.0, 55.0), M['galv'], (0.6, 0.62, 0.65), 'box', 2.0)
        for i in range(4):
            for j in range(3): K.obj(F.box(-3.2 + i * 1.75, -1.9 + i * 1.75, 0.4, 0.45, 50.4 + j * 1.5, 51.6 + j * 1.5), M['lens'], (1.0, 0.98, 0.9))


def quay_furniture(K, M, length, n_bollards=8):
    """A row of cast-iron bollards, rubber fenders and ladders along a quay edge (edge along y at x = 0, water at +x)."""
    for i in range(n_bollards):
        y = -length / 2 + (i + 0.5) * length / n_bollards
        K.obj(lathe([(0.3, 0.0), (0.3, 0.1), (0.2, 0.15), (0.17, 0.55), (0.26, 0.62), (0.26, 0.72), (0.0, 0.75)], 14, -0.6, y), M['iron'], (0.2, 0.2, 0.22), 'cyl', 0.6)
        K.obj(bbox(0.08, y + length / n_bollards / 2, -1.0, 0.25, 0.9, 2.0), M['plastic'], (0.08, 0.08, 0.08))
        if i % 3 == 1:
            for sg in (-1, 1): K.obj(bbox(0.12, y + sg * 0.25, -1.8, 0.05, 0.05, 3.6), M['galv'], (0.6, 0.6, 0.6))
            for z in np.arange(-3.3, 0.0, 0.3): K.obj(bbox(0.12, y, z, 0.04, 0.5, 0.04), M['galv'], (0.6, 0.6, 0.6))


def container(K, M):
    """20/40 ft style shipping container 12.2 x 2.5 x 2.6 m: corrugated sides, corner posts and castings, end doors with locking bars."""
    L_, W_, H_ = 12.2, 2.5, 2.6
    K.obj(bbox(0, 0, H_ / 2, L_ - 0.2, W_ - 0.1, H_ - 0.1), M['corr'], (1, 1, 1), 'box', 0.9)
    for sx in (-1, 1):
        for sy in (-1, 1): K.obj(bbox(sx * (L_ / 2 - 0.1), sy * (W_ / 2 - 0.08), H_ / 2, 0.2, 0.16, H_), M['galv'], (0.85, 0.85, 0.85))
    for z in (0.08, H_ - 0.08):
        for sy in (-1, 1): K.obj(bbox(0, sy * (W_ / 2 - 0.05), z, L_, 0.12, 0.16), M['galv'], (0.85, 0.85, 0.85))
    for y in (-0.6, -0.2, 0.2, 0.6): K.obj(lathe([(0.03, 0.15), (0.03, H_ - 0.15)], 6, L_ / 2 + 0.03, y), M['galv'], (0.7, 0.7, 0.7))
    K.obj(bbox(L_ / 2 + 0.005, 0, H_ / 2, 0.01, 0.02, H_ - 0.3), M['iron'], (0.2, 0.2, 0.2))

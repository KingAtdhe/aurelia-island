"""Art sheet 09: Aurelia landmarks, rebuilt to hero quality. Same frames and footprints as isle_landmarks (front +X, origin on the ground)
so each swaps in where the old one stands: village church, lighthouse with keeper's cottage, Mediterranean tower windmill (sails apart, they
spin), country fuel station and the stadium."""
import math
import numpy as np
import bmesh
import isle_props as P
from isle_props import bbox, lathe, sweep, prism
from isle_houses import Frame, walls, gable_roof
from isle_city import fronts

STONE = (1.0, 0.76, 0.5); TRIM = (1.0, 0.95, 0.84); TERRA = (0.85, 0.36, 0.18); WHITE = (0.95, 0.94, 0.91); IRON = (0.12, 0.12, 0.13)


# ------------------------------------------------------------------ shared pieces
def _in_frame(bm, F):
    """bmesh built in (u, n, z) coordinates -> frame F."""
    for v in bm.verts: u, n, z = v.co; v.co = tuple(F.w(u, n, z))
    return bm


def arch_head(K, M, F, uc, zs, w, t, wallmat, wallcol, stonecol=TRIM, ring=0.32, seg=9, uvs=1.8):
    """Round head over an opening that the wall leaves open from zs to zs + w/2: spandrels in the wall plane, voussoir ring on the face."""
    r = w / 2; a = uc - r; b = uc + r
    arc = [(uc - r * math.cos(th), zs + r * math.sin(th)) for th in np.linspace(0, math.pi, 2 * seg + 1)]
    for half, corner in ((arc[:seg + 1], (a, zs + r)), (arc[seg:], (b, zs + r))):
        bm = bmesh.new(); cv = bm.verts.new((corner[0], -t, corner[1])); cf = bm.verts.new((corner[0], 0.0, corner[1]))
        back = [bm.verts.new((u, -t, z)) for u, z in half]; front = [bm.verts.new((u, 0.0, z)) for u, z in half]
        for i in range(len(half) - 1):
            bm.faces.new((cf, front[i], front[i + 1])); bm.faces.new((cv, back[i + 1], back[i])); bm.faces.new((front[i], back[i], back[i + 1], front[i + 1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); K.obj(_in_frame(bm, F), wallmat, wallcol, 'box', uvs, smooth=False)
    for i in range(seg * 2 if seg < 6 else seg):                                              # voussoirs
        n_ = seg if seg >= 6 else seg * 2; t0 = math.pi * i / n_; t1 = math.pi * (i + 1) / n_
        pts = [(uc - (r + dr) * math.cos(th), zs + (r + dr) * math.sin(th)) for dr, th in ((0, t0), (ring, t0), (ring, t1), (0, t1))]
        bm = prism([(u, z) for u, z in pts], 0.0, 0.07, axis='y') if False else _slab(pts, -0.02, 0.07)
        K.obj(_in_frame(bm, F), M['stone'], np.asarray(stonecol) * (0.94 + 0.08 * (i % 2)), 'box', 1.0, smooth=False)


def _slab(pts, n0, n1):
    """Prism from a (u, z) polygon between n0 and n1, in frame coordinates."""
    bm = bmesh.new(); A = [bm.verts.new((u, n0, z)) for u, z in pts]; B = [bm.verts.new((u, n1, z)) for u, z in pts]
    bm.faces.new(A[::-1]); bm.faces.new(B)
    for i in range(len(pts)): j = (i + 1) % len(pts); bm.faces.new((A[i], A[j], B[j], B[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return bm


def arched_window(K, M, F, uc, z0, w, hs, t, glass=True, frame=(0.2, 0.18, 0.16)):
    """Glazing (or a dark louvred void) inside a round-headed opening from z0 to hs + w/2; cill below."""
    r = w / 2; zs = z0 + hs
    prof = [(uc - r, z0), (uc + r, z0)] + [(uc + r * math.cos(th), zs + r * math.sin(th)) for th in np.linspace(0, math.pi, 13)]
    K.obj(_in_frame(_slab(prof, -t + 0.05, -t + 0.08), F), M['winglass'] if glass else M['smooth'], (1, 1, 1) if glass else (0.05, 0.05, 0.05), smooth=False)
    if glass:
        K.obj(F.box(uc - 0.025, uc + 0.025, -t + 0.08, -t + 0.12, z0, zs + r - 0.02), M['iron'], frame)
        for zz in np.arange(z0 + 0.45, zs + r * 0.8, 0.45):
            hw_ = r if zz < zs else math.sqrt(max(r * r - (zz - zs) ** 2, 0.0))
            K.obj(F.box(uc - hw_, uc + hw_, -t + 0.08, -t + 0.11, zz - 0.012, zz + 0.012), M['iron'], frame)
    K.obj(F.box(uc - r - 0.1, uc + r + 0.1, -0.08, 0.12, z0 - 0.14, z0), M['stone'], TRIM, 'box', 1.2, 0.01, 1)


def tile_roof_hip(K, M, cx, cy, z0, sx, sy, rise, col=TERRA, ov=0.4):
    """Pyramid / hipped tiled roof with ridge caps."""
    hx, hy = sx / 2 + ov, sy / 2 + ov; top = (cx, cy, z0 + rise)
    bm = bmesh.new(); C = [bm.verts.new((cx + a * hx, cy + b * hy, z0 - ov * 0.4)) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]; T = bm.verts.new(top)
    for i in range(4): bm.faces.new((C[i], C[(i + 1) % 4], T))
    K.obj(bm, M['roof'], col, 'roof', 1.4, smooth=False)
    for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)): K.obj(sweep([(cx + a * hx, cy + b * hy, z0 - ov * 0.4 + 0.08), (top[0], top[1], top[2] + 0.08)], 0.09, 6), M['roof'], np.asarray(col) * 0.82, 'cylv', 1.0)


def cross(K, M, x, y, z, h=1.6, col=(0.22, 0.2, 0.17)):
    K.obj(bbox(x, y, z + h / 2, 0.08, 0.08, h), M['iron'], col); K.obj(bbox(x, y, z + h * 0.68, 0.08, 0.75, 0.08), M['iron'], col)
    K.obj(lathe([(0.0, -0.12), (0.12, 0.0), (0.0, 0.12)], 10, x, y, z + 0.05), M['galv'], (0.75, 0.6, 0.3))


def cypress(K, M, x, y, z, h=9.0, col=(0.05, 0.13, 0.05)):
    K.obj(lathe([(0.15, 0.0), (0.15, 0.5), (0.55, 0.9), (0.85, h * 0.3), (0.7, h * 0.65), (0.3, h * 0.9), (0.0, h)], 10, x, y, z), M['concrete'], col, 'cyl', 0.8)


# ------------------------------------------------------------------ 1 church
def church_hq(K, M):
    """Romanesque village church: ashlar nave with round-headed windows and buttresses, gable west front with a rose window and a
    columned portal up three steps, semicircular apse, terracotta roofs, and a campanile with an open belfry, bell, clock and tiled spire."""
    W, D, h = 10.0, 18.0, 8.0; wall = STONE; wm = M['limestone'] if 'limestone' in M else M['ashlar']
    K.obj(bbox(0, 0, 0.2, D + 0.6, W + 0.6, 0.8), M['stone'], (0.78, 0.74, 0.66), 'box', 1.4, 0.03, 2)              # plinth course
    for k, (F, Ln) in enumerate(fronts(W, D)):
        holes = []
        if k >= 2:
            for i in range(4): uc = -Ln / 2 + 2.6 + i * (Ln - 5.2) / 3; holes.append((uc - 0.6, uc + 0.6, 3.4, 6.2 + 0.6))
        if k == 0: holes = [(-1.3, 1.3, 0.6, 3.6 + 1.3)]                                     # west portal
        walls(K, M, F, Ln if k < 2 else Ln - 1.0, 0.6, h, holes, wall, 0.7, wm, 'box', 1.8)
        for (a, b, c, d) in holes:
            uc = (a + b) / 2; w = b - a; zs = d - w / 2
            if k >= 2: arched_window(K, M, F, uc, c, w, zs - c, 0.7)
            arch_head(K, M, F, uc, zs, w, 0.7, wm, wall)
        if k >= 2:
            for i in range(5):                                                                 # pilaster buttresses
                u = -Ln / 2 + 0.5 + i * (Ln - 1.0) / 4
                K.obj(F.box(u - 0.4, u + 0.4, 0.0, 0.55, 0.6, h - 0.4), wm, wall, 'box', 1.8, 0.02, 2)
                K.obj(_in_frame(_slab([(u - 0.42, h - 0.4), (u + 0.42, h - 0.4), (u + 0.42, h - 0.1), (u - 0.42, h - 0.1)], 0.0, 0.62), F), M['stone'], TRIM, 'box', 1.2)
            for i in range(int(Ln / 0.55)):                                                    # corbel table under the eaves
                u = -Ln / 2 + 0.3 + i * 0.55; K.obj(F.box(u - 0.12, u + 0.12, 0.0, 0.22, h - 0.55, h - 0.25), M['stone'], TRIM)
    F = Frame((D / 2, 0, 0), (0, 1, 0), (1, 0, 0))                                             # west front details
    K.obj(F.box(-1.3, 1.3, -0.62, -0.55, 0.6, 3.6 + 1.3), M['planks'], (0.38, 0.22, 0.12), 'boxv', 1.0)          # doors
    for uu in (-0.65, 0.65):
        for zz in (1.2, 2.3, 3.3): K.obj(lathe([(0.0, -0.04), (0.05, 0.0), (0.0, 0.04)], 6, 0, 0, 0) if False else F.box(uu - 0.04, uu + 0.04, -0.55, -0.5, zz, zz + 0.08), M['iron'], IRON)
    for sg in (-1, 1):                                                                         # columns and capitals flanking the portal
        u = sg * 1.65; K.obj(_in_frame(lathe([(0.2, 0.0), (0.2, 0.2), (0.16, 0.3), (0.15, 3.5), (0.24, 3.65), (0.26, 3.85), (0.0, 3.85)], 12, u, 0.25, 0.6), F) if False else lathe([(0.2, 0.0), (0.2, 0.2), (0.16, 0.3), (0.15, 3.5), (0.24, 3.65), (0.26, 3.85), (0.0, 3.85)], 12, *F.w(u, 0.25, 0.6)[:2], 0.6), M['stone'], TRIM, 'cyl', 1.0)
    arch_head(K, M, F, 0.0, 3.6 + 0.3, 3.6, 0.01, wm, wall, ring=0.42, seg=11)                 # outer order of the portal arch
    for i in range(3): K.obj(F.box(-2.6 + i * 0.25, 2.6 - i * 0.25, 0.0, 1.6 - i * 0.5, i * 0.2, (i + 1) * 0.2), M['stone'], (0.86, 0.83, 0.77), 'box', 1.2, 0.01, 1)   # steps
    K.obj(F.box(-W / 2 - 0.1, W / 2 + 0.1, 0.0, 0.15, h - 0.1, h + 0.2), M['stone'], TRIM, 'box', 1.2)          # string course
    oc = lathe([(1.2, 0.0), (1.55, 0.0), (1.55, 0.3), (1.2, 0.3)], 32); ocg = lathe([(0.0, 0.05), (1.2, 0.05)], 32)
    for bm_, mat_, col_ in ((oc, M['stone'], TRIM), (ocg, M['lens'], (0.16, 0.24, 0.6))):
        for v in bm_.verts: x, y, z = v.co; v.co = tuple(F.w(x, z - 0.05, h + 1.95 + y))
        K.obj(bm_, mat_, col_, 'box', 1.0)
    for k in range(8):                                                                         # rose tracery
        a = k * math.pi / 4; K.obj(F.box(-0.03, 0.03, 0.0, 0.08, 0, 0) if False else _in_frame(_slab([(0.0, h + 1.95), (1.2 * math.cos(a) + 0.04 * math.sin(a), h + 1.95 + 1.2 * math.sin(a) - 0.04 * math.cos(a)), (1.2 * math.cos(a) - 0.04 * math.sin(a), h + 1.95 + 1.2 * math.sin(a) + 0.04 * math.cos(a))], 0.0, 0.1), F), M['stone'], TRIM)
    gable_roof(K, M, W, D, h + 0.2, 3.6, TERRA, wall, 0.5, 0.22, 'x', None, wm, 'box', 1.4)
    cross(K, M, D / 2 + 0.15, 0, h + 3.95, 1.8)
    # apse (-X)
    ap = lathe([(4.2, 0.6), (4.2, h - 1.0)], 20, -D / 2, 0, 0, close_top=False, close_bottom=False, a0=math.pi / 2, a1=1.5 * math.pi)
    bmesh.ops.solidify(ap, geom=ap.faces[:], thickness=0.6); K.obj(ap, wm, wall, 'box', 1.8)
    K.obj(lathe([(4.45, h - 1.0), (4.45, h - 0.75), (0.0, h - 0.75)], 20, -D / 2, 0, 0, a0=math.pi / 2, a1=1.5 * math.pi), M['stone'], TRIM)
    K.obj(lathe([(4.7, h - 0.75), (0.0, h + 1.6)], 20, -D / 2, 0, 0, a0=math.pi / 2, a1=1.5 * math.pi), M['roof'], TERRA, 'roof', 1.4)
    for a in (math.pi * 0.75, math.pi, math.pi * 1.25):
        Fa = Frame((-D / 2 + 4.2 * math.cos(a), 4.2 * math.sin(a), 0), (-math.sin(a), math.cos(a), 0), (math.cos(a), math.sin(a), 0))
        K.obj(Fa.box(-0.35, 0.35, -0.6, 0.02, 3.4, 5.6), M['winglass'], (1, 1, 1)); K.obj(Fa.box(-0.5, 0.5, 0.0, 0.1, 3.3, 3.42), M['stone'], TRIM)
    # campanile on the south-east corner (-X, -Y)
    tx, ty, T, th = -D / 2 + 3.2, -W / 2 - 2.6, 4.8, 22.0
    K.obj(bbox(tx, ty, th / 2, T, T, th), wm, (0.98, 0.84, 0.64), 'box', 1.8)
    for z in (6.5, 12.5, 16.0, th): K.obj(bbox(tx, ty, z, T + 0.3, T + 0.3, 0.32), M['stone'], TRIM, 'box', 1.2, 0.01, 1)
    for sx in (-1, 1):
        for sy in (-1, 1): K.obj(bbox(tx + sx * (T / 2 - 0.15), ty + sy * (T / 2 - 0.15), th / 2, 0.55, 0.55, th), wm, (1.0, 0.88, 0.7), 'box', 1.8)      # corner pilasters
    for k in range(4):
        a = k * math.pi / 2; c, s = math.cos(a), math.sin(a); Ft = Frame((tx + c * T / 2, ty + s * T / 2, 0), (-s, c, 0), (c, s, 0))
        for uu in (-0.75, 0.75):                                                               # paired belfry openings
            K.obj(Ft.box(uu - 0.5, uu + 0.5, -0.02, 0.01, 16.2, 19.6), M['smooth'], (0.04, 0.04, 0.04))
            arch_head(K, M, Ft, uu, 19.0, 1.0, 0.01, wm, (0.98, 0.84, 0.64), ring=0.2, seg=7)
        K.obj(lathe([(0.12, 16.2), (0.1, 18.8), (0.18, 19.0), (0.0, 19.0)], 8, *Ft.w(0.0, 0.1, 0)[:2]), M['stone'], TRIM)   # mullion column
        for zz in (8.5, 13.5): K.obj(Ft.box(-0.18, 0.18, -0.3, 0.01, zz, zz + 1.2), M['smooth'], (0.05, 0.05, 0.05))           # slit windows
        cf = lathe([(0.0, 0.0), (0.85, 0.0), (0.95, 0.05), (0.95, 0.1), (0.0, 0.1)], 24)                                    # clock
        for v in cf.verts: x_, y_, z_ = v.co; v.co = tuple(Ft.w(x_, z_ + 0.02, 14.4 + y_))
        K.obj(cf, M['smooth'], (0.93, 0.9, 0.82))
        for hh in range(12):
            ah = hh * math.pi / 6; K.obj(Ft.box(0.72 * math.sin(ah) - 0.03, 0.72 * math.sin(ah) + 0.03, 0.12, 0.14, 14.4 + 0.72 * math.cos(ah) - 0.06, 14.4 + 0.72 * math.cos(ah) + 0.06), M['iron'], IRON)
        K.obj(Ft.box(-0.03, 0.03, 0.14, 0.16, 14.4, 15.0), M['iron'], IRON); K.obj(Ft.box(0.0, 0.45, 0.14, 0.16, 14.37, 14.43), M['iron'], IRON)
    K.obj(lathe([(0.0, -0.8), (0.55, -0.75), (0.62, -0.1), (0.42, 0.25), (0.15, 0.35), (0.0, 0.36)], 16, tx, ty, 18.3), M['galv'], (0.55, 0.42, 0.22), 'cyl', 1.0)   # bell
    K.obj(bbox(tx, ty, 18.85, 0.2, T - 0.6, 0.25), M['planks'], (0.35, 0.25, 0.16))
    K.obj(bbox(tx, ty, th + 0.4, T + 0.5, T + 0.5, 0.5), M['stone'], TRIM, 'box', 1.2, 0.02, 2)
    tile_roof_hip(K, M, tx, ty, th + 0.65, T, T, 5.2, TERRA, 0.35)
    cross(K, M, tx, ty, th + 5.8, 1.9)
    # churchyard: low wall, cypresses, gravestones, gravel path to the portal
    yard = (-D / 2 - 5.0, D / 2 + 6.5, -W / 2 - 6.0, W / 2 + 4.0)
    for (x0, x1, y0, y1) in ((yard[0], yard[1], yard[2], yard[2] + 0.5), (yard[0], yard[1], yard[3] - 0.5, yard[3]), (yard[0], yard[0] + 0.5, yard[2], yard[3])):
        K.obj(bbox((x0 + x1) / 2, (y0 + y1) / 2, 0.55, x1 - x0, y1 - y0, 1.1), M['stone'], (0.8, 0.75, 0.66), 'box', 1.0, 0.03, 2)
        K.obj(bbox((x0 + x1) / 2, (y0 + y1) / 2, 1.15, x1 - x0 + 0.1, y1 - y0 + 0.1, 0.12), M['stone'], TRIM)
    for y0, y1 in ((yard[2], -1.8), (1.8, yard[3])):
        K.obj(bbox(yard[1] - 0.25, (y0 + y1) / 2, 0.55, 0.5, y1 - y0, 1.1), M['stone'], (0.8, 0.75, 0.66), 'box', 1.0, 0.03, 2)
        for yy in (-1.8, 1.8): K.obj(bbox(yard[1] - 0.25, yy, 0.8, 0.7, 0.7, 1.6), M['stone'], TRIM, 'box', 1.0, 0.02, 2)
    K.obj(bbox((D / 2 + yard[1]) / 2 + 0.4, 0, 0.02, yard[1] - D / 2 - 0.8, 2.6, 0.04), M['gravel'] if 'gravel' in M else M['concrete'], (0.78, 0.72, 0.62), 'box', 1.2)
    for (x, y) in ((yard[0] + 1.5, yard[2] + 1.5), (yard[0] + 1.5, yard[3] - 1.5), (D / 2 + 3, yard[3] - 1.4), (D / 2 + 3, yard[2] + 1.4), (D / 2 + 5.2, yard[3] - 1.4), (D / 2 + 5.2, yard[2] + 1.4)):
        cypress(K, M, x, y, 0.0, 9.5 + (x % 2.0))
    rng = np.random.default_rng(5)
    for i in range(10):
        x = -2.0 + (i % 5) * 2.4; y = W / 2 + 2.0 + (i // 5) * 1.6
        K.obj(bbox(x, y, 0.45, 0.14, 0.6, 0.9, rng.uniform(-0.06, 0.06)), M['stone'], np.array((0.82, 0.8, 0.76)) * rng.uniform(0.85, 1.0), 'box', 1.0, 0.03, 2)
        K.obj(bbox(x - 0.6, y, 0.04, 1.1, 0.7, 0.08), M['stone'], (0.7, 0.68, 0.62))


# ------------------------------------------------------------------ 2 lighthouse
def lighthouse_hq(K, M):
    """Tapered masonry tower on a granite base, rendered white with a red band; corbelled gallery, iron railing, a glazed lantern
    with diagonal astragals round a Fresnel lens, red dome with ventilator and vane; keeper's cottage and oil store behind a wall."""
    H0, Ht, R0, R1 = 2.0, 27.0, 4.2, 2.9; rt = lambda z: R0 + (R1 - R0) * (z - H0) / (Ht - H0)
    K.obj(lathe([(5.4, 0.0), (5.4, 0.3), (5.1, 0.4), (5.0, H0 - 0.2), (4.6, H0), (0.0, H0)], 36), M['rock'] if 'rock' in M else M['ashlar'], (0.62, 0.6, 0.57), 'cyl', 2.5)
    bands = [(H0, 20.5, WHITE), (20.5, 23.0, (0.72, 0.1, 0.08)), (23.0, Ht, WHITE)]
    for z0, z1, col in bands: K.obj(lathe([(rt(z0), z0), (rt(z1), z1)], 36, close_top=False, close_bottom=False), M['plaster'], col, 'cyl', 2.4)
    for k in range(6):                                                                         # stair windows spiralling up
        z = 5.0 + k * 3.4; a = k * 1.15 + 0.4; r = rt(z)
        Fw = Frame((r * math.cos(a), r * math.sin(a), 0), (-math.sin(a), math.cos(a), 0), (math.cos(a), math.sin(a), 0))
        K.obj(Fw.box(-0.32, 0.32, -0.05, 0.03, z, z + 1.1), M['winglass'], (1, 1, 1)); K.obj(Fw.box(-0.45, 0.45, 0.0, 0.14, z - 0.12, z), M['stone'], TRIM)
        K.obj(Fw.box(-0.45, 0.45, 0.0, 0.1, z + 1.1, z + 1.25), M['stone'], TRIM)
    for k in range(24):                                                                        # gallery corbels
        a = k * 2 * math.pi / 24; K.obj(bbox((R1 + 0.35) * math.cos(a), (R1 + 0.35) * math.sin(a), Ht - 0.6, 0.8, 0.28, 1.0, a), M['stone'], TRIM, 'box', 1.0, 0.03, 2)
    zg = Ht + 0.1
    K.obj(lathe([(R1 - 0.1, zg - 0.2), (R1 + 1.25, zg - 0.05), (R1 + 1.25, zg + 0.3), (0.0, zg + 0.3)], 36), M['stone'], (0.86, 0.85, 0.82), 'cyl', 1.5)
    for a in np.linspace(0, 2 * np.pi, 48, endpoint=False): K.obj(bbox((R1 + 1.15) * math.cos(a), (R1 + 1.15) * math.sin(a), zg + 0.85, 0.05, 0.05, 1.1), M['iron'], IRON)
    for z in (zg + 1.4, zg + 0.85): K.obj(lathe([(R1 + 1.18, z), (R1 + 1.18, z + 0.06)], 48, close_top=False, close_bottom=False), M['iron'], IRON)
    K.obj(lathe([(2.0, zg + 0.3), (2.0, zg + 1.3), (2.1, zg + 1.35), (2.1, zg + 1.45)], 24, close_top=False, close_bottom=False), M['iron'], (0.72, 0.1, 0.08))     # lantern base
    zl = zg + 1.45; Hl = 3.0
    K.obj(lathe([(2.0, zl), (2.0, zl + Hl)], 24, close_top=False, close_bottom=False), M['glass'], (1, 1, 1))
    for k in range(12):                                                                        # diagonal astragals
        for sg in (-1, 1):
            pts = [(2.02 * math.cos(k * math.pi / 6 + sg * t * math.pi / 6), 2.02 * math.sin(k * math.pi / 6 + sg * t * math.pi / 6), zl + t * Hl) for t in np.linspace(0, 1, 5)]
            K.obj(sweep(pts, 0.035, 4), M['iron'], (0.72, 0.1, 0.08))
    for z in (zl, zl + Hl): K.obj(lathe([(2.06, z - 0.06), (2.06, z + 0.06)], 24, close_top=False, close_bottom=False), M['iron'], (0.72, 0.1, 0.08))
    lens = [(0.35, zl + 0.2)]                                                                  # Fresnel lens: stacked prism rings
    for i in range(9): z = zl + 0.35 + i * 0.26; lens += [(0.95 - abs(i - 4) * 0.06, z), (1.05 - abs(i - 4) * 0.06, z + 0.13)]
    lens += [(0.35, zl + 2.75), (0.0, zl + 2.8)]
    K.obj(lathe(lens, 24), M['lens'], (1.0, 0.92, 0.7), 'cyl', 1.0)
    K.obj(lathe([(0.5, zl - 0.2), (0.3, zl + 0.2), (0.0, zl + 0.2)], 12), M['galv'], (0.55, 0.45, 0.25))
    K.obj(lathe([(2.3, zl + Hl), (2.25, zl + Hl + 0.25), (1.9, zl + Hl + 1.0), (1.0, zl + Hl + 1.6), (0.3, zl + Hl + 1.8), (0.0, zl + Hl + 1.8)], 24), M['smooth'], (0.72, 0.1, 0.08), 'cyl', 1.2)
    K.obj(lathe([(0.3, zl + Hl + 1.8), (0.32, zl + Hl + 2.1), (0.0, zl + Hl + 2.2)], 10), M['galv'], (0.3, 0.3, 0.3))
    K.obj(lathe([(0.0, -0.32), (0.32, 0.0), (0.0, 0.32)], 12, 0, 0, zl + Hl + 2.55), M['galv'], (0.3, 0.3, 0.3))
    K.obj(bbox(0, 0, zl + Hl + 3.3, 0.05, 0.05, 1.4), M['iron'], IRON); K.obj(_vane(), M['iron'], IRON)
    # door at the base, facing +X
    F = Frame((R0 + 0.05, 0, 0), (0, 1, 0), (1, 0, 0))
    K.obj(F.box(-0.65, 0.65, -0.3, 0.05, H0, H0 + 2.4), M['pwood'], (0.12, 0.28, 0.4), 'box', 1.0, 0.01, 1)
    K.obj(F.box(-0.85, 0.85, 0.0, 0.5, H0 + 2.4, H0 + 2.65), M['stone'], TRIM, 'box', 1.2)
    for i in range(4): K.obj(F.box(-1.0, 1.0, 1.2 + 0.0, 1.2 + 0.4 * (4 - i) * 0.5 + 0.8, i * H0 / 4, (i + 1) * H0 / 4), M['stone'], (0.8, 0.78, 0.74), 'box', 1.2, 0.01, 1)
    # keeper's cottage behind (-X), white walls, terracotta roof, green shutters
    cx = -R0 - 5.8; CW, CD, ch = 8.0, 7.0, 3.6
    K.obj(bbox(cx, 0, 0.2, CD + 0.4, CW + 0.4, 0.4), M['stone'], (0.7, 0.68, 0.64))
    for k, (F0, Ln) in enumerate(fronts(CW, CD)):
        Fc = Frame(F0.o + np.array([cx, 0, 0]), F0.u, F0.n)
        holes = [(-2.6, -1.6, 1.4, 2.8), (1.6, 2.6, 1.4, 2.8)] if k >= 2 else ([(-0.6, 0.6, 0.4, 2.6)] if k == 1 else [(-1.5, -0.5, 1.4, 2.8)])
        walls(K, M, Fc, Ln if k < 2 else Ln - 0.5, 0.4, ch, holes, WHITE, 0.3, M['plaster'], 'box', 2.4)
        for (a, b, c, d) in holes:
            K.obj(Fc.box(a, b, -0.24, -0.22, c, d), M['winglass'] if d - c < 2 else M['pwood'], (1, 1, 1) if d - c < 2 else (0.12, 0.3, 0.2))
            if d - c < 2:
                for sg in (-1, 1): K.obj(Fc.box(a - 0.5 if sg < 0 else b, a if sg < 0 else b + 0.5, 0.0, 0.04, c, d), M['pwood'], (0.15, 0.36, 0.25), 'box', 1.0, 0.008, 1)
            K.obj(Fc.box(a - 0.08, b + 0.08, -0.05, 0.1, c - 0.1, c), M['stone'], TRIM)
    Kr = P.Part(); gable_roof(Kr, M, CW, CD, ch, 2.0, TERRA, WHITE, 0.4, 0.18, 'y'); _shift(K, Kr, (cx, 0.0, 0.0))
    K.obj(bbox(cx - 1.5, 2.0, ch + 1.6, 0.6, 0.6, 2.0), M['plaster'], WHITE, 'box', 1.0, 0.02, 1)
    # oil store and the boundary wall
    K.obj(bbox(cx + 1.0, -CW / 2 - 3.2, 1.25, 3.0, 2.6, 2.5), M['plaster'], WHITE, 'box', 2.0, 0.03, 2)
    K.obj(bbox(cx + 1.0, -CW / 2 - 3.2, 2.6, 3.4, 3.0, 0.2), M['roof'], TERRA, 'roof', 1.4)
    for (x0, x1, y0, y1) in ((-R0 - 13.5, R0 + 5.5, -10.5, -10.0), (-R0 - 13.5, R0 + 5.5, 10.0, 10.5), (-R0 - 13.5, -R0 - 13.0, -10.5, 10.5)):
        K.obj(bbox((x0 + x1) / 2, (y0 + y1) / 2, 0.6, x1 - x0, y1 - y0, 1.2), M['plaster'], WHITE, 'box', 2.0, 0.04, 2)
        K.obj(bbox((x0 + x1) / 2, (y0 + y1) / 2, 1.25, x1 - x0 + 0.15, y1 - y0 + 0.15, 0.12), M['stone'], TRIM)


def _shift(K, Kp, off):
    import mathutils
    for it in Kp.objs:
        if it[0] == 'raw': _, Pq, T_, N_, *rest = it; K.objs.append(('raw', Pq + np.array(off), T_, N_, *rest))
        else: it[0].data.transform(mathutils.Matrix.Translation(off)); K.objs.append(it)


def _vane():
    bm = bmesh.new(); pts = [(-0.7, 0.0), (0.4, 0.0), (0.7, 0.18), (0.4, 0.35), (0.25, 0.08), (-0.7, 0.08)]
    z = 2.8 + 29.25 + 3.0 + 1.6
    A = [bm.verts.new((x, -0.01, z + y)) for x, y in pts]; B = [bm.verts.new((x, 0.01, z + y)) for x, y in pts]
    bm.faces.new(A); bm.faces.new(B[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return bm


# ------------------------------------------------------------------ 3 windmill
def windmill_hq(K, M):
    """Whitewashed Mediterranean tower mill: battered stone base, small deep windows, a doorway with a stone stair, timber curb and
    a conical tiled cap turned into the wind (windshaft out at -Y), tail pole with a cart wheel. Sails are windmill_sails_hq (they spin)."""
    prof = [(4.5, 0.0), (4.5, 0.6), (4.35, 0.8)] + [(4.3 - 1.1 * t, 0.8 + 15.0 * t) for t in np.linspace(0, 1, 8)]
    K.obj(lathe([(4.9, 0.0), (4.9, 0.6), (4.5, 0.75), (0.0, 0.75)], 32), M['stone'], (0.72, 0.68, 0.6), 'cyl', 1.4)
    K.obj(lathe(prof, 32, close_top=False, close_bottom=False), M['plaster'], WHITE, 'cyl', 2.4)
    for k, (z, a) in enumerate(((3.0, 0.5), (7.0, 2.6), (10.8, -1.0), (13.4, 1.4))):
        r = 4.3 - 1.1 * (z - 0.8) / 15; Fw = Frame((r * math.cos(a), r * math.sin(a), 0), (-math.sin(a), math.cos(a), 0), (math.cos(a), math.sin(a), 0))
        K.obj(Fw.box(-0.35, 0.35, -0.5, 0.02, z, z + 0.9), M['smooth'], (0.04, 0.04, 0.04)); K.obj(Fw.box(-0.33, 0.33, -0.25, -0.2, z, z + 0.9), M['pwood'], (0.15, 0.35, 0.5), 'box', 1.0, 0.008, 1)
    F = Frame((4.32, 0, 0), (0, 1, 0), (1, 0, 0))
    K.obj(F.box(-0.7, 0.7, -0.3, 0.02, 0.8, 3.1), M['planks'], (0.15, 0.35, 0.5), 'boxv', 1.0)
    K.obj(F.box(-0.9, 0.9, 0.0, 0.25, 3.1, 3.35), M['planks'], (0.4, 0.3, 0.2))
    for i in range(3): K.obj(F.box(-1.1, 1.1, 0.0, 1.4 - i * 0.4, i * 0.25, (i + 1) * 0.25), M['stone'], (0.8, 0.77, 0.7), 'box', 1.0, 0.01, 1)
    zc = 15.8
    K.obj(lathe([(3.15, zc), (3.4, zc + 0.05), (3.4, zc + 0.45), (0.0, zc + 0.45)], 32), M['planks'], (0.4, 0.3, 0.2), 'cylv', 1.0)          # curb
    K.obj(lathe([(3.55, zc + 0.45), (3.4, zc + 0.8), (2.4, zc + 2.6), (0.9, zc + 4.2), (0.15, zc + 4.7), (0.0, zc + 4.75)], 32), M['roof'], (0.62, 0.34, 0.24), 'roof', 1.2)   # cap
    K.obj(lathe([(0.12, zc + 4.7), (0.06, zc + 5.6), (0.0, zc + 5.65)], 8), M['iron'], IRON)
    K.obj(sweep([(0.0, 1.5, 18.2), (0.0, -4.0, 18.2)], 0.28, 10), M['planks'], (0.45, 0.33, 0.22), 'cylv', 1.0)                  # windshaft
    K.obj(sweep([(0.0, 3.0, zc + 0.3), (0.0, 9.5, 0.6)], 0.16, 8), M['planks'], (0.42, 0.32, 0.22), 'cylv', 1.0)                    # tail pole
    wh = lathe([(0.7, -0.08), (0.7, 0.08)], 16, close_top=False, close_bottom=False)
    for v in wh.verts: x, y, z = v.co; v.co = (x, 9.5 + z, 0.75 + y)
    K.obj(wh, M['planks'], (0.35, 0.26, 0.18))
    for k in range(8):
        a = k * math.pi / 4; K.obj(sweep([(0.0, 9.5, 0.75), (0.68 * math.cos(a), 9.5, 0.75 + 0.68 * math.sin(a))], 0.03, 4), M['planks'], (0.35, 0.26, 0.18))
    for (x, y, s) in ((2.2, 5.6, 1.0), (3.0, 5.2, 0.9), (2.6, 4.6, 0.85)):                    # grain sacks and a low wall
        K.obj(lathe([(0.0, 0.0), (0.32 * s, 0.05), (0.36 * s, 0.4 * s), (0.25 * s, 0.75 * s), (0.0, 0.8 * s)], 10, x, y, 0.0), M['fabric'], (0.82, 0.74, 0.58))
    for k in range(9):
        a = math.pi * 0.15 + k * math.pi * 0.08; K.obj(bbox(7.2 * math.cos(a), 7.2 * math.sin(a), 0.45, 0.6, 1.6, 0.9, a), M['stone'], np.array((0.78, 0.72, 0.62)) * (0.92 + 0.1 * (k % 2)), 'box', 1.0, 0.05, 2)


def windmill_sails_hq(K, M):
    """Four sails with a lattice frame, canvas furled on two and set on two, and a bowsprit with stays to every tip
    (centred on the hub, in the x-z plane; the game spins them about local z)."""
    for k in range(4):
        a = k * math.pi / 2 + 0.3; d = np.array([math.cos(a), 0, math.sin(a)]); e = np.array([-d[2], 0, d[0]])
        K.obj(sweep([tuple(d * 0.4), tuple(d * 13.0)], 0.17, 6), M['planks'], (0.48, 0.35, 0.23), 'cylv', 1.0)
        for t in np.linspace(2.6, 12.8, 12): K.obj(sweep([tuple(d * t - e * 0.15), tuple(d * t + e * 2.5)], 0.04, 4), M['planks'], (0.72, 0.6, 0.46))
        for o in (0.0, 1.2, 2.45): K.obj(sweep([tuple(d * 2.6 + e * o), tuple(d * 12.8 + e * o)], 0.035, 4), M['planks'], (0.72, 0.6, 0.46))
        if k % 2 == 0:                                                                         # canvas set
            q = [d * 2.8 + e * 0.1, d * 12.6 + e * 0.1, d * 12.6 + e * 2.35, d * 2.8 + e * 2.35]
            for qq, dy in ((q, -0.05), (q[::-1], -0.07)):
                cl = bmesh.new(); cl.faces.new([cl.verts.new(tuple(v + np.array([0, dy, 0]))) for v in qq]); K.obj(cl, M['fabric'], (0.93, 0.89, 0.8), 'box', 1.0, smooth=False)
        else:                                                                                  # canvas furled along the leading edge
            K.obj(sweep([tuple(d * 2.8 + e * 2.3 + np.array([0, -0.08, 0])), tuple(d * 12.6 + e * 2.3 + np.array([0, -0.08, 0]))], 0.13, 8), M['fabric'], (0.86, 0.82, 0.72), 'cylv', 1.0)
        K.obj(sweep([(0.0, -4.0, 0.0), tuple(d * 12.9 + np.array([0, 0.0, 0]))], 0.012, 3), M['iron'], (0.3, 0.27, 0.22))       # stay
    K.obj(sweep([(0.0, 0.3, 0.0), (0.0, -4.1, 0.0)], 0.1, 8), M['planks'], (0.45, 0.33, 0.22), 'cylv', 1.0)                     # bowsprit
    K.obj(lathe([(0.55, -0.7), (0.65, 0.2), (0.0, 0.32)], 14), M['iron'], (0.22, 0.2, 0.18))


# ------------------------------------------------------------------ 4 fuel station
def brand_atlas(N=512):
    """2 x 2 cells: AURELIA fuel wordmark, price board, shop sign, car-wash sign (original designs)."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new('RGB', (N, N), (20, 70, 52)); d = ImageDraw.Draw(im); h = N // 2
    def font(sz):
        for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'):
            try: return ImageFont.truetype(f, sz)
            except Exception: pass
        return ImageFont.load_default()
    # 0 wordmark (top-left): green, white text, amber wave
    d.rectangle([0, 0, h, h], fill=(18, 92, 66)); d.text((h // 2, h // 2 - 18), 'AURELIA', fill=(245, 242, 232), font=font(46), anchor='mm')
    d.arc([40, h // 2 + 6, h - 40, h // 2 + 80], 200, 340, fill=(240, 170, 40), width=9); d.text((h // 2, h - 40), 'FUEL', fill=(240, 170, 40), font=font(28), anchor='mm')
    # 1 price board (top-right): three rows of amber digits on black
    d.rectangle([h, 0, N, h], fill=(14, 14, 16))
    for i, (nm, pr) in enumerate((('95', '1.68'), ('98', '1.82'), ('DSL', '1.59'))):
        y = 30 + i * 74; d.rectangle([h + 12, y, N - 12, y + 62], fill=(28, 28, 30)); d.text((h + 30, y + 31), nm, fill=(230, 230, 225), font=font(30), anchor='lm'); d.text((N - 26, y + 31), pr, fill=(255, 176, 30), font=font(40), anchor='rm')
    # 2 shop sign (bottom-left)
    d.rectangle([0, h, h, N], fill=(245, 242, 232)); d.text((h // 2, h + h // 2), 'SHOP · CAFE', fill=(18, 92, 66), font=font(34), anchor='mm')
    # 3 car wash (bottom-right)
    d.rectangle([h, h, N, N], fill=(30, 110, 170)); d.text((h + h // 2, h + h // 2), 'CAR WASH', fill=(250, 250, 250), font=font(36), anchor='mm')
    return (np.asarray(im, float) / 255.0)[::-1]


def _brand_mat(M):
    if 'brand' not in M:
        import isle_lib as L
        M['brand'] = L.new_mat('KitBrand', 0.4, 0.0, image=L.make_image('kit_brand_atlas', brand_atlas()), vcol=True)
        b = M['brand'].node_tree.nodes['Principled BSDF']; tx = [n for n in M['brand'].node_tree.nodes if n.type == 'TEX_IMAGE'][0]
        M['brand'].node_tree.links.new(tx.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 0.35
    return M['brand']


def _sign_face(K, M, F, u0, u1, n, z0, z1, cell):
    """Quad facing +n in frame F, UV-mapped to brand atlas cell (0..3)."""
    cu, cv = (cell % 2) * 0.5, (1 - cell // 2) * 0.5
    def uvf(Pq, ln):
        Q = Pq - F.o; uu = Q @ F.u; zz = Q[:, 2]
        return np.c_[cu + 0.01 + (uu - u0) / (u1 - u0) * 0.48, cv + 0.01 + (zz - z0) / (z1 - z0) * 0.48]
    K.obj(F.rect(u0, u1, n, z0, z1), _brand_mat(M), (1, 1, 1), 'sign', 1.0, smooth=False, sign=uvf)


def fuel_station_hq(K, M, rng=None, wash=True):
    """Forecourt canopy on slim columns with a lit AURELIA fascia and LED downlights over two pump islands (modern dispensers, hoses,
    crash posts), glazed shop with cafe, price totem, air/water point, car-wash bay, gas-bottle cage, bins and planters."""
    G = (0.07, 0.36, 0.26); AMB = (0.95, 0.66, 0.15)
    for a in (-5.0, 5.0):
        for b in (-3.0, 3.0): K.obj(bbox(b + 1.0, a, 2.7, 0.4, 0.4, 5.4), M['smooth'], (0.9, 0.9, 0.88), 'box', 1.0, 0.03, 2)
    K.obj(bbox(1.0, 0, 5.75, 11.6, 19.6, 0.9), M['smooth'], (0.95, 0.95, 0.93), 'box', 3.0, 0.04, 2)              # canopy slab
    K.obj(bbox(1.0, 0, 5.75, 11.7, 19.7, 0.35), M['smooth'], G, 'box', 3.0, 0.02, 1)                              # green band
    K.obj(bbox(1.0, 0, 5.28, 11.2, 19.2, 0.04), M['smooth'], (0.97, 0.97, 0.96))
    for sg in (-1, 1):
        Fs = Frame((1.0 + sg * 5.86, 0, 0), (0, sg, 0), (sg, 0, 0)); _sign_face(K, M, Fs, -2.2, 2.2, 0.01, 5.35, 6.15, 0)
    Fs = Frame((1.0, -9.86, 0), (1, 0, 0), (0, -1, 0)); _sign_face(K, M, Fs, -2.2, 2.2, 0.01, 5.35, 6.15, 0)
    for a in np.linspace(-8.0, 8.0, 5):
        for b in (-3.5, 1.0, 5.5): K.obj(bbox(b, a, 5.25, 1.2, 1.2, 0.03), M['lens'], (1.0, 0.98, 0.92))
    for a in (-5.0, 5.0):                                                                      # pump islands
        K.obj(bbox(1.0, a, 0.13, 8.0, 1.5, 0.26), M['concrete'], (0.86, 0.86, 0.84), 'box', 1.5, 0.03, 2)
        K.obj(bbox(1.0, a, 0.27, 8.1, 1.6, 0.02), M['smooth'], (0.95, 0.75, 0.12))
        for b in (-1.9, 1.9):
            x = b + 1.0
            K.obj(bbox(x, a, 1.15, 0.9, 1.1, 1.8), M['smooth'], (0.94, 0.94, 0.92), 'box', 1.0, 0.04, 2)
            K.obj(bbox(x, a, 2.2, 0.92, 1.12, 0.32), M['smooth'], G, 'box', 1.0, 0.03, 2)
            for sg in (-1, 1):
                K.obj(bbox(x + sg * 0.46, a, 1.6, 0.02, 0.6, 0.38), M['winglass'], (1, 1, 1))
                K.obj(bbox(x + sg * 0.465, a, 1.6, 0.01, 0.52, 0.3), M['lens'], (0.35, 0.6, 0.85))
                for j, yo in enumerate((-0.38, 0.0, 0.38)):                                    # nozzles in holsters, hoses
                    K.obj(bbox(x + sg * 0.5, a + yo, 1.05, 0.1, 0.12, 0.28), M['smooth'], ((0.1, 0.5, 0.2), (0.15, 0.15, 0.15), (0.9, 0.6, 0.1))[j])
                    K.obj(sweep([(x + sg * 0.48, a + yo, 1.95), (x + sg * 0.9, a + yo, 1.5), (x + sg * 0.75, a + yo, 0.45), (x + sg * 0.5, a + yo, 0.95)], 0.025, 5), M['iron'], (0.06, 0.06, 0.06))
        for b in (-3.7, 3.7):
            K.obj(lathe([(0.11, 0), (0.11, 1.0), (0.0, 1.05)], 10, b + 1.0, a), M['smooth'], AMB)
            for z in (0.55, 0.75): K.obj(lathe([(0.115, z), (0.115, z + 0.08)], 10, b + 1.0, a, close_top=False, close_bottom=False), M['smooth'], (0.08, 0.08, 0.08))
    # shop
    kx = -9.5; KW, KD, kh = 16.0, 7.0, 4.4
    K.obj(bbox(kx, 0, 0.12, KD + 1.6, KW + 0.6, 0.24), M['concrete'], (0.82, 0.82, 0.8), 'box', 1.5)
    for k, (F0, Ln) in enumerate(fronts(KW, KD)):
        Fk = Frame(F0.o + np.array([kx, 0, 0]), F0.u, F0.n); holes = []
        if k == 0: holes = [(-7.2, 7.2, 0.3, 3.3)]
        if k == 2: holes = [(-2.0, 1.2, 0.3, 2.6)]
        walls(K, M, Fk, Ln if k < 2 else Ln - 0.5, 0.24, kh, holes, (0.93, 0.93, 0.9), 0.25, M['concrete2'], 'box', 2.6)
        if k == 0:
            K.obj(Fk.box(-7.2, 7.2, -0.2, -0.18, 0.3, 3.3), M['winglass'], (1, 1, 1))
            for u in np.linspace(-7.2, 7.2, 9): K.obj(Fk.fin(u - 0.05, u + 0.05, -0.2, -0.08, 0.3, 3.3), M['galv'], (0.55, 0.57, 0.6), smooth=False)
            K.obj(Fk.box(-1.2, 1.2, -0.19, -0.15, 0.3, 2.6), M['smooth'], (0.6, 0.62, 0.64))
            K.obj(Fk.box(-8.3, 8.3, 0.0, 1.6, 3.4, 3.6), M['smooth'], (0.95, 0.95, 0.93), 'box', 2.0, 0.02, 1)       # entrance canopy
            K.obj(Fk.box(-8.4, 8.4, 0.0, 0.3, kh - 0.7, kh + 0.35), M['smooth'], G, 'box', 2.0)
            _sign_face(K, M, Fk, -3.0, 3.0, 0.31, kh - 0.62, kh + 0.27, 2)
            for u in np.linspace(-7, 7, 15): K.obj(Fk.box(u - 0.3, u + 0.3, 1.0, 1.56, 3.36, 3.38), M['lens'], (1.0, 0.97, 0.9))
            K.obj(Fk.box(4.0, 5.8, 0.0, 0.9, 0.0, 1.0), M['smooth'], (0.9, 0.92, 0.95), 'box', 1.0, 0.04, 2)          # ice chest
            K.obj(Fk.box(4.05, 5.75, 0.9, 0.92, 0.6, 0.95), M['brand'] if 'brand' in M else M['smooth'], (0.3, 0.55, 0.85))
            for uu in (-5.0, -3.6):                                                             # planters with olive shrubs
                K.obj(Fk.box(uu - 0.5, uu + 0.5, 0.4, 1.4, 0.0, 0.7), M['concrete'], (0.7, 0.7, 0.68), 'box', 1.0, 0.03, 2)
                K.obj(lathe([(0.0, 0.0), (0.5, 0.2), (0.55, 0.7), (0.3, 1.1), (0.0, 1.2)], 8, *Fk.w(uu, 0.9, 0)[:2], 0.7), M['concrete'], (0.25, 0.32, 0.16))
    K.obj(bbox(kx, 0, kh + 0.15, KD + 0.3, KW + 0.3, 0.3), M['concrete'], (0.62, 0.62, 0.62))
    for (x, y) in ((kx - 1.5, -4.0), (kx - 2.0, 3.0)): K.obj(bbox(x, y, kh + 0.8, 1.6, 1.2, 1.0), M['galv'], (0.65, 0.67, 0.7), 'box', 1.0, 0.03, 2)   # roof plant
    # car-wash bay at the -Y end of the shop
    wx, wy = kx, -KW / 2 - 3.6
    if wash:
        for sg in (-1, 1): K.obj(bbox(wx + sg * 2.6, wy, 2.2, 0.3, 6.0, 4.4), M['concrete2'], (0.9, 0.9, 0.88), 'box', 2.0)
        K.obj(bbox(wx, wy, 4.55, 5.8, 6.4, 0.3), M['smooth'], (0.95, 0.95, 0.93), 'box', 2.0, 0.02, 1)
        Fw = Frame((wx + 2.9, wy, 0), (0, 1, 0), (1, 0, 0)); _sign_face(K, M, Fw, -2.4, 2.4, -2.88 + 2.9 - 0.0, 3.8, 4.4, 3) if False else _sign_face(K, M, Frame((wx, wy - 3.21, 0), (1, 0, 0), (0, -1, 0)), -2.4, 2.4, 0.0, 3.85, 4.4, 3)
        K.obj(bbox(wx, wy, 2.4, 0.5, 4.6, 0.5), M['galv'], (0.55, 0.57, 0.6))
        for sg in (-1, 1): K.obj(lathe([(0.45, 0.0), (0.45, 2.0), (0.0, 2.05)], 12, wx + sg * 1.4, wy), M['fabric'], (0.2, 0.45, 0.85), 'cylv', 0.8)   # wash brushes
    # price totem, air/water, gas cage, bins
    Ft = Frame((7.5, -9.5, 0), (0, 1, 0), (1, 0, 0))
    K.obj(Ft.box(-0.9, 0.9, -0.35, 0.35, 0.0, 7.0), M['smooth'], G, 'box', 2.0, 0.03, 2)
    _sign_face(K, M, Ft, -0.8, 0.8, 0.36, 5.4, 6.8, 0); _sign_face(K, M, Ft, -0.8, 0.8, 0.36, 2.6, 5.2, 1)
    K.obj(bbox(6.0, 9.0, 0.7, 0.5, 0.7, 1.4), M['smooth'], (0.15, 0.35, 0.65), 'box', 1.0, 0.03, 2)
    K.obj(sweep([(6.26, 9.0, 1.1), (6.6, 9.2, 0.6), (6.4, 9.5, 0.1)], 0.02, 4), M['iron'], IRON)
    K.obj(bbox(kx + 4.6, KW / 2 + 1.0, 0.9, 1.0, 1.8, 1.8), M['galv'], (0.6, 0.62, 0.65), 'box', 1.0, 0.02, 1)
    for k in range(6): K.obj(lathe([(0.15, 0), (0.15, 0.55), (0.06, 0.65), (0.0, 0.66)], 10, kx + 4.35 + (k % 3) * 0.25, KW / 2 + 0.6 + (k // 3) * 0.7, 0.05), M['smooth'], (0.2, 0.45, 0.8))
    for y in (-2.0, 2.0): K.obj(lathe([(0.3, 0.0), (0.3, 1.0), (0.32, 1.05), (0.0, 1.1)], 12, 4.0, y * 4.0), M['galv'], (0.4, 0.42, 0.44))


# ------------------------------------------------------------------ 5 stadium
def stadium_hq(K, M, a=105.0, b=84.0):
    """Oval bowl with a white fin facade over a glazed concourse band, two seating tiers split by a hospitality box ring with
    vomitories, a translucent membrane roof on cantilever trusses, scoreboards, floodlight masts, a striped pitch with full
    markings and goals, and the AURELIA STADIUM name over the main entrance."""
    seg = 96; ang = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    E = lambda k, t: (a * k * math.cos(t), b * k * math.sin(t))
    def ring(prof, mat, col, uv='box', uvs=3.0, flip=False):
        bm = bmesh.new(); R = []
        for (k, z) in prof: R.append([bm.verts.new((*E(k, t), z)) for t in ang])
        for r0, r1 in zip(R[:-1], R[1:]):
            for i in range(seg): bm.faces.new((r0[i], r0[(i + 1) % seg], r1[(i + 1) % seg], r1[i]) if not flip else (r1[i], r1[(i + 1) % seg], r0[(i + 1) % seg], r0[i]))
        K.obj(bm, mat, col, uv, uvs, smooth=False)
    ring([(1.0, -2.0), (1.0, 7.0)], M['concrete2'], (0.86, 0.86, 0.84), 'box', 4.0)                          # plinth / ground floor
    ring([(0.995, 7.0), (0.995, 12.0)], M['winglass'], (1, 1, 1), 'box', 4.0)                                 # glazed concourse band
    ring([(1.0, 12.0), (1.0, 25.0)], M['concrete2'], (0.9, 0.9, 0.88), 'box', 4.0)
    for i in range(seg):                                                                       # white fins, angled
        t = ang[i]; x, y = E(1.025, t); K.obj(bbox(x, y, 13.0, 0.35, 2.2, 28.0, t + 0.5), M['smooth'], (0.96, 0.96, 0.95), 'box', 3.0)
    for i in range(0, seg, 4):                                                                 # entrances
        t = ang[i]; x, y = E(1.003, t); K.obj(bbox(x, y, 2.0, 0.4, 5.5, 4.0, t), M['smooth'], (0.05, 0.05, 0.06))
    # lower and upper tiers
    blocks = [(0.12, 0.3, 0.62), (0.75, 0.13, 0.1), (0.92, 0.92, 0.9), (0.12, 0.3, 0.62)]
    def tier(k0, k1, z0, z1, steps, tag):
        prof = [(k0, z0)]
        for s in range(steps):
            kk = k0 - (k0 - k1) * (s + 1) / steps; zz = z0 - (z0 - z1) * s / steps; zz1 = z0 - (z0 - z1) * (s + 1) / steps
            prof += [(kk + 1e-4, zz), (kk, zz1)]
        bm = bmesh.new(); R = [[bm.verts.new((*E(k, t), z)) for t in ang] for (k, z) in prof]
        for r0, r1 in zip(R[:-1], R[1:]):
            for i in range(seg): bm.faces.new((r1[i], r1[(i + 1) % seg], r0[(i + 1) % seg], r0[i]))
        for blk in range(4):
            b2 = bm.copy(); rm = [f for f in b2.faces if int(((math.atan2(f.calc_center_median().y / b, f.calc_center_median().x / a) + math.pi) / (math.pi / 8))) % 4 != blk]
            bmesh.ops.delete(b2, geom=rm, context='FACES'); K.obj(b2, M['plastic'], blocks[blk], 'box', 1.0, smooth=False)
        bm.free()
    tier(0.97, 0.82, 23.5, 13.0, 14, 'upper'); tier(0.8, 0.62, 10.5, 1.2, 16, 'lower')
    ring([(0.82, 13.0), (0.82, 10.5), (0.8, 10.5)], M['winglass'], (1, 1, 1), 'box', 3.0, flip=True)         # hospitality boxes
    ring([(0.825, 13.2), (0.8, 13.2)], M['concrete'], (0.8, 0.8, 0.78), flip=True)
    for i in range(2, seg, 8):                                                                 # vomitories through the lower tier
        t = ang[i]; x, y = E(0.71, t); K.obj(bbox(x, y, 6.0, 4.0, 2.6, 3.0, t), M['smooth'], (0.05, 0.05, 0.06))
    ring([(0.6, 1.4), (0.6, 0.5), (0.0, 0.5)], M['concrete'], (0.55, 0.55, 0.53))
    # pitch
    for k in range(12):
        st = bmesh.new(); x0 = -54 + k * 9; sv = [st.verts.new(v) for v in ((x0, -36, 0.62), (x0 + 9, -36, 0.62), (x0 + 9, 36, 0.62), (x0, 36, 0.62))]; st.faces.new(sv)
        K.obj(st, M['grassg'] if 'grassg' in M else M['plaster'], (0.32, 0.6, 0.2) if k % 2 else (0.38, 0.68, 0.24), 'box', 4.0, smooth=False)
    def lineq(x0, y0, x1, y1, w=0.12):
        L = math.hypot(x1 - x0, y1 - y0); K.obj(bbox((x0 + x1) / 2, (y0 + y1) / 2, 0.635, L + w, w, 0.01, math.atan2(y1 - y0, x1 - x0)), M['smooth'], (0.96, 0.96, 0.95))
    for (x0, y0, x1, y1) in ((-52.5, -34, 52.5, -34), (-52.5, 34, 52.5, 34), (-52.5, -34, -52.5, 34), (52.5, -34, 52.5, 34), (0, -34, 0, 34)): lineq(x0, y0, x1, y1)
    for sg in (-1, 1):
        X = sg * 52.5
        for (x0, y0, x1, y1) in ((X, -20.15, X - sg * 16.5, -20.15), (X - sg * 16.5, -20.15, X - sg * 16.5, 20.15), (X - sg * 16.5, 20.15, X, 20.15),
                                 (X, -9.15, X - sg * 5.5, -9.15), (X - sg * 5.5, -9.15, X - sg * 5.5, 9.15), (X - sg * 5.5, 9.15, X, 9.15)): lineq(x0, y0, x1, y1)
        for z in (0.0, 2.44):                                                                  # goal frame and net
            pass
        for yy in (-3.66, 3.66): K.obj(bbox(X + sg * 0.06, yy, 0.62 + 1.22, 0.12, 0.12, 2.44), M['smooth'], (0.98, 0.98, 0.98))
        K.obj(bbox(X + sg * 0.06, 0, 0.62 + 2.44, 0.12, 7.44, 0.12), M['smooth'], (0.98, 0.98, 0.98))
        net = bmesh.new(); nv = [net.verts.new(v) for v in ((X, -3.66, 3.06), (X + sg * 2.0, -3.66, 0.62), (X + sg * 2.0, 3.66, 0.62), (X, 3.66, 3.06))]; net.faces.new(nv)
        K.obj(net, M['fabric'], (0.92, 0.92, 0.9), smooth=False)
        K.obj(lathe([(0.11, 0.0), (0.0, 0.01)], 12, X - sg * 11.0, 0, 0.632), M['smooth'], (0.96, 0.96, 0.95))
    cc = lathe([(9.15, 0.0), (9.3, 0.0)], 64, 0, 0, 0.632, close_top=False, close_bottom=False)
    K.obj(ring_flat(9.15, 9.27, 0.633), M['smooth'], (0.96, 0.96, 0.95))
    for sg in (-1, 1):                                                                         # dugouts
        K.obj(bbox(sg * 8.0, -38.5, 1.3, 10.0, 2.2, 1.4), M['glass'], (1, 1, 1)); K.obj(bbox(sg * 8.0, -38.6, 2.05, 10.4, 2.6, 0.12), M['smooth'], (0.12, 0.3, 0.62))
    # roof: membrane on cantilever trusses, scoreboards
    ring([(1.03, 25.0), (1.06, 27.8), (1.0, 28.6)], M['galv'], (0.92, 0.93, 0.95), 'box', 4.0)
    ring([(1.0, 28.4), (0.72, 30.6)], M['glass'], (0.95, 0.96, 0.97), 'box', 6.0)
    ring([(0.72, 30.6), (0.715, 30.1)], M['galv'], (0.85, 0.86, 0.88), 'box', 4.0)
    for i in range(0, seg, 3):
        t = ang[i]; p0 = (*E(1.04, t), 27.8); p1 = (*E(0.72, t), 30.7); p2 = (*E(0.86, t), 33.2)
        K.obj(sweep([p0, p2, p1], 0.22, 6), M['galv'], (0.88, 0.89, 0.92)); K.obj(sweep([p0, p1], 0.18, 6), M['galv'], (0.88, 0.89, 0.92))
    for sg in (-1, 1):
        x, y = E(0.9, math.pi if sg < 0 else 0.0); Fb = Frame((x, y, 0), (0, -sg, 0), (-sg, 0, 0))
        K.obj(Fb.box(-9.0, 9.0, -0.6, 0.0, 24.0, 29.0), M['smooth'], (0.05, 0.05, 0.06), 'box', 2.0, 0.03, 1)
        K.obj(Fb.box(-8.6, 8.6, 0.0, 0.02, 24.4, 28.6), M['neon'], (1, 1, 1), 'box', 6.0)
    for k in range(4):                                                                         # floodlight masts
        t = k * math.pi / 2 + math.pi / 4; px, py = E(1.07, t)
        K.obj(lathe([(1.2, 0.0), (0.6, 52.0), (0.55, 54.0)], 12, px, py), M['galv'], (0.82, 0.84, 0.87), 'cyl', 3.0)
        Fm = Frame((px, py, 0), (-math.sin(t), math.cos(t), 0), (-math.cos(t), -math.sin(t), 0))
        K.obj(Fm.box(-4.0, 4.0, -0.7, 0.4, 52.0, 58.0), M['galv'], (0.6, 0.62, 0.65), 'box', 2.0)
        for i in range(5):
            for j in range(4): K.obj(Fm.box(-3.6 + i * 1.5, -2.5 + i * 1.5, 0.4, 0.46, 52.4 + j * 1.4, 53.6 + j * 1.4), M['lens'], (1.0, 0.98, 0.92))
    # main entrance with the name (front +X)
    x, y = E(1.0, 0.0); Fe = Frame((x + 0.8, 0, 0), (0, 1, 0), (1, 0, 0))
    K.obj(Fe.box(-24, 24, 0.0, 6.0, 9.0, 9.6), M['smooth'], (0.95, 0.95, 0.94), 'box', 2.0, 0.03, 1)
    for u in np.linspace(-22, 22, 9): K.obj(lathe([(0.3, 0.0), (0.3, 9.0)], 10, *Fe.w(u, 5.5, 0)[:2]), M['smooth'], (0.95, 0.95, 0.94))
    _name_sign(K, M, Fe)
    for u in np.linspace(-14, 14, 8): K.obj(Fe.box(u - 0.5, u + 0.5, 1.0, 2.2, 0.0, 1.1), M['galv'], (0.5, 0.52, 0.55), 'box', 1.0, 0.02, 1)   # turnstiles
    K.obj(Fe.box(-30, 30, 0.0, 18.0, -0.1, 0.05), M['setts'] if 'setts' in M else M['concrete'], (0.85, 0.82, 0.78), 'box', 1.6)


def ring_flat(r0, r1, z, n=64):
    bm = bmesh.new(); A = [bm.verts.new((r0 * math.cos(t), r0 * math.sin(t), z)) for t in np.linspace(0, 2 * np.pi, n, endpoint=False)]
    B = [bm.verts.new((r1 * math.cos(t), r1 * math.sin(t), z)) for t in np.linspace(0, 2 * np.pi, n, endpoint=False)]
    for i in range(n): bm.faces.new((A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]))
    return bm


def _name_sign(K, M, F):
    """AURELIA STADIUM in block letters standing on the entrance canopy (letters are boxes from a 5x7 pixel font)."""
    font = {'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'], 'U': ['10001'] * 6 + ['01110'], 'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
            'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'], 'L': ['10000'] * 6 + ['11111'], 'I': ['11111', '00100', '00100', '00100', '00100', '00100', '11111'],
            'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'], 'T': ['11111'] + ['00100'] * 6, 'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
            'M': ['10001', '11011', '10101', '10101', '10001', '10001', '10001'], ' ': ['00000'] * 7}
    txt = 'AURELIA STADIUM'; px = 0.42; wch = 6 * px; u0 = -len(txt) * wch / 2
    for ci, ch in enumerate(txt):
        rows = font[ch]
        for r, row in enumerate(rows):
            runs = []; c = 0
            while c < 5:
                if row[c] == '1':
                    s = c
                    while c < 5 and row[c] == '1': c += 1
                    runs.append((s, c))
                else: c += 1
            for s, e in runs:
                ua = u0 + ci * wch + s * px; ub = u0 + ci * wch + e * px; z1 = 9.6 + (7 - r) * px; z0 = z1 - px
                K.obj(F.box(ua, ub, 0.3, 0.6, z0, z1), M['lens'], (0.95, 0.95, 0.92))


def windmill_full(K, M):
    windmill_hq(K, M); Kp = P.Part(); windmill_sails_hq(Kp, M)
    for it in Kp.objs:
        if it[0] == 'raw': _, Pq, T_, N_, *rest = it; K.objs.append(('raw', Pq + np.array([0.0, -4.3, 18.2]), T_, N_, *rest))
        else: it[0].location = (0.0, -4.3, 18.2); it[0].data.transform(__import__('mathutils').Matrix.Translation((0.0, -4.3, 18.2))); it[0].location = (0, 0, 0); K.objs.append(it)


ITEMS = dict(windmill_full=(windmill_full, 31.0), church_hq=(church_hq, 28.0), lighthouse_hq=(lighthouse_hq, 36.0), windmill_hq=(windmill_hq, 21.5), windmill_sails_hq=(windmill_sails_hq, 13.0),
             fuel_station_hq=(fuel_station_hq, 7.0), stadium_hq=(stadium_hq, 58.0))


def kit_mats():
    """The game's kit materials with what the landmarks add (limestone, brand atlas, road photo materials)."""
    M = P.mats()
    if 'limestone' not in M:
        import isle_roads_hq as RQ; RQ.materials(M); _brand_mat(M); RQ._kit_photo(M, 'limestone', 'Bricks066', 0.62, 0.0, 1.0, 0.7)
    return M


def register(M=None):
    M = M if M is not None else P.mats()
    import isle_roads_hq as RQ; RQ.materials(M); _brand_mat(M); RQ._kit_photo(M, 'limestone', 'Bricks066', 0.62, 0.0, 1.0, 0.7)
    for k, (fn, h) in ITEMS.items(): P.PROPS['lm_' + k] = (fn, {}); P.HEIGHT['lm_' + k] = h

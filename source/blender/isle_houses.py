"""Village houses for Aurelia Island, modelled in Blender like the street kit: walls built around real window and door openings
(reveals, frames, mullions, sills, lintels, shutters, panelled doors), stone plinth, tiled roofs with thickness, fascia, barge boards,
rafter tails, half-round gutters and downpipes, stone chimneys with caps and pots, porches and balconies.
Every house is one prop (LOD0 + LOD1) placed as instances; front faces +X, origin on the ground at the middle of the footprint."""
import math
import numpy as np
import bmesh
import isle_props as P
from isle_props import bbox, lathe, sweep, prism, poly_round


class Frame:
    """Local frame on a wall: u along the wall, n outward, z up. Builds bmesh boxes in that frame."""
    def __init__(s, o, u, n): s.o = np.asarray(o, float); s.u = np.asarray(u, float); s.n = np.asarray(n, float); s.z = np.array([0, 0, 1.0])

    def w(s, u, n, z): return s.o + s.u * u + s.n * n + s.z * z

    def rect(s, u0, u1, n, z0, z1, face=1):
        """Single quad in the plane n = const, facing +n (face=1) or -n."""
        bm = bmesh.new(); C = [bm.verts.new(tuple(s.w(u, n, z))) for (u, z) in ((u0, z0), (u1, z0), (u1, z1), (u0, z1))]
        f = bm.faces.new(C if face > 0 else C[::-1]); f.normal_update()
        if np.dot(np.asarray(f.normal[:]), s.n) * face < 0: f.normal_flip()
        return bm

    def quad(s, A, B, Cc, D):
        bm = bmesh.new(); bm.faces.new([bm.verts.new(tuple(s.w(*p))) for p in (A, B, Cc, D)]); return bm

    def fin(s, u0, u1, n0, n1, z0, z1):
        """Front and two side faces of a slim box (mullions): the back, top and bottom are never seen."""
        return s.box(u0, u1, n0, n1, z0, z1, keep=(3, 4, 5))

    def box(s, u0, u1, n0, n1, z0, z1, keep=None, back=True):
        bm = bmesh.new(); C = [bm.verts.new(tuple(s.w(u, n, z))) for z in (z0, z1) for n in (n0, n1) for u in (u0, u1)]
        for k, f in enumerate(((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))):
            if (keep is not None and k not in keep) or (not back and k == 2): continue
            bm.faces.new([C[i] for i in f])
        cen = np.mean([v.co[:] for v in C], 0)
        for f in bm.faces:
            f.normal_update()
            if np.dot(np.asarray(f.normal[:]), np.asarray(f.calc_center_median()[:]) - cen) < 0: f.normal_flip()
        return bm


def walls(K, M, F, length, z0, z1, holes, col, t=0.28, mat=None, uv='box', uvs=2.6):
    """Solid wall from u=-length/2..length/2, outer face at n=0, with rectangular holes [(u0, u1, hz0, hz1)]."""
    """Built from faces, not boxes: the outer face around the openings, reveals lining each opening, end and top caps."""
    mat = mat or M['plaster']
    br = sorted(set([-length / 2, length / 2] + [min(max(v, -length / 2), length / 2) for h in holes for v in h[:2]]))
    import bmesh
    bm = bmesh.new(); vq = lambda u, n, z: bm.verts.new(tuple(F.w(u, n, z)))
    def quad(p, want):
        f = bm.faces.new([vq(*q) for q in p]); f.normal_update(); w = F.u * want[0] + F.n * want[1] + F.z * want[2]
        if np.dot(np.asarray(f.normal[:]), w) < 0: f.normal_flip()
    for u0, u1 in zip(br[:-1], br[1:]):
        if u1 - u0 < 1e-4: continue
        hz = sorted((h0, h1) for (a, b, h0, h1) in holes if a <= u0 + 1e-4 and b >= u1 - 1e-4); zz = z0
        for (h0, h1) in hz:
            if h0 > zz + 1e-3: quad([(u0, 0, zz), (u1, 0, zz), (u1, 0, h0), (u0, 0, h0)], (0, 1, 0))
            zz = max(zz, h1)
        if zz < z1 - 1e-3: quad([(u0, 0, zz), (u1, 0, zz), (u1, 0, z1), (u0, 0, z1)], (0, 1, 0))
    for (a, b, h0, h1) in holes:                                                              # reveals, facing into the opening
        a, b = max(a, -length / 2), min(b, length / 2)
        quad([(a, 0, h0), (a, -t, h0), (a, -t, h1), (a, 0, h1)], (1, 0, 0)); quad([(b, 0, h0), (b, 0, h1), (b, -t, h1), (b, -t, h0)], (-1, 0, 0))
        if h1 < z1 - 1e-3: quad([(a, 0, h1), (a, -t, h1), (b, -t, h1), (b, 0, h1)], (0, 0, -1))
        if h0 > z0 + 1e-3: quad([(a, 0, h0), (b, 0, h0), (b, -t, h0), (a, -t, h0)], (0, 0, 1))
    L2 = length / 2
    quad([(-L2, 0, z0), (-L2, 0, z1), (-L2, -t, z1), (-L2, -t, z0)], (-1, 0, 0)); quad([(L2, 0, z0), (L2, -t, z0), (L2, -t, z1), (L2, 0, z1)], (1, 0, 0))
    quad([(-L2, 0, z1), (L2, 0, z1), (L2, -t, z1), (-L2, -t, z1)], (0, 0, 1))
    K.obj(bm, mat, col, uv, uvs, 0.0, smooth=False)


def window(K, M, F, uc, z0, w, h, shut=None, trim=(0.93, 0.92, 0.88), t=0.28):
    a, b = uc - w / 2, uc + w / 2; fr = 0.07; inset = -0.12
    for (u0, u1, zz0, zz1) in ((a, a + fr, z0, z0 + h), (b - fr, b, z0, z0 + h), (a, b, z0, z0 + fr), (a, b, z0 + h - fr, z0 + h)):
        K.obj(F.box(u0, u1, inset - 0.07, inset, zz0, zz1), M['smooth'], trim, 'box', 1.0, 0.008, 1)
    K.obj(F.box(uc - 0.025, uc + 0.025, inset - 0.06, inset - 0.01, z0 + fr, z0 + h - fr), M['smooth'], trim)              # mullion
    K.obj(F.box(a + fr, b - fr, inset - 0.06, inset - 0.01, z0 + h * 0.62, z0 + h * 0.62 + 0.045), M['smooth'], trim)       # transom
    K.obj(F.box(a + fr, b - fr, inset - 0.05, inset - 0.04, z0 + fr, z0 + h - fr), M['winglass'], (1, 1, 1), 'box', 1.0)     # pane
    K.obj(F.box(a + fr, b - fr, -t + 0.02, -t + 0.04, z0 + fr, z0 + h - fr), M['smooth'], (0.12, 0.11, 0.1))               # dark room behind
    K.obj(F.box(a - 0.06, b + 0.06, -0.16, 0.06, z0 - 0.07, z0), M['stone'], (0.95, 0.93, 0.88), 'box', 1.2, 0.012, 2)        # sill
    K.obj(F.box(a - 0.08, b + 0.08, -0.02, 0.025, z0 + h, z0 + h + 0.16), M['stone'], (0.95, 0.93, 0.88), 'box', 1.2, 0.01, 1)  # lintel
    if shut is not None:
        for sg in (-1, 1):
            u0 = (a - w / 2 - 0.02) if sg < 0 else (b + 0.02); u1 = u0 + w / 2
            K.obj(F.box(u0, u1, 0.0, 0.035, z0, z0 + h), M['pwood'], shut, 'box', 1.0, 0.008, 1)
            for k in range(int(h / 0.09)):                                                    # louvres
                zz = z0 + 0.06 + k * 0.09
                if zz > z0 + h - 0.08: break
                K.obj(F.box(u0 + 0.05, u1 - 0.05, 0.035, 0.05, zz, zz + 0.05), M['pwood'], np.asarray(shut) * 0.9)


def door(K, M, F, uc, z0, w=1.0, h=2.15, col=(0.42, 0.22, 0.14), canopy=True):
    a, b = uc - w / 2, uc + w / 2
    for (u0, u1, zz0, zz1) in ((a - 0.1, a, z0, z0 + h + 0.1), (b, b + 0.1, z0, z0 + h + 0.1), (a, b, z0 + h, z0 + h + 0.1)):
        K.obj(F.box(u0, u1, -0.04, 0.04, zz0, zz1), M['stone'], (0.93, 0.9, 0.85), 'box', 1.2, 0.01, 1)
    K.obj(F.box(a, b, -0.16, -0.1, z0, z0 + h), M['pwood'], col, 'box', 1.0, 0.006, 1)
    for zz in (0.25, 1.2):                                                                    # raised panels
        for uu in (a + 0.12, uc + 0.05):
            K.obj(F.box(uu, uu + w / 2 - 0.17, -0.1, -0.08, z0 + zz, z0 + zz + 0.8), M['pwood'], np.asarray(col) * 1.08, 'box', 1.0, 0.01, 2)
    K.obj(sweep([tuple(F.w(b - 0.15, -0.08, z0 + 1.0)), tuple(F.w(b - 0.15, -0.0, z0 + 1.0)), tuple(F.w(b - 0.28, 0.0, z0 + 1.0))], 0.012, 6), M['galv'], (1.0, 0.85, 0.5))
    K.obj(F.box(a - 0.3, b + 0.3, 0.0, 0.42, z0 - 0.18, z0), M['stone'], (0.9, 0.88, 0.84), 'box', 1.2, 0.015, 2)            # step
    if canopy:
        K.obj(F.box(a - 0.35, b + 0.35, 0.0, 0.7, z0 + h + 0.22, z0 + h + 0.3), M['roof'], (0.75, 0.42, 0.3), 'roof', 1.6, 0.01, 1)
        for uu in (a - 0.25, b + 0.25):
            K.obj(sweep([tuple(F.w(uu, 0.0, z0 + h - 0.25)), tuple(F.w(uu, 0.5, z0 + h + 0.2))], 0.03, 6), M['pwood'], (0.95, 0.94, 0.9))


def gable_roof(K, M, W, D, zt, rise, roofcol, wallcol, ov=0.45, t=0.18, ridge_along='y', roofmat=None, gmat=None, guv='box', ruvs=1.7, trim=(0.9, 0.89, 0.85)):
    roofmat = roofmat or M['roof']; gmat = gmat or M['plaster']
    """Gable roof over a W (along y) x D (along x) box; ridge along y (eaves on the front and back) or along x."""
    if ridge_along == 'x':                                                                    # build as if ridge along y, then swap axes
        bm_list = []; tmp = P.Part(); gable_roof(tmp, M, D, W, zt, rise, roofcol, wallcol, ov, t, 'y', roofmat, gmat, guv, ruvs, trim)
        for it in tmp.objs:
            if it[0] == 'raw':
                _, P_, T_, N_, *rest = it; K.objs.append(('raw', P_[:, [1, 0, 2]], T_[:, ::-1], N_[:, [1, 0, 2]], *rest)); continue
            o, mat, col, uv, uvs, sign = it; me = o.data
            for v in me.vertices: x, y, z = v.co; v.co = (y, x, z)
            me.flip_normals() if hasattr(me, 'flip_normals') else None
            K.objs.append((o, mat, col, uv, uvs, sign))
        return
    hx = D / 2; hy = W / 2 + ov * 0.6; slope = rise / hx; ex = hx + ov; ez = zt - ov * slope
    for sg in (-1, 1):                                                                        # roof slabs
        out = [(0, zt + rise + t / math.cos(math.atan(slope)) * 0.5), (sg * ex, ez + t * 0.5), (sg * ex, ez - t * 0.5), (0, zt + rise - t * 0.5)]
        out = [(sg * ex, ez + t * 0.5), (0, zt + rise + t * 0.6), (0, zt + rise - t * 0.4), (sg * ex, ez - t * 0.5)]
        bm = prism([(x, z) for x, z in out], -hy, hy, axis='x')
        for v in bm.verts: a, b, c = v.co; v.co = (b, a, c)
        K.obj(bm, roofmat, roofcol, 'roof', ruvs, 0.01, 1, 20)
        for k in range(int(hy * 2 / 0.6) + 1):                                                # rafter tails under the eave
            yy = -hy + 0.3 + k * 0.6
            if yy > hy - 0.2: break
            K.obj(bbox(sg * (hx + ov * 0.45), yy, ez + 0.1 + ov * 0.55 * slope - 0.15, ov * 0.9, 0.07, 0.12), M['pwood'], (0.55, 0.42, 0.32))
        K.obj(bbox(sg * (ex + 0.02), 0, ez - 0.12, 0.04, hy * 2 + 0.05, 0.2), M['pwood'], trim, 'box', 1.0, 0.008, 1)    # fascia
        g = lathe([(0.075, 0.0), (0.075, hy * 2 + 0.1)], 12, a0=np.pi, a1=2 * np.pi, close_top=False, close_bottom=False)       # half-round gutter
        bmesh.ops.solidify(g, geom=g.faces[:], thickness=0.008)
        for v in g.verts: x, y, z = v.co; v.co = (sg * (ex + 0.1) + x, z - hy - 0.05, ez - 0.12 + y)
        K.obj(g, M['galv'], (0.7, 0.72, 0.74))
        for yy in (-hy + 0.15, hy - 0.15):                                                    # downpipes
            K.obj(sweep([(sg * (ex + 0.1), yy, ez - 0.2), (sg * (hx + 0.12), yy, ez - 0.5), (sg * (hx + 0.08), yy, 0.35), (sg * (hx + 0.2), yy, 0.08)], 0.045, 8), M['galv'], (0.7, 0.72, 0.74))
    for sy in (-1, 1):                                                                        # gable walls and barge boards
        tri = prism([(-hx, zt), (hx, zt), (0, zt + rise)], sy * W / 2 - (0.28 if sy > 0 else 0) , sy * W / 2 + (0.0 if sy > 0 else 0.28), axis='x')
        for v in tri.verts: a, b, c = v.co; v.co = (b, a, c)
        K.obj(tri, gmat, wallcol, guv, 2.6)
        for sg in (-1, 1):
            p0 = (sg * ex, sy * (hy + 0.02), ez + 0.05); p1 = (0, sy * (hy + 0.02), zt + rise + t * 0.6)
            K.obj(sweep([p0, p1], 0.0, 4) if False else _board(p0, p1, 0.04, 0.24), M['pwood'], (0.9, 0.89, 0.85), 'box', 1.0, 0.008, 1)
    ridge = lathe([(0.13, -hy - 0.05), (0.13, hy + 0.05)], 10, a0=0, a1=np.pi, close_top=False, close_bottom=False)
    bmesh.ops.solidify(ridge, geom=ridge.faces[:], thickness=0.02)
    for v in ridge.verts: x, y, z = v.co; v.co = (x, z, zt + rise + t * 0.5 + y)
    K.obj(ridge, roofmat, np.asarray(roofcol) * 0.85, 'roof', ruvs)


def _board(p0, p1, th, wd):
    """Flat board between two points in a vertical plane (barge board)."""
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float); d = p1 - p0; L = np.linalg.norm(d); d /= L
    side = np.array([0, 1.0, 0]); up = np.cross(side, d); up /= np.linalg.norm(up)
    if up[2] < 0: up = -up
    bm = bmesh.new(); C = [bm.verts.new(tuple(p0 + d * a + side * b + up * c)) for c in (-wd, 0.02) for b in (-th / 2, th / 2) for a in (-0.05, L + 0.05)]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)): bm.faces.new([C[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return bm


def _board_any(p0, p1, nrm, th, wd):
    """Flat board from p0 to p1 lying in a wall plane whose outward normal is nrm (thickness along nrm, width in-plane)."""
    import bmesh
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float); d = p1 - p0; L = np.linalg.norm(d); d /= L; n = np.asarray(nrm, float); w = np.cross(n, d)
    bm = bmesh.new(); C = [bm.verts.new(tuple(p0 + d * a + n * b + w * c)) for c in (-wd / 2, wd / 2) for b in (0, th) for a in (0, L)]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)): bm.faces.new([C[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return bm


def chimney(K, M, x, y, zbase, ztop):
    K.obj(bbox(x, y, (zbase + ztop) / 2, 0.7, 0.55, ztop - zbase), M['stone'], (0.85, 0.8, 0.74), 'box', 1.0, 0.015, 2)
    K.obj(bbox(x, y, ztop + 0.05, 0.86, 0.7, 0.1), M['stone'], (0.92, 0.9, 0.86), 'box', 1.0, 0.012, 2)
    for o in (-0.15, 0.15): K.obj(lathe([(0.09, 0), (0.08, 0.25), (0.095, 0.28), (0.07, 0.3)], 12, x, y + o, ztop + 0.1, close_top=False), M['paint'], (0.75, 0.4, 0.28))


def plinth(K, M, W, D, h=0.45):
    K.obj(bbox(0, 0, h / 2 - 0.1, D + 0.08, W + 0.08, h + 0.2), M['stone'], (0.8, 0.78, 0.74), 'box', 1.4, 0.015, 2)


def house(K, M, W=9.0, D=7.0, floors=1, fh=2.9, rise=2.6, wall=(0.96, 0.92, 0.84), roof=(0.82, 0.44, 0.3), shut=(0.35, 0.5, 0.42), porch=False, balcony=False, ridge='y', chim=True, front_door=0.0):
    z0 = 0.45; zt = z0 + floors * fh
    plinth(K, M, W, D)
    fronts = [(Frame((D / 2, 0, 0), (0, 1, 0), (1, 0, 0)), W), (Frame((-D / 2, 0, 0), (0, -1, 0), (-1, 0, 0)), W), (Frame((0, W / 2, 0), (-1, 0, 0), (0, 1, 0)), D), (Frame((0, -W / 2, 0), (1, 0, 0), (0, -1, 0)), D)]
    for k, (F, Ln) in enumerate(fronts):
        nwin = max(1, int((Ln - 1.0) / 2.4)); us = [(-Ln / 2 + (i + 0.5) * Ln / nwin) for i in range(nwin)]; holes = []; items = []
        di = int(np.argmin([abs(q - front_door) for q in us]))
        for f in range(floors):
            zb = z0 + f * fh
            for i, uc in enumerate(us):
                if k == 0 and f == 0 and i == di:
                    holes.append((uc - 0.55, uc + 0.55, zb, zb + 2.25)); dcol = uc; items.append(('door', uc, zb)); continue
                if k >= 2 and f == 0 and i == nwin // 2 and Ln < 7.5: continue
                wz = zb + 0.95; wh = min(1.4, fh - 1.25); hw_ = 0.55 if (k == 0 and i == di) else 0.5
                holes.append((uc - hw_, uc + hw_, wz, wz + wh)); items.append(('win', uc, wz, wh, hw_ * 2))
        walls(K, M, F, Ln + (0.0 if k < 2 else -0.56), z0, zt, [(a, b, c, d) for a, b, c, d in holes if abs(a) < Ln / 2], wall)
        for it in items:
            if it[0] == 'door': door(K, M, F, it[1], it[2], 1.1 if not porch else 1.0, 2.25, canopy=not porch)
            else: window(K, M, F, it[1], it[2], it[4], it[3], shut if k < 2 or floors == 1 else None)
        if floors > 1: K.obj(F.box(-Ln / 2 - 0.02, Ln / 2 + 0.02, -0.02, 0.03, z0 + fh - 0.12, z0 + fh), M['stone'], (0.95, 0.93, 0.88), 'box', 1.2, 0.006, 1)  # floor band
    K.obj(bbox(0, 0, zt - 0.1, D - 0.3, W - 0.3, 0.2), M['plaster'], wall)                      # ceiling slab closes the box under the roof
    for (sx, sy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):                                     # corner quoins
        for q in range(int((zt - z0) / 0.5)):
            zz = z0 + 0.05 + q * 0.5; lw = 0.42 if q % 2 else 0.26
            K.obj(bbox(sx * (D / 2 + 0.012) - sx * lw / 2, sy * (W / 2 + 0.012) - sy * 0.13, zz + 0.2, lw, 0.26, 0.4), M['stone'], (0.93, 0.9, 0.84), 'box', 1.0, 0.012, 2)
    gable_roof(K, M, W, D, zt, rise, roof, wall, ridge_along=ridge)
    if chim: chimney(K, M, -D * 0.18, W * 0.28, zt + rise * 0.4, zt + rise + 0.8)
    if porch:                                                                                 # front porch: deck, posts, lean-to roof
        K.obj(bbox(D / 2 + 1.0, front_door, 0.3, 2.0, 3.6, 0.3), M['wood'], (0.9, 0.8, 0.7), 'box', 1.0, 0.01, 1)
        for yy in (front_door - 1.65, front_door + 1.65):
            K.obj(bbox(D / 2 + 1.85, yy, 1.55, 0.16, 0.16, 2.3), M['pwood'], (0.95, 0.94, 0.9), 'box', 1.0, 0.012, 2)
        pr = prism([(D / 2, z0 + fh - 0.1), (D / 2 + 2.25, z0 + fh - 0.55), (D / 2 + 2.25, z0 + fh - 0.68), (D / 2, z0 + fh - 0.23)], front_door - 1.95, front_door + 1.95, axis='x')
        for v in pr.verts: a, b, c = v.co; v.co = (b, a, c)
        K.obj(pr, M['roof'], roof, 'roof', 1.7, 0.01, 1)
    if balcony and floors > 1:
        zb = z0 + fh; K.obj(bbox(D / 2 + 0.5, front_door, zb - 0.06, 1.0, 2.6, 0.12), M['stone'], (0.92, 0.9, 0.85), 'box', 1.0, 0.012, 2)
        for yy in np.linspace(front_door - 1.25, front_door + 1.25, 11): K.obj(lathe([(0.016, 0), (0.016, 0.95)], 6, D / 2 + 0.96, yy, zb), M['iron'], (0.2, 0.2, 0.22))
        K.obj(sweep([(D / 2 + 0.02, front_door - 1.27, zb + 0.95), (D / 2 + 0.98, front_door - 1.27, zb + 0.95), (D / 2 + 0.98, front_door + 1.27, zb + 0.95), (D / 2 + 0.02, front_door + 1.27, zb + 0.95)], 0.025, 6), M['iron'], (0.2, 0.2, 0.22))


DESIGNS = {
    'house_cottage': dict(W=9.0, D=7.0, floors=1, rise=2.7, wall=(0.97, 0.94, 0.86), roof=(0.85, 0.42, 0.28), shut=(0.32, 0.5, 0.42)),
    'house_family': dict(W=10.0, D=8.0, floors=2, rise=2.9, wall=(0.93, 0.85, 0.7), roof=(0.7, 0.33, 0.22), shut=(0.5, 0.36, 0.25), balcony=True),
    'house_porch': dict(W=11.0, D=8.0, floors=1, rise=2.4, wall=(0.98, 0.97, 0.94), roof=(0.42, 0.44, 0.47), shut=(0.25, 0.35, 0.55), porch=True),
    'house_town': dict(W=7.0, D=9.0, floors=2, rise=3.2, wall=(0.9, 0.78, 0.66), roof=(0.78, 0.38, 0.25), shut=(0.95, 0.94, 0.9), ridge='x'),
    'house_farm': dict(W=12.0, D=8.5, floors=2, rise=3.4, wall=(0.95, 0.93, 0.88), roof=(0.55, 0.3, 0.22), shut=(0.4, 0.28, 0.2)),
}
FOOT = {k: (v['W'], v['D']) for k, v in DESIGNS.items()}
HEIGHT = {k: 0.45 + v['floors'] * 2.9 + v['rise'] for k, v in DESIGNS.items()}


def register():
    for k, kw in DESIGNS.items():
        P.PROPS[k] = (lambda K, M, kw=kw: house(K, M, **kw), {}); P.HEIGHT[k] = HEIGHT[k]

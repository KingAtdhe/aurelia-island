"""Art sheet 06: Aurelia harbour and coast. Painted timber fishing boats, white yachts, timber jetties, stone quays with iron bollards,
striped beach umbrellas, a lifeguard tower, a beach bar, breakwater tetrapods and channel buoys, and a seafront promenade.
Every piece faces +X, origin at the waterline / ground in the middle of the footprint, built with the street kit (isle_props)."""
import math
import numpy as np
import bmesh
import isle_props as P
from isle_props import bbox, lathe, sweep, prism

WHITE = (0.9, 0.9, 0.88); NAVY = (0.03, 0.07, 0.2); TEAL = (0.02, 0.3, 0.32); RED = (0.6, 0.04, 0.02); YELLOW = (0.85, 0.55, 0.05)
TIMBER = (0.3, 0.17, 0.08); DECK = (0.6, 0.42, 0.24); IRON = (0.04, 0.04, 0.045); ROPE = (0.7, 0.6, 0.42); STONE = (0.9, 0.78, 0.6)


def hull_mesh(L, B, D, fb, sheer=0.4, bow=0.18, transom=0.62, keel=0.12, st=24, sec=9, x0=0.0):
    """Smooth displacement hull: stations along x from stern (-L/2) to bow (+L/2), each a U section from keel to gunwale.
    B beam, D depth below the waterline, fb freeboard amidships, sheer rise at the ends, transom width fraction at the stern."""
    bm = bmesh.new(); rows = []
    for i in range(st + 1):
        t = i / st; x = x0 - L / 2 + L * t
        hw = B / 2 * (transom + (1 - transom) * math.sin(min(1.0, t / 0.45) * math.pi / 2)) if t < 0.55 else B / 2 * math.cos((t - 0.55) / 0.45 * math.pi / 2) ** 0.75
        hw = max(hw, 0.015); top = fb + sheer * ((2 * t - 1) ** 2) + (sheer * 0.6 * max(0.0, t - 0.75) / 0.25)
        dep = D * (1 - 0.65 * max(0.0, t - 0.7) / 0.3) * (0.85 + 0.15 * math.sin(t * math.pi))
        ring = []
        for k in range(sec + 1):
            a = -math.pi / 2 + math.pi * k / sec                                                       # from port gunwale round the keel to starboard
            y = hw * math.sin(a); c = max(0.0, math.cos(a))
            z = -dep * c ** 0.65 + top * (1 - c) ** 1.5
            if k == sec // 2 and sec % 2 == 0: z -= keel
            ring.append(bm.verts.new((x, y, z)))
        rows.append(ring)
    for i in range(st):
        for k in range(sec): bm.faces.new((rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1]))
    bm.faces.new(rows[0][::-1])                                                                        # transom
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def deck_mesh(L, B, fb, sheer, transom, x0=0.0, inset=0.06, st=24):
    """Flat-ish deck following the gunwale outline (a little below it, so the bulwark shows)."""
    bm = bmesh.new(); L_ = []; R_ = []
    for i in range(st + 1):
        t = i / st; x = x0 - L / 2 + L * t
        hw = B / 2 * (transom + (1 - transom) * math.sin(min(1.0, t / 0.45) * math.pi / 2)) if t < 0.55 else B / 2 * math.cos((t - 0.55) / 0.45 * math.pi / 2) ** 0.75
        hw = max(hw - inset, 0.01); z = fb + sheer * ((2 * t - 1) ** 2) + (sheer * 0.6 * max(0.0, t - 0.75) / 0.25) - 0.18
        L_.append(bm.verts.new((x, -hw, z))); R_.append(bm.verts.new((x, hw, z)))
    for i in range(st): bm.faces.new((L_[i], L_[i + 1], R_[i + 1], R_[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0: f.normal_flip()
    return bm


def stripe(K, M, L, B, fb, sheer, transom, z_off, col, x0=0.0, st=24, w=0.08):
    """Painted rubbing strake just under the gunwale on both sides."""
    for sg in (-1, 1):
        pts = []
        for i in range(st + 1):
            t = i / st; x = x0 - L / 2 + L * t
            hw = B / 2 * (transom + (1 - transom) * math.sin(min(1.0, t / 0.45) * math.pi / 2)) if t < 0.55 else B / 2 * math.cos((t - 0.55) / 0.45 * math.pi / 2) ** 0.75
            pts.append((x, sg * (hw + 0.01), fb + sheer * ((2 * t - 1) ** 2) + (sheer * 0.6 * max(0.0, t - 0.75) / 0.25) - z_off))
        K.obj(sweep(pts, w / 2, 5), M['pwood'], col)


# ------------------------------------------------------------------ 1 fishing boat
def fishing_boat(K, M, hullc=(0.03, 0.18, 0.4), trim=WHITE):
    """Adriatic timber fishing boat: painted hull with a contrasting strake, wheelhouse, mast with a derrick, nets and fish boxes."""
    L, B, D, fb, sh, tr = 9.5, 3.1, 0.8, 0.85, 0.35, 0.55
    K.obj(hull_mesh(L, B, D, fb, sh, transom=tr), M['pwood'], hullc, 'box', 1.0, 0.0, smooth=True, angle=70)
    K.obj(hull_mesh(L * 1.001, B * 1.005, D, 0.02, 0.0, transom=tr, st=24, sec=9), M['paint'], (0.35, 0.03, 0.02), 'box', 1.0, 0.0, smooth=True, angle=70) if False else None
    K.obj(deck_mesh(L, B, fb, sh, tr), M['planks'], DECK, 'box', 1.2)
    stripe(K, M, L, B, fb, sh, tr, 0.12, trim); stripe(K, M, L, B, fb, sh, tr, 0.9, (0.45, 0.04, 0.02), w=0.05)
    K.obj(bbox(-1.0, 0, fb + 0.85, 2.0, 1.7, 1.7), M['pwood'], WHITE, 'box', 1.0, 0.02, 2)                       # wheelhouse
    for y in (-0.86, 0.86):
        for x in (-1.5, -0.5): K.obj(bbox(x, y, fb + 1.2, 0.6, 0.02, 0.5), M['winglass'], (1, 1, 1))
    K.obj(bbox(0.01, 0, fb + 1.25, 0.02, 1.4, 0.55), M['winglass'], (1, 1, 1))
    K.obj(bbox(-1.0, 0, fb + 1.75, 2.3, 1.95, 0.1), M['pwood'], (0.6, 0.06, 0.04), 'box', 1.0, 0.01, 1)
    K.obj(sweep([(0.9, 0, fb), (0.9, 0, fb + 5.2)], 0.07, 8), M['wood'], (0.75, 0.62, 0.45))                    # mast and derrick
    K.obj(sweep([(0.9, 0, fb + 1.0), (3.4, 0, fb + 2.4)], 0.05, 6), M['wood'], (0.75, 0.62, 0.45))
    K.obj(sweep([(0.9, 0, fb + 5.0), (4.4, 0, fb + 0.4)], 0.008, 4), M['plastic'], ROPE); K.obj(sweep([(0.9, 0, fb + 5.0), (-4.5, 0, fb + 0.6)], 0.008, 4), M['plastic'], ROPE)
    for sg in (-1, 1): K.obj(sweep([(0.9, 0, fb + 4.6), (0.9, sg * 1.45, fb + 0.1)], 0.008, 4), M['plastic'], ROPE)
    K.obj(lathe([(0.0, 0.0), (0.09, 0.02), (0.07, 0.18), (0.0, 0.2)], 10, 0.9, 0, fb + 5.2), M['lens'], (1.0, 0.9, 0.6))
    rng = np.random.default_rng(3)
    for k in range(5):                                                                                       # nets heaped on the aft deck
        K.obj(lathe([(0.0, 0.0), (0.45, 0.05), (0.38, 0.25), (0.0, 0.35)], 10, -3.2 + rng.uniform(-0.3, 0.3), rng.uniform(-0.6, 0.6), fb - 0.15), M['fabric'], (0.12, 0.3, 0.32) if k % 2 else (0.55, 0.15, 0.08), 'cyl', 0.5)
    for k in range(4): K.obj(bbox(1.9 + (k % 2) * 0.62, -0.5 + (k // 2) * 0.62, fb - 0.02 + 0.13, 0.6, 0.42, 0.26), M['plastic'], (0.75, 0.75, 0.72) if k % 3 else (0.1, 0.35, 0.6), 'box', 1.0, 0.02, 1)
    for x in (-3.0, 3.5):                                                                                    # tyre fenders over the side
        for sg in (-1, 1):
            hw = B / 2 * 0.95
            t = lathe([(0.18, -0.08), (0.28, -0.1), (0.3, 0.0), (0.28, 0.1), (0.18, 0.08)], 12)
            for v in t.verts: a, b, c = v.co; v.co = (x + a, sg * (hw + 0.1) + c, fb - 0.55 + b)
            K.obj(t, M['concrete'], (0.04, 0.04, 0.04), 'cyl', 1.0)
    K.obj(lathe([(0.0, 0.0), (0.12, 0.0), (0.12, 0.3), (0.0, 0.3)], 8, -4.45, 0.0, fb + 0.1), M['iron'], IRON)


# ------------------------------------------------------------------ 2 sailing yacht
def sail_yacht(K, M):
    """12 m sloop: white GRP hull with a navy boot stripe, teak deck, coachroof with ports, cockpit and twin wheels, tall mast, furled main, rigging."""
    L, B, D, fb, sh, tr = 12.0, 3.8, 0.7, 1.05, 0.25, 0.85
    K.obj(hull_mesh(L, B, D, fb, sh, bow=0.1, transom=tr, keel=0.02), M['smooth'], WHITE, 'box', 1.0, 0.0, smooth=True, angle=70)
    stripe(K, M, L, B, fb, sh, tr, 0.95, NAVY, w=0.12); stripe(K, M, L, B, fb, sh, tr, 0.12, (0.6, 0.6, 0.62), w=0.05)
    K.obj(deck_mesh(L, B, fb, sh, tr, inset=0.08), M['planks'], (0.7, 0.5, 0.3), 'box', 0.8)
    cr = prism([(-1.2, -1.1), (2.6, -0.9), (3.6, -0.3), (3.6, 0.3), (2.6, 0.9), (-1.2, 1.1)], fb - 0.1, fb + 0.5)                # coachroof
    K.obj(cr, M['smooth'], WHITE, 'box', 1.0, 0.04, 2)
    for x in (0.0, 1.0, 2.0):
        for sg in (-1, 1): K.obj(bbox(x, sg * 1.0, fb + 0.3, 0.5, 0.02, 0.14), M['winglass'], (1, 1, 1))
    K.obj(bbox(-3.0, 0, fb - 0.05, 3.0, 2.6, 0.1), M['planks'], (0.7, 0.5, 0.3))                                  # cockpit sole and benches
    for sg in (-1, 1): K.obj(bbox(-3.0, sg * 1.25, fb + 0.25, 3.0, 0.4, 0.5), M['smooth'], WHITE, 'box', 1.0, 0.03, 2)
    for sg in (-1, 1):
        w_ = lathe([(0.45, -0.02), (0.47, 0.0), (0.45, 0.02)], 18)
        for v in w_.verts: a, b, c = v.co; v.co = (-4.4 + c, sg * 0.6 + a, fb + 0.55 + b)
        K.obj(w_, M['galv'], (0.8, 0.8, 0.82))
        K.obj(sweep([(-4.4, sg * 0.6, fb + 0.55), (-4.4, sg * 0.6, fb - 0.05)], 0.04, 6), M['galv'], (0.8, 0.8, 0.82))
    K.obj(sweep([(1.2, 0, fb + 0.5), (1.2, 0, fb + 16.5)], 0.09, 8), M['galv'], (0.78, 0.8, 0.82))                 # mast, spreaders, boom
    for z in (6.5, 11.5): K.obj(sweep([(1.2, -1.2, fb + z), (1.2, 1.2, fb + z)], 0.035, 6), M['galv'], (0.78, 0.8, 0.82))
    K.obj(sweep([(1.2, 0, fb + 2.0), (-4.2, 0, fb + 2.0)], 0.07, 8), M['galv'], (0.78, 0.8, 0.82))
    K.obj(sweep([(1.0, 0, fb + 2.15), (-3.9, 0, fb + 2.15)], 0.22, 10), M['fabric'], (0.12, 0.2, 0.36), 'box', 1.0)      # sail cover on the boom
    for p0 in ((5.9, 0, fb + 0.2), (-5.9, 0, fb + 0.3), (1.2, -1.75, fb + 0.1), (1.2, 1.75, fb + 0.1)):
        K.obj(sweep([p0, (1.2, 0, fb + 16.3)], 0.006, 4), M['galv'], (0.7, 0.7, 0.72))
    for sg in (-1, 1):                                                                                     # guard rails on stanchions
        pts = []
        for k in range(9):
            x = -5.3 + k * 1.3; t = (x + L / 2) / L; hw = B / 2 * (tr + (1 - tr) * math.sin(min(1.0, t / 0.45) * math.pi / 2)) if t < 0.55 else B / 2 * math.cos((t - 0.55) / 0.45 * math.pi / 2) ** 0.75
            z = fb + sh * ((2 * t - 1) ** 2); pts.append((x, sg * (hw - 0.08), z + 0.65)); K.obj(sweep([(x, sg * (hw - 0.08), z - 0.05), (x, sg * (hw - 0.08), z + 0.65)], 0.015, 4), M['galv'], (0.8, 0.8, 0.82))
        K.obj(sweep(pts, 0.008, 4), M['galv'], (0.8, 0.8, 0.82))
    K.obj(sweep([(5.9, 0, fb + 0.4), (6.3, 0, fb + 0.45)], 0.05, 6), M['galv'], (0.8, 0.8, 0.82))
    K.obj(lathe([(0.0, -0.3), (0.35, -0.2), (0.35, 0.2), (0.0, 0.3)], 12, 5.9, 0, fb + 0.65), M['fabric'], (0.12, 0.2, 0.36))      # furled genoa drum


# ------------------------------------------------------------------ 3 motor yacht
def motor_yacht(K, M):
    """15 m flybridge cruiser: sharp white hull, dark glazing bands, flybridge with a bimini, swim platform, chrome rails."""
    L, B, D, fb, sh, tr = 15.0, 4.6, 0.9, 1.5, 0.35, 0.92
    K.obj(hull_mesh(L, B, D, fb, sh, transom=tr, keel=0.15), M['smooth'], WHITE, 'box', 1.0, 0.0, smooth=True, angle=70)
    for sg in (-1, 1):                                                                                       # long dark hull window band
        K.obj(prism([(-3.0, fb - 0.45), (3.4, fb - 0.35), (3.6, fb - 0.2), (-3.0, fb - 0.2)], sg * (B / 2 - 0.02), sg * (B / 2 + 0.02), axis='x') if False else bbox(0.0, sg * (B / 2 - 0.0), fb - 0.35, 6.0, 0.03, 0.22), M['winglass'], (1, 1, 1))
    K.obj(deck_mesh(L, B, fb, sh, tr, inset=0.1), M['planks'], (0.7, 0.5, 0.3), 'box', 0.8)
    sup = prism([(-6.0, -2.0), (1.5, -2.0), (3.8, -1.2), (4.2, 0.0), (3.8, 1.2), (1.5, 2.0), (-6.0, 2.0)], fb - 0.2, fb + 1.9)     # superstructure
    K.obj(sup, M['smooth'], WHITE, 'box', 1.0, 0.05, 2)
    for sg in (-1, 1): K.obj(bbox(-1.0, sg * 2.01, fb + 1.0, 7.0, 0.02, 0.9), M['winglass'], (1, 1, 1))
    K.obj(prism([(3.0, -1.5), (4.15, 0.0), (3.0, 1.5)], fb + 0.9, fb + 1.85), M['winglass'], (1, 1, 1))
    K.obj(prism([(-5.5, -1.9), (0.5, -1.9), (2.0, -1.0), (2.0, 1.0), (0.5, 1.9), (-5.5, 1.9)], fb + 1.9, fb + 2.15), M['smooth'], WHITE, 'box', 1.0, 0.03, 1)    # flybridge deck
    for (x, y) in ((-5.0, -1.7), (-5.0, 1.7), (-1.0, -1.7), (-1.0, 1.7)): K.obj(sweep([(x, y, fb + 2.15), (x, y, fb + 4.0)], 0.03, 6), M['galv'], (0.85, 0.85, 0.87))
    K.obj(bbox(-3.0, 0, fb + 4.0, 4.4, 3.6, 0.08), M['fabric'], (0.12, 0.2, 0.36), 'box', 1.0, 0.02, 1)
    K.obj(sweep([(-0.4, 0, fb + 2.15), (0.0, 0, fb + 4.6)], 0.06, 6), M['smooth'], WHITE); K.obj(lathe([(0.0, 0.0), (0.3, 0.05), (0.0, 0.12)], 16, 0.0, 0, fb + 4.6), M['smooth'], WHITE)
    K.obj(bbox(-L / 2 - 0.6, 0, 0.35, 1.2, B * 0.85, 0.12), M['planks'], (0.7, 0.5, 0.3), 'box', 0.8, 0.01, 1)           # swim platform
    for sg in (-1, 1):
        pts = [(x, sg * (B / 2 * 0.86), fb + 0.65 + 0.1 * (x > 3)) for x in np.linspace(1.5, 6.6, 6)]
        K.obj(sweep(pts, 0.02, 5), M['galv'], (0.85, 0.85, 0.87))
        for p in pts: K.obj(sweep([(p[0], p[1], fb - 0.05), p], 0.015, 4), M['galv'], (0.85, 0.85, 0.87))


# ------------------------------------------------------------------ 4 rowing boat on the sand
def rowing_boat(K, M):
    """Clinker dinghy pulled up on the beach, tilted on its keel, oars across the thwarts, an anchor in the sand."""
    L, B, D, fb, sh, tr = 4.2, 1.5, 0.35, 0.45, 0.22, 0.5; Kp = P.Part()
    Kp.obj(hull_mesh(L, B, D, fb, sh, transom=tr, st=16, sec=7), M['pwood'], (0.85, 0.82, 0.74), 'box', 1.0, 0.0, smooth=True, angle=70)
    for z in (0.12, 0.32): stripe(Kp, M, L, B, fb, sh, tr, z, (0.08, 0.3, 0.45) if z < 0.2 else (0.75, 0.72, 0.65), st=16, w=0.035)
    Kp.obj(hull_mesh(L * 0.97, B * 0.9, D * 0.85, fb - 0.05, sh, transom=tr, st=16, sec=7), M['wood'], (0.55, 0.38, 0.22), 'box', 1.0, 0.0, smooth=True, angle=70)
    for x in (-0.9, 0.4): Kp.obj(bbox(x, 0, fb - 0.12, 0.22, B * 0.85, 0.05), M['wood'], (0.5, 0.35, 0.2))
    for sg in (-1, 1):
        Kp.obj(sweep([(-1.6, sg * 0.25, fb - 0.05), (1.6, sg * 0.35, fb - 0.04)], 0.025, 5), M['wood'], (0.75, 0.62, 0.45))
        Kp.obj(bbox(1.8, sg * 0.35, fb - 0.04, 0.5, 0.12, 0.015), M['wood'], (0.75, 0.62, 0.45))
    for it in Kp.objs:                                                                                       # lean it on the keel, resting on the sand
        rot = __import__('mathutils').Matrix.Rotation(0.18, 4, 'X'); tr_ = __import__('mathutils').Matrix.Translation((0, 0, D * 0.9))
        if it[0] == 'raw':
            _, Pq, T_, N_, *rest = it; R3 = np.array(rot.to_3x3()); K.objs.append(('raw', Pq @ R3.T + np.array([0, 0, D * 0.9]), T_, N_ @ R3.T, *rest))
        else: it[0].data.transform(tr_ @ rot); K.objs.append(it)
    K.obj(sweep([(2.1, 0.0, 0.5), (3.6, 0.3, 0.05)], 0.008, 4), M['plastic'], ROPE)
    K.obj(sweep([(3.6, 0.3, -0.1), (3.6, 0.3, 0.35)], 0.025, 5), M['iron'], IRON); K.obj(sweep([(3.35, 0.3, 0.0), (3.6, 0.3, -0.05), (3.85, 0.3, 0.0)], 0.02, 5), M['iron'], IRON)


# ------------------------------------------------------------------ 5 timber jetty
def jetty(K, M, Ln=18.0, W=2.6):
    """Timber jetty on driven piles: plank deck with gaps, stringers, cleats, a ladder, a lamp post with a lifebuoy."""
    for k in range(int(Ln / 3) + 1):
        x = -Ln / 2 + k * 3.0
        for sg in (-1, 1): K.obj(lathe([(0.15, -2.5), (0.15, 1.15), (0.13, 1.25), (0.0, 1.27)], 10, x, sg * (W / 2 - 0.1), 0), M['wood'], (0.35, 0.28, 0.2), 'cyl', 1.0)
        K.obj(bbox(x, 0, 0.75, 0.2, W + 0.2, 0.22), M['wood'], (0.4, 0.3, 0.2))
    for sg in (-1, 1): K.obj(bbox(0, sg * (W / 2 - 0.25), 0.92, Ln, 0.12, 0.2), M['wood'], (0.4, 0.3, 0.2))
    rng = np.random.default_rng(7); n = int(Ln / 0.17)
    for k in range(n): K.obj(bbox(-Ln / 2 + (k + 0.5) * Ln / n, 0, 1.05, Ln / n - 0.025, W, 0.06), M['planks'], tuple(np.array(DECK) * rng.uniform(0.75, 1.1)), 'box', 1.0, 0.004, 1)
    for x in (-6.0, 0.0, 6.0):                                                                                # cleats
        for sg in (-1, 1): K.obj(bbox(x, sg * (W / 2 - 0.2), 1.14, 0.35, 0.08, 0.06), M['iron'], IRON); K.obj(bbox(x, sg * (W / 2 - 0.2), 1.1, 0.08, 0.08, 0.06), M['iron'], IRON)
    for z in np.arange(-1.0, 1.0, 0.3): K.obj(bbox(Ln / 2 - 2, W / 2 + 0.1, z, 0.04, 0.5, 0.04), M['galv'], (0.6, 0.6, 0.6))   # ladder
    for o in (-0.25, 0.25): K.obj(sweep([(Ln / 2 - 2, W / 2 + 0.1 + o, -1.2), (Ln / 2 - 2, W / 2 + 0.1 + o, 1.9)], 0.025, 5), M['galv'], (0.6, 0.6, 0.6))
    K.obj(sweep([(Ln / 2 - 0.5, -W / 2 + 0.3, 1.05), (Ln / 2 - 0.5, -W / 2 + 0.3, 4.2)], 0.05, 8), M['iron'], (0.05, 0.15, 0.15))
    K.obj(lathe([(0.0, 0.0), (0.18, 0.05), (0.2, 0.35), (0.12, 0.45), (0.0, 0.5)], 8, Ln / 2 - 0.5, -W / 2 + 0.3, 4.2), M['lens'], (1.0, 0.9, 0.6))
    ring = lathe([(0.22, -0.06), (0.32, -0.08), (0.34, 0.0), (0.32, 0.08), (0.22, 0.06)], 16)
    for v in ring.verts: a, b, c = v.co; v.co = (Ln / 2 - 0.5 + 0.08, -W / 2 + 0.3 + a, 2.2 + b)
    K.obj(ring, M['smooth'], (0.85, 0.2, 0.05), 'cyl', 1.0)


# ------------------------------------------------------------------ 6 harbour quay
def quay(K, M, Ln=16.0):
    """Stone quay edge: big dressed coping blocks, cast-iron bollards with ropes, rubber fenders, a chain, fish crates and drying nets."""
    rng = np.random.default_rng(9); x = -Ln / 2
    while x < Ln / 2:
        l = rng.uniform(1.0, 1.6); K.obj(bbox(x + l / 2, 0, -0.5, l - 0.02, 2.5, 2.6), M['ashlar'], tuple(np.array(STONE) * rng.uniform(0.85, 1.05)), 'box', 1.4, 0.03, 2); x += l
    K.obj(bbox(0, -3.0, 0.6, Ln, 4.0, 0.2), M['concrete'], (0.6, 0.58, 0.55), 'box', 2.0)
    for xb in (-5.0, 3.0):                                                                                  # bollards
        K.obj(lathe([(0.0, 0.0), (0.28, 0.0), (0.24, 0.1), (0.17, 0.3), (0.2, 0.6), (0.28, 0.72), (0.0, 0.78)], 14, xb, -0.5, 0.8), M['iron'], IRON, 'cyl', 1.0)
        K.obj(sweep([(xb, -0.5, 1.2), (xb + 0.5, 0.6, 1.0), (xb + 2.0, 2.4, -0.2)], 0.035, 6), M['plastic'], ROPE)
    for xf in (-6.5, -2.0, 2.0, 6.5):                                                                      # fenders
        K.obj(bbox(xf, 1.3, -0.6, 0.4, 0.2, 1.8), M['concrete'], (0.04, 0.04, 0.04), 'box', 1.0, 0.04, 2)
    for k in range(9): K.obj(lathe([(0.04, -0.03), (0.06, 0.0), (0.04, 0.03)], 6, -3.5 + k * 0.12, 1.25, 0.6 - k * 0.15), M['iron'], (0.3, 0.12, 0.06))
    for k in range(6):                                                                                      # fish crates stacked
        K.obj(bbox(-1.0 + (k % 3) * 0.62, -2.6 + (k // 3) * 0.0, 0.85 + (k // 3) * 0.28, 0.6, 0.42, 0.26), M['plastic'], (0.1, 0.35, 0.6) if k % 2 else (0.75, 0.75, 0.72), 'box', 1.0, 0.02, 1)
    for k in range(4):                                                                                      # net heaps and an orange buoy
        K.obj(lathe([(0.0, 0.0), (0.6, 0.06), (0.5, 0.3), (0.0, 0.42)], 10, 4.5 + rng.uniform(-0.6, 0.6), -3.0 + rng.uniform(-0.8, 0.8), 0.7), M['fabric'], (0.12, 0.3, 0.32) if k % 2 else (0.55, 0.12, 0.05), 'cyl', 0.5)
    K.obj(lathe([(0.0, -0.2), (0.2, 0.0), (0.0, 0.2)], 12, 5.6, -2.0, 1.0), M['smooth'], (0.9, 0.3, 0.02))
    K.obj(lathe([(0.0, 0.0), (0.35, 0.0), (0.35, 1.0), (0.0, 1.0)], 14, -6.2, -3.5, 0.7), M['paint'], (0.2, 0.35, 0.45), 'cyl', 1.0)   # water barrel


def canopy_tri(a, b, c, t=0.012):
    """One fabric gore with both sides: two triangles a few mm apart."""
    bm = bmesh.new(); top = [bm.verts.new(p) for p in (a, b, c)]; bot = [bm.verts.new((p[0], p[1], p[2] - t)) for p in (a, b, c)]
    bm.faces.new(top); bm.faces.new(bot[::-1]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return bm


# ------------------------------------------------------------------ 7 beach set
def beach_set(K, M):
    """Three striped umbrellas with pairs of teak sun loungers, towels, a cool box and a beach bag."""
    cols = [((0.75, 0.05, 0.03), WHITE), ((0.03, 0.2, 0.45), WHITE), ((0.9, 0.55, 0.05), (0.03, 0.25, 0.3))]
    for i, (c1, c2) in enumerate(cols):
        y = -3.5 + i * 3.5
        K.obj(sweep([(0, y, -0.4), (0, y, 2.4)], 0.025, 6), M['wood'], (0.6, 0.45, 0.3))
        for k in range(10):
            a0 = k * 2 * math.pi / 10; a1 = (k + 1) * 2 * math.pi / 10; R_ = 1.45
            bm = canopy_tri((0, y, 2.55), (R_ * math.cos(a0), y + R_ * math.sin(a0), 2.15), (R_ * math.cos(a1), y + R_ * math.sin(a1), 2.15))
            K.obj(bm, M['fabric'], c1 if k % 2 else c2, 'box', 1.0, smooth=False)
            K.obj(bbox(R_ * math.cos((a0 + a1) / 2), y + R_ * math.sin((a0 + a1) / 2), 2.08, 0.02 + 0.6 * abs(math.sin((a0 + a1) / 2)), 0.02 + 0.6 * abs(math.cos((a0 + a1) / 2)), 0.14), M['fabric'], c1 if k % 2 else c2) if False else None
        for sg in (-1, 1):                                                                                    # loungers
            x0 = 1.3; yy = y + sg * 0.85
            K.obj(bbox(x0, yy, 0.3, 1.5, 0.62, 0.05), M['wood'], (0.6, 0.42, 0.25), 'box', 1.0, 0.01, 1)
            bk = prism([(0, 0), (0.65, 0.45), (0.65, 0.5), (0, 0.05)], yy - 0.31, yy + 0.31, axis='y') if False else None
            K.obj(bbox(x0 - 0.95, yy, 0.52, 0.06, 0.62, 0.62, 0.0), M['wood'], (0.6, 0.42, 0.25), 'box', 1.0, 0.01, 1)
            for (dx, dy) in ((-0.65, -0.27), (-0.65, 0.27), (0.65, -0.27), (0.65, 0.27)): K.obj(bbox(x0 + dx, yy + dy, 0.14, 0.05, 0.05, 0.28), M['wood'], (0.5, 0.35, 0.2))
            K.obj(bbox(x0 + 0.1, yy, 0.34, 1.3, 0.55, 0.02), M['fabric'], ((0.85, 0.75, 0.2), (0.1, 0.45, 0.55), (0.8, 0.25, 0.35))[(i + (sg > 0)) % 3])
    K.obj(bbox(2.6, 1.6, 0.2, 0.55, 0.38, 0.4), M['plastic'], (0.05, 0.3, 0.6), 'box', 1.0, 0.03, 2); K.obj(bbox(2.6, 1.6, 0.42, 0.57, 0.4, 0.06), M['smooth'], WHITE)
    K.obj(lathe([(0.0, 0.0), (0.25, 0.0), (0.22, 0.35), (0.0, 0.38)], 10, 2.4, -2.0, 0.0), M['fabric'], (0.85, 0.65, 0.3), 'cyl', 1.0)
    K.obj(lathe([(0.0, -0.13), (0.13, 0.0), (0.0, 0.13)], 12, 3.0, 0.3, 0.13), M['smooth'], (0.9, 0.85, 0.2))


# ------------------------------------------------------------------ 8 lifeguard tower
def lifeguard(K, M):
    """Raised timber lifeguard hut on splayed legs, ramp, red-and-white flag, rescue board and buoy, binocular rail."""
    h = 2.6
    for (x, y) in ((-1.1, -1.1), (-1.1, 1.1), (1.1, -1.1), (1.1, 1.1)): K.obj(sweep([(x * 1.25, y * 1.25, -0.3), (x, y, h)], 0.09, 6), M['wood'], (0.75, 0.68, 0.55))
    for z in (0.9,):
        for (a, b) in (((-1.2, -1.2), (1.2, -1.2)), ((1.2, -1.2), (1.2, 1.2)), ((1.2, 1.2), (-1.2, 1.2)), ((-1.2, 1.2), (-1.2, -1.2))): K.obj(sweep([(a[0], a[1], z), (b[0], b[1], z)], 0.04, 5), M['wood'], (0.75, 0.68, 0.55))
    K.obj(bbox(0, 0, h + 0.05, 3.0, 3.0, 0.12), M['planks'], (0.8, 0.72, 0.6), 'box', 1.0, 0.01, 1)
    K.obj(bbox(-0.4, 0, h + 1.1, 1.9, 2.2, 2.0), M['pwood'], (0.85, 0.85, 0.82), 'box', 1.0, 0.02, 2)
    for y in (-1.11, 1.11): K.obj(bbox(-0.4, y, h + 1.3, 1.2, 0.02, 0.7), M['winglass'], (1, 1, 1))
    K.obj(bbox(0.56, 0, h + 1.3, 0.02, 1.6, 0.8), M['winglass'], (1, 1, 1))
    for k in range(6): K.obj(bbox(-0.4, -1.2 + k * 0.48, h + 0.6, 1.95, 0.24, 0.9), M['pwood'], RED if k % 2 else WHITE) if False else None
    K.obj(bbox(-0.4, 0, h + 0.45, 1.95, 2.25, 0.5), M['pwood'], RED, 'box', 1.0, 0.01, 1)
    K.obj(prism([(-1.6, h + 2.05), (-0.4, h + 2.55), (0.8, h + 2.05), (0.8, h + 2.0), (-0.4, h + 2.5), (-1.6, h + 2.0)], -1.35, 1.35, axis='x') if False else bbox(-0.4, 0, h + 2.2, 2.4, 2.7, 0.12), M['pwood'], RED, 'box', 1.0, 0.02, 1)
    for sg in (-1, 1): K.obj(sweep([(1.45, sg * 1.45, h + 0.05), (1.45, sg * 1.45, h + 1.0)], 0.03, 5), M['wood'], (0.75, 0.68, 0.55))
    K.obj(sweep([(1.45, -1.45, h + 1.0), (1.45, 1.45, h + 1.0)], 0.03, 5), M['wood'], (0.75, 0.68, 0.55))
    ramp_n = 10
    for k in range(ramp_n):                                                                                  # ramp down the back
        t = k / ramp_n; K.obj(bbox(-1.6 - t * 4.0, 0, h - t * (h + 0.1), 0.38, 1.0, 0.06), M['planks'], (0.8, 0.72, 0.6), 'box', 1.0, 0.005, 1)
    K.obj(sweep([(-0.4, 1.3, h + 2.2), (-0.4, 1.3, h + 4.2)], 0.025, 5), M['galv'], (0.8, 0.8, 0.8))
    K.obj(bbox(-0.4, 1.6, h + 3.9, 0.02, 0.6, 0.4), M['fabric'], RED); K.obj(bbox(-0.41, 1.6, h + 3.8, 0.02, 0.6, 0.2), M['fabric'], WHITE)
    K.obj(bbox(1.9, 1.6, 1.0, 0.1, 0.55, 2.4, 0.15), M['smooth'], (0.9, 0.35, 0.05), 'box', 1.0, 0.05, 3)          # rescue board leaning on a leg
    ring = lathe([(0.22, -0.06), (0.32, -0.08), (0.34, 0.0), (0.32, 0.08), (0.22, 0.06)], 16)
    for v in ring.verts: a, b, c = v.co; v.co = (0.56 + c + 0.03, -0.6 + a, h + 1.0 + b)
    K.obj(ring, M['smooth'], (0.85, 0.2, 0.05), 'cyl', 1.0)


# ------------------------------------------------------------------ 9 beach bar
def beach_bar(K, M):
    """Timber beach bar with a reed-thatched roof, bamboo counter, stools, a chalkboard menu and string lights."""
    W, D = 6.0, 4.0
    K.obj(bbox(0, 0, 0.12, D + 2.5, W + 1.0, 0.24), M['planks'], DECK, 'box', 1.0, 0.01, 1)
    for (x, y) in ((-D / 2, -W / 2), (-D / 2, W / 2), (D / 2, -W / 2), (D / 2, W / 2), (D / 2 + 1.2, -W / 2), (D / 2 + 1.2, W / 2)):
        K.obj(lathe([(0.11, 0.0), (0.1, 3.0)], 8, x, y, 0.24), M['wood'], (0.6, 0.48, 0.3), 'cyl', 1.0)
    K.obj(bbox(-D / 2 + 0.05, 0, 1.5, 0.12, W, 2.6), M['planks'], (0.55, 0.42, 0.28), 'box', 1.0, 0.0)          # back wall with shelves
    for z in (1.4, 1.9): K.obj(bbox(-D / 2 + 0.35, 0, z, 0.4, W - 0.6, 0.04), M['wood'], (0.5, 0.36, 0.22))
    rng = np.random.default_rng(21)
    for z in (1.42, 1.92):
        for k in range(16): K.obj(lathe([(0.0, 0.0), (0.04, 0.0), (0.04, 0.18), (0.015, 0.26), (0.0, 0.3)], 6, -D / 2 + 0.35, -W / 2 + 0.6 + k * 0.32, z + 0.02), M['lens'], tuple(rng.uniform(0.1, 0.9, 3)))
    for k in range(int(W / 0.1)):                                                                            # bamboo-faced counter
        y = -W / 2 + 0.3 + k * 0.1
        if y > W / 2 - 0.3: break
        K.obj(lathe([(0.05, 0.0), (0.05, 1.05)], 6, D / 2 - 0.3, y, 0.24), M['wood'], (0.8, 0.7, 0.4), 'cyl', 1.0)
    K.obj(bbox(D / 2 - 0.3, 0, 1.33, 0.7, W - 0.4, 0.06), M['wood'], (0.55, 0.36, 0.2), 'box', 1.0, 0.01, 1)
    for k in range(5):
        y = -W / 2 + 0.9 + k * 1.05
        K.obj(lathe([(0.0, 0.0), (0.2, 0.0), (0.03, 0.05), (0.03, 0.72), (0.18, 0.75), (0.18, 0.8), (0.0, 0.8)], 10, D / 2 + 0.55, y, 0.24), M['wood'], (0.45, 0.32, 0.2), 'cyl', 1.0)
    for sg in (-1, 1):                                                                                       # thatched roof: layered reed fringes
        for k in range(9):                                                                                 # thatch: nine overlapping reed courses
            z = 3.2 + k * 0.15; o = (D / 2 + 1.9) * (1 - k * 0.1)
            sl = prism([(sg * o, z), (sg * (o - 1.0), z + 0.45), (sg * (o - 1.0), z + 0.38), (sg * o, z - 0.08)], -W / 2 - 0.8 + k * 0.1, W / 2 + 0.8 - k * 0.1, axis='x')
            for v in sl.verts: a, b, c = v.co; v.co = (b + 0.6, a, c)
            K.obj(sl, M['boards'], (0.62, 0.45, 0.2) if k % 2 else (0.5, 0.36, 0.15), 'boxv', 0.35, 0.0, smooth=False)
    K.obj(bbox(0.6, 0, 4.55, 0.5, W + 1.4, 0.25), M['fabric'], (0.28, 0.18, 0.07), 'box', 0.5, 0.05, 2)
    pts = [(D / 2 + 1.3, y, 3.0 - 0.25 * math.sin((y + W / 2) / W * math.pi * 3) ** 2) for y in np.linspace(-W / 2, W / 2, 25)]
    K.obj(sweep(pts, 0.006, 4), M['iron'], IRON)
    for p in pts[1::2]: K.obj(lathe([(0.0, 0.0), (0.04, 0.03), (0.0, 0.08)], 6, p[0], p[1], p[2] - 0.1), M['lens'], (1.0, 0.85, 0.5))
    K.obj(bbox(D / 2 + 2.2, -W / 2 + 0.4, 0.75, 0.05, 0.6, 0.9, 0.4), M['paint'], (0.12, 0.13, 0.12), 'box', 1.0, 0.01, 1)


# ------------------------------------------------------------------ 10 breakwater and buoys
def tetrapod(K, M, c, s, rng):
    """Concrete tetrapod: four tapered legs at tetrahedral angles."""
    dirs = [(0, 0, 1), (0.943, 0, -0.333), (-0.471, 0.816, -0.333), (-0.471, -0.816, -0.333)]
    R = __import__('mathutils').Euler(tuple(rng.uniform(0, 6.28, 3))).to_matrix(); col = tuple(np.array([0.72, 0.7, 0.66]) * rng.uniform(0.85, 1.05))
    for d in dirs:
        d_ = np.array(R @ __import__('mathutils').Vector(d)); bm = lathe([(0.42 * s, 0.0), (0.26 * s, 1.15 * s), (0.0, 1.2 * s)], 8)
        z = np.array([0, 0, 1.0]); v_ = np.cross(z, d_); sn = np.linalg.norm(v_); cth = float(np.dot(z, d_))
        if sn < 1e-6: Rm = np.eye(3) * (1 if cth > 0 else -1)
        else:
            vx = np.array([[0, -v_[2], v_[1]], [v_[2], 0, -v_[0]], [-v_[1], v_[0], 0]]); Rm = np.eye(3) + vx + vx @ vx * ((1 - cth) / sn ** 2)
        for v in bm.verts: v.co = tuple(np.asarray(c) + Rm @ np.asarray(v.co[:]))
        K.obj(bm, M['concrete'], col, 'box', 1.5, 0.0)


def breakwater(K, M):
    """Breakwater end: a jumble of concrete tetrapods on a rubble bank, a green starboard beacon, a red can buoy and a yellow mooring buoy."""
    rng = np.random.default_rng(31)
    for k in range(26):
        x = rng.uniform(-6, 4); y = rng.uniform(-2.5, 2.5); z = 0.4 + 1.2 * math.exp(-(y / 2.5) ** 2) * (1 if x < 2.5 else 0.6) + rng.uniform(-0.3, 0.3)
        tetrapod(K, M, (x, y, z), rng.uniform(0.85, 1.1), rng)
    K.obj(lathe([(0.0, 0.0), (0.7, 0.0), (0.6, 2.2), (0.0, 2.2)], 12, -3.0, 0, 1.6), M['concrete'], (0.75, 0.73, 0.7), 'cyl', 1.0)
    K.obj(lathe([(0.0, 0.0), (0.35, 0.0), (0.35, 2.4), (0.0, 2.4)], 12, -3.0, 0, 3.8), M['paint'], (0.03, 0.3, 0.1), 'cyl', 1.0)
    K.obj(lathe([(0.0, 0.0), (0.42, 0.05), (0.0, 0.7)], 12, -3.0, 0, 6.2), M['paint'], (0.03, 0.3, 0.1)); K.obj(lathe([(0.0, 0.0), (0.12, 0.0), (0.12, 0.3), (0.0, 0.3)], 10, -3.0, 0, 6.9), M['lens'], (0.2, 1.0, 0.3))
    for (x, y, col, h) in ((8.0, -3.0, (0.65, 0.03, 0.02), 1.6), (9.0, 4.0, YELLOW, 0.9)):
        K.obj(lathe([(0.0, -0.4), (0.55, -0.3), (0.6, 0.0), (0.45, h), (0.0, h + 0.05)], 14, x, y, 0.0), M['paint'], col, 'cyl', 1.0)
        K.obj(lathe([(0.0, 0.0), (0.62, 0.0), (0.62, 0.12), (0.0, 0.12)], 14, x, y, -0.05), M['concrete'], (0.04, 0.04, 0.04))


# ------------------------------------------------------------------ 11 seafront promenade
def promenade(K, M, Ln=14.0):
    """Promenade edge: limestone paving and sea wall coping, white-painted iron railing, double globe lamps, a bench and a palm planter."""
    K.obj(bbox(0, -2.0, 0.08, Ln, 4.0, 0.16), M['pave'] if 'pave' in M else M['stone'], (0.9, 0.85, 0.76), 'box', 2.0)
    K.obj(bbox(0, 0.15, -0.6, Ln, 0.5, 1.6), M['ashlar'], STONE, 'box', 1.4, 0.02, 2)
    K.obj(bbox(0, 0.15, 0.25, Ln, 0.6, 0.12), M['ashlar'], (1.0, 0.92, 0.8), 'box', 1.4, 0.015, 2)
    for k in range(int(Ln / 2) + 1):                                                                         # railing
        x = -Ln / 2 + k * 2.0
        K.obj(lathe([(0.0, 0.0), (0.06, 0.0), (0.04, 0.1), (0.03, 1.0), (0.05, 1.05), (0.0, 1.1)], 8, x, 0.0, 0.31), M['paint'], WHITE, 'cyl', 1.0)
        if k < int(Ln / 2):
            for z in (0.62, 1.0): K.obj(sweep([(x, 0, 0.31 + z), (x + 2.0, 0, 0.31 + z)], 0.022, 5), M['paint'], WHITE)
            for j in range(1, 8): K.obj(sweep([(x + j * 0.25, 0, 0.45), (x + j * 0.25, 0, 1.31)], 0.01, 4), M['paint'], WHITE)
    for xl in (-5.0, 5.0):                                                                                   # double globe lamps
        K.obj(lathe([(0.0, 0.0), (0.2, 0.0), (0.18, 0.4), (0.07, 0.6), (0.06, 3.6), (0.0, 3.7)], 10, xl, -0.6, 0.16), M['paint'], (0.06, 0.18, 0.2), 'cyl', 1.0)
        for sg in (-1, 1):
            K.obj(sweep([(xl, -0.6, 3.4), (xl + sg * 0.5, -0.6, 3.6), (xl + sg * 0.6, -0.6, 3.75)], 0.03, 5), M['paint'], (0.06, 0.18, 0.2))
            K.obj(lathe([(0.0, -0.22), (0.22, 0.0), (0.0, 0.22)], 14, xl + sg * 0.6, -0.6, 3.97), M['lens'], (1.0, 0.95, 0.85))
    K.obj(bbox(0.0, -1.2, 0.6, 1.8, 0.45, 0.06), M['wood'], (0.55, 0.38, 0.22), 'box', 1.0, 0.01, 1); K.obj(bbox(0.0, -1.42, 0.85, 1.8, 0.06, 0.4), M['wood'], (0.55, 0.38, 0.22), 'box', 1.0, 0.01, 1)
    for x in (-0.8, 0.8): K.obj(bbox(x, -1.25, 0.38, 0.08, 0.5, 0.45), M['paint'], (0.06, 0.18, 0.2))
    K.obj(bbox(-2.8, -2.6, 0.45, 1.4, 1.4, 0.6), M['ashlar'], STONE, 'box', 1.0, 0.02, 2)
    K.obj(lathe([(0.08, 0.0), (0.06, 1.3), (0.0, 1.35)], 8, -2.8, -2.6, 0.75), M['wood'], (0.35, 0.26, 0.16), 'cyl', 1.0)        # clipped bay tree in the planter
    K.obj(lathe([(0.0, -0.75), (0.6, -0.55), (0.78, 0.0), (0.6, 0.55), (0.0, 0.75)], 14, -2.8, -2.6, 2.6), M['concrete'], (0.05, 0.13, 0.03), 'cyl', 0.6)

# ------------------------------------------------------------------ 12 harbour kiosk
def harbour_kiosk(K, M):
    """Harbour ticket and ice-cream kiosk: white-washed box with a blue awning, serving hatch, menu board, ice-cream cart and a ferry timetable."""
    K.obj(bbox(0, 0, 1.4, 3.0, 4.0, 2.8), M['plaster'], (0.92, 0.9, 0.86), 'box', 1.0, 0.03, 2)
    K.obj(bbox(0, 0, 2.86, 3.3, 4.3, 0.14), M['plaster'], (0.06, 0.18, 0.38), 'box', 1.0, 0.02, 1)
    K.obj(bbox(1.51, 0, 1.6, 0.02, 2.4, 1.0), M['smooth'], (0.05, 0.045, 0.04)); K.obj(bbox(1.65, 0, 1.08, 0.35, 2.6, 0.06), M['wood'], (0.55, 0.38, 0.22))
    for k in range(7):
        aw = prism([(0, 2.55), (1.2, 2.2), (1.2, 2.16), (0, 2.51)], -1.4 + k * 0.4, -1.4 + (k + 1) * 0.4, axis='x')
        for v in aw.verts: a, b, c = v.co; v.co = (1.5 + b, a, c)
        K.obj(aw, M['fabric'], (0.06, 0.18, 0.45) if k % 2 else WHITE, 'box', 1.0, 0.0, smooth=False)
    K.obj(bbox(1.52, 0, 2.7, 0.04, 2.6, 0.26), M['sign'], (1, 1, 1), 'sign', 1.0, sign=P.sign_cell_uv_frame(__import__('isle_houses').Frame((1.54, 0, 0), (0, 1, 0), (1, 0, 0)), 6, 0.0, 2.7, 2.6, 0.26))
    K.obj(bbox(0.0, -2.01, 1.6, 1.6, 0.02, 1.1), M['ads'], (1, 1, 1), 'sign', 1.0, sign=P.ad_uv_frame(__import__('isle_houses').Frame((0, -2.02, 0), (1, 0, 0), (0, -1, 0)), 5, 0.0, 1.6, 1.6, 1.1))
    cx, cy = 2.6, 2.6                                                                                         # ice-cream cart with a parasol
    K.obj(bbox(cx, cy, 0.75, 0.8, 1.4, 0.7), M['smooth'], (0.92, 0.85, 0.75), 'box', 1.0, 0.05, 2)
    for y in (cy - 0.6, cy + 0.6):
        w_ = lathe([(0.18, -0.03), (0.25, -0.04), (0.26, 0.0), (0.25, 0.04), (0.18, 0.03)], 14)
        for v in w_.verts: a, b, c = v.co; v.co = (cx + a, y + c, 0.26 + b)
        K.obj(w_, M['concrete'], (0.04, 0.04, 0.04), 'cyl', 1.0)
    K.obj(sweep([(cx, cy, 1.1), (cx, cy, 2.3)], 0.02, 5), M['galv'], (0.8, 0.8, 0.8))
    for k in range(8):
        a0, a1 = k * math.pi / 4, (k + 1) * math.pi / 4
        bm = canopy_tri((cx, cy, 2.45), (cx + 0.9 * math.cos(a0), cy + 0.9 * math.sin(a0), 2.15), (cx + 0.9 * math.cos(a1), cy + 0.9 * math.sin(a1), 2.15)); K.obj(bm, M['fabric'], (0.85, 0.35, 0.45) if k % 2 else WHITE, 'box', 1.0, smooth=False)


ITEMS = dict(fishing_boat=(fishing_boat, 6.0), fishing_boat_b=(lambda K, M: fishing_boat(K, M, (0.55, 0.05, 0.03), (0.85, 0.75, 0.25)), 6.0),
             sail_yacht=(sail_yacht, 17.5), motor_yacht=(motor_yacht, 6.5), rowing_boat=(rowing_boat, 1.0), jetty=(jetty, 4.6), quay_hq=(quay, 2.0),
             beach_set=(beach_set, 2.6), lifeguard=(lifeguard, 6.8), beach_bar=(beach_bar, 4.8), breakwater=(breakwater, 7.2), promenade=(promenade, 4.2),
             harbour_kiosk=(harbour_kiosk, 2.9))


def register():
    for k, (fn, h) in ITEMS.items(): P.PROPS[k] = (fn, {}); P.HEIGHT[k] = h

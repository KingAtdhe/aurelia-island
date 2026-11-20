"""Art sheet 08: Aurelia roads and junctions. Short road vignettes that fix the look of each road type: surface, kerbs, markings,
verges and the furniture that belongs to it. Built with the street kit (isle_props) plus asphalt, setts and gravel photo materials.
Each vignette is a prop centred on the origin, road running along y unless noted."""
import math
import numpy as np
import bmesh
import isle_props as P
from isle_props import bbox, lathe, sweep, prism

WHITE = (0.92, 0.92, 0.9); YEL = (0.9, 0.62, 0.04); ASPH = (0.54, 0.52, 0.5); KERB = (0.72, 0.71, 0.68); GRASS = (0.4, 0.72, 0.12)


def _kit_photo(M, key, photo, mean, keep=0.3, flat=1.0, nstr=1.0, rough=(0.9, 0.05)):
    if key in M: return
    import isle_lib as L
    img = L.make_image('kit_' + photo, P._col(photo, mean, keep, flat)); n = P._rawrect(photo, 'NormalGL'); r = P._rawrect(photo, 'Roughness')
    rr = np.clip(r[..., 0] * rough[0] + rough[1], 0.72, 1) if r is not None else np.full((8, 8), 0.8)
    orm = L.make_image('kit_%s_orm' % photo, np.dstack([np.ones(rr.shape), rr, np.zeros(rr.shape)]), raw=True)
    M[key] = L.new_mat('Kit' + key.capitalize(), image=img, vcol=True, normal=L.make_image('kit_%s_n' % photo, n[..., :3], raw=True) if n is not None else None, nstrength=nstr, orm=orm)
    try:
        for n_ in M[key].node_tree.nodes:
            if n_.type == 'BSDF_PRINCIPLED': n_.inputs['Specular IOR Level'].default_value = 0.05 if key == 'grassg' else 0.12
    except Exception: pass


def materials(M):
    _kit_photo(M, 'asphalt', 'Asphalt010', 0.42, 0.2, 0.8)
    _kit_photo(M, 'setts', 'PavingStones070', 0.55, 0.5, 1.0, 1.2)
    _kit_photo(M, 'gravel', 'Gravel022', 0.5, 0.4, 1.0, 1.2)
    _kit_photo(M, 'grassg', 'Grass004', 0.4, 0.6, 1.0, 0.8, (1.0, 0.0))
    if 'paint' not in M: M['paint'] = M['smooth']
    return M


def slab(K, M, cx, cy, sx, sy, z, th, mat, col, uvs=4.0, yaw=0.0):
    K.obj(bbox(cx, cy, z - th / 2, sx, sy, th, yaw), M[mat], col, 'box', uvs)


def line(K, M, x0, y0, x1, y1, w=0.15, col=WHITE, z=0.012, dash=None):
    """Painted line from (x0, y0) to (x1, y1); dash=(on, off) for broken lines."""
    L = math.hypot(x1 - x0, y1 - y0); d = ((x1 - x0) / L, (y1 - y0) / L); yaw = math.atan2(d[1], d[0])
    segs = [(0, L)] if dash is None else [(s, min(s + dash[0], L)) for s in np.arange(0, L, dash[0] + dash[1])]
    for a, b in segs:
        m = (a + b) / 2; K.obj(bbox(x0 + d[0] * m, y0 + d[1] * m, z, b - a, w, 0.012, yaw), M['smooth'], col)


def kerb(K, M, x, y0, y1, h=0.15, w=0.3, col=KERB):
    K.obj(bbox(x, (y0 + y1) / 2, h / 2 - 0.02, w, y1 - y0, h + 0.04), M['concrete'], col, 'box', 1.0, 0.02, 2)


def verge(K, M, x0, x1, y0, y1, mat='grassg', col=GRASS, z=0.0):
    K.obj(bbox((x0 + x1) / 2, (y0 + y1) / 2, z - 0.1, x1 - x0, y1 - y0, 0.2), M[mat], col, 'box', 2.0)


def tufts(K, M, x0, x1, y0, y1, n, seed, col=(0.16, 0.3, 0.05)):
    rng = np.random.default_rng(seed)
    for k in range(n): K.obj(lathe([(0.0, 0.0), (0.18, 0.04), (0.0, 0.3)], 6, rng.uniform(x0, x1), rng.uniform(y0, y1), 0.0), M['concrete'], tuple(np.asarray(col) * rng.uniform(0.7, 1.3)))


def ring_sector(r0, r1, a0, a1, z, n=32):
    bm = bmesh.new(); A = [bm.verts.new((r0 * math.cos(a), r0 * math.sin(a), z)) for a in np.linspace(a0, a1, n + 1)]; B = [bm.verts.new((r1 * math.cos(a), r1 * math.sin(a), z)) for a in np.linspace(a0, a1, n + 1)]
    for i in range(n): bm.faces.new((A[i], A[i + 1], B[i + 1], B[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0: f.normal_flip()
    return bm


def _prop(K, M, name, x, y, z=0.0, yaw=0.0):
    """Drop an existing kit prop into a vignette (built in its own Part, moved into place)."""
    import mathutils
    fn, kw = P.PROPS[name]; Kp = P.Part(); fn(Kp, M, **kw); R = mathutils.Matrix.Translation((x, y, z)) @ mathutils.Matrix.Rotation(yaw, 4, 'Z'); R3 = np.array(R.to_3x3())
    for it in Kp.objs:
        if it[0] == 'raw':
            _, Pq, T_, N_, *rest = it; K.objs.append(('raw', Pq @ R3.T + np.array([x, y, z]), T_, N_ @ R3.T, *rest))
        else: it[0].data.transform(R); K.objs.append(it)


# ------------------------------------------------------------------ 1 highway
def highway(K, M, L=40.0):
    """Dual carriageway: two 3.6 m lanes each way, concrete median barrier, hard shoulders with rumble strips, cat's eyes, cutting verge."""
    for sg in (-1, 1):
        slab(K, M, sg * 5.6, 0, 10.4, L, 0.0, 0.3, 'asphalt', ASPH)
        line(K, M, sg * 0.9, -L / 2, sg * 0.9, L / 2, 0.2, YEL)                                          # inner edge (yellow)
        line(K, M, sg * 4.5, -L / 2, sg * 4.5, L / 2, 0.15, WHITE, dash=(6.0, 6.0))                      # lane line
        line(K, M, sg * 8.2, -L / 2, sg * 8.2, L / 2, 0.25, WHITE)                                       # edge line
        for y in np.arange(-L / 2, L / 2, 0.5): K.obj(bbox(sg * 8.55, y, 0.008, 0.4, 0.12, 0.016), M['smooth'], (0.5, 0.5, 0.5))   # rumble strip
        for y in np.arange(-L / 2 + 3, L / 2, 12): K.obj(bbox(sg * 4.5, y, 0.02, 0.1, 0.18, 0.04), M['lens'], (1.0, 0.95, 0.85))   # cat's eyes
        verge(K, M, sg * 10.8, sg * 18.0, -L / 2, L / 2) if sg > 0 else verge(K, M, -18.0, -10.8, -L / 2, L / 2)
        for y in np.arange(-L / 2 + 2, L / 2, 6): _post(K, M, sg * 11.3, y)
    for y in np.arange(-L / 2, L / 2, 4.0):                                                               # median jersey barrier
        K.obj(prism([(-0.3, 0.0), (0.3, 0.0), (0.22, 0.08), (0.08, 0.32), (0.08, 0.8), (-0.08, 0.8), (-0.08, 0.32), (-0.22, 0.08)], y, y + 3.98, axis='x') if False else _jersey(y), M['concrete'], (0.78, 0.77, 0.74), 'box', 2.0, 0.0)
    tufts(K, M, 11, 17, -L / 2, L / 2, 40, 1)


def _jersey(y0, L=3.98):
    bm = prism([(-0.3, 0.0), (0.3, 0.0), (0.22, 0.08), (0.08, 0.32), (0.08, 0.8), (-0.08, 0.8), (-0.08, 0.32), (-0.22, 0.08)], y0, y0 + L, axis='x')
    for v in bm.verts: a, b, c = v.co; v.co = (b, a, c)
    return bm


def _post(K, M, x, y):
    K.obj(bbox(x, y, 0.55, 0.1, 0.1, 1.1), M['smooth'], WHITE, 'box', 1.0, 0.01, 1)
    K.obj(bbox(x, y, 0.95, 0.105, 0.06, 0.15), M['smooth'], (0.05, 0.05, 0.05)); K.obj(bbox(x - 0.055, y, 0.95, 0.01, 0.04, 0.08), M['lens'], (1.0, 0.6, 0.1))


# ------------------------------------------------------------------ 2 country road
def country_road(K, M, L=36.0):
    """Two-lane country road: worn asphalt with patches and crack sealing, faded centre line, gravel shoulders, grass verges, reflector posts."""
    slab(K, M, 0, 0, 7.0, L, 0.0, 0.3, 'asphalt', (0.68, 0.67, 0.65))
    line(K, M, 0, -L / 2, 0, L / 2, 0.12, (0.78, 0.78, 0.74), dash=(3.0, 9.0)); line(K, M, -3.3, -L / 2, -3.3, L / 2, 0.1, (0.72, 0.72, 0.68)); line(K, M, 3.3, -L / 2, 3.3, L / 2, 0.1, (0.72, 0.72, 0.68))
    rng = np.random.default_rng(3)
    for k in range(5): None if k == 1 else K.obj(bbox(rng.uniform(-2.5, 2.5), rng.uniform(-L / 2 + 2, L / 2 - 2), 0.004 + k * 0.004, rng.uniform(0.8, 2.0), rng.uniform(1.0, 3.0), 0.006, rng.uniform(-0.1, 0.1)), M['asphalt'], (0.4, 0.39, 0.38), 'box', 4.0)
    for k in range(6):
        pts = [(rng.uniform(-3, 3), -L / 2 + k * 6 + 1.0, 0.01)]
        for j in range(5): pts.append((pts[-1][0] + rng.normal(0, 0.4), pts[-1][1] + rng.uniform(0.4, 1.0), 0.01))
        K.obj(sweep(pts, 0.025, 3), M['smooth'], (0.06, 0.06, 0.06))
    for sg in (-1, 1):
        K.obj(bbox(sg * 4.2, 0, -0.05, 1.4, L, 0.12), M['gravel'], (0.75, 0.7, 0.62), 'box', 2.0)
        verge(K, M, min(sg * 4.9, sg * 14), max(sg * 4.9, sg * 14), -L / 2, L / 2)
        for y in np.arange(-L / 2 + 1, L / 2, 9): _post(K, M, sg * 5.2, y)
    tufts(K, M, 5, 13, -L / 2, L / 2, 60, 4); tufts(K, M, -13, -5, -L / 2, L / 2, 60, 5)


# ------------------------------------------------------------------ 3 mountain hairpin
def hairpin(K, M):
    """Mountain hairpin: banked switchback with a stone parapet on the outside, chevron boards, patched asphalt and a cut rock bank inside."""
    R0, R1 = 3.0, 10.0
    bm = ring_sector(R0, R1, -math.pi / 2, math.pi / 2, 0.0, 40); K.obj(bm, M['asphalt'], (0.66, 0.65, 0.63), 'box', 4.0)
    for sg in (-1, 1): slab(K, M, -9.0, sg * (R0 + R1) / 2, 18.0, R1 - R0, 0.0, 0.3, 'asphalt', (0.66, 0.65, 0.63)) if False else K.obj(bbox(-9.0, sg * (R0 + R1) / 2, -0.15, 18.0, R1 - R0, 0.3), M['asphalt'], (0.66, 0.65, 0.63), 'box', 4.0)
    rc = (R0 + R1) / 2; pts = [(rc * math.cos(a), rc * math.sin(a), 0.012) for a in np.linspace(-math.pi / 2, math.pi / 2, 30)]
    K.obj(sweep([(-18, -rc, 0.012), (0, -rc, 0.012)], 0.06, 3), M['smooth'], WHITE); K.obj(sweep(pts, 0.06, 3), M['smooth'], WHITE); K.obj(sweep([(0, rc, 0.012), (-18, rc, 0.012)], 0.06, 3), M['smooth'], WHITE)
    for k in range(13):                                                                                      # parapet blocks round the outside
        a = -math.pi / 2 + math.pi * (k + 0.5) / 13; r = R1 + 0.4; L_ = math.pi * r / 13
        K.obj(bbox(r * math.cos(a), r * math.sin(a), 0.42, 0.5, L_ - 0.04, 0.84, a), M['ashlar'], (0.8, 0.74, 0.64), 'box', 1.2, 0.015, 2)
        K.obj(bbox(r * math.cos(a), r * math.sin(a), 0.9, 0.62, L_ - 0.02, 0.12, a), M['ashlar'], (0.9, 0.86, 0.78), 'box', 1.2, 0.01, 1)
    for k in range(4):                                                                                       # chevron boards on the parapet
        a = -0.6 + k * 0.4; r = R1 + 0.75
        K.obj(bbox(r * math.cos(a), r * math.sin(a), 1.25, 0.04, 0.9, 0.6, a), M['paint'], (0.05, 0.25, 0.55), 'box', 1.0, 0.01, 1)
        for j in range(2):
            o = -0.18 + j * 0.36; cx, cy = (r - 0.03) * math.cos(a) - o * math.sin(a), (r - 0.03) * math.sin(a) + o * math.cos(a)
            K.obj(bbox(cx, cy, 1.25, 0.02, 0.1, 0.42, a), M['paint'], WHITE)
    import isle_wild_hq as W
    bmr, S = W.boulder_mesh(201, (4.0, 5.0, 3.5), sub=3, facets=14)
    for v in bmr.verts: v.co.x -= 1.0
    K.obj(bmr, M['rock'] if 'rock' in M else M['concrete'], W.GRANITE, 'box', 3.2, 0.0, smooth=True, angle=28)
    rng = np.random.default_rng(7)
    for k in range(3): K.obj(bbox(rng.uniform(-14, 6), rng.choice([-1, 1]) * rng.uniform(4, 9), 0.006, rng.uniform(1, 2.5), rng.uniform(1, 2), 0.012, rng.uniform(0, 3)), M['asphalt'], (0.4, 0.4, 0.41), 'box', 4.0)


# ------------------------------------------------------------------ 4 city crossing
def city_crossing(K, M):
    """City street at a zebra crossing: granite kerbs with dropped kerbs and tactile paving, gully grates, a green cycle lane, give-way marks."""
    L = 30.0
    slab(K, M, 0, 0, 12.0, L, 0.0, 0.3, 'asphalt', (0.6, 0.6, 0.61))
    for sg in (-1, 1):
        kerb(K, M, sg * 6.15, -L / 2, -2.6); kerb(K, M, sg * 6.15, 2.6, L / 2); K.obj(bbox(sg * 6.15, 0, 0.03, 0.3, 5.2, 0.08), M['concrete'], KERB, 'box', 1.0, 0.01, 1)
        K.obj(bbox(sg * 9.3, 0, 0.07, 6.0, L, 0.16), M['setts'], (0.82, 0.8, 0.76), 'box', 1.6)
        K.obj(bbox(sg * 7.0, 0, 0.16, 1.2, 4.0, 0.02), M['smooth'], (0.75, 0.62, 0.35))                       # tactile paving
        for y in np.arange(-1.8, 1.9, 0.12):
            for x in np.arange(-0.5, 0.51, 0.12): K.obj(bbox(sg * 7.0 + x, y, 0.18, 0.05, 0.05, 0.02), M['smooth'], (0.75, 0.62, 0.35)) if abs(x) < 0.45 and (int(y * 8) % 2) else None
        K.obj(bbox(sg * 4.8, 0, 0.004, 1.5, L, 0.008), M['smooth'], (0.12, 0.42, 0.18))                        # cycle lane
        line(K, M, sg * 4.0, -L / 2, sg * 4.0, -2.4, 0.15); line(K, M, sg * 4.0, 2.4, sg * 4.0, L / 2, 0.15)
        for y in (-8.0, 9.0): K.obj(bbox(sg * 5.75, y, 0.01, 0.4, 0.8, 0.03), M['iron'], (0.08, 0.08, 0.08))      # gully grates
    for x in np.arange(-5.4, 5.5, 1.0): K.obj(bbox(x, 0, 0.012, 0.5, 4.0, 0.012), M['smooth'], WHITE)         # zebra
    line(K, M, -6, 0, 6, 0, 0.0)
    for sg in (-1, 1):
        for x in np.arange(-3.6, 3.7, 0.6): K.obj(prism([(x - 0.2, sg * 3.2), (x + 0.2, sg * 3.2), (x, sg * 3.2 + sg * 0.45)], 0.006, 0.014), M['smooth'], WHITE)   # give-way teeth
        for xb in (-6.6, 6.6): _prop(K, M, 'bollard_hq' if 'bollard_hq' in P.PROPS else 'bollard', xb, sg * 2.9, 0.15)
        _globe(K, M, sg * 6.5, sg * 2.8)


def _globe(K, M, x, y):
    """Belisha-style beacon pole for the crossing: striped post with an amber globe."""
    for k in range(9): K.obj(bbox(x, y, 0.15 + k * 0.3 + 0.15, 0.1, 0.1, 0.3), M['paint'], (0.04, 0.04, 0.04) if k % 2 else WHITE)
    K.obj(lathe([(0.0, -0.2), (0.2, 0.0), (0.0, 0.2)], 14, x, y, 3.0), M['lens'], (1.0, 0.6, 0.05))


# ------------------------------------------------------------------ 5 old-town setts
def setts_street(K, M):
    """Old-town lane: granite setts in arcs, a central dished gutter, granite kerbs, narrow limestone pavements and heritage bollards."""
    L = 26.0
    K.obj(bbox(0, 0, -0.15, 6.0, L, 0.3), M['setts'], (0.75, 0.72, 0.68), 'box', 1.2)
    K.obj(bbox(0, 0, 0.004, 0.5, L, 0.01), M['setts'], (0.55, 0.53, 0.5), 'box', 0.6)
    for sg in (-1, 1):
        kerb(K, M, sg * 3.1, -L / 2, L / 2, h=0.12, w=0.25)
        K.obj(bbox(sg * 4.2, 0, 0.06, 2.0, L, 0.14), M['ashlar'] if 'ashlar' in M else M['concrete'], (0.88, 0.84, 0.76), 'box', 1.4)
        for y in np.arange(-L / 2 + 2, L / 2, 4.0): _prop(K, M, 'bollard_hq' if 'bollard_hq' in P.PROPS else 'bollard', sg * 3.45, y, 0.13)
    _prop(K, M, 'lamp_city_hq' if 'lamp_city_hq' in P.PROPS else 'lamp', 4.6, 2.0, 0.13, math.pi)


# ------------------------------------------------------------------ 6 roundabout
def roundabout(K, M):
    """Single-lane roundabout: planted central island with a stone apron, raised splitter islands, yield lines, chevron blocks."""
    Ri, Ro = 7.0, 14.0
    K.obj(ring_sector(Ri, Ro, 0, 2 * math.pi, 0.0, 64), M['asphalt'], ASPH, 'box', 4.0)
    for a in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):                                                  # four approach arms
        c, s = math.cos(a), math.sin(a); K.obj(bbox(c * 20, s * 20, -0.15, 12 if c else 9.0, 9.0 if c else 12, 0.3), M['asphalt'], ASPH, 'box', 4.0)
        for o in (-1.0, 1.0):                                                                                # yield line (dashed) at the give-way
            for k in range(6):
                t = -3.8 + k * 1.3; K.obj(bbox(c * 14.6 - s * (o * 2.4 + t * 0.25), s * 14.6 + c * (o * 2.4 + t * 0.25), 0.012, 0.3 if c else 0.6, 0.6 if c else 0.3, 0.012), M['smooth'], WHITE) if o > 0 else None
        isl = prism([(0, -0.6), (6.5, -1.4), (7.0, 0.0), (6.5, 1.4), (0, 0.6)], 0.0, 0.15)               # splitter island
        for v in isl.verts: x_, y_, z_ = v.co; v.co = (c * (14.5 + x_) - s * y_, s * (14.5 + x_) + c * y_, z_)
        K.obj(isl, M['concrete'], KERB, 'box', 1.0, 0.02, 2)
        K.obj(bbox(c * 20.5, s * 20.5, 0.6, 0.06 if c else 0.6, 0.6 if c else 0.06, 1.2), M['paint'], (0.05, 0.25, 0.55)) if False else None
    K.obj(lathe([(0.0, 0.0), (Ri, 0.0), (Ri, 0.18), (Ri - 1.2, 0.2), (Ri - 1.3, 0.45), (0.0, 0.55)], 48), M['setts'], (0.8, 0.76, 0.7), 'box', 1.0)
    K.obj(lathe([(0.0, 0.45), (Ri - 1.4, 0.45), (Ri - 1.5, 0.6), (0.0, 0.9)], 48), M['grassg'], GRASS, 'box', 2.0)
    for k in range(8):                                                                                      # chevron blocks facing traffic
        a = k * math.pi / 4 + math.pi / 8; K.obj(bbox((Ri - 0.4) * math.cos(a), (Ri - 0.4) * math.sin(a), 0.75, 0.05, 1.2, 0.5, a), M['paint'], (0.05, 0.25, 0.55))
        K.obj(bbox((Ri - 0.37) * math.cos(a), (Ri - 0.37) * math.sin(a), 0.75, 0.02, 0.9, 0.3, a), M['paint'], WHITE)
    rng = np.random.default_rng(11)
    for k in range(40): K.obj(lathe([(0.0, 0.0), (0.4, 0.15), (0.3, 0.5), (0.0, 0.7)], 6, *(lambda r_, a_: (r_ * math.cos(a_), r_ * math.sin(a_)))(rng.uniform(0, Ri - 2), rng.uniform(0, 6.28)), 0.8), M['concrete'], (0.06, 0.16, 0.04))
    K.obj(lathe([(0.12, 0.0), (0.1, 2.6), (0.0, 2.7)], 8, 0, 0, 0.8), M['wood'], (0.4, 0.3, 0.2))
    K.obj(lathe([(0.0, 2.2), (1.5, 2.8), (1.6, 3.6), (1.0, 4.4), (0.0, 4.6)], 12, 0, 0, 0.8), M['concrete'], (0.08, 0.2, 0.05), 'cyl', 0.6)


# ------------------------------------------------------------------ 7 signal junction
def junction(K, M):
    """Signal-controlled T-junction: stop lines, lane arrows, a ghost-island right-turn lane, kerbed traffic island with a signal pole."""
    L = 36.0
    slab(K, M, 0, 0, 14.0, L, 0.0, 0.3, 'asphalt', ASPH); slab(K, M, 14.0, 0, 14.0, 10.0, 0.0, 0.3, 'asphalt', ASPH)
    line(K, M, 0, -L / 2, 0, -6, 0.15, WHITE, dash=(3.0, 3.0)); line(K, M, 0, 6, 0, L / 2, 0.15, WHITE, dash=(3.0, 3.0))
    for sg in (-1, 1): line(K, M, sg * 6.8, -L / 2, sg * 6.8, (L / 2) if sg < 0 else -5.0, 0.15); line(K, M, 6.8, 5.0, 6.8, L / 2, 0.15) if sg > 0 else None
    for k in range(6): K.obj(prism([(0.0, -3.0 - k * 0.9), (1.2, -3.0 - k * 0.9 - 0.6), (1.2, -3.0 - k * 0.9 - 0.75), (0.0, -3.0 - k * 0.9 - 0.15)], 0.006, 0.014), M['smooth'], WHITE)   # ghost island hatching
    line(K, M, -6.8, -6.5, 0.0, -6.5, 0.4); line(K, M, 7.5, -4.8, 7.5, 4.8, 0.4)                               # stop lines
    for (x, y, d) in ((-3.4, -10.0, 1), (3.4, 10.0, -1)):                                                    # lane arrows
        K.obj(bbox(x, y, 0.012, 0.15, 2.4, 0.012), M['smooth'], WHITE)
        K.obj(prism([(x - 0.45, y + d * 1.2), (x + 0.45, y + d * 1.2), (x, y + d * 2.0)], 0.006, 0.014), M['smooth'], WHITE)
    isl = prism([(9.0, -1.2), (13.0, -0.6), (13.0, 0.6), (9.0, 1.2)], 0.0, 0.15); K.obj(isl, M['concrete'], KERB, 'box', 1.0, 0.02, 2)
    _prop(K, M, 'signal', 11.0, 0.0, 0.15, math.pi)
    for sg in (-1, 1): kerb(K, M, -7.15, -L / 2, L / 2) if sg < 0 else (kerb(K, M, 7.15, -L / 2, -5.15), kerb(K, M, 7.15, 5.15, L / 2))
    verge(K, M, -16, -7.3, -L / 2, L / 2, 'setts', (0.82, 0.8, 0.76), 0.15)


# ------------------------------------------------------------------ 8 bridge deck
def bridge_deck(K, M, L=30.0):
    """Bridge deck: concrete edge beams with a steel parapet rail, an expansion joint plate, deck drains and lamp posts."""
    slab(K, M, 0, 0, 10.0, L, 0.0, 0.3, 'asphalt', ASPH)
    K.obj(bbox(0, 0, -1.0, 12.4, L, 1.4), M['concrete'], (0.7, 0.69, 0.66), 'box', 3.0)
    line(K, M, 0, -L / 2, 0, L / 2, 0.15, WHITE, dash=(4.0, 6.0))
    for sg in (-1, 1):
        line(K, M, sg * 4.6, -L / 2, sg * 4.6, L / 2, 0.15)
        K.obj(bbox(sg * 5.6, 0, 0.25, 1.2, L, 0.5), M['concrete'], (0.78, 0.77, 0.74), 'box', 2.0, 0.02, 2)
        for z in (0.95, 1.3): K.obj(sweep([(sg * 5.8, -L / 2, z), (sg * 5.8, L / 2, z)], 0.05, 8), M['galv'], (0.7, 0.72, 0.74))
        for y in np.arange(-L / 2, L / 2 + 0.1, 2.0): K.obj(bbox(sg * 5.8, y, 0.85, 0.1, 0.1, 0.7), M['galv'], (0.6, 0.62, 0.64))
        for y in (-10.0, 10.0):
            K.obj(lathe([(0.12, 0.0), (0.08, 0.3), (0.06, 8.0), (0.0, 8.05)], 10, sg * 5.6, y, 0.5), M['galv'], (0.6, 0.62, 0.64), 'cyl', 1.0)
            K.obj(sweep([(sg * 5.6, y, 8.4), (sg * 4.4, y, 8.7)], 0.05, 6), M['galv'], (0.6, 0.62, 0.64)); K.obj(bbox(sg * 4.2, y, 8.62, 0.7, 0.3, 0.12), M['lens'], (1.0, 0.95, 0.85))
        for y in (-6.0, 6.0): K.obj(bbox(sg * 4.85, y, 0.01, 0.3, 0.5, 0.02), M['iron'], (0.08, 0.08, 0.08))
    K.obj(bbox(0, 4.0, 0.01, 10.0, 0.4, 0.02), M['galv'], (0.55, 0.56, 0.58))                                    # expansion joint
    for x in np.arange(-4.8, 4.9, 0.2): K.obj(bbox(x, 4.0, 0.02, 0.06, 0.38, 0.01), M['iron'], (0.12, 0.12, 0.12))


# ------------------------------------------------------------------ 9 road works
def roadworks(K, M, L=34.0):
    """Lane closure: taper of cones, yellow temporary lines, water-filled barriers round a dug trench, a lit arrow board and a works sign."""
    slab(K, M, 0, 0, 7.4, L, 0.0, 0.3, 'asphalt', (0.66, 0.65, 0.63))
    line(K, M, 0, -L / 2, 0, L / 2, 0.12, WHITE, dash=(3, 6)); line(K, M, -3.4, -L / 2, -3.4, L / 2, 0.12, WHITE); line(K, M, 3.4, -L / 2, 3.4, L / 2, 0.12, WHITE)
    line(K, M, 0.3, -L / 2, -1.0, L / 2, 0.15, YEL, z=0.016)
    for k in range(14):
        t = k / 13; x = 3.2 - 3.0 * min(1.0, t * 2.2); y = -L / 2 + 2 + t * (L - 4)
        K.obj(lathe([(0.0, 0.0), (0.22, 0.0), (0.22, 0.04), (0.14, 0.06), (0.03, 0.75), (0.0, 0.76)], 12, x, y, 0), M['paint'], (0.95, 0.3, 0.02), 'cyl', 1.0)
        for z in (0.35, 0.55): K.obj(lathe([(0.11 - z * 0.1, z), (0.115 - z * 0.1, z + 0.08), (0.0, z + 0.08)], 12, x, y, 0, close_top=False) if False else lathe([(0.15 - z * 0.15, z), (0.14 - z * 0.15, z + 0.08)], 12, x, y, 0, close_top=False, close_bottom=False), M['smooth'], WHITE)
    for k in range(5):
        y = -2 + k * 2.05; K.obj(bbox(0.5, y, 0.4, 0.5, 2.0, 0.8), M['paint'], (0.85, 0.15, 0.08) if k % 2 else WHITE, 'box', 1.0, 0.05, 2)
        K.obj(bbox(3.0, y, 0.4, 0.5, 2.0, 0.8), M['paint'], WHITE if k % 2 else (0.85, 0.15, 0.08), 'box', 1.0, 0.05, 2)
    K.obj(bbox(1.75, 3.0, -0.3, 1.6, 6.0, 0.6), M['gravel'], (0.5, 0.42, 0.32), 'box', 1.5)
    K.obj(lathe([(0.0, 0.0), (1.0, 0.0), (0.7, 0.6), (0.0, 0.8)], 10, 1.8, 7.5, 0), M['gravel'], (0.55, 0.45, 0.35), 'cyl', 1.0)
    K.obj(bbox(2.2, -L / 2 + 1.0, 1.4, 0.15, 2.2, 1.6), M['paint'], (0.04, 0.04, 0.04), 'box', 1.0, 0.02, 1)       # arrow board on a trailer
    for k in range(5): K.obj(lathe([(0.0, 0.0), (0.08, 0.0), (0.08, 0.04), (0.0, 0.04)], 10) if False else bbox(2.12, -L / 2 + 0.2 + k * 0.35, 1.0 + k * 0.2, 0.02, 0.16, 0.16), M['lens'], (1.0, 0.65, 0.05))
    K.obj(bbox(2.2, -L / 2 + 1.0, 0.4, 1.4, 1.8, 0.3), M['paint'], (0.85, 0.55, 0.05))
    K.obj(sweep([(5.0, -6.0, 0.0), (5.0, -6.0, 2.0)], 0.03, 5), M['galv'], (0.6, 0.6, 0.6))
    import isle_wild_hq as W; K.obj(W._sign_tri(4.97, -6.0, 1.8, 0.5), M['paint'], (0.6, 0.04, 0.02)); K.obj(W._sign_tri(4.96, -6.0, 1.83, 0.38), M['paint'], (0.9, 0.62, 0.05))


# ------------------------------------------------------------------ 10 bus lay-by
def bus_layby(K, M, L=36.0):
    """Bus lay-by: tapered inset bay with a raised boarding kerb, BUS STOP lettering blocks, yellow box marking, shelter."""
    slab(K, M, 0, 0, 7.0, L, 0.0, 0.3, 'asphalt', ASPH); slab(K, M, 5.0, 0, 3.0, 20.0, 0.0, 0.3, 'asphalt', (0.58, 0.58, 0.59))
    line(K, M, 0, -L / 2, 0, L / 2, 0.12, WHITE, dash=(3, 6)); line(K, M, -3.3, -L / 2, -3.3, L / 2, 0.12)
    line(K, M, 3.4, -L / 2, 3.4, -10.0, 0.12); line(K, M, 3.4, 10.0, 3.4, L / 2, 0.12); line(K, M, 3.4, -10.0, 3.4, 10.0, 0.12, dash=(1.0, 1.0))
    for (a, b) in (((3.5, -10), (6.4, -14)), ((3.5, 10), (6.4, 14))): K.obj(sweep([(a[0], a[1], 0.15), (b[0], b[1], 0.15)], 0.15, 4), M['concrete'], KERB)
    kerb(K, M, 6.55, -10.0, 10.0, h=0.25, w=0.35); kerb(K, M, 3.55, -L / 2, -14.0); kerb(K, M, 3.55, 14.0, L / 2)
    line(K, M, 3.6, -9.5, 6.3, -9.5, 0.2, YEL); line(K, M, 3.6, 9.5, 6.3, 9.5, 0.2, YEL); line(K, M, 6.2, -9.5, 6.2, 9.5, 0.2, YEL)
    for k, w_ in enumerate((0.9, 0.9, 0.9, 0.0, 0.9, 0.9, 0.9, 0.9)):                                          # BUS STOP block lettering
        if w_: K.obj(bbox(4.9, -3.6 + k * 1.0, 0.012, 1.4, 0.7, 0.012), M['smooth'], YEL)
    verge(K, M, 6.7, 12.0, -L / 2, L / 2, 'setts', (0.82, 0.8, 0.76), 0.25); verge(K, M, -12.0, -3.5, -L / 2, L / 2)
    _prop(K, M, 'shelter_hq' if 'shelter_hq' in P.PROPS else 'shelter', 9.0, 0.0, 0.25, math.pi)


# ------------------------------------------------------------------ 11 car park
def car_park(K, M):
    """Surface car park: marked bays with numbers, an accessible bay, wheel stops, a pay station, lighting column and a hedge edge."""
    slab(K, M, 0, 0, 22.0, 22.0, 0.0, 0.3, 'asphalt', (0.58, 0.58, 0.59))
    for row, x0 in enumerate((-10.0, 5.0)):
        for k in range(9):
            y = -9.0 + k * 2.5; line(K, M, x0, y - 1.25, x0 + 5.0, y - 1.25, 0.12)
            K.obj(bbox(x0 + (0.5 if row == 0 else 4.5), y, 0.07, 0.25, 1.6, 0.14), M['concrete'], (0.6, 0.6, 0.6), 'box', 1.0, 0.02, 2)
        line(K, M, x0, 13.25 - 2.5 * 0 - 1.25 + 0.0 if False else x0, x0 + 5.0, 13.25 - 1.25 if False else -9.0 + 9 * 2.5 - 1.25, 0.12) if False else line(K, M, x0, -9.0 + 9 * 2.5 - 1.25, x0 + 5.0, -9.0 + 9 * 2.5 - 1.25, 0.12)
    K.obj(bbox(-7.5, -9.0, 0.006, 5.0, 2.4, 0.01), M['smooth'], (0.1, 0.3, 0.6))
    K.obj(bbox(-7.0, -9.0, 0.012, 1.2, 1.2, 0.012), M['smooth'], WHITE)
    for y in np.arange(-8.0, 9.0, 4.0): K.obj(prism([(-0.4, y), (0.4, y), (0.0, y + 1.2)], 0.006, 0.014), M['smooth'], WHITE)
    K.obj(bbox(11.6, 0, 0.6, 1.0, 22.0, 1.2), M['concrete'], (0.07, 0.16, 0.05), 'box', 0.5, 0.15, 3)
    K.obj(bbox(-11.4, 6.0, 0.8, 0.5, 0.6, 1.6), M['paint'], (0.15, 0.3, 0.45), 'box', 1.0, 0.03, 2)
    K.obj(lathe([(0.15, 0.0), (0.09, 0.4), (0.07, 9.0), (0.0, 9.05)], 10, 0, 0, 0), M['galv'], (0.6, 0.62, 0.64), 'cyl', 1.0)
    for sg in (-1, 1): K.obj(sweep([(0, 0, 8.8), (sg * 1.2, 0, 9.0)], 0.05, 6), M['galv'], (0.6, 0.62, 0.64)); K.obj(bbox(sg * 1.35, 0, 8.95, 0.6, 0.3, 0.12), M['lens'], (1.0, 0.95, 0.85))


# ------------------------------------------------------------------ 12 gravel track
def gravel_track(K, M, L=30.0):
    """Farm track: gravel with two wheel ruts, a grass crown, puddles, a cattle grid with stone wings and a wooden gate post."""
    K.obj(bbox(0, 0, -0.1, 4.0, L, 0.2), M['gravel'], (0.72, 0.66, 0.56), 'box', 1.5)
    for sg in (-1, 1): K.obj(bbox(sg * 0.8, 0, -0.005, 0.5, L, 0.01), M['gravel'], (0.5, 0.45, 0.38), 'box', 1.2)
    K.obj(bbox(0, 0, 0.02, 0.6, L, 0.04), M['grassg'], GRASS, 'box', 2.0); tufts(K, M, -0.3, 0.3, -L / 2, L / 2, 50, 21)
    for (x, y, r) in ((0.8, -6.0, 0.6), (-0.8, 3.0, 0.8), (0.8, 9.0, 0.5)): K.obj(lathe([(0.0, 0.0), (r, 0.0), (r * 0.9, 0.005), (0.0, 0.006)], 16, x, y, 0.005), M['smooth'], (0.08, 0.1, 0.1))
    for sg in (-1, 1): verge(K, M, min(sg * 2.0, sg * 10), max(sg * 2.0, sg * 10), -L / 2, L / 2)
    tufts(K, M, 2, 9, -L / 2, L / 2, 50, 22); tufts(K, M, -9, -2, -L / 2, L / 2, 50, 23)
    K.obj(bbox(0, 8.0, -0.05, 3.6, 2.4, 0.1), M['smooth'], (0.02, 0.02, 0.02))                                    # cattle grid pit and rails
    for x in np.arange(-1.7, 1.75, 0.18): K.obj(bbox(x, 8.0, 0.03, 0.06, 2.4, 0.08), M['galv'], (0.45, 0.42, 0.38))
    for sg in (-1, 1):
        K.obj(bbox(sg * 2.3, 8.0, 0.35, 0.6, 2.4, 0.7), M['ashlar'] if 'ashlar' in M else M['concrete'], (0.8, 0.74, 0.64), 'box', 1.2, 0.03, 2)
        K.obj(bbox(sg * 2.9, 8.0, 0.8, 0.2, 0.2, 1.6), M['wood'], (0.45, 0.35, 0.25), 'box', 1.0, 0.01, 1)
        for z in (0.5, 1.0): K.obj(sweep([(sg * 2.9, 8.0, z), (sg * 9.0, 8.0, z)], 0.03, 4), M['wood'], (0.5, 0.42, 0.32))


ITEMS = dict(highway=(highway, 1.2), country_road=(country_road, 1.2), hairpin=(hairpin, 3.5), city_crossing=(city_crossing, 3.2), setts_street=(setts_street, 5.6),
             roundabout=(roundabout, 5.4), junction=(junction, 5.4), bridge_deck=(bridge_deck, 9.0), roadworks=(roadworks, 2.2), bus_layby=(bus_layby, 3.2),
             car_park=(car_park, 9.0), gravel_track=(gravel_track, 1.6))


def register(M=None):
    materials(M if M is not None else P.mats())
    for k, (fn, h) in ITEMS.items(): P.PROPS['road_' + k] = (fn, {}); P.HEIGHT['road_' + k] = h


# ================================================================== map kit (art sheet 08 built into the island)
# Small pieces placed along the generated roads. Each faces +X with its origin on the ground.
BLUE = (0.02, 0.1, 0.36)


def rk_post(K, M):
    """Roadside marker post: white with a black band and an amber reflector facing -X (oncoming traffic)."""
    _post(K, M, 0.0, 0.0)


def _chev_board(K, M, flip):
    for y in (-0.38, 0.38): K.obj(bbox(0.05, y, 0.75, 0.07, 0.07, 1.5), M['galv'], (0.55, 0.57, 0.6), 'box', 1.0, 0.01, 1)
    K.obj(bbox(0.0, 0.0, 1.62, 0.04, 1.0, 0.7), M['smooth'], BLUE, 'box', 1.0, 0.01, 1)
    for j in (-0.22, 0.12):                                                          # two white chevrons pointing along -Y (or +Y when flipped)
        s = 1 if flip else -1; y0 = j * s
        tip = (y0 + s * 0.12, 1.62); a = (y0 - s * 0.06, 1.88); b = (y0 - s * 0.06, 1.36)
        for p0, p1 in ((a, tip), (tip, b)):
            dy, dz = p1[0] - p0[0], p1[1] - p0[1]; Lq = math.hypot(dy, dz); ang = math.atan2(dz, dy)
            bm = bbox(0, 0, 0, 0.012, Lq + 0.06, 0.08, 0)
            for v in bm.verts:
                yy, zz = v.co.y, v.co.z; v.co.y = (p0[0] + p1[0]) / 2 + yy * math.cos(ang) - zz * math.sin(ang); v.co.z = (p0[1] + p1[1]) / 2 + yy * math.sin(ang) + zz * math.cos(ang); v.co.x -= 0.026
            K.obj(bm, M['smooth'], WHITE)


def rk_chevron_l(K, M): _chev_board(K, M, False)
def rk_chevron_r(K, M): _chev_board(K, M, True)


def rk_cone(K, M):
    K.obj(bbox(0, 0, 0.02, 0.4, 0.4, 0.04), M['smooth'], (0.08, 0.08, 0.08))
    K.obj(lathe([(0.0, 0.04), (0.16, 0.04), (0.03, 0.75), (0.0, 0.76)], 12), M['smooth'], (0.95, 0.3, 0.02), 'cyl', 1.0)
    for z in (0.32, 0.52): K.obj(lathe([(0.16 - 0.13 * (z - 0.04) / 0.71 + 0.004, z), (0.16 - 0.13 * (z + 0.09 - 0.04) / 0.71 + 0.004, z + 0.09)], 12, close_top=False, close_bottom=False), M['smooth'], WHITE)


def rk_barrier(K, M, col=(0.85, 0.12, 0.06)):
    """2 m water-filled plastic barrier along X (red or white, laid alternately)."""
    K.obj(_barrier_mesh(), M['smooth'], col, 'box', 3.0, 0.0)
    K.obj(bbox(0.0, 0.0, 0.81, 0.3, 0.12, 0.03), M['smooth'], (0.05, 0.05, 0.05))


def _barrier_mesh():
    bm = prism([(-0.25, 0.0), (0.25, 0.0), (0.2, 0.15), (0.12, 0.8), (-0.12, 0.8), (-0.2, 0.15)], -0.98, 0.98, axis='x')
    for v in bm.verts: a, b, c = v.co; v.co = (b, a, c)
    return bm


def rk_arrowboard(K, M):
    """Trailer-mounted lit arrow board, face toward -X."""
    K.obj(bbox(0.3, 0, 0.45, 1.6, 1.4, 0.35), M['smooth'], (0.85, 0.55, 0.05), 'box', 1.0, 0.03, 2)
    for y in (-0.7, 0.7): K.obj(lathe([(0.0, -0.25), (0.25, 0.0), (0.0, 0.25)], 12, 0.3, y, 0.3) if False else bbox(0.3, y, 0.28, 0.5, 0.18, 0.5), M['smooth'], (0.05, 0.05, 0.05))
    K.obj(bbox(0.0, 0, 1.25, 0.12, 0.12, 1.4), M['galv'], (0.6, 0.6, 0.6))
    K.obj(bbox(-0.05, 0, 2.0, 0.12, 2.0, 1.3), M['smooth'], (0.04, 0.04, 0.04), 'box', 1.0, 0.02, 1)
    for k, (y, z) in enumerate(((-0.6, 2.0), (-0.3, 2.0), (0.0, 2.0), (0.3, 2.0), (0.25, 2.25), (0.25, 1.75), (0.48, 2.0), (0.15, 2.4), (0.15, 1.6))):
        K.obj(bbox(-0.12, y, z, 0.03, 0.13, 0.13), M['lens'], (1.0, 0.65, 0.05))


def rk_worksign(K, M):
    import isle_wild_hq as W
    K.obj(sweep([(0.0, 0.0, 0.0), (0.0, 0.0, 2.0)], 0.035, 6), M['galv'], (0.6, 0.6, 0.6))
    K.obj(W._sign_tri(-0.04, 0.0, 1.75, 0.55), M['smooth'], (0.6, 0.04, 0.02)); K.obj(W._sign_tri(-0.05, 0.0, 1.78, 0.42), M['smooth'], (0.92, 0.65, 0.06))
    K.obj(bbox(-0.06, 0.0, 1.66, 0.01, 0.16, 0.18), M['smooth'], (0.05, 0.05, 0.05))
    K.obj(bbox(0.0, 0.0, 0.06, 0.5, 0.5, 0.12), M['concrete'], (0.4, 0.4, 0.4))


def rk_trench(K, M):
    """Dug patch beside the carriageway with a spoil heap, 6 x 1.6 m."""
    K.obj(bbox(0, 0, 0.0, 6.0, 1.6, 0.06), M['gravel'], (0.42, 0.34, 0.25), 'box', 1.5)
    K.obj(lathe([(0.0, 0.0), (1.0, 0.0), (0.7, 0.6), (0.0, 0.8)], 10, 4.2, 0.0, 0), M['gravel'], (0.55, 0.45, 0.35), 'cyl', 1.0)


def rk_island(K, M, Ri=18.0):
    """Roundabout centre: granite kerb ring, setts apron, raised planted mound, a low stone wall, clipped shrubs,
    a stone plinth with a sculpted cypress group, and blue chevron blocks round the apron facing traffic."""
    K.obj(lathe([(0.0, 0.0), (Ri, 0.0), (Ri, 0.15), (Ri - 0.3, 0.17), (Ri - 0.3, 0.12), (0.0, 0.12)], 72), M['concrete'], KERB, 'box', 1.0)
    K.obj(lathe([(0.0, 0.12), (Ri - 0.3, 0.12), (Ri - 2.6, 0.2), (0.0, 0.2)], 72), M['setts'], (0.8, 0.76, 0.7), 'box', 1.0)
    K.obj(lathe([(Ri - 2.6, 0.0), (Ri - 2.6, 0.75), (Ri - 3.1, 0.82), (Ri - 3.1, 0.0)], 72), M['ashlar'] if 'ashlar' in M else M['concrete'], (0.84, 0.78, 0.68), 'box', 1.2)
    K.obj(lathe([(0.0, 0.7), (Ri - 3.1, 0.7), (Ri - 5.0, 1.2), (Ri * 0.45, 1.9), (0.0, 2.1)], 72), M['grassg'], GRASS, 'box', 2.0)
    rng = np.random.default_rng(int(Ri * 10))
    for k in range(int(Ri * 2.2)):                                                     # clipped shrub ring
        a = k / int(Ri * 2.2) * 2 * math.pi; r = Ri - 4.4; z = 0.7 + 0.5 * (Ri - 3.1 - r) / 1.9
        K.obj(lathe([(0.0, 0.0), (0.85, 0.05), (0.95, 0.5), (0.7, 1.05), (0.0, 1.2)], 8, r * math.cos(a), r * math.sin(a), z), M['concrete'], (0.06, 0.17, 0.04) if k % 2 else (0.09, 0.2, 0.05))
    for k in range(30):
        a = rng.uniform(0, 6.28); r = rng.uniform(Ri * 0.3, Ri - 6.5); z = 1.2 + (2.0 - 1.2) * (1 - r / (Ri - 5))
        col = ((0.55, 0.1, 0.25), (0.75, 0.6, 0.1), (0.4, 0.2, 0.5))[k % 3] if k % 2 else (0.08, 0.2, 0.05)
        K.obj(lathe([(0.0, 0.0), (0.8, 0.1), (0.65, 0.6), (0.0, 0.8)], 7, r * math.cos(a), r * math.sin(a), z - 0.1), M['concrete'], col)
    K.obj(lathe([(0.0, 1.9), (2.4, 1.9), (2.4, 2.6), (2.1, 2.7), (2.1, 2.75), (0.0, 2.75)], 24), M['ashlar'] if 'ashlar' in M else M['concrete'], (0.9, 0.86, 0.78), 'box', 1.2)
    for (dx, dy, h) in ((0.0, 0.0, 8.5), (1.1, 0.5, 6.5), (-0.9, 0.8, 7.0), (0.3, -1.1, 6.0)):  # cypress group
        K.obj(lathe([(0.12, 0.0), (0.12, 0.6), (0.6, 1.2), (0.75, h * 0.35), (0.55, h * 0.7), (0.0, h)], 10, dx, dy, 2.75), M['concrete'], (0.04, 0.12, 0.04), 'cyl', 1.0)
    for k in range(12):
        a = k * math.pi / 6 + math.pi / 12; r = Ri - 0.9
        K.obj(bbox(r * math.cos(a), r * math.sin(a), 0.6, 0.06, 1.3, 0.6, a), M['smooth'], BLUE, 'box', 1.0, 0.01, 1)
        K.obj(bbox((r + 0.035) * math.cos(a), (r + 0.035) * math.sin(a), 0.6, 0.02, 0.9, 0.3, a), M['smooth'], WHITE)


KIT_ITEMS = dict(rk_post=(rk_post, 1.1), rk_chevron_l=(rk_chevron_l, 2.0), rk_chevron_r=(rk_chevron_r, 2.0), rk_cone=(rk_cone, 0.8), rk_barrier=(rk_barrier, 0.8), rk_barrier_w=(lambda K, M: rk_barrier(K, M, (0.9, 0.9, 0.88)), 0.8),
                 rk_arrowboard=(rk_arrowboard, 2.7), rk_worksign=(rk_worksign, 2.4), rk_trench=(rk_trench, 0.8))


def register_kit(M=None):
    """Map pieces only (the 12 vignettes stay out of the game library)."""
    materials(M if M is not None else P.mats())
    for k, (fn, h) in KIT_ITEMS.items(): P.PROPS[k] = (fn, {}); P.HEIGHT[k] = h
    import isle_data as KD
    for (cx, cy, rr) in KD.ROUNDABOUTS:
        ri = round(rr - KD.TYPES['rbt']['w'] / 2 - 0.4, 1); P.PROPS['rk_island_%d' % int(round(ri * 10))] = (rk_island, dict(Ri=ri)); P.HEIGHT['rk_island_%d' % int(round(ri * 10))] = 11.0

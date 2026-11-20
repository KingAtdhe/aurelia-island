"""Art sheet 11: touge kit for the mountain roads (Summit Pass, Serpentine, Eagle Descent), after the mountain-pass look of CarX touge
maps: cut slopes held by concrete lattice frames and shotcrete, retaining walls, U-ditch gutters with grates, curve mirrors at blind
bends, white guard pipes, sodium lights at the hairpins, stepped spillways, and a dense wall of tall conifers right at the road edge.
Pieces face +X with the origin on the ground; the two road scenes are vignettes centred on the origin like sheet 08."""
import math
import numpy as np
import bmesh
import isle_props as P
from isle_props import bbox, lathe, sweep, prism
import isle_roads_hq as RQ

CONC = (0.72, 0.71, 0.68); CONC_D = (0.58, 0.57, 0.54); ORANGE = (0.95, 0.42, 0.06); TREES = {}; WHITE = (0.93, 0.93, 0.9); GR = (0.36, 0.66, 0.12)


def _plane_quads(pts):
    bm = bmesh.new(); V = [bm.verts.new(p) for p in pts]; bm.faces.new(V); return bm


def slope_surface(K, M, L, H, ang, mat, col, uvs=2.0, x0=0.0):
    """Inclined plane rising away from the road (toward -X): foot at x = x0, length L along y, height H, slope angle ang (deg)."""
    run = H / math.tan(math.radians(ang)); bm = _plane_quads([(x0, -L / 2, 0.0), (x0, L / 2, 0.0), (x0 - run, L / 2, H), (x0 - run, -L / 2, H)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.x < 0: f.normal_flip()
    K.obj(bm, M[mat], col, 'box', uvs, smooth=False); return run


def lattice_slope(K, M, L=16.0, H=9.0, ang=55.0, cell=2.2, x0=0.0):
    """Cut slope held by a cast concrete lattice frame (square beams on the slope), grass and moss in the cells."""
    run = slope_surface(K, M, L, H, ang, 'grassg', GR, 1.5, x0); sl = math.hypot(run, H); t = np.array([-run, 0, H]) / sl
    nrm = np.array([H, 0, run]) / sl
    def P3(u, s, off=0.0): return np.array([x0, u, 0.0]) + t * s + nrm * off
    for u in np.arange(-L / 2, L / 2 + 0.01, cell):                                   # beams down the slope
        a, b = P3(u, 0.0, 0.18), P3(u, sl, 0.18); K.obj(sweep([tuple(a), tuple(b)], 0.0, 4) if False else _beam(a, b, 0.32, 0.3, nrm), M['concrete'], CONC, 'box', 1.5)
    for s in np.arange(0.0, sl + 0.01, cell):                                          # beams across
        a, b = P3(-L / 2, s, 0.18), P3(L / 2, s, 0.18); K.obj(_beam(a, b, 0.32, 0.3, nrm), M['concrete'], CONC, 'box', 1.5)
    rng = np.random.default_rng(int(L * 10))
    for k in range(int(L * sl / 3)):                                                   # tufts in the cells
        u = rng.uniform(-L / 2, L / 2); s = rng.uniform(0, sl); p = P3(u, s, 0.02)
        K.obj(lathe([(0.0, 0.0), (0.3, 0.05), (0.0, 0.35)], 6, p[0], p[1], p[2]), M['concrete'], np.array((0.12, 0.26, 0.05)) * rng.uniform(0.8, 1.3))
    K.obj(bbox(x0 - run - 0.6, 0, H + 0.2, 1.4, L, 0.4), M['concrete'], CONC_D, 'box', 1.5)                     # crown beam
    return run


def _beam(a, b, w, h, up):
    """Box beam from a to b with height h along 'up' and width w."""
    d = np.asarray(b, float) - np.asarray(a, float); L = np.linalg.norm(d); d /= L; up = np.asarray(up, float); up = up - d * (up @ d); up /= np.linalg.norm(up); sd = np.cross(d, up)
    bm = bmesh.new(); C = []
    for s0 in (0.0, L):
        for (eu, es) in ((-1, -1), (1, -1), (1, 1), (-1, 1)): C.append(bm.verts.new(tuple(np.asarray(a) + d * s0 + up * eu * h / 2 + sd * es * w / 2)))
    for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)): bm.faces.new([C[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return bm


def shotcrete_cut(K, M, L=16.0, H=10.0, ang=62.0, x0=0.0):
    """Sprayed-concrete cut face with weep pipes in rows, a drainage berm halfway and rust streaks below the pipes."""
    run = slope_surface(K, M, L, H, ang, 'concrete2', (0.7, 0.68, 0.64), 3.0, x0); sl = math.hypot(run, H); t = np.array([-run, 0, H]) / sl; nrm = np.array([H, 0, run]) / sl
    for s in np.arange(1.5, sl, 2.0):
        for u in np.arange(-L / 2 + 1.0, L / 2, 2.0):
            p = np.array([x0, u + (0.5 if int(s) % 2 else 0), 0.0]) + t * s
            K.obj(sweep([tuple(p - nrm * 0.05), tuple(p + nrm * 0.25)], 0.05, 8), M['plastic'] if 'plastic' in M else M['smooth'], (0.3, 0.32, 0.34))
            q = p + nrm * 0.01; K.obj(_plane_quads([tuple(q + np.array([0, -0.06, 0])), tuple(q + np.array([0, 0.06, 0])), tuple(q + np.array([0, 0.06, 0]) - t * 1.2), tuple(q + np.array([0, -0.06, 0]) - t * 1.2)]), M['smooth'], (0.32, 0.2, 0.12), smooth=False)
    mid = np.array([x0, 0, 0.0]) + t * sl * 0.5; K.obj(bbox(mid[0] - 0.5, 0, mid[2] - 0.1, 1.2, L, 0.25), M['concrete'], CONC_D, 'box', 1.5)
    return run


def retaining_wall(K, M, L=16.0, H=3.2):
    """Battered concrete gravity wall with formwork lines, weep holes, a coping and a steel handrail."""
    bm = prism([(0.0, 0.0), (0.0, H), (-0.45, H), (-0.45 - H * 0.12, 0.0)], -L / 2, L / 2, axis='y') if False else None
    poly = [(0.0, 0.0), (-0.0 - H * 0.1, H), (-0.6 - H * 0.1, H), (-0.9 - H * 0.1, 0.0)]
    b = bmesh.new(); A = [b.verts.new((x, -L / 2, z)) for x, z in poly]; B = [b.verts.new((x, L / 2, z)) for x, z in poly]
    b.faces.new(A); b.faces.new(B[::-1])
    for i in range(4): j = (i + 1) % 4; b.faces.new((A[i], A[j], B[j], B[i]))
    bmesh.ops.recalc_face_normals(b, faces=b.faces); K.obj(b, M['concrete2'], (0.74, 0.73, 0.7), 'box', 2.0, smooth=False)
    for z in np.arange(0.6, H, 0.6):                                                   # formwork lines
        K.obj(bbox(-z * 0.1 / 1.0 * 0.0 - H * 0.1 * z / H + 0.01, 0, z, 0.02, L, 0.02), M['smooth'], (0.5, 0.49, 0.47))
    for u in np.arange(-L / 2 + 1.0, L / 2, 2.0):
        for z in (0.6, 1.8):
            x = -H * 0.1 * z / H + 0.01; K.obj(lathe([(0.06, 0.0), (0.06, 0.12), (0.0, 0.13)], 8, 0, 0, 0) if False else bbox(x, u, z, 0.03, 0.12, 0.12), M['smooth'], (0.05, 0.05, 0.05))
            K.obj(_plane_quads([(x + 0.02, u - 0.05, z - 0.06), (x + 0.02, u + 0.05, z - 0.06), (x + 0.0 + 0.02 + 0.01, u + 0.03, 0.05), (x + 0.03, u - 0.03, 0.05)]), M['smooth'], (0.42, 0.4, 0.36), smooth=False)
    K.obj(bbox(-H * 0.1 - 0.3, 0, H + 0.08, 0.8, L, 0.16), M['concrete'], CONC, 'box', 1.5, 0.02, 2)
    for u in np.arange(-L / 2 + 0.5, L / 2, 2.0): K.obj(bbox(-H * 0.1 - 0.3, u, H + 0.6, 0.06, 0.06, 1.0), M['galv'], (0.7, 0.72, 0.74))
    for z in (H + 0.6, H + 1.08): K.obj(sweep([(-H * 0.1 - 0.3, -L / 2, z), (-H * 0.1 - 0.3, L / 2, z)], 0.03, 8), M['galv'], (0.7, 0.72, 0.74))


def u_ditch(K, M, L=16.0, x=0.0):
    """Precast concrete U-ditch along the uphill edge with cast-iron grates every 4 m and a dark wet bottom."""
    for sg in (-1, 1): K.obj(bbox(x + sg * 0.3, 0, -0.15, 0.12, L, 0.42), M['concrete'], CONC, 'box', 1.2)
    K.obj(bbox(x, 0, -0.35, 0.6, L, 0.04), M['smooth'], (0.08, 0.09, 0.08))
    for u in np.arange(-L / 2, L / 2, 1.0): K.obj(bbox(x, u, 0.06, 0.72, 0.03, 0.02), M['concrete'], CONC_D)       # joints
    for u in np.arange(-L / 2 + 2.0, L / 2, 4.0):
        K.obj(bbox(x, u, 0.05, 0.62, 0.9, 0.03), M['iron'], (0.12, 0.11, 0.1))
        for k in range(9): K.obj(bbox(x, u - 0.4 + k * 0.1, 0.07, 0.58, 0.03, 0.02), M['iron'], (0.2, 0.18, 0.16))


def curve_mirror(K, M):
    """Orange pole with a round convex mirror (two faces) and a hood, as at blind bends."""
    K.obj(lathe([(0.25, 0.0), (0.25, 0.3), (0.0, 0.3)], 12), M['concrete'], CONC_D)
    K.obj(lathe([(0.05, 0.3), (0.05, 3.4), (0.0, 3.42)], 10), M['smooth'], ORANGE, 'cyl', 1.0)
    K.obj(sweep([(0.0, 0.0, 3.2), (0.12, 0.0, 3.25), (0.25, 0.0, 3.25)], 0.035, 6), M['smooth'], ORANGE)
    for a in (-0.5, 0.5):                                                               # two mirrors, angled to see round the bend
        c = np.array([0.25 + 0.08 * math.cos(a), 0.45 * math.sin(a) * 2.0, 3.25])
        m = lathe([(0.0, 0.0), (0.38, -0.05), (0.42, -0.08), (0.42, -0.14), (0.0, -0.14)], 24)
        for v in m.verts:
            x, y, z = v.co; ca, sa = math.cos(a), math.sin(a); X = z; Y = x; Z = y                     # housing behind the glass, glass facing +X (the road)
            v.co = (c[0] + X * ca - Y * sa, c[1] + X * sa + Y * ca, c[2] + Z)
        K.obj(m, M['smooth'], ORANGE, 'cyl', 1.0)
        g = lathe([(0.0, 0.03), (0.37, -0.03)], 24)
        for v in g.verts:
            x, y, z = v.co; ca, sa = math.cos(a), math.sin(a); X = -(z - 0.03); Y = x; Z = y
            v.co = (c[0] + X * ca - Y * sa, c[1] + X * sa + Y * ca, c[2] + Z)
        K.obj(g, M['galv'], (0.9, 0.92, 0.95))
    K.obj(bbox(0.08, 0.0, 2.55, 0.03, 0.5, 0.34), M['smooth'], WHITE); K.obj(bbox(0.1, 0.0, 2.55, 0.01, 0.42, 0.06), M['smooth'], (0.75, 0.1, 0.08))


def guard_pipe(K, M, L=12.0):
    """White guard pipe: round posts every 2 m with three steel pipes, the touge standard on the downhill side."""
    for u in np.arange(-L / 2, L / 2 + 0.01, 2.0):
        K.obj(lathe([(0.07, 0.0), (0.07, 1.0), (0.075, 1.02), (0.0, 1.05)], 12, 0, u), M['smooth'], WHITE, 'cyl', 1.0)
        K.obj(lathe([(0.0, 0.0), (0.04, 0.02), (0.0, 0.05)], 8, 0.08, u, 0.85), M['lens'], (1.0, 0.6, 0.1))
    for z in (0.55, 0.8, 0.98): K.obj(sweep([(0.08, -L / 2, z), (0.08, L / 2, z)], 0.045, 10), M['smooth'], WHITE, 'cylv', 1.0)


def cedar(K, M, h=22.0, seed=0):
    """Tall straight conifer (cedar/cypress type): clear lower trunk, dense narrow crown of layered drooping tiers."""
    rng = np.random.default_rng(seed); col = np.array((0.06, 0.16, 0.06)) * rng.uniform(0.85, 1.15)
    K.obj(lathe([(0.32, 0.0), (0.26, 1.0), (0.18, h * 0.6), (0.05, h), (0.0, h + 0.1)], 10), M['bark'] if 'bark' in M else M['wood'], (0.4, 0.28, 0.2), 'cylv', 1.0)
    z = h * 0.35
    while z < h:
        r = (h - z) / (h * 0.65) * 2.6 + 0.4; tier = lathe([(0.1, 0.0), (r, -0.9), (r * 0.9, -1.1), (0.0, 0.25)], 10, 0, 0, z)
        for v in tier.verts: v.co.x += rng.normal(0, 0.06); v.co.y += rng.normal(0, 0.06)
        K.obj(tier, M['concrete'], col * rng.uniform(0.85, 1.15), 'cyl', 0.8); z += rng.uniform(1.0, 1.4)


def cedar_stand(K, M):
    rng = np.random.default_rng(31)
    for k in range(9): TREES.setdefault('tg_cedars', []).append((rng.uniform(-6, 2), rng.uniform(-6, 6), 0.0, rng.uniform(1.0, 1.3)))
    K.obj(bbox(-2, 0, -0.05, 10, 14, 0.1), M['grassg'], (0.2, 0.32, 0.08), 'box', 2.0)
    for k in range(60): x, y = rng.uniform(-7, 3), rng.uniform(-7, 7); K.obj(lathe([(0.0, 0.0), (0.35, 0.1), (0.0, 0.6)], 6, x, y, 0.0), M['concrete'], (0.12, 0.26, 0.05))


def road_light(K, M):
    """Mountain road light at a hairpin: galvanised tapered pole, curved arm, sodium lantern (warm orange)."""
    K.obj(lathe([(0.12, 0.0), (0.09, 0.4), (0.065, 8.0), (0.0, 8.05)], 10), M['galv'], (0.68, 0.7, 0.72), 'cyl', 1.0)
    K.obj(sweep([(0.0, 0.0, 7.6), (0.4, 0.0, 8.3), (1.5, 0.0, 8.5)], 0.05, 8), M['galv'], (0.68, 0.7, 0.72))
    K.obj(bbox(1.75, 0.0, 8.42, 0.7, 0.32, 0.16), M['galv'], (0.5, 0.52, 0.55), 'box', 1.0, 0.04, 2)
    K.obj(bbox(1.75, 0.0, 8.33, 0.6, 0.26, 0.03), M['lens'], (1.0, 0.55, 0.15))
    K.obj(lathe([(0.3, 0.0), (0.3, 0.4), (0.0, 0.4)], 10), M['concrete'], CONC_D)


def spillway(K, M, H=8.0, ang=50.0, steps=10):
    """Stepped concrete spillway carrying water down a cut slope into the U-ditch."""
    run = H / math.tan(math.radians(ang))
    for k in range(steps):
        z0 = H * k / steps; z1 = H * (k + 1) / steps; x0 = -run * k / steps; x1 = -run * (k + 1) / steps
        K.obj(bbox((x0 + x1) / 2, 0, z0 + (z1 - z0) / 2 - 0.1, abs(x1 - x0) + 0.05, 1.2, z1 - z0 + 0.2), M['concrete'], CONC, 'box', 1.2)
        for sg in (-1, 1): K.obj(bbox((x0 + x1) / 2, sg * 0.7, z1 + 0.05, abs(x1 - x0) + 0.05, 0.2, 0.4), M['concrete'], CONC_D, 'box', 1.2)
        K.obj(bbox((x0 + x1) / 2, 0, z1 + 0.005, abs(x1 - x0), 0.9, 0.01), M['smooth'], (0.18, 0.24, 0.26))
    slope_surface(K, M, 7.0, H, ang, 'grassg', GR, 1.5, 0.35)


def delineators(K, M):
    """Kilometre post, tall snow-pole delineators with arrows, and a reflector post group."""
    K.obj(bbox(0, 0, 0.5, 0.18, 0.3, 1.0), M['concrete'], WHITE, 'box', 1.0, 0.03, 2); K.obj(bbox(0.09, 0, 0.8, 0.01, 0.26, 0.3), M['smooth'], (0.1, 0.35, 0.7))
    for k, y in enumerate((-2.0, 2.0, 6.0)):
        K.obj(lathe([(0.04, 0.0), (0.04, 2.6), (0.0, 2.62)], 8, 0, y), M['smooth'], (0.95, 0.75, 0.1) if k % 2 else WHITE)
        for z in np.arange(1.6, 2.6, 0.4): K.obj(lathe([(0.042, z), (0.042, z + 0.2)], 8, 0, y, close_top=False, close_bottom=False), M['smooth'], (0.75, 0.1, 0.08))
        K.obj(bbox(0.0, y, 2.2, 0.03, 0.4, 0.4), M['smooth'], (0.95, 0.75, 0.1)); K.obj(prism([(y - 0.12, 2.1), (y + 0.12, 2.2), (y - 0.12, 2.3)], -0.03, -0.02, axis='x') if False else bbox(-0.02, y, 2.2, 0.01, 0.2, 0.06), M['smooth'], (0.05, 0.05, 0.05))
    for y in (-4.0, 0.0, 4.0): RQ._post(K, M, 0.6, y)


# ------------------------------------------------------------------ road scenes
def touge_straight(K, M, L=30.0):
    """Two-lane pass road: yellow no-overtaking centre line, uphill cut held by a lattice frame over a retaining wall and U-ditch,
    white guard pipe on the drop side, cedar wall beyond, a curve mirror and a road light."""
    RQ.slab(K, M, 0, 0, 7.0, L, 0.0, 0.3, 'asphalt', (0.5, 0.49, 0.48))
    RQ.line(K, M, 0.0, -L / 2, 0.0, L / 2, 0.15, RQ.YEL); RQ.line(K, M, 0.25, -L / 2, 0.25, L / 2, 0.15, RQ.YEL)
    for sg in (-1, 1): RQ.line(K, M, sg * 3.25, -L / 2, sg * 3.25, L / 2, 0.15)
    Ku = P.Part(); u_ditch(Ku, M, L); _shift(K, Ku, (-4.0, 0, 0))
    Kw = P.Part(); retaining_wall(Kw, M, L, 2.4); _shift(K, Kw, (-4.35, 0, 0))
    Kl = P.Part(); lattice_slope(Kl, M, L, 10.0, 55.0, 2.2); _shift(K, Kl, (-5.6, 0, 2.5))
    K.obj(bbox(4.1, 0, -0.1, 1.2, L, 0.2), M['gravel'], (0.6, 0.55, 0.48), 'box', 1.5)
    Kg = P.Part(); guard_pipe(Kg, M, L); _shift(K, Kg, (4.4, 0, 0))
    K.obj(_plane_quads([(4.7, -L / 2, 0.0), (4.7, L / 2, 0.0), (14.0, L / 2, -8.0), (14.0, -L / 2, -8.0)]), M['grassg'], (0.22, 0.36, 0.08), 'box', 2.0, smooth=False)
    rng = np.random.default_rng(5)
    for k in range(10):
        x, y = rng.uniform(9.0, 14.0), rng.uniform(-L / 2 + 2, L / 2 - 2); TREES.setdefault('tg_straight', []).append((x, y, -(x - 4.7) * 8.0 / 9.3, rng.uniform(1.0, 1.3)))
    Km = P.Part(); curve_mirror(Km, M); _shift(K, Km, (4.9, 6.0, 0.0), math.pi)
    Kr = P.Part(); road_light(Kr, M); _shift(K, Kr, (-4.6, -6.0, 0.0), 0.0)


def touge_hairpin(K, M):
    """A tight hairpin cut into the hillside: lattice slope and spillway on the inside, guard pipe and chevrons round the outside,
    curve mirror at the apex, sodium light, tyre marks."""
    R0, R1 = 2.5, 9.5; rc = (R0 + R1) / 2
    K.obj(RQ.ring_sector(R0, R1, -math.pi / 2, math.pi / 2, 0.0, 40), M['asphalt'], (0.5, 0.49, 0.48), 'box', 4.0)
    for sg in (-1, 1): K.obj(bbox(-9.0, sg * rc, -0.15, 18.0, R1 - R0, 0.3), M['asphalt'], (0.5, 0.49, 0.48), 'box', 4.0)
    for r_, col in ((rc - 0.12, RQ.YEL), (rc + 0.12, RQ.YEL), (R0 + 0.25, WHITE), (R1 - 0.25, WHITE)):
        pts = [(-18, -r_, 0.012), (0, -r_, 0.012)] + [(r_ * math.cos(a), r_ * math.sin(a), 0.012) for a in np.linspace(-math.pi / 2, math.pi / 2, 28)] + [(0, r_, 0.012), (-18, r_, 0.012)]
        K.obj(sweep(pts, 0.07, 3), M['smooth'], col)
    for k in range(3):                                                                   # rubber on the apex
        r_ = rc + 1.0 + k * 0.5; K.obj(sweep([(r_ * math.cos(a), r_ * math.sin(a), 0.014) for a in np.linspace(-1.2, 1.2, 20)], 0.09, 3), M['smooth'], (0.05, 0.05, 0.05))
    for k in range(22):                                                                  # guard pipe posts round the outside
        a = -math.pi / 2 + math.pi * k / 21; r_ = R1 + 0.6
        K.obj(lathe([(0.07, 0.0), (0.07, 1.0), (0.0, 1.05)], 10, r_ * math.cos(a), r_ * math.sin(a)), M['smooth'], WHITE)
    for z in (0.55, 0.8, 0.98): K.obj(sweep([((R1 + 0.6) * math.cos(a), (R1 + 0.6) * math.sin(a), z) for a in np.linspace(-math.pi / 2, math.pi / 2, 30)], 0.045, 8), M['smooth'], WHITE)
    for k in range(5):
        a = -0.8 + k * 0.4; r_ = R1 + 1.1; Kc = P.Part(); RQ.rk_chevron_r(Kc, M) if hasattr(RQ, 'rk_chevron_r') else None; _shift(K, Kc, (r_ * math.cos(a), r_ * math.sin(a), 0.0), a + math.pi)
    Kl = P.Part(); lattice_slope(Kl, M, 17.0, 7.0, 55.0, 2.0); _shift(K, Kl, (-9.5, R1 + 0.4, 0.0), -math.pi / 2)      # cut slope above the upper leg
    Ks = P.Part(); spillway(Ks, M, 7.0, 55.0, 9); _shift(K, Ks, (-5.0, R1 + 0.45, 0.0), -math.pi / 2)
    K.obj(lathe([(R0 - 0.2, 0.0), (R0 - 0.2, 0.18), (R0 - 0.5, 0.2), (0.0, 0.9)], 24, 0, 0, 0, a0=math.pi / 2, a1=1.5 * math.pi) if False else
          lathe([(R0 - 0.2, 0.0), (R0 - 0.2, 0.18), (R0 - 0.5, 0.25), (0.0, 1.2)], 24, 0, 0, 0, a0=-math.pi / 2, a1=math.pi / 2), M['grassg'], (0.24, 0.4, 0.09), 'box', 1.5)   # raised verge at the nose
    K.obj(bbox(-9.0, 0.0, 0.3, 18.0, 2 * R0 - 0.4, 0.6), M['grassg'], (0.24, 0.4, 0.09), 'box', 1.5)
    Km = P.Part(); curve_mirror(Km, M); _shift(K, Km, (R1 + 1.8, 0.0, 0.0), math.pi)
    Kr = P.Part(); road_light(Kr, M); _shift(K, Kr, (R1 + 1.6, -3.5, 0.0), math.pi)
    rng = np.random.default_rng(8)
    for k in range(8):
        a = rng.uniform(-1.3, 1.3); r_ = rng.uniform(R1 + 9, R1 + 15); TREES.setdefault('tg_hairpin', []).append((r_ * math.cos(a), r_ * math.sin(a), -0.05, rng.uniform(0.9, 1.2)))
    K.obj(RQ.ring_sector(R1 + 0.9, R1 + 17, -math.pi / 2, math.pi / 2, -0.05, 30), M['grassg'], (0.22, 0.36, 0.08), 'box', 2.0)


def _shift(K, Kp, off, yaw=0.0):
    import mathutils
    R = mathutils.Matrix.Translation(off) @ mathutils.Matrix.Rotation(yaw, 4, 'Z'); R3 = np.array(R.to_3x3())
    for it in Kp.objs:
        if it[0] == 'raw':
            _, Pq, T_, N_, *rest = it; K.objs.append(('raw', Pq @ R3.T + np.array(off), T_, N_ @ R3.T, *rest))
        else: it[0].data.transform(R); K.objs.append(it)


ITEMS = dict(tg_hairpin=(touge_hairpin, 9.0), tg_straight=(touge_straight, 12.0), tg_lattice=(lambda K, M: lattice_slope(K, M), 9.0), tg_shotcrete=(lambda K, M: shotcrete_cut(K, M), 10.0),
             tg_wall=(lambda K, M: retaining_wall(K, M), 4.4), tg_ditch=(lambda K, M: u_ditch(K, M, 10.0), 0.3), tg_mirror=(curve_mirror, 3.7), tg_guardpipe=(guard_pipe, 1.1),
             tg_cedars=(cedar_stand, 24.0), tg_light=(road_light, 8.6), tg_spillway=(lambda K, M: spillway(K, M), 8.0), tg_posts=(delineators, 2.6))


def register(M=None):
    M = M if M is not None else P.mats(); RQ.materials(M); RQ.register_kit(M)
    for k, (fn, h) in ITEMS.items(): P.PROPS[k] = (fn, {}); P.HEIGHT[k] = h

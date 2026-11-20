"""Art sheet 07: Aurelia mountains, desert and roadside. Sculpted granite boulders, banded sandstone hoodoos, cliff faces for road cuts,
scree, W-beam guardrail, stone parapets and kilometre stones, a stone tunnel portal, a rockfall catch fence, mountain road signs,
a desert windpump, a desert roadside stop and a mountain lookout shelter.
Every piece faces +X, origin on the ground in the middle of the footprint, built with the street kit (isle_props)."""
import math
import numpy as np
import bmesh
import isle_props as P
from isle_props import bbox, lathe, sweep, prism

GRANITE = (0.46, 0.41, 0.35); SAND = (0.78, 0.42, 0.22); STEEL = (0.62, 0.64, 0.66); IRON = (0.04, 0.04, 0.045); WHITE = (0.9, 0.9, 0.88)
RED = (0.6, 0.04, 0.02); YELLOW = (0.85, 0.55, 0.05); TIMBER = (0.3, 0.2, 0.12); STONE = (0.8, 0.74, 0.64)


def _ico(sub):
    t = (1 + 5 ** 0.5) / 2
    V = [np.array(v, float) / np.linalg.norm(v) for v in [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(sub):
        cache = {}; nf = []
        def mid(a, b):
            k = (min(a, b), max(a, b))
            if k not in cache: m = V[a] + V[b]; V.append(m / np.linalg.norm(m)); cache[k] = len(V) - 1
            return cache[k]
        for a, b, c in F:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a); nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        F = nf
    return np.array(V), np.array(F)


def _fbm(P_, rng, octaves=5, f0=1.2, ridged=False):
    """Cheap 3D fractal noise from sums of random-direction sines (no textures needed)."""
    out = np.zeros(len(P_)); a = 1.0; f = f0; tot = 0
    for o in range(octaves):
        d = rng.normal(0, 1, (6, 3)); d /= np.linalg.norm(d, axis=1)[:, None]; ph = rng.uniform(0, 6.28, 6)
        n = np.mean(np.sin(P_ @ (d.T * f) + ph), 1)
        if ridged: n = 1 - np.abs(n) * 2
        out += a * n; tot += a; a *= 0.5; f *= 2.05
    return out / tot


def _mesh(V, F):
    bm = bmesh.new(); vs = [bm.verts.new(tuple(v)) for v in V]
    for f in F:
        try: bm.faces.new([vs[i] for i in f])
        except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return bm


def boulder_mesh(seed, size=(2.2, 1.8, 1.4), sub=3, facets=16, strata=0.0, tall=False):
    """Granite boulder: an icosphere cut by random fracture planes, then roughened by fractal noise; optional sandstone bedding."""
    rng = np.random.default_rng(seed); V, F = _ico(sub); S = V.copy()
    dirs = rng.normal(0, 1, (facets, 3)); dirs /= np.linalg.norm(dirs, axis=1)[:, None]
    for d in dirs:                                                                                  # fractures: flatten everything beyond a plane
        lim = rng.uniform(0.45, 0.8); h = S @ d; S = S - np.outer(np.maximum(h - lim, 0) * rng.uniform(0.8, 0.97), d)
    S = S * (1 + 0.07 * _fbm(V * 1.3, rng, 5, 1.4)[:, None] + 0.05 * _fbm(V * 3.0, rng, 4, 2.0, ridged=True)[:, None])
    if strata:                                                                                       # bedding planes: stepped bands eaten back by weather
        z = S[:, 2]; band = np.sin(z * strata * math.pi * 2 + _fbm(V, rng, 2, 1.0) * 0.8); r = np.hypot(S[:, 0], S[:, 1])
        S[:, :2] *= (1 - 0.14 * np.clip(band, 0, 1) ** 2)[:, None]
    S = S * np.array(size) / 2; S[:, 2] -= S[:, 2].min() + size[2] * 0.12                             # bury the base a little
    if tall: S[:, :2] *= (1 - 0.35 * np.clip(S[:, 2] / S[:, 2].max(), 0, 1) ** 1.5)[:, None]
    return _mesh(S, F), S


def rock_mb(seed, lod=0, squash=0.7, tall=False, tint=(0.20, 0.185, 0.165), strata=0.0):
    """Flora-library rock (art sheet 07): fractured, roughened boulder as an isle_flora mesh buffer, about 2 m across."""
    from isle_flora import MB
    size = (1.5, 1.3, 4.6) if tall else (2.9, 2.5, 2.9 * squash)
    bm, S = boulder_mesh(seed, size, sub=2 if lod == 0 else 1, facets=14 if lod == 0 else 8, strata=strata or (0.6 if tall else 0.0), tall=tall)
    bm.verts.ensure_lookup_table(); F = np.array([[v.index for v in f.verts] for f in bm.faces if len(f.verts) == 3]); bm.free()
    Vf = S[F].reshape(-1, 3); Ff = np.arange(len(Vf)).reshape(-1, 3)
    fn = np.cross(S[F[:, 1]] - S[F[:, 0]], S[F[:, 2]] - S[F[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1), 1e-9)[:, None]
    cen = S.mean(0); out = np.sign(((S[F].mean(1) - cen) * fn).sum(1))[:, None]; fn = fn * np.where(out == 0, 1, out)
    Ff = np.where(out > 0, Ff, Ff[:, ::-1])
    vn = np.zeros_like(S); np.add.at(vn, F.ravel(), np.repeat(fn, 3, 0)); vn /= np.maximum(np.linalg.norm(vn, axis=1), 1e-9)[:, None]
    N = 0.75 * np.repeat(fn, 3, 0) + 0.25 * vn[F].reshape(-1, 3)
    an = np.abs(np.repeat(fn, 3, 0)); U = np.where((an[:, 2:3] > an[:, 0:1]) & (an[:, 2:3] > an[:, 1:2]), Vf[:, :2], np.where(an[:, 0:1] > an[:, 1:2], Vf[:, 1:], Vf[:, ::2])) * 0.9
    shade = (0.78 + 0.3 * np.clip(N[:, 2], -0.3, 1))[:, None] * np.asarray(tint) * (0.92 + 0.16 * (Vf[:, 2:3] > 0.4 * Vf[:, 2].max()))
    b = MB(); b.add(Vf, Ff, shade, U, N)
    return b, None, 1.0


def boulders(K, M):
    """Three granite boulders, nested as they fell, with lichen-coloured tops and a few loose stones."""
    for i, (x, y, s, sd) in enumerate(((0.0, 0.0, (3.2, 2.6, 2.1), 11), (2.6, -1.4, (1.9, 1.6, 1.3), 12), (-1.6, 2.0, (1.5, 1.3, 0.9), 13))):
        bm, S = boulder_mesh(sd, s)
        for v in bm.verts: v.co.x += x; v.co.y += y
        K.obj(bm, M['rock'], tuple(np.array(GRANITE) * (1.0 + 0.08 * i)), 'box', 3.2, 0.0, smooth=True, angle=28)
    rng = np.random.default_rng(14)
    for k in range(12):
        bm, _ = boulder_mesh(30 + k, tuple(rng.uniform(0.2, 0.45, 3)), sub=1, facets=6)
        x, y = rng.uniform(-3, 4), rng.uniform(-3, 3)
        for v in bm.verts: v.co.x += x; v.co.y += y
        K.obj(bm, M['rock'], GRANITE, 'box', 3.2, 0.0, smooth=True, angle=28)


def hoodoo(K, M):
    """Banded sandstone hoodoo with a harder cap rock, and a low eroded mesa shelf behind it."""
    bm, S = boulder_mesh(21, (2.6, 2.4, 7.5), sub=3, facets=8, strata=0.55, tall=True)
    K.obj(bm, M['rock'], SAND, 'box', 3.2, 0.0, smooth=True, angle=28)
    cap, _ = boulder_mesh(22, (3.0, 2.7, 1.1), sub=2, facets=9)
    for v in cap.verts: v.co.z += 6.4
    K.obj(cap, M['rock'], (0.62, 0.36, 0.2), 'box', 3.2, 0.0, smooth=True, angle=28)
    for j, (x, y, sz) in enumerate(((-5.0, 1.5, (4.0, 3.0, 2.8)), (-7.5, -1.0, (3.0, 2.6, 1.8)), (-4.0, -2.5, (2.2, 1.8, 1.4)))):   # eroded blocks behind
        blk, _ = boulder_mesh(23 + j * 7, sz, sub=3, facets=18, strata=0.9)
        for v in blk.verts: v.co.x += x; v.co.y += y
        K.obj(blk, M['rock'], (0.82, 0.48, 0.26), 'box', 3.2, 0.0, smooth=True, angle=28)
    rng = np.random.default_rng(24)
    for k in range(10):
        b, _ = boulder_mesh(40 + k, tuple(rng.uniform(0.3, 0.7, 3)), sub=1, facets=6)
        x, y = rng.uniform(-2, 3), rng.uniform(-3, 3)
        for v in b.verts: v.co.x += x; v.co.y += y
        K.obj(b, M['rock'], SAND, 'box', 3.2, 0.0, smooth=True, angle=28)


def cliff(K, M, W=16.0, H=11.0, sand=False):
    """Road-cut cliff face: a displaced rock wall with near-vertical jointing, ledges, a talus foot; facing +X."""
    rng = np.random.default_rng(51 if not sand else 52); nu, nv = 64, 44
    u = np.linspace(-W / 2, W / 2, nu); v = np.linspace(0, H, nv); UU, VV = np.meshgrid(u, v)
    P_ = np.c_[UU.ravel() / 4.0, VV.ravel() / 4.0, np.zeros(UU.size)]
    joints = np.abs(np.sin(UU.ravel() * 1.3 + 2.0 * _fbm(P_, rng, 3, 0.6)))                       # vertical joint sets
    ledges = np.abs(np.sin(VV.ravel() * (2.4 if sand else 0.9) + 0.6 * _fbm(P_, rng, 2, 0.4)))      # horizontal ledges / bedding
    d = 2.4 * _fbm(P_, rng, 6, 0.45) + 1.3 * (1 - joints) ** 3 + (1.0 if sand else 0.6) * (1 - ledges) ** 4 + 0.35 * _fbm(P_ * 3, rng, 3, 1.0, ridged=True)
    lean = 0.12 * VV.ravel()                                                                       # the face leans back a little
    X = d - lean + 1.6 * np.exp(-VV.ravel() / 1.2)                                                 # talus foot spreads out
    ZZ = VV.ravel() * (1 - 0.25 * np.clip(_fbm(np.c_[UU.ravel() / 3, np.zeros(UU.size), np.zeros(UU.size)], rng, 3, 0.8) + 0.4, 0, 1))   # ragged skyline
    V = np.c_[X, UU.ravel(), ZZ]
    F = []
    for j in range(nv - 1):
        for i in range(nu - 1):
            a = j * nu + i; F += [(a, a + 1, a + nu + 1), (a, a + nu + 1, a + nu)]
    back = len(V); Vb = V.copy(); Vb[:, 0] = X.min() - 3.0                                         # flat back so it can be set into a slope
    Vall = np.vstack([V, Vb]); Fall = list(F)
    for j in range(nv - 1): a = j * nu; b = j * nu + nu - 1; Fall += [(a, a + nu, back + a + nu, back + a), (b, back + b, back + b + nu, b + nu)]
    for i in range(nu - 1): a = (nv - 1) * nu + i; Fall += [(a, back + a, back + a + 1, a + 1)]
    bm = _mesh(Vall, Fall)
    K.obj(bm, M['rock'], SAND if sand else GRANITE, 'box', 4.5, 0.0, smooth=True, angle=40)
    for k in range(14):                                                                            # fallen blocks at the foot
        b, _ = boulder_mesh(60 + k, tuple(rng.uniform(0.3, 0.9, 3)), sub=1, facets=6)
        x, y = rng.uniform(1.2, 3.4), rng.uniform(-W / 2 + 1, W / 2 - 1)
        for vv in b.verts: vv.co.x += x; vv.co.y += y
        K.obj(b, M['rock'], SAND if sand else GRANITE, 'box', 3.2, 0.0, smooth=True, angle=28)
    for k in range(10):                                                                            # tufts on the ledges
        x = rng.uniform(-0.5, 0.8); y = rng.uniform(-W / 2 + 1, W / 2 - 1); z = rng.uniform(1.5, H - 1)
        K.obj(lathe([(0.0, 0.0), (0.35, 0.1), (0.0, 0.35)], 6, x + 0.6, y, z), M['concrete'], (0.06, 0.12, 0.03))


def scree(K, M):
    """Scree fan at the foot of a gully: a rough talus cone of angular stones graded from big at the toe to gravel at the top."""
    rng = np.random.default_rng(71)
    for k in range(380):
        a = rng.uniform(-math.pi * 0.85, math.pi * 0.85); r = rng.uniform(0.0, 1.0) ** 1.1; x = 4.6 * r * math.cos(a) - 1.0; y = 3.6 * r * math.sin(a)
        s = (0.3 + 0.7 * r ** 2) * rng.uniform(0.6, 1.3); z = 2.4 * (1 - r) ** 1.1 + rng.uniform(-0.15, 0.1)
        b, _ = boulder_mesh(100 + k, (s, s * rng.uniform(0.6, 1.0), s * 0.6), sub=1, facets=6)
        for vv in b.verts: vv.co.x += x; vv.co.y += y; vv.co.z += z - s * 0.1
        K.obj(b, M['rock'], tuple(np.array(GRANITE) * rng.uniform(0.8, 1.15)), 'box', 3.2, 0.0, smooth=True, angle=28)


# ------------------------------------------------------------------ roadside
def guardrail(K, M, L=12.0):
    """W-beam guardrail on Sigma posts with blockouts, a flared end terminal and amber reflectors; runs along y."""
    prof = [(0.0, 0.0), (0.04, 0.05), (0.08, 0.1), (0.04, 0.16), (0.0, 0.21), (0.04, 0.26), (0.08, 0.31), (0.04, 0.37), (0.0, 0.42)]
    def beam(y0, y1, flare=0.0):
        n = 12; bm = bmesh.new(); rows = []
        for i in range(n + 1):
            t = i / n; y = y0 + (y1 - y0) * t; f = flare * max(0.0, (t - 0.6) / 0.4) ** 2
            rows.append([bm.verts.new((px - f, y, 0.53 + pz)) for (px, pz) in prof])
        for i in range(n):
            for k in range(len(prof) - 1): bm.faces.new((rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1]))
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.006); return bm
    K.obj(beam(-L / 2, L / 2), M['galv'], STEEL, 'box', 1.0, 0.0, smooth=True, angle=50)
    K.obj(beam(L / 2, L / 2 + 4.0, flare=1.0), M['galv'], STEEL, 'box', 1.0, 0.0, smooth=True, angle=50)
    K.obj(lathe([(0.0, 0.0), (0.2, 0.0), (0.2, 0.42), (0.0, 0.42)], 14, -1.0, L / 2 + 4.0, 0.53, a0=-math.pi / 2, a1=math.pi / 2), M['galv'], STEEL)   # rounded end
    for y in np.arange(-L / 2 + 0.5, L / 2 + 3.6, 2.0):
        K.obj(bbox(-0.32, y, 0.38, 0.1, 0.14, 1.1), M['galv'], (0.55, 0.57, 0.6), 'box', 1.0, 0.01, 1)      # post
        K.obj(bbox(-0.2, y, 0.74, 0.18, 0.12, 0.34), M['plastic'], (0.06, 0.06, 0.06))                  # blockout
        K.obj(bbox(0.1, y, 0.86, 0.02, 0.08, 0.06), M['lens'], (1.0, 0.6, 0.05))                       # reflector
    K.obj(bbox(-0.32, -L / 2 - 0.6, 0.1, 1.0, 0.8, 0.2), M['concrete'], (0.55, 0.53, 0.5))


def parapet(K, M, L=10.0):
    """Mountain road parapet: dressed stone wall with coping and drainage slots, plus a kilometre stone and two snow poles."""
    rng = np.random.default_rng(81); y = -L / 2
    while y < L / 2:
        l = rng.uniform(0.5, 0.9)
        for row in range(3): K.obj(bbox(rng.uniform(-0.02, 0.02), y + l / 2 + (0.2 if row % 2 else 0), 0.15 + row * 0.25, 0.5, l - 0.02, 0.24), M['ashlar'], tuple(np.array(STONE) * rng.uniform(0.85, 1.05)), 'box', 1.2, 0.012, 1)
        y += l
    K.obj(bbox(0.0, 0, 0.84, 0.62, L + 0.2, 0.14), M['ashlar'], (0.88, 0.84, 0.76), 'box', 1.2, 0.02, 2)
    for y in (-3.0, 0.0, 3.0): K.obj(bbox(0.26, y, 0.1, 0.02, 0.3, 0.18), M['smooth'], (0.03, 0.03, 0.03))
    K.obj(bbox(1.0, L / 2 + 1.0, 0.45, 0.25, 0.4, 0.9), M['ashlar'], (0.95, 0.94, 0.9), 'box', 1.0, 0.04, 3)     # kilometre stone with a red top
    K.obj(lathe([(0.2, 0.0), (0.2, 0.05), (0.0, 0.18)], 4, 1.0, L / 2 + 1.0, 0.9, a0=math.pi / 4, a1=math.pi / 4 + 2 * math.pi), M['paint'], RED, smooth=False)
    for y in (-L / 2 + 0.6, L / 2 - 0.6):                                                            # snow poles
        for k in range(8): K.obj(bbox(0.45, y, 0.95 + k * 0.3, 0.06, 0.06, 0.3), M['paint'], RED if k % 2 else (1.0, 0.75, 0.05))


def tunnel_portal(K, M, hw=6.5, Rw=None, Ht=None, bore=True):
    """Stone tunnel portal: arch ring of voussoirs with a keystone (following the road tunnel's arch: half-width Rw, crown Ht),
    ashlar headwall with a cornice, wing walls, date plaque, two bracket lamps; the dark bore only for the sheet render."""
    Rw = Rw or hw + 1.3; Ht = Ht or 7.0; t = 1.0; n = 17
    def arch_pt(th, grow=0.0):                                                                       # same curve as the road tunnel (isle_build)
        f_ = lambda a: (-Rw * math.cos(a), 0.02 + Ht * max(0.0, math.sin(a)) ** 0.6)
        u, z = f_(th)
        if grow:
            e = 1e-3; ta = min(max(th, 2 * e), math.pi - 2 * e); (ua, za), (ub, zb) = f_(ta - e), f_(ta + e); tx, tz = ub - ua, zb - za; L = math.hypot(tx, tz) or 1
            nx, nz = -tz / L, tx / L
            if nz < 0 or (abs(nz) < 1e-6 and nx * u < 0): nx, nz = -nx, -nz
            u += nx * grow; z += nz * grow
        return u, z
    for k in range(n):                                                                               # voussoirs
        a0 = math.pi * k / n; a1 = math.pi * (k + 1) / n; g = 1.3 if k == n // 2 else 0.95
        pts = [arch_pt(a0), arch_pt(a0, g), arch_pt(a1, g), arch_pt(a1)]
        bm = bmesh.new(); vs = [bm.verts.new((x_, u_, z_)) for x_ in (0.15, -t) for (u_, z_) in pts]
        for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)): bm.faces.new([vs[i] for i in f])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); K.obj(bm, M['ashlar'], tuple(np.array(STONE) * (0.95 + 0.1 * (k % 2))), 'box', 1.0, 0.0, smooth=False)
    top = Ht + 3.4; ths = np.linspace(0, math.pi / 2, 200); prof = [arch_pt(th, 0.95) for th in ths]
    for z0 in np.arange(0.0, top, 0.62):                                                             # ashlar courses round the arch ring
        zc = z0 + 0.31; inner = max([abs(u) for (u, z) in prof if z <= zc] + [0.0]) if zc < Ht + 0.95 else 0.0
        inner = inner if zc < Ht + 0.95 else 0.0; outer = Rw + 5.5
        for sg in (-1, 1):
            if outer - inner > 0.05: K.obj(bbox(-t / 2, sg * (inner + (outer - inner) / 2), zc, t - 0.05, outer - inner, 0.6), M['ashlar'], tuple(np.array(STONE) * (0.84 + 0.06 * (int(z0 * 3) % 3))), 'box', 1.0, 0.0)
    K.obj(bbox(-t / 2 + 0.15, 0, top + 0.25, t + 0.3, 2 * (Rw + 5.5) + 0.6, 0.5), M['ashlar'], (0.92, 0.88, 0.8), 'box', 1.0, 0.03, 2)      # cornice
    K.obj(bbox(0.2, 0, Ht + 1.9, 0.08, 2.4, 0.7), M['ashlar'], (0.96, 0.94, 0.9), 'box', 1.0, 0.02, 2)                                     # plaque
    for sg in (-1, 1):                                                                               # pilasters, wing walls stepping down, lamps
        K.obj(bbox(-t / 2 + 0.2, sg * (Rw + 5.0), top / 2, t + 0.4, 1.2, top), M['ashlar'], (0.88, 0.84, 0.76), 'box', 1.0, 0.03, 2)
        for k in range(4): K.obj(bbox(1.2 + k * 1.5, sg * (Rw + 5.6 + k * 0.3), (top - 1.0 - k * 2.0) / 2, 1.5, 0.8, top - 1.0 - k * 2.0), M['ashlar'], (0.82, 0.76, 0.66), 'box', 1.6, 0.02, 1)
        K.obj(sweep([(0.15, sg * (Rw + 0.9), Ht * 0.62), (0.8, sg * (Rw + 0.9), Ht * 0.62 + 0.2)], 0.04, 6), M['iron'], IRON)
        K.obj(lathe([(0.0, 0.0), (0.16, 0.04), (0.18, 0.35), (0.1, 0.45), (0.0, 0.48)], 8, 0.85, sg * (Rw + 0.9), Ht * 0.62 - 0.3), M['lens'], (1.0, 0.85, 0.5))
    if bore:
        K.obj(bbox(-6.0, 0, 3.0, 10.0, 2 * Rw, 6.0), M['smooth'], (0.015, 0.015, 0.015))


def _half_disc(r, zs, x=-1.0, n=24):
    """Dark plug that fills the arch head of the bore (seen from outside)."""
    bm = bmesh.new(); c = bm.verts.new((x, 0, zs)); rim = [bm.verts.new((x, math.cos(math.pi * k / n) * r, zs + math.sin(math.pi * k / n) * r)) for k in range(n + 1)]
    for k in range(n): bm.faces.new((c, rim[k], rim[k + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.x < 0: f.normal_flip()
    return bm


def catch_fence(K, M, L=14.0):
    """Rockfall catch fence on a slope: steel I-posts with back-stays, ring-net panels, and a band of drapery mesh above."""
    for k in range(5):
        y = -L / 2 + k * L / 4
        K.obj(sweep([(0.0, y, 0.0), (-0.6, y, 4.2)], 0.09, 4), M['galv'], (0.45, 0.46, 0.48))
        K.obj(sweep([(-0.6, y, 4.2), (-4.0, y, 1.8)], 0.012, 4), M['galv'], (0.5, 0.5, 0.5))
        K.obj(bbox(0.0, y, -0.1, 0.6, 0.6, 0.3), M['concrete'], (0.55, 0.53, 0.5))
    for z in (0.1, 4.15): K.obj(sweep([(0.0 - 0.6 * z / 4.2, -L / 2, z), (0.0 - 0.6 * z / 4.2, L / 2, z)], 0.015, 4), M['galv'], (0.5, 0.5, 0.5))
    for i in range(int(L / 0.5)):                                                                    # ring net: diagonal lattice
        y = -L / 2 + i * 0.5
        for sg in (-1, 1):
            y1 = y + sg * 2.0
            if -L / 2 <= y1 <= L / 2: K.obj(sweep([(0.0, y, 0.15), (-0.6, y1, 4.1)], 0.008, 3), M['galv'], (0.45, 0.46, 0.48))
    rng = np.random.default_rng(91)
    for k in range(6):                                                                               # caught rocks
        b, _ = boulder_mesh(120 + k, tuple(rng.uniform(0.3, 0.6, 3)), sub=1, facets=6)
        x, y = rng.uniform(-0.8, -0.3), rng.uniform(-L / 2 + 1, L / 2 - 1)
        for vv in b.verts: vv.co.x += x; vv.co.y += y
        K.obj(b, M['rock'], GRANITE, 'box', 3.2, 0.0, smooth=True, angle=28)


def mountain_signs(K, M):
    """Mountain road signs: pass summit board with height, a hairpin chevron board, snow-chain sign, falling-rocks warning and a mirror."""
    def post(x, y, h): K.obj(lathe([(0.04, 0.0), (0.04, h)], 8, x, y, 0), M['galv'], (0.6, 0.62, 0.64), 'cyl', 1.0)
    post(0, -2.0, 2.6); K.obj(bbox(0.05, -2.0, 2.4, 0.04, 1.6, 0.9), M['paint'], (0.04, 0.2, 0.42), 'box', 1.0, 0.01, 1)
    K.obj(bbox(0.08, -2.0, 2.4, 0.02, 1.45, 0.75), M['sign'], (1, 1, 1), 'sign', 1.0, sign=P.sign_cell_uv_frame(__import__('isle_houses').Frame((0.09, -2.0, 0), (0, 1, 0), (1, 0, 0)), 7, 0.0, 2.4, 1.45, 0.75))
    post(0, 0.2, 1.2); post(0, 1.4, 1.2); K.obj(bbox(0.05, 0.8, 1.15, 0.04, 1.6, 0.5), M['paint'], (0.9, 0.9, 0.86), 'box', 1.0, 0.01, 1)
    for k in range(3):                                                                                # red chevrons
        y0 = 0.25 + k * 0.5; bm = prism([(y0, 0.95), (y0 + 0.25, 1.15), (y0, 1.35), (y0 + 0.12, 1.35), (y0 + 0.37, 1.15), (y0 + 0.12, 0.95)], 0.07, 0.09, axis='x'); K.obj(bm, M['paint'], RED)
    post(0, 3.0, 2.2); K.obj(lathe([(0.0, 0.0), (0.36, 0.0), (0.36, 0.03), (0.0, 0.03)], 20, 0, 0, 0) if False else _sign_disc(0.07, 3.0, 1.95, 0.36), M['paint'], (0.05, 0.22, 0.55))
    K.obj(_sign_disc(0.09, 3.0, 1.95, 0.28), M['paint'], (0.9, 0.9, 0.88))
    post(0, 4.4, 2.2); K.obj(_sign_tri(0.07, 4.4, 1.85, 0.5), M['paint'], RED); K.obj(_sign_tri(0.09, 4.4, 1.88, 0.38), M['paint'], (0.9, 0.9, 0.88))
    post(0.4, 6.0, 3.0); K.obj(lathe([(0.0, 0.0), (0.42, 0.0), (0.45, 0.06), (0.0, 0.1)], 18, 0, 0, 0) if False else _sign_disc(0.45, 6.0, 2.9, 0.45), M['paint'], (0.8, 0.3, 0.05))
    K.obj(_sign_disc(0.5, 6.0, 2.9, 0.38), M['galv'], (0.85, 0.88, 0.9))


def _sign_disc(x, y, z, r, n=20):
    bm = bmesh.new(); c0 = bm.verts.new((x, y, z)); rim = [bm.verts.new((x, y + r * math.cos(2 * math.pi * k / n), z + r * math.sin(2 * math.pi * k / n))) for k in range(n)]
    for k in range(n): bm.faces.new((c0, rim[k], rim[(k + 1) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.x < 0: f.normal_flip()
    return bm


def _sign_tri(x, y, z, s):
    bm = bmesh.new(); vs = [bm.verts.new((x, y - s, z - s * 0.55)), bm.verts.new((x, y + s, z - s * 0.55)), bm.verts.new((x, y, z + s * 1.1))]; bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.x < 0: f.normal_flip()
    return bm


def windpump(K, M):
    """Desert windpump: lattice steel tower, multi-blade wheel and tail vane, a corrugated water tank on stilts and a stone trough."""
    h = 9.0
    for (x, y) in ((-1.2, -1.2), (-1.2, 1.2), (1.2, -1.2), (1.2, 1.2)): K.obj(sweep([(x, y, 0), (x * 0.18, y * 0.18, h)], 0.05, 5), M['galv'], (0.55, 0.52, 0.48))
    for z in np.arange(1.5, h, 1.5):
        f = 1 - 0.82 * z / h; c = [(-1.2 * f, -1.2 * f), (1.2 * f, -1.2 * f), (1.2 * f, 1.2 * f), (-1.2 * f, 1.2 * f)]
        for k in range(4): K.obj(sweep([(c[k][0], c[k][1], z), (c[(k + 1) % 4][0], c[(k + 1) % 4][1], z)], 0.025, 4), M['galv'], (0.55, 0.52, 0.48))
    hub = (0.5, 0, h + 0.3)
    for k in range(18):                                                                                # sheet-steel blades
        a = k * 2 * math.pi / 18; c, s = math.cos(a), math.sin(a)
        bm = bmesh.new(); vs = [bm.verts.new((hub[0] + 0.05 * ((-1) ** j), hub[1] + rr * c - w * s, hub[2] + rr * s + w * c)) for j, (rr, w) in enumerate(((0.45, -0.06), (1.6, -0.14), (1.6, 0.14), (0.45, 0.06)))]
        bm.faces.new(vs); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.01)
        K.obj(bm, M['galv'], (0.7, 0.68, 0.64), 'box', 1.0, 0.0, smooth=False)
    for rr in (0.45, 1.6): K.obj(lathe([(rr, -0.02), (rr + 0.03, 0.0), (rr, 0.02)], 24) if False else _ring(hub, rr), M['galv'], (0.55, 0.52, 0.48))
    K.obj(sweep([(0.5, 0, h + 0.3), (-2.2, 0, h + 0.4)], 0.04, 5), M['galv'], (0.55, 0.52, 0.48))
    K.obj(bbox(-2.6, 0, h + 0.5, 1.2, 0.02, 0.9), M['paint'], (0.75, 0.2, 0.08))
    K.obj(sweep([(0, 0, 0.0), (0, 0, h)], 0.02, 4), M['galv'], (0.4, 0.4, 0.4))
    for (x, y) in ((3.0, -1.0), (3.0, 1.0), (5.0, -1.0), (5.0, 1.0)): K.obj(bbox(x, y, 1.0, 0.18, 0.18, 2.0), M['wood'], TIMBER)
    K.obj(lathe([(1.3, 0.0), (1.3, 1.6), (1.32, 1.62), (0.0, 1.9)], 20, 4.0, 0, 2.0), M['corr'], (0.6, 0.6, 0.58), 'cyl', 0.8)
    K.obj(sweep([(0, 0, 1.0), (2.8, 0, 3.0)], 0.04, 5), M['galv'], (0.4, 0.4, 0.4))
    K.obj(bbox(4.0, -3.0, 0.35, 3.2, 0.9, 0.7), M['ashlar'], STONE, 'box', 1.0, 0.03, 2); K.obj(bbox(4.0, -3.0, 0.62, 2.9, 0.65, 0.04), M['smooth'], (0.06, 0.15, 0.16))


def _ring(c, r, n=24, t=0.025):
    pts = [(c[0], c[1] + r * math.cos(2 * math.pi * k / n), c[2] + r * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]
    return sweep(pts, t, 4)


def desert_stop(K, M):
    """Desert roadside stop: weathered timber billboard on poles, oil drums, a tyre stack, a water-bag post and a broken fence."""
    for y in (-2.2, 2.2): K.obj(sweep([(0, y, 0), (0, y, 4.6)], 0.09, 6), M['wood'], (0.45, 0.36, 0.26))
    K.obj(bbox(0.08, 0, 3.4, 0.08, 5.6, 2.2), M['boards'], (0.75, 0.62, 0.45), 'boxv', 1.0, 0.01, 1)
    K.obj(bbox(0.13, 0, 3.4, 0.02, 5.0, 1.7), M['ads'], (0.85, 0.75, 0.6), 'sign', 1.0, sign=P.ad_uv_frame(__import__('isle_houses').Frame((0.14, 0, 0), (0, 1, 0), (1, 0, 0)), 3, 0.0, 3.4, 5.0, 1.7))
    for (x, y, col) in ((1.6, -1.0, (0.45, 0.08, 0.04)), (2.1, -0.4, (0.05, 0.18, 0.35)), (1.5, 0.3, (0.45, 0.3, 0.06))):
        K.obj(lathe([(0.0, 0.0), (0.29, 0.0), (0.29, 0.88), (0.0, 0.88)], 14, x, y, 0), M['paint'], col, 'cyl', 1.0)
        for z in (0.3, 0.6): K.obj(lathe([(0.29, z - 0.02), (0.31, z), (0.29, z + 0.02)], 14, x, y, 0), M['paint'], tuple(np.asarray(col) * 0.8))
    for k in range(4):
        t = lathe([(0.2, -0.1), (0.32, -0.11), (0.34, 0.0), (0.32, 0.11), (0.2, 0.1)], 14, 2.8, 1.6, 0.12 + k * 0.22)
        K.obj(t, M['concrete'], (0.04, 0.04, 0.04), 'cyl', 1.0)
    rng = np.random.default_rng(97)
    for k in range(6):
        y = 3.5 + k * 1.6; K.obj(bbox(rng.uniform(-0.1, 0.1), y, 0.55, 0.1, 0.1, 1.1, rng.uniform(-0.1, 0.1)), M['wood'], (0.5, 0.42, 0.32))
        if k < 5 and k != 2: K.obj(sweep([(0.05, y, 0.85), (0.05, y + 1.6, 0.85 + rng.uniform(-0.15, 0.1))], 0.005, 3), M['galv'], (0.5, 0.45, 0.4))


def lookout(K, M):
    """Mountain lookout: a stone-walled terrace with a timber shelter roof, a coin binocular viewer, an orientation table and a bench."""
    K.obj(bbox(0, 0, -0.15, 8.0, 10.0, 0.5), M['pave'] if 'pave' in M else M['concrete'], (0.75, 0.72, 0.66), 'box', 2.0)
    for (cx, cy, sx, sy) in ((4.0, 0, 0.5, 10.0), (0, 5.0, 8.0, 0.5), (0, -5.0, 8.0, 0.5)):
        K.obj(bbox(cx, cy, 0.45, sx, sy, 0.9), M['ashlar'], STONE, 'box', 1.2, 0.02, 2)
        K.obj(bbox(cx, cy, 0.95, sx + 0.12, sy + 0.12, 0.12), M['ashlar'], (0.9, 0.86, 0.78), 'box', 1.2, 0.015, 1)
    for (x, y) in ((-3.5, -2.5), (-3.5, 2.5), (-1.0, -2.5), (-1.0, 2.5)): K.obj(bbox(x, y, 1.3, 0.2, 0.2, 2.6), M['wood'], TIMBER, 'box', 1.0, 0.012, 2)
    roof = prism([(-4.2, 2.45), (-0.3, 3.0), (-0.3, 3.12), (-4.2, 2.57)], -3.2, 3.2, axis='x')
    for v in roof.verts: a, b, c = v.co; v.co = (b, a, c)
    K.obj(roof, M['boards'], (0.5, 0.36, 0.22), 'box', 1.0, 0.0, smooth=False)
    K.obj(bbox(-3.2, 0, 0.45, 0.45, 4.0, 0.06), M['wood'], (0.55, 0.38, 0.22), 'box', 1.0, 0.01, 1); K.obj(bbox(-3.42, 0, 0.75, 0.06, 4.0, 0.5), M['wood'], (0.55, 0.38, 0.22))
    K.obj(lathe([(0.0, 0.0), (0.2, 0.0), (0.08, 0.1), (0.06, 1.05), (0.0, 1.1)], 10, 3.0, -2.0, 0), M['paint'], (0.05, 0.25, 0.4), 'cyl', 1.0)       # binocular viewer
    K.obj(bbox(3.0, -2.0, 1.22, 0.4, 0.3, 0.25), M['paint'], (0.05, 0.25, 0.4), 'box', 1.0, 0.03, 2)
    for sg in (-1, 1): K.obj(lathe([(0.0, 0.0), (0.06, 0.0), (0.06, 0.18), (0.0, 0.18)], 10) if False else bbox(3.25, -2.0 + sg * 0.08, 1.25, 0.15, 0.07, 0.07), M['iron'], IRON)
    K.obj(lathe([(0.0, 0.0), (0.18, 0.0), (0.1, 0.1), (0.1, 0.9), (0.45, 0.95), (0.45, 1.0), (0.0, 1.0)], 16, 2.6, 2.0, 0), M['ashlar'], STONE, 'cyl', 1.0)   # orientation table
    K.obj(lathe([(0.0, 0.0), (0.42, 0.0), (0.42, 0.02), (0.0, 0.03)], 20, 2.6, 2.0, 1.0), M['galv'], (0.65, 0.5, 0.3))


def _rock_material():
    """Photo-scanned rock for the kit (kept with the other kit materials)."""
    M = P.mats()
    if 'rock' not in M:
        import isle_lib as L
        img = L.make_image('kit_Rock051', P._col('Rock051', 0.5, 0.1, 0.55)); n = P._rawrect('Rock051', 'NormalGL'); r = P._rawrect('Rock051', 'Roughness')
        orm = L.make_image('kit_Rock051_orm', np.dstack([np.ones(r.shape[:2]), np.clip(r[..., 0] * 0.9 + 0.08, 0.3, 1), np.zeros(r.shape[:2])]), raw=True)
        M['rock'] = L.new_mat('KitRock', image=img, vcol=True, normal=L.make_image('kit_Rock051_n', n[..., :3], raw=True), nstrength=1.0, orm=orm)
    return M


ITEMS = dict(boulders=(boulders, 2.2), hoodoo=(hoodoo, 7.6), cliff=(lambda K, M: cliff(K, M), 11.0), cliff_sand=(lambda K, M: cliff(K, M, sand=True), 11.0), scree=(scree, 2.6),
             guardrail_hq=(guardrail, 1.0), parapet=(parapet, 1.5), tunnel_portal=(tunnel_portal, 13.1), tunnel_portal_5=(lambda K, M: tunnel_portal(K, M, 5.0, bore=False), 11.0), tunnel_portal_7=(lambda K, M: tunnel_portal(K, M, 7.0, bore=False), 11.0), tunnel_portal_6=(lambda K, M: tunnel_portal(K, M, 6.0, bore=False), 11.0), catch_fence=(catch_fence, 4.2),
             mountain_signs=(mountain_signs, 3.4), windpump=(windpump, 11.0), desert_stop=(desert_stop, 4.6), lookout=(lookout, 3.1))


def register():
    _rock_material()
    for k, (fn, h) in ITEMS.items(): P.PROPS[k] = (fn, {}); P.HEIGHT[k] = h

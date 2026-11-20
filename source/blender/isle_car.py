"""Aurelia GT: an original two-door sports car, lofted from smooth cross-sections (body, glasshouse), with modelled wheels,
lights, grille and mirrors. Used two ways: as the player car (Blender object tree, wheel arches cut with booleans, exported
GLB) and, at low resolution, as the parked cars of the map (vertex-coloured mesh). Car frame: x forward, y left, z up."""
import math
import numpy as np

PAINT, GLASS, BLACK, CHROME, LAMP_F, LAMP_R, TYRE, RIM = range(8)


def spec(kind=0):
    """kind 0: sports coupe, 1: hatchback, 2: van."""
    if kind == 1: return dict(L=4.15, W=0.89, U=[-1, -0.97, -0.8, 0, 0.75, 0.93, 1], Wc=[0.82, 0.88, 0.91, 0.92, 0.9, 0.84, 0.70], floor=0.2, belt=[0.86, 0.9, 0.9, 0.86, 0.78, 0.66, 0.54], cab=(-0.93, 0.36), roof=[1.42, 1.46, 1.42, 1.25], top=0.8)
    if kind == 3: return dict(L=4.8, W=0.93, U=[-1, -0.97, -0.82, 0, 0.72, 0.93, 1], Wc=[0.82, 0.9, 0.94, 0.95, 0.93, 0.86, 0.72], floor=0.22, belt=[0.82, 0.9, 0.92, 0.88, 0.8, 0.7, 0.6], cab=(-0.5, 0.3), roof=[1.38, 1.45, 1.44, 1.3], top=0.76, cp=0.22, se=5.0)   # saloon
    if kind == 4: return dict(L=4.65, W=0.98, U=[-1, -0.97, -0.8, 0, 0.75, 0.93, 1], Wc=[0.86, 0.94, 0.97, 0.98, 0.96, 0.9, 0.76], floor=0.34, belt=[1.0, 1.06, 1.08, 1.04, 0.98, 0.88, 0.74], cab=(-0.9, 0.42), roof=[1.74, 1.8, 1.8, 1.72], top=0.88, cp=0.12, se=7.0)   # SUV
    if kind == 2: return dict(L=4.85, W=0.98, U=[-1, -0.98, -0.8, 0, 0.75, 0.93, 1], Wc=[0.93, 0.97, 0.98, 0.98, 0.96, 0.9, 0.78], floor=0.24, belt=[1.0, 1.04, 1.04, 1.0, 0.95, 0.84, 0.66], cab=(-0.97, 0.55), roof=[1.95, 1.98, 1.96, 1.7], top=0.9)
    return dict(L=4.5, W=0.95, U=[-1, -0.97, -0.85, 0, 0.7, 0.92, 1], Wc=[0.80, 0.90, 0.95, 0.96, 0.94, 0.86, 0.70], floor=0.2, belt=[0.7, 0.86, 0.9, 0.86, 0.78, 0.66, 0.55], cab=(-0.6, 0.4), roof=[1.16, 1.25, 1.21, 1.06], top=0.68)


def superellipse(n, m, half=False):
    t = np.linspace(0, np.pi, m) if half else np.arange(m) * 2 * np.pi / m
    c, s = np.cos(t), np.sin(t)
    return np.sign(c) * np.abs(c) ** (2 / n), np.sign(s) * np.abs(s) ** (2 / n)


def loft(R):
    """R: (stations, ring, 3) closed rings. Faces between stations plus fan caps at both ends."""
    S, M, _ = R.shape; V = R.reshape(-1, 3); F = []
    for i in range(S - 1):
        for j in range(M):
            a = i * M + j; b = i * M + (j + 1) % M; F += [(a, b, b + M), (a, b + M, a + M)]
    V = np.vstack([V, R[0].mean(0), R[-1].mean(0)]); c0, c1 = len(V) - 2, len(V) - 1
    for j in range(M): F += [(c0, (j + 1) % M, j), (c1, (S - 1) * M + j, (S - 1) * M + (j + 1) % M)]
    return V, np.array(F)


def body(kind=0, S=36, M=28):
    sp = spec(kind); hl = sp['L'] / 2; u = np.sign(np.linspace(-1, 1, S)) * np.abs(np.linspace(-1, 1, S)) ** 0.8
    w = sp['W'] * np.interp(u, sp['U'], sp['Wc']); z0 = sp['floor'] + 0.14 * np.clip((np.abs(u) - 0.88) / 0.12, 0, 1)
    z1 = np.interp(u, sp['U'], sp['belt']); cy, cz = superellipse(3.2, M)
    R = np.empty((S, M, 3)); R[..., 0] = (u * hl)[:, None]; R[..., 1] = w[:, None] * cy[None]; R[..., 2] = ((z0 + z1) / 2)[:, None] + ((z1 - z0) / 2)[:, None] * cz[None]
    R[..., 1] *= (1 - 0.1 * np.clip(-cz, 0, 1) ** 2)[None]                    # tumblehome under the sill
    return loft(R)


def cabin(kind=0, S=20, M=14):
    sp = spec(kind); hl = sp['L'] / 2; a, b = sp['cab']; u = np.linspace(a, b, S); z1 = np.interp(u, sp['U'], sp['belt'])
    zr = np.interp(u, np.linspace(a, b, 4), sp['roof']); h = (zr - z1) * np.sin(np.pi * np.clip((u - a) / (b - a), 0, 1)) ** sp.get('cp', 0.35)
    w = sp['W'] * np.interp(u, sp['U'], sp['Wc']) * 0.92; cy, cz = superellipse(sp.get('se', 4.0), M, half=True)
    R = np.empty((S, M, 3)); R[..., 0] = (u * hl)[:, None]
    taper = 1 - (1 - sp['top']) * cz[None]; R[..., 1] = (w[:, None] * cy[None]) * taper; R[..., 2] = z1[:, None] - 0.02 + h[:, None] * cz[None]
    return loft(R), zr


def parts(kind=0, res=1.0):
    """List of (V, F, part) in the car frame."""
    out = []; sp = spec(kind); hl = sp['L'] / 2
    V, F = body(kind, max(10, int(36 * res)), max(10, int(28 * res) // 2 * 2))
    fc = V[F].mean(1); n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-9)[:, None]
    low = (fc[:, 2] < sp['floor'] + 0.16) | (n[:, 2] < -0.55)
    out += [(V, F[~low], PAINT), (V, F[low], BLACK)]
    Sc, Mc = max(8, int(20 * res)), max(8, int(14 * res) // 2 * 2); (V, F), zr = cabin(kind, Sc, Mc)
    st = np.minimum(F, Sc * Mc - 1) // Mc; ring = np.minimum(F, Sc * Mc - 1) % Mc; inner = (F < Sc * Mc).all(1)
    roof = inner & (ring.min(1) >= 2) & (ring.max(1) <= Mc - 3) & (st.min(1) >= int(Sc * 0.3)) & (st.max(1) <= int(Sc * 0.72))      # roof panel; screens and side glass round it
    out += [(V, F[~roof], GLASS), (V, F[roof], PAINT)]
    def bx(cx, cy, cz, sx, sy, sz, part, n_=6):
        a = np.array([[(i & 1) - .5, ((i >> 1) & 1) - .5, ((i >> 2) & 1) - .5] for i in range(8)]) * (sx, sy, sz) + (cx, cy, cz)
        F_ = np.array([(0, 2, 3), (0, 3, 1), (4, 5, 7), (4, 7, 6), (0, 1, 5), (0, 5, 4), (2, 6, 7), (2, 7, 3), (0, 4, 6), (0, 6, 2), (1, 3, 7), (1, 7, 5)]); out.append((a, F_, part))
    def surf(u, yf):                                                                                          # height of the body top at station u, fraction yf of the half width
        z0 = sp['floor'] + 0.14 * np.clip((abs(u) - 0.88) / 0.12, 0, 1); z1 = np.interp(u, sp['U'], sp['belt']); cz = (1 - abs(yf) ** 3.2) ** (1 / 3.2)
        return (z0 + z1) / 2 + (z1 - z0) / 2 * cz, sp['W'] * np.interp(u, sp['U'], sp['Wc'])
    for s in (-1, 1):
        zh, wu = surf(0.88, 0.6); bx(hl * 0.88, s * wu * 0.6, zh - 0.035, 0.3, wu * 0.34, 0.05, LAMP_F)              # headlight lenses set into the nose
        zt, wt = surf(-0.97, 0.55); bx(-hl * 0.975, s * wt * 0.55, zt - 0.09, 0.07, wt * 0.6, 0.07, LAMP_R)          # tail light bars
        um = sp['cab'][1] - 0.02; zm = np.interp(um, sp['U'], sp['belt']); wm = sp['W'] * np.interp(um, sp['U'], sp['Wc']) * 0.92
        bx(hl * um, s * (wm + 0.07), zm + 0.08, 0.12, 0.2, 0.11, PAINT); bx(hl * um, s * (wm - 0.02), zm + 0.04, 0.06, 0.14, 0.05, BLACK)   # mirror and stalk
    wf = sp['W'] * np.interp(0.97, sp['U'], sp['Wc'])
    bx(hl * 0.995, 0, sp['floor'] + 0.2, 0.04, wf * 1.0, 0.13, BLACK)                                        # grille / intake
    bx(-hl * 0.995, 0, sp['floor'] + 0.17, 0.04, wf * 1.3, 0.09, BLACK)                                       # diffuser
    return out


def wheel(r=0.34, wdt=0.25, res=1.0, spokes=5):
    """Wheel about its own centre, axle along y. Returns list of (V, F, part)."""
    n = max(10, int(28 * res)); a = np.arange(n) * 2 * np.pi / n; out = []
    prof = [(0.66, -0.5), (0.86, -0.5), (0.97, -0.42), (1.0, -0.25), (1.0, 0.25), (0.97, 0.42), (0.86, 0.5), (0.66, 0.5)]
    def lathe(prof, part):
        k = len(prof); V = np.array([(rr * r * math.cos(t), yy * wdt, rr * r * math.sin(t)) for t in a for rr, yy in prof]); F = []
        for i in range(n):
            for j in range(k - 1):
                p = i * k + j; q = ((i + 1) % n) * k + j; F += [(p, q, q + 1), (p, q + 1, p + 1)]
        out.append((V, np.array(F), part))
    lathe(prof, TYRE)
    lathe([(0.66, 0.5), (0.6, 0.46), (0.6, -0.2), (0.66, -0.5)], RIM)                                          # rim barrel
    hub = [(0.0, 0.42), (0.16, 0.42), (0.2, 0.36)]; lathe(hub, CHROME)
    for k in range(spokes if res >= 1 else 0):                                                                 # spokes, outer face
        t = k * 2 * np.pi / spokes
        for dt_ in (-0.09, 0.09):
            p0 = np.array([0.18 * r * math.cos(t + dt_ * 1.6), 0.4 * wdt, 0.18 * r * math.sin(t + dt_ * 1.6)]); p1 = np.array([0.6 * r * math.cos(t + dt_), 0.44 * wdt, 0.6 * r * math.sin(t + dt_)])
            if dt_ < 0: q0, q1 = p0, p1
        V = np.array([q0, q1, p1, p0, q0 - (0, 0.08, 0), q1 - (0, 0.08, 0), p1 - (0, 0.08, 0), p0 - (0, 0.08, 0)])
        out.append((V, np.array([(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5), (0, 5, 1), (3, 2, 6), (3, 6, 7)]), RIM))
    return out


WHEEL_POS = {0: (1.42, -1.38, 0.34), 1: (1.27, -1.25, 0.32), 2: (1.6, -1.55, 0.36), 3: (1.45, -1.42, 0.33), 4: (1.42, -1.4, 0.39)}
COLOURS = {PAINT: None, GLASS: (0.02, 0.03, 0.04), BLACK: (0.025, 0.025, 0.028), CHROME: (0.7, 0.71, 0.73), LAMP_F: (0.9, 0.9, 0.85), LAMP_R: (0.55, 0.03, 0.02), TYRE: (0.02, 0.02, 0.02), RIM: (0.55, 0.56, 0.58)}


def low_mesh(kind, colour, res=0.45, wres=0.4):
    """One vertex-coloured mesh (car frame) for parked cars."""
    Vs, Fs, Cs = [], [], []; off = 0; sp = spec(kind); wx = sp['W'] * 0.9
    items = parts(kind, res)
    fx, rx, r = WHEEL_POS[kind]
    for x in (fx, rx):
        for s in (-1, 1):
            if wres >= 0.3: W_ = wheel(r, 0.24, wres)
            else:                                                                                             # cheap wheel: tyre band and a rim disc
                n = 10; a = np.arange(n) * 2 * np.pi / n; ring = np.c_[np.cos(a), np.zeros(n), np.sin(a)] * r
                Vt = np.vstack([ring + (0, -0.12, 0), ring + (0, 0.12, 0)]); i = np.arange(n); j = (i + 1) % n
                Vr = np.vstack([ring * 0.62 + (0, 0.125, 0), [(0, 0.125, 0)]])
                W_ = [(Vt, np.vstack([np.c_[i, j, n + j], np.c_[i, n + j, n + i]]), TYRE), (Vr, np.c_[i, j, np.full(n, n)], RIM)]
            for V, F, p in W_:
                V = V * (1, s, 1) if wres < 0.3 else V
                items.append((V + (x, s * (wx - 0.1), r), F, p))
    for V, F, p in items:
        if not len(F): continue
        used = np.unique(F); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
        c = np.asarray(colour if COLOURS[p] is None else COLOURS[p], float)
        Vs.append(V[used]); Fs.append(remap[F] + off); Cs.append(np.tile(c, (len(used), 1))); off += len(used)
    return np.vstack(Vs), np.vstack(Fs), np.vstack(Cs)


def build_blender(name='Aurelia_GT', colour=(0.55, 0.02, 0.03)):
    """Player car as a Blender object tree in Blender axes (forward -Y, axle along X so the game spins wheels about local X)."""
    import bpy
    def to_b(V): V = np.asarray(V, float); return np.c_[V[:, 1], -V[:, 0], V[:, 2]]
    mats = {}
    def mat(p):
        if p in mats: return mats[p]
        m = bpy.data.materials.new({PAINT: 'Car_Paint', GLASS: 'Car_Glass', BLACK: 'Car_Trim', CHROME: 'Car_Chrome', LAMP_F: 'Car_Headlight', LAMP_R: 'Car_Taillight', TYRE: 'Car_Tyre', RIM: 'Car_Rim'}[p]); m.use_nodes = True
        b = m.node_tree.nodes['Principled BSDF']; c = colour if p == PAINT else COLOURS[p]; b.inputs['Base Color'].default_value = (*c, 1)
        b.inputs['Roughness'].default_value = {PAINT: 0.22, GLASS: 0.04, BLACK: 0.55, CHROME: 0.15, LAMP_F: 0.1, LAMP_R: 0.2, TYRE: 0.9, RIM: 0.25}[p]
        b.inputs['Metallic'].default_value = {PAINT: 0.55, CHROME: 1.0, RIM: 0.9}.get(p, 0.0)
        if p == PAINT:
            try: b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.03
            except Exception: pass
        if p in (LAMP_F, LAMP_R): b.inputs['Emission Color'].default_value = (*c, 1); b.inputs['Emission Strength'].default_value = 0.6
        if p == GLASS:
            b.inputs['Alpha'].default_value = 0.9
            try: m.surface_render_method = 'BLENDED'
            except Exception: pass
        mats[p] = m; return m
    def obj(nm, items, parent=None, smooth=True):
        Vs, Fs, P = [], [], []; off = 0
        for V, F, p in items:
            if not len(F): continue
            Vs.append(to_b(V)); Fs.append(np.asarray(F)[:, ::-1] + off if False else np.asarray(F) + off); P.append(np.full(len(F), p)); off += len(V)
        V = np.vstack(Vs); F = np.vstack(Fs); P = np.concatenate(P); pl = sorted(set(P.tolist()))
        me = bpy.data.meshes.new(nm); me.from_pydata(V.tolist(), [], F.tolist()); me.update()
        for p in pl: me.materials.append(mat(p))
        me.polygons.foreach_set('material_index', np.array([pl.index(p) for p in P], np.int32)); me.polygons.foreach_set('use_smooth', np.full(len(F), smooth))
        o = bpy.data.objects.new(nm, me); bpy.context.scene.collection.objects.link(o)
        if parent: o.parent = parent
        return o
    root = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(root)
    items = parts(0, 1.0); bodyo = obj(name + '_Body', items[0:2], root)
    obj(name + '_Glasshouse', items[2:4], root)
    obj(name + '_Details', items[4:], root, smooth=False)
    fx, rx, r = WHEEL_POS[0]; wx = spec(0)['W'] * 0.9
    bodyo.data.update()
    for nm_, x in (('F', fx), ('R', rx)):                                                                     # cut the wheel arches
        for s, side in ((1, 'L'), (-1, 'R')):
            bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r + 0.06, depth=0.7, location=(s * (wx + 0.15), -x, r), rotation=(0, math.pi / 2, 0)); cut = bpy.context.active_object
            md = bodyo.modifiers.new('arch', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cut; md.solver = 'EXACT'
            with bpy.context.temp_override(object=bodyo, active_object=bodyo, selected_objects=[bodyo]): bpy.ops.object.modifier_apply(modifier='arch')
            bpy.data.objects.remove(cut)
            w = obj('Wheel_%s%s' % (nm_, side), [(np.c_[-V[:, 1] * s, V[:, 0], V[:, 2]] if False else V, F, p) for V, F, p in wheel(r, 0.25)], root)
            # wheel mesh is built in the car frame with the axle along y; move to its hub, axle lies along Blender X after to_b
            w.location = (s * (wx - 0.12), -x, r)
            if s < 0: w.scale = (1, 1, 1); w.rotation_euler = (0, 0, math.pi)
    return root

"""Art sheet 12: traffic cars for Aurelia Island, second generation. Original designs (no real makes): hatchback, saloon, estate, SUV,
panel van, pickup, and a taxi version of the saloon.

Each body is one loft: 41 stations along the car, each a closed section ring that runs from the floor round the sill, door and shoulder,
then either over the bonnet/boot or up the glasshouse and across the roof. A Subdivision Surface smooths it; wheel arches are cut with
booleans. Faces are then sorted into paint, glass, black trim, pillars and lower cladding by where they lie, and panel gaps, lights,
grilles, mirrors, handles, plates, wipers and five-spoke alloy wheels are added as parts.
Axes as isle_traffic: +X forward, +Y left, Z up, origin on the ground between the axles. Paint is white (the game tints it per car)."""
import math
import numpy as np
import bpy
import bmesh

PAINT, GLASS, BLACK, CHROME, LAMP_F, LAMP_R, TYRE, RIM, PLATE, AMBER, CLAD, DISC = range(12)
COLOURS = {PAINT: (0.999, 0.999, 0.999), GLASS: (0.02, 0.03, 0.04), BLACK: (0.03, 0.03, 0.033), CHROME: (0.75, 0.76, 0.78),
           LAMP_F: (0.95, 0.96, 0.95), LAMP_R: (0.62, 0.03, 0.02), TYRE: (0.022, 0.022, 0.024), RIM: (0.66, 0.67, 0.7), PLATE: (0.94, 0.94, 0.9),
           AMBER: (0.98, 0.52, 0.06), CLAD: (0.07, 0.07, 0.075), DISC: (0.32, 0.31, 0.3)}

# Per type. L length, W half width, r wheel radius, ax axle x (front, rear), hb hood/boot height at the ends and middle,
# zs shoulder (belt) height, zb sill height, cab = (u windscreen base, u roof front, u roof rear, u backlight base, roof z, roof half width factor),
# nose/tail rounding, extra flags.
TYPES = {
    'hatch':  dict(L=4.06, W=0.88, r=0.315, ax=(1.29, -1.25), zb=0.20, zs=0.86, hood=(0.74, 0.92), deck=(0.98, 0.98), cab=(0.30, -0.05, -0.80, -0.97, 1.47, 0.80), nose=0.55, tail=0.25),
    'sedan':  dict(L=4.82, W=0.91, r=0.325, ax=(1.47, -1.42), zb=0.20, zs=0.90, hood=(0.76, 0.95), deck=(0.96, 1.02), cab=(0.34, 0.06, -0.38, -0.66, 1.45, 0.80), nose=0.5, tail=0.4),
    'estate': dict(L=4.86, W=0.91, r=0.325, ax=(1.48, -1.43), zb=0.20, zs=0.90, hood=(0.76, 0.95), deck=(0.98, 0.98), cab=(0.34, 0.06, -0.86, -0.97, 1.48, 0.79), nose=0.5, tail=0.22),
    'suv':    dict(L=4.64, W=0.95, r=0.37, ax=(1.42, -1.40), zb=0.33, zs=1.08, hood=(0.98, 1.14), deck=(1.14, 1.14), cab=(0.38, 0.12, -0.84, -0.96, 1.80, 0.82), nose=0.45, tail=0.2, clad=True, rails=True),
    'van':    dict(L=5.08, W=0.99, r=0.35, ax=(1.66, -1.62), zb=0.30, zs=1.08, hood=(0.92, 1.12), deck=(2.1, 2.1), cab=(0.62, 0.42, -0.99, -0.995, 2.14, 0.94), nose=0.5, tail=0.08, cargo=True),
    'pickup': dict(L=5.20, W=0.96, r=0.39, ax=(1.62, -1.58), zb=0.38, zs=1.12, hood=(1.02, 1.18), deck=(1.12, 1.12), cab=(0.46, 0.22, -0.18, -0.24, 1.86, 0.84), nose=0.4, tail=0.1, clad=True, bed=True),
}
TYPES['taxi'] = dict(TYPES['sedan'], taxi=True)
NS = 41                                                                                   # stations along the car


def _smooth01(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


def stations(sp, ns=None):
    """Per station: x, half width, sill z, belt z, top z (bonnet/boot/roof), roof half width, glasshouse weight (0..1)."""
    ns = ns or NS; L, W = sp['L'], sp['W']; hl = L / 2; u = np.linspace(-1, 1, ns)
    ua, ub, uc, ud, zr, wr = sp['cab']
    w = W * (1 - sp['nose'] * 0.30 * _smooth01((u - 0.74) / 0.26) ** 2.0 - sp['tail'] * 0.3 * _smooth01((-u - 0.8) / 0.2) ** 2.0)
    w = w * (1 - 0.35 * _smooth01((u - 0.93) / 0.07) ** 1.5 - 0.2 * _smooth01((-u - 0.95) / 0.05) ** 1.5)          # the last stations close in to form the nose and tail faces
    zb = sp['zb'] + 0.12 * _smooth01((u - 0.8) / 0.2) + 0.14 * _smooth01((-u - 0.84) / 0.16)
    zs = sp['zs'] - 0.12 * _smooth01((u - 0.7) / 0.3) - 0.04 * _smooth01((-u - 0.85) / 0.15)
    hood = np.interp(u, [ua, 1.0], [sp['hood'][1], sp['hood'][0]]) - 0.1 * _smooth01((u - 0.9) / 0.1)
    deck = np.interp(u, [-1.0, ud], [sp['deck'][0], sp['deck'][1]]) - (0.08 if not sp.get('cargo') else 0.25) * _smooth01((-u - 0.92) / 0.08)
    top = np.where(u > (ua + ud) / 2, hood, deck); top = np.maximum(top, zs + 0.035)
    cab = np.zeros(ns); zroof = np.copy(top)
    for i, x in enumerate(u):
        if ud <= x <= ua:
            if x > ub: t = (ua - x) / max(ua - ub, 1e-3); zz = top[i] + (zr - top[i]) * np.sin(t * np.pi / 2) ** 0.85
            elif x >= uc: zz = zr - 0.015 * ((x - (ub + uc) / 2) / max(ub - uc, 1e-3)) ** 2
            else: t = (x - ud) / max(uc - ud, 1e-3); zz = top[i] + (zr - top[i]) * np.sin(t * np.pi / 2) ** 0.7
            zroof[i] = max(zz, top[i]); cab[i] = 1.0
    if sp.get('cargo'): zroof = np.where(u < ub, np.maximum(zroof, zr) - 0.25 * _smooth01((-u - 0.94) / 0.06), zroof); cab = np.where(u < ua, 1.0, cab)
    cabw = np.clip(np.convolve(cab, np.ones(3) / 3, mode='same'), 0, 1); cabw[cab > 0.5] = 1.0
    rw = W * wr * (1 - 0.05 * np.abs(u))
    return u * hl, w, zb, zs, zroof, rw, cabw


def ring(w, zb, zs, ztop, rw, cab):
    """Half section, 12 points from the floor centre to the top centre (design lines: sill, lamp band, shoulder, glass base, roof rail);
    the glasshouse and the bonnet/boot shapes are blended by the cab weight so the pillars grow smoothly out of the body."""
    zl0, zl1 = zs - 0.31, zs - 0.12
    base = [(0.0, zb), (w * 0.86, zb), (w * 0.975, zb + 0.06), (w, zb + 0.17), (w, zl0), (w * 0.995, zl1), (w * 0.97, zs), (w * 0.935, zs + 0.035)]
    deck = [(w * 0.84, ztop - 0.012), (w * 0.6, ztop - 0.002), (w * 0.3, ztop + 0.003), (0.0, ztop + 0.005)]
    glas = [(rw * 1.04, ztop - 0.075), (rw * 0.92, ztop - 0.012), (rw * 0.45, ztop + 0.006), (0.0, ztop + 0.008)]
    up = [(d[0] * (1 - cab) + g[0] * cab, d[1] * (1 - cab) + g[1] * cab) for d, g in zip(deck, glas)]
    h = base + up
    return h + [(-y, z) for (y, z) in reversed(h[1:-1])]


def _obj(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob


def _eval(ob):
    dg = bpy.context.evaluated_depsgraph_get(); e = ob.evaluated_get(dg); bm = bmesh.new(); bm.from_mesh(e.to_mesh()); e.to_mesh_clear(); return bm


def _zone(sp, uu, seg, cab):
    """Material of a cage face from its station (u, -1 tail .. 1 nose) and half-section segment (0 floor .. 10 roof centre)."""
    ua, ub, uc, ud, zr, wr = sp['cab']; clad = sp.get('clad')
    if seg <= 1: return BLACK
    if seg == 2: return CLAD if clad else PAINT
    if uu > 0.9:                                                                      # front: lower intake, lamp band wrapping the corner, grille in the middle
        if seg == 3: return BLACK if uu > 0.94 else (CLAD if clad else PAINT)
        if seg == 4: return LAMP_F if uu < 0.975 else BLACK
    if uu < -0.9:                                                                     # rear: lamp band wrapping the corner, lower bumper insert
        if seg == 4: return LAMP_R if uu > -0.985 else PAINT
        if seg == 3 and uu < -0.95: return BLACK
    if cab > 0.5:
        hl_cab = ud < uu < ua
        if seg == 7 and hl_cab:                                                       # side glass between the pillars
            if sp.get('cargo') and uu < ub - 0.08: return PAINT
            if uu > ua - 0.05 or uu < ud + 0.05: return PAINT
            bp = (ub + uc) / 2
            if abs(uu - bp) < 0.03 and not sp.get('cargo'): return BLACK                # B pillar
            if sp.get('bed') or sp.get('cargo'): return GLASS if uu > ub - 0.08 else PAINT
            return GLASS
        if seg in (8, 9, 10) and hl_cab:
            if ub < uu < ua - 0.015: return GLASS if seg >= 8 else BLACK                # windscreen
            if ud + 0.01 < uu < uc and not (sp.get('cargo') or sp.get('bed')): return GLASS if seg >= 8 else BLACK   # backlight
            if seg == 8 and (abs(uu - ub) < 0.02 or abs(uu - uc) < 0.02): return BLACK
    return PAINT


def body(sp, lod):
    ns = NS if not lod else 31; X, Wd, ZB, ZS, ZT, RW, CB = stations(sp, ns); U = np.linspace(-1, 1, ns); bm = bmesh.new(); rings = []
    for i in range(ns): rings.append([bm.verts.new((X[i], y, z)) for (y, z) in ring(Wd[i], ZB[i], ZS[i], ZT[i], RW[i], CB[i])])
    n = len(rings[0])
    for i, (a, b) in enumerate(zip(rings[:-1], rings[1:])):
        uu = (U[i] + U[i + 1]) / 2; cw = (CB[i] + CB[i + 1]) / 2
        for j in range(n):
            f = bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j])); seg = j if j <= 10 else n - 1 - j; f.material_index = _zone(sp, uu, seg, cw)
    for rr, mi in ((rings[0], BLACK), (rings[-1], BLACK)):
        f = bm.faces.new(rr); f.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cl = bm.edges.layers.float.get('crease_edge') or bm.edges.layers.float.new('crease_edge')
    for a, b in zip(rings[:-1], rings[1:]):                                               # shoulder, glass base and sill held crisp
        for j, k in ((6, 0.7), (n - 6, 0.7), (7, 0.9), (n - 7, 0.9), (3, 0.5), (n - 3, 0.5), (8, 0.6), (n - 8, 0.6)):
            e = bm.edges.get((a[j], b[j]))
            if e: e[cl] = k
    for e in bm.edges:                                                                   # zone borders a little crisper
        if len(e.link_faces) == 2 and e.link_faces[0].material_index != e.link_faces[1].material_index: e[cl] = max(e[cl], 0.6)
    ob = _obj('_th_body', bm)
    for i in range(12):
        mt = bpy.data.materials.get('_th_%d' % i) or bpy.data.materials.new('_th_%d' % i); ob.data.materials.append(mt)
    sub = ob.modifiers.new('s', 'SUBSURF'); sub.levels = 1 if lod else 2
    cut = []
    for ax in sp['ax']:
        bpy.ops.mesh.primitive_cylinder_add(vertices=32 if not lod else 16, radius=sp['r'] * 1.18, depth=sp['W'] * 2.8, location=(ax, 0, sp['r'] * 1.02), rotation=(math.pi / 2, 0, 0))
        c = bpy.context.active_object; c.name = '_th_cut'; cut.append(c)
        bo = ob.modifiers.new('b', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = c; bo.solver = 'EXACT'
    for c in cut: c.hide_set(True); c.hide_render = True
    out = _eval(ob)
    for c in cut: bpy.data.objects.remove(c, do_unlink=True)
    bpy.data.objects.remove(ob, do_unlink=True)
    return out, (X, Wd, ZB, ZS, ZT, RW, CB)


def classify(bm, sp, st):
    """Zones come from the cage; only the faces lining the wheel-arch cuts are turned dark here."""
    for f in bm.faces:
        c = f.calc_center_median()
        for ax in sp['ax']:
            if math.hypot(c.x - ax, c.z - sp['r'] * 1.02) < sp['r'] * 1.2 and f.material_index == PAINT and abs(f.normal.y) < 0.5: f.material_index = BLACK
    out = []; groups = {}
    for f in bm.faces: groups.setdefault(f.material_index, []).append(f)
    for mi in groups:
        b2 = bm.copy(); bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.material_index != mi], context='FACES'); out.append((b2, mi))
    bm.free(); return out


# ------------------------------------------------------------------ parts
def box(cx, cy, cz, sx, sy, sz, rx=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx; v.co.y *= sy; v.co.z *= sz
        if rx: y_, z_ = v.co.y, v.co.z; v.co.y = y_ * math.cos(rx) - z_ * math.sin(rx); v.co.z = y_ * math.sin(rx) + z_ * math.cos(rx)
        v.co.x += cx; v.co.y += cy; v.co.z += cz
    return bm


def rbox(cx, cy, cz, sx, sy, sz, r=0.3, seg=2):
    """Rounded box (bevelled corners)."""
    bm = box(cx, cy, cz, sx, sy, sz); bmesh.ops.bevel(bm, geom=bm.edges[:], offset=min(sx, sy, sz) * r, segments=seg, affect='EDGES'); return bm


def lathe_y(prof, seg, cx, cy, cz):
    """Profile [(r, y)] revolved about an axis along Y through (cx, cy, cz) (wheels)."""
    bm = bmesh.new(); R = []
    for (r_, y_) in prof: R.append([bm.verts.new((cx + r_ * math.cos(a), cy + y_, cz + r_ * math.sin(a))) for a in np.linspace(0, 2 * np.pi, seg, endpoint=False)])
    for a, b in zip(R[:-1], R[1:]):
        for k in range(seg): bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return bm


def wheel(ax, s, sp, out, lod):
    r = sp['r']; W = sp['W']; yc = s * (W - 0.13); tw = 0.215; seg = 36 if not lod else 16
    tyre = [(r * 0.66, -tw / 2), (r * 0.9, -tw / 2 - 0.006), (r * 0.985, -tw / 2 + 0.02), (r, -tw / 4), (r, tw / 4), (r * 0.985, tw / 2 - 0.02), (r * 0.9, tw / 2 + 0.006), (r * 0.66, tw / 2)]
    out.append((lathe_y([(a, b * s) for a, b in tyre], seg, ax, yc, r), TYRE))
    rim = [(r * 0.66, s * (tw / 2 - 0.01)), (r * 0.64, s * (tw / 2 + 0.002)), (r * 0.6, s * (tw / 2 - 0.02)), (r * 0.6, -s * (tw / 2 - 0.02))]
    out.append((lathe_y(rim, seg, ax, yc, r), RIM))
    out.append((lathe_y([(r * 0.46, s * 0.02), (r * 0.46, s * 0.04), (r * 0.12, s * 0.04)], seg, ax, yc, r), DISC))       # brake disc face
    out.append((lathe_y([(r * 0.14, s * (tw / 2 - 0.035)), (r * 0.16, s * (tw / 2 - 0.02)), (0.001, s * (tw / 2 - 0.012))], 12, ax, yc, r), RIM))   # hub
    for k in range(5 if not lod else 5):                                                  # spokes
        a = k * 2 * np.pi / 5 + 0.3; ca, sa = math.cos(a), math.sin(a); bm = bmesh.new(); pts = []
        for (rr, ww, yy) in ((r * 0.14, 0.05, tw / 2 - 0.03), (r * 0.6, 0.075, tw / 2 - 0.045)):
            for sw in (-1, 1):
                for dy in (0.0, -0.035):
                    t = np.array([-sa, ca]); p = np.array([ca, sa]) * rr + t * sw * ww / 2
                    pts.append((ax + p[0], yc + s * (yy + dy), r + p[1]))
        V = [bm.verts.new(p) for p in pts]
        for f in ((0, 2, 6, 4), (1, 5, 7, 3), (0, 4, 5, 1), (2, 3, 7, 6), (0, 1, 3, 2), (4, 6, 7, 5)):
            try: bm.faces.new([V[i] for i in f])
            except ValueError: pass
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); out.append((bm, RIM))
    if not lod:
        for k in range(5): a = k * 2 * np.pi / 5 + 0.3 + np.pi / 5; out.append((box(ax + math.cos(a) * r * 0.1, yc + s * (tw / 2 - 0.014), r + math.sin(a) * r * 0.1, 0.018, 0.012, 0.018), CHROME))
        out.append((box(ax + r * 0.42 * (1 if ax > 0 else -1) * 0.0 + 0.0, s * (W - 0.2), r + r * 0.35, r * 0.4, 0.06, r * 0.25), DISC))   # caliper


def details(sp, st, out, lod):
    X, Wd, ZB, ZS, ZT, RW, CB = st; hl = sp['L'] / 2; ua, ub, uc, ud, zr, wr = sp['cab']
    zat = lambda x, A: float(np.interp(x, X, A))
    nose_x = hl; tail_x = -hl
    zl = zat(hl - 0.2, ZT) - 0.1; wn = zat(hl - 0.2, Wd)
    zl = zat(hl - 0.2, ZS) - 0.2; wn = zat(hl - 0.2, Wd)
    for s in (-1, 1):
        # mirror on a stalk at the A pillar root
        mx = ua * hl - 0.12; zm = zat(mx, ZS) + 0.13; wm = zat(mx, Wd)
        out.append((rbox(mx, s * (wm + 0.09), zm, 0.09, 0.16, 0.11, 0.35), PAINT)); out.append((box(mx - 0.045, s * (wm + 0.1), zm, 0.01, 0.13, 0.08), GLASS))
        out.append((box(mx + 0.02, s * (wm + 0.02), zm - 0.03, 0.06, 0.06, 0.03), BLACK))
        # door handles and shut lines
        doors = [ua * hl - 0.25, (ub + uc) / 2 * hl + 0.05] if not sp.get('cargo') else [ua * hl - 0.25]
        if sp.get('hatch2') or sp is TYPES.get('hatch'): doors = doors[:1]
        for dx in doors:
            zs_ = zat(dx, ZS); wd_ = zat(dx, Wd)
            out.append((box(dx - 0.18, s * (wd_ * 0.995 + 0.004), zs_ - 0.1, 0.13, 0.016, 0.025), CHROME if not sp.get('clad') else BLACK))
        for gx in [ua * hl + 0.02, (ub + uc) / 2 * hl + 0.06, (uc + ud) / 2 * hl] + ([sp['ax'][1] + sp['r'] * 1.25] if not sp.get('cargo') else [ub * hl - 1.4]):
            zs_ = zat(gx, ZS); wd_ = zat(gx, Wd); zbx = zat(gx, ZB)
            out.append((box(gx, s * (wd_ * 0.995 + 0.002), (zs_ + zbx + 0.08) / 2, 0.006, 0.006, zs_ - zbx - 0.08), BLACK))
        # sill line, lower bumper intakes
        out.append((box(0.0, s * (zat(0, Wd) + 0.004), zat(0, ZB) + 0.06, (sp['ax'][0] - sp['ax'][1]) - sp['r'] * 2.6, 0.012, 0.03), BLACK))
    for k in range(5 if not lod else 0): out.append((box(hl - 0.03, 0, zl + 0.05 + k * 0.035, 0.03, wn * 0.62, 0.012), CHROME))           # grille bars over the dark centre
    out.append((box(hl - 0.02, 0, zat(hl, ZB) + 0.2, 0.02, 0.26, 0.06), PLATE))
    out.append((box(-hl + 0.025, 0, zat(-hl, ZS) - 0.24, 0.02, 0.26, 0.06), PLATE))
    for s in (-1, 1): out.append((lathe_y([(0.03, 0.0), (0.03, -0.0001)], 10, 0, 0, 0) if False else box(-hl - 0.01, s * 0.45, zat(-hl, ZB) + 0.1, 0.04, 0.07, 0.05), CHROME))   # exhaust
    # wipers
    xw = ua * hl - 0.04; zw = zat(xw, ZS) + 0.06
    for s in (-0.35, 0.25): out.append((box(xw - 0.04, s, zw, 0.02, 0.6, 0.015, rx=0.0), BLACK))
    roof = float(ZT.max())
    if sp.get('rails'):
        for s in (-1, 1): out.append((rbox((ub + uc) / 2 * hl, s * zat((ub + uc) / 2 * hl, RW) * 0.88, roof + 0.05, (ub - uc) * hl * 0.95, 0.04, 0.04, 0.4), CHROME))
    if sp.get('taxi'): out.append((rbox((ub + uc) / 2 * hl, 0, roof + 0.1, 0.22, 0.42, 0.11, 0.3), AMBER))
    if sp.get('bed'):                                                                     # load bed walls and floor behind the cab
        x0, x1 = -hl + 0.06, ud * hl - 0.05; zb_ = zat(x0, ZS) + 0.02; wb = zat(-0.5, Wd)
        out.append((box((x0 + x1) / 2, 0, zb_ - 0.25, x1 - x0, wb * 1.8, 0.04), BLACK))
        for s in (-1, 1): out.append((box((x0 + x1) / 2, s * (wb - 0.03), zb_ + 0.0, x1 - x0, 0.05, 0.06), PAINT))
    if sp.get('cargo'):                                                                   # rear doors split, side sliding door rail
        out.append((box(-hl - 0.004, 0, 1.1, 0.006, 0.008, 1.6), BLACK))
        for s in (-1, 1): out.append((box(-0.4, s * (zat(-0.4, Wd) + 0.004), 1.35, 1.8, 0.01, 0.02), BLACK))


def build(kind, lod=0):
    """Returns [(bmesh, zone)] for one car."""
    sp = TYPES[kind]
    for ob in [o for o in bpy.data.objects if o.name.startswith('_th_')]: bpy.data.objects.remove(ob, do_unlink=True)
    bm, st = body(sp, lod); out = classify(bm, sp, st)
    for s in (-1, 1):
        for ax in sp['ax']: wheel(ax, s, sp, out, lod)
    details(sp, st, out, lod)
    for ax in sp['ax']:                                                                   # arch liners (dark, inside the cut)
        for s in (-1, 1):
            a0 = lathe_y([(sp['r'] * 1.17, -0.32 * s), (sp['r'] * 1.17, 0.0)], 24 if not lod else 12, ax, s * (sp['W'] - 0.3), sp['r'] * 1.02)
            bmesh.ops.delete(a0, geom=[v for v in a0.verts if v.co.z < sp['r'] * 0.9], context='VERTS'); out.append((a0, BLACK))
    return out

"""Traffic cars for Aurelia Island, modelled in Blender from subdivision cages.

Each car is a lower-body cage (stations along the length, a 14-point section ring) and a cabin cage (windscreen, roof,
backlight) smoothed with a Subdivision Surface modifier, with the wheel arches cut by booleans. Window glass, pillars,
bumpers, sills and arch liners are separate material zones; lights, grille, mirrors, plates and wheels are separate
parts. The body is painted white so the game's instance colour gives every car its own paint.
Axes: +X forward, +Y left, Z up; origin on the ground between the axles.
"""
import math
import numpy as np
import bpy
import bmesh

PAINT, GLASS, BLACK, CHROME, LAMP_F, LAMP_R, TYRE, RIM, PLATE, AMBER = range(10)
COLOURS = {PAINT: (0.999, 0.999, 0.999), GLASS: (0.03, 0.045, 0.06), BLACK: (0.035, 0.035, 0.038), CHROME: (0.72, 0.73, 0.75),
           LAMP_F: (0.92, 0.93, 0.9), LAMP_R: (0.6, 0.04, 0.03), TYRE: (0.025, 0.025, 0.027), RIM: (0.62, 0.63, 0.65), PLATE: (0.93, 0.93, 0.88),
           AMBER: (0.95, 0.5, 0.08)}

# Per type: length, half width, wheel radius, axle x (front, rear), lower-body stations
# (x fraction of half length, half-width fraction, bottom z, shoulder z, deck z) and cabin stations (x, base half-width, top half-width, roof z).
TYPES = {
    'hatch': dict(L=4.05, W=0.87, r=0.31, ax=(1.27, -1.25),
                  st=[(-1.0, 0.80, 0.42, 0.78, 0.86), (-0.97, 0.94, 0.30, 0.90, 0.95), (-0.80, 1.0, 0.24, 0.92, 0.98), (-0.35, 1.0, 0.22, 0.90, 0.95),
                      (0.25, 1.0, 0.22, 0.88, 0.92), (0.62, 0.99, 0.23, 0.84, 0.86), (0.88, 0.95, 0.26, 0.76, 0.76), (1.0, 0.82, 0.34, 0.66, 0.68)],
                  cab=[(-0.93, 0.86, 0.74, 0.0), (-0.86, 0.84, 0.70, 1.44), (0.05, 0.85, 0.71, 1.50), (0.42, 0.86, 0.76, 0.0)], b=-0.38),
    'sedan': dict(L=4.78, W=0.90, r=0.32, ax=(1.45, -1.42),
                  st=[(-1.0, 0.82, 0.40, 0.84, 0.90), (-0.96, 0.95, 0.28, 0.95, 0.99), (-0.75, 1.0, 0.24, 0.96, 1.0), (-0.3, 1.0, 0.22, 0.93, 0.96),
                      (0.2, 1.0, 0.22, 0.90, 0.93), (0.55, 0.99, 0.23, 0.85, 0.86), (0.85, 0.95, 0.26, 0.76, 0.76), (1.0, 0.83, 0.34, 0.66, 0.68)],
                  cab=[(-0.66, 0.86, 0.72, 0.0), (-0.42, 0.85, 0.70, 1.42), (0.1, 0.86, 0.71, 1.46), (0.38, 0.87, 0.76, 0.0)], b=-0.15),
    'suv':   dict(L=4.62, W=0.95, r=0.37, ax=(1.42, -1.40),
                  st=[(-1.0, 0.86, 0.55, 0.98, 1.06), (-0.97, 0.96, 0.42, 1.08, 1.12), (-0.80, 1.0, 0.36, 1.10, 1.14), (-0.3, 1.0, 0.34, 1.08, 1.12),
                      (0.25, 1.0, 0.34, 1.06, 1.10), (0.62, 0.99, 0.35, 1.02, 1.05), (0.88, 0.96, 0.38, 0.97, 0.98), (1.0, 0.86, 0.45, 0.86, 0.88)],
                  cab=[(-0.95, 0.90, 0.82, 0.0), (-0.92, 0.90, 0.80, 1.78), (0.12, 0.90, 0.80, 1.82), (0.45, 0.91, 0.84, 0.0)], b=-0.4),
    'van':   dict(L=5.05, W=0.99, r=0.35, ax=(1.62, -1.55),
                  st=[(-1.0, 0.93, 0.45, 1.05, 1.08), (-0.98, 0.99, 0.36, 1.08, 1.1), (-0.80, 1.0, 0.33, 1.08, 1.1), (-0.3, 1.0, 0.32, 1.07, 1.09),
                      (0.3, 1.0, 0.32, 1.05, 1.07), (0.66, 0.99, 0.33, 1.0, 1.0), (0.88, 0.96, 0.36, 0.92, 0.92), (1.0, 0.86, 0.42, 0.8, 0.82)],
                  cab=[(-0.99, 0.96, 0.90, 0.0), (-0.98, 0.96, 0.90, 2.12), (0.38, 0.96, 0.90, 2.16), (0.62, 0.96, 0.90, 0.0)], b=0.42, cargo=True),
}
TYPES['taxi'] = dict(TYPES['sedan'], taxi=True)


def _ring_lower(w, zb, zs, zt):
    """Half section from bottom centre round the side to deck centre, then mirrored: closed loop of 14 points (y, z)."""
    h = [(0.0, zb), (w * 0.82, zb), (w * 0.98, zb + 0.10), (w, zb + (zs - zb) * 0.45), (w * 0.985, zs - 0.06), (w * 0.93, zs + 0.01), (w * 0.62, zt - 0.005), (0.0, zt)]
    return h + [(-y, z) for (y, z) in reversed(h[1:-1])]


def _cage(sp, lod):
    L, W = sp['L'], sp['W']; hl = L / 2
    bm = bmesh.new(); rings = []
    for (u, wf, zb, zs, zt) in sp['st']:
        pts = _ring_lower(W * wf, zb, zs, zt)
        rings.append([bm.verts.new((u * hl, y, z)) for (y, z) in pts])
    n = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for j in range(n):
            f = bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j])); f.material_index = PAINT
    cl = bm.edges.layers.float.get('crease_edge') or bm.edges.layers.float.new('crease_edge')
    for a, b in zip(rings[:-1], rings[1:]):                                        # shoulder line and sill held crisp
        for j, k in ((5, 0.75), (n - 5, 0.75), (2, 0.5), (n - 2, 0.5)):
            e = bm.edges.get((a[j], b[j]))
            if e: e[cl] = k
    for r, rev in ((rings[0], True), (rings[-1], False)):
        f = bm.faces.new(list(reversed(r)) if rev else r); f.material_index = PAINT
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # cabin: windscreen strip, side windows split by a B pillar, backlight strip
    cab = sp['cab']; xs = [c[0] * hl for c in cab]
    zsh = lambda x: float(np.interp(x / hl, [s[0] for s in sp['st']], [s[3] for s in sp['st']])) + 0.01
    bx = sp.get('b', 0.0) * hl
    stations = [(xs[0], cab[0]), (xs[1], cab[1]), (bx - 0.06, None), (bx + 0.06, None), (xs[2], cab[2]), (xs[3], cab[3])]
    if sp.get('cargo'): stations = [(xs[0], cab[0]), (xs[1], cab[1]), (xs[2] - 1.0, None), (xs[2] - 0.88, None), (xs[2], cab[2]), (xs[3], cab[3])]
    def cabring(x, c):
        if c is None:
            k = (x - xs[1]) / (xs[2] - xs[1]); c = (x, cab[1][1] + (cab[2][1] - cab[1][1]) * k, cab[1][2] + (cab[2][2] - cab[1][2]) * k, cab[1][3] + (cab[2][3] - cab[1][3]) * k)
        _, wb, wt, zr = c; z0 = zsh(x); W0 = W * wb; Wt = W * wt
        if zr == 0.0: zr = z0 + 0.005; Wt = W0 * 0.97
        h = [(W0, z0), (Wt, zr - 0.07), (Wt * 0.86, zr - 0.005), (0.0, zr + 0.015)]
        return h + [(-y, z) for (y, z) in reversed(h[:-1])]
    cr = [[bm.verts.new((x, y, z)) for (y, z) in cabring(x, c)] for (x, c) in stations]
    m = len(cr[0]); cl = bm.edges.layers.float.get('crease_edge')
    for a, b in zip(cr[:-1], cr[1:]):
        for j, k in ((1, 0.6), (m - 2, 0.6), (0, 0.9), (m - 1, 0.9)):
            e = bm.edges.get((a[j], b[j]))
            if e: e[cl] = k
    for s, (a, b) in enumerate(zip(cr[:-1], cr[1:])):
        for j in range(m - 1):
            f = bm.faces.new((a[j], b[j], b[j + 1], a[j + 1]))
            side = j in (0, m - 2); roof = not side
            if s == 0: f.material_index = BLACK if side else GLASS                       # windscreen with A pillars
            elif s == len(cr) - 2: f.material_index = BLACK if side else GLASS           # backlight with C pillars
            elif s == 2: f.material_index = PAINT if roof or sp.get('cargo') else BLACK  # B pillar
            else: f.material_index = PAINT if roof else (PAINT if sp.get('cargo') and s == 1 else GLASS)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def _obj(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob


def _eval(ob):
    dg = bpy.context.evaluated_depsgraph_get(); e = ob.evaluated_get(dg); me = bpy.data.meshes.new_from_object(e)
    bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me); return bm


def _parts_box(x, y, z, sx, sy, sz, mat, out, seg=1):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co.x = x + v.co.x * sx; v.co.y = y + v.co.y * sy; v.co.z = z + v.co.z * sz
    if seg: bmesh.ops.bevel(bm, geom=bm.edges[:], offset=min(sx, sy, sz) * 0.22, segments=seg, affect='EDGES')
    out.append((bm, mat))


def _wheel(x, s, sp, out, lod):
    r = sp['r']; y = s * (sp['W'] * 0.86); n = 12 if lod else 20
    # tyre: rounded profile revolved about the axle
    prof = [(r * 0.66, -0.11), (r * 0.9, -0.115), (r * 0.98, -0.095), (r, -0.04), (r, 0.04), (r * 0.98, 0.095), (r * 0.9, 0.115), (r * 0.66, 0.11)]
    bm = bmesh.new(); rings = []
    for k in range(n):
        a = 2 * math.pi * k / n; ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((x + rr * ca, y + w * s, r + rr * sa)) for (rr, w) in prof])
    for k in range(n):
        A, B = rings[k], rings[(k + 1) % n]
        for j in range(len(prof) - 1): bm.faces.new((A[j], B[j], B[j + 1], A[j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); out.append((bm, TYRE))
    # rim: dished face with five spokes
    bm = bmesh.new(); ro = r * 0.66; face = y + s * 0.1
    c0 = bm.verts.new((x, face, r)); ring = [bm.verts.new((x + ro * math.cos(2 * math.pi * k / n), face - s * 0.012, r + ro * math.sin(2 * math.pi * k / n))) for k in range(n)]
    for k in range(n): bm.faces.new((c0, ring[k], ring[(k + 1) % n]) if s > 0 else (c0, ring[(k + 1) % n], ring[k]))
    out.append((bm, BLACK))
    for k in range(5 if lod else 5):
        a = 2 * math.pi * k / 5 + 0.3; ca, sa = math.cos(a), math.sin(a)
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            lx, ly, lz = v.co.x * ro * 0.9 + ro * 0.45, v.co.y * 0.025, v.co.z * 0.075
            v.co = (x + lx * ca - lz * sa, face + s * 0.004 + ly, r + lx * sa + lz * ca)
        out.append((bm, RIM))
    bm = bmesh.new(); ring2 = [bm.verts.new((x + ro * math.cos(2 * math.pi * k / n), face + s * 0.006, r + ro * math.sin(2 * math.pi * k / n))) for k in range(n)]
    ring3 = [bm.verts.new((x + ro * 0.86 * math.cos(2 * math.pi * k / n), face + s * 0.006, r + ro * 0.86 * math.sin(2 * math.pi * k / n))) for k in range(n)]
    for k in range(n):
        q = (ring2[k], ring2[(k + 1) % n], ring3[(k + 1) % n], ring3[k]); bm.faces.new(q if s > 0 else tuple(reversed(q)))
    out.append((bm, RIM))
    if not lod:
        bm = bmesh.new(); hub = [bm.verts.new((x + 0.06 * math.cos(2 * math.pi * k / 8), face + s * 0.01, r + 0.06 * math.sin(2 * math.pi * k / 8))) for k in range(8)]
        f = bm.faces.new(hub if s > 0 else list(reversed(hub))); out.append((bm, CHROME))


def build(kind, lod=0):
    """Returns a list of (bmesh, colour index) for one traffic car."""
    sp = TYPES[kind]; L, W, r = sp['L'], sp['W'], sp['r']; hl = L / 2
    for ob in [o for o in bpy.data.objects if o.name.startswith('_tc_')]: bpy.data.objects.remove(ob, do_unlink=True)
    ob = _obj('_tc_body', _cage(sp, lod))
    for i in range(10):
        mt = bpy.data.materials.get('_tc_%d' % i) or bpy.data.materials.new('_tc_%d' % i); ob.data.materials.append(mt)
    sub = ob.modifiers.new('s', 'SUBSURF'); sub.levels = 1 if lod else 2; sub.render_levels = sub.levels
    cutters = []
    for ax in sp['ax']:
        bpy.ops.mesh.primitive_cylinder_add(vertices=24 if not lod else 14, radius=r * 1.17, depth=W * 2.6, location=(ax, 0, r * 1.02), rotation=(math.pi / 2, 0, 0))
        c = bpy.context.active_object; c.name = '_tc_cut'; c.hide_render = True; cutters.append(c)
        bo = ob.modifiers.new('b', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = c; bo.solver = 'EXACT'
    for c in cutters: c.hide_set(True)
    bm = _eval(ob)
    for c in cutters: bpy.data.objects.remove(c, do_unlink=True)
    bpy.data.objects.remove(ob, do_unlink=True)
    # zones cut with clean planes: sills, front and rear bumper valances, arch liners
    zmin = min(s[2] for s in sp['st']); zbump = zmin + sp.get('bump', 0.27); xf = sp['ax'][0] + r * 1.17; xr = sp['ax'][1] - r * 1.17
    seams = [sp['cab'][-1][0] * hl - 0.05, sp.get('b', 0.0) * hl] + ([] if sp.get('cargo') else [xr + r * 0.25])     # door shut lines
    if sp.get('cargo'): seams = [sp['cab'][-1][0] * hl - 0.05, sp['cab'][2][0] * hl - 0.95]
    cuts = [((0, 0, zmin + 0.07), (0, 0, 1)), ((0, 0, zbump), (0, 0, 1)), ((xf, 0, 0), (1, 0, 0)), ((xr, 0, 0), (1, 0, 0))]
    for sx in seams: cuts += [((sx - 0.009, 0, 0), (1, 0, 0)), ((sx + 0.009, 0, 0), (1, 0, 0))]
    for co, no in cuts:
        g = bm.verts[:] + bm.edges[:] + bm.faces[:]; bmesh.ops.bisect_plane(bm, geom=g, plane_co=co, plane_no=no)
    for f in bm.faces:
        if f.material_index != PAINT: continue
        c = f.calc_center_median()
        if c.z < zmin + 0.07: f.material_index = BLACK
        elif c.z < zbump and (c.x > xf or c.x < xr): f.material_index = BLACK
        elif any(abs(c.x - sx) < 0.009 for sx in seams) and abs(f.normal.y) > 0.45 and c.z < float(np.interp(c.x / hl, [s[0] for s in sp['st']], [s[3] for s in sp['st']])) + 0.02: f.material_index = BLACK
        else:
            for ax in sp['ax']:
                if math.hypot(c.x - ax, c.z - r * 1.02) < r * 1.19 and abs(c.y) < W * 0.96: f.material_index = BLACK
    out = []
    groups = {}
    for f in bm.faces: groups.setdefault(f.material_index, []).append(f)
    for mi, fs in groups.items():
        b2 = bm.copy()
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.material_index != mi], context='FACES')
        out.append((b2, mi))
    bm.free()
    # lights, grille, plates, mirrors
    fz = lambda i: sp['st'][i]
    nose, tail = sp['st'][-1], sp['st'][0]
    zl = (nose[2] + nose[3]) / 2 + 0.06; zt_ = (tail[2] + tail[3]) / 2 + 0.1
    for s in (-1, 1):
        wn = W * nose[1]; wt_ = W * tail[1]
        _parts_box(hl - 0.1, s * wn * 0.6, zl + 0.03, 0.2, wn * 0.36, 0.11, LAMP_F, out, 0 if lod else 1)
        _parts_box(hl - 0.12, s * wn * 0.83, zl - 0.06, 0.2, wn * 0.1, 0.04, AMBER, out, 0)
        _parts_box(-hl + 0.1, s * wt_ * 0.66, zt_ + 0.02, 0.2, wt_ * 0.36, 0.13, LAMP_R, out, 0 if lod else 1)
        cf = sp['cab'][-1][0] * hl - 0.14; zsh = float(np.interp(cf / hl, [q[0] for q in sp['st']], [q[3] for q in sp['st']]))
        wsh = W * float(np.interp(cf / hl, [q[0] for q in sp['st']], [q[1] for q in sp['st']])) * 0.93
        _parts_box(cf, s * (wsh + 0.05), zsh + 0.12, 0.08, 0.12, 0.1, PAINT, out, 0 if lod else 1)
        _parts_box(cf - 0.045, s * (wsh + 0.07), zsh + 0.12, 0.012, 0.08, 0.07, GLASS, out, 0)
        wc = W * sp['cab'][-1][1]
        _parts_box(cf + 0.01, s * (wc + wsh + 0.0) / 2, zsh + 0.09, 0.05, (wsh - wc) + 0.04, 0.03, BLACK, out, 0)   # mirror arm from the door
        if not lod:
            for ax in sp['ax']: _wheel(ax, s, sp, out, lod)
        else:
            for ax in sp['ax']: _wheel(ax, s, sp, out, 1)
    if not lod:                                                                                   # door handles at the rear edge of each door
        sx_ = [sp.get('b', 0.0) * hl] + ([] if sp.get('cargo') else [sp['ax'][1] - r * 1.17 + r * 0.25])
        for hx in sx_:
            u_ = (hx - 0.16) / hl; zs_ = float(np.interp(u_, [q[0] for q in sp['st']], [q[3] for q in sp['st']])); wf_ = float(np.interp(u_, [q[0] for q in sp['st']], [q[1] for q in sp['st']]))
            for s in (-1, 1): _parts_box(hx - 0.16, s * (W * wf_ * 0.99 + 0.006), zs_ - 0.12, 0.14, 0.025, 0.025, CHROME, out, 0)
    _parts_box(hl - 0.03, 0, zl - 0.06, 0.06, W * 0.62, 0.12, BLACK, out, 0)                    # grille
    if not lod:
        for k in range(3): _parts_box(hl - 0.005, 0, zl - 0.1 + k * 0.045, 0.012, W * 0.58, 0.01, CHROME, out, 0)
    _parts_box(hl + 0.0, 0, nose[2] + 0.17, 0.02, 0.26, 0.06, PLATE, out, 0)
    _parts_box(-hl - 0.0, 0, zt_ - 0.18, 0.02, 0.26, 0.06, PLATE, out, 0)
    if sp.get('taxi'):
        roof = max(c[3] for c in sp['cab'])
        _parts_box(sp['b'] * hl + 0.25, 0, roof + 0.1, 0.22, 0.28, 0.09, AMBER, out, 0 if lod else 1)
    return out


def preview(path, kinds=('hatch', 'sedan', 'suv', 'van', 'taxi')):
    """Studio render of all types side by side (for checking)."""
    import isle_lib as L
    for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
    mats = {}
    for i, c in COLOURS.items():
        m = bpy.data.materials.new('pv_%d' % i); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (*c, 1)
        b.inputs['Roughness'].default_value = 0.08 if i in (GLASS, PAINT, CHROME) else 0.5; b.inputs['Metallic'].default_value = 0.9 if i == CHROME else 0.0
        if i in (LAMP_F, LAMP_R, AMBER): b.inputs['Emission Color'].default_value = (*c, 1); b.inputs['Emission Strength'].default_value = 0.4
        mats[i] = m
    paints = [(0.75, 0.08, 0.06), (0.1, 0.22, 0.5), (0.85, 0.85, 0.82), (0.18, 0.2, 0.22), (0.95, 0.75, 0.1)]
    tris = {}
    for k, kind in enumerate(kinds):
        for lod in (0, 1):
            parts = build(kind, lod); n = 0
            for bm, mi in parts:
                bmesh.ops.triangulate(bm, faces=bm.faces[:]); n += len(bm.faces)
                me = bpy.data.meshes.new('pv'); bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new('pv_%s_%d' % (kind, lod), me); bpy.context.scene.collection.objects.link(ob)
                ob.location = (lod * 6.5, k * 3.0, 0)
                if mi == PAINT:
                    m = mats[PAINT].copy(); m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*paints[k], 1); ob.data.materials.append(m)
                else: ob.data.materials.append(mats[mi])
                for p in me.polygons: p.use_smooth = mi in (PAINT, GLASS, TYRE)
            tris[(kind, lod)] = n
    return tris

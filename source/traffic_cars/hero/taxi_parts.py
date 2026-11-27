"""Vela TAXI (traffic 05) for the Godot game: vela_parts.py on the hero pipeline (separate wheel nodes, tread tyres) plus roof sign,
checker band and door lettering as decals. Original docstring: Traffic car (CAR env, default mira): parts, gap lines, materials, interior, wheels, LODs; exports the game GLB and a .blend.
Blender frame: +X forward, +Y left, Z up, origin on the ground between the axles. Sheet s -> x = C0 - s."""
import sys, os, math, numpy as np, bpy, bmesh
sys.path.insert(0, '/home/claude/traffic'); import importlib; CAR = os.environ.get('CAR', 'mira'); M = importlib.import_module(CAR + '_sdf'); Zn = importlib.import_module(CAR + '_zones'); NM = CAR.capitalize()
from scipy import ndimage
from mathutils import Vector, Matrix
OUT = os.environ.get('OUT', '/tmp/' + os.environ.get('CAR', 'mira'))
bpy.ops.wm.open_mainfile(filepath='/tmp/%s_body.blend' % CAR); C0 = getattr(M, 'C0', M.L / 2)
D, s_, y_, z_ = M.field(); o3 = np.array([s_[0], y_[0], z_[0]]); Ds = ndimage.gaussian_filter(D, 1.3); G = np.gradient(Ds, M.H)
def dval(P): return ndimage.map_coordinates(D, ((np.atleast_2d(P) - o3) / M.H).T, order=1, mode='nearest')
def nrm(P):
    idx = ((np.atleast_2d(P) - o3) / M.H).T; N = np.stack([ndimage.map_coordinates(g, idx, order=1, mode='nearest') for g in G], 1); return N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-9)
def B(p): return Vector((C0 - p[0], p[1], p[2]))           # sheet point -> Blender
def Bn(n): return Vector((-n[0], n[1], n[2]))

# ---------------- materials
def mat(name, col, rough=0.5, metal=0.0, emit=None, alpha=1.0, coat=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if coat: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.04
    if emit: b.inputs['Emission Color'].default_value = (*emit[0], 1); b.inputs['Emission Strength'].default_value = emit[1]
    if alpha < 1: b.inputs['Alpha'].default_value = alpha; m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None; m.surface_render_method = 'BLENDED'
    m.use_backface_culling = name not in ('Interior', 'Headliner', 'GapLine'); m.diffuse_color = (*col, 1); return m
MATS = dict(Paint=((0.80, 0.52, 0.035), 0.26, 0.3, None, 1, 1.0), Clad=((0.045, 0.045, 0.05), 0.72), Liner=((0.018, 0.018, 0.02), 0.9), GapLine=((0.004, 0.004, 0.005), 1.0),
            Glass=((0.012, 0.018, 0.024), 0.03, 0.0, None, 0.74), GlassBlack=((0.008, 0.008, 0.01), 0.08), Lamp=((0.05, 0.055, 0.06), 0.10, 1.0), LampLens=((0.85, 0.88, 0.92), 0.05, 0.0, None, 0.25), PlateText=((1, 1, 1), 0.5), Leather=((0.10, 0.085, 0.075), 0.6), LED=((1, 1, 1), 0.2, 0, ((1, 0.98, 0.94), 4.0)),
            Tail=((0.42, 0.012, 0.018), 0.14), TailBand=((0.01, 0.01, 0.012), 0.08), TailLED=((0.9, 0.08, 0.06), 0.2, 0, ((1, 0.06, 0.03), 2.5)), Reverse=((0.92, 0.92, 0.92), 0.15),
            Grille=((0.014, 0.014, 0.016), 0.55), Intake=((0.014, 0.014, 0.016), 0.6), Reflector=((0.5, 0.02, 0.02), 0.2), Tyre=((0.028, 0.028, 0.03), 0.86), Rim=((0.58, 0.59, 0.61), 0.3, 1.0),
            Disc=((0.13, 0.13, 0.135), 0.5, 0.8), Caliper=((0.10, 0.30, 0.66), 0.38) if CAR == 'mira' else ((0.42, 0.43, 0.45), 0.35, 0.6), Graphite=((0.10, 0.105, 0.115), 0.35, 0.8), Chrome=((0.92, 0.92, 0.93), 0.07, 1.0), Plate=((0.93, 0.93, 0.89), 0.5),
            Interior=((0.03, 0.03, 0.033), 0.75), Headliner=((0.42, 0.41, 0.39), 0.9), MirrorGlass=((0.55, 0.6, 0.65), 0.02, 1.0), Amber=((0.95, 0.45, 0.05), 0.2), SignBody=((0.95, 0.86, 0.55), 0.4, 0.0, ((1.0, 0.9, 0.6), 0.6)))
for k, v in MATS.items():
    col, rough = v[0], v[1]; metal = v[2] if len(v) > 2 else 0; emit = v[3] if len(v) > 3 else None; alpha = v[4] if len(v) > 4 else 1; coat = v[5] if len(v) > 5 else 0
    mat(k, col, rough, metal, emit, alpha, coat)
mat('TyreFar', *MATS['Tyre'][:2])
import tyre_detail as TD; TD.setup_material(bpy.data.materials['Tyre'])
import decal as DC, livery_tex as LT; LT.taxi(); DECALS = []
body = bpy.data.objects['Body']
for i, m in enumerate(body.data.materials):                      # the body's zone slots use the same named materials
    if m.name in MATS: continue
    nm = {'Seal': 'GlassBlack', 'DRL': 'LED', 'Pipe': 'Intake'}.get(m.name, m.name)
    body.data.materials[i] = bpy.data.materials.get(nm) or mat(nm, (0.5, 0.5, 0.5))

PARTS = []
def obj(name, bm, mname=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    if mname: me.materials.append(bpy.data.materials[mname])
    PARTS.append(o); return o
def add_mat(o, name):
    o.data.materials.append(bpy.data.materials[name]); return len(o.data.materials) - 1

# ---------------- gap lines: dark ribbons laid on the surface along each shut line
def surf_point(proj, a, b, side):
    """Find the body surface along the projection axis for sheet-view coordinates (a, b)."""
    if proj == 'sz': t = np.linspace(1.0, 0.0, 600); P = np.c_[np.full_like(t, a), side * t, np.full_like(t, b)]
    elif proj == 'sy': t = np.linspace(1.62, 0.3, 700); P = np.c_[np.full_like(t, a), np.full_like(t, side * b), t]
    else: t = np.linspace(-0.08, 1.2, 700) if side > 0 else np.linspace(M.L + 0.08, M.L - 1.1, 700); P = np.c_[t, np.full_like(t, a), np.full_like(t, b)]
    d = dval(P); k = np.argmax(d < 0)
    if k == 0: return None
    f = d[k - 1] / (d[k - 1] - d[k]); return P[k - 1] + (P[k] - P[k - 1]) * f
def ribbon(bm, pts3, w=0.0019, lift=0.0025):
    pts3 = [p for p in pts3 if p is not None]
    if len(pts3) < 2: return
    P = np.array(pts3); N = nrm(P); vs = []
    for i in range(len(P)):
        t = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]; t /= np.linalg.norm(t) + 1e-9; bdir = np.cross(N[i], t); bdir /= np.linalg.norm(bdir) + 1e-9
        c = P[i] + N[i] * lift; vs.append((bm.verts.new(B(c + bdir * w)), bm.verts.new(B(c - bdir * w))))
    for i in range(len(vs) - 1):
        a, b_ = vs[i], vs[i + 1]; f = bm.faces.new((a[0], b_[0], b_[1], a[1]))
        fn = np.cross(np.array(B(P[i + 1]) - B(P[i])), np.array(vs[i][1].co - vs[i][0].co));
def dense(pl, step=0.012):
    pl = np.asarray(pl, float); out = [pl[0]]
    for a, b in zip(pl[:-1], pl[1:]):
        n = max(1, int(np.linalg.norm(b - a) / step))
        for k in range(1, n + 1): out.append(a + (b - a) * k / n)
    return np.array(out)
Zn.zone_fns(); bmg = bmesh.new()
for gp in Zn.GAPS:
    proj, pl, mk = gp[:3]
    sides = (1, -1) if proj in ('sz', 'sy') else (((gp[3] or 1),) if len(gp) > 3 else ((1,) if pl[0][1] < 0.8 else (-1,)))
    for sd in sides:
        pts = [surf_point(proj, a, b, sd) for a, b in dense(pl)]
        ribbon(bmg, pts)
# fuel flap outline (left side)
f0, f1, f2, f3 = getattr(Zn, 'FUEL', (3.72, 3.85, 0.87, 0.97)); fl = [(f0, f2), (f1, f2), (f1, f3), (f0, f3), (f0, f2)]
ribbon(bmg, [surf_point('sz', a, b, 1) for a, b in dense(fl, 0.008)], 0.0018)
bmesh.ops.recalc_face_normals(bmg, faces=bmg.faces[:])
og = obj('GapLines', bmg, 'GapLine')
for f in og.data.polygons:                                       # face the ribbons outward
    pass
me = og.data
Pv = np.array([[C0 - v.co.x, v.co.y, v.co.z] for v in me.vertices]); Nv = nrm(Pv)
flip = []
bm = bmesh.new(); bm.from_mesh(me)
for f in bm.faces:
    c = f.calc_center_median(); n = nrm(np.array([[C0 - c.x, c.y, c.z]]))[0]
    if f.normal.dot(Bn(n)) < 0: f.normal_flip()
bm.to_mesh(me); bm.free()

# ---------------- wheels
FX, RX, TRK, R = C0 - M.FS, C0 - M.RS, 0.79, M.R
K = R / 0.318                                                                  # Mira profile scaled to the 17" wheel
def lathe(bm, prof, seg, ax_y, center, flipw=1):
    rings = []
    for k in range(seg):
        a = 2 * math.pi * k / seg; ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((center[0] + r * ca, center[1] + w * flipw, center[2] + r * sa)) for r, w in prof])
    for k in range(seg):
        A, Bb = rings[k], rings[(k + 1) % seg]
        for i in range(len(prof) - 1): bm.faces.new((A[i], A[i + 1], Bb[i + 1], Bb[i]))
    return rings
def wheel(name, x, side):
    c = (x, side * TRK, R); bm = bmesh.new(); o_ = side; kw = 1.05
    TD.build(bm, c, o_, R, K, kw); obj(name + '_Tyre', bm, 'Tyre')
    bm = bmesh.new(); q = 0.216 / 0.203
    rim = [(0.186, -0.080), (0.198, -0.080), (0.206, -0.088), (0.212, -0.084), (0.200, -0.060), (0.186, -0.05), (0.186, 0.050), (0.196, 0.064), (0.208, 0.078), (0.206, 0.084), (0.196, 0.082), (0.190, 0.074)]
    lathe(bm, [(r * q * (0.214 / 0.2256 if r > 0.205 else 1), w * kw) for r, w in rim], 36, True, c, o_)
    lathe(bm, [(0.0, 0.060), (0.032, 0.060), (0.058, 0.054), (0.062, 0.02), (0.0, 0.02)], 20, True, c, o_)
    orim = obj(name + '_Rim', bm, 'Rim'); gi = add_mat(orim, 'Graphite')
    bm = bmesh.new(); bmg = bmesh.new()
    for k in range(10):                                                         # ten straight spokes, machined and graphite in turn
        a = 2 * math.pi * k / 10; pts = []
        for r, hw, wo in ((0.052, 0.013, 0.058), (0.206, 0.022, 0.079)):
            ca, sa = math.cos(a), math.sin(a); px, pz = -sa, ca
            for sgn in (-1, 1):
                for depth in (0, -0.026):
                    pts.append((c[0] + r * ca + px * hw * sgn, c[1] + (wo + depth) * o_, c[2] + r * sa + pz * hw * sgn))
        tb = bm if k % 2 == 0 else bmg; v = [tb.verts.new(p) for p in pts]
        for qd in ((0, 2, 6, 4), (1, 5, 7, 3), (0, 4, 5, 1), (2, 3, 7, 6), (4, 6, 7, 5), (0, 1, 3, 2)):
            try: tb.faces.new([v[i] for i in qd])
            except ValueError: pass
    for tb in (bm, bmg): bmesh.ops.recalc_face_normals(tb, faces=tb.faces[:])
    obj(name + '_Spokes', bm, 'Rim'); obj(name + '_SpokesG', bmg, 'Graphite')
    bm = bmesh.new()
    for k in range(5):                                                          # lug nuts
        a = 2 * math.pi * k / 5 + 0.3; r = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.011, radius2=0.011, depth=0.014)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'), verts=r['verts'])
        bmesh.ops.translate(bm, vec=(c[0] + math.cos(a) * 0.042, c[1] + 0.064 * o_, c[2] + math.sin(a) * 0.042), verts=r['verts'])
    obj(name + '_Nuts', bm, 'Chrome')
    bm = bmesh.new(); lathe(bm, [(0.06, 0.035), (0.165, 0.035), (0.165, 0.012), (0.06, 0.012)], 28, True, c, o_); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); obj(name + '_Disc', bm, 'Disc')
    bm = bmesh.new(); ang = math.radians(150 if x > 0 else 30)
    cc = Vector((c[0] + math.cos(ang) * 0.14, c[1] + 0.045 * o_, c[2] + math.sin(ang) * 0.14))
    bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(0.05, 0.038, 0.115), verts=bm.verts[:])
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(-(ang - math.pi / 2), 3, 'Y'), verts=bm.verts[:])
    bmesh.ops.translate(bm, vec=cc, verts=bm.verts[:]); obj(name + '_Caliper', bm, 'Caliper')
for nm, x, sd in (('Wheel_FL', FX, 1), ('Wheel_FR', FX, -1), ('Wheel_RL', RX, 1), ('Wheel_RR', RX, -1)): wheel(nm, x, sd)

# ---------------- mirrors, handles, spoiler, aerial, slats, badge, plates, pipes
def blob(name, center, size, mname, seg=14, rings=8, rot=None):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=0.5)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts[:])
    if rot: bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot, verts=bm.verts[:])
    bmesh.ops.translate(bm, vec=center, verts=bm.verts[:]); return obj(name, bm, mname)
def cube(name, center, size, mname, rot=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=size, verts=bm.verts[:])
    if rot: bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot, verts=bm.verts[:])
    bmesh.ops.translate(bm, vec=center, verts=bm.verts[:]); return obj(name, bm, mname)
for sd in (1, -1):
    LR = 'L' if sd > 0 else 'R'
    base = surf_point('sz', 1.55, 1.02, sd); bc = B(base)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=0.5)
    for v in bm.verts:
        x, y, z_ = v.co; t = y + 0.5                                              # 0 at the door end, 1 at the outer tip
        x = max(x, -0.30) * 0.13 + 0.02 * t; z_ = z_ * 0.105 * (1.0 - 0.28 * t) + 0.012 * t
        v.co = Vector((x, sd * (y + 0.5) * 0.20, z_))
    hc = bc + Vector((-0.04, sd * 0.07, 0.045)); bmesh.ops.translate(bm, vec=hc, verts=bm.verts[:]); obj('Mirror_' + LR, bm, 'Paint')
    bm = bmesh.new(); vs = []
    for k in range(20):
        a_ = 2 * math.pi * k / 20; yy = (math.cos(a_) * 0.5 + 0.5) * 0.19 + 0.006; t = yy / 0.20
        vs.append(bm.verts.new(hc + Vector((-0.0405 + 0.02 * t, sd * yy, math.sin(a_) * 0.045 * (1 - 0.28 * t) + 0.012 * t))))
    bm.faces.new(vs if sd < 0 else vs[::-1]); obj('Mirror_Glass_' + LR, bm, 'MirrorGlass')
    cube('Mirror_Arm_' + LR, bc + Vector((-0.01, sd * 0.035, 0.03)), (0.07, 0.07, 0.022), 'GlassBlack', Matrix.Rotation(sd * math.radians(12), 3, 'X'))
    blob('Mirror_Rep_' + LR, hc + Vector((0.025, sd * 0.13, -0.025)), (0.05, 0.06, 0.010), 'Amber', 8, 4)
    for hs, hz in ((2.16, 0.858), (3.22, 0.888)):                               # flush chrome handles on the feature line
        p = surf_point('sz', hs, hz, sd); n = nrm(p[None])[0]
        cube('Handle', B(p + n * 0.003), (0.19, 0.012, 0.020), 'Chrome', Matrix.Rotation(math.atan2(-n[0], n[1]) * sd if False else 0, 3, 'Z'))
    p = surf_point('sz', 1.02, 0.84, sd); n = nrm(p[None])[0]                     # side repeater on the wing
    blob('Repeater', B(p + n * 0.003), (0.09, 0.01, 0.016), 'Amber', 8, 4)
# boot lip spoiler: a slim wedge following the deck edge
prof = [(4.50, 0.0), (4.64, 0.016), (4.688, 0.010), (4.684, -0.004), (4.52, -0.004)]
bm = bmesh.new(); vl = []
for yy in np.linspace(-0.66, 0.66, 23):
    row = []
    for ps, dz in prof:
        q = surf_point('sy', min(ps, 4.62), abs(yy), 1 if yy >= 0 else -1)
        zz = (q[2] if q is not None else 1.03) + dz + 0.002 - (0.012 * (ps - 4.62) / 0.07 if ps > 4.62 else 0)
        row.append(bm.verts.new(B((ps, yy, zz))))
    vl.append(row)
for i in range(len(vl) - 1):
    A, Bb = vl[i], vl[i + 1]
    for k in range(len(prof)): bm.faces.new((A[k], A[(k + 1) % len(prof)], Bb[(k + 1) % len(prof)], Bb[k]))
bm.faces.new(vl[0][::-1]); bm.faces.new(vl[-1]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); obj('Spoiler', bm, 'GlassBlack')
# vertical DRL strips in the corner intakes
for sd in (1, -1):
    p0 = surf_point('yz', sd * 0.83, 0.455, 1)
    if p0 is not None: cube('DRL_Strip', B(p0) + Vector((-0.004, 0, 0)), (0.012, 0.026, 0.19), 'LED', Matrix.Rotation(-sd * math.radians(28), 3, 'Z'))
fin = [(2.80, 1.442), (2.88, 1.475), (2.93, 1.488), (2.96, 1.487), (2.975, 1.440)]
bm = bmesh.new(); A = [bm.verts.new(B((a, -0.018, b))) for a, b in fin]; Bb = [bm.verts.new(B((a, 0.018, b))) for a, b in fin]
for k in range(len(fin)): bm.faces.new((A[k], A[(k + 1) % len(fin)], Bb[(k + 1) % len(fin)], Bb[k]))
bm.faces.new(A[::-1]); bm.faces.new(Bb); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); obj('Aerial', bm, 'GlassBlack')
# grille slats (horizontal, gloss black with a bright top edge)
bm = bmesh.new()
for zz in (0.700, 0.668, 0.636, 0.604):
    w = 0.43 + (zz - 0.58) / 0.14 * 0.05; ys = np.linspace(-w, w, 19); rows = []
    for yy in ys:
        p = surf_point('yz', yy, zz, 1)
        if p is None: continue
        p = p + np.array([0.012, 0, 0]); rows.append([bm.verts.new(B(p + np.array([0, 0, dz]))) for dz in (0.006, -0.006)] + [bm.verts.new(B(p + np.array([0.012, 0, 0.006])))])
    for a_, b_ in zip(rows[:-1], rows[1:]):
        bm.faces.new((a_[0], b_[0], b_[1], a_[1])); bm.faces.new((a_[2], b_[2], b_[0], a_[0]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); obj('Slats', bm, 'Lamp')
# lower intake: vertical fins
bm = bmesh.new()
for k in range(-5, 6):
    yy = k * 0.10; p0 = surf_point('yz', yy, 0.475, 1); p1 = surf_point('yz', yy, 0.31, 1)
    if p0 is None or p1 is None: continue
    for p_, q_ in ((p0, p1),):
        v = [bm.verts.new(B(p_ + np.array([0.02, -0.006, 0]))), bm.verts.new(B(p_ + np.array([0.02, 0.006, 0]))), bm.verts.new(B(q_ + np.array([0.02, 0.006, 0]))), bm.verts.new(B(q_ + np.array([0.02, -0.006, 0])))]
        bm.faces.new(v)
obj('Fins', bm, 'Clad')
# V badge on the grille: two chrome bars
p = surf_point('yz', 0.0, 0.655, 1); bc = B(p) + Vector((0.018, 0, 0))
for sgn in (1, -1):
    cube('Badge', bc + Vector((0, sgn * 0.022, 0.0)), (0.010, 0.010, 0.064), 'Chrome', Matrix.Rotation(sgn * math.radians(-40), 3, 'X'))
for nm_, pz, front in (('Plate_F', 0.415, True), ('Plate_R', 0.60, False)):
    p = surf_point('yz', 0.0, pz, 1 if front else -1)
    cube(nm_, B(p) + Vector((0.008 if front else -0.008, 0, 0)), (0.008, 0.52, 0.11), 'Plate')
# chrome tail-pipe trims round the recessed outlets
for sd in (1, -1):
    p = surf_point('yz', sd * 0.52, 0.40, -1); c = B(p) + Vector((0.004, 0, 0))
    bm = bmesh.new(); n = 20; vo = []; vi = []
    for k in range(n):
        a = 2 * math.pi * k / n; cy, cz = math.cos(a), math.sin(a)
        e = lambda rx, rz: (np.sign(cy) * abs(cy) ** 0.4 * rx, np.sign(cz) * abs(cz) ** 0.4 * rz)
        oy, oz = e(0.108, 0.032); iy, iz = e(0.094, 0.020)
        vo.append(bm.verts.new(c + Vector((-0.004, oy, oz)))); vi.append(bm.verts.new(c + Vector((-0.004, iy, iz))))
    for k in range(n): bm.faces.new((vo[k], vo[(k + 1) % n], vi[(k + 1) % n], vi[k]))
    obj('Pipe_Trim', bm, 'Chrome')

# ---------------- light lines, reverse lamps, reflectors: emissive ribbons and plates laid on the body surface
def surf_diag(u, z, front=True, side=1):
    c = math.sqrt(2) * u; t = np.linspace(0.9, -0.6, 900)
    s = c / 2 - t; y = c / 2 + t
    if not front: s = M.L - s
    P = np.c_[s, side * y, np.full_like(t, z)]; d = dval(P); k = np.argmax(d < 0)
    if k == 0: return None
    f = d[k - 1] / (d[k - 1] - d[k]); return P[k - 1] + (P[k] - P[k - 1]) * f
bml = bmesh.new()
for sd in (1, -1):
    ribbon(bml, [surf_diag(u, z, True, sd) for u, z in dense(Zn.HL_DRL, 0.01)], 0.0075, 0.003)
    for bar in Zn.TL_BARS: ribbon(bml, [surf_diag(u, z, False, sd) for u, z in dense(bar, 0.01)], 0.0035, 0.0015)
gb = [surf_point('yz', yy, 0.742, 1) for yy in np.linspace(-0.45, 0.45, 69)]
gv = [(bml.verts.new(B(q) + Vector((0.006, 0, 0.0065))), bml.verts.new(B(q) + Vector((0.006, 0, -0.0065)))) for q in gb if q is not None]
for (a0, b0), (a1, b1) in zip(gv[:-1], gv[1:]): bml.faces.new((a0, b0, b1, a1))
bmesh.ops.recalc_face_normals(bml, faces=bml.faces[:]); oled = obj('LightLines', bml, 'LED')
bmt = bmesh.new()
ribbon(bmt, [surf_point('yz', yy, 0.972, -1) for yy in np.linspace(-0.60, 0.60, 80)], 0.004, 0.0015)
bmesh.ops.recalc_face_normals(bmt, faces=bmt.faces[:]); obj('TailLines', bmt, 'TailLED')
for og_, nm_ in ((oled, 'LightLines'), (bpy.data.objects['TailLines'], 'TailLines')):
    me_ = og_.data; bm_ = bmesh.new(); bm_.from_mesh(me_)
    for f in bm_.faces:
        c_ = f.calc_center_median(); n_ = nrm(np.array([[C0 - c_.x, c_.y, c_.z]]))[0]
        if f.normal.dot(Bn(n_)) < 0: f.normal_flip()
    bm_.to_mesh(me_); bm_.free()
for sd in (1, -1):
    for nm_, zz, yc, hw, hh, mt in (('Reverse', 0.315, 0.58, 0.07, 0.014, 'Reverse'), ('Reflector', 0.43, 0.78, 0.06, 0.014, 'Reflector')):
        p0 = surf_point('yz', sd * yc, zz, -1)
        if p0 is not None: cube(nm_, B(p0) + Vector((-0.002, 0, 0)), (0.008, 2 * hw, 2 * hh), mt)
# plates with printed text
from PIL import Image as _I, ImageDraw as _D, ImageFont as _F
pim = _I.new('RGB', (520, 110), (238, 236, 228)); dr = _D.Draw(pim)
try: fnt = _F.truetype('/usr/share/fonts/opentype/inter/Inter-Bold.otf', 70)
except Exception: fnt = _F.load_default()
dr.rectangle((0, 0, 519, 109), outline=(40, 40, 40), width=5); dr.rectangle((5, 5, 40, 104), fill=(30, 70, 160))
dr.text((285, 56), 'AU · T104', fill=(25, 25, 25), font=fnt, anchor='mm'); pim.save('/tmp/plate_taxi.png')
img = bpy.data.images.load('/tmp/plate_taxi.png'); img.pack()
mt_ = bpy.data.materials['PlateText']; tx = mt_.node_tree.nodes.new('ShaderNodeTexImage'); tx.image = img
mt_.node_tree.links.new(tx.outputs['Color'], mt_.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
for nm_, pz, front in (('PlateTxt_F', 0.415, True), ('PlateTxt_R', 0.60, False)):
    p0 = surf_point('yz', 0.0, pz, 1 if front else -1); c_ = B(p0) + Vector((0.0165 if front else -0.0165, 0, 0))
    bm = bmesh.new(); sgn = 1 if front else -1
    vs = [bm.verts.new(c_ + Vector((0, sgn * yy, zz))) for yy, zz in ((-0.26, -0.055), (0.26, -0.055), (0.26, 0.055), (-0.26, 0.055))]
    f = bm.faces.new(vs); uv = bm.loops.layers.uv.new()
    for l, q in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): l[uv].uv = q
    if f.normal.x * sgn < 0: f.normal_flip()
    obj(nm_, bm, 'PlateText')
# ---------------- interior (seen through the glass)
def box(name, cx, cy, cz, sx, sy, sz, mname, rot=0.0, bev=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts[:])
    if bev: bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bev, segments=3, profile=0.5, affect='EDGES')
    if rot: bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rot, 3, 'Y'), verts=bm.verts[:])
    bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=bm.verts[:]); return obj(name, bm, mname)
X = lambda s: C0 - s
box('Floor', X(2.60), 0, 0.33, 2.6, 1.50, 0.02, 'Interior')
for sd in (1, -1):
    box('DoorCard', X(2.45), sd * 0.74, 0.74, 2.0, 0.02, 0.50, 'Interior')
    box('Seat_Cushion', X(2.52), sd * 0.39, 0.50, 0.52, 0.50, 0.12, 'Leather', bev=0.04)
    box('Seat_Back', X(2.84), sd * 0.39, 0.84, 0.13, 0.48, 0.62, 'Leather', rot=math.radians(-16), bev=0.05)
    box('Headrest', X(2.93), sd * 0.39, 1.21, 0.09, 0.26, 0.17, 'Leather', rot=math.radians(-16), bev=0.035)
box('Rear_Bench', X(3.38), 0, 0.50, 0.50, 1.40, 0.12, 'Leather', bev=0.04); box('Rear_Back', X(3.60), 0, 0.80, 0.12, 1.40, 0.50, 'Leather', rot=math.radians(-22), bev=0.045)
for sd in (1, -1): box('Rear_Headrest', X(3.69), sd * 0.42, 1.06, 0.07, 0.22, 0.10, 'Leather', rot=math.radians(-22), bev=0.03)
box('Parcel_Shelf', X(3.76), 0, 1.06, 0.30, 1.30, 0.02, 'Interior')
box('Dash', X(1.92), 0, 0.84, 0.40, 1.40, 0.22, 'Interior', rot=math.radians(8), bev=0.04); box('Dash_Top', X(1.82), 0, 0.96, 0.30, 1.34, 0.04, 'Interior', rot=math.radians(-12))
box('Screen', X(1.98), 0.0, 1.02, 0.02, 0.30, 0.16, 'GlassBlack', rot=math.radians(-20))
box('Console', X(2.25), 0, 0.55, 0.70, 0.22, 0.30, 'Interior', bev=0.03)
box('Headliner', X(2.62), 0, 1.37, 1.2, 0.95, 0.012, 'Headliner')
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=False, segments=20, radius=0.18)
r2 = bmesh.ops.extrude_edge_only(bm, edges=bm.edges[:]); nv = [e for e in r2['geom'] if isinstance(e, bmesh.types.BMVert)]; bmesh.ops.scale(bm, vec=(0.82, 0.82, 1), verts=nv)
bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90 - 24), 3, 'Y'), verts=bm.verts[:]); bmesh.ops.translate(bm, vec=(X(2.08), 0.39, 0.96), verts=bm.verts[:]); obj('Steering', bm, 'Interior')

# ---------------- taxi dress: lit roof sign, checker band and lettering on both sides
q = surf_point('sy', 2.61, 0.0, 1); zr = q[2] if q is not None else 1.448
cube('Sign_Base', B((2.61, 0.0, zr + 0.010)), (0.50, 0.70, 0.022), 'GlassBlack')
bm = bmesh.new(); prof = [(-0.21, 0.0), (0.21, 0.0), (0.17, 0.145), (-0.17, 0.145)]
A = [bm.verts.new(B((2.61 + a, -0.31, zr + 0.021 + b))) for a, b in prof]; Bq = [bm.verts.new(B((2.61 + a, 0.31, zr + 0.021 + b))) for a, b in prof]
for k in range(4): bm.faces.new((A[k], A[(k + 1) % 4], Bq[(k + 1) % 4], Bq[k]))
bm.faces.new(A[::-1]); bm.faces.new(Bq); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); obj('Sign_Box', bm, 'SignBody')
sm = DC.material('SignText', '/tmp/taxi_sign.png', 0.4, 1.2); sm.use_backface_culling = True
for sgn in (1, -1):                                                   # TAXI on the front and back faces, tilted like the box
    bm = bmesh.new(); uv = bm.loops.layers.uv.new(); x0 = 2.61 - sgn * 0.2092
    pts = [(x0, -0.29, zr + 0.031), (x0, 0.29, zr + 0.031), (x0 + sgn * 0.0344, 0.29, zr + 0.156), (x0 + sgn * 0.0344, -0.29, zr + 0.156)]
    vs = [bm.verts.new(B(p)) for p in pts]; f = bm.faces.new(vs)
    for l, p in zip(f.loops, pts):
        u = (p[1] + 0.29) / 0.58; l[uv].uv = (u if sgn > 0 else 1 - u, 0.0 if p[2] < zr + 0.1 else 1.0)
    bm.normal_update()
    if (f.normal.x > 0) != (sgn > 0): f.normal_flip()
    me = bpy.data.meshes.new('SignFace'); bm.to_mesh(me); bm.free(); me.materials.append(sm); o = bpy.data.objects.new('SignFace', me); bpy.context.scene.collection.objects.link(o); PARTS.append(o)
for sd in (1, -1):
    LR = 'L' if sd > 0 else 'R'
    dm_ = DC.material('TaxiDoors_' + LR, '/tmp/taxi_doors_%s.png' % LR, 0.3)
    DECALS.append(DC.side_decal('Taxi_Doors_' + LR, dm_, 1.40, 3.42, 0.44, 0.84, sd, surf_point, nrm, B, Bn, bpy.context.scene.collection.objects.link, 72, 16, 0.0018, sd < 0))
# ---------------- join: body + parts make LOD0; a decimated copy makes LOD1
for o in bpy.context.scene.objects: o.select_set(False)
parts = [o for o in PARTS if o.name in bpy.context.scene.objects]
WHEELS = []                                                      # each wheel is its own node (origin on the axle) so the game can spin it
for wn, wx, wsd in (('Wheel_FL', FX, 1), ('Wheel_FR', FX, -1), ('Wheel_RL', RX, 1), ('Wheel_RR', RX, -1)):
    ws = [o for o in parts if o.name.startswith(wn + '_') and not o.name.endswith('_Caliper')]
    if not ws: continue
    for o in bpy.context.scene.objects: o.select_set(False)
    for o in ws: o.select_set(True)
    bpy.context.view_layer.objects.active = ws[0]; bpy.ops.object.join(); wo_ = bpy.context.view_layer.objects.active; wo_.name = NM + '_' + wn
    bpy.context.scene.cursor.location = (wx, wsd * TRK, R); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    for pp in wo_.data.polygons: pp.use_smooth = True
    wo_.data.set_sharp_from_angle(angle=math.radians(35))
    WHEELS.append(wo_); parts = [o for o in parts if o not in ws]
for o in bpy.context.scene.objects: o.select_set(False)
bpy.context.view_layer.objects.active = parts[0]
for o in parts: o.select_set(True)
bpy.ops.object.join(); P0 = bpy.context.view_layer.objects.active; P0.name = NM + '_Parts'
for p in P0.data.polygons: p.use_smooth = True
P0.data.set_sharp_from_angle(angle=math.radians(40)) if hasattr(P0.data, 'set_sharp_from_angle') else None
lod0 = bpy.data.objects.new('LOD0', None); bpy.context.scene.collection.objects.link(lod0); body.parent = lod0; P0.parent = lod0; body.name = NM + '_Body'
for wo_ in WHEELS + DECALS: wo_.parent = lod0
# far copy: field surface at 24 mm, zones taken from the finished near body (closest surface point), then decimated with zone borders held
from skimage.measure import marching_cubes
from mathutils.bvhtree import BVHTree
Dc = D[::2, ::2, ::2]; Vf, Ff, _, _ = marching_cubes(Dc, 0.0, spacing=(M.H * 2,) * 3); Vf = Vf + o3
fn_ = np.cross(Vf[Ff[:, 1]] - Vf[Ff[:, 0]], Vf[Ff[:, 2]] - Vf[Ff[:, 0]])
if (np.einsum('ij,ij->i', fn_, nrm(Vf[Ff].mean(1))) < 0).mean() > 0.5: Ff = Ff[:, ::-1]
_m = bpy.data.meshes.new('pre'); _m.from_pydata(Vf.tolist(), [], Ff.tolist()); _m.update(); _o = bpy.data.objects.new('pre', _m); bpy.context.scene.collection.objects.link(_o)
for o in bpy.context.scene.objects: o.select_set(False)
bpy.context.view_layer.objects.active = _o; _d = _o.modifiers.new('d', 'DECIMATE'); _d.ratio = float(os.environ.get('FPRE', '0.12')); _d.use_collapse_triangulate = True; bpy.ops.object.modifier_apply(modifier='d')
Vf = np.array([v.co[:] for v in _m.vertices]); Ff = np.array([pp.vertices[:] for pp in _m.polygons]); bpy.data.objects.remove(_o)
for it in range(3): Vf = Vf - nrm(Vf) * dval(Vf)[:, None]
names = ['Paint', 'Clad', 'Liner', 'Chrome', 'Glass', 'GlassBlack', 'Lamp', 'Grille', 'Intake', 'Tail']
remap = {'Seal': 'GlassBlack', 'DRL': 'Intake', 'Pipe': 'Intake', 'LED': 'Lamp', 'TailLED': 'Tail', 'Reverse': 'Clad', 'Reflector': 'Clad'}
bme = body.data; bnames = [m.name for m in bme.materials]; NZ = np.array([pp.material_index for pp in bme.polygons])
bvh = BVHTree.FromPolygons([v.co[:] for v in bme.vertices], [pp.vertices[:] for pp in bme.polygons])
import meshcut as MCUT
Fs = Ff.copy()
for n_, fnc, _ in Zn.zone_fns():
    if n_ in ('Clad', 'Liner', 'Chrome', 'Glass', 'GlassBlack', 'Lamp', 'Tail', 'Grille', 'Intake'): Vf, Fs = MCUT.cut(Vf, Fs, fnc(Vf[:, 0], Vf[:, 1], Vf[:, 2]))
Ff = Fs; Pb = np.c_[C0 - Vf[:, 0], Vf[:, 1], Vf[:, 2]]; Fb = Ff[:, ::-1]
Cb = Pb[Fb].mean(1); Nb = np.c_[-nrm(Vf[Ff].mean(1))[:, 0], nrm(Vf[Ff].mean(1))[:, 1:]]
nn = np.array([bvh.find_nearest(Vector(c - n * 0.002))[2] for c, n in zip(Cb, Nb)])
lab = [remap.get(bnames[k], bnames[k]) for k in NZ[nn]]; zi = np.array([names.index(l) if l in names else 0 for l in lab])
E = np.r_[Fb[:, [0, 1]], Fb[:, [1, 2]], Fb[:, [2, 0]]]; Ez = np.r_[zi, zi, zi]; Es = np.sort(E, 1)
order = np.lexsort((Es[:, 1], Es[:, 0])); Es, Ez = Es[order], Ez[order]
same = (Es[1:] == Es[:-1]).all(1) & (Ez[1:] != Ez[:-1]); bverts = np.unique(Es[1:][same].ravel())
mf = bpy.data.meshes.new('far'); mf.from_pydata(Pb.tolist(), [], Fb.tolist()); mf.update()
for n in names: mf.materials.append(bpy.data.materials[n])
mf.polygons.foreach_set('material_index', zi.astype(np.int32)); mf.update()
far = bpy.data.objects.new(NM + '_Far', mf); bpy.context.scene.collection.objects.link(far)
vg = far.vertex_groups.new(name='keep'); vg.add(bverts.tolist(), 1.0, 'REPLACE')
for o in bpy.context.scene.objects: o.select_set(False)
bpy.context.view_layer.objects.active = far; far.select_set(True)
dm = far.modifiers.new('d', 'DECIMATE'); dm.ratio = float(os.environ.get('FAR', '0.3')); dm.use_collapse_triangulate = True; dm.vertex_group = 'keep'; dm.invert_vertex_group = True; dm.vertex_group_factor = float(os.environ.get('VGF', '0.25'))
bpy.ops.object.modifier_apply(modifier='d') if dm.ratio < 1 else far.modifiers.remove(dm)
Pv = np.array([[C0 - v.co.x, v.co.y, v.co.z] for v in mf.vertices])
for it in range(2): Pv = Pv - nrm(Pv) * dval(Pv)[:, None]
mf.vertices.foreach_set('co', np.c_[C0 - Pv[:, 0], Pv[:, 1], Pv[:, 2]].ravel().astype(np.float32)); mf.update()
for p in mf.polygons: p.use_smooth = True
bm = bmesh.new()
for x in (FX, RX):
    for sd in (1, -1):
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=R, radius2=R, depth=0.2)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'), verts=r['verts']); bmesh.ops.translate(bm, vec=(x, sd * TRK, R), verts=r['verts'])
wo = obj('far_wheels', bm, 'TyreFar'); PARTS.remove(wo)
for o in bpy.context.scene.objects: o.select_set(False)
far.select_set(True); wo.select_set(True); bpy.context.view_layer.objects.active = far; bpy.ops.object.join()
lod1 = bpy.data.objects.new('LOD1', None); bpy.context.scene.collection.objects.link(lod1); far.parent = lod1
tris = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
print('TRIS body', tris(body), 'parts', tris(P0), 'far', tris(far))
bpy.ops.wm.save_as_mainfile(filepath=OUT + '.blend')
for o in bpy.context.scene.objects: o.select_set(o.name in ('LOD0', 'LOD1', NM + '_Body', NM + '_Parts', NM + '_Far') or o in WHEELS or o in DECALS)
bpy.ops.export_scene.gltf(filepath=OUT + '.glb', export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
print('EXPORTED')

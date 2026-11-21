"""Mira: parts, gap lines, materials, interior, wheels, LODs; exports the game GLB and a .blend.
Blender frame: +X forward, +Y left, Z up, origin on the ground between the axles. Sheet s -> x = 2.125 - s."""
import sys, os, math, numpy as np, bpy, bmesh
sys.path.insert(0, '/home/claude/traffic'); import mira_sdf as M, mira_zones as Zn
from scipy import ndimage
from mathutils import Vector, Matrix
OUT = os.environ.get('OUT', '/tmp/mira')
bpy.ops.wm.open_mainfile(filepath='/tmp/mira_body.blend')
D, s_, y_, z_ = M.field(); o3 = np.array([s_[0], y_[0], z_[0]]); Ds = ndimage.gaussian_filter(D, 1.3); G = np.gradient(Ds, M.H)
def dval(P): return ndimage.map_coordinates(D, ((np.atleast_2d(P) - o3) / M.H).T, order=1, mode='nearest')
def nrm(P):
    idx = ((np.atleast_2d(P) - o3) / M.H).T; N = np.stack([ndimage.map_coordinates(g, idx, order=1, mode='nearest') for g in G], 1); return N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-9)
def B(p): return Vector((2.125 - p[0], p[1], p[2]))           # sheet point -> Blender
def Bn(n): return Vector((-n[0], n[1], n[2]))

# ---------------- materials
def mat(name, col, rough=0.5, metal=0.0, emit=None, alpha=1.0, coat=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if coat: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.04
    if emit: b.inputs['Emission Color'].default_value = (*emit[0], 1); b.inputs['Emission Strength'].default_value = emit[1]
    if alpha < 1: b.inputs['Alpha'].default_value = alpha; m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None; m.surface_render_method = 'BLENDED'
    m.use_backface_culling = name not in ('Interior', 'Headliner', 'GapLine'); m.diffuse_color = (*col, 1); return m
MATS = dict(Paint=((0.92, 0.92, 0.92), 0.32, 0.18, None, 1, 1.0), Clad=((0.045, 0.045, 0.05), 0.72), Liner=((0.018, 0.018, 0.02), 0.9), GapLine=((0.004, 0.004, 0.005), 1.0),
            Glass=((0.012, 0.018, 0.024), 0.03, 0.0, None, 0.74), GlassBlack=((0.008, 0.008, 0.01), 0.08), Lamp=((0.05, 0.055, 0.06), 0.10, 1.0), LED=((1, 1, 1), 0.2, 0, ((1, 0.98, 0.94), 4.0)),
            Tail=((0.42, 0.012, 0.018), 0.14), TailBand=((0.01, 0.01, 0.012), 0.08), TailLED=((0.9, 0.08, 0.06), 0.2, 0, ((1, 0.06, 0.03), 2.5)), Reverse=((0.92, 0.92, 0.92), 0.15),
            Grille=((0.014, 0.014, 0.016), 0.55), Intake=((0.014, 0.014, 0.016), 0.6), Reflector=((0.5, 0.02, 0.02), 0.2), Tyre=((0.028, 0.028, 0.03), 0.86), Rim=((0.58, 0.59, 0.61), 0.3, 1.0),
            Disc=((0.13, 0.13, 0.135), 0.5, 0.8), Caliper=((0.10, 0.30, 0.66), 0.38), Chrome=((0.92, 0.92, 0.93), 0.07, 1.0), Plate=((0.93, 0.93, 0.89), 0.5),
            Interior=((0.03, 0.03, 0.033), 0.75), Headliner=((0.42, 0.41, 0.39), 0.9), MirrorGlass=((0.55, 0.6, 0.65), 0.02, 1.0), PlateText=((1, 1, 1), 0.5), Amber=((0.95, 0.45, 0.05), 0.2))
for k, v in MATS.items():
    col, rough = v[0], v[1]; metal = v[2] if len(v) > 2 else 0; emit = v[3] if len(v) > 3 else None; alpha = v[4] if len(v) > 4 else 1; coat = v[5] if len(v) > 5 else 0
    mat(k, col, rough, metal, emit, alpha, coat)
body = bpy.data.objects['Body']
for i, m in enumerate(body.data.materials):                      # the body's zone slots use the same named materials
    if m.name in MATS: continue
    nm = {'Seal': 'GlassBlack'}.get(m.name, m.name)
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
    else: t = np.linspace(-0.08, 1.2, 700) if side > 0 else np.linspace(4.33, 3.2, 700); P = np.c_[t, np.full_like(t, a), np.full_like(t, b)]
    d = dval(P); k = np.argmax(d < 0)
    if k == 0: return None
    f = d[k - 1] / (d[k - 1] - d[k]); return P[k - 1] + (P[k] - P[k - 1]) * f
def ribbon(bm, pts3, w=0.0024, lift=0.0025):
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
for proj, pl, mk in Zn.GAPS:
    sides = (1, -1) if proj in ('sz', 'sy') else ((1,) if np.mean([p[1] for p in pl]) < 1.5 and proj == 'yz' and pl[0][1] < 0.8 else (-1,))
    for sd in sides:
        pts = [surf_point(proj, a, b, sd) for a, b in dense(pl)]
        ribbon(bmg, pts)
# fuel flap outline (left side)
fl = [(3.72, 0.87), (3.85, 0.87), (3.85, 0.97), (3.72, 0.97), (3.72, 0.87)]
ribbon(bmg, [surf_point('sz', a, b, 1) for a, b in dense(fl, 0.008)], 0.0018)
bmesh.ops.recalc_face_normals(bmg, faces=bmg.faces[:])
og = obj('GapLines', bmg, 'GapLine')
for f in og.data.polygons:                                       # face the ribbons outward
    pass
me = og.data
Pv = np.array([[2.125 - v.co.x, v.co.y, v.co.z] for v in me.vertices]); Nv = nrm(Pv)
flip = []
bm = bmesh.new(); bm.from_mesh(me)
for f in bm.faces:
    c = f.calc_center_median(); n = nrm(np.array([[2.125 - c.x, c.y, c.z]]))[0]
    if f.normal.dot(Bn(n)) < 0: f.normal_flip()
bm.to_mesh(me); bm.free()

# ---------------- wheels
FX, RX, TRK, R = 1.325, -1.325, 0.762, M.R
def lathe(bm, prof, seg, ax_y, center, flipw=1):
    """Revolve (radius, w) profile round the Y axis at center."""
    rings = []
    for k in range(seg):
        a = 2 * math.pi * k / seg; ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((center[0] + r * ca, center[1] + w * flipw, center[2] + r * sa)) for r, w in prof])
    for k in range(seg):
        A, Bb = rings[k], rings[(k + 1) % seg]
        for i in range(len(prof) - 1): bm.faces.new((A[i], A[i + 1], Bb[i + 1], Bb[i]))
    return rings
def wheel(name, x, side):
    c = (x, side * TRK, R); bm = bmesh.new(); o_ = side                      # outer face toward +side
    tyre = [(0.203, -0.086), (0.232, -0.099), (0.268, -0.1035), (0.300, -0.097), (0.313, -0.083), (0.318, -0.062), (0.318, -0.034), (0.318, -0.006),
            (0.311, 0.0), (0.318, 0.006), (0.318, 0.034), (0.318, 0.062), (0.313, 0.083), (0.300, 0.097), (0.268, 0.1035), (0.232, 0.099), (0.203, 0.086)]
    lathe(bm, tyre, 30, True, c, o_); ot = obj(name + '_Tyre', bm, 'Tyre')
    bm = bmesh.new()
    rim = [(0.186, -0.080), (0.198, -0.080), (0.206, -0.088), (0.212, -0.084), (0.200, -0.060), (0.186, -0.05), (0.186, 0.050), (0.200, 0.062), (0.214, 0.078), (0.208, 0.090), (0.195, 0.086), (0.188, 0.070)]
    lathe(bm, rim, 30, True, c, o_)
    hub = [(0.0, 0.058), (0.03, 0.058), (0.055, 0.052), (0.058, 0.02), (0.0, 0.02)]
    lathe(bm, hub, 18, True, c, o_)
    for k in range(5):                                                       # five twin spokes
        for da in (-0.13, 0.13):
            a0 = 2 * math.pi * k / 5 + da * 0.55; a1 = 2 * math.pi * k / 5 + da
            pts = []
            for r, a, hw, wo in ((0.05, a0, 0.012, 0.050), (0.192, a1, 0.015, 0.076)):
                ca, sa = math.cos(a), math.sin(a); px, pz = -sa, ca
                for sgn in (-1, 1):
                    for depth in (0, -0.024):
                        pts.append((c[0] + r * ca + px * hw * sgn, c[1] + (wo + depth) * o_, c[2] + r * sa + pz * hw * sgn))
            v = [bm.verts.new(p) for p in pts]
            # v: [in-l-front, in-l-back, in-r-front, in-r-back, out-l-front, out-l-back, out-r-front, out-r-back]
            for q in ((0, 2, 6, 4), (1, 5, 7, 3), (0, 4, 5, 1), (2, 3, 7, 6), (4, 6, 7, 5), (0, 1, 3, 2)):
                try: bm.faces.new([v[i] for i in q])
                except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); orim = obj(name + '_Rim', bm, 'Rim')
    bm = bmesh.new(); lathe(bm, [(0.06, 0.035), (0.150, 0.035), (0.150, 0.015), (0.06, 0.015)], 24, True, c, o_); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); obj(name + '_Disc', bm, 'Disc')
    bm = bmesh.new(); ang = math.radians(150 if x > 0 else 30)                   # caliper behind the spokes, toward the car centre
    cc = Vector((c[0] + math.cos(ang) * 0.125, c[1] + 0.045 * o_, c[2] + math.sin(ang) * 0.125))
    r_ = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(0.05, 0.035, 0.105), verts=bm.verts[:])
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(ang - math.pi / 2, 3, 'Y').inverted() if False else Matrix.Rotation(-(ang - math.pi / 2), 3, 'Y'), verts=bm.verts[:])
    bmesh.ops.translate(bm, vec=cc, verts=bm.verts[:]); obj(name + '_Caliper', bm, 'Caliper')
for nm, x, sd in (('Wheel_FL', FX, 1), ('Wheel_FR', FX, -1), ('Wheel_RL', RX, 1), ('Wheel_RR', RX, -1)): wheel(nm, x, sd)

# ---------------- mirrors, handles, spoiler, aerial, slats, badge, plates
def blob(name, center, size, mname, seg=14, rings=8, rot=None):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=0.5)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts[:])
    if rot: bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot, verts=bm.verts[:])
    bmesh.ops.translate(bm, vec=center, verts=bm.verts[:]); return obj(name, bm, mname)
for sd in (1, -1):
    base = surf_point('sz', 1.30, 1.03, sd)                                        # mirror on the door, ahead of the window
    bc = B(base); bc.y += sd * 0.005
    LR = 'L' if sd > 0 else 'R'
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=0.5)
    for v in bm.verts:
        x, y, z_ = v.co; t = y + 0.5
        x = max(x, -0.30) * 0.13 + 0.02 * t; z_ = z_ * 0.105 * (1.0 - 0.28 * t) + 0.012 * t
        v.co = Vector((x, sd * (y + 0.5) * 0.20, z_))
    hc = bc + Vector((-0.04, sd * 0.07, 0.045)); bmesh.ops.translate(bm, vec=hc, verts=bm.verts[:]); obj('Mirror_' + LR, bm, 'Paint')
    bm = bmesh.new(); vs = []
    for k in range(20):
        a_ = 2 * math.pi * k / 20; yy = (math.cos(a_) * 0.5 + 0.5) * 0.19 + 0.006; t = yy / 0.20
        vs.append(bm.verts.new(hc + Vector((-0.0405 + 0.02 * t, sd * yy, math.sin(a_) * 0.045 * (1 - 0.28 * t) + 0.012 * t))))
    bm.faces.new(vs if sd < 0 else vs[::-1]); obj('Mirror_Glass_' + LR, bm, 'MirrorGlass')
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(0.07, 0.07, 0.022), verts=bm.verts[:])
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(sd * math.radians(12), 3, 'X'), verts=bm.verts[:]); bmesh.ops.translate(bm, vec=bc + Vector((-0.01, sd * 0.035, 0.03)), verts=bm.verts[:]); obj('Mirror_Arm_' + LR, bm, 'GlassBlack')
    blob('Mirror_Rep_' + LR, hc + Vector((0.025, sd * 0.13, -0.025)), (0.05, 0.06, 0.010), 'Amber', 8, 4)
    for hs, hz in ((1.95, 0.868), (3.02, 0.903)):
        p = surf_point('sz', hs + 0.09, hz, sd); n = nrm(p[None])[0]
        blob('Handle', B(p + n * 0.006), (0.17, 0.022, 0.028), 'Paint', 12, 6)
        blob('Handle_Pocket', B(p - n * 0.002 + np.array([0, 0, -0.004])), (0.15, 0.006, 0.036), 'GlassBlack', 10, 4)
# roof spoiler: side profile extruded across the roof end
prof = [(3.66, 1.448), (3.86, 1.432), (3.995, 1.392), (3.99, 1.362), (3.86, 1.392), (3.70, 1.425)]
bm = bmesh.new(); vl = []
for yy in (-0.56, -0.50, 0.50, 0.56):
    sh = 0.012 if abs(yy) > 0.52 else 0.0
    vl.append([bm.verts.new(B((ps, yy, pz - sh * 1.5))) for ps, pz in prof])
for i in range(3):
    A, Bb = vl[i], vl[i + 1]
    for k in range(len(prof)): bm.faces.new((A[k], A[(k + 1) % len(prof)], Bb[(k + 1) % len(prof)], Bb[k]))
bm.faces.new(vl[0][::-1]); bm.faces.new(vl[3]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); obj('Spoiler', bm, 'GlassBlack')
fin = [(3.44, 1.445), (3.52, 1.475), (3.565, 1.487), (3.595, 1.486), (3.61, 1.443)]
bm = bmesh.new(); A = [bm.verts.new(B((a, -0.018, b))) for a, b in fin]; Bb = [bm.verts.new(B((a, 0.018, b))) for a, b in fin]
for k in range(len(fin)): bm.faces.new((A[k], A[(k + 1) % len(fin)], Bb[(k + 1) % len(fin)], Bb[k]))
bm.faces.new(A[::-1]); bm.faces.new(Bb); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); obj('Aerial', bm, 'GlassBlack')
# grille slats and centre badge
bm = bmesh.new()
for k, zz in enumerate((0.545, 0.495, 0.445, 0.395)):
    w = 0.50 + (zz - 0.345) / 0.23 * 0.06 - 0.035; ys = np.linspace(-w, w, 17); rows = []
    for yy in ys:
        p = surf_point('yz', yy, zz, 1)
        if p is None: continue
        p = p + np.array([0.016, 0, 0]); rows.append([bm.verts.new(B(p + np.array([0, 0, dz]))) for dz in (0.007, -0.007)] + [bm.verts.new(B(p + np.array([0.012, 0, 0.007])))])
    for a, b_ in zip(rows[:-1], rows[1:]):
        bm.faces.new((a[0], b_[0], b_[1], a[1])); bm.faces.new((a[2], b_[2], b_[0], a[0]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); obj('Slats', bm, 'Lamp')
p = surf_point('yz', 0.0, 0.668, 1); bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=False, segments=24, radius=0.042)
ring = bm.verts[:]; bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'), verts=ring)
r2 = bmesh.ops.extrude_edge_only(bm, edges=bm.edges[:]); nv = [e for e in r2['geom'] if isinstance(e, bmesh.types.BMVert)]
bmesh.ops.scale(bm, vec=(1, 0.8, 0.8), verts=nv); bmesh.ops.translate(bm, vec=(0.004, 0, 0), verts=nv)
for v in bm.verts: v.co += B(p) + Vector((0.004, 0, 0))
obj('Badge', bm, 'Chrome')
for nm_, pz, front in (('Plate_F', 0.455, True), ('Plate_R', 0.765, False)):
    p = surf_point('yz', 0.0, pz, 1 if front else -1)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(0.008, 0.52, 0.11), verts=bm.verts[:])
    bmesh.ops.translate(bm, vec=B(p) + Vector((0.006 if front else -0.006, 0, 0)), verts=bm.verts[:]); obj(nm_, bm, 'Plate')
from PIL import Image as _I, ImageDraw as _D, ImageFont as _F
pim = _I.new('RGB', (520, 110), (238, 236, 228)); dr = _D.Draw(pim); fnt = _F.truetype('/usr/share/fonts/opentype/inter/Inter-Bold.otf', 70)
dr.rectangle((0, 0, 519, 109), outline=(40, 40, 40), width=5); dr.rectangle((5, 5, 40, 104), fill=(30, 70, 160)); dr.text((285, 56), 'AU · M1RA', fill=(25, 25, 25), font=fnt, anchor='mm'); pim.save('/tmp/plate_mira.png')
img = bpy.data.images.load('/tmp/plate_mira.png'); img.pack(); mt_ = bpy.data.materials['PlateText']; tx = mt_.node_tree.nodes.new('ShaderNodeTexImage'); tx.image = img
mt_.node_tree.links.new(tx.outputs['Color'], mt_.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
for nm_, pz, front in (('PlateTxt_F', 0.455, True), ('PlateTxt_R', 0.765, False)):
    p = surf_point('yz', 0.0, pz, 1 if front else -1); c_ = B(p) + Vector((0.0145 if front else -0.0145, 0, 0)); bm = bmesh.new(); sgn = 1 if front else -1
    vs = [bm.verts.new(c_ + Vector((0, sgn * yy, zz))) for yy, zz in ((-0.26, -0.055), (0.26, -0.055), (0.26, 0.055), (-0.26, 0.055))]
    f = bm.faces.new(vs); uv = bm.loops.layers.uv.new()
    for l, q in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): l[uv].uv = q
    if f.normal.x * sgn < 0: f.normal_flip()
    obj(nm_, bm, 'PlateText')

# ---------------- interior (seen through the glass)
def box(name, cx, cy, cz, sx, sy, sz, mname, rot=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts[:])
    if rot: bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rot, 3, 'Y'), verts=bm.verts[:])
    bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=bm.verts[:]); return obj(name, bm, mname)
X = lambda s: 2.125 - s
box('Floor', X(2.45), 0, 0.33, 2.9, 1.62, 0.02, 'Interior')
for sd in (1, -1):
    box('DoorCard', X(2.35), sd * 0.80, 0.68, 2.3, 0.02, 0.66, 'Interior')
    box('Seat_Cushion', X(2.32), sd * 0.38, 0.52, 0.52, 0.50, 0.12, 'Interior')
    box('Seat_Back', X(2.62), sd * 0.38, 0.86, 0.12, 0.48, 0.62, 'Interior', rot=math.radians(-14))
    box('Headrest', X(2.70), sd * 0.38, 1.24, 0.09, 0.26, 0.17, 'Interior', rot=math.radians(-14))
box('Rear_Bench', X(3.22), 0, 0.52, 0.50, 1.42, 0.12, 'Interior'); box('Rear_Back', X(3.48), 0, 0.84, 0.12, 1.42, 0.56, 'Interior', rot=math.radians(-16))
box('Parcel_Shelf', X(3.85), 0, 1.03, 0.55, 1.5, 0.02, 'Interior')
box('Dash', X(1.60), 0, 0.88, 0.40, 1.56, 0.24, 'Interior', rot=math.radians(8)); box('Dash_Top', X(1.50), 0, 1.01, 0.26, 1.46, 0.04, 'Interior', rot=math.radians(-12))
box('Screen', X(1.62), 0.0, 1.07, 0.02, 0.26, 0.15, 'GlassBlack', rot=math.radians(-20))
box('Headliner', X(2.6), 0, 1.375, 1.6, 1.0, 0.012, 'Headliner')
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=False, segments=20, radius=0.18)
r2 = bmesh.ops.extrude_edge_only(bm, edges=bm.edges[:]); nv = [e for e in r2['geom'] if isinstance(e, bmesh.types.BMVert)]; bmesh.ops.scale(bm, vec=(0.82, 0.82, 1), verts=nv)
bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90 - 24), 3, 'Y'), verts=bm.verts[:]); bmesh.ops.translate(bm, vec=(X(1.88), 0.38, 0.97), verts=bm.verts[:]); obj('Steering', bm, 'Interior')

# ---------------- join: body + parts make LOD0; a decimated copy makes LOD1
for o in bpy.context.scene.objects: o.select_set(False)
parts = [o for o in PARTS if o.name in bpy.context.scene.objects]
bpy.context.view_layer.objects.active = parts[0]
for o in parts: o.select_set(True)
bpy.ops.object.join(); P0 = bpy.context.view_layer.objects.active; P0.name = 'Mira_Parts'
for p in P0.data.polygons: p.use_smooth = True
P0.data.set_sharp_from_angle(angle=math.radians(40)) if hasattr(P0.data, 'set_sharp_from_angle') else None
lod0 = bpy.data.objects.new('LOD0', None); bpy.context.scene.collection.objects.link(lod0); body.parent = lod0; P0.parent = lod0; body.name = 'Mira_Body'
# far copy: the body surface again at low resolution, zones by face, plus plain wheels
from skimage.measure import marching_cubes
Dc = D[::3, ::3, ::3]; Vf, Ff, _, _ = marching_cubes(Dc, 0.0, spacing=(M.H * 3,) * 3); Vf = Vf + o3
fn_ = np.cross(Vf[Ff[:, 1]] - Vf[Ff[:, 0]], Vf[Ff[:, 2]] - Vf[Ff[:, 0]])
if (np.einsum('ij,ij->i', fn_, nrm(Vf[Ff].mean(1))) < 0).mean() > 0.5: Ff = Ff[:, ::-1]
mf = bpy.data.meshes.new('far'); mf.from_pydata(np.c_[2.125 - Vf[:, 0], Vf[:, 1], Vf[:, 2]].tolist(), [], Ff[:, ::-1].tolist()); mf.update()
far = bpy.data.objects.new('Mira_Far', mf); bpy.context.scene.collection.objects.link(far)
for o in bpy.context.scene.objects: o.select_set(False)
bpy.context.view_layer.objects.active = far; dm = far.modifiers.new('d', 'DECIMATE'); dm.ratio = float(os.environ.get('FAR', '0.12')); dm.use_collapse_triangulate = True; bpy.ops.object.modifier_apply(modifier='d')
Pf = np.array([[2.125 - v.co.x, v.co.y, v.co.z] for v in mf.vertices])
for it in range(3): Pf = Pf - nrm(Pf) * dval(Pf)[:, None]
import meshcut as MCUT
Ffar = np.array([[*p.vertices] for p in mf.polygons]); Ffar = Ffar[:, ::-1]                       # sheet-space winding
for n_, fnc, _ in Zn.zone_fns():
    if n_ in ('Clad', 'Glass', 'GlassBlack', 'Lamp', 'Tail', 'TailBand', 'Grille', 'Liner', 'Intake'): Pf, Ffar = MCUT.cut(Pf, Ffar, fnc(Pf[:, 0], Pf[:, 1], Pf[:, 2]))
far.data = mf2 = bpy.data.meshes.new('far2'); mf2.from_pydata(np.c_[2.125 - Pf[:, 0], Pf[:, 1], Pf[:, 2]].tolist(), [], Ffar[:, ::-1].tolist()); mf2.update(); mf = mf2
names = ['Paint'] + [n for n, _, _ in Zn.zone_fns()]
for n in names: mf.materials.append(bpy.data.materials.get(n) or bpy.data.materials['GlassBlack'])
C = np.array([[2.125 - p.center.x, p.center.y, p.center.z] for p in mf.polygons]); zi = np.zeros(len(C), int)
for k, (n, fnc, _) in enumerate(Zn.zone_fns()):
    if n not in ('LED', 'TailLED', 'Reverse', 'Reflector'): zi[fnc(C[:, 0], C[:, 1], C[:, 2]) < 0] = k + 1
zi[(nrm(C)[:, 2] < -0.75) & (zi == 0)] = names.index('Liner')
mf.polygons.foreach_set('material_index', zi.astype(np.int32))
for p in mf.polygons: p.use_smooth = True
bm = bmesh.new()
for x in (FX, RX):
    for sd in (1, -1):
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=R, radius2=R, depth=0.2)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'), verts=r['verts']); bmesh.ops.translate(bm, vec=(x, sd * TRK, R), verts=r['verts'])
wo = obj('far_wheels', bm, 'Tyre'); PARTS.remove(wo)
for o in bpy.context.scene.objects: o.select_set(False)
far.select_set(True); wo.select_set(True); bpy.context.view_layer.objects.active = far; bpy.ops.object.join()
lod1 = bpy.data.objects.new('LOD1', None); bpy.context.scene.collection.objects.link(lod1); far.parent = lod1
tris = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
print('TRIS body', tris(body), 'parts', tris(P0), 'far', tris(far))
bpy.ops.wm.save_as_mainfile(filepath=OUT + '.blend')
for o in bpy.context.scene.objects: o.select_set(o.name in ('LOD0', 'LOD1', 'Mira_Body', 'Mira_Parts', 'Mira_Far'))
bpy.ops.export_scene.gltf(filepath=OUT + '.glb', export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
print('EXPORTED')

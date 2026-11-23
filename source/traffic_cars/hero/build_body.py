"""Mira body: field -> marching cubes -> zone cuts -> decimate -> recesses -> analytic normals. Saves /tmp/mira_body.blend"""
import sys, numpy as np, time, bpy, bmesh
sys.path.insert(0, '/home/claude/traffic'); import importlib, os; CAR = os.environ.get('CAR', 'mira'); M = importlib.import_module(CAR + '_sdf'); Zn = importlib.import_module(CAR + '_zones'); import meshcut as MC
C0 = getattr(M, 'C0', M.L / 2)
from skimage.measure import marching_cubes
from scipy import ndimage
T0 = time.time(); RATIO = float(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else 0.06
D, s, y, z = M.field(); o3 = np.array([s[0], y[0], z[0]])
V, F, _, _ = marching_cubes(D, 0.0, spacing=(M.H,) * 3); V = V + o3; F = F[:, ::-1].copy()
Ds = ndimage.gaussian_filter(D, 1.3); G = np.gradient(Ds, M.H)
def nrm(P):
    idx = ((P - o3) / M.H).T; N = np.stack([ndimage.map_coordinates(g, idx, order=1, mode='nearest') for g in G], 1); return N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-9)
# check winding against the field
fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); cn = nrm(V[F].mean(1))
if (np.einsum('ij,ij->i', fn, cn) < 0).mean() > 0.5: F = F[:, ::-1].copy()
print('mc', len(F), round(time.time() - T0, 1))
# first pass: adaptive decimation of the plain surface, then back onto the field, so zone borders are cut at ~2 cm spacing
bpy.ops.wm.read_factory_settings(use_empty=True)
m0 = bpy.data.meshes.new('pre'); m0.from_pydata(V.tolist(), [], F.tolist()); m0.update(); o0 = bpy.data.objects.new('pre', m0); bpy.context.scene.collection.objects.link(o0)
bpy.context.view_layer.objects.active = o0; d0 = o0.modifiers.new('d', 'DECIMATE'); d0.ratio = float(__import__('os').environ.get('PRE', '0.25')); d0.use_collapse_triangulate = True; bpy.ops.object.modifier_apply(modifier='d')
V = np.array([v.co for v in m0.vertices]); F = np.array([[*p.vertices] for p in m0.polygons])
for it in range(3):
    d = ndimage.map_coordinates(D, ((V - o3) / M.H).T, order=1, mode='nearest'); V = V - nrm(V) * d[:, None]
print('pre', len(F))
ZONES = Zn.zone_fns()
for name, fnc, _ in ZONES:
    if name == 'Gap':                                              # gaps are thin strips: cut both edges
        g = fnc(V[:, 0], V[:, 1], V[:, 2]); V, F = MC.cut(V, F, g)
    else:
        V, F = MC.cut(V, F, fnc(V[:, 0], V[:, 1], V[:, 2]))
print('cut', len(F), round(time.time() - T0, 1))
C = V[F].mean(1); zid = np.zeros(len(F), int)
NAMES = ['Paint'] + [n for n, _, _ in ZONES]
for k, (name, fnc, _) in enumerate(ZONES): zid[fnc(C[:, 0], C[:, 1], C[:, 2]) < 0] = k + 1
under = cn_ = nrm(C); zid[(cn_[:, 2] < -0.75) & (zid == 0)] = NAMES.index('Liner')     # underside
# boundary vertices (between zones) are protected from decimation
E = np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]; Ez = np.r_[zid, zid, zid]; Es = np.sort(E, 1)
order = np.lexsort((Es[:, 1], Es[:, 0])); Es, Ez = Es[order], Ez[order]
same = (Es[1:] == Es[:-1]).all(1) & (Ez[1:] != Ez[:-1]); bverts = np.unique(np.r_[Es[1:][same].ravel()])
print('boundary verts', len(bverts))
bpy.ops.wm.read_factory_settings(use_empty=True)
P = np.c_[C0 - V[:, 0], V[:, 1], V[:, 2]]; Fb = F[:, ::-1]                     # s -> x flips handedness: reverse winding
me = bpy.data.meshes.new('Body'); me.from_pydata(P.tolist(), [], Fb.tolist()); me.update()
for n in NAMES:
    m = bpy.data.materials.get(n) or bpy.data.materials.new(n); me.materials.append(m)
me.polygons.foreach_set('material_index', zid.astype(np.int32)); me.update()
ob = bpy.data.objects.new('Body', me); bpy.context.scene.collection.objects.link(ob)
_, lat = np.unique(np.floor(P / float(__import__('os').environ.get('LAT', '0.15'))).astype(np.int64), axis=0, return_index=True)   # one anchor per lattice cell: caps triangle size so gentle crowns don't collapse into tents
bverts = np.unique(np.r_[bverts, lat]); print('lattice anchors', len(lat))
vg = ob.vertex_groups.new(name='keep'); vg.add(bverts.tolist(), 1.0, 'REPLACE')
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
dm = ob.modifiers.new('dec', 'DECIMATE'); dm.ratio = RATIO; dm.vertex_group = 'keep'; dm.vertex_group_factor = float(__import__('os').environ.get('VGF', '1')); dm.use_collapse_triangulate = True; dm.invert_vertex_group = True
bpy.ops.object.modifier_apply(modifier='dec')
print('decimated', len(me.polygons), round(time.time() - T0, 1))
for it in range(3):                                                   # pull every vertex back onto the true surface
    Pv = np.array([v.co for v in me.vertices]); Ps = np.c_[C0 - Pv[:, 0], Pv[:, 1], Pv[:, 2]]
    idx = ((Ps - o3) / M.H).T; d = ndimage.map_coordinates(D, idx, order=1, mode='nearest'); Nn = nrm(Ps)
    Ps = Ps - Nn * d[:, None]; Pv = np.c_[C0 - Ps[:, 0], Ps[:, 1], Ps[:, 2]]
    me.vertices.foreach_set('co', Pv.ravel().astype(np.float32))
me.update()
if os.environ.get('RECUT', '0') == '1':                              # decimation can drag faces across zone borders: cut the final mesh again, exactly
    Pv = np.array([v.co for v in me.vertices]); V2 = np.c_[C0 - Pv[:, 0], Pv[:, 1], Pv[:, 2]]; F2 = np.array([p_.vertices[:] for p_ in me.polygons])[:, ::-1]
    for name, fnc, _ in ZONES: V2, F2 = MC.cut(V2, F2, fnc(V2[:, 0], V2[:, 1], V2[:, 2]))
    C2 = V2[F2].mean(1); z2 = np.zeros(len(F2), int)
    for k, (name, fnc, _) in enumerate(ZONES): z2[fnc(C2[:, 0], C2[:, 1], C2[:, 2]) < 0] = k + 1
    z2[(nrm(C2)[:, 2] < -0.75) & (z2 == 0)] = NAMES.index('Liner')
    mats = list(me.materials); me2 = bpy.data.meshes.new('Body2'); me2.from_pydata(np.c_[C0 - V2[:, 0], V2[:, 1], V2[:, 2]].tolist(), [], F2[:, ::-1].tolist()); me2.update()
    for m in mats: me2.materials.append(m)
    me2.polygons.foreach_set('material_index', z2.astype(np.int32)); me2.update(); ob.data = me2; bpy.data.meshes.remove(me); me = me2
    print('recut', len(me.polygons))
# recesses: extrude each zone group inward, walls get the group's wall material
GROUPS = getattr(Zn, 'GROUPS', None) or [(('Lamp', 'LED'), 0.006, 'Lamp'), (('Tail', 'TailBand', 'TailLED', 'Reverse'), 0.006, 'TailBand'), (('Grille',), 0.03, 'Grille'),
          (('Intake',), 0.018, 'Intake')]
for extra in ('Seal',):
    if extra not in NAMES: NAMES.append(extra); me.materials.append(bpy.data.materials.new(extra))
bm = bmesh.new(); bm.from_mesh(me); walls = set()
def sheet(co): return np.array([C0 - co.x, co.y, co.z])
for zs, depth, wall in GROUPS:
    ids = {NAMES.index(n) for n in zs}; faces = [f for f in bm.faces if f.material_index in ids]
    if not faces: continue
    nf0 = len(bm.faces); r = bmesh.ops.extrude_face_region(bm, geom=faces, use_keep_orig=False); print('walls', zs, len(faces), len(bm.faces) - nf0)
    nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
    Pn = np.array([sheet(v.co) for v in nv]); Nn = nrm(Pn)
    for v, n in zip(nv, Nn): v.co.x += n[0] * depth; v.co.y -= n[1] * depth; v.co.z -= n[2] * depth       # inward (x is mirrored)
    newf = set(f for f in r['geom'] if isinstance(f, bmesh.types.BMFace))
    wi = NAMES.index(wall)
    for v in nv:
        for f in v.link_faces:
            if f not in newf and f.material_index not in ids: pass
    for f in bm.faces:
        if f in newf: continue
    # walls are the faces touching both old and new verts that are not part of the moved region
    nvs = set(nv)
    for f in bm.faces:
        if not all(v in nvs for v in f.verts) and any(v in nvs for v in f.verts): f.material_index = wi; walls.add(f.index)
bm.normal_update(); bm.to_mesh(me); bm.free()
# analytic normals per corner; walls keep their flat normal
Pv = np.array([sheet(v.co) for v in me.vertices]); Nv = nrm(Pv); Nv = np.c_[-Nv[:, 0], Nv[:, 1], Nv[:, 2]]
wall_ids = {NAMES.index(w) for _, _, w in GROUPS}
ln = []
for p in me.polygons:
    for li in p.loop_indices:
        vi = me.loops[li].vertex_index; n = Nv[vi]
        if p.index in walls or np.dot(n, p.normal) < 0.2: n = np.array(p.normal)
        ln.append(n.tolist())
for p in me.polygons: p.use_smooth = True
me.normals_split_custom_set(ln)
print('final', len(me.polygons), round(time.time() - T0, 1))
bpy.ops.wm.save_as_mainfile(filepath=__import__('os').environ.get('OUT', '/tmp/%s_body.blend' % CAR))

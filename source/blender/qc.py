"""Quality check of the built map: python3 qc.py -- out"""
import bpy, sys, os, json
import numpy as np
from scipy.spatial import cKDTree
OUT = sys.argv[sys.argv.index('--') + 1]; R = []
def say(*a): s = 'QC ' + ' '.join(str(x) for x in a); print(s); R.append(s)
W = json.load(open(f'{OUT}/world.json')); hm = W['heightmap']; H = np.fromfile(f'{OUT}/height.bin', '<i2').reshape(hm['ny'], hm['nx']) * hm['scale']
def h(x, z):
    fx = np.clip((x - hm['x0']) / hm['cell'], 0, hm['nx'] - 1.001); fy = np.clip((-z - hm['y0']) / hm['cell'], 0, hm['ny'] - 1.001); ix = fx.astype(int); iy = fy.astype(int); u = fx - ix; v = fy - iy
    return (H[iy, ix] * (1 - u) + H[iy, ix + 1] * u) * (1 - v) + (H[iy + 1, ix] * (1 - u) + H[iy + 1, ix + 1] * u) * v
worst = 9; pts = []; hws = []
for r in W['roads']:
    P = np.array(r['pts']).reshape(-1, 3); wall = np.array(r['wall'], bool); T = np.gradient(P[:, [0, 2]], axis=0); T /= np.linalg.norm(T, axis=1)[:, None]; Nn = np.c_[-T[:, 1], T[:, 0]]
    for o in np.linspace(-r['w'] / 2, r['w'] / 2, 5):
        q = P[:, [0, 2]] + Nn * o; c = (P[:, 1] - h(q[:, 0], q[:, 1]))[~wall]
        if len(c): worst = min(worst, float(c.min()))
    pts.append(P[:, [0, 2]]); hws.append(np.full(len(P), r['w'] / 2))
say('roads', len(W['roads']), 'length km', round(sum(len(r['pts']) / 3 * r['step'] for r in W['roads']) / 1000, 1), 'bridges', len(W['bridges']), 'tunnels', len(W['tunnels']))
say('lowest road clearance above the 6 m terrain (m)', round(worst, 2))
tree = cKDTree(np.vstack(pts)); hw = np.concatenate(hws); F = json.load(open(f'{OUT}/flora.json')); bad = 0; tot = 0; flo = 0; fmax = 0
for sp, a in F['instances'].items():
    A = np.array(a).reshape(-1, 8); tot += len(A); d, i = tree.query(A[:, [0, 2]]); big = not sp.startswith(('grass', 'flowers'))
    bad += int((d < hw[i] + (1.0 if big else 0.2)).sum()); dz = A[:, 1] - h(A[:, 0], A[:, 2]); flo += int((dz > 0.6).sum()); fmax = max(fmax, float(dz.max()))
say('plant instances', tot, 'species', len(F['instances']), '| on a carriageway', bad, '| floating more than 0.6 m', flo, '(max', round(fmax, 2), ')')
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(f'{OUT}/aurelia_island.blend'))
nomat = nouv = 0; tris = 0; n = 0
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name.startswith(('COL_', 'INST_')) or o.name.endswith('_LOD1'): continue
    n += 1; tris += len(o.data.polygons)
    if not o.data.materials: nomat += 1
    elif any(m and m.node_tree and any(x.type == 'TEX_IMAGE' for x in m.node_tree.nodes) for m in o.data.materials) and not o.data.uv_layers: nouv += 1
say('mesh objects', n, 'triangles stored', tris, '| without material', nomat, '| textured without UVs', nouv)
say('images', len(bpy.data.images), 'packed', sum(1 for i in bpy.data.images if i.packed_file), '| scenes', [s.name for s in bpy.data.scenes], '| night lamps', sum(1 for o in bpy.data.objects if o.name.startswith('LAMP_')))
dg = bpy.context.evaluated_depsgraph_get(); inst = sum(1 for i in dg.object_instances if i.is_instance); say('face instances evaluated by Blender', inst)
ob = np.array(W['obstacles']); cen = ob[:, :2]; rad = np.hypot(ob[:, 2], ob[:, 3]); d, i = tree.query(cen); say('solid footprints', len(ob), '| centre on a carriageway', int((d < hw[i]).sum()), '(these are the cars parked along city kerbs, placed on purpose)')
bpy.ops.wm.read_factory_settings(use_empty=True)
for f in ('aurelia_island.fbx', 'aurelia_flora.fbx'):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=f'{OUT}/{f}'); ms = [o for o in bpy.data.objects if o.type == 'MESH']
    say(f, 're-imported: mesh objects', len(ms), 'triangles', sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in ms))
open(f'{OUT}/QC_REPORT.txt', 'w').write('\n'.join(R) + '\n')

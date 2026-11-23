"""Replace the body's vertex normals in the GLB with the exact surface normals of the field (smooth shading on a light mesh)."""
import sys, numpy as np
sys.path.insert(0, '/home/claude/traffic'); import os, importlib; CAR = os.environ.get('CAR', 'mira'); M = importlib.import_module(CAR + '_sdf'); NM = CAR.capitalize(); C0 = getattr(M, 'C0', M.L / 2)
from scipy import ndimage
from pygltflib import GLTF2
src, out = sys.argv[1:3]
D, s_, y_, z_ = M.field(); o3 = np.array([s_[0], y_[0], z_[0]]); G = np.gradient(ndimage.gaussian_filter(D, float(__import__('os').environ.get('NSIG', '1.3'))), M.H)
g = GLTF2().load(src); blob = bytearray(g.binary_blob())
def view(ai, n):
    a = g.accessors[ai]; bv = g.bufferViews[a.bufferView]; off = (bv.byteOffset or 0) + (a.byteOffset or 0); st = bv.byteStride or 4 * n
    return np.ndarray((a.count, n), dtype=np.float32, buffer=blob, offset=off, strides=(st, 4))
SKIP = {'Tyre', 'TyreFar', 'Rim', 'Disc', 'Caliper', 'Interior', 'Headliner', 'MirrorGlass', 'Amber', 'Chrome', 'Plate', 'Graphite'}
tot = 0
for nd in g.nodes:
    if nd.name not in (NM + '_Body', NM + '_Far') or nd.mesh is None: continue
    m = g.meshes[nd.mesh]; m.name = nd.name
    for p in m.primitives:
        mn = g.materials[p.material].name if p.material is not None else ''
        if mn in SKIP: continue
        P = view(p.attributes.POSITION, 3); N = view(p.attributes.NORMAL, 3)
        S = np.c_[C0 - P[:, 0], -P[:, 2], P[:, 1]]; idx = ((S - o3) / M.H).T
        d = ndimage.map_coordinates(D, idx, order=1, mode='nearest'); n = np.stack([ndimage.map_coordinates(q, idx, order=int(os.environ.get('NORD', '3')), mode='nearest') for q in G], 1)
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        ng = np.c_[-n[:, 0], n[:, 2], -n[:, 1]]
        ok = (np.abs(d) < (0.012 if nd.name == NM + '_Body' else 0.006)) & ((ng * N).sum(1) > 0.8)
        N[ok] = ng[ok]; tot += ok.sum()
g.set_binary_blob(bytes(blob)); g.save(out); print('patched', tot)

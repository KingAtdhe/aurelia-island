"""Storefronts of the city (art sheet 10) for the Godot game. The web game drops the 1,542 shop prefabs: a few hundred of
their records sit 1-6 m behind the podium wall of the glass towers (the podium was widened after the shops were placed).
Here each shop is checked with a ray along its facing: when a wall of the map stands 1-6 m in front of it, the shop is moved
out onto that wall. All shops of a 100 m cell are then merged into one mesh per material (LOD1 models), s_<cx>_<cz>.glb,
streamed like the detail chunks (kind 'd', group 'Shops', drawn to 280 m) — instanced, they would cost hundreds of draws.
usage: python3 export_shops.py florakc_raw.glb <repo> <godot>/assets/island"""
import sys, os, json, math, glob, struct, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from glbcut import Src, CS, NC
from pygltflib import GLTF2, Scene, Node, Mesh, Accessor, BufferView, Buffer, Image, Asset, Primitive, Attributes
FK, REPO, OUT = sys.argv[1:4]; CELL = 100.0
# walls of the city the shops can stand against
WT = []
for f in glob.glob(OUT + '/chunks/[bd]_*.glb'):
    b = open(f, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]; gj = json.loads(b[20:20 + L]); B = b[20 + L + 8:]
    def A(i):
        a = gj['accessors'][i]; v = gj['bufferViews'][a['bufferView']]; n = NC[a['type']]
        dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[a['componentType']]
        return np.frombuffer(B, dt, a['count'] * n, v.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, n).astype(np.float64)
    for n in gj['nodes']:
        if 'mesh' not in n or n['name'].split('__')[0] not in ('Structures', 'Houses', 'Glazing', 'Towers'): continue
        sc = np.array(n.get('scale', [1, 1, 1])); tr = np.array(n.get('translation', [0, 0, 0]))
        for p in gj['meshes'][n['mesh']]['primitives']:
            T = (A(p['attributes']['POSITION']) * sc + tr)[A(p['indices'])[:, 0].astype(np.int64).reshape(-1, 3)]
            c = T.mean(1); WT.append(T[(abs(c[:, 0]) < 900) & (abs(c[:, 2]) < 500)])
WT = np.concatenate(WT); WC = WT.mean(1)
def ray(o, d, maxd):
    T = WT[np.hypot(WC[:, 0] - o[0], WC[:, 2] - o[2]) < maxd + 60]
    e1 = T[:, 1] - T[:, 0]; e2 = T[:, 2] - T[:, 0]; pv = np.cross(d, e2); det = (e1 * pv).sum(1); ok = abs(det) > 1e-9
    inv = np.where(ok, 1 / np.where(ok, det, 1), 0); tv = o - T[:, 0]; u = (tv * pv).sum(1) * inv; q = np.cross(tv, e1)
    v = (d * q).sum(1) * inv; t = (e2 * q).sum(1) * inv; hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0.02) & (t < maxd)
    return t[hit].min() if hit.any() else None
s = Src(FK, OUT + '/tex', 'k'); g = s.g; blob = s.blob
def arr(ai):
    a = g.accessors[ai]; v = g.bufferViews[a.bufferView]; es = CS[a.componentType] * NC[a.type]; st = v.byteStride or es
    raw = np.frombuffer(blob, np.uint8, count=(a.count - 1) * st + es, offset=(v.byteOffset or 0) + (a.byteOffset or 0))
    x = np.lib.stride_tricks.as_strided(raw, (a.count, es), (st, 1)).copy()
    x = x.view({5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]).reshape(a.count, NC[a.type]).astype(np.float64)
    if a.normalized: x /= {5121: 255.0, 5123: 65535.0}[a.componentType]
    return x
names = {n.name: i for i, n in enumerate(g.nodes) if n.name}
def species(sp):
    out = {}
    def walk(ni, M):
        n = g.nodes[ni]; m = s.world(ni, M)
        if n.mesh is not None:
            for p in g.meshes[n.mesh].primitives:
                P = arr(p.attributes.POSITION); P = P @ m[:3, :3].T + m[:3, 3]; I = arr(p.indices)[:, 0].astype(np.int64)
                if p.attributes.NORMAL is not None: Nn = arr(p.attributes.NORMAL) @ np.linalg.inv(m[:3, :3])
                else:
                    T = I.reshape(-1, 3); fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); Nn = np.zeros_like(P)
                    for k in range(3): np.add.at(Nn, T[:, k], fn)
                Nn /= np.linalg.norm(Nn, axis=1, keepdims=True) + 1e-9
                UV = arr(p.attributes.TEXCOORD_0) if p.attributes.TEXCOORD_0 is not None else np.zeros((len(P), 2))
                C = arr(p.attributes.COLOR_0)[:, :3] if p.attributes.COLOR_0 is not None else np.ones((len(P), 3))
                out.setdefault(p.material, []).append((P, Nn, UV, C, I))
        for c in n.children or []: walk(c, m)
    walk(names['FLORA_%s_LOD1' % sp], np.eye(4))
    return out
inst = json.load(open(REPO + '/data/flora.json'))['instances']
cells = {}; moved = 0; n_all = 0
for sp, a in inst.items():
    if not sp.startswith('prop_shop_'): continue
    geo = species(sp); a = np.array(a, np.float64).reshape(-1, 8)
    for x, y, z, sc, yaw, r, gg, b in a:
        if sc <= 0: continue
        n_all += 1; c, si = math.cos(yaw), math.sin(yaw); nf = np.array([c, 0.0, -si])          # the way the shop faces
        h = ray(np.array([x, y + 2.0, z]), nf, 6.0)
        if h is not None and h > 1.0: x += nf[0] * (h + 0.06); z += nf[2] * (h + 0.06); moved += 1
        R = np.array([[c, 0, si], [0, 1, 0], [-si, 0, c]]) * sc                         # Basis(UP, yaw).scaled(sc), as flora.gd does
        cell = (int(math.floor(x / CELL)), int(math.floor(z / CELL)))
        for mat, parts in geo.items():
            for P, Nn, UV, C, I in parts:
                cells.setdefault(cell, {}).setdefault(mat, []).append((P @ R.T + [x, y, z], Nn @ (R / sc).T, UV, C * [r, gg, b], I))
idx = json.load(open(OUT + '/index.json'))
for k in [k for k in idx['chunks'] if k.startswith('s_')]: del idx['chunks'][k]
for f in glob.glob(OUT + '/chunks/s_*'): os.remove(f)
tot = 0
for cell, mats in sorted(cells.items()):
    out = GLTF2(); out.asset = Asset(version='2.0', generator='aurelia export_shops')
    out.samplers = g.samplers; out.textures = g.textures; out.materials = g.materials
    out.images = [Image(name=im.name, uri='../tex/' + s.imgs[i], mimeType=im.mimeType) for i, im in enumerate(g.images)]
    data = bytearray(); prims = []; lo = np.full(3, 1e9); hi = -lo; tris = 0
    org = np.array([(cell[0] + 0.5) * CELL, 14.0, (cell[1] + 0.5) * CELL])      # node at the cell centre
    def put(x, ct, typ, target, mn=False):
        while len(data) % 4: data.append(0)
        off = len(data); data.extend(x.tobytes())
        out.bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=x.nbytes, target=target))
        out.accessors.append(Accessor(bufferView=len(out.bufferViews) - 1, componentType=ct, count=len(x), type=typ, min=x.min(0).tolist() if mn else None, max=x.max(0).tolist() if mn else None))
        return len(out.accessors) - 1
    for mat, parts in sorted(mats.items()):
        P = []; Nn = []; UV = []; C = []; I = []; base = 0
        for p, n_, uv, c, i in parts: P.append(p); Nn.append(n_); UV.append(uv); C.append(c); I.append(i + base); base += len(p)
        P = (np.concatenate(P) - org).astype(np.float32); I = np.concatenate(I)
        lo = np.minimum(lo, P.min(0) + org); hi = np.maximum(hi, P.max(0) + org); tris += len(I) // 3
        q = Primitive(material=mat, attributes=Attributes())
        q.attributes.POSITION = put(P, 5126, 'VEC3', 34962, True)
        q.attributes.NORMAL = put(np.concatenate(Nn).astype(np.float32), 5126, 'VEC3', 34962)
        q.attributes.TEXCOORD_0 = put(np.concatenate(UV).astype(np.float32), 5126, 'VEC2', 34962)
        q.attributes.COLOR_0 = put(np.c_[np.concatenate(C), np.ones(len(P))].astype(np.float32), 5126, 'VEC4', 34962)
        big = base > 65535; q.indices = put(I.astype(np.uint32 if big else np.uint16), 5125 if big else 5123, 'SCALAR', 34963)
        prims.append(q)
    out.meshes = [Mesh(name='Shops', primitives=prims)]; name = 's_%d_%d' % cell
    out.nodes = [Node(name='Shops__%d_%d' % cell, mesh=0, translation=org.tolist())]; out.scenes = [Scene(nodes=[0])]; out.scene = 0
    out.buffers = [Buffer(byteLength=len(data))]; out.set_binary_blob(bytes(data)); out.save_binary('%s/chunks/%s.glb' % (OUT, name))
    idx['chunks'][name] = {'kind': 'd', 'cell': list(cell), 'min': lo.round(1).tolist(), 'max': hi.round(1).tolist(), 'tris': tris, 'bytes': len(data), 'groups': {'Shops': tris}}
    tot += tris
json.dump(idx, open(OUT + '/index.json', 'w'), indent=0)
print('shops: %d placed, %d moved out onto the podium wall; %d cells, %d tris' % (n_all, moved, len(cells), tot))

# The close-up city buildings (BuildingsHDModel) come one node per building with ~10 materials each: ~450 draw calls in a
# city street on their own. Run after export_chunks.py (and fix_podium.py): in every detail chunk the buildings of each
# 200 m quarter are merged into one node with one primitive per material (transforms baked in), which cuts them to ~25
# draws per quarter. The node sits at the quarter centre, so the group's visibility range (island.gd RANGE) still works.
import glob, os, numpy as np
from pygltflib import GLTF2, Node, Mesh, Accessor, BufferView, Primitive, Attributes
REPO = os.path.abspath(os.path.dirname(__file__) + '/../..'); Q = 200.0
DT = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}; NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
def mat4(n):
    if n.matrix: return np.array(n.matrix).reshape(4, 4).T
    t = np.array(n.translation or [0, 0, 0]); s = np.array(n.scale or [1, 1, 1]); x, y, z, w = n.rotation or [0, 0, 0, 1]
    r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    m = np.eye(4); m[:3, :3] = r * s; m[:3, 3] = t; return m
tot_before = tot_after = 0
for f in sorted(glob.glob(REPO + '/godot/assets/island/chunks/d_*.glb')):
    g = GLTF2().load(f); blob = g.binary_blob()
    def acc(i):
        a = g.accessors[i]; v = g.bufferViews[a.bufferView]; n = NC[a.type]; es = DT[a.componentType]().itemsize * n; st = v.byteStride or es
        raw = np.frombuffer(blob, np.uint8, count=(a.count - 1) * st + es, offset=(v.byteOffset or 0) + (a.byteOffset or 0))
        x = np.lib.stride_tricks.as_strided(raw, (a.count, es), (st, 1)).copy().view(DT[a.componentType]).reshape(a.count, n).astype(np.float64)
        if a.normalized: x /= {5121: 255.0, 5123: 65535.0}[a.componentType]
        return x
    roots = g.scenes[g.scene or 0].nodes
    hd = [r for r in roots if (g.nodes[r].name or '').startswith('BuildingsHDModel') and g.nodes[r].mesh is not None and not g.nodes[r].children]
    if not hd: continue
    groups = {}          # (qx, qz) -> material -> list of (P, N, UV, C, I)
    for r in hd:
        n = g.nodes[r]; m = mat4(n); nm3 = np.linalg.inv(m[:3, :3]).T
        for p in g.meshes[n.mesh].primitives:
            P = acc(p.attributes.POSITION) @ m[:3, :3].T + m[:3, 3]; I = acc(p.indices)[:, 0].astype(np.int64)
            if p.attributes.NORMAL is not None: N = acc(p.attributes.NORMAL) @ nm3.T
            else:
                T = I.reshape(-1, 3); fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); N = np.zeros_like(P)
                for k in range(3): np.add.at(N, T[:, k], fn)
            N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-9
            UV = acc(p.attributes.TEXCOORD_0) if p.attributes.TEXCOORD_0 is not None else np.zeros((len(P), 2))
            C = acc(p.attributes.COLOR_0) if p.attributes.COLOR_0 is not None else np.ones((len(P), 4))
            if C.shape[1] == 3: C = np.c_[C, np.ones(len(C))]
            c = P.mean(0); q = (int(np.floor(c[0] / Q)), int(np.floor(c[2] / Q)))
            groups.setdefault(q, {}).setdefault(p.material, []).append((P, N, UV, C, I))
            tot_before += 1
    # new file: every other root node kept as it is, the buildings replaced by one node per quarter; buffer rebuilt tight
    data = bytearray(); new_acc = []; new_bv = []; amap = {}
    def put(x, ct, typ, target, mn=False):
        while len(data) % 4: data.append(0)
        off = len(data); data.extend(x.tobytes()); new_bv.append(BufferView(buffer=0, byteOffset=off, byteLength=x.nbytes, target=target))
        new_acc.append(Accessor(bufferView=len(new_bv) - 1, componentType=ct, count=len(x), type=typ, min=x.min(0).tolist() if mn else None, max=x.max(0).tolist() if mn else None))
        return len(new_acc) - 1
    def copy_acc(i, target):
        if i is None: return None
        if i in amap: return amap[i]
        a = g.accessors[i]; x = acc(i)
        if a.normalized: x = (x * {5121: 255.0, 5123: 65535.0}[a.componentType]).round()
        x = x.astype(DT[a.componentType]); amap[i] = put(x, a.componentType, a.type, target, a.min is not None)
        new_acc[amap[i]].normalized = a.normalized; return amap[i]
    meshes = []; nodes = []; mmap = {}
    def copy_node(ni):
        n = g.nodes[ni]; me = None
        if n.mesh is not None:
            if n.mesh not in mmap:
                ps = []
                for p in g.meshes[n.mesh].primitives:
                    q = Primitive(mode=p.mode, material=p.material, indices=copy_acc(p.indices, 34963), attributes=Attributes())
                    for at in ('POSITION', 'NORMAL', 'TANGENT', 'TEXCOORD_0', 'TEXCOORD_1', 'COLOR_0'): setattr(q.attributes, at, copy_acc(getattr(p.attributes, at), 34962))
                    ps.append(q)
                meshes.append(Mesh(name=g.meshes[n.mesh].name, primitives=ps)); mmap[n.mesh] = len(meshes) - 1
            me = mmap[n.mesh]
        o = Node(name=n.name, mesh=me, translation=n.translation, rotation=n.rotation, scale=n.scale, matrix=n.matrix)
        nodes.append(o); k = len(nodes) - 1; o.children = [copy_node(c) for c in (n.children or [])] or None; return k
    keep = [copy_node(r) for r in roots if r not in hd]
    tag = os.path.basename(f)[2:-4]
    for q, mats in sorted(groups.items()):
        org = np.array([(q[0] + 0.5) * Q, 14.0, (q[1] + 0.5) * Q]); ps = []
        for mt, parts in sorted(mats.items(), key=lambda kv: -1 if kv[0] is None else kv[0]):
            P = []; N = []; UV = []; C = []; I = []; base = 0
            for p_, n_, uv, c, i in parts: P.append(p_); N.append(n_); UV.append(uv); C.append(c); I.append(i + base); base += len(p_)
            pr = Primitive(material=mt, attributes=Attributes())
            pr.attributes.POSITION = put((np.concatenate(P) - org).astype(np.float32), 5126, 'VEC3', 34962, True)
            pr.attributes.NORMAL = put(np.concatenate(N).astype(np.float32), 5126, 'VEC3', 34962)
            pr.attributes.TEXCOORD_0 = put(np.concatenate(UV).astype(np.float32), 5126, 'VEC2', 34962)
            pr.attributes.COLOR_0 = put(np.concatenate(C).astype(np.float32), 5126, 'VEC4', 34962)
            big = base > 65535; pr.indices = put(np.concatenate(I).astype(np.uint32 if big else np.uint16), 5125 if big else 5123, 'SCALAR', 34963)
            ps.append(pr); tot_after += 1
        meshes.append(Mesh(name='HD_%s_%d_%d' % (tag, q[0], q[1]), primitives=ps))
        nodes.append(Node(name='BuildingsHDModel__m%s_%d_%d' % (tag, q[0], q[1]), mesh=len(meshes) - 1, translation=org.tolist())); keep.append(len(nodes) - 1)
    g.nodes = nodes; g.meshes = meshes; g.accessors = new_acc; g.bufferViews = new_bv; g.scenes[g.scene or 0].nodes = keep
    g.buffers[0].byteLength = len(data); g.set_binary_blob(bytes(data)); g.save_binary(f)
    print(os.path.basename(f), len(hd), 'buildings ->', len(groups), 'quarters')
print('HD buildings: %d primitives -> %d' % (tot_before, tot_after))

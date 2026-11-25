# The ground floors of the city towers and blocks are closed with big near-black panels in the source map ("Structures",
# PaintedSurface): meant as dark shop glazing, they read as blank grey slabs in the game. Run after export_chunks.py: in the
# detail chunks of the city those panels (near-black, upright, larger than 1.5 m2, taller than 2.5 m) move to their own
# primitive with the WindowGlass material, which the game draws as glass with lit rooms behind it (shaders/interior.gdshader).
import glob, os, numpy as np
from pygltflib import GLTF2, Accessor, BufferView, Primitive, Attributes, Material, PbrMetallicRoughness
REPO = os.path.abspath(os.path.dirname(__file__) + '/../..'); CITY = (-800.0, 700.0, -400.0, 400.0)
DT = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}; NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
moved = 0
for f in sorted(glob.glob(REPO + '/godot/assets/island/chunks/d_*.glb')):
    g = GLTF2().load(f); blob = bytearray(g.binary_blob()); hit = False
    def acc(i):
        a = g.accessors[i]; v = g.bufferViews[a.bufferView]; n = NC[a.type]
        x = np.frombuffer(bytes(blob), DT[a.componentType], a.count * n, (v.byteOffset or 0) + (a.byteOffset or 0)).reshape(-1, n).astype(np.float64)
        if a.normalized: x /= {5121: 255.0, 5123: 65535.0}[a.componentType]
        return x
    def put(x, ct):
        while len(blob) % 4: blob.append(0)
        off = len(blob); blob.extend(x.tobytes())
        g.bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=x.nbytes, target=34963))
        g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=ct, count=len(x), type='SCALAR')); return len(g.accessors) - 1
    glass = None
    for n in g.nodes:
        if not (n.name or '').startswith('Structures__') or n.mesh is None: continue
        s = np.array(n.scale or [1, 1, 1]); t = np.array(n.translation or [0, 0, 0])
        mesh = g.meshes[n.mesh]; add = []
        for p in mesh.primitives:
            if p.attributes.COLOR_0 is None or p.indices is None: continue
            P = acc(p.attributes.POSITION) * s + t; C = acc(p.attributes.COLOR_0); I = acc(p.indices)[:, 0].astype(np.int64).reshape(-1, 3)
            T = P[I]; cr = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); ar = np.linalg.norm(cr, axis=1) / 2; nr = cr / (2 * ar[:, None] + 1e-9)
            cen = T.mean(1); lum = C[I[:, 0], :3].mean(1); h = T[:, :, 1].max(1) - T[:, :, 1].min(1)
            sel = (lum < 0.025) & (abs(nr[:, 1]) < 0.2) & (ar > 1.5) & (h > 2.5) & (cen[:, 0] > CITY[0]) & (cen[:, 0] < CITY[1]) & (cen[:, 2] > CITY[2]) & (cen[:, 2] < CITY[3])
            if not sel.any(): continue
            ct = g.accessors[p.indices].componentType; dt = DT[ct]
            p.indices = put(I[~sel].reshape(-1).astype(dt), ct)
            if glass is None:
                g.materials.append(Material(name='WindowGlass', pbrMetallicRoughness=PbrMetallicRoughness(baseColorFactor=[0.02, 0.025, 0.03, 1.0], metallicFactor=0.0, roughnessFactor=0.06)))
                glass = len(g.materials) - 1
            q = Primitive(mode=p.mode, material=glass, indices=put(I[sel].reshape(-1).astype(dt), ct), attributes=Attributes(**{k: v for k, v in p.attributes.__dict__.items()}))
            add.append(q); moved += int(sel.sum()); hit = True
        mesh.primitives += add
    if hit:
        g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save_binary(f); print(os.path.basename(f))
print('podium glazing: %d triangles' % moved)

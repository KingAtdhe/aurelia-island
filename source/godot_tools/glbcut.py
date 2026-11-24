"""Small glTF cutter for the Godot port: copies chosen node trees of a plain (unpacked) GLB into a new GLB, with each accessor
packed tight (no shared views dragged along) and images written once to a shared texture folder the new files point at."""
import os, json, hashlib, numpy as np
from pygltflib import GLTF2, Scene, Node, Mesh, Accessor, BufferView, Buffer, Image, Asset, Primitive, Attributes
CS = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}; NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
ATTS = ('POSITION', 'NORMAL', 'TANGENT', 'TEXCOORD_0', 'TEXCOORD_1', 'COLOR_0')

class Src:
    def __init__(self, path, texdir, tag, images=True):
        self.g = GLTF2().load(path); self.blob = self.g.binary_blob(); self.texdir = texdir; self.imgs = []
        if not images: return
        os.makedirs(texdir, exist_ok=True)
        man_p = os.path.join(texdir, '_src.json')            # md5 of each original picture -> its file (files may be shrunk later)
        man = json.load(open(man_p)) if os.path.exists(man_p) else {}
        for im in self.g.images:
            bv = self.g.bufferViews[im.bufferView]; data = self.blob[(bv.byteOffset or 0):(bv.byteOffset or 0) + bv.byteLength]
            ext = 'png' if im.mimeType == 'image/png' else 'jpg'; md = hashlib.md5(data).hexdigest()
            if md not in man:
                used = set(man.values()); fn = '%s.%s' % (im.name, ext); k = 0
                while fn in used: k += 1; fn = '%s_%s%d.%s' % (im.name, tag, k, ext)
                open(os.path.join(texdir, fn), 'wb').write(data); man[md] = fn
            self.imgs.append(man[md])
        json.dump(man, open(man_p, 'w'), indent=0)
    def world(self, ni, parent=np.eye(4)):
        n = self.g.nodes[ni]
        if n.matrix: m = np.array(n.matrix).reshape(4, 4).T
        else:
            t = np.array(n.translation or [0, 0, 0]); s = np.array(n.scale or [1, 1, 1]); x, y, z, w = n.rotation or [0, 0, 0, 1]
            r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
            m = np.eye(4); m[:3, :3] = r * s; m[:3, 3] = t
        return parent @ m
    def bbox(self, ni, parent=np.eye(4)):            # world box of a node tree, from accessor min/max corners
        m = self.world(ni, parent); n = self.g.nodes[ni]; lo = np.full(3, 1e9); hi = -lo; tris = 0
        if n.mesh is not None:
            for p in self.g.meshes[n.mesh].primitives:
                a = self.g.accessors[p.attributes.POSITION]; mn, mx = np.array(a.min), np.array(a.max)
                c = np.array([[mn[0] if i & 1 else mx[0], mn[1] if i & 2 else mx[1], mn[2] if i & 4 else mx[2], 1] for i in range(8)]) @ m.T
                lo = np.minimum(lo, c[:, :3].min(0)); hi = np.maximum(hi, c[:, :3].max(0))
                if p.indices is not None: tris += self.g.accessors[p.indices].count // 3
        for c in n.children or []:
            l2, h2, t2 = self.bbox(c, m); lo = np.minimum(lo, l2); hi = np.maximum(hi, h2); tris += t2
        return lo, hi, tris

    def write(self, roots, path, texrel, rename=None):
        g, blob = self.g, self.blob
        out = GLTF2(); out.asset = Asset(version='2.0', generator='aurelia glbcut')
        out.samplers = g.samplers; out.textures = g.textures; out.materials = g.materials
        out.images = [Image(name=im.name, uri=texrel + self.imgs[i], mimeType=im.mimeType) for i, im in enumerate(g.images)]
        out.extensionsUsed = [e for e in (g.extensionsUsed or []) if e not in ('EXT_meshopt_compression', 'KHR_mesh_quantization')]
        data = bytearray(); amap = {}; mmap = {}
        def acc(ai, target):
            if ai is None: return None
            if ai in amap: return amap[ai]
            a = g.accessors[ai]; v = g.bufferViews[a.bufferView]; es = CS[a.componentType] * NC[a.type]; st = v.byteStride or es
            raw = np.frombuffer(blob, np.uint8, count=(a.count - 1) * st + es, offset=(v.byteOffset or 0) + (a.byteOffset or 0))
            arr = np.lib.stride_tricks.as_strided(raw, (a.count, es), (st, 1)).copy(); ct = a.componentType
            if target == 34963 and ct == 5125 and a.count and arr.view(np.uint32).max() < 65535:
                arr = arr.view(np.uint32).astype(np.uint16).view(np.uint8).reshape(a.count, 2); ct = 5123
            while len(data) % 4: data.append(0)
            off = len(data); data.extend(arr.tobytes())
            out.bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=arr.size, target=target))
            out.accessors.append(Accessor(bufferView=len(out.bufferViews) - 1, byteOffset=0, componentType=ct, normalized=a.normalized, count=a.count, type=a.type, max=a.max, min=a.min))
            amap[ai] = len(out.accessors) - 1; return amap[ai]
        def mesh(mi):
            if mi in mmap: return mmap[mi]
            m = g.meshes[mi]; prims = []
            for p in m.primitives:
                q = Primitive(mode=p.mode, material=p.material, indices=acc(p.indices, 34963), attributes=Attributes())
                for at in ATTS: setattr(q.attributes, at, acc(getattr(p.attributes, at), 34962))
                prims.append(q)
            out.meshes.append(Mesh(name=m.name, primitives=prims)); mmap[mi] = len(out.meshes) - 1; return mmap[mi]
        def node(ni, top):
            n = g.nodes[ni]; name = rename(n.name) if (rename and top) else n.name
            o = Node(name=name, mesh=mesh(n.mesh) if n.mesh is not None else None, translation=n.translation, rotation=n.rotation, scale=n.scale, matrix=n.matrix)
            out.nodes.append(o); k = len(out.nodes) - 1
            o.children = [node(c, False) for c in (n.children or [])] or None
            return k
        tops = [node(r, True) for r in roots]
        out.scenes = [Scene(nodes=tops)]; out.scene = 0
        out.buffers = [Buffer(byteLength=len(data))]; out.set_binary_blob(bytes(data)); out.save_binary(path)
        return len(data)

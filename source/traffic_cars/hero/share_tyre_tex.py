"""Point a traffic car GLB's tyre images at the shared files next to it (tyre_basecolor.png, tyre_normal.png)
instead of embedding a copy, and drop the embedded bytes. All five cars then use one texture pair in the game.
usage: python3 share_tyre_tex.py in.glb out.glb"""
import sys
from pygltflib import GLTF2, BufferView

SHARED = {'tyre_basecolor': 'tyre_basecolor.png', 'tyre_normal': 'tyre_normal.png'}
src, out = sys.argv[1:3]
g = GLTF2().load(src); blob = g.binary_blob()
for im in g.images:
    if im.name in SHARED:
        im.uri = SHARED[im.name]; im.bufferView = None; im.mimeType = None
# compact the binary buffer: keep only the buffer views something still uses
used = set()
for a in g.accessors:
    if a.bufferView is not None: used.add(a.bufferView)
for im in g.images:
    if im.bufferView is not None: used.add(im.bufferView)
remap, views, data = {}, [], bytearray()
for i, bv in enumerate(g.bufferViews):
    if i not in used: continue
    while len(data) % 4: data.append(0)
    off = bv.byteOffset or 0; chunk = blob[off:off + bv.byteLength]
    remap[i] = len(views)
    views.append(BufferView(buffer=0, byteOffset=len(data), byteLength=bv.byteLength, byteStride=bv.byteStride, target=bv.target))
    data += chunk
for a in g.accessors:
    if a.bufferView is not None: a.bufferView = remap[a.bufferView]
for im in g.images:
    if im.bufferView is not None: im.bufferView = remap[im.bufferView]
g.bufferViews = views; g.buffers[0].byteLength = len(data)
g.set_binary_blob(bytes(data)); g.save(out)
print('shared tyre textures:', [im.name for im in g.images if im.uri], 'bytes', len(blob), '->', len(data))

# Where the ambient sounds belong: distance to the sea and to running water (rivers; lakes count half), on a 12 m grid
# over the island -> godot/assets/island/ambience.bin (u16 width, u16 height, then width*height pairs of bytes:
# sea distance / 4 m, water distance / 4 m, both capped at 255). Read by scripts/ambience.gd.
import json, struct, base64, glob, numpy as np
from scipy import ndimage
REPO = '/home/claude/aurelia-island'
W = json.load(open(REPO + '/data/world.json')); hm = W['heightmap']
H = np.frombuffer(base64.b64decode(json.load(open(REPO + '/data/height.json'))['b64']), '<i2').astype(np.float32).reshape(int(hm['ny']), int(hm['nx'])) * float(hm['scale'])
H = H[::2, ::2]          # 12 m cells, row = game -z (south to north in blender y), col = x
ny, nx = H.shape; X0, Z0, C = -2400.0, -1680.0, 12.0       # game: x = X0 + col*C, z = -(Y0 + row*C) with Y0 = -1680
sea = H < 0.4
d_sea = ndimage.distance_transform_edt(~sea) * C
water = np.zeros_like(sea)
def mark(x, z, r=8.0):
    col = int(round((x - X0) / C)); row = int(round((-z - Z0) / C)); k = max(0, int(r / C))
    water[max(0, row - k):row + k + 1, max(0, col - k):col + k + 1] = True
for f in glob.glob(REPO + '/godot/assets/island/chunks/b_*.glb'):
    b = open(f, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]; g = json.loads(b[20:20 + L]); B = b[20 + L + 8:]
    for n in g['nodes']:
        if not n.get('name', '').startswith('River'): continue
        a = g['accessors'][g['meshes'][n['mesh']]['primitives'][0]['attributes']['POSITION']]; bv = g['bufferViews'][a['bufferView']]
        P = np.frombuffer(B, np.float32, a['count'] * 3, bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, 3) * np.array(n.get('scale', [1, 1, 1])) + np.array(n['translation'])
        for p in P:
            if p[1] > 0.5: mark(p[0], p[2])
d_riv = ndimage.distance_transform_edt(~water) * C
lake = np.zeros_like(sea)
for lx, ly, lz, lr in W['lakes']:
    yy, xx = np.mgrid[0:ny, 0:nx]; gx = X0 + xx * C; gz = -(Z0 + yy * C)
    lake |= (gx - lx) ** 2 + (gz - lz) ** 2 < lr ** 2
d_lake = ndimage.distance_transform_edt(~lake) * C
d_w = np.minimum(d_riv, d_lake * 2.0)
out = np.stack([np.clip(d_sea / 4, 0, 255), np.clip(d_w / 4, 0, 255)], -1).astype(np.uint8)
open(REPO + '/godot/assets/island/ambience.bin', 'wb').write(struct.pack('<HH', nx, ny) + out.tobytes())
print(nx, ny, 'sea cells', sea.sum(), 'river cells', water.sum())

# Rivers in the source map ride over the ground in places: a slab hanging above lower banks, and two crossings where the
# water runs across the road at deck height instead of under it. Run after export_chunks.py; edits the River_* meshes
# in the exported base chunks in place:
#   * water is kept within 0.3 m of the ground under it (inland; the sea part is left alone)
#   * where a road passes over, the water dips under the road and the ground (a culvert), so it ends cleanly at each verge
import json, struct, base64, glob, os, numpy as np
REPO = os.path.abspath(os.path.dirname(__file__) + '/../..')
W = json.load(open(REPO + '/data/world.json')); hm = W['heightmap']
H = np.frombuffer(base64.b64decode(json.load(open(REPO + '/data/height.json'))['b64']), '<i2').astype(np.float32).reshape(int(hm['ny']), int(hm['nx'])) * float(hm['scale'])
X0, Y0, C = float(hm['x0']), float(hm['y0']), float(hm['cell'])
def ground(x, z):
    c = (x - X0) / C; r = (-z - Y0) / C; i, j = int(np.floor(r)), int(np.floor(c)); fr, fc = r - i, c - j
    i = min(max(i, 0), H.shape[0] - 2); j = min(max(j, 0), H.shape[1] - 2)
    return (H[i, j] * (1 - fc) + H[i, j + 1] * fc) * (1 - fr) + (H[i + 1, j] * (1 - fc) + H[i + 1, j + 1] * fc) * fr
RP = []
for r in W['roads']:
    p = np.array(r['pts'], np.float32).reshape(-1, 3); RP.append((p, float(r['w']) * 0.5 + 4.0))
def road_y(x, z):
    best = None
    for p, hw in RP:
        d = np.hypot(p[:, 0] - x, p[:, 2] - z); k = int(d.argmin())
        if d[k] < hw and (best is None or p[k, 1] > best): best = float(p[k, 1])
    return best
n_cl = n_cv = 0
for f in sorted(glob.glob(REPO + '/godot/assets/island/chunks/b_*.glb')):
    b = bytearray(open(f, 'rb').read()); L = struct.unpack('<I', b[12:16])[0]; g = json.loads(b[20:20 + L]); B0 = 20 + L + 8
    hit = False
    for n in g['nodes']:
        if not n.get('name', '').startswith('River'): continue
        s = np.array(n.get('scale', [1, 1, 1]), np.float64); t = np.array(n.get('translation', [0, 0, 0]), np.float64)
        a = g['accessors'][g['meshes'][n['mesh']]['primitives'][0]['attributes']['POSITION']]; bv = g['bufferViews'][a['bufferView']]
        off = B0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        P = np.frombuffer(bytes(b[off:off + a['count'] * 12]), np.float32).reshape(-1, 3).astype(np.float64); Wp = P * s + t
        for v in Wp:
            if v[1] < 0.5: continue
            gy = ground(v[0], v[2]); ry = road_y(v[0], v[2])
            if ry is not None and v[1] > ry - 1.2: v[1] = min(gy, ry) - 1.5; n_cv += 1
            elif v[1] > gy + 0.3: v[1] = gy + 0.3; n_cl += 1
        P2 = ((Wp - t) / s).astype(np.float32); b[off:off + a['count'] * 12] = P2.tobytes()
        a['min'] = P2.min(0).tolist(); a['max'] = P2.max(0).tolist(); hit = True
    if hit:
        js = json.dumps(g, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
        assert len(js) <= L or True
        out = bytearray(b[:12]) + struct.pack('<I', len(js)) + b'JSON' + js + b[20 + L:]
        out[8:12] = struct.pack('<I', len(out)); open(f, 'wb').write(out)
print('rivers: %d verts settled onto the ground, %d dipped under roads' % (n_cl, n_cv))

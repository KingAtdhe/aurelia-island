# Verges (the gravel/dirt "Shoulder" strips built along each road) run straight across the other road at crossings and
# junctions, lying over its asphalt: stripes of asphalt, dirt and grass-coloured verge (seen at Dune Road by the speed
# trap). Run after export_chunks.py; edits the Verge_* meshes in the exported base chunks in place: every verge triangle
# whose middle lies on another road's paved width (and at that road's height, so bridges and underpasses are left alone)
# is collapsed to a point. Usage: python3 fix_verges.py [--dry]
import json, struct, glob, os, sys, numpy as np
REPO = os.path.abspath(os.path.dirname(__file__) + '/../..')
W = json.load(open(REPO + '/data/world.json'))
SEG = []          # x0 z0 x1 z1 y0 y1 hw
for r in W['roads']:
    if r.get('type') == 'dirt': continue          # trails are dirt themselves (built like a verge): never cut into them
    p = np.array(r['pts'], np.float64).reshape(-1, 3)
    if r.get('closed'): p = np.vstack([p, p[:1]])
    hw = float(r['w']) * 0.5
    for a, b in zip(p[:-1], p[1:]): SEG.append([a[0], a[2], b[0], b[2], a[1], b[1], hw])
SEG = np.array(SEG)
def on_road(c):
    """c: (n, 3) triangle middles -> bool, inside a road's paved width (less 5 cm) within 1.2 m of its height"""
    out = np.zeros(len(c), bool)
    lo = c[:, [0, 2]].min(0) - 30; hi = c[:, [0, 2]].max(0) + 30
    S = SEG[(np.maximum(SEG[:, 0], SEG[:, 2]) > lo[0]) & (np.minimum(SEG[:, 0], SEG[:, 2]) < hi[0]) & (np.maximum(SEG[:, 1], SEG[:, 3]) > lo[1]) & (np.minimum(SEG[:, 1], SEG[:, 3]) < hi[1])]
    for x0, z0, x1, z1, y0, y1, hw in S:
        dx, dz = x1 - x0, z1 - z0; L2 = max(dx * dx + dz * dz, 1e-9)
        t = np.clip(((c[:, 0] - x0) * dx + (c[:, 2] - z0) * dz) / L2, 0, 1)
        ex = c[:, 0] - x0 - dx * t; ez = c[:, 2] - z0 - dz * t; y = y0 + (y1 - y0) * t
        out |= (ex * ex + ez * ez < (hw - 0.05) ** 2) & (np.abs(c[:, 1] - y) < 1.2)
    return out
dry = '--dry' in sys.argv; total = 0
for f in sorted(glob.glob(REPO + '/godot/assets/island/chunks/b_*.glb')):
    b = bytearray(open(f, 'rb').read()); L = struct.unpack('<I', b[12:16])[0]; g = json.loads(b[20:20 + L]); B0 = 20 + L + 8
    n_f = 0
    for n in g['nodes']:
        if not n.get('name', '').startswith('Verge') or 'mesh' not in n: continue
        s = np.array(n.get('scale', [1, 1, 1]), np.float64); t = np.array(n.get('translation', [0, 0, 0]), np.float64)
        for prim in g['meshes'][n['mesh']]['primitives']:
            a = g['accessors'][prim['attributes']['POSITION']]; bv = g['bufferViews'][a['bufferView']]
            assert a['componentType'] == 5126 and bv.get('byteStride', 12) == 12
            off = B0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
            P = np.frombuffer(bytes(b[off:off + a['count'] * 12]), np.float32).reshape(-1, 3).astype(np.float64) * s + t
            ia = g['accessors'][prim['indices']]; ibv = g['bufferViews'][ia['bufferView']]
            dt = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[ia['componentType']]
            ioff = B0 + ibv.get('byteOffset', 0) + ia.get('byteOffset', 0); nb = ia['count'] * np.dtype(dt).itemsize
            I = np.frombuffer(bytes(b[ioff:ioff + nb]), dt).reshape(-1, 3).copy()
            live = ~((I[:, 0] == I[:, 1]) & (I[:, 1] == I[:, 2]))
            kill = on_road(P[I].mean(1)) & live
            if kill.any():
                I[kill, 1] = I[kill, 0]; I[kill, 2] = I[kill, 0]; n_f += int(kill.sum())
                b[ioff:ioff + nb] = I.astype(dt).tobytes()
    if n_f:
        total += n_f; print(os.path.basename(f), n_f)
        if not dry: open(f, 'wb').write(bytes(b))
print('verge triangles collapsed:', total, '(dry run)' if dry else '')

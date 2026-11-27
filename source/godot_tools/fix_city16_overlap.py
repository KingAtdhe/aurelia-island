# Concept 16 put new towers on the 44 city plots and hid the old "Towers" boxes, but at some plots the old map also
# had a tall block in its Structures group (with KitTrim piers, ArchTrim, window glass) standing on the same spot,
# a little larger than the new tower, so the old flat facade covered the new one (Street E260). Run after
# export_chunks.py (and export_city16.py); edits the d_*/b_* chunks in place: every triangle of an old building group
# whose middle lies inside a city16 plot (+0.6 m) and above the new tower's podium (y0 + 7 m) is collapsed.
# Shops, roads, ground and street kit are left alone. Usage: python3 fix_city16_overlap.py [--dry]
import json, struct, glob, os, sys, numpy as np
REPO = os.path.abspath(os.path.dirname(__file__) + '/../..')
PL = json.load(open(os.path.join(os.path.dirname(__file__), 'city16_plots.json')))
GROUPS = ('Structures', 'KitTrim', 'ArchTrim', 'Houses', 'Facades', 'Roofs', 'Trim')          # not Towers: those boxes are the skyline past 1250 m, where city16 is not drawn
dry = '--dry' in sys.argv; total = {}
def inside(c):
    k = np.zeros(len(c), bool)
    for p in PL:
        k |= (np.abs(c[:, 0] - p['x']) < p['w'] / 2 + 0.6) & (np.abs(c[:, 2] - p['z']) < p['d'] / 2 + 0.6) & (c[:, 1] > p['y0'] + 7.0)
    return k
for f in sorted(glob.glob(REPO + '/godot/assets/island/chunks/[db]_*.glb')):
    b = bytearray(open(f, 'rb').read()); L = struct.unpack('<I', b[12:16])[0]; g = json.loads(b[20:20 + L]); B0 = 20 + L + 8
    hit = 0
    for n in g['nodes']:
        nm = n.get('name', '')
        if 'mesh' not in n or nm.split('__')[0] not in GROUPS: continue
        s = np.array(n.get('scale', [1, 1, 1]), np.float64); t = np.array(n.get('translation', [0, 0, 0]), np.float64)
        assert 'rotation' not in n and 'matrix' not in n
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
            kill = inside(P[I].mean(1)) & live
            if kill.any():
                I[kill, 1] = I[kill, 0]; I[kill, 2] = I[kill, 0]; b[ioff:ioff + nb] = I.astype(dt).tobytes()
                hit += int(kill.sum()); total[nm.split('__')[0]] = total.get(nm.split('__')[0], 0) + int(kill.sum())
    if hit:
        print(os.path.basename(f), hit)
        if not dry: open(f, 'wb').write(bytes(b))
print('collapsed by group:', total, '(dry run)' if dry else '')

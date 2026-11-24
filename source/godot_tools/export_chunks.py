"""Cut the packed island (map/islandc + map/islanddc, unpacked) into streaming chunks for the Godot game.
Every mesh goes to the 400 m cell its box centre is in: b_<cx>_<cz>.glb (ground, roads, water edge, far buildings) and
d_<cx>_<cz>.glb (close-up buildings, street kit, landmarks). index.json: each chunk's world box, triangles and groups.
usage: python3 export_chunks.py islandc_raw.glb islanddc_raw.glb <godot>/assets/island"""
import sys, os, json, re, math, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from glbcut import Src
BASE, DET, OUT = sys.argv[1:4]; CELL = 400.0
SKIP = re.compile(r'^Water$')                       # the open sea is one plane in the game (lakes and rivers stay)
FAR = re.compile(r'^(Landmark|TowerCrown|Spin_)')  # seen from across the island: always loaded with the base
os.makedirs(OUT + '/chunks', exist_ok=True)
index = {}
for kind, path in (('b', BASE), ('d', DET)):
    s = Src(path, OUT + '/tex', kind); g = s.g
    roots = g.scenes[g.scene or 0].nodes
    flat = []
    for r in roots:                                  # the scene root may be a plain group: take its children
        n = g.nodes[r]
        if n.mesh is None and n.children: flat += n.children
        else: flat.append(r)
    cells = {}
    for ni in flat:
        nm = g.nodes[ni].name or ''
        if SKIP.match(nm): continue
        lo, hi, tris = s.bbox(ni)
        if tris == 0: continue
        c = (int(math.floor((lo[0] + hi[0]) / 2 / CELL)), int(math.floor((lo[2] + hi[2]) / 2 / CELL)))
        if kind == 'd' and FAR.match(nm): c = ('f',) + c
        e = cells.setdefault(c, {'n': [], 'lo': np.full(3, 1e9), 'hi': np.full(3, -1e9), 'tris': 0, 'groups': {}})
        e['n'].append(ni); e['lo'] = np.minimum(e['lo'], lo); e['hi'] = np.maximum(e['hi'], hi); e['tris'] += tris
        grp = nm.split('__')[0]; e['groups'][grp] = e['groups'].get(grp, 0) + tris
    for c, e in sorted(cells.items(), key=lambda kv: str(kv[0])):
        k2 = 'b' if c[0] == 'f' else kind; c2 = c[1:] if c[0] == 'f' else c
        name = '%s_%d_%d' % (kind + ('f' if c[0] == 'f' else ''), c2[0], c2[1]); b = s.write(e['n'], '%s/chunks/%s.glb' % (OUT, name), '../tex/')
        index[name] = {'kind': k2, 'cell': list(c2), 'min': e['lo'].round(1).tolist(), 'max': e['hi'].round(1).tolist(), 'tris': e['tris'], 'bytes': b, 'groups': e['groups']}
    print(kind, len(cells), 'chunks', sum(e['tris'] for e in cells.values()), 'tris')
json.dump({'cell': CELL, 'chunks': index}, open(OUT + '/index.json', 'w'), indent=0)
print('MB', round(sum(v['bytes'] for v in index.values()) / 1e6, 1), 'tex', len(os.listdir(OUT + '/tex')))

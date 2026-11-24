"""Plants, rocks and street furniture of the whole island for the Godot game.
Library: flora.glb with one S_<species>_LOD0/_LOD1 tree per species (kit and plant libraries of the web game, with Saba's
Tripo trees, rocks and buildings replacing the old ones the same way the web game does). Instances: flora.bin (float32
x y z scale yaw r g b per object) + flora.json (species -> [first float, count]). The coast keeps the hand-placed set of
the coast slice (Tripo houses, café, cliff faces), everything else comes from data/flora.json.
usage: python3 export_flora.py florac_raw.glb florakc_raw.glb tprops_raw.glb <repo> <out dir>"""
import sys, os, re, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from glbcut import Src
FC, FK, TP, REPO, OUT = sys.argv[1:6]
DROP = re.compile(r'^(prop_(cottage|cottage_b|village_row|silos|warehouse|hay_shed|hut_red|hut_blue|winery_hq|container|jetty|sail_yacht|motor_yacht|person_\d|tcar_[cde]|shop_.*)|sandstone_spire)$')
TTREE = {'pine': 'tree_t_pine', 'oak': 'tree_t_oak', 'oak_b': 'tree_t_oak', 'plane': 'tree_t_oak', 'plane_b': 'tree_t_oak', 'fruit': 'tree_t_olive', 'cypress': 'tree_t_cypress'}
COAST = (-1950.0, -650.0, 280.0, 1340.0)           # x0 x1 z0 z1 of the coast slice
isl = json.load(open(REPO + '/data/flora.json')); coast = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'coast_flora.json')))
inst = {}
for sp, a in isl['instances'].items():
    if DROP.match(sp): continue
    a = np.array(a, np.float32).reshape(-1, 8)
    out = (a[:, 0] < COAST[0]) | (a[:, 0] > COAST[1]) | (a[:, 2] < COAST[2]) | (a[:, 2] > COAST[3])
    if out.any(): inst[sp] = a[out]
for sp, a in coast.items():
    a = np.array(a, np.float32).reshape(-1, 8); inst[sp] = np.concatenate([inst[sp], a]) if sp in inst else a
inst = {sp: a[a[:, 3] > 0] for sp, a in inst.items()}
# as the web game does once Saba's Tripo houses are in: every farmhouse becomes her village house
if 'prop_farmhouse' in inst:
    a = inst.pop('prop_farmhouse').copy(); a[:, 3] = 1.0; inst['prop_house_t_village'] = np.concatenate([inst.get('prop_house_t_village', np.zeros((0, 8), np.float32)), a])
# the café (two of Saba's Tripo cafés) beside the coast roads, on flat ground facing the road, clear of everything else
import base64, math
W = json.load(open(REPO + '/godot/assets/world.json')); hm = W['heightmap']
H = np.frombuffer(base64.b64decode(json.load(open(REPO + '/data/height.json'))['b64']), '<i2').astype(np.float32).reshape(hm['ny'], hm['nx'])
def hAt(x, z):
    fx = min(max((x - hm['x0']) / hm['cell'], 0), hm['nx'] - 1.001); fy = min(max((-z - hm['y0']) / hm['cell'], 0), hm['ny'] - 1.001)
    ix, iy = int(fx), int(fy); u, v = fx - ix, fy - iy
    return ((H[iy, ix] * (1 - u) + H[iy, ix + 1] * u) * (1 - v) + (H[iy + 1, ix] * (1 - u) + H[iy + 1, ix + 1] * u) * v) * hm['scale']
RP = [(np.array(r['pts']).reshape(-1, 3), r['w'] / 2) for r in W['roads']]
def road_clear(x, z, r):
    for p, hw in RP:
        if np.min(np.hypot(p[:, 0] - x, p[:, 2] - z)) < hw + r + 2.5: return False
    return True
def busy(x, z, r):
    for sp2, a in inst.items():
        if not sp2.startswith(('prop_', 'rock_t', 'tree')) and sp2 not in ('oak', 'oak_b', 'pine', 'palm', 'palm_b', 'plane', 'plane_b', 'spruce', 'spruce_b', 'fruit'): continue
        if len(a) and np.min(np.hypot(a[:, 0] - x, a[:, 2] - z)) < r + 8: return True
    for o in W['obstacles']:
        if math.hypot(o[0] - x, o[1] - z) < r + math.hypot(o[2], o[3]) + 2: return True
    for o in W['circles']:
        if math.hypot(o[0] - x, o[1] - z) < r + o[2] + 2: return True
    return False
def site(x, z, r, flat):
    hs = [hAt(x + math.cos(k * 0.785) * (r if k else 0), z + math.sin(k * 0.785) * (r if k else 0)) for k in range(9)]
    return min(hs) if max(hs) - min(hs) < flat and min(hs) > 2.0 else None
rng = np.random.default_rng(11); cafes = []
for rname in ('Lighthouse Road', 'Peninsula Road', 'West Avenue'):
    p = next(np.array(r['pts']).reshape(-1, 3) for r in W['roads'] if r['name'] == rname); hw = 5.0
    for i in range(4, len(p) - 4, 3):
        if len(cafes) >= 2 or (cafes and cafes[-1][3] == rname): break
        t = p[i + 1] - p[i - 1]; t /= np.linalg.norm(t[[0, 2]]); nx, nz = -t[2], t[0]
        for side in (1, -1):
            off = hw + 5.5 + 4 + rng.random() * 3; x, z = p[i, 0] + nx * side * off, p[i, 2] + nz * side * off
            if not road_clear(x, z, 5.5) or busy(x, z, 5.5): continue
            y = site(x, z, 5.5, 1.6)
            if y is None: continue
            ya = math.atan2(-nx * side, -nz * side); cafes.append((x, y - 0.12, z, rname, ya)); break
for x, y, z, rname, ya in cafes:
    inst['prop_house_t_cafe'] = np.concatenate([inst.get('prop_house_t_cafe', np.zeros((0, 8), np.float32)), np.array([[x, y, z, 1.0, ya, 0.91, 0.91, 0.91]], np.float32)])
print('cafes', [(round(c[0]), round(c[2]), c[3]) for c in cafes])
# library
srcs = [Src(FC, OUT + '/tex', 'f'), Src(FK, OUT + '/tex', 'k'), Src(TP, OUT + '/tex', 't')]
have = {}                                            # species -> {lod: (src, node)}; later sources win (Tripo over kit)
for s, pre in zip(srcs, ('FLORA_', 'FLORA_', 'T_')):
    for i, n in enumerate(s.g.nodes):
        m = re.match('^' + pre + r'(.+)_LOD([01])$', n.name or '')
        if m: have.setdefault(m.group(1), {})[int(m.group(2))] = (s, i)
use = {}
for sp in inst:
    src = TTREE.get(sp, sp)
    if src not in have: print('no model for', sp, len(inst[sp])); continue
    use[src] = have[src]
inst = {sp: a for sp, a in inst.items() if TTREE.get(sp, sp) in use}
roots = {}
for sp, lods in use.items():
    for lod, (s, i) in lods.items(): roots.setdefault(id(s), (s, []))[1].append((i, 'S_%s_LOD%d' % (sp, lod)))
# one GLB per source library, all into the same texture folder
for k, (s, lst) in roots.items():
    nm = {i: new for i, new in lst}; tag = 'tprops' if s is srcs[2] else ('flora' if s is srcs[0] else 'kit')
    b = s.write([i for i, _ in lst], '%s/flora_%s.glb' % (OUT, tag), 'tex/', rename=None)
    # rename top nodes in place (pygltflib rename hook is for the top node names)
    from pygltflib import GLTF2
    g = GLTF2().load('%s/flora_%s.glb' % (OUT, tag))
    for j, ni in enumerate(g.scenes[0].nodes): g.nodes[ni].name = lst[j][1]
    g.save_binary('%s/flora_%s.glb' % (OUT, tag)); print(tag, len(lst), 'nodes', round(b / 1e6, 1), 'MB')
buf = []; idx = {}; off = 0
for sp in sorted(inst):
    a = inst[sp].astype(np.float32); idx[sp] = [off, len(a)]; buf.append(a.ravel()); off += a.size
np.concatenate(buf).astype('<f4').tofile(OUT + '/flora.bin')
spec = {sp: isl['species'].get(sp, {}) for sp in idx}
json.dump({'note': 'x y z scale yaw r g b per object; species -> [first float, count]', 'species': idx, 'model': {sp: TTREE.get(sp, sp) for sp in idx}, 'info': spec}, open(OUT + '/flora.json', 'w'))
print('species', len(idx), 'objects', sum(v[1] for v in idx.values()))

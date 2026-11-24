"""Island-wide collision data for the Godot game, built with the web game's rules (index.html prepWorld + floraColliders):
map obstacles and circles, a collider for every lamp, sign, trunk and rock from its real size (light street furniture can
be knocked away, soft plants never collide), and per-road side limits: rock-cut retaining walls on the mountain passes and
guard rails on the drop side of main roads. -> island/coll.json
usage: python3 gen_coll.py <repo>"""
import sys, os, re, json, math, base64, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from glbcut import Src
REPO = sys.argv[1]; G = REPO + '/godot/assets/'
W = json.load(open(G + 'world.json')); hm = W['heightmap']
H = np.frombuffer(base64.b64decode(json.load(open(REPO + '/data/height.json'))['b64']), '<i2').astype(np.float32).reshape(hm['ny'], hm['nx'])
def hAt(x, z):
    fx = min(max((x - hm['x0']) / hm['cell'], 0), hm['nx'] - 1.001); fy = min(max((-z - hm['y0']) / hm['cell'], 0), hm['ny'] - 1.001)
    ix, iy = int(fx), int(fy); u, v = fx - ix, fy - iy
    return ((H[iy, ix] * (1 - u) + H[iy, ix + 1] * u) * (1 - v) + (H[iy + 1, ix] * (1 - u) + H[iy + 1, ix + 1] * u) * v) * hm['scale']
SG = 48.0
roads = []
for r in W['roads']:
    p = np.array(r['pts'], np.float64).reshape(-1, 3); roads.append({'name': r['name'], 'type': r['type'], 'hw': r['w'] / 2, 'p': p, 'n': len(p), 'closed': r['closed'], 'wall': r['wall']})
seg = {}
for ri, r in enumerate(roads):
    n = r['n']; p = r['p']
    for i in range(n if r['closed'] else n - 1):
        j = (i + 1) % n; k = (math.floor((p[i, 0] + p[j, 0]) / 2 / SG), math.floor((p[i, 2] + p[j, 2]) / 2 / SG)); seg.setdefault(k, []).append((ri, i))
def road_query(x, z, y):
    best = 1e9; out = None; gx, gz = math.floor(x / SG), math.floor(z / SG)
    for ax in (gx - 1, gx, gx + 1):
        for az in (gz - 1, gz, gz + 1):
            for ri, i in seg.get((ax, az), ()):
                r = roads[ri]; p = r['p']; j = (i + 1) % r['n']; x0, z0 = p[i, 0], p[i, 2]; dx, dz = p[j, 0] - x0, p[j, 2] - z0; L2 = dx * dx + dz * dz
                if L2 < 1e-6: continue
                t = min(max(((x - x0) * dx + (z - z0) * dz) / L2, 0), 1); px, pz = x0 + dx * t, z0 + dz * t; d = math.hypot(x - px, z - pz)
                if d > r['hw'] + 4: continue
                yy = p[i, 1] + (p[j, 1] - p[i, 1]) * t; sc = d + 4 * max(0, abs(y - yy) - 2.5)
                if sc < best: best = sc; out = (r, d)
    return out
# side limits
def runs(m, n, closed, dil, minlen):
    d = np.zeros(n, np.uint8)
    for i in np.nonzero(m)[0]:
        for k in range(-dil, dil + 1):
            q = (i + k) % n if closed else i + k
            if 0 <= q < n: d[q] = 1
    i = 0
    while i < n:
        if not d[i]: i += 1; continue
        j = i
        while j < n and d[j]: j += 1
        if j - i < minlen: d[i:j] = 0
        i = j
    return d
for r in roads:
    pas = r['name'] in ('Summit Pass', 'Skyline Road', 'Eagle Descent', 'Serpentine'); main = r['type'] in ('hwy', 'road'); r['lim'] = None
    if not pas and not main: continue
    n, p = r['n'], r['p']; cut = [np.zeros(n, np.uint8), np.zeros(n, np.uint8)]; drop = [np.zeros(n, np.uint8), np.zeros(n, np.uint8)]
    for i in range(n):
        if r['wall'][i]: continue
        j, k = min(n - 1, i + 1), max(0, i - 1); tx, tz = p[j, 0] - p[k, 0], p[j, 2] - p[k, 2]; L = math.hypot(tx, tz) or 1; tx /= L; tz /= L; y = p[i, 1]
        near = False; gx, gz = math.floor(p[i, 0] / SG), math.floor(p[i, 2] / SG)
        for ax in (gx - 1, gx, gx + 1):
            for az in (gz - 1, gz, gz + 1):
                for ri, m in seg.get((ax, az), ()):
                    o = roads[ri]
                    if o is r: continue
                    if math.hypot(o['p'][m, 0] - p[i, 0], o['p'][m, 2] - p[i, 2]) < r['hw'] + o['hw'] + 22: near = True; break
                if near: break
            if near: break
        if near: continue
        for si, s in ((0, 1), (1, -1)):
            at = lambda d: hAt(p[i, 0] + tz * s * (r['hw'] + d), p[i, 2] - tx * s * (r['hw'] + d))
            if pas and (r['closed'] or 2 < i < n - 3) and at(31) - y > 4 and at(18) > y - 0.5: cut[si][i] = 1
            if main and y - at(24) > 4.5: drop[si][i] = 1
    lim = []
    for si in (0, 1):
        c = runs(cut[si], n, r['closed'], 2, 5); g = runs(drop[si], n, r['closed'], 3, 1)
        lim.append([round(r['hw'] + 0.25, 2) if c[i] else round(r['hw'] + 1.6, 2) if g[i] else 0 for i in range(n)])
    r['lim'] = lim
# flora colliders
POLE = re.compile(r'lamp|signal|power_pole|tg_light|tg_mirror|windpump')
KNOCK = re.compile(r'^prop_(cones|beach_set|rk_post|rk_cone|rk_chevron|rk_worksign|rk_arrowboard|reflector|bin|trashbags|newsbox|scooter|bikerack|bench|planter|sign_|board_|mailbox|cafe)')
SOFT = re.compile(r'^(grass|flowers|bush|fern|oleander|prop_walker|prop_rk_trench|prop_rk_island|prop_vineyard|prop_scree|prop_walls_fences|prop_rk_barrier)|^prop_shop_|hay_field|jetty|breakwater|tunnel|portal|bridge|gantry|arch|overpass|flyover|canopy')
TREE = re.compile(r'^(oak|pine|spruce|palm|birch|plane|cypress|fruit|olive|cedar)')
FD = json.load(open(G + 'island/flora.json')); FB = np.fromfile(G + 'island/flora.bin', '<f4')
boxes = {}
for f in ('flora_flora', 'flora_kit', 'flora_tprops'):
    s = Src(G + 'island/%s.glb' % f, '/tmp/_tex_scratch', 'x', images=False)
    for ni in s.g.scenes[0].nodes:
        m = re.match(r'^S_(.+)_LOD([01])$', s.g.nodes[ni].name)
        if m and (m.group(2) == '0' or m.group(1) not in boxes): boxes[m.group(1)] = s.bbox(ni)[:2]
box, circ, knock = [], [], []
for o in W['obstacles']: box.append([round(v, 3) for v in o[:5]])
for o in W['circles']: circ.append([round(v, 3) for v in o[:3]])
for sp, (off, cnt) in FD['species'].items():
    mdl = FD['model'][sp]
    if SOFT.search(sp) or mdl not in boxes: continue
    lo, hi = boxes[mdl]; w, d, ht = hi[0] - lo[0], hi[2] - lo[2], hi[1] - lo[1]; cx0, cz0 = (hi[0] + lo[0]) / 2, (hi[2] + lo[2]) / 2
    if not ht > 0.3: continue
    info = FD['info'].get(sp, {}); tree = info.get('card', -1) >= 0 or TREE.match(sp); kn = KNOCK.match(sp)
    a = FB[off:off + cnt * 8].reshape(-1, 8)
    for k, (x, y, z, s, ya) in enumerate(a[:, :5]):
        c, sn = math.cos(ya), math.sin(ya); ox, oz = x + (cx0 * c + cz0 * sn) * s, z + (-cx0 * sn + cz0 * c) * s
        if tree: circ.append([round(float(x), 2), round(float(z), 2), round(min(max(0.045 * ht * s, 0.18), 0.6), 2)]); continue
        if POLE.search(sp): circ.append([round(float(x), 2), round(float(z), 2), 0.22]); continue
        if kn: knock.append([round(float(ox), 2), round(float(oz), 2), round(min(max(max(w, d) * s * 0.45, 0.2), 1.2), 2), sp, k]); continue
        if max(w, d) * s < 1.6: circ.append([round(float(ox), 2), round(float(oz), 2), round(max(0.15, max(w, d) * s * 0.42), 2)])
        else:
            q = road_query(ox, oz, y)
            if q and q[1] < q[0]['hw']: continue
            box.append([round(float(ox), 2), round(float(oz), 2), round(float(w * s / 2), 2), round(float(d * s / 2), 2), round(float(ya), 3)])
out = {'box': box, 'circ': circ, 'knock': knock, 'roads': {r['name']: {'hw': r['hw'], 'wall': r['wall'], 'lim': r['lim']} for r in roads}}
json.dump(out, open(G + 'island/coll.json', 'w'), separators=(',', ':'))
print('box', len(box), 'circ', len(circ), 'knock', len(knock), 'roads with limits', sum(1 for r in roads if r['lim']), 'lim points', sum(sum(1 for v in l if v) for r in roads if r['lim'] for l in r['lim']))

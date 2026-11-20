"""Aurelia Island: terrain, biomes and road network (numpy only, no Blender).
Blender coordinates: X east, Y north, Z up, metres."""
import numpy as np
from scipy.spatial import cKDTree

X0, X1, Y0, Y1 = -2400.0, 2400.0, -1680.0, 1680.0
CELL = 12.0
NX = int((X1 - X0) / CELL) + 1
NY = int((Y1 - Y0) / CELL) + 1
STEP = 5.0
SEA_FLOOR = -30.0

_rng = np.random.default_rng(20261115)
_TABLES = _rng.uniform(-1, 1, size=(80, 256, 256))


def vnoise(x, y, seed):
    t = _TABLES[seed % 80]
    xi = np.floor(x).astype(np.int64); yi = np.floor(y).astype(np.int64)
    xf = x - xi; yf = y - yi
    u = xf * xf * (3 - 2 * xf); v = yf * yf * (3 - 2 * yf)
    a = t[xi & 255, yi & 255]; b = t[(xi + 1) & 255, yi & 255]
    c = t[xi & 255, (yi + 1) & 255]; d = t[(xi + 1) & 255, (yi + 1) & 255]
    return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v


def fbm(x, y, octaves, seed):
    s = 0.0; amp = 1.0; f = 1.0; tot = 0.0
    for i in range(octaves):
        s = s + amp * vnoise(x * f + 17.3 * i, y * f - 9.1 * i, seed + i)
        tot += amp; amp *= 0.5; f *= 2.03
    return s / tot


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def gauss(x, y, cx, cy, sx, sy):
    return np.exp(-((x - cx) / sx) ** 2 - ((y - cy) / sy) ** 2)


def sq(x, y, cx, cy, rx, ry, p=4):
    return (np.abs((x - cx) / rx) ** p + np.abs((y - cy) / ry) ** p) ** (1 / p)


# ---------------------------------------------------------------- places
LOBES = [(-1250, -1100, 300), (1690, -1000, 230), (-2050, 300, 160), (2060, -150, 120),
         (-2235, -1090, 120), (2265, 950, 100), (330, -1570, 85), (-1500, 1490, 90)]      # last four: offshore islets
PEAKS = [(-680, 900, 430, 240), (-250, 790, 520, 250), (150, 930, 470, 235), (520, 870, 390, 225),
         (-60, 1090, 320, 180), (-920, 1050, 300, 200)]
MESAS = [(1180, 800, 90, 70), (1190, 320, 100, 80), (1500, 600, 70, 55), (1730, 255, 65, 55), (1400, 240, 85, 70),
         (1620, 880, 70, 50), (1090, 480, 28, 38), (1330, 860, 30, 42), (1700, 700, 24, 36), (1120, 180, 30, 40), (1560, 180, 28, 36)]
CITY = (0, -20, 760, 450); CITY_Z = 14.0
CIRCUIT = (1260, -355, 520, 360); CIRCUIT_Z = 16.0
HELI = (1715, -1010, 120); HELI_Z = 9.0
BAY = (-350, -700, 600, 330)
CHANNEL_X = -750.0
ESCARP = (80, 480, 455, 505, 62.0)       # x0, x1, y0, y1, height
LAKES = [(-1500, 520, 150), (-1000, 470, 110), (280, 610, 78), (280, 405, 62), (1185, -695, 38)]   # last two: tarn above / pool below the falls
RIVER = [(1180, -715), (1090, -790), (1000, -845), (900, -950), (880, -1010), (840, -1100), (850, -1150), (820, -1280), (810, -1345)]
RIVERS = [(RIVER, 9.5), ([(-1645, 512), (-1740, 548), (-1880, 590), (-2010, 625), (-2120, 650)], 4.5), ([(-1108, 478), (-1200, 500), (-1290, 512), (-1352, 512)], 3.5)]
ROUNDABOUTS = [(900, 560, 24.0), (440, -780, 22.0)]
FLY = {'Beach Flyover': 'Ring'}            # road that crosses another on a bridge with no junction
SERP = (560, 640, 890, 960, 640, 700, 1000, 1060)     # switchback hillside: x feather in/out, y feather in/out
FALLS = [(235, 28), (330, 20)]           # x position, width
REGIONS = [('Mountain Roads', -150, 900, 900, 420), ('Desert', 1380, 620, 600, 470), ('Forest Trails', -1350, 420, 600, 560),
           ('City', 0, -20, 640, 400), ('Racing Circuit', 1260, -355, 470, 330), ('Coastal Highway', -1300, -780, 520, 520),
           ('Countryside', 700, -900, 760, 300), ('Harbour', -350, -700, 560, 300), ('Heliport', 1715, -1010, 170, 150)]


def land_L(x, y):
    ang = np.arctan2(y / 1380, x / 2150)
    k = 1 + 0.07 * fbm(np.cos(ang) * 2 + 3, np.sin(ang) * 2 + 3, 3, 0) + 0.025 * fbm(np.cos(ang) * 8 + 1, np.sin(ang) * 8 + 1, 2, 5)
    L = 1 - np.sqrt((x / 2150) ** 2 + (y / 1380) ** 2) / k
    for cx, cy, r in LOBES:
        L = np.maximum(L, (1 - np.hypot(x - cx, y - cy) / (r * (1 + 0.15 * fbm(x / 90, y / 90, 2, 7)))) * 0.22)
    return L


def biomes(x, y):
    """Soft biome weights used for colours and vegetation."""
    n = fbm(x / 260, y / 260, 3, 33) * 0.25
    desert = smoothstep(1.05, 0.75, sq(x, y, 1400, 640, 640, 500, 2) + n)
    forest = smoothstep(1.1, 0.7, sq(x, y, -1350, 430, 680, 620, 2) + n)
    country = smoothstep(1.1, 0.8, sq(x, y, 720, -900, 800, 300, 2) + n)
    city = smoothstep(1.0, 0.86, sq(x, y, CITY[0], CITY[1], CITY[2], CITY[3]))
    circuit = smoothstep(1.0, 0.86, sq(x, y, *CIRCUIT, 3))
    return dict(desert=desert, forest=forest, country=country, city=city, circuit=circuit)


_PADZ = {}
PAD_LIFT = [13.0, 0.0]


def base_h(x, y, lakes=True, river=True, pads=True):
    x = np.asarray(x, float); y = np.asarray(y, float)
    L = land_L(x, y)
    shore = np.where(L > 0, 9 * smoothstep(0, 0.045, L) + 6 * smoothstep(0.03, 0.2, L), np.maximum(SEA_FLOOR, 300 * L))
    cf = smoothstep(0.0, 0.13, L)
    cliff = np.clip(gauss(x, y, -1450, -820, 520, 520) + gauss(x, y, -200, 1420, 1100, 260) + gauss(x, y, 2100, 500, 300, 500) * 0.6, 0, 1)
    h = shore + 40 * cliff * smoothstep(0.004, 0.035, L)
    hd_ = np.array([-200.0, 260.0]); hd_ /= np.linalg.norm(hd_); al_ = (x + 1480) * hd_[0] + (y + 730) * hd_[1]; ac_ = -(x + 1480) * hd_[1] + (y + 730) * hd_[0]
    h = h + 82 * np.exp(-(al_ / 72) ** 2 - (ac_ / 240) ** 2) * smoothstep(0.0, 0.05, L)          # rocky headland the coast road tunnels through
    m = 0.0
    for px, py, ph, pr in PEAKS:
        m = np.maximum(m, ph * np.exp(-((x - px) ** 2 + (y - py) ** 2) / pr ** 2))
    ridg = 1 - np.abs(fbm(x / 260, y / 260, 4, 20))
    m = m * (0.72 + 0.4 * ridg) + 55 * gauss(x, y, -100, 880, 950, 400) * (0.6 + 0.5 * ridg)
    dv = valley_tree().query(np.c_[x.ravel(), y.ravel()])[0].reshape(x.shape)
    m = m * (0.26 + 0.74 * smoothstep(100, 430, dv + 60 * fbm(x / 150, y / 150, 2, 27)))      # passes where the mountain roads run
    wx_ = x + 55 * fbm(x / 240, y / 240, 2, 63); wy_ = y + 55 * fbm(x / 240, y / 240, 2, 65)
    rdg = (1 - np.abs(fbm(wx_ / 190, wy_ / 190, 4, 67))) ** 2; far_ = smoothstep(120, 340, dv)
    m = m * (1 + 0.3 * (rdg - 0.5) * far_) + 58 * (rdg - 0.45) * smoothstep(40, 200, m) * far_      # sharp ridges and gullies away from the roads
    crag = (1 - np.abs(fbm(x / 85, y / 85, 3, 61))) - 0.6
    m = m + 26 * crag * smoothstep(60, 170, m)
    h = h + m * smoothstep(0.0, 0.17, L)
    h = h + 42 * gauss(x, y, -1350, 380, 650, 600) * (0.55 + 0.6 * fbm(x / 380, y / 380, 4, 12)) * cf
    dz = gauss(x, y, 1400, 640, 650, 500)
    h = h + (16 + 9 * np.abs(fbm(x / 160, y / 160, 3, 14))) * dz * cf
    for mx, my, mr, mh in MESAS:
        an_ = np.arctan2(y - my, x - mx)
        d = np.hypot(x - mx, y - my) + 22 * fbm(x / 70, y / 70, 2, 16) + mr * 0.09 * np.sin(an_ * 9 + mx) * np.sin(an_ * 4 + my)      # erosion gullies
        p_ = smoothstep(mr, mr * 0.66, d); p_ = (np.floor(p_ * 3) + smoothstep(0.3, 0.7, (p_ * 3) % 1)) / 3                          # three sandstone ledges
        h = h + mh * np.clip(p_, 0, 1) * (1 + 0.04 * fbm(x / 30, y / 30, 2, 17))
    h = h + 13 * gauss(x, y, 700, -900, 850, 330) * (1 + fbm(x / 330, y / 330, 3, 18)) * cf
    h = h + 4 * fbm(x / 170, y / 170, 3, 30) * cf
    # escarpment with the waterfalls north of the city
    ex0, ex1, ey0, ey1, eh = ESCARP
    wx = smoothstep(ex0 - 90, ex0 + 20, x) * smoothstep(ex1 + 110, ex1, x)
    h = h + eh * wx * smoothstep(ey0, ey1, y + 14 * fbm(x / 60, y / 60, 2, 21)) * smoothstep(900, 700, y)
    # flats
    for (cx, cy, rx, ry), zz, p in ((CITY, CITY_Z, 4), (CIRCUIT, CIRCUIT_Z, 3)):
        w = smoothstep(1.0, 0.8, sq(x, y, cx, cy, rx, ry, p)) * smoothstep(-0.01, 0.03, L)
        h = h * (1 - w) + zz * w
    w = smoothstep(HELI[2] + 60, HELI[2] - 10, np.hypot(x - HELI[0], y - HELI[1])) * smoothstep(0.0, 0.05, L)
    h = h * (1 - w) + HELI_Z * w
    if pads:                                               # level ground under the roundabouts
        for k, (cx, cy, rr) in enumerate(ROUNDABOUTS):
            if k not in _PADZ: _PADZ[k] = float(base_h(cx, cy, lakes=False, river=False, pads=False)) + PAD_LIFT[k]
            w = smoothstep(rr + 120, rr + 28, np.hypot(x - cx, y - cy)); h = h * (1 - w) + _PADZ[k] * w
    if pads:                                               # even hillside for the switchback road
        w = smoothstep(SERP[0], SERP[1], x) * smoothstep(SERP[3], SERP[2], x) * smoothstep(SERP[4], SERP[5], y) * smoothstep(SERP[7], SERP[6], y)
        h = h * (1 - w) + (_PADZ[0] + 9.0 + 0.26 * np.clip(y - 690, 0, 300)) * w
    # harbour bay and its channel to the open sea
    w = smoothstep(1.12, 0.84, sq(x, y, *BAY, 2.6) + 0.05 * fbm(x / 120, y / 120, 2, 23))
    h = h * (1 - w) + (-13) * w
    w = smoothstep(215, 105, np.abs(x - CHANNEL_X + 30 * fbm(y / 150, 0 * y, 2, 24))) * smoothstep(-880, -960, y)
    h = h * (1 - w) + (-15) * w
    if lakes:
        for lx, ly, lr in LAKES:
            lvl = lake_level(lx, ly)
            d = np.hypot(x - lx, y - ly) * (1 + 0.12 * fbm(x / 80, y / 80, 2, 25))
            floor = lvl - 1.0 - 3.5 * (1 - np.clip(d / lr, 0, 1) ** 2)
            h = np.where(d < lr, floor, np.maximum(h, lvl + 1.3 - np.maximum(0, d - lr - 28) * 0.45))
    if river:
        for R in get_rivers():
            d, i = R['tree'].query(np.c_[x.ravel(), y.ravel()]); d = d.reshape(x.shape); lv = R['lvl'][i].reshape(x.shape); k_ = R['hw'] / 9.5
            w = smoothstep(27 * k_ + 4, 11 * k_, d + 4 * k_ * fbm(x / 40, y / 40, 2, 71))
            h = h * (1 - w) + np.minimum(h, lv - 0.6 - 1.1 * k_) * w
    return np.maximum(h, SEA_FLOOR)


_RV = {}


def get_rivers():
    if not _RV:
        out = []
        for pts, hw in RIVERS:
            Pd = catmull(pts, False, 16); seg = np.linalg.norm(np.diff(Pd, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
            s = np.arange(0, cum[-1], 6.0); P = np.stack([np.interp(s, cum, Pd[:, 0]), np.interp(s, cum, Pd[:, 1])], 1)
            nat = base_h(P[:, 0], P[:, 1], river=False)
            k = np.ones(9) / 9; nat = np.convolve(np.pad(nat, 4, mode='edge'), k, mode='valid')
            lvl = np.maximum(np.minimum.accumulate(nat) - 0.9, 0.0)
            out.append(dict(xy=P, lvl=lvl, tree=cKDTree(P), hw=hw))
        _RV['all'] = out
    return _RV['all']


def get_river(): return get_rivers()[0]


_LVL = {}


def lake_level(lx, ly):
    k = (lx, ly)
    if k not in _LVL:
        a = np.linspace(0, 2 * np.pi, 16, endpoint=False)
        r = dict((l[:2], l[2]) for l in LAKES)[k]
        ring = base_h(lx + r * np.cos(a), ly + r * np.sin(a), lakes=False, river=False)
        _LVL[k] = float(max(np.median(ring) - 1.0, 4.0))
    return _LVL[k]


# ---------------------------------------------------------------- roads
TYPES = {'hwy': dict(w=14.0, g=0.055), 'road': dict(w=10.0, g=0.085), 'street': dict(w=12.0, g=0.04),
         'dirt': dict(w=7.0, g=0.105), 'circuit': dict(w=15.0, g=0.03), 'rbt': dict(w=9.0, g=0.03)}
SX = [-480, -320, -160, 0, 160, 320, 480]
SY = [-300, -160, -20, 120, 260]
ROADS = [
    ('Ring', 'hwy', True, [(1500, -960), (1100, -1110), (700, -1170), (300, -1190), (-100, -1180), (-400, -1130), (-560, -1110),
                           (-960, -1100), (-1180, -1040), (-1380, -860), (-1580, -600), (-1720, -300), (-1790, 50), (-1740, 400),
                           (-1560, 740), (-1250, 980), (-800, 1160), (-300, 1250), (200, 1250), (700, 1140), (1150, 960),
                           (1500, 760), (1760, 460), (1880, 80), (1870, -300), (1740, -680)]),
    ('West Avenue', 'road', False, [(-480, -20), (-800, -40), (-1150, -180), (-1480, -310), (-1720, -300)]),
    ('East Avenue', 'road', False, [(480, -20), (700, 25), (880, 45), (1000, 55), (1300, 70), (1700, 70), (1880, 80)]),
    ('South Road', 'road', False, [(160, -300), (330, -480), (440, -780), (380, -1000), (300, -1190)]),
    ('Canyon Road', 'road', False, [(480, 260), (700, 400), (900, 560)]),
    ('Peninsula Road', 'road', False, [(-1150, -180), (-1260, -480), (-1380, -860)]),
    ('Summit Pass', 'road', False, [(0, 260), (-30, 400), (-180, 480), (-400, 500), (-520, 580), (-420, 690), (-520, 800), (-440, 960), (-330, 1120), (-300, 1250)]),
    ('Skyline Road', 'road', False, [(-440, 960), (-250, 1000), (-100, 930), (-30, 830), (120, 720), (330, 740), (380, 900), (450, 1050), (700, 1140)]),
    ('Eagle Descent', 'road', False, [(330, 740), (600, 640), (900, 560)]),
    ('Dune Road', 'road', False, [(900, 560), (1200, 640), (1500, 760)]),
    ('Mesa Road', 'road', False, [(900, 560), (960, 300), (1000, 55)]),
    ('Dish Road', 'road', False, [(1200, 640), (1350, 520), (1500, 430), (1600, 330)]),
    ('Lake Trail', 'dirt', False, [(-1740, 400), (-1560, 330), (-1330, 270), (-1250, 300), (-1100, 250), (-880, 240), (-640, 140), (-480, 120)]),
    ('Pine Trail', 'dirt', False, [(-1250, 300), (-1280, 520), (-1230, 760), (-1250, 980)]),
    ('Farm Road', 'road', False, [(440, -780), (700, -760), (950, -830), (1200, -900), (1500, -960)]),
    ('Orchard Lane', 'dirt', False, [(700, -760), (760, -950), (950, -1050), (1100, -1110)]),
    ('Heliport Road', 'road', False, [(1500, -960), (1620, -1000), (1690, -1010)]),
    ('Lighthouse Road', 'road', False, [(-1180, -1040), (-1280, -1130), (-1340, -1215)]),
    ('Pit Access', 'road', False, [(880, 45), (890, -50), (950, -130)]),
    ('Circuit', 'circuit', True, [(950, -130), (1230, -118), (1500, -112), (1630, -180), (1640, -310), (1460, -292), (1250, -262),
                                  (1120, -335), (1250, -422), (1450, -445), (1585, -545), (1410, -605), (1150, -585),
                                  (965, -525), (885, -350)]),
    ('Mesa Trail', 'dirt', False, [(1600, 330), (1700, 380), (1760, 460)]),
    ('Arroyo Trail', 'dirt', False, [(1200, 640), (1285, 760), (1265, 880), (1150, 960)]),
    ('Serpentine', 'road', False, [(900, 560), (892, 630), (848, 688), (760, 712), (668, 738), (640, 745), (624, 756), (640, 767), (668, 774), (750, 796), (832, 820), (860, 827), (876, 838), (860, 849), (832, 856), (750, 878), (668, 902), (640, 909), (624, 920), (640, 931), (668, 938), (750, 960), (835, 984)]),
    ('Beach Flyover', 'road', False, [(1700, 70), (1785, 12), (1877, -62), (1962, -112), (2032, -142)]),
]
for _k, (_cx, _cy, _r) in enumerate(ROUNDABOUTS):
    ROADS.append((['Mesa Roundabout', 'Farm Roundabout'][_k], 'rbt', True, [(_cx + _r * np.cos(a), _cy + _r * np.sin(a)) for a in np.arange(8) * np.pi / 4]))
for _x in SX: ROADS.append(('Street N%d' % _x, 'street', False, [(_x, SY[0]), (_x, SY[-1])]))
for _y in SY: ROADS.append(('Street E%d' % _y, 'street', False, [(SX[0], _y), (SX[-1], _y)]))


def catmull(P, closed, per=40):
    P = np.asarray(P, float); n = len(P); out = []
    if len(P) == 2: return np.linspace(P[0], P[1], per + 1)
    tt = np.linspace(0, 1, per, endpoint=False)[:, None]
    for i in range(n if closed else n - 1):
        if closed: p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        else:
            p1, p2 = P[i], P[i + 1]
            p0 = P[i - 1] if i > 0 else 2 * p1 - p2
            p3 = P[i + 2] if i + 2 < n else 2 * p2 - p1
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * tt + (2 * p0 - 5 * p1 + 4 * p2 - p3) * tt ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * tt ** 3))
    if not closed: out.append(P[-1:])
    return np.vstack(out)


_VT = []


def valley_tree():
    if not _VT:
        pts = [catmull(p, c, 12) for n, t, c, p in ROADS if n in ('Summit Pass', 'Skyline Road', 'Eagle Descent', 'Canyon Road')]
        ring = catmull(ROADS[0][3], True, 12); pts.append(ring[(ring[:, 1] > 900)])
        _VT.append(cKDTree(np.vstack(pts)))
    return _VT[0]


def build_roads():
    """Returns list of road dicts and the global sample arrays."""
    roads = []; off = 0
    for name, typ, closed, pts in ROADS:
        dense = catmull(pts, closed)
        if closed: dense = np.vstack([dense, dense[:1]])
        seg = np.linalg.norm(np.diff(dense, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)]); Ln = cum[-1]
        n = max(2, int(round(Ln / STEP))); s = np.linspace(0, Ln, n + 1)
        xy = np.stack([np.interp(s, cum, dense[:, 0]), np.interp(s, cum, dense[:, 1])], 1)
        if closed: xy = xy[:-1]
        m = len(xy)
        if closed: tan = np.roll(xy, -1, 0) - np.roll(xy, 1, 0)
        else: tan = np.gradient(xy, axis=0)
        tan /= np.linalg.norm(tan, axis=1)[:, None]
        roads.append(dict(name=name, type=typ, closed=closed, xy=xy, tan=tan, left=np.stack([-tan[:, 1], tan[:, 0]], 1),
                          head=np.arctan2(tan[:, 1], tan[:, 0]), n=m, step=Ln / n, length=Ln, off=off,
                          w=TYPES[typ]['w'], g=TYPES[typ]['g']))
        off += m
    N = off
    XY = np.vstack([r['xy'] for r in roads]); rid = np.concatenate([np.full(r['n'], i) for i, r in enumerate(roads)])
    # graph edges along roads
    ea = []; eb = []; ec = []
    for r in roads:
        i = np.arange(r['n'] - (0 if r['closed'] else 1)) + r['off']
        j = (np.arange(r['n'] - (0 if r['closed'] else 1)) + 1) % r['n'] + r['off']
        ea.append(i); eb.append(j); ec.append(np.full(len(i), r['g'] * r['step']))
    # junction links: samples of different roads closer than 3.6 m, plus end points to nearest foreign sample
    tree = cKDTree(XY); pairs = tree.query_pairs(3.6, output_type='ndarray')
    pairs = pairs[rid[pairs[:, 0]] != rid[pairs[:, 1]]]
    nm_ = [r['name'] for r in roads]
    for fn_, on_ in FLY.items():
        a_, b_ = nm_.index(fn_), nm_.index(on_); ra, rb = rid[pairs[:, 0]], rid[pairs[:, 1]]; pairs = pairs[~(((ra == a_) & (rb == b_)) | ((ra == b_) & (rb == a_)))]
    extra = []
    for r in roads:
        if r['closed']: continue
        for e in (r['off'], r['off'] + r['n'] - 1):
            d, idx = tree.query(XY[e], k=12, distance_upper_bound=14.0)
            for dd, ii in zip(d, idx):
                if np.isfinite(dd) and rid[ii] != rid[e]: extra.append((e, ii)); break
    links = np.vstack([pairs, np.array(extra, int).reshape(-1, 2)]) if len(extra) else pairs
    ea.append(links[:, 0]); eb.append(links[:, 1]); ec.append(np.zeros(len(links)))
    ea = np.concatenate(ea); eb = np.concatenate(eb); ec = np.concatenate(ec)
    nat = base_h(XY[:, 0], XY[:, 1])
    t = np.maximum(nat, 3.5)
    water = nat < 1.0
    ringmask = (rid == 0) & water & (np.abs(XY[:, 0] - CHANNEL_X) < 420) & (XY[:, 1] < -900)
    t[water] = 7.0; t[ringmask] = 27.0
    inriv = np.zeros(N, bool)
    for RVd in get_rivers():
        dr_, ir_ = RVd['tree'].query(XY); m_ = (dr_ < RVd['hw'] + 3.0) & ~water; t[m_] = RVd['lvl'][ir_[m_]] + 2.6; inriv |= m_
    names = [r['name'] for r in roads]; flybr = np.zeros(N, bool)
    for fn_, on_ in FLY.items():                              # flyover: lift the deck over the road below
        fi = names.index(fn_); oi = names.index(on_); dd_ = cKDTree(XY[rid == oi]).query(XY[rid == fi])[0]
        idx_ = np.where(rid == fi)[0]; t[idx_[dd_ < 36]] = np.maximum(nat[idx_[dd_ < 36]], 3.5) + 8.6; flybr[idx_[dd_ < 27]] = True

    # slope-limited profile: closest heights to the natural ground with every graph edge within its grade limit (ADMM)
    import scipy.sparse as sp, scipy.sparse.linalg as spl
    M = len(ea); A = sp.csr_matrix((np.r_[np.ones(M), -np.ones(M)], (np.r_[np.arange(M), np.arange(M)], np.r_[ea, eb])), shape=(M, N))
    rho = 2.0; lu = spl.splu((sp.identity(N) + rho * (A.T @ A)).tocsc())
    z = t.copy(); d = np.clip(A @ z, -ec, ec); u = np.zeros(M)
    for it in range(40000):
        z = lu.solve(t + rho * (A.T @ (d - u)))
        Az = A @ z; dn = np.clip(Az + u, -ec, ec); u += Az - dn
        rp = np.linalg.norm(Az - dn); rd = rho * np.linalg.norm(A.T @ (dn - d)); d = dn
        if np.abs(Az - dn).max() < 3e-3 and rd < 0.05: break
        if it % 200 == 199 and (rp > 8 * rd or rd > 8 * rp):
            f = 2.0 if rp > rd else 0.5; rho *= f; u /= f
            lu = spl.splu((sp.identity(N) + rho * (A.T @ A)).tocsc())
    print('admm iterations', it, 'residual %.4f' % np.abs(Az - dn).max())
    # round off vertical kinks (graph smoothing, links weighted strongly)
    wgt = np.where(ec == 0, 6.0, 1.0)
    for _ in range(14):
        acc = np.zeros(N); cnt = np.zeros(N)
        np.add.at(acc, ea, z[eb] * wgt); np.add.at(acc, eb, z[ea] * wgt); np.add.at(cnt, ea, wgt); np.add.at(cnt, eb, wgt)
        z = 0.4 * z + 0.6 * acc / np.maximum(cnt, 1e-9)
    for _ in range(4):                                     # make linked samples exactly equal
        zm = 0.5 * (z[links[:, 0]] + z[links[:, 1]]); z[links[:, 0]] = zm; z[links[:, 1]] = zm
    junction = np.zeros(N, bool); junction[links.ravel()] = True
    # flags
    bridge = (nat < 1.0) | (z - nat > 13.0) | inriv | flybr
    tunnel = (nat - z > 27.0)
    for i, r in enumerate(roads):
        sl = slice(r['off'], r['off'] + r['n'])
        b = clean_mask(bridge[sl], r['closed'], min_run=3, grow=2)
        tn = clean_mask(tunnel[sl], r['closed'], min_run=12, grow=0) & ~b if r['type'] in ('hwy', 'road') else np.zeros(r['n'], bool)
        r['z'] = z[sl]; r['nat'] = nat[sl]; r['bridge'] = b; r['tunnel'] = tn; r['junction'] = junction[sl]; r['river'] = inriv[sl]
        bridge[sl] = b; tunnel[sl] = tn
    return roads, dict(XY=XY, Z=z, rid=rid, bridge=bridge, tunnel=tunnel, junction=junction, links=links, nat=nat, tree=tree)


def runs(mask, closed):
    """List of (start, length) runs of True."""
    n = len(mask); out = []
    if mask.all(): return [(0, n)]
    if not mask.any(): return []
    off = int(np.argmin(mask)) if closed else 0
    m = np.roll(mask, -off) if closed else mask
    i = 0
    while i < n:
        if m[i]:
            j = i
            while j < n and m[j]: j += 1
            out.append(((i + off) % n, j - i)); i = j
        else: i += 1
    return out


def clean_mask(mask, closed, min_run, grow):
    out = np.zeros(len(mask), bool); n = len(mask)
    for a, ln in runs(mask, closed):
        if ln >= min_run:
            idx = np.arange(a - grow, a + ln + grow)
            idx = idx % n if closed else idx[(idx >= 0) & (idx < n)]
            out[idx] = True
    return out


def build_terrain(roads, G):
    ax = np.linspace(X0, X1, NX); ay = np.linspace(Y0, Y1, NY)
    X, Y = np.meshgrid(ax, ay, indexing='xy')
    H0 = base_h(X, Y)
    dist, idx = G['tree'].query(np.c_[X.ravel(), Y.ravel()])
    dist = dist.reshape(X.shape); idx = idx.reshape(X.shape)
    hw = np.concatenate([np.full(r['n'], r['w'] / 2) for r in roads])
    # let embankments run a little under each bridge end and cuttings a little into each tunnel mouth, so no road floats or is buried
    solid = np.zeros(len(G['Z']), bool)
    for r in roads:
        def erode(m, k):
            o = m.copy()
            for q in range(1, k + 1):
                a_ = np.roll(m, q); b_ = np.roll(m, -q)
                if not r['closed']: a_[:q] = m[:q]; b_[-q:] = m[-q:]
                o &= a_ & b_
            return o
        br = np.where(r['river'], r['bridge'], erode(r['bridge'], 2)); tn = erode(r['tunnel'], 3)
        solid[r['off']:r['off'] + r['n']] = ~(br | tn)
    # soften the ground mask along each road so cuts ramp in near bridge ends
    gm = solid.astype(float)
    inner = hw[idx] + 8.0
    w = (1.0 - smoothstep(inner, inner + 62.0, dist)) * gm[idx]
    H = H0 * (1 - w) + (G['Z'][idx] - 0.55) * w
    dk, ik = G['tree'].query(np.c_[X.ravel(), Y.ravel()], k=10, distance_upper_bound=26.0)          # never stand above any road that passes close by
    ok_ = np.isfinite(dk); ik = np.where(ok_, ik, 0); near_ = ok_ & solid[ik] & (dk < hw[ik] + 8.0)
    cap = np.where(near_, G['Z'][ik] - 0.55, np.inf).min(1).reshape(X.shape); H = np.minimum(H, cap)
    return dict(X=X, Y=Y, H=H, H0=H0, dist=dist, idx=idx, ax=ax, ay=ay, onroad=(dist < hw[idx]) & solid[idx])


def sample_h(TR, x, y):
    fx = (np.asarray(x, float) - X0) / CELL; fy = (np.asarray(y, float) - Y0) / CELL
    fx = np.clip(fx, 0, NX - 1.001); fy = np.clip(fy, 0, NY - 1.001)
    ix = fx.astype(int); iy = fy.astype(int); u = fx - ix; v = fy - iy
    H = TR['H']
    return (H[iy, ix] * (1 - u) + H[iy, ix + 1] * u) * (1 - v) + (H[iy + 1, ix] * (1 - u) + H[iy + 1, ix + 1] * u) * v


if __name__ == '__main__':
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, time
    t0 = time.time(); roads, G = build_roads(); TR = build_terrain(roads, G); print('built in %.1fs' % (time.time() - t0))
    tot = 0
    for r in roads[:20]:
        g = np.abs(np.diff(r['z'])) / r['step']
        print('%-16s %-7s len %5.0f  z %5.1f..%5.1f  maxgrade %.3f  bridges %s tunnels %s  maxcut %.0f maxfill %.0f' % (
            r['name'], r['type'], r['length'], r['z'].min(), r['z'].max(), g.max(),
            [(a, round(l * r['step'])) for a, l in runs(r['bridge'], r['closed'])],
            [(a, round(l * r['step'])) for a, l in runs(r['tunnel'], r['closed'])], (r['nat'] - r['z']).max(), (r['z'] - r['nat']).max()))
    print('total road km %.1f samples %d links %d' % (sum(r['length'] for r in roads) / 1000, len(G['Z']), len(G['links'])))
    print('terrain', TR['H'].min(), TR['H'].max(), 'lake levels', {k: round(v, 1) for k, v in _LVL.items()})
    fig, ax = plt.subplots(figsize=(20, 14))
    ax.imshow(TR['H'], origin='lower', extent=[X0, X1, Y0, Y1], cmap='terrain', vmin=-90, vmax=420)
    ax.contour(TR['X'], TR['Y'], TR['H'], levels=[0.0], colors='b', linewidths=1)
    col = {'hwy': 'k', 'road': '#444', 'street': '#666', 'dirt': '#7a4a1a', 'circuit': 'm'}
    for r in roads:
        p = r['xy']; ax.plot(p[:, 0], p[:, 1], '-', color=col.get(r['type'], 'k'), lw=2 if r['type'] == 'hwy' else 1.2)
        ax.plot(p[r['bridge'], 0], p[r['bridge'], 1], 'r.', ms=3); ax.plot(p[r['tunnel'], 0], p[r['tunnel'], 1], 'c.', ms=4)
    for lx, ly, lr in LAKES: ax.add_patch(plt.Circle((lx, ly), lr, color='deepskyblue'))
    for nm, cx, cy, rx, ry in REGIONS: ax.text(cx, cy, nm, ha='center', color='w', fontsize=12, weight='bold')
    plt.tight_layout(); plt.savefig('/home/claude/isle/out/layout.png', dpi=50)

"""Stage 7 for Aurelia Island: junction aprons and stop lines, embankments, tunnel portal masonry, modelled cars,
kerbside parking, rooftops, bus shelters, and the extra planting (hedgerows, crops, scree, desert rock, undergrowth)."""
import math
import numpy as np
from scipy.spatial import cKDTree
import isle_data as K
import isle_lib as L
import isle_arch as AR
from isle_lib import lin, box, beam, cyl, tube
from isle_data import smoothstep

rng = np.random.default_rng(2026)
STAT = dict(junction_aprons=0, stop_lines=0, kerbside_cars=0, bus_shelters=0, roof_kits=0, hedgerow=0, crops=0, scree=0, desert_rock=0, desert_plants=0, undergrowth=0, embankment_m=0)
CAR_COLS = [lin(c) for c in ('#b3241d', '#1f3f7a', '#e8e8e4', '#2b2d31', '#8a8f96', '#d9a521', '#2f6b45', '#f4f4f0', '#5a1f1f', '#3b8fa3', '#c9c9c4', '#101114')]
GLASS = lin('#141c24'); TYRE = lin('#0d0d0d')


_PARK_HEX = ('#b3241d', '#1f3f7a', '#e8e8e4', '#2b2d31', '#8a8f96', '#d9a521', '#2f6b45', '#f4f4f0', '#5a1f1f', '#3b8fa3', '#c9c9c4', '#101114')


def car_mesh(buf, x, y, z, yaw, col, kind=0):
    """Parked car: an instance of the modelled traffic cars (isle_traffic), with its own paint colour."""
    import isle_props as KP
    h = int(abs(x * 13.7 + y * 7.1)) % 997
    name = ('tcar_b', 'tcar_a', 'tcar_c')[kind % 3]
    if name == 'tcar_b' and h % 3 == 0: name = 'tcar_d'                       # some saloons become SUVs
    hx = _PARK_HEX[h % len(_PARK_HEX)]; c = tuple(int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5))
    KP.KIT.append((name, x, y, z, yaw, c))


_LOW = {}
def car_mesh_low(buf, x, y, z, yaw, col, kind=0):
    """Parked car: the Aurelia car generator's low-detail body (lofted, glazed cabin, lamps, mirrors, wheels), vertex-coloured."""
    import isle_car as CAR
    if kind not in _LOW: _LOW[kind] = CAR.low_mesh(kind, (1.0, 0.0, 1.0), 0.22, 0.2)
    V, F, Cc = _LOW[kind]; paint = (Cc[:, 0] > 0.99) & (Cc[:, 1] < 0.01) & (Cc[:, 2] > 0.99)
    Cc = np.where(paint[:, None], np.asarray(col, float)[None, :], Cc); c, s = math.cos(yaw), math.sin(yaw)
    W = np.c_[x + V[:, 0] * c - V[:, 1] * s, y + V[:, 0] * s + V[:, 1] * c, z + V[:, 2]]
    buf.add((W, F), Cc, solid=False)


def car_mesh_old(buf, x, y, z, yaw, col, kind=0):
    """Car body lofted from cross-sections (bonnet, cabin, boot), glazed cabin, lamps and four wheels. kind: 0 saloon, 1 hatchback, 2 van."""
    ln, wd = (4.5, 1.8) if kind == 0 else ((4.1, 1.76) if kind == 1 else (4.9, 1.95)); hl = ln / 2
    if kind == 0:   st = [(-hl, .46, .70, .74, .80), (-hl + .12, .30, .86, .90, .96), (-hl + .95, .28, .92, .95, 1.0), (-hl + 1.45, .28, .93, 1.40, .78), (0.25, .28, .94, 1.44, .80), (0.95, .28, .92, .98, .96), (hl - .15, .30, .84, .86, .95), (hl, .44, .66, .70, .82)]
    elif kind == 1: st = [(-hl, .46, .74, .9, .80), (-hl + .1, .30, .92, 1.38, .80), (-hl + .5, .28, .94, 1.46, .80), (0.35, .28, .95, 1.47, .80), (1.0, .28, .92, 1.0, .96), (hl - .15, .30, .84, .86, .95), (hl, .44, .66, .70, .82)]
    else:           st = [(-hl, .46, .80, 1.7, .9), (-hl + .1, .32, 1.0, 1.9, .9), (0.9, .32, 1.0, 1.9, .9), (1.5, .32, .98, 1.5, .86), (hl - .2, .32, .9, .98, .95), (hl, .46, .7, .76, .84)]
    c, s = math.cos(yaw), math.sin(yaw); hw = wd / 2

    def Wd(a, b, h): return (x + a * c - b * s, y + a * s + b * c, z + h)
    V = []; F = []; Cc = []

    cen = np.array([x, y, z + 0.75])

    def quad(p, colr):
        p = [np.asarray(q, float) for q in p]
        if np.dot(np.cross(p[1] - p[0], p[2] - p[0]), (p[0] + p[2]) / 2 - cen) < 0: p = p[::-1]
        n = len(V); V.extend(p); F.extend([(n, n + 1, n + 2), (n, n + 2, n + 3)]); Cc.extend([colr] * 4)
    for (a0, zb0, zs0, zt0, k0), (a1, zb1, zs1, zt1, k1) in zip(st[:-1], st[1:]):
        cabin = max(zt0, zt1) > 1.2; gl = GLASS if cabin else col
        for sg in (-1, 1):
            quad([Wd(a0, sg * hw, zb0), Wd(a1, sg * hw, zb1), Wd(a1, sg * hw, zs1), Wd(a0, sg * hw, zs0)][::sg], col * 0.94)                       # flank
            quad([Wd(a0, sg * hw, zs0), Wd(a1, sg * hw, zs1), Wd(a1, sg * hw * k1, zt1), Wd(a0, sg * hw * k0, zt0)][::sg], gl if cabin and min(zt0, zt1) > 1.2 else (GLASS if cabin else col))
        quad([Wd(a0, -hw * k0, zt0), Wd(a1, -hw * k1, zt1), Wd(a1, hw * k1, zt1), Wd(a0, hw * k0, zt0)][::-1], GLASS if (cabin and abs(zt1 - zt0) > 0.3) else col * 1.05)   # top: bonnet, screens, roof
    for a_, zb_, zs_, zt_, k_, sg in ((st[0][0], st[0][1], st[0][2], st[0][3], st[0][4], -1), (st[-1][0], st[-1][1], st[-1][2], st[-1][3], st[-1][4], 1)):
        quad([Wd(a_, -hw, zb_), Wd(a_, hw, zb_), Wd(a_, hw * k_, zt_), Wd(a_, -hw * k_, zt_)][::-sg], col * 0.9)
        lampc = lin('#f6f1dc') if sg > 0 else lin('#a81410')
        for b_ in (-hw * 0.62, hw * 0.62): quad([Wd(a_ + sg * 0.012, b_ - .22, zs_ - .12), Wd(a_ + sg * 0.012, b_ + .22, zs_ - .12), Wd(a_ + sg * 0.012, b_ + .22, zs_ - 0.0), Wd(a_ + sg * 0.012, b_ - .22, zs_ - 0.0)][::-sg], lampc)
    V = np.array(V); F = np.array(F); buf.add((V, F), np.array(Cc), solid=False)
    for a_ in (-hl + 0.82, hl - 0.86):
        for b_ in (-hw + 0.1, hw - 0.1):
            p0 = np.array(Wd(a_, b_ - 0.11, 0.33)); p1 = np.array(Wd(a_, b_ + 0.11, 0.33)); ax = (p1 - p0) / 0.22; an = np.arange(8) * np.pi / 4
            u = np.array([c, s, 0.0]); ring = np.outer(np.cos(an), u) * 0.33 + np.outer(np.sin(an), [0, 0, 0.33])
            Vw = np.vstack([p0 + ring, p1 + ring, [p0], [p1]]); i = np.arange(8); j = (i + 1) % 8
            Fw = np.vstack([np.c_[i, j, 8 + j], np.c_[i, 8 + j, 8 + i], np.c_[j, i, np.full(8, 16)], np.c_[8 + i, 8 + j, np.full(8, 17)]])
            buf.add((Vw, Fw), np.vstack([np.tile(TYRE, (16, 1)), [lin('#9a9da1')], [lin('#9a9da1')]]), solid=True)


def roads_extra(C, roads, G, Rd, Mk):
    """Aprons with rounded corners where a road ends on another, and a stop line across the joining road."""
    rid = G['rid']; XY = G['XY']; tree = G['tree']; WH = lin('#eeeeea'); up = np.array([0, 0, 1.0])
    for ri, r in enumerate(roads):
        if r['closed'] or r['type'] in ('dirt', 'circuit'): continue
        for e, sgn in ((0, -1), (r['n'] - 1, 1)):
            if not r['junction'][e] or r['bridge'][e] or r['tunnel'][e]: continue
            d, idx = tree.query(r['xy'][e], k=24); other = [j for j, dd in zip(idx, d) if rid[j] != ri and dd < 9]
            if not other: continue
            B = roads[rid[other[0]]]
            if B['type'] == 'dirt': continue
            hwA, hwB = r['w'] / 2, B['w'] / 2; tA = r['tan'][e] * sgn; nA = np.array([-tA[1], tA[0]]); pe = r['xy'][e]; z = float(r['z'][e]) + 0.025; R = 5.5 if r['type'] != 'street' else 3.5
            for sg in (-1, 1):
                Cn = pe - tA * hwB + nA * sg * hwA; O = pe - tA * (hwB + R) + nA * sg * (hwA + R); th = np.linspace(0, np.pi / 2, 7)
                arc = O + np.outer(np.cos(th), -nA * sg * R) + np.outer(np.sin(th), tA * R)
                V = np.vstack([np.r_[Cn, z], np.c_[arc, np.full(7, z)]]); F = np.array([(0, 1 + k, 2 + k) for k in range(6)])
                if np.cross(V[1] - V[0], V[2] - V[0])[2] < 0: F = F[:, ::-1]
                Rd.add((V, F), np.ones(3) * 0.97, solid=False, uv=V[:, :2] / 8.0)
                STAT['junction_aprons'] += 1
            if B['type'] == 'rbt':                                # art sheet 08: give-way at roundabouts, a broken double line and a triangle
                for off_ in (1.0, 1.5):
                    for k_ in range(int(2 * (hwA - 0.3) / 0.9)):
                        o0 = -(hwA - 0.3) + k_ * 0.9; a = pe - tA * (hwB + off_); b = a - tA * 0.3
                        Vq = np.array([np.r_[a + nA * o0, z + 0.04], np.r_[a + nA * (o0 + 0.6), z + 0.04], np.r_[b + nA * (o0 + 0.6), z + 0.04], np.r_[b + nA * o0, z + 0.04]]); Fq = np.array([(0, 1, 2), (0, 2, 3)])
                        if np.cross(Vq[1] - Vq[0], Vq[2] - Vq[0])[2] < 0: Fq = Fq[:, ::-1]
                        Mk.add((Vq, Fq), WH, solid=False)
                for sgn_ in (-1, 1):
                    c_ = pe - tA * (hwB + 5.5) + nA * sgn_ * hwA * 0.5; Vt = np.array([np.r_[c_ - nA * 0.7 + tA * 1.2, z + 0.04], np.r_[c_ + nA * 0.7 + tA * 1.2, z + 0.04], np.r_[c_ - tA * 1.6, z + 0.04]]); Ft = np.array([(0, 1, 2)])
                    if np.cross(Vt[1] - Vt[0], Vt[2] - Vt[0])[2] < 0: Ft = Ft[:, ::-1]
                    Mk.add((Vt, Ft), WH, solid=False)
                STAT['stop_lines'] += 1; continue
            a = pe - tA * (hwB + 1.0); b = pe - tA * (hwB + 1.45)
            Vq = np.array([np.r_[a - nA * (hwA - 0.3), z + 0.04], np.r_[a + nA * (hwA - 0.3), z + 0.04], np.r_[b + nA * (hwA - 0.3), z + 0.04], np.r_[b - nA * (hwA - 0.3), z + 0.04]])
            Fq = np.array([(0, 1, 2), (0, 2, 3)])
            if np.cross(Vq[1] - Vq[0], Vq[2] - Vq[0])[2] < 0: Fq = Fq[:, ::-1]
            Mk.add((Vq, Fq), WH, solid=False); STAT['stop_lines'] += 1


def portal_masonry(BT, arch_pts, out_dir, left, wall_h, hw):
    """Stone arch ring, pilasters and a string course on a tunnel headwall. arch_pts: (9, 3) along the arch; out_dir: unit vector pointing out of the tunnel."""
    stone = lin('#b9b2a2'); dk = lin('#8d877a'); o = np.array([out_dir[0], out_dir[1], 0.0]) * 0.22; A = np.asarray(arch_pts, float); cen = A.mean(0)
    for k in range(len(A) - 1):
        a, b = A[k], A[k + 1]; da = (a - cen); db = (b - cen); da[2] *= 1.0; a2 = a + da / np.linalg.norm(da) * 0.75; b2 = b + db / np.linalg.norm(db) * 0.75
        V = np.array([a + o, b + o, b2 + o, a2 + o, a, b, b2, a2]); F = np.array([(0, 1, 2), (0, 2, 3), (3, 2, 6), (3, 6, 7), (0, 3, 7), (0, 7, 4), (1, 5, 6), (1, 6, 2)])
        BT.add((V, F), stone if k % 2 else dk * 1.12, solid=True)
    base = A[0].copy(); base[2] = min(A[0][2], A[-1][2]); mid = (A[0] + A[-1]) / 2; l3 = np.array([left[0], left[1], 0.0])
    for sg in (-1, 1):
        p = mid + l3 * sg * (hw + 3.4) + o * 0.5; BT.add(box(p[0], p[1], base[2] - 1.0, 1.3, 1.3, min(wall_h, 12.5) + 1.0, math.atan2(left[1], left[0])), stone)
        BT.add(box(p[0], p[1], base[2] + min(wall_h, 12.5), 1.7, 1.7, 0.35, math.atan2(left[1], left[0])), dk)
    zc = base[2] + 8.9; p0 = mid - l3 * (hw + 3.4) + o * 0.5; p1 = mid + l3 * (hw + 3.4) + o * 0.5
    q0 = mid - l3 * (hw + 14.6) + o * 0.3; q1 = mid + l3 * (hw + 14.6) + o * 0.3                  # masonry courses across the whole headwall
    for zz in np.arange(base[2] + 8.9, base[2] + wall_h - 0.6, 2.3): BT.add(beam((q0[0], q0[1], zz), (q1[0], q1[1], zz), 0.28, 0.22), dk if int(zz) % 2 else stone)
    for a_ in np.arange(-(hw + 12), hw + 12.1, 6.0):
        if abs(a_) > hw + 4.5: p = mid + l3 * a_ + o * 0.3; BT.add(box(p[0], p[1], base[2] - 1.0, 0.7, 0.5, wall_h + 1.0, math.atan2(left[1], left[0])), dk * 1.05)


def city(C):
    S, PR, Sm, roads = C.S, C.PR, C.Sm, C.roads; cz = K.CITY_Z; TR = C.TR
    # ---- rooftops of the mid-rise blocks: parapet, stair head, tank or plant, solar rows
    for kind, x, y, sx, sy, h, yaw, z in C.bld:
        if kind != 'mid': AR.contact(C, x, y, sx + 5, sy + 5, yaw, 3.2)
        if kind != 'mid' or min(sx, sy) < 9: continue
        c, s = math.cos(yaw), math.sin(yaw); zr = z + h + 0.58
        def loc(a, b): return (x + a * c - b * s, y + a * s + b * c)
        pc = lin('#cfcabd') * rng.uniform(0.85, 1.05)
        for a, b, wx, wy in ((0, sy / 2 + 0.1, sx + 0.5, 0.3), (0, -sy / 2 - 0.1, sx + 0.5, 0.3), (sx / 2 + 0.1, 0, 0.3, sy + 0.5), (-sx / 2 - 0.1, 0, 0.3, sy + 0.5)):
            p = loc(a, b); S.add(box(p[0], p[1], zr, wx, wy, 0.95, yaw), pc)
        p = loc(-sx / 4, sy / 5); S.add(box(p[0], p[1], zr, 3.4, 2.8, 2.7, yaw), lin('#b3aea2')); S.add(box(p[0], p[1], zr + 2.7, 3.8, 3.2, 0.18, yaw), lin('#5b5d61'))
        q = loc(-sx / 4 + 1.72, sy / 5); S.add(box(q[0], q[1], zr, 0.06, 1.0, 2.05, yaw), lin('#30363d'))
        u = rng.random()
        if u < 0.4:                                               # water tank on a frame
            p = loc(sx / 4, -sy / 5)
            for da, db in ((-.9, -.9), (.9, -.9), (.9, .9), (-.9, .9)): q = loc(sx / 4 + da, -sy / 5 + db); S.add(box(q[0], q[1], zr, .14, .14, 1.6, yaw), lin('#4c5157'))
            S.add(cyl(p[0], p[1], zr + 1.6, 1.35, 1.35, 2.3, 12), lin('#8a6a4a')); S.add(L.cone(p[0], p[1], zr + 3.9, 1.45, 0.7, 12), lin('#5b5d61'))
        elif u < 0.75 and sx > 14:                                # solar rows tilted south
            for k in range(int((sx / 2 - 2) / 2.2)):
                p = loc(1.5 + k * 2.2, -sy / 5); Vq = np.array([(p[0] - 0.9, p[1] - 0.55, zr + 0.25), (p[0] + 0.9, p[1] - 0.55, zr + 0.25), (p[0] + 0.9, p[1] + 0.55, zr + 0.95), (p[0] - 0.9, p[1] + 0.55, zr + 0.95)])
                S.add((Vq, np.array([(0, 1, 2), (0, 2, 3)])), lin('#16243a'), solid=False); S.add((Vq, np.array([(0, 2, 1), (0, 3, 2)])), lin('#6a6d70'), solid=False)
        STAT['roof_kits'] += 1
    # ---- cars parked along the kerb, bus shelters
    okc = lambda p: abs(K.sample_h(TR, p[0], p[1]) - (cz - 0.55)) < 1.2 or True
    for r in roads:
        if r['type'] != 'street': continue
        hw = r['w'] / 2; n = r['n']; jm = r['junction'].copy()
        for k in range(1, 6): jm[k:] |= r['junction'][:-k]; jm[:-k] |= r['junction'][k:]
        i = 3
        while i < n - 3:
            if not jm[i] and not r['bridge'][i] and rng.random() < 0.16:
                sg = 1 if rng.random() < 0.5 else -1; p = r['xy'][i] + r['left'][i] * sg * (hw - 1.15); yaw = float(r['head'][i]) + (0 if sg < 0 else math.pi)
                car_mesh(Sm, p[0], p[1], float(r['z'][i]) + 0.02, yaw, CAR_COLS[rng.integers(len(CAR_COLS))] * rng.uniform(0.85, 1.05), int(rng.choice([0, 0, 1, 1, 2])))
                C.obst.append([p[0], -p[1], 2.3, 0.95, float(r['head'][i])]); STAT['kerbside_cars'] += 1; i += 1
            i += 1
        if r['name'].startswith('Street E'):
            for i in range(26, n - 10, 52):
                if jm[i]: continue
                sg = 1 if (i // 52) % 2 else -1; p = r['xy'][i] + r['left'][i] * sg * (hw + 2.7); hd = float(r['head'][i]); z = float(K.sample_h(TR, p[0], p[1])); z = max(z, cz + 0.16)
                import isle_props as KP; l = r['left'][i] * sg; KP.KIT.append(('shelter', p[0] + l[0] * 0.2, p[1] + l[1] * 0.2, z, math.atan2(-l[1], -l[0])))   # open side toward the road
                STAT['bus_shelters'] += 1


def circuit(C):
    """Racing circuit dressing: tyre walls on the outside of corners, sponsor boards along the straights."""
    r = next(q for q in C.roads if q['name'] == 'Circuit'); S = C.S; hw = r['w'] / 2; n = r['n']; cv = r.get('curv', np.zeros(n))
    ob = np.array([(o[0], -o[1]) for o in C.obst] + [(o[0], -o[1]) for o in C.circ]); ot = cKDTree(ob); cols = [lin(c) for c in ('#c5261f', '#eeeeea')]
    brd = [lin(c) for c in ('#1f4f8a', '#c98a1c', '#1f6b4a', '#a3271f', '#22262b', '#e8e8e4')]; nt = nb = 0
    for i in range(n):
        j = (i + 1) % n; out = -np.sign(cv[i]) if abs(cv[i]) > 1 / 240 else 0
        if out:
            p0 = C.P(r, i, out * (hw + 12.5)); p1 = C.P(r, j, out * (hw + 12.5))
            if ot.query(p0[:2])[0] > 16:
                for tier in (0, 1): S.add(beam(p0 + (0, 0, 0.2 + tier * 0.5), p1 + (0, 0, 0.2 + tier * 0.5), 0.9, 0.48), cols[(i + tier) % 2])
                nt += 1
        elif i % 4 == 0:
            for sg in (-1, 1):
                p0 = C.P(r, i, sg * (hw + 9.5)); p1 = C.P(r, (i + 2) % n, sg * (hw + 9.5))
                if ot.query(p0[:2])[0] > 22 and ot.query(p1[:2])[0] > 22:
                    c_ = brd[(i // 4 + (sg > 0)) % len(brd)]; S.add(beam(p0 + (0, 0, 0.75), p1 + (0, 0, 0.75), 0.12, 1.1), c_); S.add(beam(p0 * 0.75 + p1 * 0.25 + (0, 0, 0.75), p0 * 0.25 + p1 * 0.75 + (0, 0, 0.75), 0.16, 0.45), lin('#f4f1e8') if c_[0] < 0.6 else lin('#22262b')); nb += 1
    STAT['tyre_wall_m'] = nt * 5; STAT['sponsor_boards'] = nb


def scatter(C):
    """Extra planting, all as instances: hedgerows on field boundaries, crop rows near roads, scree, desert rock and scrub, forest undergrowth."""
    TR = C.TR; roads = C.roads; G = C.G; inst = C.inst
    hwv = np.concatenate([np.full(r['n'], r['w'] / 2) for r in roads])
    ob = np.array([(o[0], -o[1], math.hypot(o[2], o[3]) + 2.5) for o in C.obst] + [(o[0], -o[1], o[2] + 2.5) for o in C.circ] + [(q[0], q[1], q[2]) for q in C.noveg if q[2] > 0]); ot = cKDTree(ob[:, :2])
    RV = K.get_rivers()

    def field(x, y):
        ci = (np.clip(((y - K.Y0) / K.CELL + .5).astype(int), 0, K.NY - 1), np.clip(((x - K.X0) / K.CELL + .5).astype(int), 0, K.NX - 1)); return C.FIELD[ci]

    def ok(P, margin):
        h = K.sample_h(TR, P[:, 0], P[:, 1]); d, i = G['tree'].query(P); m = (h > 2.6) & (d > hwv[i] + margin)
        dd, ii = ot.query(P, k=3); m &= (dd > ob[ii, 2]).all(1)
        for lx, ly, lr in K.LAKES: m &= np.hypot(P[:, 0] - lx, P[:, 1] - ly) > lr + 5
        for R_ in RV: m &= R_['tree'].query(P)[0] > R_['hw'] + 3.5
        sl = np.hypot(K.sample_h(TR, P[:, 0] + 5, P[:, 1]) - h, K.sample_h(TR, P[:, 0], P[:, 1] + 5) - h) / 5
        return m, h, sl, d - hwv[i]
    def rnd(n): return np.c_[rng.uniform(K.X0 + 60, K.X1 - 60, n), rng.uniform(K.Y0 + 60, K.Y1 - 60, n)]
    # hedgerows along the long sides of the field strips
    th = 0.35; ct, st = math.cos(th), math.sin(th); pts = []
    for iu in range(-40, 41):
        v = np.arange(-3600, 3600, 3.0); u = np.full(len(v), iu * 90.0) + rng.normal(0, 0.25, len(v)); pts.append(np.c_[u * ct - v * st, u * st + v * ct])
    P = np.vstack(pts); P = P[(np.abs(P[:, 0]) < K.X1 - 80) & (np.abs(P[:, 1]) < K.Y1 - 80)]
    nx_, ny_ = ct * 7, st * 7; m = field(P[:, 0] + nx_, P[:, 1] + ny_) | field(P[:, 0] - nx_, P[:, 1] - ny_); P = P[m]
    m, h, sl, dr = ok(P, 6.0); P = P[m & (sl < 0.25) & (rng.random(len(P)) < 0.82)]; h = K.sample_h(TR, P[:, 0], P[:, 1])
    for k, (p, z) in enumerate(zip(P[:6500], h)):
        if k % 17 == 5: g = rng.uniform(.8, 1.0); inst.append((('oak', 'oak_b')[k % 2], p[0], p[1], z - 0.25, rng.uniform(0.6, 0.95), g, g, g * 0.9))
        else: g = rng.uniform(.85, 1.05); inst.append(('bush', p[0], p[1], z - 0.1, rng.uniform(1.25, 1.9), g * 0.9, g, g * 0.72))
    STAT['hedgerow'] = min(len(P), 4200)
    # crop rows in the fields beside roads
    P = rnd(260000); P = P[field(P[:, 0], P[:, 1])]; m, h, sl, dr = ok(P, 9.0); P = P[m & (dr < 75) & (sl < 0.2)][:5200]
    u = (P[:, 0] * ct + P[:, 1] * st); v = (-P[:, 0] * st + P[:, 1] * ct); u = np.round(u / 1.6) * 1.6; P = np.c_[u * ct - v * st, u * st + v * ct]; h = K.sample_h(TR, P[:, 0], P[:, 1])
    cell = (np.floor(u / 90) * 7 + np.floor(v / 60) * 13).astype(int) % 3
    for p, z, cl in zip(P, h, cell):
        tint = ((1.0, 0.86, 0.42), (0.75, 1.0, 0.55), (1.0, 0.95, 0.6))[cl]; inst.append(('grass_tall', p[0], p[1], z, rng.uniform(0.8, 1.15), *tint))
    STAT['crops'] = len(P)
    # scree and boulders on steep mountain ground
    P = rnd(220000); B = K.biomes(P[:, 0], P[:, 1]); m, h, sl, dr = ok(P, 9.0); sel = m & (sl > 0.42) & (sl < 1.2) & (h > 30) & (B['desert'] < 0.4) & (B['city'] < 0.3); P = P[sel][:1500]; h = h[sel][:1500]
    for k, (p, z) in enumerate(zip(P, h)):
        sc = rng.uniform(0.45, 1.1) if rng.random() < 0.8 else rng.uniform(1.4, 3.0); g = rng.uniform(.75, 1.05); sn = 1.3 if z > 150 else 1.0
        inst.append((('rock', 'rock_b', 'rock_c')[k % 3], p[0], p[1], z - sc * 0.15, sc, g * sn, g * sn, g * sn))
    STAT['scree'] = len(P)
    # desert: sandstone blocks and spires, dry scrub, more cactus
    P = rnd(160000); B = K.biomes(P[:, 0], P[:, 1]); m, h, sl, dr = ok(P, 8.0); sel = m & (B['desert'] > 0.6) & (h > 4); P = P[sel]; h = h[sel]; sl = sl[sel]
    nr = 0
    for k, (p, z, s_) in enumerate(zip(P[:2100], h, sl)):
        u = rng.random(); g = rng.uniform(.8, 1.08)
        if u < 0.2 and nr < 430: sc = rng.uniform(0.6, 2.2) if rng.random() < 0.85 else rng.uniform(2.6, 4.5); inst.append(('sandstone', p[0], p[1], z - sc * 0.18, sc, g, g, g)); nr += 1
        elif u < 0.24 and s_ < 0.3: sc = rng.uniform(1.4, 3.6); inst.append(('sandstone_spire', p[0], p[1], z - 0.5, sc, g, g, g)); nr += 1
        elif u < 0.36 and s_ < 0.35: inst.append((('cactus', 'cactus_b')[k % 2], p[0], p[1], z + 0.25, rng.uniform(0.55, 1.2), g, g, g)); STAT['desert_plants'] += 1
        elif s_ < 0.5: inst.append(('bush', p[0], p[1], z - 0.05, rng.uniform(0.45, 0.85), 1.0 * g, 0.86 * g, 0.5 * g)); STAT['desert_plants'] += 1
    STAT['desert_rock'] = nr
    # forest undergrowth
    P = rnd(200000); B = K.biomes(P[:, 0], P[:, 1]); m, h, sl, dr = ok(P, 6.0); sel = m & (B['forest'] > 0.45) & (sl < 0.5) & (h < 120); P = P[sel]; h = h[sel]; dr = dr[sel]
    for k, (p, z, d_) in enumerate(zip(P[:4200], h, dr)):
        g = rng.uniform(.6, .9)
        if k % 3 == 0 or d_ > 90: inst.append(('bush', p[0], p[1], z - 0.05, rng.uniform(0.55, 1.05), g * 0.8, g, g * 0.65))
        elif d_ < 90: inst.append(('grass_tall', p[0], p[1], z, rng.uniform(0.7, 1.2), 0.55, 0.9, 0.45))
    STAT['undergrowth'] = min(len(P), 4200)
    L.STATS['stage7'] = dict(STAT)

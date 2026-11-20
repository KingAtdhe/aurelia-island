"""Scenery for Aurelia Island: bridge, city, stadium, harbour, circuit, village, desert, mountains, forest, coast, heliport, plants."""
import math, bpy
import numpy as np
from scipy.spatial import cKDTree
import isle_data as K
import isle_lib as L
from isle_lib import lin, box, beam, cyl, cone, tube, sphere, roof, lathe, rot_x, rot_z, Buf, compact, make_obj
from isle_data import smoothstep, fbm

rng = L.rng


import isle_arch as AR


def build(C):
    S, Sm, FA, FB, D, Rk, Mk, M = C.S, C.Sm, C.FA, C.FB, C.V, C.Rk, C.Mk, C.M
    H = C.hgt; P = C.P; roads = C.roads; TR = C.TR
    CONC, STEEL, WHITE, RED, DARK = (C.col[k] for k in ('CONC', 'STEEL', 'WHITE', 'RED', 'DARK'))
    BLUE = lin('#2b5fae'); YEL = lin('#f2c230'); GLASS = lin('#5f8fb5'); WOOD = lin('#8a6a48'); TERRA = lin('#a8452d')
    R = {r['name']: r for r in roads}
    C.plats = []; park_trees = []
    rd = lambda x, y: float(C.G['tree'].query([x, y])[0])
    def ob(x, y, sx, sy, yaw=0.0): C.obst.append([x, -y, sx / 2, sy / 2, yaw])
    def oc(x, y, r): C.circ.append([x, -y, r])
    def nov(x, y, r): C.noveg.append((x, y, r))
    def plat(x, y, sx, sy, yaw, top): C.plats.append([x, -y, sx / 2, sy / 2, yaw, top])
    def lm(name, p): C.landmarks.append((name, np.asarray(p, float)))

    def facade(buf, x, y, z, sx, sy, h, yaw, color, bay=4.2, floor=3.6):
        c, s = math.cos(yaw), math.sin(yaw)
        cs = [(-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2)]
        W = [(x + a * c - b * s, y + a * s + b * c) for a, b in cs]
        for k in range(4):
            p0, p1 = W[k], W[(k + 1) % 4]; ln = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            nu = max(1, round(ln / bay)); nv = max(1, round(h / floor))
            Vq = np.array([(p0[0], p0[1], z), (p1[0], p1[1], z), (p1[0], p1[1], z + h), (p0[0], p0[1], z + h)])
            buf.add((Vq, np.array([(0, 1, 2), (0, 2, 3)])), color, solid=False, uv=np.array([(0, 0), (nu, 0), (nu, nv), (0, nv)], float))

    def house(x, y, sx, sy, sz, yaw, wall, rf, rh=None, found=2.0):
        z = H(x, y)
        import isle_props as KP, isle_houses as HS                                   # modelled house from the kit, picked by size
        import isle_country_hq as CQ                                                 # art sheet 05: Adriatic village and farm houses
        k_ = len(C.houses); nm = (['cottage', 'cottage_b'] if sz < 4.6 else ['farmhouse', 'village_row', 'farmhouse'])[k_ % (2 if sz < 4.6 else 3)]
        if nm == 'village_row' and np.hypot(x - 610.0, y + 850.0) > 120: nm = 'farmhouse'                       # terraced rows only in the village core
        W_, D_ = CQ.FOOT[nm]; sx, sy = W_, D_
        S.add(box(x, y, z - found, sx + 0.3, sy + 0.3, found + 0.3, yaw), lin('#8f8d86'))
        KP.KIT.append((nm, x, y, z - 0.02, yaw - math.pi / 2)); ob(x, y, sx, sy, yaw); nov(x, y, max(sx, sy) * 0.8); C.houses.append((x, y, sx, sy, CQ.ITEMS[nm][1], yaw, z))

    def frame(r, i):
        o = r['xy'][i]; t = r['tan'][i]; l = r['left'][i]; z = r['z'][i]
        return (lambda a, off, dz=0.0: np.array([o[0] + t[0] * a + l[0] * off, o[1] + t[1] * a + l[1] * off, z + dz])), float(r['head'][i])

    def grandstand(Fr, hd, ac, off0, length, side, tiers=9):
        cols = [lin('#2f5fa8'), lin('#c5261f'), lin('#e8e8e4'), lin('#2f5fa8')]; nsec = max(2, int(length / 14)); sl = length / nsec
        for k in range(tiers):                                    # concrete terrace with seat rows split by aisles, colour blocks by section
            p = Fr(ac, side * (off0 + 1.25 * k + 0.6), -0.6); S.add(box(p[0], p[1], p[2], length, 1.25, 1.3 + 0.62 * k, hd), CONC * (0.92 + 0.08 * (k % 2)))
            if k:
                for q in range(nsec):
                    a = -length / 2 + (q + 0.5) * sl; p = Fr(ac + a, side * (off0 + 1.25 * k + 0.25), 0.7 + 0.62 * k - 0.6); S.add(box(p[0], p[1], p[2], sl - 1.4, 0.45, 0.42, hd), cols[(q + k // 3) % 4])
                    p = Fr(ac + a, side * (off0 + 1.25 * k + 0.5), 0.7 + 0.62 * k - 0.6 + 0.42); S.add(box(p[0], p[1], p[2], sl - 1.4, 0.08, 0.38, hd), cols[(q + k // 3) % 4] * 0.8)
        zt_ = 0.62 * tiers + 6.0; p0 = Fr(ac - length / 2, side * (off0 + 1.25 * tiers + 0.6), -0.6); p1 = Fr(ac + length / 2, side * (off0 + 1.25 * tiers + 0.6), -0.6)
        AR.wall(p1[:2] if side > 0 else p0[:2], p0[:2] if side > 0 else p1[:2], p0[2], zt_ / 2, 2, 4.0, (3.0, 1.8, 0.7), lin('#d5d2c8'), 'plaster', None, depth=0.3, cornice=True)    # back wall: hospitality boxes
        p = Fr(ac, side * (off0 + 1.25 * tiers / 2 - 0.5), zt_ + 0.6); S.add(box(p[0], p[1], p[2], length + 2, 1.25 * tiers + 3.5, 0.3, hd), lin('#e9e9e6'))
        p = Fr(ac, side * (off0 - 1.4), zt_ + 0.3); S.add(box(p[0], p[1], p[2], length + 2, 0.3, 0.9, hd), lin('#c5261f'))                    # roof fascia
        for a in np.linspace(-length / 2 + 2, length / 2 - 2, max(3, int(length / 20))):           # cantilever trusses from the back wall
            pb = Fr(ac + a, side * (off0 + 1.25 * tiers + 0.4), zt_ + 0.6); pf = Fr(ac + a, side * (off0 - 1.2), zt_ + 0.6); pt = Fr(ac + a, side * (off0 + 1.25 * tiers + 0.4), zt_ + 3.8)
            S.add(beam(pb, pf, 0.3, 0.3), STEEL); S.add(beam(pt, pf, 0.25, 0.25), STEEL); S.add(beam(pb, pt, 0.3, 0.3), STEEL)
        p = Fr(ac, side * (off0 + 1.25 * tiers / 2), 0); ob(p[0], p[1], length, 1.25 * tiers + 1, hd); nov(p[0], p[1], length / 2 + 6)

    # ============================================================ suspension bridge
    if hasattr(C, 'suspension'):
        r, a, ln = C.suspension; n = r['n']; hw = r['w'] / 2
        iA = a + int(0.2 * ln); iB = a + int(0.8 * ln); TH = 72.0; TW = lin('#e9e6dc'); CB = lin('#3d5a73')
        for it in (iA, iB):
            zi = r['z'][it % n]; hd = r['head'][it % n]
            for o in (-(hw + 2.4), hw + 2.4):
                p = P(r, it, o); bed = float(K.base_h(p[0], p[1])) - 2
                C.BT.add(cyl(p[0], p[1], bed, 3.4, 3.0, zi - 2 - bed, 8, a0=hd), CONC)
                C.BT.add(box(p[0], p[1], zi - 2, 3.2, 3.2, TH * 0.55 + 2, hd), TW); C.BT.add(box(p[0], p[1], zi + TH * 0.55, 2.7, 2.7, TH * 0.45, hd), TW)
                C.BT.add(box(p[0], p[1], zi + TH, 3.6, 3.6, 1.2, hd), lin('#bdb9ad')); C.BT.add(cyl(p[0], p[1], zi + TH + 1.2, .35, .35, 1.4, 6), RED)
            pa = P(r, it, -(hw + 2.4)); pb = P(r, it, hw + 2.4)
            for hh in (22.0, 46.0, TH - 2):
                C.BT.add(beam((pa[0], pa[1], zi + hh), (pb[0], pb[1], zi + hh), 2.4, 3.0), TW)
        def cab_h(i):
            if iA <= i <= iB:
                u = (i - iA) / (iB - iA); return 5.0 + (TH - 5.0) * (2 * u - 1) ** 2
            if i < iA: u = (i - a) / max(1, iA - a)
            else: u = (a + ln - 1 - i) / max(1, a + ln - 1 - iB)
            return 1.2 + (TH - 1.2) * np.clip(u, 0, 1) ** 1.35
        for o in (-(hw + 2.4), hw + 2.4):
            ids = list(range(a, a + ln - 1, 2))
            if ids[-1] != a + ln - 1: ids.append(a + ln - 1)
            for i0, i1 in zip(ids[:-1], ids[1:]):
                C.BT.add(beam(P(r, i0, o, cab_h(i0)), P(r, i1, o, cab_h(i1)), 0.55), CB)
            for i in range(a + 3, a + ln - 3, 3):
                if cab_h(i) > 3 and abs(i - iA) > 1 and abs(i - iB) > 1:
                    C.BT.add(beam(P(r, i, o, 1.0), P(r, i, o, cab_h(i)), 0.16), lin('#c9c6bb'))
        lm('Suspension Bridge', P(r, a + ln // 2))

    # ============================================================ city
    cz = K.CITY_Z; SXs, SYs = K.SX, K.SY
    walls = [lin(c) for c in ('#d9d2c2', '#c9b9a0', '#e2ddd2', '#b8a58c', '#cfc8ba', '#a9a39a', '#d6c2a8')]
    glassc = [lin(c) for c in ('#7fa7c9', '#6f9bb5', '#8db3c4', '#5f86a8', '#9ab8cc', '#7c9a8f', '#a7b6c4')]
    def tower(x, y, sx, sy, h, yaw=0.0):
        if h > 128 and C.hero(x, y, sx, sy, h): return
        C.bld.append(('tower', x, y, sx, sy, h, yaw, cz + 0.15))
        col = glassc[rng.integers(len(glassc))] * rng.uniform(0.85, 1.1); z = cz + 0.15
        tiers = 1 if h < 60 else rng.integers(1, 4); zz = z; w, d = sx, sy
        fr = [1.0] if tiers == 1 else ([0.62, 0.38] if tiers == 2 else [0.5, 0.3, 0.2])
        for k, f in enumerate(fr):
            hh = h * f; AR.curtain(C, AR.rect(x, y, w, d, yaw), zz, hh, col)
            S.add(box(x, y, zz + hh - 0.02, w + 0.4, d + 0.4, 0.7, yaw), lin('#4a4f57')); zz += hh; w *= 0.8; d *= 0.8
        import isle_props as KP, isle_city as CI                     # modelled crown: fin screen, lit band, mast
        K_ = KP.Part(); CI.tower_crown(K_, KP.mats(), w * 0.97 / 0.8, d * 0.97 / 0.8, rng); AR.emit_model(K_, x, y, zz + 0.3, yaw, 'TowerCrown_%d' % len(C.bld))
        import isle_props as KP, isle_city as CI                     # modelled street level: plinth, entrance portal, canopy, revolving door
        K_ = KP.Part(); CI.tower_base(K_, KP.mats(), sx, sy, rng); tk = AR.tile_key(x, y); AR.emit_model(K_, x, y, z, yaw, 'BuildingsHDModel__t%d_%d_tw%d' % (tk[0], tk[1], len(C.bld)))
        ob(x, y, sx, sy, yaw)
    def midrise(x, y, sx, sy, h, yaw=0.0, z=None):
        z = cz + 0.15 if z is None else z
        AR.midrise(C, x, y, sx, sy, h, yaw, z, walls[rng.integers(len(walls))] * rng.uniform(0.9, 1.08))
        S.add(box(x, y, z + h - 0.3, sx - 0.7, sy - 0.7, 0.55, yaw), lin('#5a5550'))          # roof for the far version, hidden inside the modelled parapet
        ob(x, y, sx, sy, yaw); nov(x, y, max(sx, sy) * 0.75); C.bld.append(('mid', x, y, sx, sy, h, yaw, z))
    nb = 0
    for i in range(len(SXs) - 1):
        for j in range(len(SYs) - 1):
            x0, x1 = SXs[i] + 7.5, SXs[i + 1] - 7.5; y0, y1 = SYs[j] + 7.5, SYs[j + 1] - 7.5
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            S.add(box(cx, cy, cz - 0.7, x1 - x0, y1 - y0, 0.86), lin('#8f8d86')); nov(cx, cy, 0)
            Vp_ = np.array([(x0, y0, cz + 0.165), (x1, y0, cz + 0.165), (x1, y1, cz + 0.165), (x0, y1, cz + 0.165)]); C.PV.add((Vp_, np.array([(0, 1, 2), (0, 2, 3)])), lin('#c9c6bd'), solid=False, uv=Vp_[:, :2] / 4.0)
            core = math.exp(-((cx / 330) ** 2 + ((cy + 20) / 240) ** 2))
            nxl = 2 if rng.random() < 0.6 else 3; nyl = 2
            lw = (x1 - x0 - 8) / nxl; ld = (y1 - y0 - 8) / nyl
            for a in range(nxl):
                for b in range(nyl):
                    lx = x0 + 4 + lw * (a + 0.5); ly = y0 + 4 + ld * (b + 0.5); u = rng.random()
                    if x0 < 0 < x1 and y0 < -20 < y1:                       # civic plaza: paving, a fountain, a ring of trees, benches, lamps
                        if a or b: continue
                        pz = cz + 0.17; C.Sm.add(lathe(0, -20, pz, [(7.5, 0.0), (7.8, 0.8), (7.2, 0.85), (7.1, 0.35), (0.0, 0.35)], 1, 1, 36), lin('#cfc9bb'), solid=False)
                        C.Sm.add(lathe(0, -20, pz, [(7.1, 0.62), (0.0, 0.62)], 1, 1, 36), lin('#3f9fb5'), solid=False)
                        C.Sm.add(lathe(0, -20, pz, [(0.8, 0.3), (0.5, 2.4), (2.4, 2.8), (2.5, 3.1), (0.4, 3.0), (0.3, 4.6), (1.0, 4.8), (0.12, 5.0)], 1, 1, 20), lin('#d8d2c3'), solid=False)
                        for k_ in range(12):
                            ang = k_ * math.pi / 6; park_trees.append((16 * math.cos(ang), -20 + 16 * math.sin(ang)))
                            if k_ % 2 == 0: bx_, by_ = 11 * math.cos(ang + 0.26), -20 + 11 * math.sin(ang + 0.26); S.add(box(bx_, by_, pz, 1.8, 0.5, 0.45, ang + math.pi / 2), lin('#8a6a48')); S.add(box(bx_ + 0.25 * math.cos(ang), by_ + 0.25 * math.sin(ang), pz + 0.45, 1.8, 0.08, 0.45, ang + math.pi / 2), lin('#8a6a48'))
                        for k_ in range(4): ang = k_ * math.pi / 2 + math.pi / 4; lx_, ly_ = 22 * math.cos(ang), -20 + 22 * math.sin(ang); S.add(cyl(lx_, ly_, pz, 0.12, 0.09, 4.5, 6), lin('#2b2d31')); C.Sm.add(lathe(lx_, ly_, pz + 4.3, [(0.0, 0.0), (0.32, 0.1), (0.3, 0.6), (0.0, 0.7)], 1, 1, 10), lin('#f4efd8'), solid=False)
                        oc(0, -20, 8); nov(0, -20, 30); continue
                    if u < 0.09:
                        S.add(box(lx, ly, cz + 0.1, lw - 5, ld - 5, 0.12), lin('#5f9a46'))
                        for _ in range(5): park_trees.append((lx + rng.uniform(-lw / 3, lw / 3), ly + rng.uniform(-ld / 3, ld / 3)))
                        continue
                    fw = (lw - 5) * rng.uniform(0.72, 0.96); fd = (ld - 5) * rng.uniform(0.72, 0.96)
                    if core > 0.3 and rng.random() < 0.55 + 0.4 * core:
                        tower(lx, ly, min(fw, 46), min(fd, 46), rng.uniform(55, 120) + 95 * core * rng.uniform(0.4, 1.0))
                    else: midrise(lx, ly, fw, fd, rng.uniform(13, 30) + 26 * core * rng.random())
                    nb += 1
    tries = 0; sub = []
    while len(sub) < 46 and tries < 5000:                         # low buildings round the grid
        tries += 1; x = rng.uniform(-690, 690); y = rng.uniform(-345, 345)
        if abs(x) < 494 and -314 < y < 274: continue
        if K.biomes(np.array(x), np.array(y))['city'] < 0.8 or abs(H(x, y) - cz) > 0.6 or rd(x, y) < 20: continue
        if any(math.hypot(x - q[0], y - q[1]) < 34 for q in sub) or math.hypot(x - 650, y + 195) < 150: continue
        sub.append((x, y)); midrise(x, y, rng.uniform(16, 26), rng.uniform(12, 20), rng.uniform(7, 16), rng.choice([0, math.pi / 2]), z=H(x, y))
    lm('City Centre', (0, -20, cz))
    L.STATS['buildings'] = nb + len(sub)

    # ============================================================ stadium
    sx_, sy_ = 650.0, -195.0; sz_ = H(sx_, sy_) + 0.5; a_, b_ = 105.0, 84.0
    import isle_props as KP, isle_landmarks as LMK; import isle_landmarks_hq as LQ; K_ = KP.Part(); LQ.stadium_hq(K_, LQ.kit_mats(), a_, b_); AR.emit_model(K_, sx_, sy_, sz_ - 0.5, math.pi / 2, 'Landmark_Stadium')
    oc(sx_, sy_, 100); nov(sx_, sy_, 125); lm('Stadium', (sx_, sy_ + 110, sz_))

    # ============================================================ harbour
    qz = 3.0; qx, qy, qw, qd = -150.0, -402.0, 640.0, 66.0
    S.add(box(qx, qy, -16, qw, qd, 16 + qz), lin('#a8a59c')); plat(qx, qy, qw, qd, 0, qz); nov(qx, qy, 0)
    import isle_props as KP, isle_landmarks as LMK; K_ = KP.Part(); LMK.quay_furniture(K_, KP.mats(), qw - 20, 48); AR.emit_model(K_, qx, qy - qd / 2, qz, 0.0, 'Landmark_Quay')
    S.add(box(qx, qy + qd / 2 + 16, -3, qw, 34, 3 + qz + 0.0), lin('#9c9990')); plat(qx, qy + qd / 2 + 16, qw, 34, 0, qz)
    ccols = [lin(c) for c in ('#b3241d', '#2b5fae', '#2f9a57', '#e0a526', '#d8d8d4', '#7a4a2a', '#3b8fa3')]
    for k in range(16):                                           # container stacks
        bx = -420 + 26 * k
        if -310 < bx < -40 and k % 4 == 3: continue
        for row in range(2):
            for lv in range(rng.integers(1, 4)):
                cc_ = ccols[rng.integers(len(ccols))] ** (1 / 2.2); __import__('isle_props').KIT.append(('container', bx, qy + 6 + 7 * row, qz + 2.6 * lv, rng.choice([0.0, math.pi]), tuple(cc_)))
        ob(bx, qy + 9.5, 12.2, 9.6)
    for cxr in (-300.0, -170.0, -40.0):                           # gantry cranes
        yb = qy - qd / 2 + 6
        for dx in (-9, 9):
            for dy in (0, 16): S.add(box(cxr + dx, yb + dy, qz, 1.3, 1.3, 34), lin('#d85a1e'))
            S.add(beam((cxr + dx, yb, qz + 34), (cxr + dx, yb + 16, qz + 34), 1.4), lin('#d85a1e'))
        S.add(beam((cxr, yb + 24, qz + 37), (cxr, yb - 44, qz + 37), 3.0, 2.6), lin('#d85a1e'))
        S.add(beam((cxr, yb + 8, qz + 37), (cxr, yb + 8, qz + 52), 1.2), lin('#d85a1e'))
        S.add(beam((cxr, yb + 8, qz + 52), (cxr, yb - 42, qz + 38.5), 0.3), DARK); S.add(box(cxr, yb - 6, qz + 32.5, 4, 5, 3.4), WHITE)
        oc(cxr - 9, yb + 8, 9); oc(cxr + 9, yb + 8, 9)
    for k in range(3):
        wx = 60 + 46 * k; __import__('isle_props').KIT.append(('warehouse', wx, qy + 8, qz - 0.3, -math.pi / 2)); ob(wx, qy + 8, 38, 30)

    def hull(x, y, yaw, ln, bm, dr, fb, col, deckc):
        st = np.linspace(-0.5, 0.5, 11); Vh = []
        for s_ in st:
            wb = bm / 2 * (1 - max(0.0, (s_ - 0.18) / 0.32) ** 1.7) * (0.82 + 0.18 * min(1.0, (s_ + 0.5) / 0.12))
            wb = max(wb, 0.25); sheer = fb + 2.2 * max(0.0, (s_ - 0.2) / 0.3) ** 2
            Vh += [(s_ * ln, 0, -dr), (s_ * ln, -wb * 0.72, -dr * 0.55), (s_ * ln, -wb, sheer), (s_ * ln, wb, sheer), (s_ * ln, wb * 0.72, -dr * 0.55)]
        Vh = np.array(Vh); Fh = []
        for k in range(10):
            for q in range(5):
                a0 = k * 5 + q; a1 = k * 5 + (q + 1) % 5; b0 = a0 + 5; b1 = a1 + 5
                Fh += [(a0, b0, b1), (a0, b1, a1)]
        cols = np.where((Vh[:, 2] > 0)[:, None], col, lin('#7a2a22')) * np.ones((len(Vh), 3))
        Vh = rot_z(Vh, np.zeros(3), yaw) + (x, y, 0); Sm.add((Vh, np.array(Fh)), cols)
        return Vh
    def ship_box(x, y, yaw, along, sx, sy, z, h, col, fac=None):
        px = x + along * math.cos(yaw); py = y + along * math.sin(yaw)
        if fac is not None: facade(fac, px, py, z, sx, sy, h, yaw, col, bay=3.0, floor=2.8); S.add(box(px, py, z + h - 0.01, sx + 0.6, sy + 0.6, 0.35, yaw), WHITE)
        else: S.add(box(px, py, z, sx, sy, h, yaw), col)
    cx_, cy_, cyaw = -110.0, -474.0, 0.0                           # cruise ship
    hull(cx_, cy_, cyaw, 210, 30, 7, 7.5, WHITE, WHITE); S.add(box(cx_ - 8, cy_, 7.4, 172, 27, 0.4, cyaw), lin('#c9b48a'))
    for k, (ln_, wd_) in enumerate(((158, 25), (146, 23.5), (132, 22), (112, 20))):
        ship_box(cx_, cy_, cyaw, -12 + k * 1.5, ln_, wd_, 7.8 + k * 5.6, 5.6, lin('#f2f2ee'), FA)
    ship_box(cx_, cy_, cyaw, -30, 13, 9, 30.2, 9, lin('#c5261f')); ship_box(cx_, cy_, cyaw, 30, 16, 14, 30.2, 3.4, GLASS)
    gx_, gy_, gyaw = -470.0, -560.0, 0.5                          # cargo ship
    hull(gx_, gy_, gyaw, 150, 24, 8, 5, lin('#263c57'), DARK); ship_box(gx_, gy_, gyaw, -56, 14, 20, 5, 15, WHITE, FA)
    for k in range(7):
        for q in range(3):
            for lv in range(rng.integers(1, 4)):
                px = gx_ + (-36 + 14 * k) * math.cos(gyaw) - (-7 + 7 * q) * math.sin(gyaw); py = gy_ + (-36 + 14 * k) * math.sin(gyaw) + (-7 + 7 * q) * math.cos(gyaw)
                S.add(box(px, py, 5 + 2.6 * lv, 12.2, 6.4, 2.6, gyaw), ccols[rng.integers(len(ccols))])
    mdx_, mdy_ = 0.0, 0.0; best_ = None                            # marina: slide the three piers to open water next to the shore
    for ddx in range(-240, 121, 12):
        for ddy in range(-120, 61, 6):
            ok_ = all(C.hgt(150 + 36 * k + ddx + o, yv + ddy) < -0.4 for k in range(3) for o in (-8, 0, 8) for yv in (-446, -470, -494, -508))
            if ok_ and any(C.hgt(150 + 36 * k + ddx, -428 + ddy) > -0.4 for k in range(3)):
                sc_ = abs(ddx) + abs(ddy)
                if best_ is None or sc_ < best_: best_ = sc_; mdx_, mdy_ = float(ddx), float(ddy)
    C.marina_shift = (mdx_, mdy_)
    for k in range(3):                                            # marina piers (art sheet 06 timber jetties) and yachts
        px = 150 + 36 * k + mdx_; plat(px, -470 + mdy_, 3.2, 76, 0, 1.3)
        for j in range(4):
            if C.hgt(px, -470 + mdy_ - 28.5 + j * 19.0) < 0.3: __import__('isle_props').KIT.append(('jetty', px, -470 + mdy_ - 28.5 + j * 19.0, 0.22, math.pi / 2))   # only where there is water under it
    def yacht(x, y, yaw, ln=9.0, sail=True):
        hull(x, y, yaw, ln, ln * 0.3, 0.8, 1.0, WHITE, WHITE); d = np.array([math.cos(yaw), math.sin(yaw), 0])
        S.add(box(x - d[0] * ln * .08, y - d[1] * ln * .08, 1.0, ln * .32, ln * .2, 0.9, yaw), lin('#e9e6dc'))
        if sail:
            S.add(cyl(x, y, 1.0, .08, .05, ln * 1.2, 4), DARK); m0 = np.array([x, y, 2.0])
            D.add((np.array([m0, m0 - d * ln * .42, m0 + (0, 0, ln * 1.1)]), np.array([(0, 1, 2)])), lin('#f5f2e8'), solid=False)
            D.add((np.array([m0 + d * .2, m0 + d * ln * .45, m0 + (0, 0, ln * 0.95)]), np.array([(0, 1, 2)])), lin('#f0ede2'), solid=False)
    KPm = __import__('isle_props')
    for k in range(3):
        for q in range(5):
            if rng.random() < 0.8:
                sail_ = rng.random() < 0.6; yy_ = -440 - 14 * q + mdy_; xx_ = 150 + 36 * k + mdx_ + rng.choice([-1, 1]) * (4.2 if sail_ else 4.8)
                if max(C.hgt(xx_ + dx_, yy_ + dy_) for dx_ in (-2, 2) for dy_ in (-6, 0, 6)) > -0.4: continue
                KPm.KIT.append(('sail_yacht' if sail_ else 'motor_yacht', xx_, yy_, 0.0, math.pi / 2 + rng.normal(0, .04) + (math.pi if q % 2 else 0)))
    for (yx, yy) in ((-300, -760), (-80, -820), (-560, -700), (40, -640), (-700, -860), (-760, -1250), (-200, -1420), (900, -1400), (-1900, -700), (2200, -400), (500, 1500)):
        if K.base_h(yx, yy) < -4: KPm.KIT.append(('sail_yacht' if rng.random() < 0.7 else 'motor_yacht', yx, yy, 0.0, rng.uniform(0, 6.28)))
    KPm.KIT.append(('harbour_kiosk', -462.0, -418.0, qz, -math.pi / 2)); ob(-462.0, -418.0, 3.0, 4.0)
    for (bwx, bwy, bwa) in ((-600.0, -520.0, 2.6), (260.0, -560.0, -1.2), (-300.0, -640.0, 1.6)):
        if K.base_h(bwx, bwy) < -3: KPm.KIT.append(('breakwater', bwx, bwy, 0.0, bwa)); oc(bwx, bwy, 6.5)
    # ferris wheel (spins in the game)
    fx_, fy_, fr_ = -438.0, -388.0, 31.0; hubz = qz + fr_ + 5
    for dy in (-3.2, 3.2):
        for dx in (-14, 14): S.add(beam((fx_ + dx, fy_ + dy, qz), (fx_, fy_ + dy * 0.6, hubz), 1.0), WHITE)
    S.add(beam((fx_, fy_ - 2.6, hubz), (fx_, fy_ + 2.6, hubz), 1.6), lin('#d7d9dc'))
    W = Buf()
    for k in range(24):
        a0 = k * 2 * np.pi / 24; a1 = (k + 1) * 2 * np.pi / 24
        for dy in (-1.3, 1.3):
            W.add(beam((fr_ * math.cos(a0), dy, fr_ * math.sin(a0)), (fr_ * math.cos(a1), dy, fr_ * math.sin(a1)), 0.5), lin('#e9e6dc'))
            if k % 2 == 0: W.add(beam((0, dy, 0), (fr_ * math.cos(a0), dy, fr_ * math.sin(a0)), 0.22), lin('#c9ccd0'))
        if k % 2 == 0:
            W.add(sphere(fr_ * math.cos(a0), 0, fr_ * math.sin(a0), 1.7, 1.5, 1.7, 7, 5), ccols[(k // 2) % len(ccols)])
    Vw, Fw, Cw, _ = W.arrays(); o = make_obj('Spin_FerrisWheel', Vw, Fw, Cw, None, M.vc, smooth=False); o.location = (fx_, fy_, hubz)
    C.spinners.append(dict(name='Spin_FerrisWheel', axis='z', speed=0.12, pos=[fx_, hubz, -fy_])); oc(fx_, fy_, 15); lm('Harbour & Ferris Wheel', (fx_, fy_ + 30, qz))

    # ============================================================ racing circuit
    r = R['Circuit']; n = r['n']; hw = r['w'] / 2
    i0 = int(np.argmin(np.hypot(r['xy'][:, 0] - 1230, r['xy'][:, 1] + 118))); C.circuit_start = i0
    Fr, hd = frame(r, i0)
    cv = np.array([Fr(-1, -hw, .07), Fr(1, -hw, .07), Fr(1, hw, .07), Fr(-1, hw, .07)])
    make_obj('StartLine', cv, np.array([(0, 1, 2), (0, 2, 3)]), None, np.array([(0, 0), (0, 1.0), (1, 1.0), (1, 0)]), M.chk)
    for o_ in (-hw - 2.4, hw + 2.4):
        p = Fr(0, o_); S.add(box(p[0], p[1], p[2] - 0.6, 0.7, 0.7, 8.8, hd), DARK)
    p = Fr(0, 0, 7.4); S.add(box(p[0], p[1], p[2], 1.0, r['w'] + 5.6, 1.5, hd), DARK)
    for k in range(5):
        p = Fr(-0.66, -4.8 + 2.4 * k, 7.82); S.add(cyl(p[0], p[1], p[2], .42, .42, .66, 10), RED if k < 4 else lin('#2fbf4a'))
    grid = []
    for k in range(12):
        a_ = -14 - 9 * k; o_ = 3.5 if k % 2 == 0 else -3.5; base = Fr(a_, o_, 0.07)
        fw_ = np.array([math.cos(hd), math.sin(hd), 0]); lf = np.array([-fw_[1], fw_[0], 0])
        for q0, q1 in ((base - lf * 1.5, base + lf * 1.5), (base - lf * 1.5, base - lf * 1.5 - fw_ * 2.2), (base + lf * 1.5, base + lf * 1.5 - fw_ * 2.2)):
            Mk.add(beam(q0, q1, 0.28, 0.02), WHITE)
    grandstand(Fr, hd, 0, 17, 240, 1, 10)
    p = Fr(-10, -33, -0.6); AR.block(C, p[0], p[1], p[2], 230, 12, 8.2, hd, lin('#e4e1d8'), fh=4.1, bw=7.6, shop=True); S.add(box(p[0], p[1], p[2] + 8.2, 232, 13.4, 0.4, hd), lin('#39424d')); ob(p[0], p[1], 230, 12, hd)
    p = Fr(-10, -19.5, -0.56); S.add(box(p[0], p[1], p[2], 250, 14, 0.5, hd), lin('#3b3d41'))
    p = Fr(-10, -11.2, -0.5); S.add(box(p[0], p[1], p[2], 240, 0.4, 1.6, hd), CONC); ob(p[0], p[1], 240, 0.6, hd)
    p = Fr(118, -34, -0.5); AR.block(C, p[0], p[1], p[2], 10, 10, 18, hd, lin('#e4e1d8'), fh=3.6, bw=3.4, win=(1.8, 1.7, 0.9)); S.add(box(p[0], p[1], p[2] + 18, 13, 13, 3.4, hd), lin('#39505f')); S.add(box(p[0], p[1], p[2] + 21.4, 14, 14, 0.4, hd), WHITE); ob(p[0], p[1], 10, 10, hd)
    for a_ in (-150, -75, 0, 75, 150):
        for o_ in (-15.5, 15.5):
            p = Fr(a_, o_, -0.5); S.add(cyl(p[0], p[1], p[2], .28, .16, 18, 6), STEEL); q = Fr(a_, o_ - np.sign(o_) * 1.6, 17.3); S.add(box(q[0], q[1], q[2], 2.2, 3.4, 0.5, hd), lin('#f4f1d8'))
    for k in range(9):
        p = Fr(-120 + 30 * k, 33.5, 0); S.add(cyl(p[0], p[1], p[2], .09, .07, 17, 5), WHITE); q = Fr(-120 + 30 * k + 1.4, 33.5, 14.4)
        S.add(box(q[0], q[1], q[2], 2.6, 0.06, 1.7, hd), [RED, YEL, BLUE, lin('#2f9a57')][k % 4])
    for k in range(12):
        p = Fr(-110 + 19 * k, -47, -0.3)
        if k % 3 == 2: __import__('isle_props').KIT.append((['hut_red', 'hut_blue'][k % 2], p[0], p[1], p[2] - 0.3, hd - math.pi / 2))
        else: AR.block(C, p[0], p[1], p[2], 3.0, 12.5, 3.9, hd, [lin('#d8d8d4'), lin('#5a6470'), lin('#b3241d')][k % 3], fh=3.9, bw=3.1, shop=True)
    curv = r['curv']; tight = np.abs(curv) > 1 / 130
    apex = [i for i in range(n) if tight[i] and abs(curv[i]) >= abs(curv[(i - 1) % n]) and abs(curv[i]) > abs(curv[(i + 1) % n])]
    for k, i in enumerate(apex[:6]):
        side = -1 if curv[i] > 0 else 1; Fa, ha = frame(r, i)
        if k % 2 == 0: grandstand(Fa, ha, 0, hw + 26, 70, side, 7)
    for i in np.where(np.roll(tight, 2) | np.roll(tight, -2) | tight)[0]:
        side = -1 if curv[i] > 0 else 1; p = P(r, i, side * (hw + 19)); zb = H(p[0], p[1])
        S.add(box(p[0], p[1], zb - 0.2, r['step'] * 1.02, 1.5, 1.3, r['head'][i]), RED if i % 2 else WHITE)
    for k, i in enumerate(range(0, n, n // 5)):
        if k == 0: continue
        Fa, ha = frame(r, i)                                    # sponsor-free arches round the lap
        for o_ in (-hw - 2.2, hw + 2.2):
            p = Fa(0, o_); S.add(box(p[0], p[1], p[2] - 0.8, 0.8, 0.8, 8.0, ha), YEL)
        p = Fa(0, 0, 6.4); S.add(box(p[0], p[1], p[2], 1.2, r['w'] + 5.2, 1.6, ha), YEL)
    lm('Racing Circuit', Fr(0, 0)); nov(*Fr(-10, -30)[:2], 150)

    # ============================================================ countryside
    vc_ = np.array([610.0, -850.0]); hs = []; tries = 0
    hw_c = [lin(c) for c in ('#f1ece0', '#e9dcc3', '#f4f1ea', '#d9c7a8', '#e7e2d3')]; rf_c = [TERRA, lin('#b85a35'), lin('#8f3b28'), lin('#6d6f73')]
    while len(hs) < 34 and tries < 5000:
        tries += 1; p = vc_ + rng.normal(0, 85, 2); hz = H(*p)
        if hz < 4 or abs(H(p[0] + 6, p[1]) - hz) > 1.3 or abs(H(p[0], p[1] + 6) - hz) > 1.3 or rd(*p) < 15: continue
        if any(np.hypot(*(p - q)) < 17 for q in hs): continue
        hs.append(p); house(p[0], p[1], rng.uniform(7, 11), rng.uniform(5.5, 7.5), rng.uniform(3.2, 6), rng.uniform(0, 3.14), hw_c[rng.integers(5)], rf_c[rng.integers(4)])
    for dx, dy in ((-30, -55), (40, 60), (-70, 30), (60, -40)):
        p = vc_ + (dx, dy)
        if rd(*p) > 16 and all(np.hypot(*(p - q)) > 15 for q in hs):
            hz = H(*p); import isle_props as KP, isle_landmarks_hq as LQ; K_ = KP.Part(); LQ.church_hq(K_, LQ.kit_mats())
            S.add(box(p[0], p[1] + 2, hz - 2.5, 10, 25, 2.6, 0.3), lin('#8f8d86')); AR.emit_model(K_, p[0], p[1], hz - 0.1, 0.3 + math.pi, 'Landmark_Church')
            ob(p[0], p[1] + 2, 8, 18, 0.3); ca_, sa_ = math.cos(0.3 + math.pi / 2), math.sin(0.3 + math.pi / 2); tw_ = (p[0] - 5.8 * ca_ + 7.6 * sa_, p[1] - 5.8 * sa_ - 7.6 * ca_); ob(tw_[0], tw_[1], 2.6, 2.6, 0.3); nov(p[0], p[1], 19); lm('Village Church', (p[0], p[1], hz)); break
    for fx0, fy0 in ((990, -965), (1290, -790), (190, -935), (1370, -1050), (880, -690)):
        if H(fx0, fy0) < 5 or rd(fx0, fy0) < 22: continue
        ya = rng.uniform(0, 3.14); hz = H(fx0, fy0)
        KP_ = __import__('isle_props'); fa = ya - math.pi / 2; fwd = np.array([math.cos(fa), math.sin(fa)]); sid = np.array([-fwd[1], fwd[0]])   # art sheet 05 farm yard
        S.add(box(fx0, fy0, hz - 2, 16.3, 10.3, 2.3, ya), lin('#8f8d86')); KP_.KIT.append(('barn_hq', fx0, fy0, hz, fa)); ob(fx0, fy0, 16, 10, ya); nov(fx0, fy0, 26)
        sx0, sy0 = fx0 + 18 * math.cos(ya + 1.2), fy0 + 18 * math.sin(ya + 1.2)
        if rd(sx0, sy0) > 12: KP_.KIT.append(('silos', sx0, sy0, H(sx0, sy0) - 0.1, fa)); oc(sx0, sy0 - 0.0, 3.0); ob(sx0 + 6.5 * fwd[0] - 3 * sid[0], sy0 + 6.5 * fwd[1] - 3 * sid[1], 6, 5, ya)
        tx_, ty_ = np.array([fx0, fy0]) + fwd * 11 + sid * 5
        if rd(tx_, ty_) > 7: KP_.KIT.append(('tractor', tx_, ty_, H(tx_, ty_), fa + 2.6)); oc(tx_, ty_, 2.2)
        bx_, by_ = np.array([fx0, fy0]) - fwd * 30 + sid * 8
        if rd(bx_, by_) > 12 and abs(H(bx_ + 5, by_) - H(bx_ - 5, by_)) < 1.5: KP_.KIT.append(('hay_field', bx_, by_, H(bx_, by_), fa)); nov(bx_, by_, 9)
        hb_ = np.array([fx0, fy0]) - sid * 16
        if rd(*hb_) > 12: KP_.KIT.append(('hay_shed', hb_[0], hb_[1], H(*hb_), fa)); ob(hb_[0], hb_[1], 12, 7, ya); nov(hb_[0], hb_[1], 10)
        wl_ = np.array([fx0, fy0]) + fwd * 24 - sid * 3
        if rd(*wl_) > 9: KP_.KIT.append(('walls_fences', wl_[0], wl_[1], H(*wl_), fa + math.pi / 2))
        hx0, hy0 = fx0 + 22 * math.cos(ya - 1.4), fy0 + 22 * math.sin(ya - 1.4)
        if rd(hx0, hy0) > 14: house(hx0, hy0, 10, 7, 5.0, ya, hw_c[0], rf_c[0])
    import isle_props as KPv; vy_ = 0                                     # art sheet 05: vineyard plots round the village, farm stands on the country roads
    for ang in np.linspace(0, 2 * np.pi, 9)[:-1]:
        for rr_ in (150.0, 185.0):
            c_ = vc_ + rr_ * np.array([math.cos(ang), math.sin(ang)]); a_ = ang + math.pi / 2; d1 = np.array([math.cos(a_), math.sin(a_)]); d2 = np.array([-d1[1], d1[0]])
            cells = [c_ + d1 * i * 17 + d2 * j * 9.5 for i in (-1, 0, 1) for j in (0, 1)]
            if all(rd(*q) > 12 and H(*q) > 4 and abs(H(*q) - H(*c_)) < 2.5 and all(np.hypot(*(q - h_)) > 16 for h_ in hs) for q in cells):
                for q in cells: KPv.KIT.append(('vineyard', q[0], q[1], H(*q) - 0.05, a_)); nov(q[0], q[1], 10)
                vy_ += 1; break
    C.stats_vineyards = vy_
    for rn_, fr_ in (('Farm Road', 0.35), ('Farm Road', 0.7), ('Orchard Lane', 0.5)):
        if rn_ not in R: continue
        r_ = R[rn_]; i_ = int(r_['n'] * fr_)
        for k_ in range(40):
            j_ = min(r_['n'] - 1, i_ + k_)
            if r_['junction'][j_] or r_['bridge'][j_]: continue
            Fr_, hd_ = frame(r_, j_); q = Fr_(0, r_['w'] / 2 + 4.5)
            if rd(q[0], q[1]) > r_['w'] / 2 + 3 and abs(H(q[0], q[1]) - r_['z'][j_]) < 1.2:
                ln_ = r_['left'][j_]; KPv.KIT.append(('farm_stand', q[0], q[1], H(q[0], q[1]), math.atan2(-ln_[1], -ln_[0]))); oc(q[0], q[1], 2.2); break
    wx_, wy_ = 1060.0, -735.0                                     # windmill
    if rd(wx_, wy_) > 14:
        wz = H(wx_, wy_); import isle_props as KP, isle_landmarks as LMK
        import isle_landmarks_hq as LQ; K_ = KP.Part(); LQ.windmill_hq(K_, LQ.kit_mats()); AR.emit_model(K_, wx_, wy_, wz - 0.3, 0.0, 'Landmark_Windmill')
        K_ = KP.Part(); LQ.windmill_sails_hq(K_, LQ.kit_mats()); o, _ = KP.make_prop('Spin_Windmill', [(Pq, T, N, U, Cq, mt) for Pq, T, N, U, Cq, mt in K_.arrays()]); o.location = (wx_, wy_ - 4.3, wz + 18.2); o.parent = L.ROOT
        C.spinners.append(dict(name='Spin_Windmill', axis='z', speed=0.5, pos=[wx_, wz + 18.2, -(wy_ - 4.3)])); oc(wx_, wy_, 4.4); nov(wx_, wy_, 16); lm('Windmill', (wx_, wy_, wz))
    for _ in range(300):                                          # hay bales in the fields
        x = rng.uniform(100, 1450); y = rng.uniform(-1150, -650)
        ci = (int((y - K.Y0) / K.CELL + .5), int((x - K.X0) / K.CELL + .5))
        if C.FIELD[ci] and rng.random() < 0.3: Sm.add(cyl(x, y, H(x, y) - 0.2, 0.9, 0.9, 1.5, 7), lin('#c9a84f'))

    # ============================================================ desert
    r = R['Dish Road']; e = r['xy'][-1] + r['tan'][-1] * 34; dx_, dy_ = float(e[0]), float(e[1]); dzb = H(dx_, dy_)
    S.add(box(dx_, dy_, dzb - 2, 9, 9, 9), CONC); Sm.add(cyl(dx_, dy_, dzb + 7, 2.2, 1.6, 9, 8), WHITE)
    Vd, Fd = lathe(dx_, dy_, dzb + 17, [(0.001, 0.0), (5, 0.35), (10, 1.4), (15, 3.15), (19, 5.05)], 1, 1, 24)
    piv = np.array([dx_, dy_, dzb + 17]); Vd = rot_z(rot_x(Vd, piv, math.radians(38)), piv, 0.6); D.add((Vd, Fd), lin('#f1f1ee'), solid=False)
    fo = rot_z(rot_x(np.array([[dx_, dy_, dzb + 17 + 15.0]]), piv, math.radians(38)), piv, 0.6)[0]
    for k in range(3):
        a0 = k * 2.1; rimp = rot_z(rot_x(np.array([[dx_ + 15 * math.cos(a0), dy_ + 15 * math.sin(a0), dzb + 17 + 3.15]]), piv, math.radians(38)), piv, 0.6)[0]
        S.add(beam(rimp, fo, 0.25), STEEL)
    S.add(box(fo[0], fo[1], fo[2] - 0.6, 1.6, 1.6, 1.4), DARK); house(dx_ - 26, dy_ + 12, 12, 8, 4, 0.2, lin('#e4dccb'), lin('#8b8f93'), 0.8)
    oc(dx_, dy_, 7); nov(dx_, dy_, 26); lm('Satellite Dish', (dx_, dy_, dzb))
    gx0, gy0 = 1052.0, 98.0; gz0 = H(gx0, gy0)                    # roadside fuel stop
    S.add(box(gx0, gy0, gz0 - 1.2, 30, 22, 1.25), lin('#8f8d86')); plat(gx0, gy0, 30, 22, 0, gz0 + 0.05)
    for dx in (-7, 7):
        for dy in (-3.5, 3.5): S.add(box(gx0 + dx, gy0 - 3 + dy, gz0, .4, .4, 5.2), WHITE)
    S.add(box(gx0, gy0 - 3, gz0 + 5.2, 18, 10, 0.7), RED); S.add(box(gx0 - 4, gy0 - 3, gz0, 1, .6, 1.6), YEL); S.add(box(gx0 + 4, gy0 - 3, gz0, 1, .6, 1.6), YEL)
    facade(FA, gx0, gy0 + 7.5, gz0, 16, 6, 4, 0, lin('#efe7d6'), bay=4); S.add(box(gx0, gy0 + 7.5, gz0 + 4, 16.6, 6.6, 0.4), lin('#6d6f73')); ob(gx0, gy0 + 7.5, 16, 6); nov(gx0, gy0, 22)
    S.add(cyl(gx0 + 17, gy0 - 9, gz0, .25, .25, 11, 6), STEEL); S.add(box(gx0 + 17, gy0 - 9, gz0 + 8, 5, .4, 3), YEL)
    lm('Desert Mesas', (K.MESAS[1][0], K.MESAS[1][1] - 130, H(K.MESAS[1][0], K.MESAS[1][1] - 130)))

    # ============================================================ mountains
    Hh = TR['H']; im = np.unravel_index(np.argmax(Hh), Hh.shape); mx_, my_, mz_ = float(TR['X'][im]), float(TR['Y'][im]), float(Hh[im])
    for k in range(6): S.add(cyl(mx_, my_, mz_ - 1 + 8 * k, 1.1 - 0.15 * k, 0.95 - 0.15 * k, 8, 4, a0=0.6), RED if k % 2 == 0 else WHITE)
    S.add(box(mx_ + 6, my_ - 2, mz_ - 3, 6, 4, 6, 0.3), CONC)
    r = R['Skyline Road']; it = int(np.argmax(r['z'] * ~(r['bridge'] | r['tunnel']))); Fa, ha = frame(r, it)
    for side in (1, -1):
        p = Fa(0, side * 34)
        if abs(H(p[0], p[1]) - r['z'][it]) < 7 and rd(p[0], p[1]) > 20:
            hz = H(p[0], p[1]); S.add(box(p[0], p[1], hz - 3, 14.3, 8.3, 3.3, ha), lin('#6f6b63')); __import__('isle_props').KIT.append(('winery_hq', p[0], p[1], hz, ha - math.pi / 2))
            ob(p[0], p[1], 14, 8, ha); nov(p[0], p[1], 20); lm('Summit Lodge', (p[0], p[1], hz))
            for k in range(5):
                q = Fa(-60 + 26 * k + (13 if k > 1 else 0), side * (30 + 6 * (k % 2)))
                if rd(q[0], q[1]) > 13 and np.hypot(q[0] - p[0], q[1] - p[1]) > 22: house(q[0], q[1], 8, 6, 3.4, ha, lin('#7a5a3c'), lin('#e9eef2'), 3.0, 3.0)
            break
    # waterfalls: sheets that follow the cliff from the tarn down to the pool
    tarn = K.LAKES[2]; pool = K.LAKES[3]; lvT = K.lake_level(tarn[0], tarn[1]); lvP = K.lake_level(pool[0], pool[1])
    for k, (fx0, fw0) in enumerate(K.FALLS):
        ys = np.arange(tarn[1] - 58, pool[1] + pool[2] - 18, -4.0)
        zs = np.array([max(H(fx0 + dx, y + dy) for dx, dy in ((0, 0), (-8, 0), (8, 0), (0, 7), (0, -7), (-8, -7), (8, -7))) for y in ys]) + 1.0; zs[0] = lvT + 0.3; zs = np.minimum.accumulate(zs); zs[-1] = lvP + 0.15
        sl = np.concatenate([[0], np.cumsum(np.hypot(np.diff(ys), np.diff(zs)))])
        wv = fw0 * (0.8 + 0.4 * (sl / sl[-1]))
        Vf = np.vstack([np.c_[fx0 - wv / 2, ys, zs], np.c_[fx0 + wv / 2, ys, zs]]); m = len(ys); i = np.arange(m - 1)
        Ff = np.vstack([np.c_[i, i + 1, m + i + 1], np.c_[i, m + i + 1, m + i]])
        make_obj('Waterfall_%d' % k, Vf, Ff, None, np.vstack([np.c_[np.zeros(m), sl / 14], np.c_[np.full(m, 1.5), sl / 14]]), M.fall)
        for q in range(5): Sm.add(sphere(fx0 + rng.uniform(-fw0, fw0) * .6, ys[-1] - rng.uniform(0, 8), lvP + 0.3, 5, 5, 1.6, 7, 4, jit=.2), lin('#f4f8fb'))
        nov(fx0, (ys[0] + ys[-1]) / 2, 55)
    lm('Twin Falls', (pool[0], pool[1] - pool[2] - 30, lvP + 2))

    # ============================================================ forest
    lk = K.LAKES[0]; lvl = K.lake_level(lk[0], lk[1])
    for k in range(7):
        a0 = k * 0.9 + 0.2; px, py = lk[0] + (lk[2] + 48) * math.cos(a0), lk[1] + (lk[2] + 48) * math.sin(a0)
        if rd(px, py) > 14 and abs(H(px + 5, py) - H(px, py)) < 2.5: house(px, py, 9, 6.5, 3.4, a0, lin('#6e5137'), lin('#3f4a3a'), 3.0, 3.0)
    S.add(beam((lk[0] + lk[2] + 16, lk[1], lvl + 0.7), (lk[0] + lk[2] - 46, lk[1], lvl + 0.7), 2.8, 0.3), WOOD); plat(lk[0] + lk[2] - 15, lk[1], 62, 2.8, 0, lvl + 0.85)
    for a_ in np.arange(-44, 14, 10):
        for o_ in (-1.2, 1.2): S.add(cyl(lk[0] + lk[2] + a_, lk[1] + o_, lvl - 5, .2, .2, 5.8, 5), lin('#5d4631'))
    lm('Forest Lake', (lk[0] + lk[2] + 30, lk[1], lvl))
    best = None
    for _ in range(600):
        x = rng.uniform(-1900, -900); y = rng.uniform(-50, 850)
        if rd(x, y) > 40 and all(np.hypot(x - l[0], y - l[1]) > l[2] + 60 for l in K.LAKES[:2]):
            hz = H(x, y)
            if best is None or hz > best[2]: best = (x, y, hz)
    tx_, ty_, tz_ = best
    for dx in (-2.2, 2.2):
        for dy in (-2.2, 2.2): S.add(beam((tx_ + dx * 1.5, ty_ + dy * 1.5, tz_ - 1), (tx_ + dx, ty_ + dy, tz_ + 20), 0.35), WOOD)
    S.add(box(tx_, ty_, tz_ + 20, 6.4, 6.4, 0.3), WOOD); S.add(box(tx_, ty_, tz_ + 20.3, 5, 5, 2.6), lin('#7a5a3c')); S.add(roof(tx_, ty_, tz_ + 22.9, 5, 5, 1.8, 0, 0.9), lin('#3f4a3a'))
    oc(tx_, ty_, 3.6); nov(tx_, ty_, 9); lm('Fire Lookout', (tx_, ty_, tz_))

    # ============================================================ coast: lighthouse, sea stacks, beach
    r = R['Lighthouse Road']; e = r['xy'][-1] + r['tan'][-1] * 24; lx, ly = float(e[0]), float(e[1]); lz = H(lx, ly); r0 = 4.6
    import isle_props as KP, isle_landmarks_hq as LQ; K_ = KP.Part(); LQ.lighthouse_hq(K_, LQ.kit_mats()); hd_ = math.atan2(-r['tan'][-1][1], -r['tan'][-1][0])
    AR.emit_model(K_, lx, ly, lz - 0.3, hd_ + math.pi / 2, 'Landmark_Lighthouse')
    oc(lx, ly, 5); nov(lx, ly, 19); lm('Lighthouse', (lx, ly, lz))
    hx0, hy0 = lx + 16 * r['left'][-1][0], ly + 16 * r['left'][-1][1]
    # art sheet 09: the keeper's cottage is part of the lighthouse model now
    for (sx0, sy0) in ((-1600, -1230), (-1500, -1350), (-1780, -960), (-1900, -640), (-1120, -1420), (-2080, -200), (2230, 160), (640, -1440), (1520, -1350), (-900, 1420), (300, 1470), (2120, -620), (-2200, 620)):
        if K.base_h(sx0, sy0) < -2:
            for q in range(rng.integers(1, 4)):
                rr = rng.uniform(10, 24); Rk.add(sphere(sx0 + rng.uniform(-30, 30), sy0 + rng.uniform(-30, 30), -6 + rr * 0.9, rr, rr * rng.uniform(.7, 1.1), rr * rng.uniform(1.3, 2.1), 8, 6, jit=0.2), lin('#7d776c') * rng.uniform(.8, 1.1))
    nu = 0
    for _ in range(4000):                                         # beach umbrellas on the south shore
        if nu >= 26: break
        x = rng.uniform(-200, 1300); y = rng.uniform(-1340, -1200); hz = H(x, y)
        if 1.6 < hz < 3.6:
            Sm.add(cyl(x, y, hz, .06, .06, 2.3, 4), WHITE); Sm.add(cone(x, y, hz + 2.0, 1.9, 0.8, 8), ccols[rng.integers(len(ccols))], solid=False); nu += 1; nov(x, y, 4)

    # ============================================================ heliport
    hx_, hy_, hz_ = K.HELI[0], K.HELI[1], K.HELI_Z
    Sm.add(cyl(hx_, hy_, hz_ - 1.5, 27, 27, 1.9, 28), lin('#6f7276')); plat(hx_, hy_, 46, 46, 0, hz_ + 0.4)
    for q0, q1 in (((-5, -7), (-5, 7)), ((5, -7), (5, 7)), ((-5, 0), (5, 0))):
        Mk.add(beam((hx_ + q0[0], hy_ + q0[1], hz_ + 0.46), (hx_ + q1[0], hy_ + q1[1], hz_ + 0.46), 1.6, 0.02), WHITE)
    for k in range(28):
        a0 = k * 2 * np.pi / 28; a1 = (k + 1) * 2 * np.pi / 28
        Mk.add(beam((hx_ + 20 * math.cos(a0), hy_ + 20 * math.sin(a0), hz_ + 0.46), (hx_ + 20 * math.cos(a1), hy_ + 20 * math.sin(a1), hz_ + 0.46), 0.8, 0.02), YEL)
    bx_, by_ = hx_ - 30, hy_ + 52
    if H(bx_, by_) > 3 and rd(bx_, by_) > 14:
        bz_ = H(bx_, by_); facade(FA, bx_, by_, bz_ - 2, 22, 11, 8.5, 0.2, lin('#e4e1d8')); S.add(box(bx_, by_, bz_ + 6.5, 23, 12, 0.4, 0.2), lin('#39424d')); ob(bx_, by_, 22, 11, 0.2); nov(bx_, by_, 18)
        S.add(cyl(bx_ + 16, by_ - 10, bz_, .12, .1, 9, 5), WHITE); D.add((np.array([(bx_ + 16, by_ - 10, bz_ + 9), (bx_ + 16, by_ - 10, bz_ + 8), (bx_ + 19.5, by_ - 10.6, bz_ + 8.3)]), np.array([(0, 1, 2)])), lin('#f08a24'), solid=False)
    hb = np.array([hx_ + 2, hy_ - 1, hz_ + 0.4])                  # helicopter on the pad
    Sm.add(sphere(hb[0], hb[1], hb[2] + 2.0, 3.3, 1.45, 1.5, 9, 6), lin('#d83a2a')); Sm.add(sphere(hb[0] + 1.9, hb[1], hb[2] + 2.15, 1.5, 1.2, 1.1, 8, 5), lin('#22303c'))
    S.add(beam(hb + (-2.6, 0, 2.3), hb + (-8.4, 0, 2.9), 0.5), lin('#d83a2a')); S.add(box(hb[0] - 8.5, hb[1], hb[2] + 2.6, 1.2, 0.14, 2.0), WHITE)
    for o_ in (-1.25, 1.25):
        S.add(beam(hb + (-2.2, o_, 0.12), hb + (2.6, o_, 0.12), 0.14), DARK)
        for a_ in (-1.2, 1.4): S.add(beam(hb + (a_, o_, 0.12), hb + (a_, o_ * 0.7, 1.0), 0.1), DARK)
    S.add(cyl(hb[0], hb[1], hb[2] + 3.4, .14, .14, 0.6, 5), DARK)
    Rt = Buf(); Rt.add(beam((-6.4, 0, 0), (6.4, 0, 0), 0.42, 0.06), DARK); Rt.add(beam((0, -6.4, 0), (0, 6.4, 0), 0.42, 0.06), DARK)
    Vw, Fw, Cw, _ = Rt.arrays(); o = make_obj('Spin_HeliRotor', Vw, Fw, Cw, None, M.vc, smooth=False); o.location = (hb[0], hb[1], hb[2] + 4.05)
    C.spinners.append(dict(name='Spin_HeliRotor', axis='y', speed=2.2, pos=[float(hb[0]), float(hb[2] + 4.05), float(-hb[1])])); oc(hb[0], hb[1], 4.2); nov(hx_, hy_, 34); lm('Heliport', (hx_, hy_ + 30, hz_))

    # ============================================================ vegetation
    cand = np.c_[rng.uniform(K.X0 + 60, K.X1 - 60, 420000), rng.uniform(K.Y0 + 60, K.Y1 - 60, 420000)]
    hc = K.sample_h(TR, cand[:, 0], cand[:, 1])
    sl = np.hypot(K.sample_h(TR, cand[:, 0] + 6, cand[:, 1]) - hc, K.sample_h(TR, cand[:, 0], cand[:, 1] + 6) - hc) / 6
    td, ti = C.G['tree'].query(cand); B = K.biomes(cand[:, 0], cand[:, 1])
    hwv = np.concatenate([np.full(rr['n'], rr['w'] / 2) for rr in roads])[ti]
    ci = (np.clip(((cand[:, 1] - K.Y0) / K.CELL + .5).astype(int), 0, K.NY - 1), np.clip(((cand[:, 0] - K.X0) / K.CELL + .5).astype(int), 0, K.NX - 1))
    ok = (hc > 2.4) & (sl < 0.75) & (td > hwv + 9) & ~C.FIELD[ci] & (B['city'] < 0.35) & ((B['circuit'] < 0.3) | (td > hwv + 42))
    nv_ = np.array([q for q in C.noveg if q[2] > 0])
    dn, ii = cKDTree(nv_[:, :2]).query(cand); ok &= dn > nv_[ii, 2]
    for lx0, ly0, lr0 in K.LAKES: ok &= np.hypot(cand[:, 0] - lx0, cand[:, 1] - ly0) > lr0 + 12
    ok &= ~((np.abs(cand[:, 0] - qx) < qw / 2 + 10) & (cand[:, 1] < qy + qd / 2 + 45) & (cand[:, 1] > qy - qd))
    dens = np.clip(0.22 + 0.9 * fbm(cand[:, 0] / 300, cand[:, 1] / 300, 3, 52), 0.03, 1) ** 1.4
    dens = np.maximum(dens, B['forest'] * 0.95)
    mtn = smoothstep(55, 95, hc) * (1 - B['desert'])
    dens = np.where(mtn > 0.5, 0.55 * smoothstep(205, 120, hc), dens)
    dens = np.where(B['desert'] > 0.5, 0.05, dens); dens = np.where(hc < 8, 0.3 * (B['desert'] < 0.5), dens)
    dens = np.where(B['country'] > 0.5, dens * 0.45, dens)
    ok &= rng.random(len(cand)) < dens * 0.95
    kind = np.where(B['desert'] > 0.5, 3, np.where((hc < 8) & (cand[:, 1] < 250), 2, np.where((B['forest'] > 0.4) | (mtn > 0.5), 0, 1)))
    kind = np.where((kind == 1) & (rng.random(len(cand)) < 0.22), 0, kind)
    u_ = rng.random(len(cand)); kind = np.where((kind == 1) & (B['country'] > 0.4) & (u_ < 0.4), 5, kind)
    kind = np.where((kind == 0) & (B['forest'] > 0.3) & (mtn < 0.5) & (u_ < 0.2), 6, kind)
    cap = {0: 5400, 1: 1800, 2: 420, 3: 330, 5: 300, 6: 800}; cnt = {0: 0, 1: 0, 2: 0, 3: 0, 5: 0, 6: 0}
    TRUNK = lin('#5a4330'); pts = []
    for q in np.where(ok)[0]:
        k = int(kind[q])
        if cnt[k] < cap[k]: cnt[k] += 1; pts.append((cand[q, 0], cand[q, 1], hc[q], k))
    for px, py in park_trees: pts.append((px, py, cz + 0.2, 1)); cnt[1] += 1
    for a in range(9):                                            # orchard rows
        for b in range(6):
            px, py = 830 + 13 * a + 4 * b, -985 + 12 * b - 3 * a
            if rd(px, py) > 9 and H(px, py) > 4: pts.append((px, py, H(px, py), 4))
    cards = []; inst = C.inst
    for px, py, pz, k in pts:
        sc = rng.uniform(0.8, 1.35); pz -= 0.4
        if k == 2:
            hgt = rng.uniform(9, 13) * sc; v = rng.uniform(.85, 1.0); cards.append((px, py, pz, hgt, hgt * 0.95, 5, 7, 0.9, v, v, v))
        elif k == 0:
            hgt = rng.uniform(13, 24) * sc; snowy = pz + rng.uniform(-10, 10) > 140; v = rng.uniform(.72, 1.0)
            cards.append((px, py, pz, hgt, hgt * 0.5, 3 if snowy else int(rng.integers(0, 2)), 6, 0.3, v, v * rng.uniform(.94, 1.0), v))
        elif k == 6:
            hgt = rng.uniform(11, 17) * sc; v = rng.uniform(.8, 1.0); cards.append((px, py, pz, hgt, hgt * 0.6, 4, 7, 0.66, v, v, v * 0.92))
        elif k in (1, 4):
            hgt = (rng.uniform(9, 16) * sc) if k == 1 else rng.uniform(4.6, 6.0)
            cards.append((px, py, pz, hgt, hgt * 0.98, 2, 7, 0.62, rng.uniform(.75, 1.0), rng.uniform(.85, 1.0), rng.uniform(.6, 0.95)))
        elif k == 3:                                             # cactus or desert shrub
            if rng.random() < 0.6:
                hgt = rng.uniform(3.5, 7); gc = rng.uniform(.85, 1.1)
                for sgn in (-1, 1):
                    if rng.random() < 0.75: rng.uniform(0, 3.14); rng.uniform(.35, .55)
                inst.append(('cactus' if len(inst) % 2 else 'cactus_b', px, py, pz + 0.3, hgt / 5.6, gc, gc, gc))
            else: v = [rng.uniform(.9, 1.6), rng.uniform(.9, 1.6), rng.uniform(.6, 1)]; L.rng.uniform(-.2, .2, (20, 1)); v.append(rng.uniform(.8, 1.1)); inst.append(('bush', px, py, pz + 0.3, v[0] * 0.9, 1.0 * v[3], 0.92 * v[3], 0.6 * v[3]))
        elif k == 5:                                             # cypress
            hgt = rng.uniform(11, 17) * sc; gc = rng.uniform(.85, 1.15); inst.append(('cypress', px, py, pz + 0.2, hgt / 14.0, gc, gc, gc))
    C.cards = cards
    okb = (hc > 2.6) & (hc < 120) & (sl < 0.6) & (td > hwv + 5) & ~C.FIELD[ci] & (B['city'] < 0.3) & (B['circuit'] < 0.3) & (B['desert'] < 0.4) & (dn > nv_[ii, 2])
    for lx0, ly0, lr0 in K.LAKES: okb &= np.hypot(cand[:, 0] - lx0, cand[:, 1] - ly0) > lr0 + 6
    idb = np.where(okb & (rng.random(len(cand)) < 0.03))[0][:1300]; fcol = [lin(c) for c in ('#d8452f', '#e8c63a', '#f2f0e6', '#8a5fb5', '#e58aa5')]
    for q in idb[:850]:
        rr_ = rng.uniform(.9, 1.9); L.rng.uniform(-.15, .15, (12, 1)); g_ = (1.0, 1.12, 0.9)[rng.integers(3)] * rng.uniform(.85, 1.1); inst.append(('bush', cand[q, 0], cand[q, 1], hc[q] - 0.05, rr_ * 0.95, g_, g_, g_))
    for q in idb[850:]:
        for _ in range(3):
            fx_, fy_ = cand[q, 0] + rng.uniform(-1.6, 1.6), cand[q, 1] + rng.uniform(-1.6, 1.6); fs_ = rng.uniform(.5, .9); inst.append((('flowers_red', 'flowers_white', 'flowers_white', 'flowers_violet', 'flowers_red')[rng.integers(5)], fx_, fy_, float(K.sample_h(TR, fx_, fy_)), fs_ * 1.5, 1, 1, 1))
    L.STATS['trees'] = dict(pine=cnt[0], broadleaf=cnt[1], palm=cnt[2], desert=cnt[3], cypress=cnt[5], birch=cnt[6], bushes=min(850, len(idb)), flower_patches=max(0, len(idb) - 850))

    # ============================================================ rocks
    c2 = np.c_[rng.uniform(K.X0 + 60, K.X1 - 60, 60000), rng.uniform(K.Y0 + 60, K.Y1 - 60, 60000)]; h2 = K.sample_h(TR, c2[:, 0], c2[:, 1])
    s2 = np.hypot(K.sample_h(TR, c2[:, 0] + 6, c2[:, 1]) - h2, K.sample_h(TR, c2[:, 0], c2[:, 1] + 6) - h2) / 6
    d2 = C.G['tree'].query(c2)[0]; B2 = K.biomes(c2[:, 0], c2[:, 1]); u = rng.random(len(c2))
    okr = (d2 > 16) & (B2['city'] < 0.3) & (B2['circuit'] < 0.3) & (((h2 > -1) & (h2 < 3.5) & (u < 0.12)) | ((s2 > 0.5) & (h2 > 4) & (u < 0.35)) | ((B2['desert'] > 0.6) & (h2 > 4) & (u < 0.05)))
    for (px, py), pz, dsr in zip(c2[okr][:520], h2[okr][:520], B2['desert'][okr][:520]):
        rr = rng.uniform(1.0, 4.5); tall = dsr > 0.6 and rng.random() < 0.3
        colr = lin('#b3683d') if dsr > 0.6 else (lin('#857d70') if pz < 120 else lin('#9a9a9c'))
        v = (rng.uniform(.8, 1.3), rng.uniform(.8, 1.3), (rng.uniform(1.8, 3.2) if tall else rng.uniform(.55, .9))); L.rng.uniform(-.22, .22, (20, 1)); g_ = rng.uniform(0.75, 1.1)
        sp_ = ('sandstone_spire' if tall else 'sandstone') if dsr > 0.6 else ('rock', 'rock_b', 'rock_c')[len(C.inst) % 3]; tn_ = (1.0, 1.0, 1.0) if pz < 120 or dsr > 0.6 else (1.25, 1.27, 1.32)
        C.inst.append((sp_, px, py, pz - rr * 0.12, rr * (v[0] + v[1]) / 2 * (0.62 * v[2] if tall else 1.0), g_ * tn_[0], g_ * tn_[1], g_ * tn_[2]))

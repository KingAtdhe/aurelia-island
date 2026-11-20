"""Stage 2 detail for Aurelia Island: hero towers, facade detail, street furniture, signs, parking, river assets,
vineyard, coastal village, desert settlement, viewpoints, roundabout islands, technical organisation."""
import math, bpy
import numpy as np
import isle_data as K
import isle_arch as AR
import isle_lib as L
from isle_lib import lin, box, beam, cyl, cone, tube, sphere, roof, lathe, Buf, make_obj
from isle_data import smoothstep, fbm

rng = np.random.default_rng(777)
CAR_COLS = ['#b3241d', '#1f3f7a', '#e8e8e4', '#2b2d31', '#8a8f96', '#d9a521', '#2f6b45', '#f4f4f0', '#5a1f1f', '#3b8fa3']


def facade_poly(buf, pts, z, h, color, bay=3.6, floor=3.9, top=1.0):
    pts = np.asarray(pts, float); c = pts.mean(0); n = len(pts); tp = c + (pts - c) * top
    per = np.concatenate([[0], np.cumsum(np.linalg.norm(np.roll(pts, -1, 0) - pts, axis=1))])
    tot = max(1, round(per[-1] / bay)); nv = max(1, round(h / floor))
    for k in range(n):
        a, b = pts[k], pts[(k + 1) % n]; ta, tb = tp[k], tp[(k + 1) % n]
        u0, u1 = per[k] / per[-1] * tot, per[k + 1] / per[-1] * tot
        Vq = np.array([(a[0], a[1], z), (b[0], b[1], z), (tb[0], tb[1], z + h), (ta[0], ta[1], z + h)])
        buf.add((Vq, np.array([(0, 1, 2), (0, 2, 3)])), color, solid=False, uv=np.array([(u0, 0), (u1, 0), (u1, nv), (u0, nv)]))
    return tp


def cap_poly(buf, pts, z, color):
    pts = np.asarray(pts, float); c = pts.mean(0); n = len(pts)
    V = np.vstack([np.c_[pts, np.full(n, z)], [[c[0], c[1], z]]])
    buf.add((V, np.array([(i, (i + 1) % n, n) for i in range(n)])), color, solid=False)


def rect(x, y, sx, sy, yaw=0.0):
    c, s = math.cos(yaw), math.sin(yaw)
    return [(x + a * c - b * s, y + a * s + b * c) for a, b in ((-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2))]


def flat_quad(buf, p0, p1, w, z, color):
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float); d = p1 - p0; d /= np.linalg.norm(d); nrm = np.array([-d[1], d[0]]) * w / 2
    V = np.array([(*(p0 - nrm), z), (*(p1 - nrm), z), (*(p1 + nrm), z), (*(p0 + nrm), z)])
    buf.add((V, np.array([(0, 1, 2), (0, 2, 3)])), color, solid=False)


def pre(C):
    C.bld = []; C.hero_n = 0; C.houses = []; C.lamps = []
    S, FB = C.S, C.FB; cz = K.CITY_Z + 0.15
    glass = [lin(c) for c in ('#86aecf', '#9cc0c9', '#7391b3', '#a9bccb', '#8fb39f')]
    DK = lin('#3d4249')

    def hero(x, y, sx, sy, h):
        k = C.hero_n % 5; C.hero_n += 1; col = glass[k] * rng.uniform(0.9, 1.1); r = min(sx, sy) / 2
        if k == 0:                                             # round tower with a crown ring and mast
            pts = [(x + r * math.cos(a), y + r * math.sin(a)) for a in np.arange(24) * 2 * np.pi / 24]
            AR.curtain(C, pts, cz, h, col); cap_poly(S, pts, cz + h, DK)
            C.Sm.add(cyl(x, y, cz + h, r * 0.82, r * 0.82, 4.5, 24), lin('#cfd4d8')); C.Sm.add(cyl(x, y, cz + h + 4.5, r * 0.5, r * 0.3, 7, 16), DK)
            S.add(cyl(x, y, cz + h + 11.5, 0.45, 0.1, h * 0.2, 6), lin('#d7d9dc'))
        elif k == 1:                                           # tapering tower with a glass pyramid
            tp = AR.curtain(C, rect(x, y, sx, sy), cz, h, col, top=0.62); cap_poly(S, tp, cz + h, DK)
            V = np.vstack([np.c_[tp, np.full(4, cz + h)], [[x, y, cz + h + sx * 0.45]]])
            FB.add((V, np.array([(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)])), col * 1.1, solid=False, uv=np.array([(0, 0), (4, 0), (0, 0), (4, 0), (2, 4)], float))
        elif k == 2:                                           # twin slabs joined by a sky bridge
            w = sx * 0.4
            for sgn, hh in ((-1, h), (1, h * 0.84)):
                pts = rect(x + sgn * sx * 0.3, y, w, sy); AR.curtain(C, pts, cz, hh, col * (1.0 if sgn < 0 else 0.92)); cap_poly(S, pts, cz + hh, DK)
                S.add(box(x + sgn * sx * 0.3, y, cz + hh, w * 0.6, sy * 0.5, 3.2), lin('#8b8f93'))
            facade_poly(FB, rect(x, y, sx * 0.24, sy * 0.4), cz + h * 0.55, 7.8, col * 0.8); S.add(box(x, y, cz + h * 0.55 + 7.8, sx * 0.26, sy * 0.42, 0.4), DK)
            S.add(box(x, y, cz + h * 0.55 - 0.4, sx * 0.26, sy * 0.42, 0.4), DK)
        elif k == 3:                                           # three tiers, each turned 45 degrees
            zz = cz; w = sx
            for t_, f in enumerate((0.45, 0.33, 0.22)):
                pts = rect(x, y, w, w, t_ * math.pi / 4); AR.curtain(C, pts, zz, h * f, col * (1 - 0.05 * t_)); cap_poly(S, pts, zz + h * f, DK); zz += h * f; w *= 0.74
            S.add(cyl(x, y, zz, 0.5, 0.12, h * 0.18, 6), lin('#d7d9dc'))
        else:                                                  # slab with a sloped crown
            pts = rect(x, y, sx, sy * 0.7); AR.curtain(C, pts, cz, h, col); cap_poly(S, pts, cz + h, DK)
            S.add(roof(x, y, cz + h, sx, sy * 0.7, 9, 0, 0.0), lin('#aeb6bd')); S.add(cyl(x - sx * 0.3, y, cz + h + 4, 0.35, 0.1, 22, 5), lin('#d7d9dc'))
        S.add(box(x, y, cz - 0.1, sx + 3.2, sy + 3.2, 5.2), lin('#3a3d42')); S.add(box(x, y, cz + 5.1, sx + 4.6, sy + 4.6, 0.35), lin('#4a4f57'))      # podium with a glazed ground floor
        Rp = AR.rect(x, y, sx + 4, sy + 4)
        for k_ in range(4): AR.wall(Rp[k_], Rp[(k_ + 1) % 4], cz - 0.1, 5.2, 1, 6.0, (3, 3, 1), lin('#8d9299'), 'plaster', None, depth=0.3, shop=True)
        C.obst.append([x, -y, sx / 2 + 2, sy / 2 + 2, 0.0]); C.bld.append(('hero', x, y, sx + 4, sy + 4, h, 0.0, cz))
        return True
    C.hero = hero
    for a in ((620, -1020, 92), (-1835, -470, 95), (1300, 455, 70), (1580, 790, 30), (1560, 470, 28), (1345, 690, 12), (518, -190, 62)): C.noveg.append(a)
    for R in K.get_rivers():
        for p in R['xy'][::3]: C.noveg.append((p[0], p[1], R['hw'] + 5.5))
    for cx, cy, rr in K.ROUNDABOUTS: C.noveg.append((cx, cy, rr + 12))


def post(C):
    S, Sm, FA, D, Rk, Mk, M, PR = C.S, C.Sm, C.FA, C.V, C.Rk, C.Mk, C.M, C.PR
    H = C.hgt; P = C.P; roads = C.roads; R = {r['name']: r for r in roads}
    CONC, STEEL, WHITE, RED, DARK = (C.col[k] for k in ('CONC', 'STEEL', 'WHITE', 'RED', 'DARK'))
    YEL = lin('#f2c230'); WOOD = lin('#8a6a48'); BLUE = lin('#2b5fae'); GREEN = lin('#2f9a57')
    rd = lambda x, y: float(C.G['tree'].query([x, y])[0])
    cz = K.CITY_Z
    def plat(x, y, sx, sy, yaw, top): C.plats.append([x, -y, sx / 2, sy / 2, yaw, top])
    n_ = dict(lamps=0, signs=0, lights=0, poles=0, cars=0, balcony=0)

    # ---------------------------------------------------------------- building detail
    for kind, x, y, sx, sy, h, yaw, z in C.bld:
        c, s = math.cos(yaw), math.sin(yaw)
        def loc(a, b, zz=0.0): return (x + a * c - b * s, y + a * s + b * c, z + zz)
        if kind == 'mid':
            if h < 36 and rng.random() < 0.5:                 # residential: balcony slabs with glass rails on both long sides
                long_x = sx >= sy; ln = (sx if long_x else sy) * 0.78; dep = (sy if long_x else sx) / 2
                for fl in range(1, int(h / 3.6)):
                    for sgn in (-1, 1):
                        p = loc(0, sgn * (dep + 0.55)) if long_x else loc(sgn * (dep + 0.55), 0)
                        yw = yaw if long_x else yaw + math.pi / 2
                        S.add(box(p[0], p[1], z + fl * 3.6 - 0.1, ln, 1.1, 0.16, yw), lin('#d9d6cf'))
                        q = loc(0, sgn * (dep + 1.05)) if long_x else loc(sgn * (dep + 1.05), 0)
                        S.add(box(q[0], q[1], z + fl * 3.6 + 0.06, ln, 0.06, 0.95, yw), lin('#7fa0b5')); n_['balcony'] += 1
            for _ in range(rng.integers(2, 6)):               # rooftop air-conditioning units
                p = loc(rng.uniform(-sx / 2 + 2, sx / 2 - 2), rng.uniform(-sy / 2 + 2, sy / 2 - 2), h + 0.55)
                S.add(box(p[0], p[1], p[2], 1.6, 1.1, 0.95, yaw), lin('#b9bcc0')); S.add(cyl(p[0], p[1], p[2] + 0.95, .38, .38, .08, 8), DARK)
            p = loc(0, -sy / 2 - 1.3, 3.3); S.add(box(p[0], p[1], p[2], min(7, sx * .4), 2.6, 0.22, yaw), lin('#3f444b'))      # entrance canopy and doors
            p = loc(0, -sy / 2 - 0.06, 0.0); S.add(box(p[0], p[1], p[2], min(5, sx * .3), 0.12, 3.0, yaw), lin('#1f2a33'))
        elif kind == 'tower':
            p = loc(0, -sy / 2 - 2.0, 5.0); S.add(box(p[0], p[1], p[2], sx * .5, 4.0, 0.3, yaw), lin('#3f444b'))
            for sgn in (-1, 1):
                q = loc(sgn * sx * .22, -sy / 2 - 3.6, 0); S.add(cyl(q[0], q[1], q[2], .28, .28, 5.0, 8), lin('#c9ccd0'))
            p = loc(0, -sy / 2 - 0.06, 0.0); S.add(box(p[0], p[1], p[2], sx * .34, 0.12, 4.4, yaw), lin('#17212b'))
    # multi-storey car park and a hotel sign on two edge buildings
    gx, gy = 568.0, 150.0
    if rd(gx, gy) > 22 and abs(H(gx, gy) - cz) < 1:
        for fl in range(5):
            S.add(box(gx, gy, cz - 0.4 + fl * 3.1, 46, 30, 0.4), CONC)
            for a in np.linspace(-21, 21, 7):
                for b in (-14, 0, 14): S.add(box(gx + a, gy + b, cz + fl * 3.1, .6, .6, 2.7), lin('#a9a69d'))
            for sgn in (-1, 1): S.add(box(gx, gy + sgn * 14.8, cz + fl * 3.1, 46, .25, 1.0), lin('#c9c6bd'))
        S.add(box(gx - 26, gy, cz - 0.5, 8, 9, 0.5), lin('#3b3d41')); S.add(box(gx + 19, gy + 11, cz, 5, 5, 17.5), lin('#5f6770'))
        C.obst.append([gx, -gy, 23, 15, 0.0]); C.landmarks.append(('City Car Park', np.array([gx, gy, cz])))

    # ---------------------------------------------------------------- city street furniture
    def lamp(x, y, z, yaw, hgt=8.0, arm=2.2):
        import isle_props as KP, isle_props_hq as HQ
        if HQ.oldtown(x, y):                                                                                 # old town: heritage lantern lamp (art sheet 03), lanterns at 4-5 m
            KP.KIT.append(('lamp_city_hq', x, y, z - 0.05, yaw)); e = (x, y, z + 4.75)
        else:
            KP.KIT.append(('lamp', x, y, z - 0.05, yaw))                                                       # modelled street lamp (kit), luminaire 2.45 m out at 8.3 m
            e = (x + 2.45 * math.cos(yaw), y + 2.45 * math.sin(yaw), z + 8.3)
        n_['lamps'] += 1; C.lamps.append((e[0], e[2] - 0.15, -e[1]))
        if n_['lamps'] % 3 == 0: KP.KIT.append(('hydrant', x + 1.2 * math.cos(yaw + 1.5708), y + 1.2 * math.sin(yaw + 1.5708), z - 0.05, yaw))
    for r in roads:
        if r['type'] != 'street': continue
        hw = r['w'] / 2
        for i in range(4, r['n'] - 2, 8):
            if r['junction'][max(0, i - 2):i + 3].any(): continue
            for side in (-1, 1):
                j = i + (4 if side > 0 else 0)
                if j >= r['n'] - 2 or r['junction'][max(0, j - 2):j + 3].any(): continue
                p = P(r, j, side * (hw + 1.6)); lamp(p[0], p[1], p[2] + 0.15, r['head'][j] + (math.pi / 2 if side < 0 else -math.pi / 2))
    for x in K.SX:
        for y in K.SY:
            z = cz
            for sx_, sy_ in ((1, 1), (-1, -1)):                # traffic lights on two corners
                px, py = x + sx_ * 7.6, y + sy_ * 7.6
                import isle_props as KP; KP.KIT.append(('signal', px, py, z + 0.12, math.pi if sx_ > 0 else 0.0))
                n_['lights'] += 1
            import isle_props_hq as HQ
            if HQ.oldtown(x, y):                               # cast-iron bollards guarding each corner beside the crossings
                for cx_, cy_ in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                    for ax_, ay_ in ((11.4, 6.6), (6.6, 11.4)):
                        bx_, by_ = x + cx_ * ax_, y + cy_ * ay_
                        if K.SX[0] - 1 <= bx_ <= K.SX[-1] + 1 and K.SY[0] - 1 <= by_ <= K.SY[-1] + 1: KP.KIT.append(('bollard', bx_, by_, z + 0.16, 0.0)); n_['bollards'] = n_.get('bollards', 0) + 1
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):  # pedestrian crossings
                if not (K.SX[0] <= x + dx * 20 <= K.SX[-1] and K.SY[0] <= y + dy * 20 <= K.SY[-1]): continue
                for k in range(-4, 5):
                    o = k * 1.2; cx_ = x + dx * 9.4 - dy * o; cy_ = y + dy * 9.4 + dx * o
                    flat_quad(Mk, (cx_ - dx * 1.5, cy_ - dy * 1.5), (cx_ + dx * 1.5, cy_ + dy * 1.5), 0.55, z + 0.07, WHITE)
    C.walk = []                                                  # pavement lines the game's walkers follow (game axes: x, z = -y)
    for i in range(len(K.SX) - 1):
        for j in range(len(K.SY)):
            for o in (-8.6, 8.6): C.walk.append([round(K.SX[i] + 9, 1), round(-(K.SY[j] + o), 1), round(K.SX[i + 1] - 9, 1), round(-(K.SY[j] + o), 1), round(cz + 0.16, 2)])
    for i in range(len(K.SX)):
        for j in range(len(K.SY) - 1):
            for o in (-8.6, 8.6): C.walk.append([round(K.SX[i] + o, 1), round(-(K.SY[j] + 9), 1), round(K.SX[i] + o, 1), round(-(K.SY[j + 1] - 9), 1), round(cz + 0.16, 2)])
    for i in range(len(K.SX) - 1):                             # benches, bins and planters on the pavements
        for j in range(len(K.SY) - 1):
            x0, x1 = K.SX[i] + 9, K.SX[i + 1] - 9; y0 = K.SY[j] + 8.6
            for q in range(3):
                bx = x0 + (x1 - x0) * (q + 0.5) / 3 + rng.uniform(-6, 6)
                import isle_props as KP; KP.KIT.append(('bench', bx, y0, cz + 0.16, -math.pi / 2)); KP.KIT.append(('bin', bx + 2.2, y0, cz + 0.16, 0.0))
                u_ = rng.random(); zc_ = cz + 0.16                                                         # street life along the pavement
                if u_ < 0.35: KP.KIT.append(('cafe', bx + 6.5, y0 + 2.6, zc_, 0.0)); KP.KIT.append(('cafe', bx + 9.5, y0 + 2.6, zc_, 1.0)); KP.KIT.append(('person_%d' % (q % 4), bx + 7.3, y0 + 3.4, zc_, -2.0))
                elif u_ < 0.6: KP.KIT.append(('bikerack', bx + 6.5, y0 - 0.6, zc_, 0.0 + math.pi / 2))
                elif u_ < 0.8: KP.KIT.append(('planter', bx + 6.0, y0 + 0.4, zc_, 0.0)); KP.KIT.append(('fountain' if (i + j + q) % 3 == 0 else 'planter', bx + 9.0, y0 + 0.4, zc_, -math.pi / 2))
                else: KP.KIT.append(('kiosk', bx + 7.0, y0 + 1.2, zc_, -math.pi / 2)); KP.KIT.append(('person_%d' % ((q + 1) % 4), bx + 7.0, y0 - 0.6, zc_, math.pi / 2))
                for _k in range(int(rng.integers(0, 3))): KP.KIT.append(('scooter', bx - 6.0 - _k * 1.0, y0 - 1.1, zc_, 0.0, tuple([(0.85, 0.15, 0.12), (0.15, 0.3, 0.6), (0.95, 0.95, 0.92), (0.2, 0.2, 0.22)][int(rng.integers(4))])))
                if rng.random() < 0.5: KP.KIT.append(('person_%d' % int(rng.integers(4)), bx + rng.uniform(-3, 3), y0 + 1.5, zc_, rng.uniform(0, 6.28)))
                PR.add(box(bx - 3.4, y0 + 0.1, cz + 0.16, 1.5, 1.5, 0.55), CONC); C.inst.append(('bush', bx - 3.4, y0 + 0.1, cz + 0.7, 0.8, 0.9, 1.0, 0.8))
            y1 = K.SY[j + 1] - 8.6; zc_ = cz + 0.16                                                        # the opposite pavement gets everyday clutter
            for q in range(4):
                bx = x0 + (x1 - x0) * (q + 0.5) / 4 + rng.uniform(-5, 5); u_ = rng.random()
                if u_ < 0.25: KP.KIT.append(('newsbox', bx, y1 - 0.4, zc_, math.pi))
                elif u_ < 0.45: KP.KIT.append(('trashbags', bx, y1 + 2.2, zc_, rng.uniform(0, 6)))
                elif u_ < 0.6: KP.KIT.append(('phonebooth', bx, y1 + 0.2, zc_, math.pi / 2))
                elif u_ < 0.72: KP.KIT.append(('cones', bx, y1 - 2.2, zc_, 0.0))
                elif u_ < 0.85: KP.KIT.append(('mailbox', bx, y1 - 0.5, zc_, math.pi / 2))
                else: KP.KIT.append(('bench', bx, y1, zc_, math.pi / 2)); KP.KIT.append(('person_%d' % int(rng.integers(4)), bx + 1.0, y1 + 1.0, zc_, rng.uniform(0, 6.28)))
                if rng.random() < 0.4: KP.KIT.append(('bin', bx + 3.0, y1 - 0.3, zc_, 0.0))
    # ---------------------------------------------------------------- roundabout islands
    for (cx, cy, rr), r in zip(K.ROUNDABOUTS, [R['Mesa Roundabout'], R['Farm Roundabout']]):
        z = float(r['z'].mean()); ri = rr - r['w'] / 2 - 0.4
        import isle_props as KPr; Sm.add(cyl(cx, cy, z - 1.2, ri - 0.2, ri - 0.2, 1.25, 28), lin('#8f8c84'))     # art sheet 08: modelled island (setts apron, planted mound, cypress group, chevrons)
        KPr.KIT.append(('rk_island_%d' % int(round(round(rr - r['w'] / 2 - 0.4, 1) * 10)), cx, cy, z + 0.01, 0.0))
        C.circ.append([cx, -cy, ri - 0.4]); C.landmarks.append((r['name'], np.array([cx + rr + 20, cy, z])))

    # ---------------------------------------------------------------- road signs, arrows, billboards
    def sign(r, i, kind):
        hw = r['w'] / 2; p = P(r, i, -(hw + 2.3)); hd = r['head'][i % r['n']]; z = H(p[0], p[1]) if not r['bridge'][i % r['n']] else p[2]
        import isle_props as KP; k_ = n_['signs']
        nm = (('sign_speed80' if r['type'] == 'hwy' else 'sign_speed'), ('sign_curve', 'sign_bend')[k_ % 2], ('board_a', 'board_b', 'board_c')[k_ % 3])[kind]
        KP.KIT.append((nm, p[0], p[1], z - 0.02, hd + math.pi))
        n_['signs'] += 1
    for r in roads:
        if r['type'] not in ('hwy', 'road'): continue
        jm = r['junction']; n = r['n']
        for i in range(30, n - 12, 64):
            if r['tunnel'][i] or jm[max(0, i - 3):i + 4].any(): continue
            hd = np.unwrap(r['head'][max(0, i):min(n, i + 26)]); sign(r, i, 1 if abs(hd[-1] - hd[0]) > 0.5 else 0)
        for j in np.where(jm)[0]:                              # direction boards and lane arrows before junctions
            i = j - 14
            if i < 4 or jm[i - 3:i + 4].any() or r['tunnel'][i] or r['bridge'][i]: continue
            if rng.random() < 0.6: sign(r, i, 2)
            pa = P(r, i, -r['w'] / 4 if r['type'] == 'road' else -5.2, 0.07); t = r['tan'][i]
            flat_quad(Mk, pa[:2] - t * 2.2, pa[:2] + t * 1.0, 0.22, pa[2], WHITE)
            lf = np.array([-t[1], t[0]]); Va = np.array([(*(pa[:2] + t * 1.0 - lf * .5), pa[2]), (*(pa[:2] + t * 2.6), pa[2]), (*(pa[:2] + t * 1.0 + lf * .5), pa[2])])
            Mk.add((Va, np.array([(0, 1, 2)])), WHITE, solid=False)
    ring = roads[0]; pal = [lin(c) for c in ('#e0a526', '#2b5fae', '#c5261f', '#2f9a57', '#7a3fa0', '#e8e4d8', '#1f8f9c')]
    for k, i in enumerate(range(90, ring['n'], 148)):
        if ring['bridge'][i] or ring['tunnel'][i]: continue
        side = 1 if k % 2 else -1; p = P(ring, i, side * 15); z = H(p[0], p[1]); hd = ring['head'][i] + 0.35 * side
        if z < 3: continue
        lf = (-math.sin(hd), math.cos(hd))
        for o in (-4, 4): PR.add(tube(p[0] + lf[0] * o, p[1] + lf[1] * o, z - 0.5, .22, .18, 7.5, 5), STEEL, solid=False)
        PR.add(box(p[0], p[1], z + 5.0, 0.3, 13, 5.6, hd), lin('#22262b')); f = (math.cos(hd), math.sin(hd)); c0 = pal[k % len(pal)]
        for sg in (-1, 1):                                     # abstract graphic panels, no lettering
            b = (p[0] - sg * 0.17 * f[0], p[1] - sg * 0.17 * f[1])
            PR.add(box(b[0], b[1], z + 5.25, 0.06, 12.4, 5.1, hd), c0); PR.add(box(b[0] - sg * .04 * f[0] + lf[0] * 2.8, b[1] - sg * .04 * f[1] + lf[1] * 2.8, z + 6.2, 0.05, 4.4, 2.6, hd), pal[(k + 3) % len(pal)])
            PR.add(box(b[0] - sg * .04 * f[0] - lf[0] * 3.0, b[1] - sg * .04 * f[1] - lf[1] * 3.0, z + 6.0, 0.05, 3.6, 0.7, hd), WHITE)
        C.circ.append([p[0], -p[1], 1.2])

    # ---------------------------------------------------------------- utility poles with wires
    for name, side in (('Farm Road', 1), ('West Avenue', 1), ('Peninsula Road', -1), ('Mesa Road', 1), ('Lake Trail', -1)):
        r = R[name]; hw = r['w'] / 2; prev = None
        for i in range(6, r['n'] - 4, 9):
            if r['bridge'][i] or r['tunnel'][i] or r['junction'][i - 2:i + 3].any(): prev = None; continue
            p = P(r, i, side * (hw + 6.5)); z = H(p[0], p[1]); hd = r['head'][i]; lf = np.array([-math.sin(hd), math.cos(hd), 0])
            import isle_props as KP; KP.KIT.append(('power_pole', p[0], p[1], z, hd)); top = np.array([p[0], p[1], z + 9.18]); n_['poles'] += 1
            if prev is not None:
                for o in (-1.15, 0, 1.15): PR.add(beam(prev[0] + prev[1] * o + (0, 0, .12), top + lf * o + (0, 0, .12), 0.05), lin('#1d1f22'))
            prev = (top, lf)

    # ---------------------------------------------------------------- parking areas with painted bays and parked cars
    def parked(x, y, z, yaw):
        col = lin(CAR_COLS[rng.integers(len(CAR_COLS))]); import isle_stage7 as S7; S7.car_mesh(Sm, x, y, z, yaw, col, n_['cars'] % 3)
        n_['cars'] += 1
    def car_park(x, y, sx, sy, yaw, fill=0.4):
        hs = [H(*q) for q in rect(x, y, sx, sy, yaw)] + [H(x, y)]; top = max(hs) + 0.12
        S.add(box(x, y, top - 3.2, sx, sy, 3.2, yaw), lin('#3b3d41')); plat(x, y, sx, sy, yaw, top); c, s = math.cos(yaw), math.sin(yaw)
        for row, yy in enumerate((-sy / 2 + 2.7, sy / 2 - 2.7)):
            for k in range(int((sx - 4) / 2.7) + 1):
                a = -sx / 2 + 2 + k * 2.7; p0 = (x + a * c - (yy - 2.5) * s, y + a * s + (yy - 2.5) * c); p1 = (x + a * c - (yy + 2.5) * s, y + a * s + (yy + 2.5) * c)
                flat_quad(Mk, p0, p1, 0.12, top + 0.06, WHITE)
                if rng.random() < fill and k < int((sx - 4) / 2.7):
                    b = a + 1.35; parked(x + b * c - yy * s, y + b * s + yy * c, top, yaw + math.pi / 2 + (0 if row else math.pi))
    car_park(518, -190, 110, 48, math.pi / 2, 0.45)
    r = R['Circuit']; i0 = C.circuit_start; o = r['xy'][i0] + r['left'][i0] * 58
    car_park(float(o[0]), float(o[1]), 210, 34, float(r['head'][i0]), 0.5)
    car_park(K.HELI[0] - 62, K.HELI[1] + 22, 44, 30, 0.2, 0.3)
    car_park(-150, -352, 150, 24, 0.0, 0.35)

    # ---------------------------------------------------------------- river: stone bridges get abutments, a wooden footbridge, reeds
    RV = K.get_river(); im = len(RV['xy']) // 2 + 6; pm = RV['xy'][im]; tv = RV['xy'][im + 1] - RV['xy'][im - 1]; tv /= np.linalg.norm(tv); nv = np.array([-tv[1], tv[0]])
    a0 = pm - nv * 15; a1 = pm + nv * 15; zb = max(H(*a0), H(*a1)) + 0.3
    for k in range(10):
        u0, u1 = k / 10, (k + 1) / 10; h0 = 1.6 * math.sin(math.pi * u0); h1 = 1.6 * math.sin(math.pi * u1)
        q0 = a0 + (a1 - a0) * u0; q1 = a0 + (a1 - a0) * u1
        S.add(beam((q0[0], q0[1], zb + h0), (q1[0], q1[1], zb + h1), 2.6, 0.22), WOOD)
        for sg in (-1.25, 1.25):
            S.add(beam((q0[0] + tv[0] * sg, q0[1] + tv[1] * sg, zb + h0 + 1.0), (q1[0] + tv[0] * sg, q1[1] + tv[1] * sg, zb + h1 + 1.0), 0.1), lin('#6b4f33'))
            S.add(beam((q0[0] + tv[0] * sg, q0[1] + tv[1] * sg, zb + h0), (q0[0] + tv[0] * sg, q0[1] + tv[1] * sg, zb + h0 + 1.0), 0.1), lin('#6b4f33'))
    C.landmarks.append(('River Footbridge', np.array([pm[0], pm[1], zb])))
    for q in range(0, len(RV['xy']) - 6, 2):
        p = RV['xy'][q] + rng.normal(0, 1, 2) + nv * rng.choice([-9.5, 9.5])
        if rd(p[0], p[1]) > 9 and RV['lvl'][q] > 0.5: C.inst.append(('grass_tall', p[0], p[1], H(p[0], p[1]) - 0.05, 1.7 * rng.uniform(.8, 1.1), 1, 1, 0.8))

    # ---------------------------------------------------------------- vineyard, farm fences
    vx, vy, va = 620.0, -1020.0, 0.2; c, s = math.cos(va), math.sin(va)
    for row in range(-14, 15):
        for k in range(-7, 7):
            x = vx + (k * 8 + 4) * c - row * 4.6 * s; y = vy + (k * 8 + 4) * s + row * 4.6 * c
            if rd(x, y) < 10 or H(x, y) < 5: continue
            D.add(box(x, y, H(x, y) - 0.2, 7.6, 0.75, 1.55, va), lin('#4f7f33') * rng.uniform(.85, 1.1))
            if k % 2 == 0: PR.add(box(x - 3.9 * c, y - 3.9 * s, H(x, y) - 0.2, .12, .12, 1.9), WOOD)
    hz = H(vx - 70, vy + 62)
    if rd(vx - 70, vy + 62) > 14: S.add(box(vx - 70, vy + 62, hz - 2, 16.3, 9.3, 2.3, va), lin('#8f8d86')); AR.house(C, vx - 70, vy + 62, hz, 16, 9, 4.5, va, lin('#e9dcc3'), lin('#a8452d'), 3.0); C.obst.append([vx - 70, -(vy + 62), 8, 4.5, va])
    C.landmarks.append(('Vineyard', np.array([vx, vy + 70, H(vx, vy + 70)])))
    nf = 0; th = 0.35; ct, st = math.cos(th), math.sin(th)
    for _ in range(400):
        if nf >= 9: break
        x = rng.uniform(150, 1450); y = rng.uniform(-1150, -680)
        fu = math.floor((x * ct + y * st) / 90); fv = math.floor((-x * st + y * ct) / 60)
        cor = [((fu + a) * 90 * ct - (fv + b) * 60 * st, (fu + a) * 90 * st + (fv + b) * 60 * ct) for a, b in ((0.04, 0.05), (0.96, 0.05), (0.96, 0.95), (0.04, 0.95))]
        if not all(C.FIELD[int((q[1] - K.Y0) / K.CELL + .5), int((q[0] - K.X0) / K.CELL + .5)] for q in cor): continue
        nf += 1
        for k in range(4):
            a, b = np.array(cor[k]), np.array(cor[(k + 1) % 4]); m = int(np.linalg.norm(b - a) / 7.5)
            pts = [a + (b - a) * q / m for q in range(m + 1)]
            for q0, q1 in zip(pts[:-1], pts[1:]):
                if rd(*q0) < 9 or rd(*q1) < 9: continue
                z0, z1 = H(*q0), H(*q1); PR.add(box(q0[0], q0[1], z0 - 0.3, .14, .14, 1.5), WOOD)
                PR.add(beam((q0[0], q0[1], z0 + 0.85), (q1[0], q1[1], z1 + 0.85), 0.08, 0.12), WOOD)

    # ---------------------------------------------------------------- coastal fishing village with a small harbour
    def house(x, y, sx, sy, sz, yaw, wall, rf, flat=False):
        z = H(x, y); S.add(box(x, y, z - 2.5, sx + 0.3, sy + 0.3, 2.8, yaw), lin('#8f8d86'))
        AR.house(C, x, y, z, sx, sy, sz, yaw, wall, rf, 0.0 if flat else rng.uniform(1.8, 2.7), flat)
        C.obst.append([x, -y, sx / 2, sy / 2, yaw]); C.houses.append((x, y, sx, sy, sz, yaw, z))
    vc = np.array([-1835.0, -470.0]); hs = []; tries = 0
    cw = [lin(c) for c in ('#f4f1ea', '#e7d9c0', '#d8e2e6', '#f0e0c8', '#e9c9b0')]; cr = [lin(c) for c in ('#a8452d', '#8f3b28', '#4f6f8a', '#b85a35')]
    while len(hs) < 18 and tries < 4000:
        tries += 1; p = vc + rng.normal(0, 55, 2); hz = H(*p)
        if hz < 3.5 or abs(H(p[0] + 6, p[1]) - hz) > 1.6 or abs(H(p[0], p[1] + 6) - hz) > 1.6 or rd(*p) < 15 or any(np.hypot(*(p - q)) < 15 for q in hs): continue
        hs.append(p); house(p[0], p[1], rng.uniform(7, 10), rng.uniform(5.5, 7), rng.uniform(3.2, 5.6), rng.uniform(0, 3.14), cw[rng.integers(5)], cr[rng.integers(4)])
    tt = np.arange(0, 400, 2.0); hh = np.array([float(K.base_h(vc[0] - t, vc[1])) for t in tt])
    if (hh < 0.4).any():
        ts = tt[np.argmax(hh < 0.4)]; pa = (vc[0] - ts + 8, vc[1]); pb = (vc[0] - ts - 52, vc[1])
        S.add(beam((pa[0], pa[1], 1.5), (pb[0], pb[1], 1.5), 3.4, 0.35), WOOD); plat((pa[0] + pb[0]) / 2, pa[1], 60, 3.4, 0, 1.68)
        for a in np.arange(0, 60, 7.5):
            for o in (-1.4, 1.4): PR.add(tube(pa[0] - a, pa[1] + o, -6, .2, .2, 7.6, 5), lin('#5d4631'), solid=False)
        for k in range(6):                                     # moored fishing boats
            bx, by = pb[0] + 10 + 9 * k, pa[1] + (6 if k % 2 else -6)                  # art sheet 06: modelled fishing boats moored along the pier
            import isle_props as KP; KP.KIT.append((('fishing_boat', 'fishing_boat_b')[k % 2], bx, by, 0.0, math.pi * (k % 2) + 0.05 * (k - 3)))
        C.landmarks.append(('Fishing Village', np.array([vc[0], vc[1], H(*vc)])))

    # ---------------------------------------------------------------- desert: adobe settlement, ruins, tower, rock arch
    dc = np.array([1300.0, 455.0]); hs = []; tries = 0; adobe = [lin(c) for c in ('#d9b88a', '#cfa877', '#e2c79d', '#c49a6c')]
    while len(hs) < 11 and tries < 3000:
        tries += 1; p = dc + rng.normal(0, 38, 2); hz = H(*p)
        if abs(H(p[0] + 6, p[1]) - hz) > 1.5 or abs(H(p[0], p[1] + 6) - hz) > 1.5 or rd(*p) < 14 or any(np.hypot(*(p - q)) < 14 for q in hs): continue
        hs.append(p); house(p[0], p[1], rng.uniform(7, 11), rng.uniform(6, 8), rng.uniform(3, 4.6), rng.choice([0.2, 1.77]), adobe[rng.integers(4)], adobe[rng.integers(4)] * 0.85, flat=True)
    S.add(tube(dc[0] + 4, dc[1] - 3, H(dc[0] + 4, dc[1] - 3) - 0.5, 1.5, 1.5, 1.4, 10), lin('#b79a78'), solid=False)                  # well
    rx, ry = 1580.0, 790.0
    for k in range(9):                                         # abandoned walls
        a = rng.uniform(0, 6.28); px, py = rx + rng.uniform(-18, 18), ry + rng.uniform(-14, 14)
        if rd(px, py) > 12: S.add(box(px, py, H(px, py) - 1, rng.uniform(4, 9), 0.6, rng.uniform(1.2, 4.2) + 1, rng.choice([0.3, 1.87])), adobe[k % 4] * 0.8)
    C.landmarks.append(('Desert Ruins', np.array([rx, ry, H(rx, ry)])))
    ox, oy = 1345.0, 690.0; oz = H(ox, oy)
    if rd(ox, oy) > 14:
        for dx in (-2, 2):
            for dy in (-2, 2): S.add(beam((ox + dx * 1.6, oy + dy * 1.6, oz - 1), (ox + dx, oy + dy, oz + 22), 0.3), STEEL)
        for lv in (6, 12, 18):
            for dx, dy, ex, ey in ((-1, -1, 1, -1), (1, -1, 1, 1), (1, 1, -1, 1), (-1, 1, -1, -1)):
                f = 1.6 - 0.6 * lv / 22 * 0.0 - 0.027 * lv; S.add(beam((ox + dx * 2 * f, oy + dy * 2 * f, oz + lv), (ox + ex * 2 * f, oy + ey * 2 * f, oz + lv), 0.14), STEEL)
        S.add(box(ox, oy, oz + 22, 6.4, 6.4, 0.3), lin('#6d6f73'))
        for dx, dy, wx_, wy_ in ((0, 3.1, 6.4, .1), (0, -3.1, 6.4, .1), (3.1, 0, .1, 6.4), (-3.1, 0, .1, 6.4)): S.add(box(ox + dx, oy + dy, oz + 22.3, wx_, wy_, 1.1), STEEL)
        S.add(roof(ox, oy, oz + 25.2, 6, 6, 1.4, 0, 0.6), lin('#a8452d'))
        for dx in (-2.6, 2.6):
            for dy in (-2.6, 2.6): S.add(box(ox + dx, oy + dy, oz + 22.3, .14, .14, 2.9), STEEL)
        C.circ.append([ox, -oy, 4.2]); C.landmarks.append(('Observation Tower', np.array([ox, oy, oz])))
    ax_, ay_, aa = 1560.0, 470.0, 0.6; az_ = H(ax_, ay_)
    for k in range(13):                                        # natural rock arch
        t = math.pi * k / 12; rr = 4.6 - 1.4 * math.sin(t); d = 14 * math.cos(t)
        Rk.add(sphere(ax_ + d * math.cos(aa), ay_ + d * math.sin(aa), az_ - 1 + 13.5 * math.sin(t), rr * rng.uniform(.9, 1.15), rr * rng.uniform(.9, 1.15), rr * rng.uniform(.9, 1.2), 7, 5, jit=0.18), lin('#b3683d') * rng.uniform(.85, 1.08))
    for sg in (-1, 1): C.circ.append([ax_ + sg * 14 * math.cos(aa), -(ay_ + sg * 14 * math.sin(aa)), 4.4])
    C.landmarks.append(('Rock Arch', np.array([ax_, ay_, az_])))

    # ---------------------------------------------------------------- scenic viewpoints beside the road
    def viewpoint(r, i, name):
        if r['bridge'][i] or r['tunnel'][i]: return
        hw = r['w'] / 2; hL = float(K.base_h(*(r['xy'][i] + r['left'][i] * 45))); hR = float(K.base_h(*(r['xy'][i] - r['left'][i] * 45)))
        side = 1 if hL < hR else -1; p = P(r, i, side * (hw + 9.5)); hd = float(r['head'][i]); z = float(r['z'][i]) - 0.05
        S.add(box(p[0], p[1], z - 6, 32, 11, 6, hd), lin('#8f8d86')); plat(p[0], p[1], 32, 11, hd, z)
        t = r['tan'][i]; lf = r['left'][i] * side; edge = p[:2] + lf * 5.2
        for a in np.arange(-15, 15.1, 3.0):
            q = edge + t * a; PR.add(box(q[0], q[1], z, .12, .12, 1.1), STEEL)
        PR.add(beam((*(edge - t * 15), z + 1.05), (*(edge + t * 15), z + 1.05), 0.1), STEEL); PR.add(beam((*(edge - t * 15), z + 0.55), (*(edge + t * 15), z + 0.55), 0.07), STEEL)
        for a in (-8, 8):
            q = p[:2] + t * a + lf * 2.6; PR.add(box(q[0], q[1], z, 1.9, 0.5, 0.45, hd), WOOD); PR.add(box(q[0] - lf[0] * .28, q[1] - lf[1] * .28, z + .45, 1.9, .08, .5, hd), WOOD)
        q = edge - lf * 0.8; PR.add(tube(q[0], q[1], z, .09, .09, 1.3, 5), STEEL, solid=False); PR.add(beam((q[0], q[1], z + 1.4), (q[0] + lf[0] * .8, q[1] + lf[1] * .8, z + 1.5), 0.24), lin('#2b5fae'))
        q = p[:2] - t * 13 - lf * 3.5; PR.add(tube(q[0], q[1], z, .06, .06, 2.4, 4), STEEL, solid=False); PR.add(box(q[0], q[1], z + 1.7, .06, 1.5, .9, hd), lin('#7a4a2a'))
        C.circ.append([edge[0], -edge[1], 0.2]); C.landmarks.append((name, np.array([p[0], p[1], z])))
    ring = roads[0]
    def near(r, x, y): return int(np.argmin(np.hypot(r['xy'][:, 0] - x, r['xy'][:, 1] - y)))
    viewpoint(ring, near(ring, -1790, 50), 'West Cliffs Viewpoint'); viewpoint(ring, near(ring, 200, 1250), 'North Shore Viewpoint')
    sp = R['Summit Pass']; viewpoint(sp, int(np.argmax(sp['z'] * ~(sp['bridge'] | sp['tunnel']))), 'Summit Viewpoint')
    viewpoint(R['Dune Road'], R['Dune Road']['n'] // 2, 'Mesa Viewpoint'); viewpoint(R['Serpentine'], R['Serpentine']['n'] - 7, 'Serpentine Summit')
    fl = R['Beach Flyover']; C.landmarks.append(('Beach Flyover', C.P(fl, fl['n'] - 3)))
    L.STATS['stage2'] = n_


# ============================================================================ technical organisation
COLL = ['01_TERRAIN', '02_OCEAN', '03_ROAD_NETWORK', '04_CITY', '05_MOUNTAINS', '06_FOREST', '07_DESERT', '08_RACING_CIRCUIT', '09_COASTAL_ENVIRONMENT',
        '10_COUNTRYSIDE', '11_BUILDINGS', '12_VEGETATION', '13_BRIDGES_AND_TUNNELS', '14_ROADSIDE_PROPS', '15_LIGHTING', '16_CAMERA', '17_COLLISION', '18_GAMEPLAY_LANDMARKS']
REG2COL = {'Mountain Roads': 4, 'Desert': 6, 'Forest Trails': 5, 'City': 3, 'Harbour': 3, 'Racing Circuit': 7, 'Coastal Highway': 8, 'Heliport': 8, 'Countryside': 9}


def region_of(x, y):
    best, bd = 'Coastal Highway', 1.25
    for nm, cx, cy, rx, ry in K.REGIONS:
        d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        if d < bd: bd = d; best = nm
    return best


def collision(C):
    roads, TR = C.roads, C.TR; V = []; F = []; off = 0
    for r in roads:
        hw = r['w'] / 2; Vr, Fr, _ = C.rib(r, [(-hw - 4, -0.78), (-hw, 0), (hw, 0), (hw + 4, -0.78)]); V.append(Vr); F.append(Fr + off); off += len(Vr)
    make_obj('COL_Roads', np.vstack(V), np.vstack(F))
    Hs = TR['H'][::2, ::2]; Xs = TR['X'][::2, ::2]; Ys = TR['Y'][::2, ::2]; ny, nx = Hs.shape
    iy, ix = np.mgrid[0:ny - 1, 0:nx - 1]; a = (iy * nx + ix).ravel(); b = a + 1; c = a + nx + 1; d = a + nx
    keep = np.maximum.reduce([Hs.ravel()[a], Hs.ravel()[b], Hs.ravel()[c], Hs.ravel()[d]]) > -6
    make_obj('COL_Terrain', np.c_[Xs.ravel(), Ys.ravel(), Hs.ravel()], np.vstack([np.c_[a, b, c][keep], np.c_[a, c, d][keep]]))
    B = Buf(); hts = {(round(b[1], 1), round(b[2], 1)): b[5] for b in C.bld}
    for o in C.obst:
        x, y = o[0], -o[1]; h = hts.get((round(x, 1), round(y, 1)), 9.0); B.add(box(x, y, C.hgt(x, y) - 1, o[2] * 2, o[3] * 2, h + 1, o[4]), np.ones(3))
    for o in C.circ: B.add(cyl(o[0], -o[1], C.hgt(o[0], -o[1]) - 1, o[2], o[2], 9, 8), np.ones(3))
    Vb, Fb, _, _ = B.arrays(); make_obj('COL_Buildings', Vb, Fb)
    for nm in ('COL_Roads', 'COL_Terrain', 'COL_Buildings'):
        o = bpy.data.objects[nm]; o.hide_render = True; o.display_type = 'WIRE'; L.STATS.pop(nm, None)


def lighting_and_cameras(C):
    scn = bpy.context.scene; roads = C.roads; R = {r['name']: r for r in roads}
    from mathutils import Vector
    w = bpy.data.worlds.new('World_LateAfternoon'); scn.world = w; w.use_nodes = True; nt = w.node_tree; bg = nt.nodes['Background']
    sky = nt.nodes.new('ShaderNodeTexSky')
    for t in ('MULTIPLE_SCATTERING', 'NISHITA', 'HOSEK_WILKIE'):
        try: sky.sky_type = t; break
        except Exception: pass
    el, az = math.radians(37), math.radians(243)
    for k, v in (('sun_elevation', el), ('sun_rotation', az), ('sun_intensity', 1.0), ('sun_disc', False), ('air_density', 1.0), ('aerosol_density', 1.1), ('dust_density', 1.2)):
        try: setattr(sky, k, v)
        except Exception: pass
    nt.links.new(sky.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.3
    sun = bpy.data.lights.new('SUN_LateAfternoon', 'SUN'); sun.energy = 5.4; sun.angle = math.radians(2.2); sun.color = (1.0, 0.90, 0.76)
    so = bpy.data.objects.new('SUN_LateAfternoon', sun); scn.collection.objects.link(so)
    so.rotation_euler = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el))).to_track_quat('Z', 'Y').to_euler()
    scn.render.engine = 'CYCLES'; scn.cycles.samples = 64; scn.cycles.use_denoising = True
    try: scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass

    def cam(name, pos, tgt, lens):
        c = bpy.data.cameras.new(name); c.lens = lens; c.clip_start = 0.5; c.clip_end = 40000
        o = bpy.data.objects.new(name, c); scn.collection.objects.link(o); o.location = pos
        o.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler(); return o
    def drive(r, i, up=2.0, off=-1.6, ahead=14, lens=22, dz=0.0):
        i = int(np.clip(i, 2, r['n'] - ahead - 2)); p = C.P(r, i, off, up); q = C.P(r, i + ahead, 0, up * 0.8 + dz); return p, q, lens
    near = lambda r, x, y: int(np.argmin(np.hypot(r['xy'][:, 0] - x, r['xy'][:, 1] - y)))
    ring = roads[0]; sk = R['Skyline Road']; g = ~(sk['bridge'] | sk['tunnel'])
    c1 = cam('CAM_01_Island_Aerial', (150, -4300, 2500), (0, -150, 0), 30); scn.camera = c1
    cam('CAM_02_City_Skyline', (-300, -980, 55), (40, -60, 95), 30)
    cam('CAM_03_Mountain_Road', *drive(sk, int(np.argmax(sk['z'] * g)) - 26, up=3.0, ahead=20, lens=20))
    lt = R['Lake Trail']; cam('CAM_04_Forest_Road', *drive(lt, near(lt, -1420, 290), up=2.2, off=0.5, lens=22))
    cam('CAM_05_Desert_Highway', *drive(ring, near(ring, 1560, 720), up=2.6, off=-3.0, ahead=22, lens=22))
    ci = R['Circuit']; i0 = C.circuit_start; cam('CAM_06_Racing_Circuit', tuple(C.P(ci, i0 - 40, -30, 34)), tuple(C.P(ci, i0 + 8, 6, 2)), 24)
    iw = near(ring, -1640, -520); sd_ = 1 if float(K.base_h(*(ring['xy'][iw] + ring['left'][iw] * 60))) < float(K.base_h(*(ring['xy'][iw] - ring['left'][iw] * 60))) else -1
    cam('CAM_07_Coastal_Highway', tuple(C.P(ring, iw - 30, -sd_ * 16, 14)), tuple(C.P(ring, iw + 14, sd_ * 30, 0)), 22)
    cam('CAM_08_Countryside_Village', (470, -1000, 42), (625, -855, 10), 28)
    stt = R['Street E-20']; cam('CAM_09_Ground_Level_Street', *drive(stt, 44, up=1.6, off=-2.6, ahead=18, lens=18, dz=6))
    cam('CAM_10_Detail_Harbour', (-372, -452, 8), (-430, -392, 24), 24)


def organise(C):
    scn = bpy.context.scene; cols = []
    for nm in COLL:
        c = bpy.data.collections.new(nm); scn.collection.children.link(c); cols.append(c)
    for nm, p in C.landmarks:
        if nm:
            e = bpy.data.objects.new('LM_' + nm.replace(' ', '_'), None); e.empty_display_size = 12; e.location = tuple(p); scn.collection.objects.link(e)
    for ob in list(scn.collection.objects):
        nm = ob.name; base = nm.split('__')[0]
        if base.startswith('COL_'): k = 16
        elif base.startswith('LM_'): k = 17
        elif base.startswith('SUN_'): k = 14
        elif base.startswith('CAM_'): k = 15
        elif base.startswith('Terrain') or base == 'AureliaIsland': k = 0
        elif base in ('Water', 'Seabed', 'River') or base.startswith('Lake_') or base.startswith('Waterfall_'): k = 1
        elif base in ('Road', 'Verge', 'Kerbs', 'Markings', 'StartLine', 'RoadDecals'): k = 2
        elif base in ('Buildings', 'Towers', 'Houses', 'Roofs', 'Glazing', 'ArchTrim', 'KitTrim', 'ContactAO') or base.startswith('KIT_') or base.startswith('BuildingsHD') or base.startswith('BuildingsLOD'): k = 10
        elif base.startswith('INST_') or base.startswith('FLORA_'): k = 11
        elif base in ('Vegetation', 'TreeCards', 'GrassCards'): k = 11
        elif base.startswith('Spin_Turbine'): k = 8
        elif base in ('Bridges', 'TunnelPortal'): k = 12
        elif base == 'Props': k = 13
        elif base == 'Spin_FerrisWheel': k = 3
        elif base == 'Spin_Windmill': k = 9
        elif base == 'Spin_HeliRotor': k = 8
        elif '__' in nm:
            ix, iy = (int(v) for v in nm.split('__')[1].split('_')); k = REG2COL[region_of((ix + .5) * L.TILE, (iy + .5) * L.TILE)]
        else: k = 0
        cols[k].objects.link(ob); scn.collection.objects.unlink(ob)
    return cols

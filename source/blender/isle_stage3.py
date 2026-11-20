"""Stage 3/4 upgrade for Aurelia Island: building articulation, village yards, forest floor, grass cards,
wind farm, industrial estate, construction site, roadside shops, rural fuel station, farm machinery."""
import math, bpy
import numpy as np
import isle_data as K
import isle_arch as AR
import isle_lib as L
from isle_lib import lin, box, beam, cyl, cone, tube, sphere, roof, rot_x, rot_z, Buf, make_obj, fft_noise
from isle_stage2 import facade_poly, cap_poly, rect, flat_quad, CAR_COLS
from isle_data import smoothstep, fbm

rng = np.random.default_rng(4242)


def grass_atlas():
    """512 x 256 cut-out atlas: cell 0 grass tuft, cell 1 tall grass with seed heads and flowers."""
    n = 256; yy, xx = np.mgrid[0:n, 0:n]; xx = (xx + .5) / n; yy = (yy + .5) / n
    out = np.zeros((n, 2 * n, 4)); r = np.random.default_rng(9)
    for cell in range(2):
        C = np.zeros((n, n, 3)); A = np.zeros((n, n)); nb = 70 if cell == 0 else 46
        for k in range(nb):
            x0 = 0.5 + r.normal(0, 0.14); lean = r.normal(0, 0.22); hgt = r.uniform(0.45, 0.95) * (0.8 if cell == 0 else 1.0)
            t = np.clip(yy / hgt, 0, 1); cx = x0 + lean * t * t; w = 0.016 * (1 - t) ** 0.7 + 0.002
            m = (np.abs(xx - cx) < w) & (yy < hgt)
            g = r.uniform(0.75, 1.15); col = np.array([0.30, 0.52, 0.18]) * g * (0.55 + 0.6 * t)[..., None] if cell == 0 else np.array([0.50, 0.56, 0.24]) * g * (0.6 + 0.5 * t)[..., None]
            C[m] = col[m]; A[m] = 1
            if cell == 1 and k % 3 == 0:
                tipx = x0 + lean; d = np.hypot((xx - tipx) / 0.022, (yy - hgt) / 0.05); m2 = d < 1
                C[m2] = [[0.86, 0.74, 0.30], [0.90, 0.88, 0.80], [0.78, 0.32, 0.36], [0.62, 0.42, 0.72]][k % 4]; A[m2] = 1
        mm = A > 0.5; C[~mm] = C[mm].mean(0); out[:, cell * n:(cell + 1) * n] = np.dstack([np.clip(C * 1.25, 0, 1), A])
    return out


def emit_cards(name, rows, mat, ncols):
    """rows: x, y, z, height, width, cell, r, g, b  -> two crossed quads each, normals up."""
    T = np.array(rows, float); n = len(T)
    if not n: return
    r = np.random.default_rng(6); a = r.uniform(0, np.pi, n); x, y, z, h, w = T[:, 0], T[:, 1], T[:, 2], T[:, 3], T[:, 4]; cell = T[:, 5]
    u0 = cell / ncols + 0.004; u1 = (cell + 1) / ncols - 0.004; V = []; U = []
    for da in (0.0, np.pi / 2):
        dx = np.cos(a + da) * w / 2; dy = np.sin(a + da) * w / 2
        V.append(np.stack([np.c_[x - dx, y - dy, z], np.c_[x + dx, y + dy, z], np.c_[x + dx, y + dy, z + h], np.c_[x - dx, y - dy, z + h]], 1))
        U.append(np.stack([np.c_[u0, np.full(n, .01)], np.c_[u1, np.full(n, .01)], np.c_[u1, np.full(n, .99)], np.c_[u0, np.full(n, .99)]], 1))
    V = np.concatenate(V, 0).reshape(-1, 3); U = np.concatenate(U, 0).reshape(-1, 2)
    q = np.arange(2 * n) * 4; F = np.vstack([np.c_[q, q + 1, q + 2], np.c_[q, q + 2, q + 3]])
    Cc = np.repeat(np.tile(T[:, 6:9], (2, 1)), 4, axis=0); Nn = np.tile(np.array([0, 0, 1.0]), (len(V), 1))
    L.make_chunked(name, V, F, Cc, U, mat, True, normals=Nn)


def hedge(buf, p0, p1, col):
    """Clipped hedge: rounded section, slightly uneven along its length."""
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float); ln = np.linalg.norm(p1 - p0); k = max(2, int(ln / 1.3)); t = (p1 - p0) / ln; nr = np.array([-t[1], t[0], 0])
    prof = [(-0.5, 0.0), (-0.55, 0.7), (-0.42, 1.15), (-0.15, 1.35), (0.15, 1.35), (0.42, 1.15), (0.55, 0.7), (0.5, 0.0)]; m = len(prof); V = []; Cc = []
    for i in range(k + 1):
        c = p0 + (p1 - p0) * i / k; j = 1 + rng.uniform(-0.09, 0.09, m)
        for q, (a, b) in enumerate(prof): V.append(c + nr * a * j[q] + np.array([0, 0, b * j[q]])); Cc.append(col * (0.62 + 0.4 * b / 1.35) * rng.uniform(0.9, 1.1))
    F = []
    for i in range(k):
        for q in range(m - 1): a = i * m + q; b = a + m; F += [(a, b, b + 1), (a, b + 1, a + 1)]
    for i0, rev in ((0, False), (k * m, True)):
        for q in range(1, m - 1): F.append((i0, i0 + q + 1, i0 + q) if rev else (i0, i0 + q, i0 + q + 1))
    buf.add((np.array(V), np.array(F)), np.array(Cc), solid=False)


def post(C):
    S, Sm, FA, D, Rk, Mk, PR, M = C.S, C.Sm, C.FA, C.V, C.Rk, C.Mk, C.PR, C.M
    H = C.hgt; P = C.P; roads = C.roads; R = {r['name']: r for r in roads}; TR = C.TR
    CONC, STEEL, WHITE, RED, DARK = (C.col[k] for k in ('CONC', 'STEEL', 'WHITE', 'RED', 'DARK'))
    WOOD = lin('#8a6a48'); YEL = lin('#f2c230'); ORANGE = lin('#e8731c')
    rd = lambda x, y: float(C.G['tree'].query([x, y])[0])
    cz = K.CITY_Z; n_ = dict(fins=0, gardens=0, grass=0, logs=0, shops=0)
    def ob(x, y, sx, sy, yaw=0.0): C.obst.append([x, -y, sx / 2, sy / 2, yaw])
    def lm(name, p): C.landmarks.append((name, np.asarray(p, float)))

    def wheel(x, y, z, r, w, yaw, col=None):
        V, F = cyl(0, 0, -w / 2, r, r, w, 10); V = rot_z(rot_x(V, np.zeros(3), math.pi / 2), np.zeros(3), yaw) + (x, y, z + r); Sm.add((V, F), col if col is not None else lin('#161616'))
    def car(x, y, z, yaw):
        col = lin(CAR_COLS[rng.integers(len(CAR_COLS))]); c, s = math.cos(yaw), math.sin(yaw)
        import isle_stage7 as S7; S7.car_mesh(Sm, x, y, z, yaw, col, int(abs(x) * 7) % 3)
    def tractor(x, y, yaw, col):
        z = H(x, y); c, s = math.cos(yaw), math.sin(yaw)
        Sm.add(box(x + 0.5 * c, y + 0.5 * s, z + 0.7, 2.6, 1.1, 0.9, yaw), col); Sm.add(box(x - 0.9 * c, y - 0.9 * s, z + 1.2, 1.5, 1.4, 1.5, yaw), lin('#22303a'))
        Sm.add(box(x - 0.9 * c, y - 0.9 * s, z + 2.7, 1.7, 1.6, 0.12, yaw), col); S.add(tube(x + 1.2 * c, y + 1.2 * s, z + 1.6, .07, .07, 1.2, 5), DARK, solid=False)
        for sg in (-1, 1):
            wheel(x - 0.9 * c - sg * 0.95 * s, y - 0.9 * s + sg * 0.95 * c, z, 0.85, 0.42, yaw); wheel(x + 1.4 * c - sg * 0.8 * s, y + 1.4 * s + sg * 0.8 * c, z, 0.48, 0.3, yaw)
        C.circ.append([x, -y, 1.9])

    # ---------------------------------------------------------------- city: tower fins, crowns, podiums; mid-rise cornices and shopfronts
    aw = [lin(c) for c in ('#b3241d', '#1f5f4a', '#22407a', '#c98a1c', '#5a2d6b')]
    for kind, x, y, sx, sy, h, yaw, z in C.bld:
        c, s = math.cos(yaw), math.sin(yaw)
        def loc(a, b): return (x + a * c - b * s, y + a * s + b * c)
        if kind == 'tower':
            fc = lin('#c9d2da') * rng.uniform(.8, 1.0)
            for a in np.arange(-sx / 2, sx / 2 + 0.1, max(4.5, sx / 6)):
                for sg in (-1, 1): p = loc(a, sg * (sy / 2 + 0.22)); S.add(box(p[0], p[1], z + 5.2, 0.28, 0.5, h * 0.5 - 5.2, yaw), fc); n_['fins'] += 1
            for b in np.arange(-sy / 2, sy / 2 + 0.1, max(4.5, sy / 6)):
                for sg in (-1, 1): p = loc(sg * (sx / 2 + 0.22), b); S.add(box(p[0], p[1], z + 5.2, 0.5, 0.28, h * 0.5 - 5.2, yaw), fc); n_['fins'] += 1
            S.add(box(x, y, z - 0.3, sx + 4.2, sy + 4.2, 5.4, yaw), lin('#2e3136')); Rp_ = AR.rect(x, y, sx + 5, sy + 5, yaw)
            for k_ in range(4): AR.wall(Rp_[k_], Rp_[(k_ + 1) % 4], z - 0.3, 5.4, 1, 5.2, (3, 3, 1), lin('#d5d2c8'), 'plaster', None, depth=0.3, shop=True)
            cap_poly(S, rect(x, y, sx + 5.4, sy + 5.4, yaw), z + 5.1, lin('#4a4f57'))
            for k in range(3): p = loc(-sx / 3 + k * sx / 3, -sy / 2 - 3.3); S.add(box(p[0], p[1], z + 3.1, sx / 4, 1.5, 0.14, yaw), aw[(k + int(x)) % 5])
        elif kind == 'mid':
            S.add(box(x, y, z + h - 0.75, sx + 0.9, sy + 0.9, 0.5, yaw), lin('#e2ded3')); S.add(box(x, y, z + 3.9, sx + 0.5, sy + 0.5, 0.3, yaw), lin('#cfcabd'))
            for a, b in ((-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2)): p = loc(a, b); S.add(box(p[0], p[1], z, 0.7, 0.7, h, yaw), lin('#d9d4c8'))
            if rng.random() < 0.6:
                nsh = max(1, int(sx / 7))
                for k in range(nsh):
                    a = -sx / 2 + (k + 0.5) * sx / nsh; p = loc(a, -sy / 2 - 0.1); S.add(box(p[0], p[1], z + 0.3, sx / nsh - 1.4, 0.16, 2.9, yaw), lin('#1f2c36'))
                    p = loc(a, -sy / 2 - 0.9); S.add(box(p[0], p[1], z + 3.25, sx / nsh - 1.0, 1.6, 0.12, yaw), aw[(k + int(y)) % 5])
    for i in range(len(K.SX) - 1):                             # street trees along the block edges
        for j in range(len(K.SY) - 1):
            for q in range(4):
                tx = K.SX[i] + 12 + (K.SX[i + 1] - K.SX[i] - 24) * (q + 0.5) / 4; ty = K.SY[j + 1] - 8.4; hgt = rng.uniform(7, 10)
                C.cards.append((tx, ty, cz + 0.15, hgt, hgt * 0.9, 2, 7, 0.62, rng.uniform(.8, 1), rng.uniform(.9, 1), rng.uniform(.7, .9)))
                PR.add(box(tx, ty, cz + 0.13, 1.5, 1.5, 0.08), lin('#4a4034'))

    # ---------------------------------------------------------------- village and other houses: doors, porches, hedged yards, sheds, cars
    for (x, y, sx, sy, sz, yaw, z) in C.houses:
        c, s = math.cos(yaw), math.sin(yaw)
        def loc(a, b): return (x + a * c - b * s, y + a * s + b * c)
        rng.integers(4)
        if rng.random() < 0.75:                                # hedge on three sides of the yard, open to the front
            gx, gy = sx / 2 + rng.uniform(4, 7), sy / 2 + rng.uniform(4, 7); n_['gardens'] += 1
            for (a0, b0, a1, b1) in ((-gx, -gy, -gx, gy), (-gx, gy, gx, gy), (gx, gy, gx, -gy)):
                p0 = loc(a0, b0); p1 = loc(a1, b1)
                if rd(*p0) > 7 and rd(*p1) > 7 and abs(H(*p0) - z) < 2.5 and abs(H(*p1) - z) < 2.5:
                    ln_ = math.hypot(p1[0] - p0[0], p1[1] - p0[1])                      # hedge as a dense row of leafy shrubs
                    for t_ in np.linspace(0, 1, max(2, int(ln_ / 1.15)) + 1):
                        q = (p0[0] + (p1[0] - p0[0]) * t_, p0[1] + (p1[1] - p0[1]) * t_); g = rng.uniform(.88, 1.05)
                        C.inst.append(('bush', q[0], q[1], H(*q) - 0.15, rng.uniform(0.75, 0.95), g * 0.9, g, g * 0.72))
            t = loc(rng.uniform(-gx + 2, gx - 2), gy - 2.5)
            if rd(*t) > 8: hgt = rng.uniform(5, 8); C.cards.append((t[0], t[1], H(*t) - 0.2, hgt, hgt, 2, 7, 0.62, rng.uniform(.8, 1), rng.uniform(.9, 1), rng.uniform(.6, .9)))
            if rng.random() < 0.4:
                q = loc(-gx + 2.2, gy - 2.4); S.add(box(q[0], q[1], H(*q) - 0.3, 2.6, 2.2, 2.4, yaw), lin('#7a5a3c')); S.add(roof(q[0], q[1], H(*q) + 2.1, 2.6, 2.2, 0.8, yaw, 0.2), lin('#4a4f57'))
            if rng.random() < 0.35:
                q = loc(sx / 2 + 2.4, -sy / 2 - 2.5)
                if rd(*q) > 6: car(q[0], q[1], H(*q), yaw + math.pi / 2)

    # ---------------------------------------------------------------- farm machinery
    for fx0, fy0 in ((990, -965), (1290, -790), (190, -935), (880, -690)):
        p = (fx0 + rng.uniform(14, 22), fy0 + rng.uniform(-14, 14))
        if rd(*p) > 12 and H(*p) > 4: tractor(p[0], p[1], rng.uniform(0, 6.28), lin(['#b3241d', '#2f7a3a', '#1f4f9a'][rng.integers(3)]))
        q = (fx0 - rng.uniform(14, 20), fy0 + rng.uniform(-10, 10))
        if rd(*q) > 12 and H(*q) > 4:
            zz = H(*q); ya = rng.uniform(0, 3.14); S.add(box(q[0], q[1], zz + 0.8, 5, 2.2, 0.25, ya), WOOD)
            for a in (-1.6, 1.6):
                for b in (-1.1, 1.1): wheel(q[0] + a * math.cos(ya) - b * math.sin(ya), q[1] + a * math.sin(ya) + b * math.cos(ya), zz, .42, .26, ya)
            for k in range(3): Sm.add(cyl(q[0] + (k - 1) * 1.5 * math.cos(ya), q[1] + (k - 1) * 1.5 * math.sin(ya), zz + 1.05, .7, .7, 1.2, 7), lin('#c9a84f'))

    # ---------------------------------------------------------------- forest floor: logs, stumps, boulders, trail fence, picnic clearing
    cand = np.c_[rng.uniform(-2000, -700, 6000), rng.uniform(-150, 1000, 6000)]
    hc = K.sample_h(TR, cand[:, 0], cand[:, 1]); td = C.G['tree'].query(cand)[0]; Bf = K.biomes(cand[:, 0], cand[:, 1])['forest']
    okf = (Bf > 0.5) & (hc > 3) & (td > 9) & (td < 70)
    for l0, l1, l2 in K.LAKES[:2]: okf &= np.hypot(cand[:, 0] - l0, cand[:, 1] - l1) > l2 + 8
    for q in np.where(okf)[0][:420]:
        x, y, z = cand[q, 0], cand[q, 1], hc[q]; u = rng.random()
        if u < 0.4:
            a = rng.uniform(0, 3.14); ln = rng.uniform(4, 9); d = np.array([math.cos(a), math.sin(a)]) * ln / 2; z1 = H(x + d[0], y + d[1]); z0 = H(x - d[0], y - d[1])
            V, F = cyl(0, 0, 0, .34, .26, ln, 7); V = rot_z(rot_x(V - (0, 0, ln / 2), np.zeros(3), math.pi / 2), np.zeros(3), a + math.pi / 2) + (x, y, (z0 + z1) / 2 + 0.25)
            Sm.add((V, F), lin('#5a4330') * rng.uniform(.8, 1.1)); n_['logs'] += 1
        elif u < 0.6: Sm.add(cyl(x, y, z - 0.2, .45, .38, rng.uniform(.5, .9), 7), lin('#6b5540'))
        else: rr = rng.uniform(.7, 2.2); Rk.add(sphere(x, y, z + rr * .2, rr * rng.uniform(.8, 1.3), rr * rng.uniform(.8, 1.3), rr * rng.uniform(.5, .8), 6, 4, jit=.22), lin('#77736a') * rng.uniform(.8, 1.1))
    r = R['Lake Trail']
    for i in range(20, r['n'] - 20, 2):                        # split-rail fence along one side of the trail near the lake
        if 60 <= i <= 170 and not r['junction'][i - 3:i + 4].any():
            p0 = P(r, i, r['w'] / 2 + 3.2); p1 = P(r, i + 2, r['w'] / 2 + 3.2); z0, z1 = H(*p0[:2]), H(*p1[:2])
            PR.add(box(p0[0], p0[1], z0 - 0.3, .16, .16, 1.5), WOOD)
            for hh in (0.55, 1.0): PR.add(beam((p0[0], p0[1], z0 + hh), (p1[0], p1[1], z1 + hh), 0.09, 0.13), WOOD)
    lk = K.LAKES[1]; px, py = lk[0] - lk[2] - 34, lk[1] + 10
    if rd(px, py) > 12:
        for k in range(4):
            tx, ty = px + (k % 2) * 7, py + (k // 2) * 6; z = H(tx, ty)
            PR.add(box(tx, ty, z + 0.7, 2.0, 0.9, 0.08), WOOD)
            for sg in (-0.75, 0.75): PR.add(box(tx, ty + sg, z + 0.4, 2.0, 0.3, 0.06), WOOD); PR.add(box(tx + sg, ty, z - 0.1, .1, 1.5, 0.8), WOOD)
        C.noveg.append((px, py, 16)); lm('Picnic Clearing', (px, py, H(px, py)))

    # ---------------------------------------------------------------- grass, tall grass and wildflowers beside the roads and in clearings
    rows = []; Bc = None
    for r in roads:
        if r['type'] in ('street', 'circuit', 'rbt'): continue
        hw = r['w'] / 2; g = ~(r['bridge'] | r['tunnel'])
        for i in np.where(g)[0][::2]:
            for _ in range(3):
                o = rng.choice([-1, 1]) * (hw + 4.5 + rng.uniform(0, 13)); p = r['xy'][i] + r['left'][i] * o + r['tan'][i] * rng.uniform(-5, 5)
                rows.append((p[0], p[1], 0, 0, 0, 0, 0, 0, 0))
    T = np.array(rows); bx = K.biomes(T[:, 0], T[:, 1]); hz = K.sample_h(TR, T[:, 0], T[:, 1]); td = C.G['tree'].query(T[:, :2])[0]
    okg = (bx['city'] < 0.3) & (bx['desert'] < 0.4) & (bx['circuit'] < 0.3) & (hz > 2.5) & (hz < 125) & (td > 4.2)
    T = T[okg]; hz = hz[okg]; n = len(T); tall = rng.random(n) < 0.3
    T[:, 2] = hz - 0.12; T[:, 3] = np.where(tall, rng.uniform(1.0, 1.7, n), rng.uniform(0.6, 1.1, n)); T[:, 4] = T[:, 3] * rng.uniform(1.1, 1.6, n); T[:, 5] = tall
    v = rng.uniform(0.75, 1.0, n); T[:, 6] = v * rng.uniform(0.85, 1.0, n); T[:, 7] = v; T[:, 8] = v * rng.uniform(0.7, 0.95, n)
    C.grass = T[:11000]; n_['grass'] = len(C.grass)

    # ---------------------------------------------------------------- wind farm on the western hills (rotors spin in the game)
    best = []
    for _ in range(4000):
        x = rng.uniform(-2020, -1560); y = rng.uniform(-260, 260); hz = H(x, y)
        if hz > 12 and rd(x, y) > 55: best.append((hz, x, y))
    best.sort(reverse=True); tur = []
    for hz, x, y in best:
        if all(math.hypot(x - a, y - b) > 120 for a, b in tur): tur.append((x, y))
        if len(tur) >= 6: break
    for k, (x, y) in enumerate(tur):
        z = H(x, y); Sm.add(cyl(x, y, z - 2, 2.2, 1.2, 74, 12), WHITE); Sm.add(box(x - 1.2, y, z + 71.4, 7.5, 2.8, 2.9), WHITE); hub = (x - 5.6, y, z + 72.8)
        Rb = Buf(); Rb.add(sphere(0, 0, 0, 1.9, 1.5, 1.5, 8, 6), WHITE)
        for bl in range(3):
            a = bl * 2 * np.pi / 3; d = np.array([0, math.sin(a), math.cos(a)]); Vb, Fb = beam(d * 1.0, d * 36.0, 0.34, 2.7)
            tc = (Vb @ d - 1.0) / 35.0; Vb = d * (Vb @ d)[:, None] + (Vb - d * (Vb @ d)[:, None]) * (1 - 0.74 * tc)[:, None]; Rb.add((Vb, Fb), WHITE)
        Vt, Ft, Ct, _ = Rb.arrays(); o = make_obj('Spin_Turbine_%d' % k, Vt, Ft, Ct, None, M.vc, smooth=False); o.location = hub; o.rotation_euler = (rng.uniform(0, 2), 0, 0)
        C.spinners.append(dict(name='Spin_Turbine_%d' % k, axis='x', speed=0.9, pos=[hub[0], hub[2], -hub[1]])); C.circ.append([x, -y, 3]); C.noveg.append((x, y, 9))
    if tur: lm('Wind Farm', (tur[0][0], tur[0][1], H(*tur[0])))

    # ---------------------------------------------------------------- industrial estate
    ic = np.array([585.0, -545.0]); placed = []
    def shed(x, y, sx, sy, sz, yaw, col):
        z = H(x, y); S.add(box(x, y, z - 3, sx + 0.3, sy + 0.3, 3.3, yaw), lin('#8f8d86')); AR.house(C, x, y, z, sx, sy, sz, yaw, col, lin('#6d6f73'), 2.2)
        c, s = math.cos(yaw), math.sin(yaw)
        for k in range(int(sx / 9)): a = -sx / 2 + 5 + k * 9; S.add(box(x + a * c + (sy / 2 + .08) * s, y + a * s - (sy / 2 + .08) * c, z, 4.2, 0.16, 4.4, yaw), lin('#39424d'))
        ob(x, y, sx, sy, yaw); placed.append((x, y)); C.noveg.append((x, y, max(sx, sy) * .7))
    tries = 0
    while len(placed) < 6 and tries < 600:
        tries += 1; p = ic + rng.uniform(-110, 110, 2); hz = H(*p)
        if rd(*p) < 32 or hz < 5 or abs(H(p[0] + 20, p[1]) - hz) > 2.5 or abs(H(p[0], p[1] + 12) - hz) > 2.5 or any(math.hypot(p[0] - a, p[1] - b) < 52 for a, b in placed): continue
        shed(p[0], p[1], rng.uniform(34, 46), rng.uniform(20, 26), rng.uniform(8, 11), rng.choice([0.0, 0.25]), lin(['#b9c2c9', '#c9c2b2', '#8fa3b3'][rng.integers(3)]))
    if placed:
        bx_, by_ = placed[0]
        for k in range(2):
            x, y = bx_ + 30 + 9 * k, by_ + 22; z = H(x, y)
            if rd(x, y) > 14:
                for q in range(6): Sm.add(cyl(x, y, z - 2 + 7 * q, 1.9 - 0.12 * q, 1.78 - 0.12 * q, 7, 10), RED if q % 2 else WHITE)
                C.circ.append([x, -y, 2.2])
        for k in range(4):
            x, y = bx_ - 34 + (k % 2) * 19, by_ - 30 - (k // 2) * 19; z = H(x, y)
            if rd(x, y) > 16: Sm.add(cyl(x, y, z - 2, 8, 8, 12, 16), lin('#e4e6e8')); Sm.add(cone(x, y, z + 10, 8, 1.6, 16), lin('#c9ccd0'), solid=False); C.circ.append([x, -y, 8.3]); C.noveg.append((x, y, 11))
        lm('Industrial Estate', (bx_, by_ + 30, H(bx_, by_)))

    # ---------------------------------------------------------------- construction site on the city's north edge
    sx_, sy_ = -520.0, 395.0
    if rd(sx_, sy_) > 30:
        z = H(sx_, sy_)
        for fl in range(6):
            S.add(box(sx_, sy_, z - 2.5 + (2.5 if fl else 0) + fl * 3.6, 30, 22, 0.35 if fl else 3.0), CONC)
            if fl < 5:
                for a in np.linspace(-13.5, 13.5, 5):
                    for b in (-9.5, 0, 9.5): S.add(box(sx_ + a, sy_ + b, z + 0.35 + fl * 3.6, .55, .55, 3.3), lin('#a9a69d'))
        for a in np.linspace(-13, 13, 6): S.add(tube(sx_ + a, sy_ - 9.5, z + 18.3, .05, .05, 1.6, 4), lin('#8a3a20'), solid=False)
        mx_, my_ = sx_ + 24, sy_ + 6; mh = 58                    # tower crane
        for dx in (-.8, .8):
            for dy in (-.8, .8): S.add(beam((mx_ + dx, my_ + dy, z - 1), (mx_ + dx, my_ + dy, z + mh), 0.16), YEL)
        for lv in np.arange(3, mh, 3.0):
            S.add(beam((mx_ - .8, my_ - .8, z + lv), (mx_ + .8, my_ + .8, z + lv + 3), 0.09), YEL); S.add(beam((mx_ + .8, my_ - .8, z + lv), (mx_ - .8, my_ + .8, z + lv + 3), 0.09), YEL)
        S.add(beam((mx_ - 13, my_, z + mh), (mx_ + 42, my_, z + mh), 1.0, 1.2), YEL); S.add(box(mx_ - 11, my_, z + mh - 2.6, 4, 2, 2.2), CONC)
        S.add(beam((mx_, my_, z + mh), (mx_, my_, z + mh + 7), 0.3), YEL); S.add(beam((mx_, my_, z + mh + 7), (mx_ + 40, my_, z + mh + 0.6), 0.07), DARK); S.add(beam((mx_, my_, z + mh + 7), (mx_ - 12, my_, z + mh + 0.6), 0.07), DARK)
        S.add(box(mx_ + 1.6, my_, z + mh - 2.4, 1.8, 1.6, 2.0), WHITE); S.add(beam((mx_ + 26, my_, z + mh - 0.6), (mx_ + 26, my_, z + 26), 0.05), DARK); S.add(box(mx_ + 26, my_, z + 24.6, 2.4, 1.2, 1.4), lin('#8f8d86'))
        for k in range(34):                                    # hoarding round the site
            t = k / 34 * 2 * (64 + 52); a, b = (t - 32, -26) if t < 64 else ((32, t - 64 - 26) if t < 116 else ((32 - (t - 116), 26) if t < 180 else (-32, 26 - (t - 180))))
            S.add(box(sx_ + a, sy_ + b, H(sx_ + a, sy_ + b) - 0.2, 6.6 if abs(b) == 26 else 0.12, 0.12 if abs(b) == 26 else 6.6, 2.2), ORANGE if k % 2 else WHITE)
        for k in range(3): S.add(box(sx_ - 24, sy_ - 16 + 7 * k, H(sx_ - 24, sy_ - 16 + 7 * k), 6.1, 2.5, 2.6, 1.57), lin(['#2b5fae', '#e0a526', '#d8d8d4'][k]))
        Sm.add(sphere(sx_ - 20, sy_ + 14, z, 7, 6, 3.2, 8, 5, jit=.18), lin('#8a6b47'))
        ob(sx_, sy_, 64, 52); C.circ.append([mx_, -my_, 2]); C.noveg.append((sx_, sy_, 48)); lm('Construction Site', (sx_, sy_ - 34, z))

    # ---------------------------------------------------------------- roadside shops and a rural fuel station
    def shop(r, i, side, col, sign):
        hw = r['w'] / 2; p = P(r, i, side * (hw + 17)); hd = float(r['head'][i]); z = H(p[0], p[1])
        if abs(z - r['z'][i]) > 2.2 or r['bridge'][i] or r['tunnel'][i] or r['junction'][max(0, i - 6):i + 7].any(): return
        if C.G['tree'].query([p[0], p[1]])[0] < hw + 9: return
        AR.block(C, p[0], p[1], z, 17, 9, 4.4, hd, col, fh=4.4, bw=4.2, shop=True)
        f = np.array([-math.sin(hd), math.cos(hd)]) * side
        S.add(box(p[0] - f[0] * 4.7, p[1] - f[1] * 4.7, z + 4.5, 9, 0.3, 1.5, hd), sign); S.add(box(p[0] - f[0] * 5.6, p[1] - f[1] * 5.6, z + 3.0, 15, 1.8, 0.12, hd), sign * 0.8)
        q = P(r, i, side * (hw + 7.5)); S.add(box(q[0], q[1], min(H(q[0], q[1]), r['z'][i]) - 2.6, 20, 8.5, 2.7 + 0.08, hd), lin('#3b3d41')); C.plats.append([q[0], -q[1], 10, 4.25, hd, min(H(q[0], q[1]), r['z'][i]) + 0.18])
        for k in (-1, 0, 1):
            if rng.random() < 0.6: t = r['tan'][i] * k * 5.4; car(q[0] + t[0], q[1] + t[1], min(H(q[0], q[1]), r['z'][i]) + 0.18, hd + math.pi / 2)
        ob(p[0], p[1], 17, 9, hd); C.noveg.append((p[0], p[1], 20)); n_['shops'] += 1
    scol = [lin(c) for c in ('#e9dcc3', '#d8e2e6', '#f0e0c8', '#e4e1d8')]; sg_ = [lin(c) for c in ('#b3241d', '#1f5f4a', '#22407a', '#c98a1c', '#5a2d6b')]
    for nm, idxs, side in (('West Avenue', (60, 130, 200), 1), ('East Avenue', (70, 150, 230), -1), ('South Road', (70, 150), 1), ('Farm Road', (40, 170), -1), ('Peninsula Road', (60,), 1)):
        for k, i in enumerate(idxs):
            if i < R[nm]['n'] - 8: shop(R[nm], i, side, scol[(k + len(nm)) % 4], sg_[(k * 2 + len(nm)) % 5])
    r = R['Farm Road']; i = 20; p = P(r, i, r['w'] / 2 + 20); hd = float(r['head'][i]); z = H(p[0], p[1])
    if abs(z - r['z'][i]) < 2.5:
        S.add(box(p[0], p[1], z - 2.4, 30, 22, 2.5, hd), lin('#8f8d86')); C.plats.append([p[0], -p[1], 15, 11, hd, z + 0.1]); t = r['tan'][i]; lf = r['left'][i]
        import isle_props as KP, isle_landmarks_hq as LQ, isle_arch as AR_; K_ = KP.Part(); LQ.fuel_station_hq(K_, LQ.kit_mats(), rng, wash=False)
        q = p[:2] + lf * 1.5; AR_.emit_model(K_, q[0], q[1], z + 0.1, math.atan2(-lf[1], -lf[0]) + math.pi / 2, 'Landmark_FuelStation')
        q2 = p[:2] + lf * 11.0; ob(q2[0], q2[1], 16, 7, hd)
        C.noveg.append((p[0], p[1], 24)); lm('Country Fuel Station', (p[0], p[1], z))
    L.STATS['stage3'] = n_

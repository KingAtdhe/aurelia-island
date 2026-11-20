"""Art sheet 08 (roads and junctions) built into the island: highway rumble strips and cat's eyes, marker posts, chevron boards on
tight bends, gravel tracks with wheel ruts and a grass crown, bridge expansion joints, and road-works sites beside the carriageway.
Old-town setts and the roundabout islands are wired in isle_build / isle_stage2; roundabout give-way lines in isle_stage7."""
import math
import numpy as np
import isle_data as K
import isle_props as KP
from isle_lib import lin

STAT = dict(rumble_bars=0, cats_eyes=0, marker_posts=0, chevrons=0, roadworks=0, rut_m=0, joints=0)
WH = lin('#eeeeea')


def along(r, spacing, mask=None, phase=0.0):
    """Evenly spaced stations along road r (finer than the road step): returns idx (float), xy, z, tan, left."""
    n = r['n']; last = n if r['closed'] else n - 1
    t = np.arange(phase, last - 1e-6, spacing / r['step']); i0 = np.floor(t).astype(int); f = (t - i0)[:, None]; i1 = (i0 + 1) % n; i0 = i0 % n
    if mask is not None: keep = mask[i0] & mask[i1]; t, i0, i1, f = t[keep], i0[keep], i1[keep], f[keep]
    xy = r['xy'][i0] * (1 - f) + r['xy'][i1] * f; z = r['z'][i0] * (1 - f[:, 0]) + r['z'][i1] * f[:, 0]
    tn = r['tan'][i0] * (1 - f) + r['tan'][i1] * f; tn /= np.linalg.norm(tn, axis=1)[:, None]; lf = np.c_[-tn[:, 1], tn[:, 0]]
    return t, xy, z, tn, lf


def bars(Mk, xy, z, tn, lf, off, along_len, across, color, dz=0.062):
    """Small painted rectangles centred at xy + lf*off: along_len along the road, across wide."""
    if not len(xy): return 0
    c = xy + lf * off[:, None] if np.ndim(off) else xy + lf * off
    a = tn * along_len / 2; b = lf * across / 2
    V = np.stack([c - a - b, c + a - b, c + a + b, c - a + b], 1); Z = np.repeat((z + dz)[:, None], 4, 1)
    V = np.concatenate([V, Z[..., None]], 2).reshape(-1, 3); q = np.arange(len(c)) * 4
    Mk.add((V, np.vstack([np.c_[q, q + 1, q + 2], np.c_[q, q + 2, q + 3]])), color, solid=False)
    return len(c)


def apply(C, roads, Mk, Dt, rib, dilate, rng):
    TR = C.TR
    for ri, r in enumerate(roads):
        typ = r['type']; hw = r['w'] / 2; n = r['n']; ground = ~(r['bridge'] | r['tunnel']); jm = dilate(r['junction'], 4)
        free = ground & ~jm
        # ---- highway: rumble strip outside each edge line, cat's eyes on the lane lines
        if typ == 'hwy':
            ok = ~jm & ~r['tunnel']
            t, xy, z, tn, lf = along(r, 0.9, ok)
            for sd in (-1, 1): STAT['rumble_bars'] += bars(Mk, xy, z, tn, lf, sd * (hw - 0.1), 0.32, 0.42, lin('#c9c9c4'))
            t, xy, z, tn, lf = along(r, 12.0, ok, 0.3)
            for o in (-3.45, 3.45): STAT['cats_eyes'] += bars(Mk, xy, z, tn, lf, o, 0.16, 0.14, lin('#fff6d8'), 0.075)
            for o in (-(hw - 0.45), hw - 0.45): STAT['cats_eyes'] += bars(Mk, xy, z, tn, lf, o * 0.0 + o, 0.16, 0.14, lin('#ffb020'), 0.075)
        # ---- marker posts every 50 m on fast and country roads (not in town)
        if typ in ('hwy', 'road'):
            t, xy, z, tn, lf = along(r, 50.0, free, 2.0)
            for k in range(len(xy)):
                for sd in (-1, 1):
                    p = xy[k] + lf[k] * sd * (hw + 3.1); B = K.biomes(np.array([p[0]]), np.array([p[1]]))
                    if B['city'][0] > 0.3: continue
                    zg = float(K.sample_h(TR, p[0], p[1]))
                    if abs(zg - z[k]) > 1.6: continue
                    hd = math.atan2(tn[k, 1], tn[k, 0]); KP.KIT.append(('rk_post', p[0], p[1], zg - 0.05, hd + (0.0 if sd > 0 else math.pi))); STAT['marker_posts'] += 1
        # ---- chevron boards round the outside of tight bends
        if typ in ('hwy', 'road'):
            hd = np.unwrap(r['head']); cv = np.gradient(hd) / r['step']; tight = (np.abs(cv) > 1 / 90) & free
            last = -99
            for i in np.where(tight)[0]:
                if (i - last) * r['step'] < 11: continue
                sd = -1 if cv[i] > 0 else 1                                            # outside of the bend
                p = r['xy'][i] + r['left'][i] * sd * (hw + 3.4); zg = float(K.sample_h(TR, p[0], p[1]))
                if abs(zg - r['z'][i]) > 2.5: continue
                inward = -r['left'][i] * sd; yaw = math.atan2(inward[1], inward[0]) + math.pi             # board face (-X) toward the road
                KP.KIT.append(('rk_chevron_r' if cv[i] > 0 else 'rk_chevron_l', p[0], p[1], max(zg, float(r['z'][i]) - 0.6) - 0.05, yaw)); STAT['chevrons'] += 1; last = i
        # ---- gravel tracks: two darker wheel ruts and a grassy crown
        if typ == 'dirt':
            for o, w_, col, dz in ((-0.95, 0.6, lin('#5e4a33'), 0.012), (0.95, 0.6, lin('#5e4a33'), 0.012), (0.0, 0.7, lin('#56653a'), 0.02)):
                Vr, Fr, _ = rib(r, [(o - w_ / 2, dz), (o + w_ / 2, dz)])
                Dt.add((Vr, Fr), col * (0.85 + 0.3 * rng.random((len(Vr), 1))), solid=False, uv=Vr[:, :2] / 3.2)
            STAT['rut_m'] += int(n * r['step'])
        # ---- bridge expansion joints: a dark steel strip across each end
        if typ != 'dirt':
            for a, ln in K.runs(r['bridge'], r['closed']):
                for e in (a, a + ln - 1):
                    t, xy, z, tn, lf = along(r, 1e9, None, float(e % n))
                    for k in range(-6, 7):
                        bars(Mk, xy, z, tn, lf, k * (hw - 0.3) / 6.5, 0.36, (hw - 0.3) / 6.5 + 0.02, lin('#3a3c40'), 0.064)
                    STAT['joints'] += 1
    roadworks(C, roads, dilate)
    return STAT


def roadworks(C, roads, dilate, sites=4):
    """Works beside the carriageway on straight country-road stretches: a dug trench behind red-and-white barriers on the verge,
    cones along the edge line, an arrow board, and warning signs 80 m before in both directions."""
    TR = C.TR; r_ = np.random.default_rng(23); cand = []
    for ri, r in enumerate(roads):
        if r['type'] not in ('road', 'hwy'): continue
        hd = np.unwrap(r['head']); n = r['n']; free = ~(dilate(r['junction'] | r['bridge'] | r['tunnel'], 30)); k = int(60 / r['step'])
        for i in range(k + 30, n - k - 30, k):
            if not free[i - k:i + k].all() or abs(hd[i + k] - hd[i - k]) > 0.12: continue
            B = K.biomes(r['xy'][i:i + 1, 0], r['xy'][i:i + 1, 1])
            if B['city'][0] > 0.2: continue
            cand.append((ri, i))
    if not cand: return
    pick = [cand[j] for j in sorted(r_.choice(len(cand), min(sites, len(cand)), replace=False))]
    for ri, i in pick:
        r = roads[ri]; hw = r['w'] / 2; sd = 1 if r_.random() < 0.5 else -1; step = r['step']; n = r['n']
        def at(s_m, o):                                                                  # s_m: metres from the site centre along the road
            t = i + s_m / step; i0 = int(np.floor(t)) % n; i1 = (i0 + 1) % n; f = t - np.floor(t)
            c = r['xy'][i0] * (1 - f) + r['xy'][i1] * f; tn = r['tan'][i0] * (1 - f) + r['tan'][i1] * f; lf = np.array([-tn[1], tn[0]]) / np.linalg.norm(tn)
            p = c + lf * o; return p, float(K.sample_h(TR, p[0], p[1])), float(r['z'][i0] * (1 - f) + r['z'][i1] * f), math.atan2(tn[1], tn[0])
        for k, s_m in enumerate(np.arange(-20.0, 20.01, 2.0)):                              # barriers on the verge, red and white alternately
            p, zg, zr, hd = at(s_m, sd * (hw + 1.4)); KP.KIT.append(('rk_barrier' if k % 2 else 'rk_barrier_w', p[0], p[1], max(zg, zr - 0.3) - 0.03, hd))
            C.obst.append([p[0], -p[1], 1.0, 0.3, hd])
        for s_m in np.arange(-16.0, 16.01, 6.0):
            p, zg, zr, hd = at(s_m, sd * (hw + 3.2)); KP.KIT.append(('rk_trench', p[0], p[1], max(zg, zr - 0.4) + 0.01, hd))
        for s_m in np.arange(-36.0, 26.01, 4.0):                                           # cone line on the edge marking
            p, zg, zr, hd = at(s_m, sd * (hw - 0.35)); KP.KIT.append(('rk_cone', p[0], p[1], zr + 0.04, hd))
        p, zg, zr, hd = at(-30.0, sd * (hw + 1.6)); KP.KIT.append(('rk_arrowboard', p[0], p[1], max(zg, zr - 0.3), hd))
        for s_m, flip in ((-80.0, 0.0), (80.0, math.pi)):
            for s2 in (-1, 1):
                p, zg, zr, hd = at(s_m, s2 * (hw + 2.4)); KP.KIT.append(('rk_worksign', p[0], p[1], zg - 0.05, hd + flip))
        STAT['roadworks'] += 1


# ================================================================== art sheet 11: touge treatment of the mountain passes
MTN = ('Summit Pass', 'Skyline Road', 'Eagle Descent', 'Serpentine')
TSTAT = dict(cut_m=0, lattice_m=0, shotcrete_m=0, mirrors=0, lights=0, conifers=0)


def lattice_image(N=512, cells=2):
    """Concrete lattice frame: square beams with transparent cells (the terrain's grass shows through); 'cells' x 'cells' per tile."""
    rng = np.random.default_rng(12); a = np.zeros((N, N, 4)); c = N // cells; w = int(c * 0.16)
    g = 0.7 + 0.08 * rng.random((N, N)); g = g - 0.06 * (rng.random((N, N)) > 0.985)
    m = np.zeros((N, N), bool)
    for k in range(cells + 1):
        lo, hi = max(0, k * c - w // 2), min(N, k * c + w // 2); m[lo:hi, :] = True; m[:, lo:hi] = True
    a[..., 0] = g * 0.98; a[..., 1] = g * 0.97; a[..., 2] = g * 0.93; a[..., 3] = m.astype(float)
    for k in range(cells + 1):                                                         # a darker joint where beams cross
        for j in range(cells + 1):
            y0, x0 = max(0, k * c - w // 2), max(0, j * c - w // 2); a[y0:y0 + w, x0:x0 + w, :3] *= 0.9
    return a


def _surface(Bf, rows, color, uvs=2.2):
    """rows: list of (n_cols, 3) arrays along the road (consecutive stations). Quads between rows; faces turned to point up/outward."""
    R = np.array(rows); m, k, _ = R.shape
    if m < 2: return 0
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(R[:, 0, :2], axis=0), axis=1))]
    d = np.zeros((m, k)); d[:, 1:] = np.cumsum(np.linalg.norm(np.diff(R, axis=1), axis=2), axis=1)
    V = R.reshape(-1, 3); U = np.c_[np.repeat(s, k), d.ravel()] / uvs
    a = (np.arange(m - 1)[:, None] * k + np.arange(k - 1)[None, :]).ravel(); b = a + k
    F = np.vstack([np.c_[a, b, b + 1], np.c_[a, b + 1, a + 1]])
    nz = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])[:, 2]
    if (nz < 0).sum() > len(nz) / 2: F = F[:, ::-1]
    Bf.add((V, F), color, solid=False, uv=U); return s[-1]


def touge(C, roads, Mk, Dt, rib, dilate, rng):
    import isle_lib as L, isle_props as KP, isle_touge_hq as TQ
    TR = C.TR; BT = C.BT; LT = L.Buf(); SC = L.Buf(); GT = L.Buf(); CONC = lin('#b5b2aa'); DK = lin('#3b3d3b')
    TQ.register_kit()
    for r in roads:
        if r['name'] not in MTN: continue
        hw = r['w'] / 2; n = r['n']; ground = ~(r['bridge'] | r['tunnel']); jm = dilate(r['junction'], 4)
        offs = np.array([1.25, 2.5, 4.5, 7.0, 10.0, 14.0, 19.0, 25.0, 31.0])
        cutmask = {}
        for side in (-1, 1):
            q30 = r['xy'] + r['left'] * side * (hw + 31.0); H30 = K.sample_h(TR, q30[:, 0], q30[:, 1])
            q18 = r['xy'] + r['left'] * side * (hw + 18.0); H18 = K.sample_h(TR, q18[:, 0], q18[:, 1])
            cut = dilate((H30 - r['z'] > 4.0) & (H18 > r['z'] - 0.5), 2) & ground & ~jm; cutmask[side] = cut
            for a, ln in K.runs(cut, r['closed']):
                if ln < 5: continue
                idx = [(a + k) % n for k in range(ln)]; m = np.zeros(n, bool); m[idx] = True
                # retaining wall at the foot of the cut, with a coping, and the U-ditch in front of it
                o = side * (hw + 1.25); Vw, Fw, _ = rib(r, [(o, -0.3), (o, 1.35)] if side > 0 else [(o, 1.35), (o, -0.3)], m); Vw, Fw = L.compact(Vw, Fw)
                BT.add((Vw, Fw), lin('#a9a69e'), solid=False); BT.add((Vw, Fw[:, ::-1]), lin('#a9a69e'), solid=False)
                Vc, Fc, _ = rib(r, [(o - 0.35 * side, 1.35), (o + 0.25 * side, 1.35)] if side > 0 else [(o + 0.25 * side, 1.35), (o - 0.35 * side, 1.35)], m); Vc, Fc = L.compact(Vc, Fc); BT.add((Vc, Fc), lin('#8f8c84'), solid=False); BT.add((Vc, Fc[:, ::-1]), lin('#8f8c84'), solid=False)
                for (o0, o1, col) in ((hw + 0.15, hw + 0.3, CONC), (hw + 0.3, hw + 0.95, DK), (hw + 0.95, hw + 1.1, CONC)):
                    pr = [(side * o0, 0.07), (side * o1, 0.07)]; Vd, Fd, _ = rib(r, pr if side > 0 else pr[::-1], m); Vd, Fd = L.compact(Vd, Fd); Mk.add((Vd, Fd), col, solid=False)
                # the cut: a steep engineered face from the wall top to the hillside's height within ~10 m, then a grassed terrace back to the slope
                rows, trows = [], []; Ht = np.convolve(H30[idx] if False else H30[idx], np.ones(5) / 5, mode='same') if ln >= 5 else H30[idx]
                for kk, i in enumerate(idx):
                    z0 = r['z'][i] + 1.38; top = max(float(Ht[kk]), z0 + 2.0); row = []; trow = []
                    for d_ in offs:
                        p = r['xy'][i] + r['left'][i] * side * (hw + d_); zg = float(K.sample_h(TR, p[0], p[1])) + 0.12
                        t = np.clip((d_ - 1.25) / 8.75, 0, 1); zf = z0 + (top - z0) * (t ** 0.85)
                        if d_ <= 10.0: row.append((p[0], p[1], max(zf, zg)))
                        if d_ >= 10.0: trow.append((p[0], p[1], max(top if d_ < 25 else 0.5 * (top + zg), zg)))
                    rows.append(row); trows.append(trow)
                steep = float(np.median([(row[-1][2] - row[0][2]) / 8.75 for row in rows])) > 1.6
                L_ = _surface(SC if steep else LT, rows, lin('#9d9a92') if steep else np.ones(3), 2.2)
                _surface(GT, trows, lin('#4f7a2c'), 6.0)
                for kk in range(0, len(idx), max(1, int(9 / r['step']))):                     # conifers along the terrace edge, above the cut
                    i = idx[kk]
                    for d_ in (12.5, 17.0, 22.0):
                        if rng.random() < 0.35: continue
                        p = r['xy'][i] + r['left'][i] * side * (hw + d_ + rng.uniform(-1, 1)) + r['tan'][i] * rng.uniform(-3, 3); zt_ = trows[kk][1 if d_ < 16 else 2][2]
                        v = rng.uniform(0.7, 0.95); C.inst.append((('spruce', 'spruce_b', 'pine')[int(rng.integers(3))], p[0], p[1], zt_ - 0.1, rng.uniform(0.8, 1.15), v, v * 1.02, v * 0.95)); TSTAT['conifers'] += 1
                C.noveg.extend([(r['xy'][i][0] + r['left'][i][0] * side * (hw + 6), r['xy'][i][1] + r['left'][i][1] * side * (hw + 6), 6.0) for i in idx[::3]])
                TSTAT['cut_m'] += int(ln * r['step']); TSTAT['shotcrete_m' if steep else 'lattice_m'] += int(L_)
        # hairpins: curve mirror and a sodium light on the outside of every tight bend
        hd = np.unwrap(r['head']); cv = np.gradient(hd) / r['step']; last = -999
        for i in np.where((np.abs(cv) > 1 / 45) & ground & ~jm)[0]:
            if (i - last) * r['step'] < 45: continue
            sd = -1 if cv[i] > 0 else 1; p = r['xy'][i] + r['left'][i] * sd * (hw + 2.2); zg = float(K.sample_h(TR, p[0], p[1]))
            if abs(zg - r['z'][i]) > 2.0: continue
            face = -r['left'][i] * sd; yaw = math.atan2(face[1], face[0])
            KP.KIT.append(('tg_mirror', p[0], p[1], zg - 0.05, yaw)); TSTAT['mirrors'] += 1
            j = int(np.clip(i + int(8 / r['step']), 0, n - 1)); p2 = r['xy'][j] + r['left'][j] * sd * (hw + 2.4); z2 = float(K.sample_h(TR, p2[0], p2[1]))
            if abs(z2 - r['z'][j]) < 2.0:
                f2 = -r['left'][j] * sd; KP.KIT.append(('tg_light', p2[0], p2[1], z2 - 0.05, math.atan2(f2[1], f2[0]))); TSTAT['lights'] += 1
            last = i
        # a close wall of conifers on the open side of the road
        for i in range(0, n, max(1, int(4.5 / r['step']))):
            if not ground[i] or jm[i]: continue
            for side in (-1, 1):
                for row_o in (5.5, 9.0, 13.0):
                    if rng.random() < 0.25: continue
                    p = r['xy'][i] + r['left'][i] * side * (hw + row_o + rng.uniform(-1.0, 1.0)) + r['tan'][i] * rng.uniform(-2.0, 2.0); zg = float(K.sample_h(TR, p[0], p[1]))
                    if cutmask.get(side, np.zeros(n, bool))[i] or zg - r['z'][i] > 2.0 or zg < 3.0 or zg > 140: continue      # cut side gets the slope cover, not trees
                    v = rng.uniform(0.7, 0.95); C.inst.append((('spruce', 'spruce_b', 'pine')[int(rng.integers(3))], p[0], p[1], zg - 0.1, rng.uniform(0.75, 1.1), v, v * 1.02, v * 0.95)); TSTAT['conifers'] += 1
    img = L.make_image('touge_lattice', lattice_image())
    if len(LT.V): LT.emit('TougeLattice', L.new_mat('TougeLattice', 0.9, image=img, vcol=True, cutout=True, double=True), smooth=False, uv=True)
    if len(GT.V):
        import isle_ground as GRd; GT.emit('TougeTerrace', getattr(C.M, 'forest', None) or C.M.ter, smooth=True, uv=True)
    if len(SC.V):
        SC.emit('TougeShotcrete', C.M.pt, smooth=True, uv=True)
    return TSTAT

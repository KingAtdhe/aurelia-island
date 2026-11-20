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

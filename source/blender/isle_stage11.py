"""Stage 11 for Aurelia Island: shoreline foam and shallows, beach furniture, fountains, viaduct railings, rock outcrops,
bend markers, planting at the road edge, and the ground shade map."""
import math, json, os
import numpy as np
from scipy.spatial import cKDTree
import isle_data as K
import isle_lib as L
import isle_arch as AR
from isle_lib import lin, box, beam, cyl, cone, lathe
rng = np.random.default_rng(1111); STAT = {}


def coast(C):
    M = C.M; TR = C.TR; H = TR['H']; X = TR['X']; Y = TR['Y']
    for nm, colr in (('foam', (0.95, 0.97, 0.98)), ('shallow', (0.22, 0.78, 0.74))):
        m = M.ao.copy(); m.name = 'ShoreFoam' if nm == 'foam' else 'Shallows'; b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (*colr, 1); b.inputs['Roughness'].default_value = 0.3 if nm == 'shallow' else 0.9; setattr(M, nm, m)
    land = H > 0.25; edge = land & ~(np.roll(land, 1, 0) & np.roll(land, -1, 0) & np.roll(land, 1, 1) & np.roll(land, -1, 1)); edge[[0, -1]] = False; edge[:, [0, -1]] = False
    gy, gx = np.gradient(H, K.CELL); iy, ix = np.where(edge); B = K.biomes(X[iy, ix], Y[iy, ix]); ok = B['city'] < 0.5; iy, ix = iy[ok], ix[ok]
    p = np.c_[X[iy, ix], Y[iy, ix]]; g = np.c_[gx[iy, ix], gy[iy, ix]]; g /= np.maximum(np.linalg.norm(g, axis=1), 1e-6)[:, None]; t = np.c_[-g[:, 1], g[:, 0]]; n = len(p); up = np.array([0, 0, 1.0])
    def strip(part, a_in, a_out, z, half):
        Q = np.stack([np.c_[p + g * a_in - t * half, np.full(n, z)], np.c_[p + g * a_in + t * half, np.full(n, z)], np.c_[p + g * a_out + t * half, np.full(n, z)], np.c_[p + g * a_out - t * half, np.full(n, z)]], 1)
        AR.quads(part, Q, up, np.ones(3), np.tile(np.array([[(0, 0.02), (1, 0.02), (1, 0.98), (0, 0.98)]]), (n, 1, 1)), None)
    strip('shallow', 4.0, -38.0, 0.05, 9.0); strip('foam', 3.0, -5.0, 0.11, 8.5); STAT['shore_cells'] = n
    # beach furniture where the shore is gentle sand outside the city and the desert
    rd = C.G['tree'].query(p)[0]; sl = np.hypot(gx[iy, ix], gy[iy, ix]); sel = np.where((sl < 0.16) & (rd > 30) & (B['desert'][ok] < 0.4))[0][::5]; cols = [lin(c) for c in ('#d8452f', '#2b6fae', '#e8c63a', '#f2f0e6', '#2f9a57')]; nb = 0
    for k in sel:
        q = p[k] + g[k] * 9.0; z = C.hgt(q[0], q[1])
        if z < 0.7 or z > 3.2: continue
        import isle_props as KP; sea = math.atan2(-g[k][1], -g[k][0])             # art sheet 06: modelled beach kit, facing the sea
        kind = 'rowing_boat' if nb % 4 == 3 else ('lifeguard' if nb % 7 == 1 else ('beach_bar' if nb % 11 == 5 else 'beach_set'))
        if kind == 'beach_bar': q = q + g[k] * 4.0; z = C.hgt(q[0], q[1])
        KP.KIT.append((kind, q[0], q[1], z - 0.05, sea)); C.circ.append([q[0], -q[1], {'beach_bar': 4.5, 'lifeguard': 2.2, 'beach_set': 2.5, 'rowing_boat': 1.6}[kind]])
        nb += 1
    STAT['beach_sets'] = nb


def fountains(C):
    for cx, cy, rr in K.ROUNDABOUTS:
        z = C.hgt(cx, cy) + 0.2; st = lin('#cfc9bb')
        C.Sm.add(lathe(cx, cy, z, [(4.4, 0.0), (4.6, 0.7), (4.2, 0.75), (4.1, 0.3), (0.0, 0.3)], 1, 1, 28), st, solid=False)
        C.Sm.add(lathe(cx, cy, z, [(4.1, 0.55), (0.0, 0.55)], 1, 1, 28), lin('#3f9fb5'), solid=False)
        C.Sm.add(lathe(cx, cy, z, [(0.55, 0.3), (0.4, 1.6), (1.5, 1.9), (1.6, 2.1), (0.3, 2.0), (0.22, 3.0), (0.7, 3.2), (0.1, 3.35)], 1, 1, 16), st, solid=False)
        for k in range(8):
            a = k * math.pi / 4; p0 = np.array([cx + 1.5 * math.cos(a), cy + 1.5 * math.sin(a), z + 2.05]); p1 = np.array([cx + 3.3 * math.cos(a), cy + 3.3 * math.sin(a), z + 0.6]); C.S.add(beam(p0, (p0 + p1) / 2 + (0, 0, 0.5), 0.07), lin('#bfe6f2')); C.S.add(beam((p0 + p1) / 2 + (0, 0, 0.5), p1, 0.07), lin('#bfe6f2'))
        C.landmarks.append(('Fountain' if cx > 600 else None, np.array([cx, cy, z])))
    STAT['fountains'] = len(K.ROUNDABOUTS)


def roadside(C):
    """Reflector posts round bends and chevron boards on the outside of sharp ones."""
    PR = C.PR; np_ = nc = 0
    for r in C.roads:
        if r['type'] not in ('hwy', 'road'): continue
        hd = np.unwrap(r['head']); cv = np.gradient(hd) / r['step']; hw = r['w'] / 2; ok = ~(r['bridge'] | r['tunnel'] | r['junction'])
        for i in range(2, r['n'] - 2, 3):
            if not ok[i] or abs(cv[i]) < 1 / 320: continue
            import isle_props as KP
            for sg in (-1, 1): p = C.P(r, i, sg * (hw + 1.1)); KP.KIT.append(('reflector', p[0], p[1], p[2] - 0.05, float(r['head'][i]) + (math.pi if sg > 0 else 0.0))); np_ += 1
            if abs(cv[i]) > 1 / 95 and i % 2 == 0:
                o = -np.sign(cv[i]) * (hw + 2.3); p = C.P(r, i, o); h = r['head'][i]
                PR.add(box(p[0], p[1], p[2] - 0.3, 0.09, 0.09, 1.6, h), lin('#6a6f75')); PR.add(box(p[0], p[1], p[2] + 0.75, 0.06, 1.0, 0.55, h + math.pi / 2), lin('#e8b520')); PR.add(box(p[0], p[1], p[2] + 0.9, 0.08, 0.5, 0.22, h + math.pi / 2), lin('#141414')); nc += 1
    STAT['reflector_posts'] = np_; STAT['chevron_boards'] = nc


def lookouts(C):
    """Lay-bys where a road runs along a drop: a paved pad on a stone base, a parapet, a bench and a board."""
    TR = C.TR; out = []; S = C.S; BT = C.BT; stone = lin('#857c6e')
    for r in C.roads:
        if r['type'] not in ('road', 'hwy') or r['closed']: continue
        hw = r['w'] / 2; ok = ~(r['bridge'] | r['tunnel'] | r['junction']); jm = r['junction'].copy()
        for k in range(1, 12): jm[k:] |= r['junction'][:-k]; jm[:-k] |= r['junction'][k:]
        for sg in (-1, 1):
            drop = np.max([r['z'] - K.sample_h(TR, *(r['xy'] + r['left'] * sg * (hw + D_)).T) for D_ in (22, 45, 70)], 0); drop[~ok | jm] = 0; drop[:6] = 0; drop[-6:] = 0
            for i in np.argsort(-drop)[:6]:
                if drop[i] < 12 or any(math.hypot(*(r['xy'][i] - o[:2])) < 450 for o in out): continue
                c = r['xy'][i] + r['left'][i] * sg * (hw + 3.25); z = float(r['z'][i]); hd = float(r['head'][i])
                if C.G['tree'].query(c)[0] < hw + 1.5 or C.G['tree'].query(c + r['left'][i] * sg * 3.6)[0] < 6.5 or any(abs(C.P(r, j, sg * (hw + 3.6))[2] - z) > 0.6 for j in (i - 1, i + 1)): continue
                bot = min(float(K.sample_h(TR, c[0], c[1])), z - 1.0) - 1.5; BT.add(box(c[0], c[1], bot, 14.0, 6.6, z - 0.02 - bot, hd), stone)
                Vp = np.array([[c[0] + a * math.cos(hd) - b * math.sin(hd), c[1] + a * math.sin(hd) + b * math.cos(hd), z + 0.01] for a, b in ((-7, -3.3), (7, -3.3), (7, 3.3), (-7, 3.3))])
                C.PV.add((Vp, np.array([(0, 1, 2), (0, 2, 3)])), lin('#8f8b82'), solid=False, uv=Vp[:, :2] / 4.0)
                w0 = c + r['left'][i] * sg * 3.1; lv_ = r['left'][i] * sg                                                  # art sheet 07: modelled lookout terrace
                import isle_props as KP; kc_ = c - lv_ * 0.6; KP.KIT.append(('lookout', kc_[0], kc_[1], z + 0.02, math.atan2(lv_[1], lv_[0])))
                C.plats.append([c[0], -c[1], 7.0, 3.3, hd, z + 0.02]); C.obst.append([w0[0], -w0[1], 7.0, 0.3, hd]); C.noveg.append((c[0], c[1], 9.0))
                C.landmarks.append(('Lookout' if not out else None, np.array([c[0], c[1], z]))); out.append(np.array([c[0], c[1]]))
    STAT['lookouts'] = len(out)


def wild_props(C):
    """Art sheet 07 roadside pieces: windpumps and desert stops beside the desert roads, mountain signs at the foot of the pass."""
    import isle_props as KP; R = {r['name']: r for r in C.roads}; n_ = dict(windpump=0, desert_stop=0, mountain_signs=0)
    plan = [('Dune Road', 0.3, 'desert_stop', 9.0), ('Dune Road', 0.62, 'windpump', 26.0), ('Mesa Road', 0.45, 'windpump', 28.0), ('Mesa Road', 0.8, 'desert_stop', 9.0),
            ('Canyon Road', 0.55, 'windpump', 30.0), ('Summit Pass', 0.08, 'mountain_signs', 5.5), ('Eagle Descent', 0.1, 'mountain_signs', 5.5)]
    for rn, fr, kind, off in plan:
        r = R.get(rn)
        if r is None: continue
        for k in range(60):
            i = int(r['n'] * fr) + k
            if i >= r['n'] - 2 or r['junction'][i] or r['bridge'][i] or r['tunnel'][i]: continue
            sg = 1 if k % 2 == 0 else -1; q = r['xy'][i] + r['left'][i] * sg * (r['w'] / 2 + off); z = C.hgt(q[0], q[1])
            if C.G['tree'].query(q)[0] < r['w'] / 2 + off - 2 or max(abs(C.hgt(q[0] + dx, q[1] + dy) - z) for dx, dy in ((4, 0), (-4, 0), (0, 4), (0, -4))) > 1.2: continue
            face = -r['left'][i] * sg                                                                # +X of the piece faces the road
            KP.KIT.append((kind, q[0], q[1], z - 0.05, math.atan2(face[1], face[0]))); C.circ.append([q[0], -q[1], {'windpump': 3.0, 'desert_stop': 3.0, 'mountain_signs': 0.6}[kind]]); n_[kind] += 1; break
    STAT['wild_props'] = n_


def road_decals(C):
    """Cracks, repair patches, oil stains and manhole covers laid on the carriageways (alpha-blended decals)."""
    import bpy, isle_tex as TX
    img = L.make_image('road_decals', TX.decal_atlas()); m = bpy.data.materials.new('RoadDecals'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; nt.links.new(t.outputs['Color'], b.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], b.inputs['Alpha']); b.inputs['Roughness'].default_value = 0.6
    try: m.surface_render_method = 'BLENDED'
    except Exception: pass
    D = L.Buf(); cells = {'crack': (0, 0.5), 'patch': (0.5, 0.5), 'oil': (0, 0), 'manhole': (0.5, 0)}; n_ = {k: 0 for k in cells}
    for r in C.roads:
        if r['type'] in ('dirt',): continue
        hw = r['w'] / 2; ok = ~(r['bridge'] | r['tunnel']); i = int(rng.integers(2, 6))
        while i < r['n'] - 3:
            if ok[i]:
                u = rng.random(); kind = 'crack' if u < 0.42 else ('patch' if u < 0.62 else ('oil' if u < 0.9 else ('manhole' if r['type'] == 'street' else 'crack')))
                if r['type'] == 'circuit' and kind != 'crack': kind = 'crack' if rng.random() < 0.5 else 'oil'
                L_ = {'crack': rng.uniform(3, 6), 'patch': rng.uniform(2.5, 5), 'oil': rng.uniform(1.2, 2.2), 'manhole': 0.9}[kind]; W_ = {'crack': L_ * 0.8, 'patch': L_ * 0.6, 'oil': L_ * 0.8, 'manhole': 0.9}[kind]
                lane = rng.choice([-1, 1]) * (hw * 0.5 + rng.uniform(-0.7, 0.7) * (hw * 0.25)); c = r['xy'][i] + r['left'][i] * lane; t = r['tan'][i]; lf = r['left'][i]; z = float(r['z'][i]) + 0.035
                Vq = np.array([np.r_[c - t * L_ / 2 - lf * W_ / 2, z], np.r_[c + t * L_ / 2 - lf * W_ / 2, z], np.r_[c + t * L_ / 2 + lf * W_ / 2, z], np.r_[c - t * L_ / 2 + lf * W_ / 2, z]])
                u0, v0 = cells[kind]; Uq = np.array([(u0, v0), (u0 + 0.5, v0), (u0 + 0.5, v0 + 0.5), (u0, v0 + 0.5)]) * 0.98 + 0.005
                Fq = np.array([(0, 1, 2), (0, 2, 3)]) if np.cross(Vq[1] - Vq[0], Vq[2] - Vq[0])[2] > 0 else np.array([(0, 2, 1), (0, 3, 2)])
                D.add((Vq, Fq), np.ones(3), solid=False, uv=Uq); n_[kind] += 1
            i += int(rng.integers(3, 9)) if r['type'] == 'street' else int(rng.integers(4, 12))
    D.emit('RoadDecals', m, smooth=False, uv=True); STAT['road_decals'] = n_
    road_wear(C)
    street_detail(C)


def road_wear(C):
    """Tyre skid marks (pairs of rubber streaks, at bends and junctions) and rain puddles in the dips along the road edges."""
    import bpy
    from PIL import Image, ImageDraw, ImageFilter
    def mat(name, rgba, rough, metal=0.0):
        img = L.make_image(name.lower(), rgba); m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; nt.links.new(t.outputs['Color'], b.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
        b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
        return m
    r_ = np.random.default_rng(11)
    sk = np.zeros((512, 64, 4)); sk[..., :3] = 0.03; prof = np.exp(-((np.arange(64) - 31.5) / 18.0) ** 4)          # skid: soft-edged rubber streak with grain
    sk[..., 3] = prof[None, :] * (0.55 + 0.45 * r_.random((512, 64))) * (0.7 + 0.3 * np.sin(np.arange(512) / 512 * np.pi)[:, None]) ** 0.5 * 0.75
    im = Image.new('L', (256, 256), 0); d = ImageDraw.Draw(im)                                                        # puddle: irregular blob
    for k in range(9): x, y, rr = r_.uniform(70, 186), r_.uniform(90, 166), r_.uniform(30, 70); d.ellipse([x - rr, y - rr * 0.55, x + rr, y + rr * 0.55], fill=255)
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(9)), float) / 255.0; a = np.clip((a - 0.35) * 3.0, 0, 1)
    pu = np.dstack([np.full((256, 256), 0.035), np.full((256, 256), 0.04), np.full((256, 256), 0.05), a * 0.92])
    Ms, Mp = mat('Skids', sk, 0.75), mat('Puddles', pu, 0.03)
    Sk, Pu = L.Buf(), L.Buf(); ns = npud = 0
    for r in C.roads:
        if r['type'] in ('dirt',): continue
        hw = r['w'] / 2; ok = ~(r['bridge'] | r['tunnel']); hd = np.unwrap(r['head']); cv = np.gradient(hd) / r['step']; n = r['n']
        for i in range(4, n - 8, 3):
            if not ok[i]: continue
            hot = abs(cv[i]) > 1 / 120 or r['junction'][max(0, i - 4):i + 5].any() or r['type'] == 'circuit'
            if hot and r_.random() < (0.35 if r['type'] == 'circuit' else 0.12):                                          # a pair of skid marks curving through
                L_ = r_.uniform(8, 22); lane = r_.uniform(-0.4, 0.4) * hw; k = max(2, int(L_ / r['step']))
                for side in (-0.78, 0.78):
                    pts = [r['xy'][min(n - 1, i + j)] + r['left'][min(n - 1, i + j)] * (lane + side + 0.4 * math.sin(j / k * 2.0)) for j in range(k + 1)]
                    zs = [float(r['z'][min(n - 1, i + j)]) + 0.037 for j in range(k + 1)]
                    V = []; Uq = []
                    for j, (p, z) in enumerate(zip(pts, zs)):
                        lf = r['left'][min(n - 1, i + j)]; V += [np.r_[p - lf * 0.12, z], np.r_[p + lf * 0.12, z]]; Uq += [(0.0, j / k), (1.0, j / k)]
                    F = [(2 * j, 2 * j + 2, 2 * j + 3) for j in range(k)] + [(2 * j, 2 * j + 3, 2 * j + 1) for j in range(k)]
                    V = np.array(V); F = np.array(F)
                    if np.cross(V[2] - V[0], V[3] - V[0])[2] < 0: F = F[:, ::-1]
                    Sk.add((V, F), np.ones(3), solid=False, uv=np.array(Uq))
                ns += 1
            if r['type'] != 'circuit' and r_.random() < 0.05:                                                       # puddle near the kerb
                L_ = r_.uniform(1.6, 3.6); W_ = L_ * r_.uniform(0.45, 0.7); c = r['xy'][i] + r['left'][i] * r_.choice([-1, 1]) * (hw - W_ / 2 - 0.25); t = r['tan'][i]; lf = r['left'][i]; z = float(r['z'][i]) + 0.04
                V = np.array([np.r_[c - t * L_ / 2 - lf * W_ / 2, z], np.r_[c + t * L_ / 2 - lf * W_ / 2, z], np.r_[c + t * L_ / 2 + lf * W_ / 2, z], np.r_[c - t * L_ / 2 + lf * W_ / 2, z]])
                F = np.array([(0, 1, 2), (0, 2, 3)]) if np.cross(V[1] - V[0], V[2] - V[0])[2] > 0 else np.array([(0, 2, 1), (0, 3, 2)])
                Pu.add((V, F), np.ones(3), solid=False, uv=np.array([(0, 0), (1, 0), (1, 1), (0, 1)], float)); npud += 1
    Sk.emit('Skids', Ms, smooth=False, uv=True); Pu.emit('Puddles', Mp, smooth=False, uv=True); STAT['skid_pairs'] = ns; STAT['puddles'] = npud


def grass_verges(C):
    """Dense grass clumps on the verges, the first thing seen beside the car."""
    TR = C.TR; G = C.G; hwv = np.concatenate([np.full(r['n'], r['w'] / 2) for r in C.roads]); pts = []
    for r in C.roads:
        if r['type'] in ('street', 'circuit', 'rbt'): continue
        hw = r['w'] / 2; g_ = ~(r['bridge'] | r['tunnel'] | r['junction'])
        for i in np.where(g_)[0]:
            for _ in range(4): o = rng.choice([-1, 1]) * (hw + 3.6 + rng.uniform(0, 9)); q = r['xy'][i] + r['left'][i] * o + r['tan'][i] * rng.uniform(-2.5, 2.5); pts.append((q[0], q[1]))
    P = np.array(pts); B = K.biomes(P[:, 0], P[:, 1]); h = K.sample_h(TR, P[:, 0], P[:, 1]); d, i = G['tree'].query(P)
    m = (d > hwv[i] + 3.2) & (h > 2.6) & (h < 135) & (B['city'] < 0.3) & (B['desert'] < 0.45) & (B['circuit'] < 0.3)
    for lx, ly, lr in K.LAKES: m &= np.hypot(P[:, 0] - lx, P[:, 1] - ly) > lr + 4
    k_ = 0
    for k in np.where(m)[0][:42000]:
        g = rng.uniform(0.8, 1.05); dry = rng.uniform(0, 1) * (1 - B['forest'][k]); C.inst.append(('grass' if rng.random() < 0.82 else 'grass_tall', P[k, 0], P[k, 1], h[k], rng.uniform(0.9, 1.6), g * (1 + 0.25 * dry), g * (1 + 0.05 * dry), g * (0.85 - 0.1 * dry))); k_ += 1
    STAT['verge_grass'] = k_


def scatter(C):
    TR = C.TR; G = C.G; inst = C.inst; hwv = np.concatenate([np.full(r['n'], r['w'] / 2) for r in C.roads]); rtype = np.concatenate([np.full(r['n'], r['type'] == 'dirt') for r in C.roads])
    ob = np.array([(o[0], -o[1], math.hypot(o[2], o[3]) + 2.5) for o in C.obst] + [(o[0], -o[1], o[2] + 2.5) for o in C.circ] + [(q[0], q[1], q[2]) for q in C.noveg if q[2] > 0]); ot = cKDTree(ob[:, :2])
    def ok(P):
        h = K.sample_h(TR, P[:, 0], P[:, 1]); dd, ii = ot.query(P, k=3); m = (h > 2.6) & (dd > ob[ii, 2]).all(1)
        for lx, ly, lr in K.LAKES: m &= np.hypot(P[:, 0] - lx, P[:, 1] - ly) > lr + 5
        sl = np.hypot(K.sample_h(TR, P[:, 0] + 5, P[:, 1]) - h, K.sample_h(TR, P[:, 0], P[:, 1] + 5) - h) / 5; return m, h, sl
    # rock outcrops: big blocks sunk into steep ground
    P = np.c_[rng.uniform(K.X0 + 60, K.X1 - 60, 200000), rng.uniform(K.Y0 + 60, K.Y1 - 60, 200000)]; B = K.biomes(P[:, 0], P[:, 1]); m, h, sl = ok(P); d, i = G['tree'].query(P)
    sel = np.where(m & (sl > 0.62) & (sl < 1.6) & (h > 25) & (d > hwv[i] + 12) & (B['city'] < 0.3))[0][:900]
    for k in sel:
        sc = rng.uniform(3.0, 8.0); des = B['desert'][k] > 0.5; g = rng.uniform(.8, 1.05); sn = 1.3 if (h[k] > 150 and not des) else 1.0
        inst.append(('sandstone' if des else ('rock', 'rock_b', 'rock_c')[k % 3], P[k, 0], P[k, 1], h[k] - sc * 0.42, sc, g * sn, g * sn, g * sn))
    STAT['outcrops'] = len(sel)
    # planting right at the road edge in forest and countryside
    pts = []
    for r in C.roads:
        if r['type'] in ('street', 'circuit', 'rbt'): continue
        hw = r['w'] / 2; g_ = ~(r['bridge'] | r['tunnel'] | r['junction'])
        for i in np.where(g_)[0]:
            for _ in range(2): o = rng.choice([-1, 1]) * (hw + 5.5 + rng.uniform(0, 15)); q = r['xy'][i] + r['left'][i] * o + r['tan'][i] * rng.uniform(-2.5, 2.5); pts.append((q[0], q[1]))
    P = np.array(pts); B = K.biomes(P[:, 0], P[:, 1]); m, h, sl = ok(P); d, i = G['tree'].query(P); m &= (d > hwv[i] + 4.5) & (sl < 0.5) & (B['city'] < 0.3) & (B['desert'] < 0.4) & (B['circuit'] < 0.3) & (h < 125); nf = nc = 0
    for k in np.where(m)[0]:
        u = rng.random()
        if B['forest'][k] > 0.4:
            if u < 0.22: v = rng.uniform(.75, 1); inst.append((('spruce', 'spruce_b', 'birch')[k % 3], P[k, 0], P[k, 1], h[k] - 0.1, rng.uniform(0.22, 0.45), v, v, v)); nf += 1
            elif u < 0.6: inst.append(('bush', P[k, 0], P[k, 1], h[k] - 0.05, rng.uniform(0.6, 1.2), 0.6, 0.8, 0.5)); nf += 1
            elif u < 0.8: inst.append(('grass_tall', P[k, 0], P[k, 1], h[k], rng.uniform(0.8, 1.3), 0.5, 0.85, 0.4)); nf += 1
        elif u < 0.45: inst.append((('flowers_red', 'flowers_white', 'flowers_violet', 'grass_tall', 'grass')[k % 5], P[k, 0], P[k, 1], h[k], rng.uniform(0.9, 1.5), 1, 1, 0.85)); nc += 1
    STAT['road_edge_forest'] = nf; STAT['road_edge_country'] = nc


def shade_map(C, out):
    """Ground shade map (2048 px across the island): soft shade round buildings and under trees, for the terrain materials."""
    from PIL import Image, ImageDraw, ImageFilter
    W_ = 2048; Hh = int(W_ * (K.Y1 - K.Y0) / (K.X1 - K.X0)); im = Image.new('L', (W_, Hh), 255); d = ImageDraw.Draw(im); s = W_ / (K.X1 - K.X0)
    def px(x, y): return ((x - K.X0) * s, (K.Y1 - y) * s)
    F = json.load(open(os.path.join(out, 'flora.json')))
    for sp, a in F['instances'].items():
        spec = F['species'][sp]
        if spec['card'] < 0: continue
        A = np.array(a).reshape(-1, 8)
        for x, _, z, sc in A[:, :4]: r = max(1.2, sc * spec['height'] * 0.2 * s); cx, cy = px(x, -z); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=205)
    for o in C.obst:
        x, y = o[0], -o[1]; c, sn = math.cos(o[4]), math.sin(o[4]); hx, hy = o[2] + 1.2, o[3] + 1.2
        d.polygon([px(x + a * c - b * sn, y + a * sn + b * c) for a, b in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))], fill=120)
    im = im.filter(ImageFilter.GaussianBlur(1.6)); im.save(os.path.join(out, 'ground_shade.png')); STAT['shade_map_px'] = [W_, Hh]
    L.STATS['stage11'] = dict(STAT)


def street_detail_atlas(N=512):
    """2 x 2 atlas: damp gutter streak, cast-iron drain grate, pavement stain, chewing-gum and grit speckle."""
    r_ = np.random.default_rng(31); A = np.zeros((N, N, 4)); h = N // 2
    # gutter (top-left): dark damp band, strongest at the kerb edge (v = 1), streaky along the length
    u = np.linspace(0, 1, h)[None, :]; v = np.linspace(0, 1, h)[:, None]
    streak = np.cumsum(r_.normal(0, 1, (h, h)), 1); streak = (streak - streak.min(1, keepdims=True)) / (np.ptp(streak, 1, keepdims=True) + 1e-6)
    a = np.clip(v ** 2.2 * 0.85 + 0.15 * streak * v, 0, 1) * (0.75 + 0.25 * r_.random((h, h))) * np.clip(np.minimum(u, 1 - u) * 12, 0, 1)
    A[h:, :h, :3] = (0.035, 0.034, 0.03); A[h:, :h, 3] = a * 0.8
    # drain grate (top-right): frame with slots
    g = np.zeros((h, h, 4)); g[..., :3] = 0.07; g[..., 3] = 1.0
    yy, xx = np.mgrid[0:h, 0:h] / h
    inner = (xx > 0.08) & (xx < 0.92) & (yy > 0.12) & (yy < 0.88); slot = inner & (np.sin(xx * np.pi * 18) > 0.1)
    g[slot, :3] = 0.008; g[inner & ~slot, :3] = 0.11
    g[..., :3] *= (0.85 + 0.3 * r_.random((h, h)))[..., None]; g[..., 0] *= 1.08                     # a little rust
    A[h:, h:] = g
    # pavement stain (bottom-left): soft irregular blot
    from PIL import Image, ImageDraw, ImageFilter
    im = Image.new('L', (h, h), 0); d = ImageDraw.Draw(im)
    for k in range(12): x, y, rr = r_.uniform(60, h - 60), r_.uniform(60, h - 60), r_.uniform(15, 55); d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=int(r_.uniform(90, 200)))
    s = np.asarray(im.filter(ImageFilter.GaussianBlur(14)), float) / 255.0
    A[:h, :h, :3] = (0.09, 0.085, 0.075); A[:h, :h, 3] = np.clip(s * 1.1, 0, 0.7)
    # gum and grit (bottom-right): small dark dots
    gg = np.zeros((h, h))
    for k in range(70): x, y, rr = r_.integers(4, h - 4), r_.integers(4, h - 4), r_.uniform(1.5, 4.5); gg[max(0, int(y - rr)):int(y + rr), max(0, int(x - rr)):int(x + rr)] = r_.uniform(0.4, 0.9)
    gg = np.asarray(Image.fromarray((gg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), float) / 255.0
    A[:h, h:, :3] = (0.06, 0.06, 0.06); A[:h, h:, 3] = gg * np.clip(1 - (((xx - 0.5) ** 2 + (yy - 0.5) ** 2) * 4), 0, 1)
    return A


def street_detail(C):
    """City streets: a damp gutter line along both kerbs, cast-iron drain grates in it every 20-30 m, and stains, grit and
    chewing-gum marks on the pavements."""
    import bpy
    img = L.make_image('street_detail', street_detail_atlas()); m = bpy.data.materials.new('RoadDecalsStreet'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; nt.links.new(t.outputs['Color'], b.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], b.inputs['Alpha']); b.inputs['Roughness'].default_value = 0.45
    try: m.surface_render_method = 'BLENDED'
    except Exception: pass
    r_ = np.random.default_rng(37); D = L.Buf(); n_ = dict(gutter_m=0, drains=0, stains=0)
    cell = {'gutter': (0, 0.5), 'drain': (0.5, 0.5), 'stain': (0, 0), 'gum': (0.5, 0)}
    def quad(c, t_, lf, Lq, Wq, z, kind, flip=False):
        Vq = np.array([np.r_[c - t_ * Lq / 2 - lf * Wq / 2, z], np.r_[c + t_ * Lq / 2 - lf * Wq / 2, z], np.r_[c + t_ * Lq / 2 + lf * Wq / 2, z], np.r_[c - t_ * Lq / 2 + lf * Wq / 2, z]])
        u0, v0 = cell[kind]; Uq = np.array([(u0, v0), (u0 + 0.5, v0), (u0 + 0.5, v0 + 0.5), (u0, v0 + 0.5)]) * 0.98 + 0.005
        if flip: Uq = Uq[[3, 2, 1, 0]][:, :] * [1, 1] if False else np.array([Uq[0][0], Uq[2][1]]) * 0 + Uq[[3, 2, 1, 0]]
        Fq = np.array([(0, 1, 2), (0, 2, 3)]) if np.cross(Vq[1] - Vq[0], Vq[2] - Vq[0])[2] > 0 else np.array([(0, 2, 1), (0, 3, 2)])
        D.add((Vq, Fq), np.ones(3), solid=False, uv=Uq)
    for r in C.roads:
        if r['type'] != 'street': continue
        hw = r['w'] / 2; n = r['n']; jm = r['junction'].copy()
        for k in range(1, 4): jm[k:] |= r['junction'][:-k]; jm[:-k] |= r['junction'][k:]
        ok = ~(r['bridge'] | r['tunnel'] | jm); nxt = r_.integers(3, 6)
        for i in range(1, n - 1):
            if not ok[i]: continue
            c0 = r['xy'][i]; t_ = r['tan'][i]; lf = r['left'][i]; z = float(r['z'][i]); step = r['step']
            for sd in (-1, 1):                                                              # gutter ribbon, damp edge toward the kerb
                quad(c0 + lf * sd * (hw - 0.3), t_, lf * sd, step * 1.02, 0.6, z + 0.033, 'gutter'); n_['gutter_m'] += step
            if i >= nxt:
                sd = 1 if r_.random() < 0.5 else -1; quad(c0 + lf * sd * (hw - 0.28), t_, lf * sd, 0.8, 0.42, z + 0.036, 'drain'); n_['drains'] += 1; nxt = i + int(r_.integers(4, 7))
            if r_.random() < 0.35:                                                         # pavement marks
                sd = 1 if r_.random() < 0.5 else -1; o = hw + r_.uniform(0.9, 3.4); kind = 'stain' if r_.random() < 0.55 else 'gum'; sz = r_.uniform(0.8, 1.8) if kind == 'stain' else r_.uniform(1.2, 2.2)
                quad(c0 + lf * sd * o + t_ * r_.uniform(-2, 2), t_, lf, sz, sz * r_.uniform(0.6, 1.0), z + 0.165, kind); n_['stains'] += 1
    D.emit('RoadDecalsStreet', m, smooth=False, uv=True); STAT['street_detail'] = {k: int(v) for k, v in n_.items()}

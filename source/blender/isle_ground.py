"""Aurelia Island ground: the terrain mesh at 6 m near roads (12 m elsewhere) with small-scale relief, and the placement of
the plant library as instances (Blender face instancing; the same list is written out for the game and for Unity)."""
import math, json, os
import numpy as np
import bpy
from scipy.spatial import cKDTree
import isle_data as K
import isle_lib as L
import isle_flora as FL
from isle_data import smoothstep, fbm


def up2(A):
    """Bilinear x2 upsample of a (ny, nx[, k]) lattice to (2ny-1, 2nx-1[, k])."""
    ny, nx = A.shape[:2]; O = np.zeros((2 * ny - 1, 2 * nx - 1) + A.shape[2:], float)
    O[::2, ::2] = A; O[1::2, ::2] = (A[:-1] + A[1:]) / 2; O[:, 1::2] = (O[:, :-2:2] + O[:, 2::2]) / 2
    return O


def sample6(H6, x, y):
    c = K.CELL / 2; fx = np.clip((np.asarray(x, float) - K.X0) / c, 0, H6.shape[1] - 1.001); fy = np.clip((np.asarray(y, float) - K.Y0) / c, 0, H6.shape[0] - 1.001)
    ix = fx.astype(int); iy = fy.astype(int); u = fx - ix; v = fy - iy
    return (H6[iy, ix] * (1 - u) + H6[iy, ix + 1] * u) * (1 - v) + (H6[iy + 1, ix] * (1 - u) + H6[iy + 1, ix + 1] * u) * v


def emit_terrain(C, X, Y, H, col, cls, holes, B, slope, mats):
    TR = C.TR; NY, NX = H.shape; n2y, n2x = 2 * NY - 1, 2 * NX - 1
    H6 = up2(H); X6 = up2(X); Y6 = up2(Y); col6 = up2(col); d6 = up2(TR['dist'])
    dc = TR['dist']; cmin = np.minimum.reduce([dc[:-1, :-1], dc[:-1, 1:], dc[1:, 1:], dc[1:, :-1]]); hmax = np.maximum.reduce([H[:-1, :-1], H[:-1, 1:], H[1:, 1:], H[1:, :-1]])
    fine = (cmin < 52) & (hmax > 0.5)
    # ---- relief amplitude: none on or beside roads, flats, water edges and anything built
    a = smoothstep(17, 36, d6) * (1 - up2(B['city'])) * (1 - up2(B['circuit'])) * smoothstep(1.5, 4.5, H6)
    P = np.c_[X6.ravel(), Y6.ravel()]
    ob = [(o[0], -o[1], math.hypot(o[2], o[3]) + 5) for o in C.obst] + [(o[0], -o[1], o[2] + 5) for o in C.circ] + [(o[0], -o[1], math.hypot(o[2], o[3]) + 5) for o in C.plats] + [(q[0], q[1], q[2] + 3) for q in C.noveg if q[2] > 0]
    ob = np.array(ob); rmax = ob[:, 2].max(); tr = cKDTree(ob[:, :2]); keep = np.ones(len(P))
    near = np.where(a.ravel() > 0)[0]
    for i0 in range(0, len(near), 20000):
        idx = near[i0:i0 + 20000]; dd, ii = tr.query(P[idx], k=4)
        keep[idx] = np.min(smoothstep(0, 7, dd - ob[ii, 2]), axis=1)
    a *= keep.reshape(a.shape)
    for lx, ly, lr in K.LAKES: a *= smoothstep(lr + 8, lr + 26, np.hypot(X6 - lx, Y6 - ly))
    for RV in K.get_rivers(): a *= smoothstep(RV['hw'] + 6, RV['hw'] + 20, RV['tree'].query(P)[0].reshape(a.shape))
    a *= np.where(up2(C.FIELD.astype(float)) > 0.5, 0.3, 1.0)
    nz = fbm(X6 / 13, Y6 / 13, 3, 91) + 0.6 * fbm(X6 / 31, Y6 / 31, 2, 92)
    amp = 0.34 + 1.0 * smoothstep(0.35, 0.9, up2(slope))
    pf = np.zeros((n2y, n2x), bool); iy, ix = np.where(fine)
    for dy in (0, 1, 2):
        for dx in (0, 1, 2): pf[2 * iy + dy, 2 * ix + dx] = True
    D = a * amp * nz; D[~pf] = 0; H6 += D
    Fp = np.pad(fine, ((1, 1), (0, 0))); both = Fp[1:] & Fp[:-1]                                   # edges between a fine and a coarse cell stay straight (no cracks)
    mid = (H6[::2, :-2:2] + H6[::2, 2::2]) / 2; H6[::2, 1::2] = np.where(both, H6[::2, 1::2], mid)
    Fp = np.pad(fine, ((0, 0), (1, 1))); both = Fp[:, 1:] & Fp[:, :-1]
    mid = (H6[:-2:2, ::2] + H6[2::2, ::2]) / 2; H6[1::2, ::2] = np.where(both, H6[1::2, ::2], mid)
    cen = (H6[:-2:2, :-2:2] + H6[:-2:2, 2::2] + H6[2::2, 2::2] + H6[2::2, :-2:2]) / 4; H6[1::2, 1::2] = np.where(fine, H6[1::2, 1::2], cen)
    # ---- mesh
    col6 = col6 * (0.93 + 0.14 * fbm(X6 / 8, Y6 / 8, 2, 49))[..., None]
    Vt = np.c_[X6.ravel(), Y6.ravel(), H6.ravel()]
    cy, cx = np.mgrid[0:NY - 1, 0:NX - 1]; keepc = hmax > K.SEA_FLOOR + 0.05
    if holes:
        hp = np.array(holes); cc = np.c_[(X[:-1, :-1] + X[1:, 1:]).ravel() / 2, (Y[:-1, :-1] + Y[1:, 1:]).ravel() / 2]
        dd, ii = cKDTree(hp[:, :2]).query(cc); keepc &= ~(dd < hp[ii, 2]).reshape(keepc.shape)
    cl = cls.reshape(NY, NX)[:-1, :-1]
    def quads(r0, c0, st, m):
        a_ = (r0 * n2x + c0)[m]; b_ = a_ + st; c_ = a_ + st * n2x + st; d_ = a_ + st * n2x
        return np.vstack([np.c_[a_, b_, c_], np.c_[a_, c_, d_]]), np.concatenate([cl[m], cl[m]])
    Fs = []; Ks = []
    f_, k_ = quads(2 * cy, 2 * cx, 2, keepc & ~fine); Fs.append(f_); Ks.append(k_)
    for dy in (0, 1):
        for dx in (0, 1): f_, k_ = quads(2 * cy + dy, 2 * cx + dx, 1, keepc & fine); Fs.append(f_); Ks.append(k_)
    Ft = np.vstack(Fs); fc = np.concatenate(Ks); colr = col6.reshape(-1, 3)
    ct_, st_ = math.cos(0.35), math.sin(0.35); UVf = np.c_[Vt[:, 0] * ct_ + Vt[:, 1] * st_, -Vt[:, 0] * st_ + Vt[:, 1] * ct_] / 5.0       # crop rows follow the field strips
    for k_, (nm_, mt_, sc_) in enumerate((('Terrain', mats.ter, 4.5), ('TerrainRock', mats.rock, 11.0), ('TerrainSand', mats.sand, 5.5), ('TerrainSnow', mats.snow, 7.0), ('TerrainForest', mats.forest, 4.0), ('TerrainField', mats.field, 0), ('TerrainPave', mats.pave, 3.0))):
        if (fc == k_).any(): L.make_chunked(nm_, Vt, Ft[fc == k_], colr, UVf if sc_ == 0 else Vt[:, :2] / sc_, mt_)
    # soft borders: where a face touches ground of another kind, that kind is laid over it and fades out across the face (weight in UVBlend.x)
    cv = np.repeat(np.repeat(cls.reshape(NY, NX), 2, 0), 2, 1)[:n2y, :n2x].ravel(); Vb = Vt + np.array([0, 0, 0.03]); nb_ = 0
    kinds = (('Grass', mats.ter, 4.5), ('Rock', mats.rock, 11.0), ('Sand', mats.sand, 5.5), ('Snow', mats.snow, 7.0), ('Forest', mats.forest, 4.0), ('Field', mats.field, 0), ('Pave', mats.pave, 3.0))
    for B_, (nm_, mt_, sc_) in enumerate(kinds):
        hit = (fc != B_) & ((cv[Ft[:, 0]] == B_) | (cv[Ft[:, 1]] == B_) | (cv[Ft[:, 2]] == B_))
        if hit.any(): L.make_chunked('TerrainBlend_' + nm_, Vb, Ft[hit], colr, UVf if sc_ == 0 else Vt[:, :2] / sc_, mats.blend[B_], uv2=np.c_[(cv == B_).astype(float), np.zeros(len(cv))]); nb_ += int(hit.sum())
    L.STATS['terrain_blend_faces'] = nb_
    L.STATS['terrain_fine_cells'] = int((keepc & fine).sum()); L.STATS['terrain_relief_max_m'] = round(float(np.abs(D).max()), 2)
    TR['H6'] = H6
    return H6


def place_flora(C, H6, out):
    """Build the plant library and place every plant as an instance. Returns the list written to flora.json."""
    M = C.M; TR = C.TR; r = np.random.default_rng(9)
    lib = FL.build_library(dict(bark=M.bark, leaf=M.leaf, painted=M.pflora, rock=M.rockf))
    import isle_props as KP, isle_houses as HS, isle_sheds as SH, isle_life as LF; HS.register(); SH.register(); LF.register()    # modelled street furniture and houses, placed as instances like the plants
    import isle_landmarks as LMK_; KP.PROPS['container'] = (LMK_.container, {})
    import isle_props_hq as HQ, isle_country_hq as CQ, isle_coast_hq as CO, isle_wild_hq as WH; HQ.register(); CQ.register(); CO.register(); WH.register(); import isle_roads_hq as RQ_; RQ_.register_kit(); L.STATS['kit_swapped_hq'] = HQ.apply(KP.KIT)                        # art sheet 03 street furniture in the old town
    KP.PROPS.pop('fountain', None); KP.KIT[:] = [it if it[0] != 'fountain' else ('planter',) + tuple(it[1:]) for it in KP.KIT]   # fountains exist only in the heritage family
    KP.PREFIX = 'FLORA_prop_'; plib = KP.build(); KP.PREFIX = 'PROP_'
    for k, e in plib.items(): e['kind'] = 'prop'; lib['prop_' + k] = e
    KP.bake_ao([e['lod%d' % l] for e in plib.values() for l in (0, 1)], out)                          # contact shadows and crevice darkening baked into every prop
    rows = {k: [] for k in lib}
    for it in KP.KIT:
        nm, x, y, z, yaw = it[:5]; tc = it[5] if len(it) > 5 else (1.0, 1.0, 1.0)
        rows['prop_' + nm].append((x, y, z, 1.0, yaw % 6.283185, 0.91 * tc[0], 0.91 * tc[1], 0.91 * tc[2]))
    L.STATS['kit_props'] = {k: len(v) for k, v in rows.items() if k.startswith('prop_') and v}

    def zfix(x, y, z): return float(sample6(H6, x, y) + (z - K.sample_h(TR, x, y)))
    for i, c in enumerate(C.cards):
        cell = int(c[5]); ch = FL.CARD_SPECIES[cell]; sp = ch[(i * 7 + int(c[0])) % len(ch)]
        if cell == 2 and c[3] < 6.6: sp = 'fruit'
        elif cell == 2 and abs(c[0]) < 720 and -360 < c[1] < 360: sp = ('plane', 'plane_b')[i % 2]                  # art sheet 04: plane trees in the city
        rows[sp].append((c[0], c[1], c[2] + 0.22, c[3] / lib[sp]['h'], r.uniform(0, 6.283), c[8], c[9], c[10]))
    for i_, it in enumerate(C.inst):
        sp, x, y, z, s = it[:5]
        if sp == 'bush' and it[6] > 0:                                                  # art sheet 04: forest undergrowth -> ferns, garden shrubs -> some oleander
            rr_, bb_ = it[5] / it[6], it[7] / it[6]
            if abs(rr_ - 0.8) < 0.02 and abs(bb_ - 0.65) < 0.02: sp = 'fern'; s = s * 1.1
            elif abs(rr_ - 0.9) < 0.02 and abs(bb_ - 0.72) < 0.02 and s < 1.0 and i_ % 2 == 0: sp = 'oleander'; s = s * 0.9
        rows[sp].append((x, y, zfix(x, y, z), s, r.uniform(0, 6.283), it[5], it[6], it[7]))
    for g in C.grass:
        tall = g[5] > 0.5; u = r.random(); sp = 'grass_tall' if tall else ('grass' if u < 0.86 else ('flowers_red', 'flowers_white', 'flowers_violet')[int(u * 100) % 3])
        rows[sp].append((g[0], g[1], g[2] + 0.1, g[3] / (1.3 if tall else 0.7), r.uniform(0, 6.283), g[6], g[7], g[8]))
    rt = C.G['tree']; rhw = np.concatenate([np.full(q['n'], q['w'] / 2) for q in C.roads]); dropped = 0
    for sp in rows:                                              # nothing on a carriageway; small plants sit on the ground
        if not rows[sp] or sp.startswith('prop_'): continue
        A = np.array(rows[sp], float); small = sp.startswith(('grass', 'flowers')); d, i = rt.query(A[:, :2]); ok = d > rhw[i] + (1.6 if not small else 0.5)
        if small: A[:, 2] = sample6(H6, A[:, 0], A[:, 1]) + 0.02
        dropped += int((~ok).sum()); rows[sp] = [tuple(v) for v in A[ok]]
    L.STATS['flora_removed_from_roads'] = dropped
    sc = bpy.context.scene; data = {}; tot0 = tot1 = 0
    for sp, rr in rows.items():
        e = lib[sp]; e['lod1'].hide_render = True
        if not rr: e['lod0'].hide_render = True; continue
        A = np.array(rr, float); n = len(A); cs, sn = np.cos(A[:, 4]), np.sin(A[:, 4]); V = np.empty((n, 4, 3))
        for k, (a, b) in enumerate(((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5))):
            V[:, k, 0] = A[:, 0] + (a * cs - b * sn) * A[:, 3]; V[:, k, 1] = A[:, 1] + (a * sn + b * cs) * A[:, 3]; V[:, k, 2] = A[:, 2]
        me = bpy.data.meshes.new('INST_' + sp); me.vertices.add(n * 4); me.vertices.foreach_set('co', V.astype(np.float32).ravel())
        me.loops.add(n * 4); me.loops.foreach_set('vertex_index', np.arange(n * 4, dtype=np.int32)); me.polygons.add(n)
        me.polygons.foreach_set('loop_start', np.arange(n, dtype=np.int32) * 4); me.polygons.foreach_set('loop_total', np.full(n, 4, np.int32)); me.update(calc_edges=True)
        ob = bpy.data.objects.new('INST_' + sp, me); sc.collection.objects.link(ob); ob.parent = L.ROOT
        ob.instance_type = 'FACES'; ob.use_instance_faces_scale = True; ob.instance_faces_scale = 1.0; ob.show_instancer_for_render = False; ob.show_instancer_for_viewport = False
        e['lod0'].parent = ob
        data[sp] = np.round(np.c_[A[:, 0], A[:, 2], -A[:, 1], A[:, 3], A[:, 4], A[:, 5:8]], 2).ravel().tolist(); tot0 += n * e['t0']; tot1 += n * e['t1']
        L.STATS.setdefault('flora_instances', {})[sp] = n
    L.STATS['flora_triangles_if_all_LOD0'] = tot0; L.STATS['flora_triangles_if_all_LOD1'] = tot1
    card = {s: c for c, ss in FL.CARD_SPECIES.items() for s in ss}; card['fruit'] = 2; card['plane'] = card['plane_b'] = 2
    spec = {sp: dict(height=e['h'], kind=e['kind'], tris_lod0=e['t0'], tris_lod1=e['t1'], card=card.get(sp, -1)) for sp, e in lib.items() if sp in data}
    json.dump(dict(note='Plant instances. Axes as in glTF / Unity: x, y up, z = -Blender y. Per instance: x, y, z, uniform scale, yaw (radians, about y), tint r, g, b. '
                        'Meshes: aurelia_flora.glb / .fbx, objects FLORA_<species>_LOD0 and _LOD1. card = cell in tex_tree_atlas.png for the far impostor (-1: none).',
                   stride=8, species=spec, instances=data), open(os.path.join(out, 'flora.json'), 'w'), separators=(',', ':'))
    C.flora = lib
    return lib

import os
"""Aurelia Island: builds the whole map in Blender, saves .blend, exports GLB + game data.
Run:  python3 isle_build.py -- <outdir>"""
import bpy, sys, os, json, math, types
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import isle_data as K
import isle_lib as L
from isle_lib import lin, box, beam, cyl, cone, tube, sphere, roof, lathe, Buf, compact, make_obj, make_chunked, fft_noise, make_image, new_mat
from isle_data import smoothstep, fbm

OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'out'
os.makedirs(OUT, exist_ok=True); L.OUT = OUT
rng = L.rng


def facade_photo():
    """Far-building facade, 4 bays x 2 floors (1024 x 512): plaster photo wall, recessed windows with shadowed reveals,
    stone sills and lintels, glass reflecting the sky, and a different curtain, blind or open window in each opening."""
    from PIL import Image
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'tex_kit_Plaster001.png')
    st_ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'tex_kit_Concrete044A.png')
    wall = np.asarray(Image.open(src).convert('RGB').resize((1024, 1024)), float)[:512] / 255.0
    stone = np.asarray(Image.open(st_).convert('RGB').resize((1024, 512)), float) / 255.0
    wall = wall / wall.mean((0, 1)) * 0.86; wall = np.clip(wall, 0, 1)                           # neutral light plaster so the building tint shows through
    stone = np.clip(stone / stone.mean((0, 1)) * 0.78, 0, 1)
    A = wall.copy(); r_ = np.random.default_rng(77); B = 256
    for fl in range(2):
        for by in range(4):
            x0, y0 = by * B, fl * B                                                                # image rows top-down
            wx0, wx1, wy0, wy1 = x0 + 62, x0 + 194, y0 + 52, y0 + 206
            A[wy0 - 14:wy0, wx0 - 10:wx1 + 10] = stone[wy0 - 14:wy0, wx0 - 10:wx1 + 10]             # lintel
            A[wy1:wy1 + 12, wx0 - 12:wx1 + 12] = stone[wy1:wy1 + 12, wx0 - 12:wx1 + 12] * 1.05     # sill
            A[wy1 + 12:wy1 + 16, wx0 - 10:wx1 + 10] *= 0.6                                         # shadow under the sill
            h_ = wy1 - wy0; g = np.linspace(0, 1, h_)[:, None]
            sky = np.stack([0.30 - 0.14 * g, 0.36 - 0.16 * g, 0.44 - 0.18 * g], -1) * np.ones((1, wx1 - wx0, 1))
            sky *= (0.9 + 0.2 * r_.random((1, wx1 - wx0, 1)))
            kind = r_.integers(4)
            if kind == 1:                                                                           # curtains drawn at the sides
                cw = int(r_.uniform(18, 40)); cc = np.array([0.55, 0.5, 0.42]) * r_.uniform(0.5, 0.8)
                fold = 0.85 + 0.15 * np.sin(np.arange(cw) * 0.9)[None, :, None]
                sky[:, :cw] = cc * fold * 0.6; sky[:, -cw:] = cc * fold[:, ::-1] * 0.6
            elif kind == 2:                                                                         # venetian blind part way down
                bh = int(h_ * r_.uniform(0.3, 0.8)); slats = 0.36 + 0.06 * (np.arange(bh) % 6 < 3)[:, None, None]
                sky[:bh] = slats * np.array([1.0, 0.98, 0.92])
            elif kind == 3:                                                                         # dark room behind open glass
                sky *= 0.55
            A[wy0:wy1, wx0:wx1] = sky
            A[wy0:wy0 + 8, wx0:wx1] *= 0.45; A[wy0:wy1, wx0:wx0 + 6] *= 0.55                        # reveal shadows (top and left)
            fc = np.array([0.82, 0.82, 0.8]) if (by + fl) % 3 else np.array([0.22, 0.22, 0.23])    # frames: white or dark
            mx = (wx0 + wx1) // 2; A[wy0:wy1, mx - 3:mx + 3] = fc; A[wy0 + 56:wy0 + 61, wx0:wx1] = fc
            A[wy0:wy0 + 4, wx0:wx1] = fc * 0.9; A[wy1 - 4:wy1, wx0:wx1] = fc * 0.9; A[wy0:wy1, wx0:wx0 + 4] = fc * 0.9; A[wy0:wy1, wx1 - 4:wx1] = fc * 0.9
        A[y0 + 236:y0 + 244] = stone[y0 + 236:y0 + 244, :1024 % 512 or 512].repeat(2, 1)[:, :1024] * 0.95 if False else A[y0 + 236:y0 + 244] * 0.9   # faint floor band
    A = np.clip(A, 0, 1)
    return A[::-1].copy()


def dilate(m, r):
    out = m.copy()
    for k in range(1, r + 1): out |= np.roll(m, k) | np.roll(m, -k)
    return out


def rib(r, prof, mask=None):
    """Ribbon along road r. prof: [(offset_left, dz), ...] ordered right -> left for an up-facing strip."""
    n = r['n']; idx = (np.arange(n + 1) % n) if r['closed'] else np.arange(n); m = len(idx); k = len(prof)
    V = np.empty((m, k, 3)); UV = np.empty((m, k, 2)); s = np.arange(m) * r['step']
    for j, (off, dz) in enumerate(prof):
        V[:, j, :2] = r['xy'][idx] + r['left'][idx] * off; V[:, j, 2] = r['z'][idx] + dz
        UV[:, j, 0] = off / 8.0; UV[:, j, 1] = s / 8.0
    seg = np.arange(m - 1)
    if mask is not None: seg = seg[mask[idx[seg]]]
    F = []
    for j in range(k - 1):
        a = seg * k + j; b = (seg + 1) * k + j
        F.append(np.c_[a, b, b + 1]); F.append(np.c_[a, b + 1, a + 1])
    return V.reshape(-1, 3), (np.vstack(F) if len(seg) else np.zeros((0, 3), int)), UV.reshape(-1, 2)


def P(r, i, off=0.0, dz=0.0):
    i = i % r['n'] if r['closed'] else int(np.clip(i, 0, r['n'] - 1))
    return np.array([r['xy'][i, 0] + r['left'][i, 0] * off, r['xy'][i, 1] + r['left'][i, 1] * off, r['z'][i] + dz])


def textures():
    T = {}
    g = 0.21 + 0.11 * (fft_noise(512, 0.6, 1) - 0.5) + 0.05 * (fft_noise(512, 1.8, 2) - 0.5)
    g = g - 0.045 * (fft_noise(512, 2.3, 19) > 0.66) + 0.03 * (fft_noise(512, 2.3, 20) > 0.72); g[np.abs(fft_noise(512, 1.7, 21) - 0.5) < 0.005] -= 0.08
    T['asphalt'] = make_image('asphalt', np.repeat(g[..., None], 3, 2) * (1.0, 1.0, 1.04))
    d = 0.86 + 0.24 * (fft_noise(512, 1.5, 5) - 0.5) + 0.22 * (fft_noise(512, 0.45, 6) - 0.5) + 0.10 * (fft_noise(512, 0.05, 9) - 0.5)
    gt = 0.84 + 0.30 * (fft_noise(512, 0.15, 61) - 0.5) + 0.26 * (fft_noise(512, 0.9, 62) - 0.5) + 0.2 * (fft_noise(512, 1.7, 63) - 0.5)
    dry = np.clip((fft_noise(512, 1.9, 64) - 0.55) * 5, 0, 1); dk = np.clip((fft_noise(512, 2.2, 65) - 0.62) * 6, 0, 1)
    d = np.clip(gt * (1 - 0.06 * dk), 0, 1.2)
    pass
    k = np.zeros((128, 64, 3)); k[:64] = (0.78, 0.07, 0.06); k[64:] = (0.9, 0.9, 0.88)
    T['kerb'] = make_image('kerb', k * (0.9 + 0.2 * fft_noise(128, 1.0, 7)[:, :64, None]))
    yy, xx = np.mgrid[0:64, 0:512]
    ch = (((xx // 32) + (yy // 32)) % 2).astype(float) * 0.86 + 0.05
    T['checker'] = make_image('checker', np.repeat(ch[..., None], 3, 2))
    # facade A: punched windows, one bay x one floor per tile (two windows)
    fa = np.ones((128, 128, 3)) * 0.93
    fa *= (0.96 + 0.08 * fft_noise(128, 1.2, 8))[..., None]
    for x0 in (12, 76):
        fa[30:98, x0:x0 + 40] = (0.20, 0.27, 0.36); fa[30:98, x0 + 19:x0 + 21] = (0.55, 0.57, 0.6)
        fa[96:101, x0 - 3:x0 + 43] = 0.70; fa[62:64, x0:x0 + 40] = (0.5, 0.52, 0.55)
    fa[:4] = 0.78
    try: fa = facade_photo()                                                                    # photo-based far facade: 4 bays x 2 floors
    except Exception as e: print('facade photo failed', e)
    T['facadeA'] = make_image('facade_windows', fa)
    # facade B: glass curtain wall
    fb = np.ones((128, 128, 3)) * (0.50, 0.62, 0.74)
    fb *= (0.85 + 0.3 * fft_noise(128, 2.0, 9))[..., None]
    fb[:26] = fb[:26] * 0.62
    for x0 in (0, 64): fb[:, x0:x0 + 3] = 0.86
    fb[24:27] = 0.86; fb[125:] = 0.86
    T['facadeB'] = make_image('facade_glass', fb)
    import isle_tex as TX
    for nm_, fn_, st_ in (('detail', TX.grass, 3.5), ('forest', TX.forest, 4.0), ('field', TX.field, 4.5), ('pave', TX.pave, 2.5)):
        rgb_, hh_ = fn_(); T[nm_] = make_image('ground_' + nm_, rgb_); T[nm_ + '_n'] = L.nmap('ground_' + nm_ + '_n', hh_, st_)
    T['asphalt_n'] = L.nmap('asphalt_n', g, 9.0)
    import isle_trees as TRS, isle_stage3 as S3
    src_ = os.path.join(OUT, 'tree_atlas_src.npy')                     # impostors rendered from the modelled trees (flora_impostors.py)
    T['trees'] = make_image('tree_atlas', np.load(src_).astype(float) if os.path.exists(src_) else TRS.atlas()); T['grass'] = make_image('grass_atlas', S3.grass_atlas())
    rk = 0.84 + 0.26 * (fft_noise(512, 1.3, 31) - 0.5) + 0.16 * (fft_noise(512, 0.5, 32) - 0.5); rk[np.abs(fft_noise(512, 1.9, 33) - 0.5) < 0.012] -= 0.3
    vv = (np.arange(512) / 512)[:, None]; sd = 0.9 + 0.07 * np.sin(2 * np.pi * (18 * vv + 2.5 * fft_noise(512, 1.6, 34))) + 0.08 * (fft_noise(512, 0.6, 35) - 0.5)
    sn = 0.95 + 0.07 * (fft_noise(512, 1.4, 36) - 0.5)
    for nm_, arr, st in (('snow', sn, 4.0),):
        T[nm_] = make_image('ground_' + nm_, np.repeat(np.clip(arr, 0, 1)[..., None], 3, 2)); T[nm_ + '_n'] = L.nmap('ground_' + nm_ + '_n', arr, st)
    for nm_, fn_, st_ in (('rock', TX.rock, 7.0), ('sand', TX.sand, 3.0)):
        rgb_, hh_ = fn_(); T[nm_] = make_image('ground_' + nm_, rgb_); T[nm_ + '_n'] = L.nmap('ground_' + nm_ + '_n', hh_, st_)
    T['facadeA_n'] = L.nmap('facadeA_n', fa.mean(2), 2.2); T['facadeB_n'] = L.nmap('facadeB_n', fb.mean(2), 1.6)
    def orm(name, rough, metal): return make_image(name, np.dstack([np.ones_like(rough), np.clip(rough, 0.04, 1), np.clip(metal, 0, 1)]), raw=True)
    T['asphalt_orm'] = orm('asphalt_orm', 0.86 + 0.16 * (fft_noise(512, 0.8, 41) - 0.5) - 0.07 * (fft_noise(512, 2.3, 19) > 0.66), np.zeros((512, 512)))
    wa = fa.mean(2) < 0.45; T['facadeA_orm'] = orm('facadeA_orm', np.where(wa, 0.1, 0.86), np.where(wa, 0.55, 0.0))
    gb = fb.mean(2) < 0.8; T['facadeB_orm'] = orm('facadeB_orm', np.where(gb, 0.07, 0.45), np.where(gb, 0.8, 0.9))
    wf = np.ones((256, 64, 3)) * (0.62, 0.80, 0.92)
    st = fft_noise(256, 1.4, 11)[:, :64]; st = np.clip((st - 0.35) * 2.2, 0, 1)
    col = (fft_noise(64, 0.8, 12)[:1, :] > 0.45).astype(float) * 0.5 + 0.5
    wf = wf * (1 - (st * col)[..., None]) + (st * col)[..., None]
    T['waterfall'] = make_image('waterfall', wf)
    import isle_photo as PH; PH.images(T, ('asphalt', 'detail', 'forest', 'field', 'rock', 'sand', 'snow', 'pave', 'gravel', 'boulder', 'bark'))
    return T


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    L.ROOT = bpy.data.objects.new('AureliaIsland', None); scn.collection.objects.link(L.ROOT)
    roads, G = K.build_roads(); TR = K.build_terrain(roads, G)
    T = textures()
    M = types.SimpleNamespace(
        ter=new_mat('Terrain', 0.95, image=T['detail'], vcol=True, normal=T['detail_n'], nstrength=0.6), road=new_mat('Asphalt', 0.8, image=T['asphalt'], vcol=True, normal=T['asphalt_n'], orm=T['asphalt_orm']),
        kerb=new_mat('Kerb', 0.7, image=T['kerb']), chk=new_mat('Checker', 0.7, image=T['checker']),
        vc=new_mat('Painted', 0.75, vcol=True), pt=None, fol=new_mat('Foliage', 0.9, vcol=True, double=True),
        fa=new_mat('FacadeWindows', 0.6, image=T['facadeA'], vcol=True, normal=T['facadeA_n'], orm=T['facadeA_orm']), fb=new_mat('FacadeGlass', 0.22, metal=0.35, image=T['facadeB'], vcol=True, normal=T['facadeB_n'], orm=T['facadeB_orm']),
        water=new_mat('Water', 0.06, color=lin('#1c6c88'), alpha=0.86), bed=new_mat('Seabed', 1.0, color=lin('#0c3848')),
        cards=new_mat('TreeCards', 0.9, image=T['trees'], vcol=True, double=True, cutout=True), grass=new_mat('GrassCards', 0.95, image=T['grass'], vcol=True, double=True, cutout=True),
        rock=new_mat('TerrainRock', 0.9, image=T['rock'], vcol=True, normal=T['rock_n']), sand=new_mat('TerrainSand', 0.97, image=T['sand'], vcol=True, normal=T['sand_n'], nstrength=0.7),
        snow=new_mat('TerrainSnow', 0.6, image=T['snow'], vcol=True, normal=T['snow_n'], nstrength=0.5), fall=new_mat('Waterfall', 0.3, image=T['waterfall'], alpha=0.93, double=True), mark=new_mat('Markings', 0.6, vcol=True))
    import isle_arch as AR, isle_flora as FL, isle_ground as GR
    import isle_tex as TX; g_, gh_ = TX.grunge(); M.pt = new_mat('PaintedSurface', 0.78, image=make_image('painted_grunge', g_), vcol=True, normal=L.nmap('painted_grunge_n', gh_, 4.0), nstrength=0.6)
    M.forest = new_mat('TerrainForest', 0.97, image=T['forest'], vcol=True, normal=T['forest_n'], nstrength=0.7); M.field = new_mat('TerrainField', 0.96, image=T['field'], vcol=True, normal=T['field_n'], nstrength=0.8)
    M.blend = []
    M.pave = new_mat('TerrainPave', 0.85, image=T['pave'], vcol=True, normal=T['pave_n'], nstrength=0.6); C_PV = Buf()
    AR.P.clear(); AR.materials(M)
    bh = FL.bark_height(); M.bark = new_mat('Bark', 0.9, image=T['bark'] if 'bark' in T else make_image('bark', np.repeat(bh[..., None], 3, 2) * 0.9 + 0.1), vcol=True, normal=T['bark_n'] if 'bark_n' in T else L.nmap('bark_n', bh, 5.0))
    M.leaf = new_mat('Leaves', 1.0, image=make_image('leaf_atlas', FL.leaf_atlas()), vcol=True, double=True, cutout=True); M.pflora = new_mat('PaintedFlora', 0.85, vcol=True, double=True)
    import isle_tex as TX; rgb_, hh_ = TX.boulder(); M.rockf = new_mat('Boulders', 0.92, image=T['boulder'] if 'boulder' in T else make_image('boulder', rgb_), vcol=True, normal=T['boulder_n'] if 'boulder_n' in T else L.nmap('boulder_n', hh_, 6.0))
    for m_ in (M.bark, M.leaf, M.pflora):
        try: m_.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.1
        except Exception: pass
    for m_ in (M.ter, M.rock, M.sand, M.snow, M.forest, M.field, M.pave): b_ = m_.copy(); b_.name = 'TerrainBlend_' + m_.name; b_.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value -= 0.017; M.blend.append(b_)
    nt_ = M.water.node_tree; tc_ = nt_.nodes.new('ShaderNodeTexCoord'); nz_ = nt_.nodes.new('ShaderNodeTexNoise'); bp_ = nt_.nodes.new('ShaderNodeBump')
    nz_.inputs['Scale'].default_value = 0.09; nz_.inputs['Detail'].default_value = 6.0; bp_.inputs['Strength'].default_value = 0.18
    nt_.links.new(tc_.outputs['Object'], nz_.inputs['Vector']); nt_.links.new(nz_.outputs[0], bp_.inputs['Height']); nt_.links.new(bp_.outputs['Normal'], nt_.nodes['Principled BSDF'].inputs['Normal'])
    X, Y, H = TR['X'], TR['Y'], TR['H']
    hgt = lambda x, y: float(K.sample_h(TR, x, y))
    C = types.SimpleNamespace(roads=roads, G=G, TR=TR, M=M, hgt=hgt, S=Buf(), Sm=Buf(), FA=Buf(), FB=Buf(), V=Buf(), Rk=Buf(), Mk=Buf(),
                              obst=[], circ=[], landmarks=[], spinners=[], P=P, rib=rib, rng=rng, noveg=[], inst=[], PV=C_PV)
    S = C.S; BT = C.BT = Buf(); PR = C.PR = Buf(); C.plats = []
    import isle_stage2 as S2
    CONC = lin('#b9b6ad'); STEEL = lin('#9aa0a6'); WHITE = lin('#eeeeea'); RED = lin('#c5261f'); DARK = lin('#2b2d31')
    C.col = dict(CONC=CONC, STEEL=STEEL, WHITE=WHITE, RED=RED, DARK=DARK)

    # ------------------------------------------------ tunnels first (they punch holes in the terrain)
    holes = []; tunnels_out = []; C_PT = Buf()
    for ri, r in enumerate(roads):
        hw = r['w'] / 2
        for a, ln in K.runs(r['tunnel'], r['closed']):
            Rw = hw + 1.3; Ht = 7.0
            th = np.pi * np.arange(9) / 8
            arch = [(-Rw * math.cos(t), 0.02 + Ht * math.sin(t) ** 0.6) for t in th]
            prof = [(-hw + 0.2, 0.03)] + arch + [(hw - 0.2, 0.03)]
            mask = np.zeros(r['n'], bool); mask[np.clip(np.arange(a - 1, a + ln + 1), 0, r['n'] - 1)] = True
            Vl, Fl, _ = rib(r, prof, mask)
            kcol = np.array([lin('#55585c')] + [lin('#8d8f90'), lin('#8d8f90'), lin('#6a6c70'), lin('#3c3e42'), lin('#fff0c0'), lin('#3c3e42'), lin('#6a6c70'), lin('#8d8f90'), lin('#8d8f90')] + [lin('#55585c')])
            cl = np.tile(kcol, (len(Vl) // len(prof), 1))
            Vl, Fl, cl = compact(Vl, Fl[:, ::-1], cl); BT.add((Vl, Fl), cl, solid=False)
            tunnels_out.append([ri, int(a), int(ln)])
            for p, inward in ((a, 1), (a + ln - 1, -1)):
                p = int(np.clip(p, 2, r['n'] - 3))
                ins = [int(np.clip(p + inward * k, 0, r['n'] - 1)) for k in range(-2, 6)]
                for i in ins[2:]: holes.append((r['xy'][i, 0], r['xy'][i, 1], hw + 6.5))
                depth = max(r['nat'][i] - r['z'][i] for i in ins[2:])
                Hd = depth + 2.5; Wd = hw + 15.0; pe = int(np.clip(p - inward, 0, r['n'] - 1))
                outer = [(-Wd, -1), (-Wd, Hd * .5), (-Wd, Hd), (-Wd / 2, Hd), (0, Hd), (Wd / 2, Hd), (Wd, Hd), (Wd, Hd * .5), (Wd, -1)]
                A_ = np.array([P(r, pe, o, dz) for o, dz in arch]); O_ = np.array([P(r, pe, o, dz) for o, dz in outer])
                Vh = np.vstack([A_, O_]); i = np.arange(8)
                Fh = np.vstack([np.c_[i, i + 1, 9 + i + 1], np.c_[i, 9 + i + 1, 9 + i]])
                uvh = np.c_[Vh[:, :2] @ r['left'][pe] / 7.0, Vh[:, 2] / 7.0]; C_PT.add((Vh, Fh), lin('#a59d90'), solid=False, uv=uvh); C_PT.add((Vh, Fh[:, ::-1]), lin('#a59d90'), solid=False, uv=uvh)     # headwall faced with the rock texture
                # coping, apron in front, and a lid over the notch behind the headwall
                BT.add(beam(P(r, pe, -Wd - .5, Hd), P(r, pe, Wd + .5, Hd), 1.6, 1.0), lin('#8f8c84'))
                import isle_props as KPt; po_ = P(r, pe, 0.0, 0.0); od_ = -inward * r['tan'][pe]                          # art sheet 07: modelled stone portal
                hwk = min((5.0, 6.0, 7.0), key=lambda v: abs(v - hw)); KPt.KIT.append(('tunnel_portal_%d' % int(hwk), po_[0], po_[1], po_[2] - 0.02, math.atan2(od_[1], od_[0])))
                lv = []
                for i in ins[1:] + [int(np.clip(ins[-1] + inward, 0, r['n'] - 1))]:
                    zt = max(r['nat'][i] + 1.5, r['z'][i] + Ht + 1.5)
                    for o in (-hw - 12, hw + 12): lv.append([r['xy'][i, 0] + r['left'][i, 0] * o, r['xy'][i, 1] + r['left'][i, 1] * o, zt])
                lv = np.array(lv); m = len(lv) // 2; i = np.arange(m - 1) * 2
                Fq = np.vstack([np.c_[i, i + 2, i + 3], np.c_[i, i + 3, i + 1]])
                BT.add((lv, Fq), lin('#77756c'), solid=False); BT.add((lv, Fq[:, ::-1]), lin('#77756c'), solid=False)
                C.landmarks.append(('Tunnel' if inward == 1 else None, P(r, p)))

    # ------------------------------------------------ terrain
    B = K.biomes(X, Y)
    gy, gx = np.gradient(H, K.CELL); slope = np.hypot(gx, gy)
    nz1 = fbm(X / 260, Y / 260, 4, 40); nz2 = fbm(X / 70, Y / 70, 3, 44)
    col = lin('#5c8a3a')[None, None, :] * np.ones(H.shape + (3,))

    def blend(c, w):
        return col * (1 - w[..., None]) + lin(c) * w[..., None]
    col = blend('#7f9a45', smoothstep(-0.1, 0.35, nz1))
    col = blend('#3e6a31', smoothstep(0.05, 0.4, -nz1) * 0.8)
    col = blend('#35602f', B['forest'] * 0.75)
    rid_v = G['rid'][TR['idx']]; rtype = np.array([r['type'] for r in roads])[rid_v]; rhw = np.array([r['w'] / 2 for r in roads])[rid_v]
    solid_v = ~(G['bridge'] | G['tunnel'])[TR['idx']]
    # farmland patchwork
    th = 0.35; fu = (X * math.cos(th) + Y * math.sin(th)) / 90; fv = (-X * math.sin(th) + Y * math.cos(th)) / 60
    cell = (np.floor(fu) * 73856093 + np.floor(fv) * 19349663).astype(np.int64); hsh = ((cell * 2654435761) % 1000) / 1000.0
    edge = np.minimum(np.minimum(fu % 1, 1 - fu % 1) * 90, np.minimum(fv % 1, 1 - fv % 1) * 60)
    fm = (B['country'] > 0.45) & (slope < 0.14) & (H > 5) & (hsh > 0.22) & (TR['dist'] > 16)
    fw = fm * smoothstep(1.5, 6.0, edge)
    fcols = np.array([lin(c) for c in ('#b8a657', '#6f9a3d', '#8b6e4e', '#a9b868', '#cdb86a', '#5f8f48', '#d2c070')])
    col = col * (1 - fw[..., None]) + fcols[(hsh * 997).astype(int) % len(fcols)] * (0.9 + 0.1 * np.sin(fv * 60 / 2.2))[..., None] * fw[..., None]
    C.FIELD = fm
    col = blend('#d6b27a', B['desert'])
    col = blend('#c4875a', B['desert'] * smoothstep(52, 70, H))
    col = blend('#b56a3c', B['desert'] * smoothstep(0.3, 0.7, slope))
    col = blend('#8a8273', smoothstep(0.42, 0.72, slope + 0.08 * nz2) * (1 - B['desert']))
    col = blend('#7c7873', smoothstep(95, 150, H + 20 * nz1) * (1 - B['desert']) * 0.8)
    band = 0.5 + 0.5 * np.sin(H * 0.6 + 4 * nz2 + 2 * nz1); steep = smoothstep(0.5, 0.95, slope)
    col = col * (1 - 0.26 * band * steep * (1 - B['desert']))[..., None]
    col = blend('#e6c595', B['desert'] * steep * (band > 0.62) * 0.55); col = blend('#8f4a2c', B['desert'] * steep * (band < 0.22) * 0.5)
    snow = smoothstep(135, 172, H + 28 * nz2 + 15 * nz1) * (1 - 0.5 * smoothstep(1.1, 1.9, slope)) * (1 - B['desert'])
    col = blend('#f3f6f9', snow); C.snowline = 150.0
    col = blend('#9d9e99', B['city'] * 0.92)
    col = blend('#5fa046', B['circuit'] * 0.92)
    col = blend('#cbbd9b', (rtype == 'circuit') * smoothstep(rhw + 17, rhw + 9, TR['dist']) * 0.85)
    col = blend('#dccb9c', smoothstep(4.2, 1.6, H + 1.5 * nz2) * (1 - B['city'] * 0.7))
    vd = smoothstep(rhw + 16, rhw + 5, TR['dist']) * solid_v * (1 - B['city']) * (1 - B['circuit']) * (1 - snow * 0.6)
    col = blend('#8d7f69', vd * 0.85 * (rtype != 'dirt')); col = blend('#86694a', vd * 0.9 * (rtype == 'dirt'))
    for RV in K.get_rivers():
        rvd = RV['tree'].query(np.c_[X.ravel(), Y.ravel()])[0].reshape(X.shape); col = blend('#2d6a78', smoothstep(RV['hw'] + 1.5, RV['hw'] * 0.6, rvd) * (H > 0) * 0.85)
    for lx, ly, lr in K.LAKES:
        col = blend('#2d6a78', smoothstep(lr + 6, lr - 14, np.hypot(X - lx, Y - ly)) * 0.9)
    col = blend('#2f6d78', smoothstep(-0.5, -9, H) * 0.8)
    col *= (0.92 + 0.16 * fbm(X / 25, Y / 25, 2, 48))[..., None]
    cls = np.where(snow > 0.5, 3, np.where((slope > 0.55) | ((H > 95) & (B['desert'] < 0.5)), 1, np.where(B['city'] > 0.5, 6, np.where((B['desert'] > 0.5) | (H < 4), 2, np.where(fm, 5, np.where(B['forest'] > 0.5, 4, 0)))))).ravel()
    col = np.where((cls.reshape(H.shape) == 4)[..., None], col * 0.5 + lin('#6b5a3c') * 0.5, col)

    # ------------------------------------------------ roads
    Rd = Buf(); Dt = Buf(); Kb = Buf(); Mk = C.Mk; Rs = Buf(); import isle_props_hq as HQo
    tint = {'hwy': 1.0, 'road': 0.95, 'street': 1.08, 'circuit': 0.8, 'rbt': 1.0}
    shc = {'hwy': '#85786a', 'road': '#85786a', 'street': '#a3a29b', 'circuit': '#6aa24a', 'dirt': '#7d6a4c', 'rbt': '#a3a29b'}
    WH = lin('#eeeeea'); YL = lin('#e8b520')

    def quads(r, off, wd, i, j, color, dz=0.06):
        if not len(i): return
        n = r['n']; i = i % n; j = j % n
        def pt(k, o): return np.c_[r['xy'][k] + r['left'][k] * o, r['z'][k] + dz]
        Vq = np.stack([pt(i, off - wd / 2), pt(j, off - wd / 2), pt(j, off + wd / 2), pt(i, off + wd / 2)], 1).reshape(-1, 3)
        q = np.arange(len(i)) * 4
        Mk.add((Vq, np.vstack([np.c_[q, q + 1, q + 2], np.c_[q, q + 2, q + 3]])), color, solid=False)
    C.quads = quads
    bridges_out = []
    for ri, r in enumerate(roads):
        hw = r['w'] / 2; n = r['n']; typ = r['type']; ground = ~(r['bridge'] | r['tunnel'])
        Vr, Fr, UVr = rib(r, [(-hw, 0), (hw, 0)])
        if typ == 'dirt': Dt.add((Vr, Fr), lin('#8a6c48') * (0.9 + 0.2 * rng.random((len(Vr), 1))), solid=False, uv=Vr[:, :2] / 3.2)
        elif typ == 'street' and any(HQo.oldtown(*q) for q in r['xy'][::8]):     # art sheet 08: old-town streets in granite setts, asphalt elsewhere
            old_ = np.array([HQo.oldtown(*q) for q in r['xy']]); prof5 = [(-hw, 0), (-hw * 0.5, 0), (0, 0), (hw * 0.5, 0), (hw, 0)]
            Vr, Fr, UVr = rib(r, prof5, ~old_); cl_ = np.tile(np.array([1.07, 0.9, 1.05, 0.9, 1.07])[:, None] * tint[typ] * np.ones(3), (len(Vr) // 5, 1)); Vr, Fr, UVr, cl_ = compact(Vr, Fr, UVr, cl_); Rd.add((Vr, Fr), cl_, solid=False, uv=UVr * 2.4) if len(Fr) else None
            Vs_, Fs_, _ = rib(r, [(-hw, 0.012), (0, 0.022), (hw, 0.012)], old_); Vs_, Fs_ = compact(Vs_, Fs_)
            if len(Fs_): Rs.add((Vs_, Fs_), np.ones(3) * 0.95 * (0.92 + 0.12 * rng.random((len(Vs_), 1))), solid=False, uv=np.c_[Vs_[:, 0], Vs_[:, 1]] / 2.2)
        else:                                                   # wheel tracks a little darker than the lane centres and edges
            Vr, Fr, UVr = rib(r, [(-hw, 0), (-hw * 0.5, 0), (0, 0), (hw * 0.5, 0), (hw, 0)]); Rd.add((Vr, Fr), np.tile(np.array([1.07, 0.9, 1.05, 0.9, 1.07])[:, None] * tint[typ] * np.ones(3), (len(Vr) // 5, 1)), solid=False, uv=UVr * 2.4)
        gm = dilate(ground, 1)
        for side in (-1, 1):
            prof = [(side * hw, 0.0), (side * (hw + 4.0), -0.78)]
            if side < 0: prof = prof[::-1]
            Vs, Fs, _ = rib(r, prof, gm); Vs, Fs = compact(Vs, Fs)
            if len(Fs): Dt.add((Vs, Fs), lin(shc[typ]) * (0.9 + 0.2 * rng.random((len(Vs), 1))), solid=False, uv=Vs[:, :2] / 3.2)
        for side in (-1, 1):                                    # retaining walls where the ground beside the road is lower (switchbacks, ramps)
            q9 = r['xy'] + r['left'] * side * (hw + 9.5); z9 = K.sample_h(TR, q9[:, 0], q9[:, 1]) - 0.3; me = dilate(z9 < r['z'] - 1.1, 1) & ground     # embankment from the verge down to the natural ground
            if me.any():
                n_ = r['n']; idx_ = (np.arange(n_ + 1) % n_) if r['closed'] else np.arange(n_); Ve = np.empty((len(idx_), 2, 3))
                Ve[:, 0, :2] = r['xy'][idx_] + r['left'][idx_] * side * (hw + 3.9); Ve[:, 0, 2] = r['z'][idx_] - 0.74; Ve[:, 1, :2] = q9[idx_]; Ve[:, 1, 2] = np.minimum(z9[idx_], r['z'][idx_] - 0.8)
                sg_ = np.arange(len(idx_) - 1); sg_ = sg_[me[idx_[sg_]]]; a_ = sg_ * 2; b_ = a_ + 2
                Fe = np.vstack([np.c_[a_, b_, b_ + 1], np.c_[a_, b_ + 1, a_ + 1]]) if side < 0 else np.vstack([np.c_[a_, b_ + 1, b_], np.c_[a_, a_ + 1, b_ + 1]])
                Ve = Ve.reshape(-1, 3); Ve, Fe = compact(Ve, Fe); Dt.add((Ve, Fe), lin('#6f7a4a' if typ != 'dirt' else '#7d6a4c') * (0.85 + 0.2 * rng.random((len(Ve), 1))), solid=False, uv=Ve[:, :2] / 3.2)
                L.STATS['embankment_m'] = L.STATS.get('embankment_m', 0) + int(me.sum() * r['step'])
            q = r['xy'] + r['left'] * side * (hw + 2.2); m = dilate((r['z'] - K.sample_h(TR, q[:, 0], q[:, 1]) > 3.2), 1) & ground
            if m.any():
                o = side * (hw + 0.35); Vw, Fw, _ = rib(r, [(o, 0.28), (o, -6.5)], m); Vw, Fw = compact(Vw, Fw)
                BT.add((Vw, Fw), lin('#a7a49b'), solid=False); BT.add((Vw, Fw[:, ::-1]), lin('#a7a49b'), solid=False)
                Vc_, Fc_, _ = rib(r, [(o - 0.25, 0.28), (o + 0.25, 0.28)], m); Vc_, Fc_ = compact(Vc_, Fc_); BT.add((Vc_, Fc_), lin('#8f8c84'), solid=False)
                L.STATS['retaining_wall_m'] = L.STATS.get('retaining_wall_m', 0) + int(m.sum() * r['step'])
        # markings
        jm = dilate(r['junction'], 3); last = n if r['closed'] else n - 1
        i2 = np.arange(0, last - 1, 2); ok = ~jm[i2 % n] & ~jm[(i2 + 2) % n]
        if typ in ('hwy', 'road', 'circuit'):
            for o in (-(hw - 0.45), hw - 0.45): quads(r, o, 0.22, i2[ok], i2[ok] + 2, WH)
        if typ == 'hwy':
            quads(r, 0, 0.3, i2[ok], i2[ok] + 2, YL)
            i4 = np.arange(0, last - 2, 4); ok4 = ~jm[i4 % n]
            for o in (-3.45, 3.45): quads(r, o, 0.2, i4[ok4], i4[ok4] + 2, WH)
        if typ in ('road', 'street'):
            i3 = np.arange(1, last - 1, 3); ok3 = ~jm[i3 % n] & ~jm[(i3 + 1) % n]
            quads(r, 0, 0.2, i3[ok3], i3[ok3] + 1, WH)
        if typ == 'circuit':
            hd = np.unwrap(r['head']); curv = (np.roll(hd, -1) - np.roll(hd, 1)); curv[0] = curv[1]; curv[-1] = curv[-2]
            r['curv'] = curv / (2 * r['step'])
            km = dilate(np.abs(r['curv']) > 1 / 220, 3)
            for side in (-1, 1):
                prof = [(side * (hw - 0.1), 0.02), (side * (hw + 0.6), 0.11), (side * (hw + 1.6), 0.03)]
                if side < 0: prof = prof[::-1]
                Vk, Fk, UVk = rib(r, prof, km); UVk = np.c_[(np.abs(UVk[:, 0] * 8) - hw) / 1.7, UVk[:, 1] * 8 / 6.0]
                Vk, Fk, UVk = compact(Vk, Fk, UVk); Kb.add((Vk, Fk), np.ones(3), solid=False, uv=UVk)
        # guard rails on the drop side
        if typ in ('hwy', 'road'):
            for side in (-1, 1):
                q = r['xy'] + r['left'] * side * (hw + 24)
                drop = (r['z'] - K.sample_h(TR, q[:, 0], q[:, 1]) > 4.5)
                m = dilate(drop, 3) & ground & ~dilate(r['junction'], 5)
                if not m.any(): continue
                o = side * (hw + 2.6)
                wb = [(-.05, .20), (.02, .25), (.05, .31), (-.01, .39), (.05, .47), (.02, .53), (-.05, .60)]                   # art sheet 07: W-beam profile
                prof = [(o + side * dx, z) for dx, z in wb]
                Vg, Fg, _ = rib(r, prof if side < 0 else prof[::-1], m)
                Vg, Fg = compact(Vg, Fg); PR.add((Vg, Fg), STEEL, solid=False); PR.add((Vg, Fg[:, ::-1]), STEEL, solid=False)
                for i in np.where(m)[0][::3]:
                    p = P(r, i, o - side * 0.28); PR.add(box(p[0], p[1], p[2] - 0.7, .12, .14, 1.3, r['head'][i]), lin('#70757a'))
                    p = P(r, i, o - side * 0.14); PR.add(box(p[0], p[1], p[2] + 0.22, .16, .12, .32, r['head'][i]), lin('#1e1f21'))          # blockout
                    p = P(r, i, o + side * 0.06); PR.add(box(p[0], p[1], p[2] + 0.36, .02, .08, .06, r['head'][i]), lin('#ffb020'))           # reflector
        # bridges and viaducts
        for a, ln in K.runs(r['bridge'], r['closed']):
            e = hw + 0.7
            mask = np.zeros(n, bool); idx = np.arange(a - 2, a + ln + 2); idx = idx % n if r['closed'] else idx[(idx >= 0) & (idx < n)]; mask[idx] = True
            prof = [(-e - .4, -1.7), (-e - .4, 0.42), (-e, 0.42), (-e, -0.05), (e, -0.05), (e, 0.42), (e + .4, 0.42), (e + .4, -1.7), (-e - .4, -1.7)]
            for sd_ in (-1, 1):                                  # open steel railing on a low kerb instead of a solid parapet
                o_ = sd_ * (e + 0.2)
                for zr_ in (0.78, 1.12):
                    Vg_, Fg_, _ = rib(r, [(o_ - .04, zr_), (o_ - .04, zr_ + .07), (o_ + .04, zr_ + .07), (o_ + .04, zr_), (o_ - .04, zr_)], mask); Vg_, Fg_ = compact(Vg_, Fg_); PR.add((Vg_, Fg_), STEEL, solid=False); PR.add((Vg_, Fg_[:, ::-1]), STEEL, solid=False)
                for i_ in idx[::2]: p_ = P(r, i_, o_); PR.add(box(p_[0], p_[1], p_[2] + 0.42, .09, .09, .78, r['head'][i_ % n]), lin('#70757a'))
            stone = bool(r['river'][(a + ln // 2) % n]); STONE = lin('#8a6a48') if typ == 'dirt' else lin('#a39a8a')
            Vb, Fb, _ = rib(r, prof, mask); Vb, Fb = compact(Vb, Fb); BT.add((Vb, Fb), STONE if stone else CONC, solid=False)
            if stone:
                for e_ in (a - 1, a + ln):
                    p = P(r, e_, 0); BT.add(box(p[0], p[1], p[2] - 6.6, 6.0, r['w'] + 3.6, 6.5, r['head'][e_ % n]), lin('#8f8778'))
                C.landmarks.append(('Stone Bridge' if r['name'] == 'Farm Road' else None, P(r, a + ln // 2)))
            big = (ri == 0 and abs(r['xy'][(a + ln // 2) % n, 0] - K.CHANNEL_X) < 300 and r['xy'][(a + ln // 2) % n, 1] < -900)
            bridges_out.append([ri, int(a), int(ln)])
            if big:
                C.suspension = (r, a, ln)
            else:
                for i in idx[4::8]:
                    for o in (-hw * 0.55, hw * 0.55):
                        p = P(r, i, o); bed = float(K.base_h(p[0], p[1])) - 1.5; dq, iq = G['tree'].query([p[0], p[1]], k=6); clear = all(G['rid'][j_] == ri or d_ > 9.5 for d_, j_ in zip(dq, iq))
                        if p[2] - 1.7 - bed > 1.0 and clear: BT.add(cyl(p[0], p[1], bed, 1.3, 1.05, p[2] - 1.7 - bed, 8), CONC)
                    p = P(r, i, 0); BT.add(box(p[0], p[1], p[2] - 2.6, 2.6, r['w'] + 1.5, 0.9, r['head'][i % n]), CONC)
    import isle_stage7 as S7; S7.roads_extra(C, roads, G, Rd, Mk)
    import isle_roads_build as RB; L.STATS['roads_sheet08'] = RB.apply(C, roads, Mk, Dt, rib, dilate, rng)
    if len(Rs.F):                                                # art sheet 08: granite setts on the old-town streets
        import isle_props as KPm; Ms_ = L.new_mat('Setts', image=make_image('setts', KPm._col('PavingStones070', 0.5, 0.5, 1.0)), vcol=True, normal=make_image('setts_n', KPm._rawrect('PavingStones070', 'NormalGL')[..., :3], raw=True), nstrength=1.2,
                                                          orm=make_image('setts_orm', np.dstack([np.ones((8, 8)), np.full((8, 8), 0.82), np.zeros((8, 8))]), raw=True))
        Rs.emit('RoadSetts', Ms_, uv=True)
    Rd.emit('Road', M.road, uv=True); M.gravel = new_mat('Shoulder', 0.95, image=T['gravel'], vcol=True, normal=T.get('gravel_n'), nstrength=0.8) if 'gravel' in T else M.ter; Dt.emit('Verge', M.gravel, uv=True); Kb.emit('Kerbs', M.kerb, uv=True)

    # ------------------------------------------------ everything else
    import isle_features as Fz
    import isle_stage3 as S3
    S2.pre(C); Fz.build(C); S2.post(C); nv0 = len(C.noveg); ob0 = len(C.obst); S3.post(C); S7.city(C); S7.circuit(C); S7.scatter(C)
    import isle_stage11 as S11; S11.coast(C); S11.fountains(C); S11.roadside(C); S11.lookouts(C); S11.wild_props(C); S11.road_decals(C); S11.grass_verges(C); S11.scatter(C)
    extra = [q for q in C.noveg[nv0:] if q[2] > 0] + [(o[0], -o[1], math.hypot(o[2], o[3]) + 2) for o in C.obst[ob0:]]
    if extra:                                                   # drop trees that would stand inside things added after planting
        ex = np.array(extra); cd = np.array([c_[:2] for c_ in C.cards]); dd, ii = cKDTree(ex[:, :2]).query(cd); C.cards = [c_ for c_, d_, i_ in zip(C.cards, dd, ii) if d_ > ex[i_, 2]]
    H6 = GR.emit_terrain(C, X, Y, H, col, cls, holes, B, slope, M)
    zf = lambda x_, y_, z_: float(GR.sample6(H6, x_, y_) + (z_ - K.sample_h(TR, x_, y_)))
    C.cards = [(c_[0], c_[1], zf(*c_[:3])) + tuple(c_[3:]) for c_ in C.cards]
    for g_ in C.grass: g_[2] = zf(g_[0], g_[1], g_[2])
    TR['H12'] = TR['H']
    AR.emit(C)
    import isle_hero as HR; HR.finish_atlas()                                         # shared shop-sign texture for the hero buildings
    GR.place_flora(C, H6, OUT)
    C_PT.emit('TunnelPortal', M.rock, smooth=False, uv=True); BT.emit('Bridges', M.pt, smooth=False, boxuv=True, tile=300); PR.emit('Props', M.pt, smooth=False, boxuv=True, tile=300)
    import isle_trees as TRS; TRS.emit(C, M.cards); S3.emit_cards('GrassCards', C.grass, M.grass, 2)
    C.PV.emit('Pavement', M.pave, smooth=False, uv=True); C.S.emit('Structures', M.pt, smooth=False, boxuv=True, tile=300); C.Sm.emit('Shapes', M.vc, smooth=True, tile=300)
    C.FA.emit('Buildings', M.fa, smooth=False, uv=True); C.FB.emit('Towers', M.fb, smooth=False, uv=True)
    C.V.emit('Vegetation', M.fol); C.Rk.emit('Rocks', M.vc); C.Mk.emit('Markings', M.mark, smooth=False)

    # ------------------------------------------------ water
    def disc(name, cx, cy, zz, rad, mat, n=28):
        a = np.arange(n) * 2 * np.pi / n
        Vw = np.vstack([[[cx, cy, zz]], np.c_[cx + rad * np.cos(a), cy + rad * np.sin(a), np.full(n, zz)]])
        make_obj(name, Vw, np.array([(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]), None, None, mat)
    for nm, hf, zz, mt in (('Water', 30000, 0.0, M.water), ('Seabed', 30000, K.SEA_FLOOR - 0.5, M.bed)):
        make_obj(nm, np.array([(-hf, -hf, zz), (hf, -hf, zz), (hf, hf, zz), (-hf, hf, zz)], float), np.array([(0, 1, 2), (0, 2, 3)]), None, None, mt)
    lakes = []
    for k, (lx, ly, lr) in enumerate(K.LAKES):
        lv = K.lake_level(lx, ly); disc('Lake_%d' % k, lx, ly, lv, lr + 24, M.water); lakes.append([lx, lv, -ly, lr + 6])

    for kr, RV in enumerate(K.get_rivers()):
        rp = RV['xy']; rt = np.gradient(rp, axis=0); rt /= np.linalg.norm(rt, axis=1)[:, None]; rn = np.c_[-rt[:, 1], rt[:, 0]]; m = len(rp)
        Vr_ = np.vstack([np.c_[rp - rn * RV['hw'], RV['lvl']], np.c_[rp + rn * RV['hw'], RV['lvl']]]); i = np.arange(m - 1)
        make_obj('River' if kr == 0 else 'River_%d' % kr, Vr_, np.vstack([np.c_[i, i + 1, m + i + 1], np.c_[i, m + i + 1, m + i]]), None, None, M.water)
        for k in range(0, m, 1):
            if RV['lvl'][k] > 0.3: lakes.append([float(rp[k, 0]), float(RV['lvl'][k]), float(-rp[k, 1]), RV['hw'] - 0.5])
    json.dump(dict(note='Instancing data. Axes: glTF/Unity style x, y up, z = -blender y. Trees are two crossed quads plus a top quad; cell indexes the 4x2 tree atlas (tex_tree_atlas.png).',
                   tree_types=['pine A', 'pine B', 'broadleaf', 'snowy pine', 'birch', 'palm'], trees_format='x, y, z, height, width, atlas cell',
                   trees=[[round(float(c_[0]), 1), round(float(c_[2]), 1), round(float(-c_[1]), 1), round(float(c_[3]), 1), round(float(c_[4]), 1), int(c_[5])] for c_ in C.cards],
                   grass_format='x, y, z, height, width, cell (0 grass, 1 tall grass)', grass=[[round(float(c_[0]), 1), round(float(c_[2]), 1), round(float(-c_[1]), 1), round(float(c_[3]), 2), round(float(c_[4]), 2), int(c_[5])] for c_ in C.grass]),
              open(os.path.join(OUT, 'vegetation_instances.json'), 'w'), separators=(',', ':'))
    S11.shade_map(C, OUT)
    S2.collision(C); S2.lighting_and_cameras(C)
    # ------------------------------------------------ game data (three.js axes: x, y up, z = -blender y)
    def g3(p): return [round(float(p[0]), 2), round(float(p[2]), 2), round(float(-p[1]), 2)]
    world = dict(
        name='Aurelia Island', bounds=[K.X0, K.X1, K.Y0, K.Y1], seaFloor=K.SEA_FLOOR,
        heightmap=dict(file='height.bin', nx=int(H6.shape[1]), ny=int(H6.shape[0]), cell=K.CELL / 2, x0=K.X0, y0=K.Y0, scale=0.02,
                       note='Int16 LE, row = blender y (south to north), col = x; game z = -y'),
        roads=[dict(name=r['name'], type=r['type'], w=r['w'], closed=bool(r['closed']), step=round(float(r['step']), 4),
                    pts=np.round(np.c_[r['xy'][:, 0], r['z'], -r['xy'][:, 1]], 2).ravel().tolist(),
                    wall=(r['bridge'] | r['tunnel']).astype(int).tolist()) for r in roads],
        bridges=bridges_out, tunnels=tunnels_out, lakes=lakes,
        regions=[dict(name=nm, x=cx, z=-cy, rx=rx, rz=ry) for nm, cx, cy, rx, ry in K.REGIONS],
        obstacles=[[round(float(v), 2) for v in o] for o in C.obst], platforms=[[round(float(v), 2) for v in o] for o in C.plats], circles=[[round(float(v), 2) for v in o] for o in C.circ],
        landmarks=[dict(name=nm, pos=g3(p)) for nm, p in C.landmarks if nm], spinners=C.spinners, lamps=[[round(float(v), 1) for v in q] for q in C.lamps], walkways=getattr(C, 'walk', []),
        circuit=dict(road=[r['name'] for r in roads].index('Circuit'), start=int(C.circuit_start)), ring=0, snowline=C.snowline)
    json.dump(world, open(os.path.join(OUT, 'world.json'), 'w'), separators=(',', ':'))
    np.round(np.clip(H6, -600, 600) * 50).astype('<i2').tofile(os.path.join(OUT, 'height.bin'))
    C.cols = S2.organise(C)
    return C


def export(C):
    import isle_bake as BK; BK.bake(OUT)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(OUT, 'aurelia_island.blend')))
    allv = [o for c in C.cols[:14] for o in c.objects]; col = list(C.cols[16].objects)
    flora = [o for o in allv if o.name.startswith('FLORA_')]; blod = [o for o in allv if o.name.startswith('BuildingsLOD')]
    kit = [o for o in allv if o.name.startswith('KIT_')]; tbl = [o for o in allv if o.name.startswith('TerrainBlend')]
    skip = set(o.name for o in flora + blod + kit + tbl) | set(o.name for o in allv if o.name.startswith('INST_'))
    vis = [o for o in allv if o.name not in skip]
    def sel(objs):
        for o in bpy.data.objects: o.select_set(False)
        for o in objs: o.hide_render = False; o.select_set(True)
    fbx = dict(use_selection=True, object_types={'MESH', 'EMPTY'}, apply_scale_options='FBX_SCALE_UNITS', axis_forward='-Z', axis_up='Y',
               path_mode='COPY', embed_textures=True, mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False)
    tc1 = [o for o in vis if o.name.startswith('TreeCards')][:1]
    par_ = {o.name: o.parent for o in flora}
    for o in flora: o.parent = None                                   # the library is exported at the origin, not as one of its instances
    game = [o for o in vis if not (o.name.startswith('TreeCards') or o.name.startswith('GrassCards'))] + tc1 + blod + tbl
    for objs, stem in ((vis, 'aurelia_island'), (col, 'aurelia_island_collision'), (flora, 'aurelia_flora'), (kit, 'aurelia_kit'), (blod, 'aurelia_buildings_far'), (game, 'aurelia_game'), ([o for o in game if not o.name.startswith('BuildingsHD')], 'aurelia_game_lite')):
        sel(objs)
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, stem + '.glb'), export_format='GLB', export_yup=True, export_apply=True,
                                  export_cameras=False, export_lights=False, use_selection=True, export_vertex_color='ACTIVE')
        if not stem.startswith('aurelia_game'):
            try: bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, stem + '.fbx'), **fbx)
            except Exception as e: print('FBX export failed:', e)
    for o in flora: o.parent = par_[o.name]
    # lower-detail versions (suffix _LOD1) of the heavy meshes, in their own collection
    lc = bpy.data.collections.new('19_LOD1'); bpy.context.scene.collection.children.link(lc); lod = []; before = after = 0
    for o in vis + blod:
        if o.type != 'MESH': continue
        base = o.name.split('__')[0]
        if base.startswith('BuildingsHD'): continue
        if base in ('Props', 'GrassCards', 'Markings', 'Kerbs') or base.startswith('COL_'): continue
        heavy = (base.startswith('Terrain') or base in ('Structures', 'Shapes', 'Rocks', 'Bridges', 'Vegetation', 'Verge')) and len(o.data.polygons) > 300
        d = o.copy(); d.data = o.data.copy(); d.name = o.name + '_LOD1'; lc.objects.link(d); before += len(o.data.polygons)
        if heavy:
            md = d.modifiers.new('dec', 'DECIMATE'); md.ratio = 0.25 if base.startswith('Terrain') else 0.35
            with bpy.context.temp_override(object=d, active_object=d, selected_objects=[d]): bpy.ops.object.modifier_apply(modifier='dec')
        after += len(d.data.polygons); lod.append(d)
    sel(lod)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'aurelia_island_LOD1.glb'), export_format='GLB', export_yup=True, export_apply=True, export_cameras=False, export_lights=False, use_selection=True, export_vertex_color='ACTIVE')
    try: bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'aurelia_island_LOD1.fbx'), **fbx)
    except Exception as e: print('FBX export failed:', e)
    for d in lod: d.hide_render = True; d.hide_viewport = True
    L.STATS['LOD1'] = dict(objects=len(lod), triangles_LOD0_same_set=before, triangles_LOD1=after)
    import isle_trees as TRS, isle_night as NT; TRS.render_material(bpy.data.materials['Leaves'])
    for o in bpy.data.objects:
        b_ = o.name.split('__')[0]
        if b_ in ('TreeCards', 'GrassCards') or b_.startswith('BuildingsLOD') or b_.startswith('KIT_') or b_.startswith('COL_') or o.name.endswith('_LOD1'): o.hide_render = True
        if o.name.startswith('FLORA_'): o.hide_render = o.parent is None or not o.parent.name.startswith('INST_')
    for mn_ in ('Terrain', 'TerrainRock', 'TerrainSand', 'Boulders', 'TerrainBlend_Terrain', 'TerrainBlend_TerrainRock', 'TerrainBlend_TerrainSand'):                    # render-only: large-scale colour drift so the ground texture does not read as a repeat
        nt = bpy.data.materials[mn_].node_tree; bs = nt.nodes['Principled BSDF']; src = bs.inputs['Base Color'].links[0].from_socket
        tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.016; nz.inputs['Detail'].default_value = 5.0
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs[1].default_value = 0.3; mr.inputs[2].default_value = 0.7; mr.inputs[3].default_value = 0.80; mr.inputs[4].default_value = 1.14
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(nz.outputs[0], mr.inputs[0]); nt.links.new(src, mx.inputs[6]); nt.links.new(mr.outputs[0], mx.inputs[7]); nt.links.new(mx.outputs[2], bs.inputs['Base Color'])
    sh_ = bpy.data.images.load(os.path.abspath(os.path.join(OUT, 'ground_shade.png'))); sh_.colorspace_settings.name = 'Non-Color'; sh_.pack()
    for m_ in bpy.data.materials:                                        # render-only: the ground shade map multiplies every terrain material
        if m_.name.startswith('Terrain'):
            nt = m_.node_tree; bs = nt.nodes['Principled BSDF']; src = bs.inputs['Base Color'].links[0].from_socket; ge = nt.nodes.new('ShaderNodeNewGeometry'); mp = nt.nodes.new('ShaderNodeMapping')
            mp.inputs['Scale'].default_value = (1 / (K.X1 - K.X0), 1 / (K.Y1 - K.Y0), 1); mp.inputs['Location'].default_value = (0.5, 0.5, 0); ti = nt.nodes.new('ShaderNodeTexImage'); ti.image = sh_; ti.extension = 'EXTEND'
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 0.85
            nt.links.new(ge.outputs['Position'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], ti.inputs['Vector']); nt.links.new(src, mx.inputs[6]); nt.links.new(ti.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], bs.inputs['Base Color'])
    for m_ in bpy.data.materials:                                        # the overlay ground fades out with the weight stored in the second UV set
        if m_.name.startswith('TerrainBlend'):
            nt = m_.node_tree; uv = nt.nodes.new('ShaderNodeUVMap'); uv.uv_map = 'UVBlend'; sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(uv.outputs[0], sp.inputs[0]); nt.links.new(sp.outputs[0], nt.nodes['Principled BSDF'].inputs['Alpha'])
            try: m_.surface_render_method = 'BLENDED'
            except Exception: pass
    for mn_ in ('PaintedSurface', 'KitTrim', 'WallPlaster', 'WallBrick', 'Trim', 'RoofTiles', 'Painted'):     # render-only: rounded-edge shading (Bevel node) so edges catch light
        m_ = bpy.data.materials.get(mn_)
        if not m_: continue
        nt = m_.node_tree; bs = nt.nodes['Principled BSDF']; bv = nt.nodes.new('ShaderNodeBevel'); bv.samples = 6; bv.inputs['Radius'].default_value = 0.035
        if bs.inputs['Normal'].links: nt.links.new(bs.inputs['Normal'].links[0].from_socket, bv.inputs['Normal'])
        nt.links.new(bv.outputs[0], bs.inputs['Normal'])
    NT.setup(C)
    for o in bpy.data.objects: o.select_set(False)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(OUT, 'aurelia_island.blend')))
    L.STATS['TOTAL'] = sum(v for v in L.STATS.values() if isinstance(v, int)); L.STATS['objects'] = len(vis)
    L.STATS['collections'] = {c.name: len(c.objects) for c in C.cols}
    print('STATS ' + json.dumps(L.STATS))


if __name__ == '__main__':
    export(build())

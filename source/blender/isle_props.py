"""Street furniture kit for Aurelia Island, modelled in Blender: each part is a real mesh (lathed, swept, extruded or bevelled box)
run through Bevel + Weighted Normal modifiers, then merged into one object per prop with real-world UVs and photo PBR materials
(CC0 ambientCG scans: galvanised steel, cast iron, painted metal, concrete, wood, plastic) plus a painted sign-face atlas.
Origin of every prop: on the ground at its foot; +X is the direction it faces (arms, sign faces and signal lenses point that way).
Each prop gets LOD0 and a decimated LOD1 and is placed in the map as instances, like the plants."""
import math, os
import numpy as np
import bpy, bmesh
import isle_lib as L
import isle_photo as PH

PREFIX = 'PROP_'
KIT = []                       # placements: (prop, x, y, z, yaw) in Blender axes, filled by the map generators
SEG = 20                       # radial segments of round parts at LOD0
LOD = 0                        # 1 while building the far copies: half the segments, no bevels


# ---------------------------------------------------------------- materials
def _orm(name, rough_scale=1.0, rough_add=0.0, metal=None):
    r = PH.raw(name, 'Roughness'); m = PH.raw(name, 'Metalness')
    if r is None: return None
    rr = np.clip(r[..., 0] * rough_scale + rough_add, 0.04, 1); mm = (m[..., 0] if m is not None else np.zeros_like(rr)) if metal is None else np.full_like(rr, metal)
    return L.make_image('kit_%s_orm' % name, np.dstack([np.ones_like(rr), rr, mm]), raw=True)


def _rawrect(name, kind):
    f = os.path.join(PH.D, '%s_%s.raw' % (name, kind))
    if not os.path.exists(f): return None
    a = np.fromfile(f, np.uint8)
    for w in (512, 1024, 256):
        if len(a) % (w * 4) == 0 and len(a) // (w * 4) in (w, w // 2, w * 2):
            a = a.reshape(-1, w, 4).astype(float) / 255.0
            if kind in ('Color', 'NormalGL'):
                import isle_hd; a = isle_hd.upres(name, kind, a)
            return a[::-1]


def _col(name, mean, keep=0.8, flat=1.0, native=False):
    if native:                                                                   # keep the photo's own colour (bricks that should read as red, cream, brown)
        a = _rawrect(name, 'Color')[..., :3] ** 2.2; return np.clip(a / a.mean() * mean, 0, 1) ** (1 / 2.2)
    a = _rawrect(name, 'Color')[..., :3] ** 2.2; l = a.mean(2, keepdims=True); m = a.reshape(-1, 3).mean(0)
    c = l + (a / np.maximum(m, 1e-3) * m.mean() - l) * keep; c = c.mean() + (c - c.mean()) * flat
    return np.clip(c / c.mean() * mean, 0, 1) ** (1 / 2.2)


def sign_atlas(N=1024):
    """4 x 4 cells of sign faces, painted here (original designs, place names on Aurelia Island)."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new('RGB', (N, N), (200, 200, 200)); d = ImageDraw.Draw(im); c = N // 4
    def font(s, bold=True):
        try: return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else ''), s)
        except Exception: return ImageFont.load_default()
    def cell(i): return (i % 4) * c, (i // 4) * c
    for i, num in enumerate(('50', '80', '30')):                              # 0-2 speed limits
        x, y = cell(i); d.rectangle([x, y, x + c, y + c], fill=(205, 205, 200)); d.ellipse([x + 6, y + 6, x + c - 6, y + c - 6], fill=(196, 22, 24)); d.ellipse([x + 34, y + 34, x + c - 34, y + c - 34], fill=(240, 240, 236))
        f = font(96); w = d.textlength(num, font=f); d.text((x + c / 2 - w / 2, y + c / 2 - 58), num, font=f, fill=(18, 18, 20))
    for i, kind in ((3, 'curve'), (4, 'bend'), (5, 'cross')):                 # 3-5 warning triangles
        x, y = cell(i); d.rectangle([x, y, x + c, y + c], fill=(205, 205, 200))
        T = [(x + c / 2, y + 10), (x + c - 8, y + c - 22), (x + 8, y + c - 22)]; d.polygon(T, fill=(196, 22, 24))
        t = [(x + c / 2, y + 48), (x + c - 40, y + c - 42), (x + 40, y + c - 42)]; d.polygon(t, fill=(240, 236, 220))
        if kind == 'curve': d.line([(x + 112, y + 200), (x + 112, y + 160), (x + 150, y + 125), (x + 150, y + 95)], fill=(15, 15, 15), width=16)
        elif kind == 'bend': d.line([(x + 98, y + 200), (x + 98, y + 150), (x + 158, y + 150), (x + 158, y + 110)], fill=(15, 15, 15), width=16)
        else: d.line([(x + 128, y + 200), (x + 128, y + 96)], fill=(15, 15, 15), width=16); d.line([(x + 96, y + 150), (x + 160, y + 150)], fill=(15, 15, 15), width=16)
    for i, (a, b) in ((6, ('City Centre', 'Harbour')), (7, ('Circuit', 'Mesa')), (8, ('Coast Road', 'Pine Lake'))):   # 6-8 direction boards (2:1, two cells wide is too much; drawn 2:1 inside the cell)
        x, y = cell(i); d.rectangle([x, y, x + c, y + c], fill=(26, 74, 150)); d.rectangle([x + 6, y + 6, x + c - 6, y + c - 6], outline=(240, 240, 236), width=5)
        f = font(23)
        for k, (t, arr) in enumerate(((a, 1), (b, -1))):
            yy = y + 52 + k * 96; d.text((x + 22, yy), t, font=f, fill=(245, 245, 240)); ax = x + c - 46
            d.polygon([(ax + arr * 22, yy + 18), (ax - arr * 8, yy + 2), (ax - arr * 8, yy + 34)], fill=(245, 245, 240)); d.rectangle([min(ax - arr * 8, ax - arr * 26), yy + 12, max(ax - arr * 8, ax - arr * 26), yy + 24], fill=(245, 245, 240))
    x, y = cell(9); d.rectangle([x, y, x + c, y + c], fill=(26, 74, 150)); f = font(150); d.text((x + 70, y + 30), 'P', font=f, fill=(245, 245, 240))          # 9 parking
    x, y = cell(10); d.rectangle([x, y, x + c, y + c], fill=(205, 205, 200)); d.polygon([(x + c / 2, y + 8), (x + c - 8, y + c / 2), (x + c / 2, y + c - 8), (x + 8, y + c / 2)], fill=(240, 240, 236))   # 10 priority road
    d.polygon([(x + c / 2, y + 40), (x + c - 40, y + c / 2), (x + c / 2, y + c - 40), (x + 40, y + c / 2)], fill=(232, 178, 24))
    x, y = cell(11); d.rectangle([x, y, x + c, y + c], fill=(205, 205, 200)); d.regular_polygon((x + c / 2, y + c / 2, c / 2 - 8), 8, rotation=22.5, fill=(196, 22, 24))   # 11 stop (octagon, word)
    f = font(62); w = d.textlength('STOP', font=f); d.text((x + c / 2 - w / 2, y + c / 2 - 36), 'STOP', font=f, fill=(245, 245, 240))
    for i, (bg, fg) in ((12, ((236, 120, 40), (250, 240, 220))), (13, ((40, 120, 90), (240, 236, 220)))):                     # 12-13 shelter adverts (abstract)
        x, y = cell(i); d.rectangle([x, y, x + c, y + c], fill=bg); d.ellipse([x + 40, y + 30, x + 200, y + 190], fill=fg); d.rectangle([x + 30, y + 206, x + 226, y + 222], fill=fg)
    x, y = cell(14); d.rectangle([x, y, x + c, y + c], fill=(230, 230, 226)); d.rectangle([x, y + 96, x + c, y + 160], fill=(18, 18, 20))                       # 14 bollard / post band
    x, y = cell(15); d.rectangle([x, y, x + c, y + c], fill=(70, 72, 76))                                                                                     # 15 sign back (galvanised grey)
    a = np.asarray(im, float) / 255.0
    noise = np.random.default_rng(3).normal(0, 0.012, a.shape[:2])[..., None]; return np.clip(a * 0.92 + noise, 0, 1)[::-1]


_M = None
def mats():
    global _M
    if _M is None: _M = materials()
    return _M


def materials():
    M = {}
    def m(key, photo, mean, rough=(1.0, 0.0), metal=None, nstr=1.0, keep=0.8, flat=1.0, native=False):
        img = L.make_image('kit_' + photo, _col(photo, mean, keep, flat, native)); n = _rawrect(photo, 'NormalGL'); r = _rawrect(photo, 'Roughness'); mt = _rawrect(photo, 'Metalness')
        rr = np.clip(r[..., 0] * rough[0] + rough[1], 0.05, 1); mm = (mt[..., 0] if mt is not None else np.zeros_like(rr)) if metal is None else np.full_like(rr, metal)
        orm = L.make_image('kit_%s_orm' % photo, np.dstack([np.ones_like(rr), rr, mm]), raw=True)
        M[key] = L.new_mat('Kit' + key.capitalize(), image=img, vcol=True, normal=L.make_image('kit_%s_n' % photo, n[..., :3], raw=True), nstrength=nstr, orm=orm)
    m('galv', 'Metal032', 0.62, (0.7, 0.18), None, 0.6)
    m('iron', 'Metal046A', 0.5, (0.9, 0.05), 0.65, 1.0)
    m('paint', 'PaintedMetal004', 0.75, (0.9, 0.0), None, 1.0, 0.25)
    m('concrete', 'Concrete034', 0.72, (1.0, 0.0), 0.0, 1.0)
    m('wood', 'Wood049', 0.62, (1.0, 0.05), 0.0, 1.0, 0.9)
    m('plastic', 'Plastic006', 0.55, (0.8, 0.05), 0.0, 0.5, 0.0)
    M['smooth'] = L.new_mat('KitSmooth', 0.38, 0.0, vcol=True)
    m('plaster', 'Plaster001', 0.86, (1.0, 0.0), 0.0, 1.2, 0.0)
    m('roof', 'RoofingTiles006', 0.62, (1.0, 0.0), 0.0, 1.0, 0.0)
    m('stone', 'Bricks076A', 0.72, (1.0, 0.0), 0.0, 1.0, 0.0, 0.6)
    m('pwood', 'PaintedWood005', 0.8, (0.9, 0.05), 0.0, 0.8, 0.0, 0.35)
    m('corr', 'CorrugatedSteel005', 0.62, (0.9, 0.05), None, 1.0, 0.0)
    m('planks', 'Planks012', 0.62, (1.0, 0.0), 0.0, 1.0, 0.9)
    m('boards', 'Planks021', 0.8, (1.0, 0.0), 0.0, 1.0, 0.0, 0.7)
    m('brick', 'Bricks059', 0.5, (1.0, 0.0), 0.0, 1.0, 0.85)
    m('ashlar', 'Bricks066', 0.72, (1.0, 0.0), 0.0, 1.0, 0.3)
    m('brick2', 'Bricks085', 0.5, (1.0, 0.0), 0.0, 1.0, 0.9, native=True)                   # classic red
    m('brick3', 'Bricks029', 0.68, (1.0, 0.0), 0.0, 1.0, 0.85, native=True)                 # cream / yellow
    m('brick4', 'Bricks023', 0.42, (1.0, 0.0), 0.0, 1.0, 0.9, native=True)                  # dark brown, irregular
    m('brickg', 'Bricks061', 0.7, (1.0, 0.0), 0.0, 1.0, 0.2, native=True)                   # painted grey
    m('plaster2', 'Plaster004', 0.86, (1.0, 0.0), 0.0, 1.2, 0.0)
    m('concrete2', 'Concrete044A', 0.75, (1.0, 0.0), 0.0, 1.0, 0.2)
    m('fabric', 'Fabric026', 0.75, (1.0, 0.0), 0.0, 1.0, 0.0, 0.6)
    M['shops'] = L.new_mat('KitShops', 0.5, 0.0, image=L.make_image('kit_shop_atlas', shop_atlas()), vcol=True)
    M['ads'] = L.new_mat('KitAds', 0.5, 0.0, image=L.make_image('kit_ad_atlas', ad_atlas()), vcol=True)
    M['neon'] = L.new_mat('KitNeon', 0.35, 0.0, image=L.make_image('kit_neon_atlas', ad_atlas()), vcol=True)
    nb_ = M['neon'].node_tree.nodes['Principled BSDF']; tx_ = [n for n in M['neon'].node_tree.nodes if n.type == 'TEX_IMAGE'][0]; M['neon'].node_tree.links.new(tx_.outputs['Color'], nb_.inputs['Emission Color']); nb_.inputs['Emission Strength'].default_value = 1.6
    M['winglass'] = L.new_mat('KitWindow', 0.06, 0.0, color=(0.05, 0.07, 0.09), vcol=False)
    M['sign'] = L.new_mat('KitSigns', 0.45, 0.0, image=L.make_image('kit_sign_atlas', sign_atlas()), vcol=True)
    M['lens'] = L.new_mat('KitLens', 0.08, 0.0, vcol=True); b = M['lens'].node_tree.nodes['Principled BSDF']
    vc = [n for n in M['lens'].node_tree.nodes if n.type == 'VERTEX_COLOR'][0]; M['lens'].node_tree.links.new(vc.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 1.2
    M['glass'] = L.new_mat('KitGlass', 0.05, 0.0, color=(0.7, 0.8, 0.82), alpha=0.32, vcol=False, double=True)
    return M


# ---------------------------------------------------------------- part builder
class Part:
    """Collects modelled parts (Blender objects with modifiers), evaluates them and merges into numpy arrays."""
    def __init__(s): s.objs = []

    def obj(s, bm, mat, col=(1, 1, 1), uv='box', uvs=1.0, bevel=0.0, bseg=2, angle=40, smooth=True, sign=None):
        if LOD: bevel = 0.0
        if bevel <= 0:                                                    # fast path: no modifiers, read the mesh straight from bmesh
            bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.normal_update()
            V = np.array([v.co[:] for v in bm.verts]); VN = np.array([v.normal[:] for v in bm.verts])
            T = np.array([[v.index for v in f.verts] for f in bm.faces], np.int64).reshape(-1, 3); bm.free()
            if not len(T): return None
            P = V[T.ravel()]; Tn = np.arange(len(P)).reshape(-1, 3)
            fn = np.cross(P[Tn[:, 1]] - P[Tn[:, 0]], P[Tn[:, 2]] - P[Tn[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1), 1e-12)[:, None]; fnc = np.repeat(fn, 3, 0)
            vn = VN[T.ravel()]; N = np.where(((vn * fnc).sum(1) > math.cos(math.radians(angle)))[:, None] & smooth, vn, fnc)
            s.objs.append(('raw', P, Tn, N, mat, np.asarray(col, float), uv, uvs, sign)); return None
        me = bpy.data.meshes.new('kp'); bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = smooth
        o = bpy.data.objects.new('kp', me); bpy.context.scene.collection.objects.link(o)
        b = o.modifiers.new('b', 'BEVEL'); b.width = bevel; b.segments = bseg; b.limit_method = 'ANGLE'; b.angle_limit = math.radians(angle); b.harden_normals = False; b.miter_outer = 'MITER_ARC'
        if smooth:
            w = o.modifiers.new('w', 'WEIGHTED_NORMAL'); w.keep_sharp = True; w.mode = 'FACE_AREA'
            try: me.set_sharp_from_angle(angle=math.radians(angle))
            except Exception: pass
        s.objs.append((o, mat, np.asarray(col, float), uv, uvs, sign)); return o

    @staticmethod
    def finish(P, T, N, mat, col, uv, uvs, sign):
        fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1), 1e-12)[:, None]
        ln = np.zeros((len(P), 3)); ln[T.ravel()] = np.repeat(fn, 3, 0)
        if uv in ('cyl', 'cylv'):
            cx_, cy_ = P[:, 0].mean(), P[:, 1].mean(); a = np.arctan2(P[:, 1] - cy_, P[:, 0] - cx_); r = np.hypot(P[:, 0] - cx_, P[:, 1] - cy_); U = np.c_[a / (2 * np.pi) * max(r.max(), 0.05) * 2 * np.pi, P[:, 2]] / uvs
            cap = np.abs(ln[:, 2]) > 0.8; U[cap] = P[cap][:, :2] / uvs
            if uv == 'cylv': U = U[:, ::-1]
        elif uv == 'roof':                                                              # tile rows run along the slope's contour
            nh = ln[:, :2] / np.maximum(np.linalg.norm(ln[:, :2], axis=1), 1e-6)[:, None]; tt = np.c_[-nh[:, 1], nh[:, 0]]
            U = np.c_[(P[:, :2] * tt).sum(1), (P[:, :2] * nh).sum(1) / np.maximum(np.abs(ln[:, 2]), 0.35)] / uvs
        elif uv == 'sign':
            U = sign(P, ln)
        else:
            ax = np.argmax(np.abs(ln), 1); U = np.where((ax == 2)[:, None], P[:, [0, 1]], np.where((ax == 0)[:, None], P[:, [1, 2]], P[:, [0, 2]])) / uvs
            if uv == 'boxv': U = U[:, ::-1]
        ao = np.clip(0.72 + 0.28 * np.clip(P[:, 2] / 0.9, 0, 1), 0, 1) * (1 - 0.12 * np.clip(-ln[:, 2], 0, 1))      # cheap occlusion in the vertex colour
        return (P, T, N, U, col[None, :] * ao[:, None], mat)

    def arrays(s):
        dg = None; out = []
        for it in s.objs:
            if it[0] == 'raw':
                _, P, T, N, mat, col, uv, uvs, sign = it; out.append(Part.finish(P, T, N, mat, col, uv, uvs, sign)); continue
            o, mat, col, uv, uvs, sign = it
            if dg is None: dg = bpy.context.evaluated_depsgraph_get()
            e = o.evaluated_get(dg); me = e.to_mesh(); me.calc_loop_triangles()
            V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
            T = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get('loops', T); T = T.reshape(-1, 3)
            LV = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', LV)
            N = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', N); N = N.reshape(-1, 3)
            out.append(Part.finish(V[LV], T, N, mat, col, uv, uvs, sign)); e.to_mesh_clear()
        for it in s.objs:
            if it[0] != 'raw': bpy.data.objects.remove(it[0], do_unlink=True)
        s.objs = []
        return out


def make_prop(name, groups):
    """groups: list of (P, T, N, U, C, mat). Builds one Blender object, one material slot per material."""
    mats = []; Vs = []; Fs = []; Ns = []; Us = []; Cs = []; mi = []; off = 0
    for P, T, N, U, C, mat in groups:
        if mat not in mats: mats.append(mat)
        Vs.append(P); Fs.append(T + off); Ns.append(N); Us.append(U); Cs.append(C); mi.append(np.full(len(T), mats.index(mat))); off += len(P)
    V = np.vstack(Vs); F = np.vstack(Fs); N = np.vstack(Ns); U = np.vstack(Us); C = np.vstack(Cs); mi = np.concatenate(mi)
    o = np.argsort(mi, kind='stable'); F = F[o]; mi = mi[o]
    # weld identical corners (same position, normal, uv, colour) so the mesh is indexed
    key = np.c_[np.round(V * 2e4), np.round(N * 500), np.round(U * 4e3), np.round(C * 255)].astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.ravel()
    V, N, U, C = V[first], N[first], U[first], C[first]; F = inv[F]
    ok = (F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2]); F = F[ok]; mi = mi[ok]                 # drop triangles collapsed by the weld
    N = np.nan_to_num(N); N[np.linalg.norm(N, axis=1) < 0.5] = (0, 0, 1)
    me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co', V.astype(np.float32).ravel())
    me.loops.add(len(F) * 3); me.loops.foreach_set('vertex_index', F.astype(np.int32).ravel()); me.polygons.add(len(F))
    me.polygons.foreach_set('loop_start', np.arange(len(F), dtype=np.int32) * 3); me.polygons.foreach_set('loop_total', np.full(len(F), 3, np.int32))
    for m in mats: me.materials.append(m)
    me.polygons.foreach_set('material_index', mi.astype(np.int32)); me.update(calc_edges=True); me.polygons.foreach_set('use_smooth', np.ones(len(F), bool))
    li = F.astype(np.int32).ravel()
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER'); ca.data.foreach_set('color', np.c_[np.clip(C[li], 0, 1), np.ones(len(li))].astype(np.float32).ravel())
    uv = me.uv_layers.new(name='UVMap'); uv.data.foreach_set('uv', U[li].astype(np.float32).ravel())
    me.normals_split_custom_set([tuple(n) for n in N[li]])
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob, len(F)


# ---------------------------------------------------------------- modelling primitives (bmesh)
def lathe(profile, seg=SEG, x=0, y=0, z=0, close_top=True, close_bottom=True, a0=0.0, a1=2 * np.pi):
    """profile: [(r, h)] bottom to top. Revolved about the vertical axis through (x, y)."""
    if LOD: seg = max(6, seg // 2)
    bm = bmesh.new(); full = abs(a1 - a0 - 2 * np.pi) < 1e-6; n = seg if full else seg + 1
    rings = []
    for r, h in profile:
        ring = []
        for k in range(n):
            a = a0 + (a1 - a0) * k / seg; ring.append(bm.verts.new((x + max(r, 1e-4) * math.cos(a), y + max(r, 1e-4) * math.sin(a), z + h)))
        rings.append(ring)
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(seg):
            k1 = (k + 1) % n if full else k + 1
            try: bm.faces.new((r0[k], r0[k1], r1[k1], r1[k]))
            except ValueError: pass
    if close_bottom and full and profile[0][0] > 1e-3: bm.faces.new(list(reversed(rings[0])))
    if close_top and full and profile[-1][0] > 1e-3: bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def sweep(path, r, seg=12, caps=True):
    """Round tube along a polyline (parallel-transported frames)."""
    if LOD: seg = max(5, seg // 2)
    path = [np.asarray(p, float) for p in path]; bm = bmesh.new(); rings = []
    t_prev = None; nrm = None
    for i, p in enumerate(path):
        t = path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]; t /= np.linalg.norm(t)
        if nrm is None: nrm = np.cross(t, [0, 0, 1.0]) if abs(t[2]) < 0.9 else np.cross(t, [1.0, 0, 0]); nrm /= np.linalg.norm(nrm)
        else: nrm = nrm - t * np.dot(nrm, t); nrm /= np.linalg.norm(nrm)
        b = np.cross(t, nrm); rr = r(i / (len(path) - 1)) if callable(r) else r
        rings.append([bm.verts.new(tuple(p + rr * (math.cos(a) * nrm + math.sin(a) * b))) for a in np.arange(seg) * 2 * np.pi / seg])
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(seg): bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
    if caps: bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return bm


def bbox(cx, cy, cz, sx, sy, sz, yaw=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        x, y, z = v.co.x * sx, v.co.y * sy, v.co.z * sz; c, s = math.cos(yaw), math.sin(yaw); v.co = (cx + x * c - y * s, cy + x * s + y * c, cz + z)
    return bm


def prism(outline, z0, z1, axis='z', at=0.0):
    """Extrude a 2D outline [(u, v)]: axis 'z' -> outline in xy from z0 to z1; axis 'x' -> outline in (y, z) from x=z0 to x=z1."""
    bm = bmesh.new(); A = []; B = []
    for u, v in outline:
        if axis == 'z': A.append(bm.verts.new((u, v, z0))); B.append(bm.verts.new((u, v, z1)))
        else: A.append(bm.verts.new((z0, u, v))); B.append(bm.verts.new((z1, u, v)))
    n = len(outline); bm.faces.new(list(reversed(A))); bm.faces.new(B)
    for k in range(n): bm.faces.new((A[k], A[(k + 1) % n], B[(k + 1) % n], B[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return bm


def poly_round(pts, r, seg=4):
    """Round the corners of a closed 2D polygon."""
    pts = [np.asarray(p, float) for p in pts]; out = []; n = len(pts)
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]; a = (p0 - p1) / np.linalg.norm(p0 - p1); b = (p2 - p1) / np.linalg.norm(p2 - p1)
        ang = math.acos(np.clip(np.dot(a, b), -1, 1)); d = r / math.tan(ang / 2); s0 = p1 + a * d; s1 = p1 + b * d
        bis = (a + b) / np.linalg.norm(a + b); c = p1 + bis * (r / math.sin(ang / 2))
        a0 = math.atan2(*(s0 - c)[::-1]); a1 = math.atan2(*(s1 - c)[::-1]); da = (a1 - a0 + np.pi) % (2 * np.pi) - np.pi
        for k in range(seg + 1): t = a0 + da * k / seg; out.append((c[0] + r * math.cos(t), c[1] + r * math.sin(t)))
    return out


SHOPS = ['Cafe Aurelia', 'Bakery', 'Pharmacy', 'Books', 'Florist', 'Harbour Deli', 'Optician', 'Pizzeria', 'Wine Bar', 'Hardware', 'Bistro', 'Tailor', 'Gelato', 'Market', 'Barber', 'Records']


def shop_atlas(N=1024):
    """4 x 4 shop name panels (original names), letters on painted boards."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new('RGB', (N, N // 4 * 4)); d = ImageDraw.Draw(im); cw, ch = N // 4, N // 4
    bgs = [(28, 30, 34), (238, 232, 218), (22, 52, 40), (110, 24, 22), (24, 40, 78), (196, 150, 60), (60, 62, 66), (230, 226, 214)]
    for i, name in enumerate(SHOPS):
        x, y = (i % 4) * cw, (i // 4) * ch; bg = bgs[i % len(bgs)]; fg = (245, 240, 228) if sum(bg) < 400 else (30, 30, 32)
        d.rectangle([x, y, x + cw, y + ch], fill=bg); d.rectangle([x + 6, y + 6, x + cw - 6, y + ch - 6], outline=fg, width=3)
        s = 64
        while s > 14:
            f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', s)
            if d.textlength(name, font=f) < cw - 28: break
            s -= 2
        w = d.textlength(name, font=f); d.text((x + cw / 2 - w / 2, y + ch / 2 - s * 0.62), name, font=f, fill=fg)
    a = np.asarray(im, float) / 255.0; return a[::-1]


ADS = [('AURELIA COLA', (190, 20, 30), (250, 245, 235)), ('VORTEX MOTORS', (20, 22, 26), (240, 60, 40)), ('ISLAND AIR', (25, 90, 170), (250, 250, 250)), ('MARE BANK', (20, 70, 60), (240, 220, 150)),
       ('SUNSET RADIO', (240, 120, 30), (40, 20, 60)), ('PIXEL PHONE', (30, 30, 34), (90, 220, 250)), ('GELATO BLU', (90, 160, 230), (255, 255, 255)), ('HOTEL CORAL', (230, 110, 110), (255, 250, 240))]


def ad_atlas(N=1024):
    """4 x 2 cells of billboard and neon artwork for made-up brands (2:1 cells)."""
    from PIL import Image, ImageDraw, ImageFont
    cw, ch = N // 4, N // 4; im = Image.new('RGB', (N, N // 2)); d = ImageDraw.Draw(im)
    for i, (txt, bg, fg) in enumerate(ADS):
        x, y = (i % 4) * cw, (i // 4) * ch; d.rectangle([x, y, x + cw, y + ch], fill=bg)
        for k in range(6): d.ellipse([x + cw * 0.62 + k * 6 - 40, y + 20 + k * 3, x + cw * 0.62 + 60 - k * 4, y + ch - 30 - k * 2], outline=tuple(int(v * 0.8 + c * 0.2) for v, c in zip(bg, fg)), width=2)
        s = 46
        while s > 12:
            f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', s)
            if d.textlength(txt, font=f) < cw - 24: break
            s -= 2
        w = d.textlength(txt, font=f); d.text((x + cw / 2 - w / 2, y + ch / 2 - s * 0.6), txt, font=f, fill=fg)
        d.rectangle([x + 4, y + 4, x + cw - 4, y + ch - 4], outline=fg, width=3)
    a = np.asarray(im.resize((N, N), Image.LANCZOS), float) / 255.0; return a[::-1]


def ad_uv_frame(F, cell, uc, zc, w, h):
    """UV mapper for the ad atlas (4 x 2 cells stretched over the full texture)."""
    u0 = (cell % 4) / 4; v0 = 1 - (cell // 4 + 1) / 2
    def f(Pt, ln):
        front = (ln @ F.n) > 0.5; uu = np.clip(((Pt - F.o) @ F.u - uc) / w + 0.5, 0.01, 0.99); vv = np.clip((Pt[:, 2] - zc) / h + 0.5, 0.01, 0.99)
        return np.where(front[:, None], np.c_[u0 + uu / 4, v0 + vv / 2], np.c_[u0 + 0.01, v0 + 0.01] + 0 * uu[:, None])
    return f


def sign_cell_uv_frame(F, cell, uc, zc, w, h):
    """UV mapper for a panel facing along a Frame's normal: cell of a 4x4 atlas."""
    u0 = (cell % 4) / 4; v0 = 1 - (cell // 4 + 1) / 4
    def f(Pt, ln):
        front = (ln @ F.n) > 0.5; uu = np.clip(((Pt - F.o) @ F.u - uc) / w + 0.5, 0.01, 0.99); vv = np.clip((Pt[:, 2] - zc) / h + 0.5, 0.01, 0.99)
        return np.where(front[:, None], np.c_[u0 + uu / 4, v0 + vv / 4], np.c_[u0 + 0.01, v0 + 0.01] + 0 * uu[:, None])
    return f


def sign_cell_uv(cell, ox, oy, w, h, face_x):
    """UV mapper for a sign plate whose face is the plane x = face_x (facing +X), centred (oy, oz) size w x h."""
    u0 = (cell % 4) / 4; v0 = 1 - (cell // 4 + 1) / 4; back = 15
    bu0 = (back % 4) / 4; bv0 = 1 - (back // 4 + 1) / 4
    def f(P, ln):
        front = (ln[:, 0] > 0.5) & (P[:, 0] > face_x - 0.004)
        uu = np.clip((P[:, 1] - ox) / w + 0.5, 0.01, 0.99); vv = np.clip((P[:, 2] - oy) / h + 0.5, 0.01, 0.99)
        return np.where(front[:, None], np.c_[u0 + uu / 4, v0 + vv / 4], np.c_[bu0 + 0.02 + uu * 0.21, bv0 + 0.02 + vv * 0.21])
    return f


# ---------------------------------------------------------------- the props
IRON = (0.32, 0.4, 0.36)        # dark green paint on cast iron
GREY = (0.75, 0.76, 0.78)
WHITE = (1, 1, 1)


def streetlamp(K, M):
    base = [(0.2, 0), (0.2, 0.06), (0.17, 0.08), (0.16, 0.42), (0.18, 0.46), (0.18, 0.5), (0.13, 0.56), (0.12, 0.8), (0.14, 0.84), (0.14, 0.88), (0.105, 0.94)]
    K.obj(lathe(base, SEG), M['iron'], IRON, 'cyl', 0.6, 0.012, 2, 30)
    K.obj(lathe([(0.105, 0.9), (0.085, 4.0), (0.065, 7.5), (0.06, 7.66)], SEG), M['galv'], GREY, 'cyl', 1.2)
    for k in range(4):                                                                      # base bolts
        a = k * np.pi / 2 + np.pi / 4; K.obj(lathe([(0.018, 0), (0.018, 0.05), (0.012, 0.07)], 8, 0.19 * math.cos(a) * 0.98, 0.19 * math.sin(a) * 0.98, 0.0), M['galv'], GREY)
    K.obj(bbox(0.168, 0, 0.27, 0.03, 0.12, 0.26), M['iron'], IRON, 'box', 0.4, 0.006, 2)  # access door
    arc = [(0.0, 0, 7.6)] + [(1.9 * (1 - math.cos(t)) * 0.0 + 0.55 * math.sin(t) * 0 + 0, 0, 0) for t in []]
    pts = []; R_ = 0.9
    for t in np.linspace(0, np.pi / 2, 9): pts.append((R_ - R_ * math.cos(t), 0, 7.4 + R_ * math.sin(t)))
    pts += [(R_ + d, 0, 7.4 + R_ + 0.04 * d) for d in np.linspace(0.15, 1.35, 5)]
    pts = [(0, 0, 7.2)] + pts
    K.obj(sweep(pts, lambda u: 0.05 - 0.015 * u, 12), M['galv'], GREY, 'box', 1.0)
    hx = R_ + 1.55; hz = 7.4 + R_ + 0.04 * 1.4
    lum = prism(poly_round([(-0.42, -0.17), (0.4, -0.15), (0.46, 0.0), (0.4, 0.15), (-0.42, 0.17)], 0.05, 3), hz - 0.06, hz + 0.05)
    for v in lum.verts:
        v.co.x += hx; f = max(0, (v.co.z - hz)) * (1 - abs(v.co.y) / 0.2) * 0.8; v.co.z += f * 0.5
    K.obj(lum, M['iron'], (0.24, 0.25, 0.27), 'box', 0.5, 0.012, 2, 35)
    K.obj(bbox(hx + 0.02, 0, hz - 0.068, 0.62, 0.22, 0.02), M['lens'], (1.0, 0.94, 0.78), 'box', 1.0, 0.005, 1)


def signal(K, M):
    K.obj(lathe([(0.17, 0), (0.17, 0.05), (0.13, 0.1), (0.11, 0.6), (0.095, 5.2), (0.09, 5.3)], SEG), M['galv'], GREY, 'cyl', 1.2, 0.0)
    K.obj(lathe([(0.06, 0), (0.1, 0.02), (0.1, 0.06), (0.0, 0.08)], 12, 0, 0, 5.3), M['plastic'], (0.3, 0.3, 0.3))
    def head(yaw, zc, ped=False):
        c, s = math.cos(yaw), math.sin(yaw); off = 0.27
        def T(bm):
            for v in bm.verts:
                x, y, z = v.co; v.co = (x * c - y * s, x * s + y * c, z)
            return bm
        n = 2 if ped else 3; hh = 0.36 * n + 0.08
        K.obj(T(bbox(off, 0, zc, 0.26, 0.32, hh)), M['plastic'], (0.22, 0.22, 0.22), 'box', 0.6, 0.03, 3)
        bp = T(prism(poly_round([(-0.3, -hh / 2 - 0.08), (0.3, -hh / 2 - 0.08), (0.3, hh / 2 + 0.08), (-0.3, hh / 2 + 0.08)], 0.06, 3), off - 0.15, off - 0.13, axis='x'))
        for v in bp.verts: v.co.z += zc
        K.obj(bp, M['plastic'], (0.12, 0.12, 0.12), 'box', 0.6, 0.006, 1)
        cols = [(1.0, 0.12, 0.08), (1.0, 0.62, 0.08), (0.15, 1.0, 0.45)] if not ped else [(1.0, 0.25, 0.1), (0.9, 0.95, 0.9)]
        for k in range(n):
            z = zc + (n - 1) / 2 * 0.36 - k * 0.36
            ln = T(lathe([(0.0, 0.0), (0.1, 0.0), (0.105, 0.012), (0.09, 0.03), (0.0, 0.04)], 16))
            for v in ln.verts: x, y, zz = v.co; v.co = (zz * c + off * c + 0.13 * c - 0.0, zz * s + off * s + 0.13 * s, z) if False else v.co
            l2 = lathe([(0.0, 0.0), (0.1, 0.0), (0.105, 0.012), (0.09, 0.03), (0.0, 0.04)], 16)
            for v in l2.verts:                                                                 # lens: lathe axis turned to face out
                x, y, zz = v.co; px, py, pz = off + 0.13 + zz, x, z + y; v.co = (px * c - py * s, px * s + py * c, pz)
            ln.free(); K.obj(l2, M['lens'], cols[k] if not (ped and k == 0) else cols[0], 'box', 1.0)
            vi = lathe([(0.125, 0.0), (0.125, 0.22)], 14, a0=-0.15, a1=np.pi + 0.15, close_top=False, close_bottom=False)   # visor: half tube over the lens
            bmesh.ops.solidify(vi, geom=vi.faces[:], thickness=0.012)
            for v in vi.verts:
                x, y, zz = v.co; px, py, pz = off + 0.13 + zz, y, z + x * 0.0 + 0.0
                px, py, pz = off + 0.13 + zz, -x, z + y * 1.0
                v.co = (px * c - py * s, px * s + py * c, pz)
            K.obj(vi, M['plastic'], (0.16, 0.16, 0.16), 'box', 0.5)
        K.obj(T(bbox(0.13, 0, zc + hh / 2 - 0.1, 0.12, 0.08, 0.06)), M['galv'], GREY)        # bracket
        K.obj(T(bbox(0.13, 0, zc - hh / 2 + 0.1, 0.12, 0.08, 0.06)), M['galv'], GREY)
    head(0.0, 4.6); head(np.pi / 2, 4.6); head(np.pi, 2.6, ped=True)
    K.obj(bbox(0.12, 0, 1.15, 0.1, 0.12, 0.22), M['paint'], (0.95, 0.75, 0.15), 'box', 0.4, 0.015, 2)   # push-button box
    K.obj(bbox(0.17, 0, 1.18, 0.02, 0.05, 0.05), M['plastic'], (0.2, 0.2, 0.2))


def bench(K, M):
    for yy in (-0.85, 0.85):                                     # cast iron side frames
        fr = prism(poly_round([(-0.28, 0.0), (-0.2, 0.0), (-0.12, 0.38), (0.18, 0.38), (0.22, 0.0), (0.3, 0.0), (0.24, 0.44), (-0.12, 0.47), (-0.26, 0.9), (-0.34, 0.88), (-0.22, 0.44)], 0.025, 2), yy - 0.035, yy + 0.035, axis='z')
        for v in fr.verts: x, y, z = v.co; v.co = (x, z, y)
        K.obj(fr, M['iron'], IRON, 'box', 0.4, 0.012, 2, 30)
        arm = sweep([(-0.25, yy, 0.62), (-0.05, yy, 0.66), (0.2, yy, 0.64), (0.26, yy, 0.58)], 0.025, 10)
        K.obj(arm, M['iron'], IRON, 'box', 0.4)
    for k, x in enumerate(np.linspace(-0.13, 0.19, 5)):            # seat slats
        K.obj(bbox(x + 0.0, 0, 0.42, 0.06, 1.95, 0.035), M['wood'], (0.95, 0.82, 0.68), 'box', 0.9, 0.008, 2)
    for k in range(3):                                           # back slats following the frame slope
        z = 0.55 + k * 0.13; x = -0.13 - (z - 0.47) * 0.32
        b = bbox(x, 0, z, 0.03, 1.95, 0.09)
        for v in b.verts: v.co.x += (v.co.z - z) * -0.32
        K.obj(b, M['wood'], (0.95, 0.82, 0.68), 'box', 0.9, 0.008, 2)
    for yy in (-0.6, 0, 0.6): K.obj(lathe([(0.012, 0), (0.012, 0.02), (0.0, 0.025)], 8, 0.03, yy, 0.44), M['galv'], GREY)


def litter_bin(K, M):
    prof = [(0.0, 0.0), (0.19, 0.0), (0.21, 0.04), (0.2, 0.08), (0.22, 0.12), (0.24, 0.7), (0.26, 0.74), (0.26, 0.8), (0.22, 0.82), (0.2, 0.86), (0.16, 0.86), (0.15, 0.8)]
    K.obj(lathe(prof, 24, close_top=False), M['iron'], IRON, 'cyl', 0.5, 0.0)
    for k in range(12):                                          # vertical ribs
        a = k * np.pi / 6; K.obj(bbox(0.235 * math.cos(a), 0.235 * math.sin(a), 0.42, 0.03, 0.025, 0.56, a), M['iron'], IRON, 'box', 0.5, 0.008, 2)
    K.obj(lathe([(0.13, 0.62), (0.13, 0.79), (0.0, 0.79)], 16, close_bottom=False), M['plastic'], (0.08, 0.08, 0.08))


def hydrant(K, M):
    prof = [(0.0, 0), (0.15, 0), (0.15, 0.04), (0.12, 0.06), (0.1, 0.1), (0.1, 0.5), (0.12, 0.52), (0.12, 0.56), (0.105, 0.58), (0.1, 0.66), (0.07, 0.72), (0.04, 0.74), (0.03, 0.78), (0.0, 0.79)]
    K.obj(lathe(prof, 20), M['paint'], (0.95, 0.2, 0.12), 'cyl', 0.4)
    for yaw in (0, np.pi / 2, np.pi):
        l = lathe([(0.045, 0), (0.045, 0.06), (0.055, 0.07), (0.055, 0.1), (0.035, 0.11), (0.0, 0.11)], 12)
        for v in l.verts:
            x, y, z = v.co; px, py, pz = 0.09 + z, x, 0.42 + y; c, s = math.cos(yaw), math.sin(yaw); v.co = (px * c - py * s, px * s + py * c, pz)
        K.obj(l, M['paint'], (0.95, 0.2, 0.12) if yaw else (0.9, 0.85, 0.75))
    for k in range(6): a = k * np.pi / 3; K.obj(lathe([(0.012, 0), (0.012, 0.03)], 6, 0.13 * math.cos(a), 0.13 * math.sin(a), 0.04), M['galv'], GREY)


def bollard(K, M):
    K.obj(lathe([(0.0, 0), (0.09, 0), (0.09, 0.85), (0.075, 0.92), (0.0, 0.95)], 16), M['iron'], (0.18, 0.18, 0.2), 'cyl', 0.5)
    K.obj(lathe([(0.093, 0.7), (0.093, 0.76)], 16, close_top=False, close_bottom=False), M['smooth'], (0.95, 0.95, 0.92), 'cyl', 1.0)


def signpost(K, M, cell, shape):
    K.obj(lathe([(0.04, -0.3), (0.04, 2.75), (0.045, 2.77), (0.0, 2.8)], 12), M['galv'], GREY, 'cyl', 1.0)
    zc = 2.25; t = 0.02; fx = 0.06
    if shape == 'circle': out = [(0.36 * math.cos(a), zc + 0.36 * math.sin(a)) for a in np.linspace(0, 2 * np.pi, 32, endpoint=False)]; w = h = 0.72; oy = zc
    elif shape == 'tri': out = poly_round([(-0.45, zc - 0.33), (0.45, zc - 0.33), (0.0, zc + 0.45)], 0.05, 3); w = h = 0.9; oy = zc
    elif shape == 'oct': out = [(0.36 * math.cos(a), zc + 0.36 * math.sin(a)) for a in np.linspace(np.pi / 8, 2 * np.pi + np.pi / 8, 8, endpoint=False)]; w = h = 0.765; oy = zc
    else: out = poly_round([(-0.36, zc - 0.36), (0.36, zc - 0.36), (0.36, zc + 0.36), (-0.36, zc + 0.36)], 0.04, 2); w = h = 0.72; oy = zc
    if shape == 'diamond': out = [(0.36, zc), (0.0, zc + 0.36), (-0.36, zc), (0.0, zc - 0.36)]; out = poly_round(out, 0.03, 2)
    pl = prism(out, fx - t, fx, axis='x'); K.obj(pl, M['sign'], WHITE, 'sign', 1.0, 0.006, 2, 30, sign=sign_cell_uv(cell, 0.0, oy, w, h, fx))
    for z in (zc - 0.22, zc + 0.22):                                # clamps
        K.obj(bbox(0.02, 0, z, 0.05, 0.1, 0.04), M['galv'], GREY, 'box', 0.4, 0.006, 1)


def direction_board(K, M, cell):
    for y in (-0.8, 0.8): K.obj(lathe([(0.05, -0.3), (0.05, 3.0), (0.0, 3.03)], 12, 0, y), M['galv'], GREY, 'cyl', 1.0)
    zc = 2.35; W, H = 2.2, 1.1; out = poly_round([(-W / 2, zc - H / 2), (W / 2, zc - H / 2), (W / 2, zc + H / 2), (-W / 2, zc + H / 2)], 0.06, 2)
    K.obj(prism(out, 0.05, 0.075, axis='x'), M['sign'], WHITE, 'sign', 1.0, 0.006, 2, 30, sign=sign_cell_uv(cell, 0.0, zc, W, H, 0.075))
    for z in (zc - 0.35, zc + 0.35): K.obj(bbox(0.0, 0, z, 0.06, 2.0, 0.06), M['galv'], GREY, 'box', 1.0, 0.008, 1)


def power_pole(K, M):
    K.obj(lathe([(0.0, -0.5), (0.16, -0.5), (0.15, 3.0), (0.12, 9.6), (0.1, 9.75), (0.0, 9.8)], 14), M['wood'], (0.55, 0.45, 0.38), 'cylv', 1.4)
    K.obj(bbox(0.0, 0, 9.1, 0.11, 2.7, 0.12), M['wood'], (0.6, 0.5, 0.42), 'box', 1.2, 0.01, 2)
    for sg in (-1, 1): K.obj(sweep([(0.0, sg * 0.05, 8.5), (0.0, sg * 0.75, 9.06)], 0.025, 6), M['galv'], GREY)
    for y in (-1.15, 0.0, 1.15):
        ins = [(0.03, 0), (0.05, 0.02), (0.05, 0.05), (0.03, 0.06), (0.055, 0.08), (0.055, 0.11), (0.03, 0.12), (0.045, 0.14), (0.045, 0.17), (0.02, 0.19), (0.0, 0.2)]
        K.obj(lathe(ins, 10, 0, y, 9.16), M['plastic'], (0.85, 0.72, 0.55), 'cyl', 0.3)


def reflector_post(K, M):
    p = prism(poly_round([(-0.06, -0.05), (0.06, -0.05), (0.07, 0.03), (0.0, 0.06), (-0.07, 0.03)], 0.012, 2), -0.2, 1.0)
    for v in p.verts: x, y, z = v.co; v.co = (y, x, z)
    K.obj(p, M['smooth'], (0.92, 0.92, 0.9), 'box', 0.5)
    K.obj(bbox(0.06, 0, 0.8, 0.012, 0.1, 0.24), M['plastic'], (0.08, 0.08, 0.08)); K.obj(bbox(0.068, 0, 0.82, 0.006, 0.05, 0.1), M['lens'], (1.0, 0.45, 0.05))


def bus_shelter(K, M):
    W, D, H = 4.2, 1.6, 2.6
    for x in (-D / 2 + 0.05, D / 2 - 0.05):
        for y in (-W / 2 + 0.05, 0, W / 2 - 0.05):
            if x > 0 and y == 0: continue
            K.obj(bbox(x, y, H / 2, 0.08, 0.08, H), M['galv'], GREY, 'box', 1.0, 0.01, 2)
    roof = prism(poly_round([(-D / 2 - 0.25, -W / 2 - 0.2), (D / 2 + 0.35, -W / 2 - 0.2), (D / 2 + 0.35, W / 2 + 0.2), (-D / 2 - 0.25, W / 2 + 0.2)], 0.12, 3), H, H + 0.12)
    for v in roof.verts: v.co.z += (v.co.x) * -0.06
    K.obj(roof, M['galv'], (0.55, 0.57, 0.6), 'box', 1.5, 0.02, 2)
    K.obj(bbox(-D / 2 + 0.05, 0, H / 2 + 0.1, 0.012, W - 0.15, H - 0.4), M['glass'], WHITE)
    for y in (-W / 2 + 0.05, W / 2 - 0.05): K.obj(bbox(0, y, H / 2 + 0.1, D - 0.15, 0.012, H - 0.4), M['glass'], WHITE)
    K.obj(bbox(-D / 2 + 0.05, W / 2 - 0.62, H / 2 + 0.05, 0.12, 1.1, 1.75), M['galv'], GREY, 'box', 1.0, 0.01, 2)
    adv = prism(poly_round([(W / 2 - 1.12, 0.35), (W / 2 - 0.12, 0.35), (W / 2 - 0.12, 1.85), (W / 2 - 1.12, 1.85)], 0.02, 1), -D / 2 + 0.115, -D / 2 + 0.12, axis='x')
    K.obj(adv, M['sign'], WHITE, 'sign', 1.0, sign=sign_cell_uv(12, W / 2 - 0.62, 1.1, 1.0, 1.5, -D / 2 + 0.12))
    for x in np.linspace(-0.62, -0.38, 3): K.obj(bbox(x, -0.3, 0.48, 0.07, 2.0, 0.035), M['wood'], (0.95, 0.82, 0.68), 'box', 0.9, 0.008, 2)
    for y in (-1.2, 0.6): K.obj(bbox(-0.5, y, 0.24, 0.3, 0.05, 0.46), M['galv'], GREY, 'box', 1.0, 0.008, 1)
    K.obj(bbox(-0.3, 0, 0.04, D + 0.1, W + 0.2, 0.08), M['concrete'], (0.9, 0.9, 0.88), 'box', 1.5, 0.015, 2)


def jersey(K, M):
    out = poly_round([(-0.3, 0.0), (0.3, 0.0), (0.3, 0.08), (0.2, 0.25), (0.08, 0.8), (-0.08, 0.8), (-0.2, 0.25), (-0.3, 0.08)], 0.02, 2)
    b = prism([(x, z) for x, z in out], -1.5, 1.5, axis='x')
    for v in b.verts: x, y, z = v.co; v.co = (y, x, z)
    K.obj(b, M['concrete'], (0.92, 0.92, 0.9), 'box', 1.5, 0.012, 2)


def fence(K, M):
    for y in (-1.5, 0.0, 1.5): K.obj(bbox(0, y, 0.55, 0.1, 0.1, 1.3), M['wood'], (0.7, 0.6, 0.5), 'box', 1.0, 0.012, 2)
    for z in (0.45, 0.9): K.obj(bbox(0.07, 0, z, 0.04, 3.05, 0.12), M['wood'], (0.75, 0.65, 0.55), 'box', 1.2, 0.01, 2)


PROPS = {
    'lamp': (streetlamp, {}), 'signal': (signal, {}), 'bench': (bench, {}), 'bin': (litter_bin, {}), 'hydrant': (hydrant, {}), 'bollard': (bollard, {}),
    'sign_speed': (signpost, dict(cell=0, shape='circle')), 'sign_speed80': (signpost, dict(cell=1, shape='circle')), 'sign_curve': (signpost, dict(cell=3, shape='tri')),
    'sign_bend': (signpost, dict(cell=4, shape='tri')), 'sign_cross': (signpost, dict(cell=5, shape='tri')), 'sign_stop': (signpost, dict(cell=11, shape='oct')),
    'sign_priority': (signpost, dict(cell=10, shape='diamond')), 'sign_parking': (signpost, dict(cell=9, shape='square')),
    'board_a': (direction_board, dict(cell=6)), 'board_b': (direction_board, dict(cell=7)), 'board_c': (direction_board, dict(cell=8)),
    'power_pole': (power_pole, {}), 'reflector': (reflector_post, {}), 'shelter': (bus_shelter, {}), 'jersey': (jersey, {}), 'fence': (fence, {}),
}
HEIGHT = dict(container=2.6, lamp=8.4, signal=5.4, bench=0.9, bin=0.9, hydrant=0.8, bollard=1.0, power_pole=9.8, reflector=1.0, shelter=2.8, jersey=0.8, fence=1.2)


def build(M=None, names=None, lod1=0.35):
    """Returns {prop: dict(lod0=obj, lod1=obj, t0=, t1=, h=)}. Object names: PROP_<name>_LOD0 / _LOD1."""
    M = M or mats(); lib = {}
    for name, (fn, kw) in PROPS.items():
        if names and name not in names: continue
        e = {}
        global SEG, LOD
        for lod, seg in ((0, 20), (1, 20)):
            SEG = seg; LOD = lod; K = Part(); fn(K, M, **kw)
            groups = K.arrays()
            if lod == 1: groups = [g for g in groups if (np.sort(np.ptp(g[0], 0))[1] > 0.1 if name.startswith('house') else np.ptp(g[0], 0).max() > 0.09) or g[5] in (M['sign'], M['lens'])] or groups   # far copy drops bolts and tiny parts
            ob, nt = make_prop('%s%s_LOD%d' % (PREFIX, name, lod), groups); e['lod%d' % lod] = ob; e['t%d' % lod] = nt
        SEG = 20; LOD = 0; e['h'] = HEIGHT.get(name, 3.0); lib[name] = e
    return lib


def bake_ao(objs, out, samples=24, dist=1.6):
    """Ambient occlusion baked by Cycles into the vertex colours of each prop, on its own over a ground plane (cached by name and size)."""
    import os, time
    scn = bpy.context.scene; path = os.path.join(out, 'prop_ao_cache.npz'); cache = dict(np.load(path)) if os.path.exists(path) else {}
    todo = [o for o in objs if not (o.name in cache and len(cache[o.name]) == len(o.data.loops))]
    res = {o.name: cache[o.name] for o in objs if o not in todo}
    if todo:
        hid = [o for o in scn.objects if not o.hide_render]
        for o in hid: o.hide_render = True
        me = bpy.data.meshes.new('ao_ground'); me.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)]); gp = bpy.data.objects.new('ao_ground', me); scn.collection.objects.link(gp)
        old = (scn.render.engine, scn.cycles.samples); scn.render.engine = 'CYCLES'; scn.cycles.samples = samples; scn.render.bake.target = 'VERTEX_COLORS'
        if scn.world is None: scn.world = bpy.data.worlds.new('w')
        scn.world.light_settings.distance = dist; t0 = time.time()
        for o in todo:
            o.hide_render = False; loc = o.location.copy(); par = o.parent; mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw; o.location = (0, 0, 0)
            a = o.data.color_attributes.new('AO', 'FLOAT_COLOR', 'CORNER'); o.data.color_attributes.active_color = a
            for q in bpy.context.selected_objects: q.select_set(False)
            o.select_set(True); bpy.context.view_layer.objects.active = o
            try:
                bpy.ops.object.bake(type='AO'); v = np.empty(len(o.data.loops) * 4, np.float32); a.data.foreach_get('color', v); res[o.name] = v.reshape(-1, 4)[:, 0].copy()
            except Exception as e: print('ao bake failed', o.name, e)
            o.data.color_attributes.remove(o.data.color_attributes['AO']); o.data.color_attributes.active_color = o.data.color_attributes['Col']
            o.select_set(False); o.parent = par; o.matrix_world = mw; o.hide_render = True
        bpy.data.objects.remove(gp, do_unlink=True)
        for o in hid: o.hide_render = False
        scn.render.engine, scn.cycles.samples = old
        np.savez_compressed(path, **res); print('prop AO baked', len(todo), 'objects in %.0f s' % (time.time() - t0))
    for o in objs:
        if o.name not in res: continue
        me = o.data; ao = res[o.name]; li = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', li); nv = len(me.vertices)
        ao = (np.bincount(li, weights=ao, minlength=nv) / np.maximum(np.bincount(li, minlength=nv), 1))[li]            # per vertex, keeps vertices shared
        ca = me.color_attributes['Col']; c = np.empty(len(me.loops) * 4, np.float32); ca.data.foreach_get('color', c); c = c.reshape(-1, 4)
        c[:, :3] *= (0.38 + 0.62 * np.clip(ao, 0, 1) ** 0.85)[:, None]; ca.data.foreach_set('color', c.ravel())

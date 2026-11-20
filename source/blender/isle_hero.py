"""Hero city buildings for Aurelia Island, modelled from the approved elevation sheets (art sheet 01 / 02).

A  Corner apartment block   red brick, stone ground floor, cornice with dentils, iron balconies, Caffe Marina + Panificio Rossi
B  Art-deco office           cream ashlar piers, bronze spandrels, stepped crown with gold trim, gilded 3D lettering, canopied entrance
C  Modern glass office       blue-green curtain wall, aluminium mullions, concrete floor bands, double-height lobby, NORDA letters, roof screen
D  Townhouse row             three plaster houses (terracotta / ochre / harbour blue), green louvred shutters, clay roofs with dormers,
                             barber (with pole), pharmacy (green cross blade sign), florist (flower buckets)

Every building faces -Y (the street), its frontage runs along +X from x0, and it stands on z = 0.
Shop signs are individual textures painted here with real fonts; large lettering is real 3D text.
"""
import math
import numpy as np
import bpy
import bmesh
import isle_lib as L
import isle_props as P
from isle_houses import Frame, walls
from isle_props import bbox, lathe, prism
import isle_city as CI

FONTS = {'Lora': '/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf', 'Baskerville': '/usr/share/fonts/truetype/baskerville/GFSBaskerville.otf',
         'Inter': '/usr/share/fonts/opentype/inter/Inter-Bold.otf', 'InterX': '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'}
_SIGNS = {}


def hexc(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


class _Atlas:
    """All hero shop signs painted into one 2048 x 2048 atlas (rows of 128 px), one material for the whole city."""
    N = 2048; RH = 128
    def __init__(s): s.im = None; s.mask = None; s.x = 0; s.y = 0; s.cells = {}; s.mat = None


ATL = _Atlas()


def sign_mat(key, text, bg, fg, font, aspect, border=None, emit=1.2, italic=False):
    """Paint a sign into the shared atlas; returns (material, (u0, v0, u1, v1)) of its cell."""
    from PIL import Image, ImageDraw, ImageFont
    A = ATL
    if A.im is None: A.im = Image.new('RGB', (A.N, A.N), (40, 40, 40)); A.mask = Image.new('L', (A.N, A.N), 0)
    if key in A.cells: return _mat(), A.cells[key]
    Wp = int(min(1024, max(A.RH, A.RH * aspect))); Hp = A.RH
    if A.x + Wp > A.N: A.x = 0; A.y += A.RH
    x0, y0 = A.x, A.y; A.x += Wp + 4
    d = ImageDraw.Draw(A.im); dm = ImageDraw.Draw(A.mask)
    d.rectangle([x0, y0, x0 + Wp - 1, y0 + Hp - 1], fill=bg)
    if border: d.rectangle([x0 + 6, y0 + 6, x0 + Wp - 7, y0 + Hp - 7], outline=border, width=3)
    s = int(Hp * 0.62)
    while s > 10:
        f = ImageFont.truetype(FONTS[font], s)
        if d.textlength(text, font=f) < Wp * 0.86: break
        s -= 2
    tw = d.textlength(text, font=f); bb = d.textbbox((0, 0), text, font=f); th = bb[3] - bb[1]
    tx = x0 + (Wp - tw) / 2; ty = y0 + (Hp - th) / 2 - bb[1]
    d.text((tx, ty), text, font=f, fill=fg); dm.text((tx, ty), text, font=f, fill=255)
    N = A.N; cell = (x0 / N, 1 - (y0 + Hp) / N, (x0 + Wp) / N, 1 - y0 / N)            # image rows top-down -> uv bottom-up
    A.cells[key] = cell
    return _mat(), cell


def _mat():
    if ATL.mat is None:
        ATL.mat = L.new_mat('HeroSigns', 0.45, vcol=True); ATL.mat['night_emit'] = 1.2
    return ATL.mat


def finish_atlas():
    """Write the painted atlas into the shared material (call once after all hero buildings are built)."""
    if ATL.im is None or ATL.mat is None: return
    a = np.asarray(ATL.im, float)[::-1] / 255.0; m = np.asarray(ATL.mask, float)[::-1] / 255.0
    img = L.make_image('hero_signs', a); em = L.make_image('hero_signs_e', np.repeat(m[..., None], 3, 2))
    nt = ATL.mat.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
    old = [l for l in nt.links if l.to_socket == b.inputs['Base Color']]
    for l in old: nt.links.remove(l)
    vc = [n for n in nt.nodes if n.type in ('VERTEX_COLOR', 'ATTRIBUTE')]
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    te = nt.nodes.new('ShaderNodeTexImage'); te.image = em; nt.links.new(te.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 0.0


def sign_uv(F, u0, u1, z0, z1, cell=(0, 0, 1, 1)):
    cu0, cv0, cu1, cv1 = cell
    def f(Pt, ln):
        front = (ln @ F.n) > 0.5
        uu = np.clip(((Pt - F.o) @ F.u - u0) / (u1 - u0), 0, 1); vv = np.clip((Pt[:, 2] - z0) / (z1 - z0), 0, 1)
        return np.where(front[:, None], np.c_[cu0 + uu * (cu1 - cu0), cv0 + vv * (cv1 - cv0)], np.c_[uu * 0 + cu0 + 0.001, vv * 0 + cv0 + 0.001])
    return f


def text3d(text, font, size, depth=0.08):
    """Real 3D lettering (Blender text, converted to mesh): returns a bmesh in the text's local frame (x along, y up, z out)."""
    cu = bpy.data.curves.new('t', 'FONT'); cu.body = text; cu.size = size; cu.extrude = depth / 2; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    try: cu.font = bpy.data.fonts.load(FONTS[font], check_existing=True)
    except Exception: pass
    ob = bpy.data.objects.new('t', cu); bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me); bpy.data.objects.remove(ob); bpy.data.curves.remove(cu)
    return bm


def place_text(K, F, text, font, size, u, n, z, mat, col, depth=0.08):
    bm = text3d(text, font, size, depth)
    for v in bm.verts:
        x, y, zz = v.co; v.co = tuple(F.w(u + x, n + zz + depth / 2, z + y))
    K.obj(bm, mat, col, 'box', 1.0, 0.0, smooth=False)


def awning(K, M, F, a, b, zt, c1, c2, depth=1.3, stripes=True):
    """Fabric awning with alternating stripes and a scalloped valance, on two iron arms."""
    n = max(2, int((b - a) / 0.45)); us = np.linspace(a, b, n + 1)
    for i in range(n):
        col = c1 if (i % 2 == 0 or not stripes) else c2
        aw = prism([(0.12, zt + 0.02), (depth, zt - 0.55), (depth, zt - 0.62), (0.12, zt - 0.06)], us[i], us[i + 1], axis='x')
        for v in aw.verts: x_, y_, z_ = v.co; v.co = tuple(F.w(x_, y_, z_))
        K.obj(aw, M['fabric'], col, 'box', 0.8)
        sc = prism([(depth - 0.01, zt - 0.6), (depth + 0.01, zt - 0.6), (depth + 0.01, zt - 0.86), (depth - 0.01, zt - 0.86)], us[i] + 0.02, us[i + 1] - 0.02, axis='x')
        for v in sc.verts:
            x_, y_, z_ = v.co
            if z_ < zt - 0.8: z_ += 0.12 * (1 - math.sin(math.pi * (x_ - us[i]) / (us[i + 1] - us[i])))
            v.co = tuple(F.w(x_, y_, z_))
        K.obj(sc, M['fabric'], col, 'box', 0.8)
    for u in (a + 0.2, b - 0.2): K.obj(P.sweep([tuple(F.w(u, 0.1, zt - 0.75)), tuple(F.w(u, depth - 0.05, zt - 0.62))], 0.02, 5), M['iron'], (0.18, 0.18, 0.19))


def shop(K, M, F, a, b, gf, frame, sign, aw=None, door_at=0.62, goods=None):
    """Shop bay: stall riser, display glass with mullions, recessed door, painted timber fascia with the shop's own sign, awning."""
    w = b - a; z0 = 0.15; zt = gf - 1.05; ud = a + w * door_at
    K.obj(F.box(a, b, -0.34, -0.1, 0.0, z0 + 0.5), M['stone'], (0.72, 0.7, 0.67), 'box', 1.2)
    K.obj(F.box(a, b, -0.3, -0.28, z0 + 0.5, zt), M['winglass'], (1, 1, 1))
    for u in (a + 0.04, a + (ud - 0.6 - a) / 2, ud - 0.62, ud + 0.62, b - 0.04): K.obj(F.fin(u - 0.05, u + 0.05, -0.3, -0.16, z0 + 0.5, zt), M['pwood'], frame, smooth=False)
    K.obj(F.box(a, b, -0.3, -0.16, zt - 0.6, zt - 0.52), M['pwood'], frame); K.obj(F.box(a, b, -0.3, -0.16, z0 + 0.46, z0 + 0.54), M['pwood'], frame)
    K.obj(F.box(ud - 0.6, ud + 0.6, -0.42, -0.3, 0.0, zt), M['pwood'], frame)
    K.obj(F.box(ud - 0.5, ud + 0.5, -0.36, -0.35, 0.05, zt - 0.62), M['winglass'], (1, 1, 1))
    K.obj(CI.sweep_handle(F, ud + 0.32, -0.33, 1.1), M['galv'], (0.85, 0.85, 0.82))
    K.obj(F.box(a - 0.15, b + 0.15, -0.05, 0.1, zt, gf - 0.15), M['pwood'], frame, 'box', 1.0)                                   # fascia board
    K.obj(F.box(a - 0.2, b + 0.2, -0.05, 0.18, gf - 0.15, gf - 0.05), M['pwood'], frame)                                         # cornice moulding
    sm, cell = sign; K.obj(F.box(a + 0.15, b - 0.15, 0.1, 0.12, zt + 0.12, gf - 0.27), sm, (1, 1, 1), 'sign', 1.0, sign=sign_uv(F, a + 0.15, b - 0.15, zt + 0.12, gf - 0.27, cell))
    for u in (a - 0.15, b + 0.15): K.obj(F.box(u - 0.18, u + 0.18, -0.05, 0.16, 0.0, gf - 0.15), M['pwood'], frame, 'box', 1.0)   # pilasters
    if aw: awning(K, M, F, a + 0.1, b - 0.1, zt - 0.05, *aw)
    if goods: goods(K, M, F, a + 0.2, ud - 0.75, z0 + 0.55)


def goods_bread(K, M, F, a, b, z):
    K.obj(F.box(a, b, -0.75, -0.32, z, z + 0.08), M['wood'], (0.5, 0.36, 0.24))
    for i, u in enumerate(np.arange(a + 0.2, b - 0.1, 0.32)):
        bm = lathe([(0.0, 0.0), (0.13, 0.02), (0.12, 0.08), (0.0, 0.11)], 10, 0, 0, 0)
        for v in bm.verts: x, y, zz = v.co; v.co = tuple(F.w(u + x * 1.3, -0.5 + y * 0.7, z + 0.08 + zz + (i % 2) * 0.0))
        K.obj(bm, M['smooth'], (0.78, 0.5, 0.24) if i % 2 else (0.85, 0.6, 0.3))


def goods_flowers(K, M, F, a, b, z):
    rng = np.random.default_rng(3)
    for u in np.arange(a + 0.25, b, 0.55):
        for nn in (0.45, 0.95):
            bm = lathe([(0.0, 0.0), (0.16, 0.0), (0.19, 0.38), (0.0, 0.38)], 10, 0, 0, 0)
            for v in bm.verts: x, y, zz = v.co; v.co = tuple(F.w(u + x, nn + y, zz))
            K.obj(bm, M['galv'], (0.6, 0.62, 0.64))
            for k in range(7):
                c = [(0.9, 0.15, 0.25), (0.98, 0.78, 0.15), (0.98, 0.98, 0.95), (0.65, 0.3, 0.8), (1.0, 0.5, 0.2)][int(rng.integers(5))]
                bm = lathe([(0.0, 0.0), (0.05, 0.02), (0.0, 0.06)], 6, 0, 0, 0)
                ox, oy, oz = rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), rng.uniform(0.42, 0.62)
                for v in bm.verts: x, y, zz = v.co; v.co = tuple(F.w(u + ox + x, nn + oy + y, oz + zz))
                K.obj(bm, M['smooth'], c)
            bm = lathe([(0.0, 0.38), (0.13, 0.45), (0.0, 0.55)], 8, 0, 0, 0)
            for v in bm.verts: x, y, zz = v.co; v.co = tuple(F.w(u + x, nn + y, zz))
            K.obj(bm, M['plastic'], (0.2, 0.45, 0.15))


def balcony(K, M, F, a, b, z):
    K.obj(F.box(a - 0.15, b + 0.15, 0.0, 0.8, z - 0.18, z), M['stone'], (0.92, 0.9, 0.85), 'box', 1.2)
    for u in np.arange(a - 0.1, b + 0.12, 0.12): K.obj(F.box(u - 0.012, u + 0.012, 0.72, 0.75, z, z + 0.95), M['iron'], (0.12, 0.12, 0.13))
    K.obj(F.box(a - 0.12, b + 0.12, 0.7, 0.78, z + 0.93, z + 1.0), M['iron'], (0.12, 0.12, 0.13))
    for u in (a - 0.12, b + 0.12): K.obj(F.box(u - 0.012, u + 0.012, 0.0, 0.78, z + 0.93, z + 1.0), M['iron'], (0.12, 0.12, 0.13))
    for u in np.linspace(a, b, 3): K.obj(F.box(u - 0.08, u + 0.08, 0.0, 0.5, z - 0.4, z - 0.18), M['stone'], (0.9, 0.88, 0.84))   # corbels


def body(K, M, x0, W, D, h, mat, col, uvs=2.4, gf=None, fl=None, n=0, frame=(0.95, 0.94, 0.9), ww=1.3, wh=1.9):
    """Side and back walls (with a window grid when the floor layout is given) plus the roof slab; the street front is built separately."""
    for F, Ln in ((Frame((x0, (D + 0.4) / 2, 0), (0, -1, 0), (-1, 0, 0)), D - 0.4), (Frame((x0 + W, (D + 0.4) / 2, 0), (0, 1, 0), (1, 0, 0)), D - 0.4), (Frame((x0 + W / 2, D, 0), (-1, 0, 0), (0, 1, 0)), W)):
        holes = []; wins = []
        if n and gf is not None:
            nb = max(1, int((Ln - 1.0) / 3.5))
            for f in range(n):
                zb = gf + f * fl + 0.75
                for i in range(nb):
                    uc = -Ln / 2 + (i + 0.5) * Ln / nb; holes.append((uc - ww / 2, uc + ww / 2, zb, zb + wh)); wins.append((uc, zb))
        walls(K, M, F, Ln, 0.0, h, holes, col, 0.3, mat, 'box', uvs)
        for uc, zb in wins: CI.cwindow(K, M, F, uc, zb, ww, wh, frame, 0.3, lintel=False)
    K.obj(bbox(x0 + W / 2, D / 2, h + 0.1, W - 0.3, D - 0.3, 0.2), M['concrete'], (0.55, 0.55, 0.54), 'box', 3.0)


VAR_A = [dict(wall='brick2', shops=[('CAFFÈ MARINA', '#1f3d2f', '#f1e3c2', 'Lora', '#d4af5a'), ('Panificio Rossi', '#efe4cf', '#6b2c1f', 'Lora', None)]),
         dict(wall='brick4', shops=[('BAR CENTRALE', '#1d2b4a', '#f3ead9', 'InterX', None), ('Gelateria Sole', '#f6e7c4', '#b5462a', 'Lora', None)]),
         dict(wall='brick3', shops=[('TRATTORIA ONDA', '#7a1f1a', '#f6ecd8', 'Baskerville', '#e0c070'), ('Libreria Ponte', '#1d2b4a', '#efe6d2', 'Baskerville', None)])]
VAR_B = [dict(cream=(0.96, 0.8, 0.56), name='AURELIA  INSURANCE'), dict(cream=(0.93, 0.9, 0.84), name='BANCA  DEL  PORTO'), dict(cream=(0.9, 0.72, 0.55), name='PALAZZO  NETTUNO')]
VAR_C = [dict(glass=(0.18, 0.36, 0.4), name='NORDA', acc=(0.2, 0.75, 0.55)), dict(glass=(0.14, 0.24, 0.42), name='KAIRO', acc=(0.3, 0.55, 0.95)), dict(glass=(0.3, 0.26, 0.2), name='VELA', acc=(0.95, 0.6, 0.25))]
VAR_D = [[((0.78, 0.44, 0.31), 'BARBIERE 1962', '#1d2b4a', '#f3ead9', 'Inter', 'barber'), ((0.85, 0.68, 0.33), 'FARMACIA', '#f4f6f4', '#1c7a4c', 'InterX', 'pharm'), ((0.62, 0.71, 0.77), 'Fiori di Lucia', '#3c5a3a', '#f6efe0', 'Lora', 'florist')],
         [((0.86, 0.78, 0.6), 'OTTICA LUCE', '#2a2a2e', '#f2e6c8', 'InterX', None), ((0.72, 0.36, 0.3), 'Pasticceria Bea', '#f6e2e6', '#8a2e4a', 'Lora', None), ((0.55, 0.66, 0.55), 'FARMACIA', '#f4f6f4', '#1c7a4c', 'InterX', 'pharm')],
         [((0.62, 0.71, 0.77), 'Fiori di Lucia', '#3c5a3a', '#f6efe0', 'Lora', 'florist'), ((0.9, 0.8, 0.62), 'TABACCHI', '#1b1b1d', '#f4f1ea', 'InterX', None), ((0.8, 0.52, 0.42), 'BARBIERE 1962', '#1d2b4a', '#f3ead9', 'Inter', 'barber')]]
DIMS = {'A': (22.0, 14.0, 22.0), 'B': (24.0, 16.0, 37.0), 'C': (26.0, 18.0, 44.0), 'D': (22.2, 11.0, 17.5)}


def awn_cols(bg):
    c = hexc(bg); return (tuple(v * 0.9 for v in c), (0.95, 0.92, 0.86))


def building_A(K, M, x0=0.0, var=0, seed=1):
    V = VAR_A[var % 3]; wall = V['wall']; names = [(s[0][0],) + s[1:4] for s in V['shops']]
    rng = np.random.default_rng(seed); W, D, gf, fl, n = 22.0, 14.0, 4.6, 3.2, 5; h = gf + n * fl
    F = Frame((x0 + W / 2, 0, 0), (1, 0, 0), (0, -1, 0)); wm = M[wall]
    shops = [(-10.4, -0.6), (0.6, 10.4)]
    walls(K, M, F, W, 0.0, gf, [(a, b, 0.0, gf - 0.15) for a, b in shops], (0.85, 0.82, 0.77), 0.35, M['ashlar'], 'box', 1.6)
    for k, (nm, sbg, sfg, fnt, brd) in enumerate(V['shops']):
        fr = tuple(v * 0.75 for v in hexc(sbg if hexc(sbg)[0] + hexc(sbg)[1] < 1.6 else sfg))
        shop(K, M, F, *shops[k], gf, fr, sign_mat('A_' + nm, nm, sbg, sfg, fnt, 7.5, brd), awn_cols(sbg if sum(hexc(sbg)) < 1.8 else sfg), goods=goods_bread if 'Panific' in nm or 'Pasticc' in nm else None)
    K.obj(F.box(-W / 2 - 0.08, W / 2 + 0.08, -0.05, 0.3, gf - 0.05, gf + 0.45), M['stone'], (0.93, 0.9, 0.84), 'box', 1.4)       # band over the shops
    holes = []; wins = []
    for f in range(n):
        zb = gf + f * fl + 0.75
        for i in range(6):
            uc = -W / 2 + 1.2 + 0.725 + i * 3.55; holes.append((uc - 0.725, uc + 0.725, zb, zb + 1.95)); wins.append((uc, zb, f, i))
    walls(K, M, F, W, gf, h, holes, (1.0, 1.0, 1.0), 0.3, wm, 'box', 2.0)
    for uc, zb, f, i in wins:
        CI.cwindow(K, M, F, uc, zb, 1.45, 1.95, (0.95, 0.94, 0.9), 0.3, lintel=True)
        if f in (1, 3) and i in (0, 1, 4, 5) and i % 2 == 0: balcony(K, M, F, uc - 0.9, uc + 3.55 + 0.9, zb - 0.02)
    for f in range(1, n): K.obj(F.box(-W / 2, W / 2, -0.02, 0.08, gf + f * fl - 0.1, gf + f * fl + 0.1), M['stone'], (0.93, 0.9, 0.84), 'box', 1.4)
    CI.cornice(K, M, F, W, h, (0.94, 0.91, 0.85), 0.55)
    for u in np.arange(-W / 2 - 0.3, W / 2 + 0.35, 0.42): K.obj(F.box(u - 0.09, u + 0.09, 0.0, 0.3, h + 0.05, h + 0.22), M['stone'], (0.93, 0.9, 0.84))   # dentils
    K.obj(F.box(-W / 2, W / 2, -0.3, 0.0, h + 0.5, h + 1.2), wm, (1, 1, 1), 'box', 2.0); K.obj(F.box(-W / 2 - 0.05, W / 2 + 0.05, -0.35, 0.05, h + 1.2, h + 1.32), M['stone'], (0.92, 0.9, 0.85))
    body(K, M, x0, W, D, h + 1.2, wm, (1, 1, 1), 2.0, gf, fl, n, (0.95, 0.94, 0.9), 1.45, 1.95)
    CI.roof_plant(K, M, D, W, h + 0.2, rng) if False else None
    tx, ty = x0 + W * 0.68, 6.0                                                                         # rooftop water tank
    for dx, dy in ((-0.9, -0.9), (0.9, -0.9), (-0.9, 0.9), (0.9, 0.9)): K.obj(bbox(tx + dx, ty + dy, h + 1.3, 0.14, 0.14, 2.2), M['galv'], (0.5, 0.5, 0.5))
    K.obj(lathe([(1.3, 0), (1.3, 2.4), (1.0, 2.8), (0.0, 3.0)], 18, tx, ty, h + 2.3), M['planks'], (0.7, 0.55, 0.42), 'cylv', 2.0)
    for k in range(3): K.obj(bbox(x0 + 4 + k * 2.4, 7, h + 0.85, 1.8, 1.2, 1.2), M['galv'], (0.8, 0.82, 0.84), 'box', 1.0, 0.02, 1)
    K.obj(P.sweep([tuple(F.w(W / 2 - 0.4, 0.18, 0.2)), tuple(F.w(W / 2 - 0.4, 0.18, h + 0.4))], 0.07, 8), M['galv'], (0.4, 0.42, 0.44))     # drainpipe
    bl, bc = sign_mat('blade_' + names[0][0], names[0][0], names[0][1], names[0][2], names[0][3], 0.6)        # blade sign with the cafe's initial
    G = Frame(F.w(-1.0, 0.0, 0), F.n, -F.u)
    K.obj(G.box(0.15, 0.95, -0.06, 0.06, gf + 0.6, gf + 2.0), bl, (1, 1, 1), 'sign', 1.0, sign=sign_uv(Frame(G.o, G.u, G.n), 0.15, 0.95, gf + 0.6, gf + 2.0, bc))
    K.obj(G.box(0.0, 1.05, -0.03, 0.03, gf + 2.0, gf + 2.06), M['iron'], (0.15, 0.15, 0.15))
    return W


def building_B(K, M, x0=0.0, var=0, seed=2):
    V = VAR_B[var % 3]; W, D, gf, fl, n = 24.0, 16.0, 5.2, 3.6, 7; h = gf + n * fl
    F = Frame((x0 + W / 2, 0, 0), (1, 0, 0), (0, -1, 0)); cream = V['cream']; bronze = (0.3, 0.19, 0.08)
    ent = (-4.0, 4.0); side = [(-10.0, -5.0), (5.0, 10.0)]
    walls(K, M, F, W, 0.0, gf, [(ent[0], ent[1], 0.0, gf - 0.4)] + [(a, b, 0.9, gf - 1.2) for a, b in side], (0.8, 0.78, 0.72), 0.4, M['stone'], 'box', 2.0)
    K.obj(F.box(ent[0], ent[1], -0.38, -0.36, 0.0, gf - 0.4), M['winglass'], (1, 1, 1))
    for u in np.linspace(ent[0], ent[1], 5): K.obj(F.fin(u - 0.06, u + 0.06, -0.38, -0.25, 0.0, gf - 0.4), M['galv'], (0.85, 0.66, 0.3), smooth=False)
    K.obj(F.box(ent[0], ent[1], -0.38, -0.25, 3.0, 3.1), M['galv'], (0.85, 0.66, 0.3))
    for a, b in side:
        K.obj(F.box(a, b, -0.3, -0.28, 0.9, gf - 1.2), M['winglass'], (1, 1, 1))
        for u in np.linspace(a, b, 4): K.obj(F.fin(u - 0.05, u + 0.05, -0.3, -0.2, 0.9, gf - 1.2), M['galv'], (0.85, 0.66, 0.3), smooth=False)
    K.obj(F.box(ent[0] - 1.0, ent[1] + 1.0, 0.0, 2.2, gf - 0.45, gf - 0.25), M['smooth'], (0.12, 0.11, 0.1))                         # canopy
    for u in (ent[0] - 0.8, ent[1] + 0.8): K.obj(P.sweep([tuple(F.w(u, 2.0, gf - 0.3)), tuple(F.w(u, 0.0, gf + 0.9))], 0.03, 6), M['galv'], (0.85, 0.66, 0.3))
    K.obj(F.box(-8.6, 8.6, -0.02, 0.12, gf - 0.2, gf + 0.75), M['smooth'], (0.13, 0.12, 0.1))                                        # sign band
    place_text(K, F, V['name'], 'Baskerville', 0.62, 0.0, 0.12, gf + 0.27, M['galv'], (0.95, 0.75, 0.35), 0.06)
    bays = 6; bw = (W - 2.4) / bays; holes = []; wins = []
    for f in range(n):
        zb = gf + f * fl + 1.0
        for i in range(bays):
            a = -W / 2 + 1.2 + i * bw + 0.45; b = a + bw - 0.9; holes.append((a, b, zb - 0.95, zb + fl - 1.3)); wins.append((a, b, zb, fl - 1.3))
    walls(K, M, F, W, gf, h, holes, cream, 0.32, M['plaster2'], 'box', 2.6)
    for a, b, zb, wh in wins:
        K.obj(F.rect(a, b, -0.24, zb, zb + wh), M['winglass'], (1, 1, 1), smooth=False)
        for u in np.linspace(a, b, 4): K.obj(F.fin(u - 0.04, u + 0.04, -0.24, -0.16, zb, zb + wh), M['galv'], (0.42, 0.32, 0.18), smooth=False)
        K.obj(F.box(a, b, -0.24, -0.16, zb + wh * 0.72 - 0.03, zb + wh * 0.72 + 0.03), M['galv'], (0.42, 0.32, 0.18))
        K.obj(F.box(a, b, -0.2, -0.12, zb - 0.95, zb - 0.02), M['paint'], bronze)                                                    # bronze spandrel
        for u in np.linspace(a + 0.15, b - 0.15, 5): K.obj(F.box(u - 0.05, u + 0.05, -0.12, -0.07, zb - 0.9, zb - 0.1), M['paint'], (0.7, 0.5, 0.22))
    for i in range(bays + 1):                                                                           # piers, the ones beside the centre rise into the crown
        u = -W / 2 + 1.2 + i * bw; top = h + (2.8 if i in (2, 4) else 0.9)
        K.obj(F.box(u - 0.42, u + 0.42, 0.0, 0.35, gf, top), M['plaster2'], (0.98, 0.85, 0.62), 'box', 2.6, smooth=False)
    for (cw, ch, cd) in ((W * 0.44, 2.6, 0.4), (W * 0.26, 4.8, 1.2), (W * 0.11, 6.8, 2.0)):          # stepped crown with gold trim, each tier set back
        K.obj(bbox(x0 + W / 2, cd + (D - 4 - cd) / 2, h + ch / 2, cw, D - 4 - cd, ch), M['plaster2'], cream, 'box', 2.6)
        K.obj(F.box(-cw / 2 - 0.06, cw / 2 + 0.06, -cd - 0.02, -cd + 0.1, h + ch - 0.2, h + ch), M['galv'], (0.95, 0.75, 0.35))
    K.obj(lathe([(0.08, 0), (0.05, 3.5), (0.0, 3.6)], 8, x0 + W / 2, 4.0, h + 6.8), M['galv'], (0.6, 0.6, 0.6))
    K.obj(F.box(-W / 2 - 0.1, W / 2 + 0.1, -0.1, 0.25, h, h + 0.9), M['plaster2'], cream, 'box', 2.6)
    K.obj(F.box(-W / 2 - 0.12, W / 2 + 0.12, -0.12, 0.28, h + 0.9, h + 1.0), M['galv'], (0.95, 0.75, 0.35))
    body(K, M, x0, W, D, h + 0.9, M['plaster2'], cream, 2.6, gf, fl, n, (0.42, 0.32, 0.18), 1.6, 2.2)
    return W


def building_C(K, M, x0=0.0, var=0, seed=3):
    V = VAR_C[var % 3]; W, D, gf, fl, n = 26.0, 18.0, 7.0, 3.8, 9; h = gf + n * fl
    F = Frame((x0 + W / 2, 0, 0), (1, 0, 0), (0, -1, 0))
    K.obj(F.rect(-W / 2, W / 2, -0.25, gf, h), M['curtain'], tuple(min(1, v / 0.4) for v in V['glass']), smooth=False)                                    # curtain wall glass
    for u in np.linspace(-W / 2, W / 2, 14): K.obj(F.fin(u - 0.06, u + 0.06, -0.25, 0.08, gf, h), M['galv'], (0.7, 0.74, 0.77), smooth=False)
    for f in range(n + 1):
        z = gf + f * fl; K.obj(F.box(-W / 2 - 0.1, W / 2 + 0.1, -0.25, 0.18, z - 0.55, z), M['concrete2'], (0.88, 0.88, 0.86), 'box', 3.0)
    K.obj(F.box(-W / 2, W / 2, -0.3, 0.0, 0.0, 0.6), M['concrete2'], (0.85, 0.85, 0.83), 'box', 3.0)
    K.obj(F.box(-W / 2 + 1.5, W / 2 - 1.5, -0.6, -0.58, 0.6, gf - 0.6), M['winglass'], (1, 1, 1))                         # lobby glass
    for u in np.linspace(-W / 2 + 1.5, W / 2 - 1.5, 9): K.obj(F.fin(u - 0.07, u + 0.07, -0.6, -0.45, 0.6, gf - 0.6), M['galv'], (0.55, 0.58, 0.6), smooth=False)
    for u in (-W / 2, W / 2): K.obj(F.box(u - 0.6 if u > 0 else u, u if u > 0 else u + 0.6, -0.6, 0.15, 0.0, gf), M['concrete2'], (0.86, 0.86, 0.84), 'box', 3.0)
    K.obj(F.box(-W / 2, W / 2, -0.6, 0.15, gf - 0.6, gf), M['concrete2'], (0.86, 0.86, 0.84), 'box', 3.0)
    place_text(K, F, V['name'], 'InterX', 1.05, 0.0, 0.18, gf - 1.5, M['smooth'], (0.08, 0.18, 0.16), 0.12)
    K.obj(F.box(-3.4, 3.4, 0.15, 0.22, gf - 2.25, gf - 2.17), M['lens'], V['acc'])
    for u in np.linspace(-W * 0.35, W * 0.35, 46): K.obj(bbox(x0 + W / 2 + u, D * 0.45, h + 1.3, 0.08, D * 0.6, 2.6), M['galv'], (0.55, 0.58, 0.62))   # roof screen fins
    for Fs, Ln in ((Frame((x0, D / 2, 0), (0, -1, 0), (-1, 0, 0)), D), (Frame((x0 + W, D / 2, 0), (0, 1, 0), (1, 0, 0)), D), (Frame((x0 + W / 2, D, 0), (-1, 0, 0), (0, 1, 0)), W)):   # curtain wall on every side
        Fs2 = Frame(Fs.o, Fs.u, Fs.n)
        K.obj(Fs2.rect(-Ln / 2, Ln / 2, 0.0, 0.0, h), M['curtain'], tuple(min(1, v / 0.4) for v in V['glass']), smooth=False)
        for u in np.linspace(-Ln / 2, Ln / 2, max(2, int(Ln / 2.0)) + 1): K.obj(Fs2.fin(u - 0.06, u + 0.06, 0.0, 0.25, 0.0, h), M['galv'], (0.7, 0.74, 0.77), smooth=False)
        for f in range(n + 1):
            z = gf + f * fl; K.obj(Fs2.box(-Ln / 2, Ln / 2, 0.0, 0.3, z - 0.55, z), M['concrete2'], (0.88, 0.88, 0.86), 'box', 3.0)
    K.obj(bbox(x0 + W / 2, D / 2, h + 0.1, W - 0.3, D - 0.3, 0.2), M['concrete'], (0.55, 0.55, 0.54), 'box', 3.0)
    return W


def building_D(K, M, x0=0.0, var=0, seed=4):
    Wt, D, gf, fl, n = 7.4, 11.0, 4.2, 3.1, 3; h = gf + n * fl
    specs = []
    for (col, sign, sbg, sfg, font, kind) in VAR_D[var % 3]:
        dark = sbg if sum(hexc(sbg)) < 1.8 else sfg; fr = tuple(v * 0.8 for v in hexc(dark))
        specs.append((col, sign, sbg, sfg, font, None if kind == 'pharm' else awn_cols(dark), fr, kind))
    for i, (col, sign, sbg, sfg, font, aw, frame, kind) in enumerate(specs):
        xc = x0 + i * Wt; hh = h + (0.6 if i == 1 else 0.0); F = Frame((xc + Wt / 2, 0, 0), (1, 0, 0), (0, -1, 0))
        walls(K, M, F, Wt, 0.0, gf, [(-3.2, 3.2, 0.0, gf - 0.15)], col, 0.3, M['plaster2'], 'box', 2.8)
        shop(K, M, F, -3.2, 3.2, gf, frame, sign_mat('D_' + sign, sign, sbg, sfg, font, 6.0), aw, goods=goods_flowers if kind == 'florist' else (goods_bread if kind is None and 'Pastic' in sign else None))
        holes = []; wins = []
        for f in range(n):
            zb = gf + f * fl + 0.7
            for uc in (-1.45, 1.45): holes.append((uc - 0.62, uc + 0.62, zb, zb + 1.9)); wins.append((uc, zb, f))
        walls(K, M, F, Wt, gf, hh, holes, col, 0.3, M['plaster2'], 'box', 2.8)
        for uc, zb, f in wins:
            CI.cwindow(K, M, F, uc, zb, 1.24, 1.9, (0.96, 0.95, 0.92), 0.3, lintel=False)
            for s in (-1, 1):                                                                       # louvred shutters, folded open
                a = uc + s * 0.62 if s > 0 else uc - 0.62 - 0.6; b = a + 0.6
                K.obj(F.box(a, b, 0.0, 0.05, zb, zb + 1.9), M['pwood'], (0.18, 0.36, 0.22), 'box', 1.0)
                for z in np.arange(zb + 0.12, zb + 1.85, 0.11): K.obj(F.box(a + 0.05, b - 0.05, 0.05, 0.075, z - 0.025, z + 0.015), M['pwood'], (0.15, 0.31, 0.19))
            if f == 0: balcony(K, M, F, uc - 0.75, uc + 0.75, zb - 0.02)
        K.obj(F.box(-Wt / 2, Wt / 2, -0.02, 0.1, gf - 0.08, gf + 0.12), M['stone'], (0.93, 0.9, 0.84), 'box', 1.4)
        K.obj(F.box(-Wt / 2 - 0.05, Wt / 2 + 0.05, -0.05, 0.35, hh - 0.05, hh + 0.25), M['stone'], (0.95, 0.93, 0.88), 'box', 1.4)    # eaves
        for j, (F2, Ln) in enumerate(((Frame((xc, (D + 0.4) / 2, 0), (0, -1, 0), (-1, 0, 0)), D - 0.4), (Frame((xc + Wt, (D + 0.4) / 2, 0), (0, 1, 0), (1, 0, 0)), D - 0.4), (Frame((xc + Wt / 2, D, 0), (-1, 0, 0), (0, 1, 0)), Wt))):
            outer = (j == 0 and i == 0) or (j == 1 and i == 2) or j == 2                         # end walls of the row and the backs get windows
            hl = []; wl = []
            if outer:
                for f in range(n):
                    zb = gf + f * fl + 0.7
                    for uc in ((-Ln / 4, Ln / 4) if Ln > 6 else (0.0,)): hl.append((uc - 0.6, uc + 0.6, zb, zb + 1.8)); wl.append((uc, zb))
            walls(K, M, F2, Ln, 0.0, hh, hl, col, 0.3, M['plaster2'], 'box', 2.8)
            for uc, zb in wl: CI.cwindow(K, M, F2, uc, zb, 1.2, 1.8, (0.96, 0.95, 0.92), 0.3, lintel=False)
        rh = 3.6; ov = 0.45                                                                         # clay-tile roof, ridge along the street, gable ends
        rf = prism([(-ov, hh - 0.15), (D / 2, hh + rh), (D + ov, hh - 0.15), (D + ov, hh + 0.05), (D / 2, hh + rh + 0.2), (-ov, hh + 0.05)], xc - 0.1, xc + Wt + 0.1, axis='x')
        for v in rf.verts: x_, y_, z_ = v.co; v.co = (x_, y_, z_)
        K.obj(rf, M['roof'], (0.86, 0.48, 0.34), 'roof', 1.0)
        for xx in (xc, xc + Wt):
            gb = prism([(0.0, hh), (D / 2, hh + rh - 0.1), (D, hh)], xx - 0.15, xx + 0.15, axis='x'); K.obj(gb, M['plaster2'], col, 'box', 2.8)
        dx = xc + Wt / 2; dy = D / 2 * 0.42; dz = hh + rh * 0.42                                        # dormer
        K.obj(bbox(dx, dy + 0.6, dz + 0.6, 1.8, 1.4, 1.4), M['plaster2'], col, 'box', 2.8)
        Fd = Frame((dx, dy - 0.11, 0), (1, 0, 0), (0, -1, 0)); CI.cwindow(K, M, Fd, 0.0, dz + 0.1, 0.9, 1.0, (0.96, 0.95, 0.92), 0.2, lintel=False)
        dr = prism([(-1.05, dz + 1.25), (0.0, dz + 1.8), (1.05, dz + 1.25), (1.05, dz + 1.35), (0.0, dz + 1.92), (-1.05, dz + 1.35)], dy - 0.25, dy + 1.4, axis='x')
        for v in dr.verts: X_, U_, Z_ = v.co; v.co = (dx + U_, X_, Z_)
        K.obj(dr, M['roof'], (0.8, 0.45, 0.32), 'roof', 1.0)
        if i != 1: K.obj(bbox(xc + Wt * 0.8, D * 0.7, hh + rh * 0.7 + 0.8, 0.7, 0.9, 2.6), M['brick2'], (1, 1, 1), 'box', 1.5)
        if kind == 'barber':                                                                        # barber pole
            px, py = xc + Wt - 0.3, -0.35
            for k in range(10): K.obj(lathe([(0.11, 0.0), (0.11, 0.12), (0.0, 0.12)], 12, px, py, 1.9 + k * 0.12), M['smooth'], [(0.85, 0.12, 0.12), (0.97, 0.97, 0.96), (0.12, 0.22, 0.55)][k % 3])
            K.obj(lathe([(0.0, 0.0), (0.13, 0.05), (0.0, 0.12)], 12, px, py, 3.1), M['galv'], (0.8, 0.8, 0.8))
        if kind == 'pharm':                                                                         # green cross blade sign
            G = Frame(F.w(Wt / 2 - 0.6, 0.0, 0), F.n, -F.u); 
            K.obj(G.box(0.2, 1.1, -0.07, 0.07, gf + 0.2, gf + 1.1), M['lens'], (0.15, 0.7, 0.4))
            for (a, b, z0_, z1_) in ((0.55, 0.75, gf + 0.3, gf + 1.0), (0.3, 1.0, gf + 0.55, gf + 0.75)): K.obj(G.box(a, b, -0.09, 0.09, z0_, z1_), M['lens'], (0.9, 1.0, 0.95))
            K.obj(G.box(0.0, 0.25, -0.03, 0.03, gf + 0.6, gf + 0.7), M['iron'], (0.15, 0.15, 0.15))
    return 3 * Wt


def hero_materials(M):
    if 'curtain' not in M:
        M['curtain'] = L.new_mat('HeroCurtain', 0.05, 0.6, color=(0.18, 0.36, 0.4))
    return M


class Rotated:
    """Wraps a Part built facing -Y (frontage along X, depth 0..D along +Y) so it faces +X centred on the origin."""
    def __init__(s, K, D): s.K = K; s.D = D

    def arrays(s):
        out = []
        for Pq, T, N, U, Cq, mt in s.K.arrays():
            x, y = Pq[:, 0], Pq[:, 1] - s.D / 2
            P2 = np.c_[-y, x, Pq[:, 2]]; N2 = np.c_[-N[:, 1], N[:, 0], N[:, 2]]
            out.append((P2, T, N2, U, Cq, mt))
        return out

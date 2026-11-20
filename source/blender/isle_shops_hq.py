"""Art sheet 10: city street level. Storefront kit that replaces the dark shop bays of the city blocks and the black ground floor of
the glass towers: pilasters, stall risers, framed glazing in front of a lit painted interior, recessed doors, fascia signs with original
shop names, awnings, blade signs, gooseneck lamps and the pavement life in front (cafe tables, planters, A-boards, produce crates).
Frame convention as isle_city.shopfront: F has u along the wall, n outward, z up; the bay runs u = a..b, ground floor height gf."""
import math
import numpy as np
import bmesh
import isle_props as P
from isle_props import bbox, lathe, sweep, prism
from isle_houses import Frame

# ------------------------------------------------------------------ atlases (original names, painted here)
SHOPS = [  # name, sub, bg, fg, serif, interior cell
    ('Caffè Marina', 'espresso · dolci', (24, 58, 52), (236, 214, 160), True, 0),
    ('LUNA', 'boutique', (20, 20, 22), (240, 236, 228), False, 1),
    ('Farmacia', 'Aurelia', (238, 240, 236), (20, 120, 70), False, 2),
    ('Trattoria Sole', 'cucina di casa', (120, 34, 26), (246, 222, 170), True, 3),
    ('Panetteria', 'Nonna Rosa', (232, 214, 178), (110, 60, 30), True, 0),
    ('MERCATO', 'frutta · verdura', (30, 92, 48), (250, 246, 230), False, 2),
    ('Banca dell\'Isola', '', (60, 62, 66), (226, 200, 140), True, 1),
    ('Gelateria Onda', 'artigianale', (246, 210, 214), (150, 40, 80), True, 3),
    ('Libreria Faro', 'libri · mappe', (26, 52, 92), (240, 232, 210), True, 2),
    ('OTTICA', 'occhiali', (240, 240, 240), (30, 30, 34), False, 1),
    ('Fiori Bella', 'fiorista', (246, 236, 220), (60, 110, 50), True, 0),
    ('BICI', 'riparazioni', (230, 160, 30), (20, 20, 22), False, 2),
    ('Pizzeria Vesta', 'forno a legna', (24, 24, 26), (240, 120, 40), True, 3),
    ('TABACCHI', 'giornali', (24, 40, 110), (245, 245, 245), False, 2),
    ('Studio Nove', 'parrucchiere', (220, 220, 214), (40, 40, 44), False, 1),
    ('Enoteca', 'vini dell\'isola', (70, 20, 34), (232, 210, 160), True, 3),
]
INTERIOR_OF = [s[5] for s in SHOPS]


def _font(serif, size, bold=True):
    from PIL import ImageFont
    for f in ((['/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Bold.ttf', '/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf'] if serif else
               ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'])):
        try: return ImageFont.truetype(f, size)
        except Exception: pass
    return ImageFont.load_default()


def sign_atlas(N=2048):
    """4 x 4 cells; each shop's fascia is drawn in the middle 512 x 128 band of its cell (the band the 4:1 sign quad samples)."""
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (N, N), (30, 30, 30)); d = ImageDraw.Draw(im); c = N // 4; bh = c // 4
    for i, (nm, sub, bg, fg, serif, _) in enumerate(SHOPS):
        x, y = (i % 4) * c, (i // 4) * c; d.rectangle([x, y, x + c - 1, y + c - 1], fill=bg)
        y0 = y + (c - bh) // 2; d.rectangle([x + 6, y0 + 6, x + c - 7, y0 + bh - 7], outline=fg, width=3)
        for sz in range(84, 20, -2):                                                  # largest size that fits the band
            f = _font(serif, sz); bb = d.textbbox((0, 0), nm, font=f)
            if bb[2] - bb[0] <= c - 60 and bb[3] - bb[1] <= (bh * 0.52 if sub else bh * 0.66): break
        d.text((x + c // 2, y0 + bh // 2 - (14 if sub else 0)), nm, fill=fg, font=f, anchor='mm')
        if sub: d.text((x + c // 2, y0 + bh - 22), sub.upper(), fill=fg, font=_font(False, 20, False), anchor='mm')
    return (np.asarray(im, float) / 255.0)[::-1]


def interior_atlas(N=1024):
    """2 x 2 painted shop interiors seen through the glass: cafe counter, clothes rails, shelves, dining room."""
    from PIL import Image, ImageDraw, ImageFilter
    r = np.random.default_rng(4); im = Image.new('RGB', (N, N)); d = ImageDraw.Draw(im); h = N // 2
    def room(x0, y0, wall, floor):
        d.rectangle([x0, y0, x0 + h, y0 + h], fill=wall); d.rectangle([x0, y0 + int(h * 0.72), x0 + h, y0 + h], fill=floor)
        for k in range(5):                                                       # pendant / ceiling lights
            cx = x0 + 40 + k * (h - 80) // 4; d.ellipse([cx - 16, y0 + 18, cx + 16, y0 + 34], fill=(255, 236, 190))
    # 0 cafe: counter, back bar with bottles, menu boards
    room(0, 0, (120, 84, 56), (70, 52, 40))
    d.rectangle([20, 70, h - 20, 150], fill=(30, 30, 28)); [d.text((40 + k * 150, 90), 'MENU', fill=(240, 230, 210)) for k in range(3)]
    for k in range(40): x = 24 + k * 12; d.rectangle([x, 170, x + 7, 200 + (k % 3) * 6], fill=tuple(int(v) for v in r.integers(60, 230, 3)))
    d.rectangle([10, 250, h - 10, 370], fill=(64, 44, 30)); d.rectangle([10, 250, h - 10, 262], fill=(200, 180, 150))
    d.rectangle([300, 210, 360, 250], fill=(170, 170, 175))
    # 1 boutique: white walls, rails of clothes, mannequins
    room(h, 0, (232, 228, 222), (180, 170, 160))
    for rail in range(2):
        y = 120 + rail * 90; d.line([h + 30, y, h + h - 30, y], fill=(60, 60, 60), width=4)
        for k in range(22): x = h + 40 + k * 20; d.rectangle([x, y + 4, x + 14, y + 70], fill=tuple(int(v) for v in r.integers(40, 220, 3)))
    for k in range(3): x = h + 90 + k * 150; d.ellipse([x - 14, 250, x + 14, 278], fill=(220, 210, 200)); d.rectangle([x - 22, 278, x + 22, 360], fill=tuple(int(v) for v in r.integers(30, 200, 3)))
    # 2 shelves: pharmacy / market / books
    room(0, h, (226, 232, 230), (150, 150, 146))
    for row in range(6):
        y = h + 60 + row * 52; d.rectangle([20, y + 40, h - 20, y + 46], fill=(120, 110, 100))
        for k in range(36): x = 24 + k * 13; d.rectangle([x, y + 8 + (k % 4) * 3, x + 10, y + 40], fill=tuple(int(v) for v in r.integers(50, 240, 3)))
    # 3 dining room: tables with cloths, warm walls, framed pictures
    room(h, h, (150, 70, 44), (90, 60, 44))
    for k in range(3): x = h + 70 + k * 150; d.rectangle([x - 40, h + 70, x + 40, h + 130], fill=(220, 200, 160)); d.rectangle([x - 34, h + 76, x + 34, h + 124], fill=tuple(int(v) for v in r.integers(40, 180, 3)))
    for k in range(4): x = h + 60 + k * 125; d.rectangle([x - 46, h + 300, x + 46, h + 320], fill=(245, 245, 240)); d.rectangle([x - 4, h + 320, x + 4, h + 380], fill=(60, 40, 30))
    im = im.filter(ImageFilter.GaussianBlur(1.6))                                  # seen through glass and a little out of focus
    return (np.asarray(im, float) / 255.0)[::-1]


def mats(M):
    if 'shopsign' in M: return M
    import isle_lib as L
    for key, name, img, em in (('shopsign', 'KitShopSign', sign_atlas(), 0.25), ('shopin', 'KitShopInterior', interior_atlas(), 1.3)):
        m = L.new_mat(name, 0.5, 0.0, image=L.make_image('kit_' + key + '_atlas', img), vcol=True); b = m.node_tree.nodes['Principled BSDF']
        tx = [n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE'][0]; m.node_tree.links.new(tx.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = em
        M[key] = m
    M['shopglass'] = L.new_mat('KitShopGlass', 0.03, 0.0, color=(0.05, 0.06, 0.065), alpha=0.22, vcol=False, double=True)
    return M


def _cell_quad(K, M, F, u0, u1, n, z0, z1, mat, cell, grid, aspect=1.0):
    """Quad facing +n, UV-mapped to an atlas cell (grid x grid); aspect < 1 uses the top part of the cell only (fascia 4:1)."""
    cu, cv = (cell % grid) / grid, (grid - 1 - cell // grid) / grid; s = 1.0 / grid
    def uvf(Pq, ln):
        Q = Pq - F.o; uu = Q @ F.u; zz = Q[:, 2]
        v0 = cv + s * (1 - aspect) * 0.5
        return np.c_[cu + 0.004 + (uu - u0) / (u1 - u0) * (s - 0.008), v0 + 0.004 + (zz - z0) / (z1 - z0) * (s * aspect - 0.008)]
    K.obj(F.rect(u0, u1, n, z0, z1), M[mat], (1, 1, 1), 'sign', 1.0, smooth=False, sign=uvf)


# ------------------------------------------------------------------ the storefront
STYLES = {  # frame colour, frame material, riser material/colour, pilaster material/colour, awning colours (None = none)
    'cafe': ((0.08, 0.22, 0.18), 'pwood', 'stone', (0.82, 0.8, 0.76), 'ashlar', (0.9, 0.86, 0.78), ((0.12, 0.3, 0.24), (0.92, 0.88, 0.78))),
    'boutique': ((0.04, 0.04, 0.045), 'smooth', 'stone', (0.15, 0.15, 0.16), 'stone', (0.2, 0.2, 0.21), None),
    'pharmacy': ((0.92, 0.92, 0.9), 'smooth', 'stone', (0.7, 0.72, 0.7), 'plaster', (0.9, 0.9, 0.88), None),
    'trattoria': ((0.36, 0.16, 0.09), 'pwood', 'brick', (0.7, 0.5, 0.4), 'brick', (0.75, 0.55, 0.42), ((0.6, 0.12, 0.08), (0.95, 0.9, 0.8))),
    'bakery': ((0.62, 0.48, 0.3), 'pwood', 'pwood', (0.55, 0.42, 0.28), 'plaster', (0.94, 0.88, 0.76), ((0.94, 0.9, 0.8), (0.75, 0.45, 0.22))),
    'market': ((0.1, 0.32, 0.16), 'smooth', 'concrete', (0.6, 0.6, 0.58), 'plaster', (0.86, 0.84, 0.8), ((0.1, 0.36, 0.18), (0.95, 0.95, 0.92))),
    'gelateria': ((0.9, 0.62, 0.7), 'pwood', 'stone', (0.94, 0.9, 0.86), 'plaster', (0.98, 0.92, 0.88), ((0.95, 0.75, 0.8), (0.98, 0.97, 0.95))),
    'books': ((0.06, 0.18, 0.32), 'pwood', 'pwood', (0.06, 0.18, 0.32), 'ashlar', (0.86, 0.82, 0.74), None),
}
STYLE_OF = {0: 'cafe', 1: 'boutique', 2: 'pharmacy', 3: 'trattoria', 4: 'bakery', 5: 'market', 6: 'boutique', 7: 'gelateria', 8: 'books', 9: 'boutique',
            10: 'bakery', 11: 'market', 12: 'trattoria', 13: 'books', 14: 'boutique', 15: 'trattoria'}


def storefront(K, M, F, a, b, gf, rng, door=True, shop=None, extras=True):
    """One shop bay from u=a to u=b on wall frame F (outer face n=0), ground floor height gf."""
    mats(M)
    shop = int(rng.integers(len(SHOPS))) if shop is None else shop; st = STYLES[STYLE_OF[shop]]
    fcol, fmat, rmat, rcol, pmat, pcol, awn = st; fmat = M[fmat]; w = b - a; uc = (a + b) / 2
    zt = min(gf - 1.15, 3.3); depth = 1.8; pw = 0.42
    # pilasters and fascia
    for u0, u1 in ((a, a + pw), (b - pw, b)):
        K.obj(F.box(u0, u1, 0.0, 0.22, 0.0, gf - 0.05), M[pmat], pcol, 'box', 1.6, 0.02, 2)
        K.obj(F.box(u0 - 0.03, u1 + 0.03, 0.0, 0.26, 0.0, 0.35), M['stone'], np.asarray(pcol) * 0.85, 'box', 1.2, 0.01, 1)
    K.obj(F.box(a, b, 0.0, 0.3, zt + 0.1, gf - 0.1), fmat, fcol, 'box', 1.0, 0.02, 2)
    K.obj(F.box(a - 0.05, b + 0.05, 0.0, 0.42, gf - 0.12, gf + 0.05), M['stone'], (0.88, 0.86, 0.82), 'box', 1.2, 0.02, 2)
    sw = min(w - 2 * pw - 0.3, 6.5); sh_ = min(gf - 0.4 - zt, sw / 4); zc_ = (zt + gf) / 2; _cell_quad(K, M, F, uc - sh_ * 2, uc + sh_ * 2, 0.31, zc_ - sh_ / 2, zc_ + sh_ / 2, 'shopsign', shop, 4, 0.25)
    for u in np.linspace(uc - sw / 2 + 0.4, uc + sw / 2 - 0.4, max(2, int(sw / 2.2) + 1)):           # gooseneck lamps over the sign
        K.obj(sweep([tuple(F.w(u, 0.3, gf - 0.12)), tuple(F.w(u, 0.7, gf + 0.15)), tuple(F.w(u, 0.85, gf - 0.05))], 0.018, 5), M['iron'], (0.08, 0.08, 0.08))
        K.obj(lathe([(0.0, -0.1), (0.12, -0.12), (0.06, 0.0), (0.0, 0.0)], 10, *F.w(u, 0.85, 0)[:2], gf - 0.05), M['iron'], (0.08, 0.08, 0.08))
        K.obj(lathe([(0.1, -0.13), (0.0, -0.12)], 10, *F.w(u, 0.85, 0)[:2], gf - 0.05), M['lens'], (1.0, 0.85, 0.55))
    # glazing bays, risers, mullions; door at one side or the middle
    du = (a + pw + 0.75) if (door and rng.random() < 0.5) else uc
    spans = [(a + pw, du - 0.75), (du + 0.75, b - pw)] if door else [(a + pw, b - pw)]
    for s0, s1 in spans:
        if s1 - s0 < 0.3: continue
        K.obj(F.box(s0, s1, -0.18, 0.06, 0.0, 0.55), M[rmat], rcol, 'box', 1.2, 0.015, 2)
        K.obj(F.box(s0, s1, -0.18, 0.1, 0.55, 0.62), M['stone'], (0.9, 0.88, 0.84), 'box', 1.2)
        K.obj(F.box(s0, s1, -0.14, -0.12, 0.62, zt), M['shopglass'], (1, 1, 1))
        n = max(1, int((s1 - s0) / 1.5))
        for i in range(n + 1): u = s0 + (s1 - s0) * i / n; K.obj(F.fin(u - 0.05, u + 0.05, -0.14, -0.04, 0.62, zt), fmat, fcol, smooth=False)
        for zz in (0.62, zt - 0.55, zt): K.obj(F.box(s0, s1, -0.14, -0.04, zz - 0.04, zz + 0.04), fmat, fcol)
    if door:                                                                                          # recessed glazed door
        K.obj(F.box(du - 0.75, du + 0.75, -0.9, -0.88, 0.0, zt + 0.05), fmat, fcol)
        K.obj(F.box(du - 0.6, du + 0.6, -0.88, -0.86, 0.08, zt - 0.6), M['shopglass'], (1, 1, 1))
        K.obj(F.box(du - 0.75, du + 0.75, -0.9, 0.0, 0.0, 0.03), M['stone'], (0.6, 0.58, 0.55), 'box', 1.0)
        for sg in (-1, 1): K.obj(F.box(du + sg * 0.75 - (0.02 if sg > 0 else 0), du + sg * 0.75 + (0.0 if sg > 0 else 0.02), -0.9, -0.14, 0.0, zt), fmat, fcol)
        K.obj(sweep([tuple(F.w(du + 0.45, -0.84, 0.9)), tuple(F.w(du + 0.45, -0.84, 1.5))], 0.02, 6), M['galv'], (0.85, 0.75, 0.5))
    # the lit room behind the glass: back wall picture, ceiling with light strips, floor, side walls
    ic = INTERIOR_OF[shop]; _cell_quad(K, M, F, a + pw, b - pw, -depth, 0.0, zt + 0.2, 'shopin', ic, 2)
    K.obj(F.box(a + pw, b - pw, -depth, -0.14, zt + 0.2, zt + 0.25), M['smooth'], (0.9, 0.88, 0.84))
    for u in np.linspace(a + pw + 0.8, b - pw - 0.8, max(2, int(w / 2.5))): K.obj(F.box(u - 0.5, u + 0.5, -1.0, -0.6, zt + 0.17, zt + 0.19), M['lens'], (1.0, 0.92, 0.75))
    K.obj(F.box(a + pw, b - pw, -depth, -0.14, -0.02, 0.0), M['planks'], (0.5, 0.4, 0.3), 'box', 1.0)
    for u0 in (a + pw, b - pw): K.obj(F.rect(-depth, -0.14, u0, 0, 0) if False else F.box(u0 - 0.01, u0 + 0.01, -depth, -0.14, 0.0, zt + 0.2), M['plaster'], (0.85, 0.8, 0.72))
    # awning, blade sign, pavement life
    if awn is not None:
        c1, c2 = awn; ns = max(4, int((b - a - 2 * pw) / 0.5)); us = np.linspace(a + pw, b - pw, ns + 1)
        for i in range(ns):
            aw = prism([(0.32, zt + 0.08), (1.9, zt - 0.62), (1.9, zt - 0.66), (0.32, zt + 0.04)], us[i], us[i + 1], axis='x')
            for v in aw.verts: x_, y_, z_ = v.co; v.co = tuple(F.w(x_, y_, z_))
            K.obj(aw, M['fabric'], c1 if i % 2 == 0 else c2, 'box', 0.8)
            K.obj(F.box(us[i], us[i + 1], 1.88, 1.92, zt - 0.9, zt - 0.62), M['fabric'], c1 if i % 2 == 0 else c2, 'box', 0.8)        # valance
        for u in (a + pw + 0.15, b - pw - 0.15): K.obj(sweep([tuple(F.w(u, 0.3, zt - 0.7)), tuple(F.w(u, 1.85, zt - 0.66))], 0.02, 5), M['iron'], (0.15, 0.15, 0.15))
    if extras and STYLE_OF[shop] in ('pharmacy', 'books', 'trattoria', 'cafe') and w > 4:              # blade sign on a bracket
        ub = b - pw / 2; K.obj(sweep([tuple(F.w(ub, 0.22, zt + 0.45)), tuple(F.w(ub, 1.3, zt + 0.45))], 0.025, 5), M['iron'], (0.1, 0.1, 0.1))
        if STYLE_OF[shop] == 'pharmacy':
            for (du_, dz_, ww, hh) in ((0.0, 0.0, 0.7, 0.24), (0.0, 0.0, 0.24, 0.7)): K.obj(bbox(*F.w(ub, 0.85, 0)[:2], zt + dz_ - 0.05, 0.08, ww, hh) if False else F.box(ub - 0.04, ub + 0.04, 0.85 - ww / 2, 0.85 + ww / 2, zt - 0.1 - hh / 2, zt - 0.1 + hh / 2), M['lens'], (0.15, 0.95, 0.4))
        else:
            K.obj(F.box(ub - 0.04, ub + 0.04, 0.4, 1.25, zt - 0.55, zt + 0.35), fmat, fcol, 'box', 1.0, 0.01, 1)
    if extras:
        s_ = STYLE_OF[shop]; rr = np.random.default_rng(shop * 7 + int(abs(a) * 3))
        if s_ in ('cafe', 'gelateria', 'trattoria'):                                                  # tables and chairs
            for k in range(max(1, int((b - a) / 3.2))):
                u = a + 1.6 + k * 3.2
                if u > b - 1.2: break
                c = F.w(u, 2.6, 0); K.obj(lathe([(0.32, 0.72), (0.32, 0.75), (0.0, 0.76)], 16, c[0], c[1]), M['smooth'], (0.92, 0.92, 0.9)); K.obj(lathe([(0.25, 0.0), (0.03, 0.04), (0.03, 0.72), (0.0, 0.72)], 10, c[0], c[1]), M['iron'], (0.12, 0.12, 0.12))
                for sg in (-1, 1):
                    q = F.w(u + sg * 0.6, 2.6, 0)
                    K.obj(bbox(q[0], q[1], 0.45, 0.42, 0.42, 0.04), M['pwood'], fcol if s_ != 'gelateria' else (0.95, 0.95, 0.95)); K.obj(F.box(u + sg * 0.6 + sg * 0.19, u + sg * 0.6 + sg * 0.21, 2.4, 2.8, 0.45, 0.95), M['pwood'], fcol if s_ != 'gelateria' else (0.95, 0.95, 0.95))
                    for dd in ((-0.18, -0.18), (0.18, -0.18), (0.18, 0.18), (-0.18, 0.18)): K.obj(bbox(q[0] + dd[0], q[1] + dd[1], 0.22, 0.03, 0.03, 0.44), M['iron'], (0.12, 0.12, 0.12))
        if s_ == 'market':                                                                            # produce crates on a stand
            K.obj(F.box(a + pw + 0.2, b - pw - 0.2, 0.25, 1.15, 0.55, 0.62), M['planks'], (0.55, 0.42, 0.3), 'box', 1.0)
            for k in range(int((b - a - 2 * pw - 0.4) / 0.6)):
                u = a + pw + 0.5 + k * 0.6; col = [(0.8, 0.15, 0.08), (0.95, 0.6, 0.1), (0.35, 0.6, 0.15), (0.9, 0.85, 0.2), (0.45, 0.15, 0.35)][k % 5]
                K.obj(F.box(u - 0.27, u + 0.27, 0.3, 1.1, 0.62, 0.9), M['planks'], (0.6, 0.45, 0.3)); K.obj(F.box(u - 0.24, u + 0.24, 0.34, 1.06, 0.88, 0.95), M['smooth'], col)
            for k in range(2): K.obj(F.box(a + pw + 0.3 + k * 0.5, a + pw + 0.7 + k * 0.5, 0.3, 0.9, 0.0, 0.55), M['planks'], (0.6, 0.45, 0.3))
        if s_ in ('bakery', 'cafe', 'trattoria', 'books'):                                            # A-board
            u = a + pw + 0.5; q = F.w(u, 1.2, 0)
            for sg in (-1, 1):
                bm = bmesh.new(); pts = [F.w(u - 0.28, 1.2 + sg * 0.02, 0.0), F.w(u + 0.28, 1.2 + sg * 0.02, 0.0), F.w(u + 0.28, 1.2 + sg * 0.28, 0.95), F.w(u - 0.28, 1.2 + sg * 0.28, 0.95)]
                f = bm.faces.new([bm.verts.new(tuple(p)) for p in pts]); K.obj(bm, M['smooth'], (0.06, 0.06, 0.06), smooth=False)
        if s_ in ('cafe', 'boutique', 'pharmacy', 'trattoria', 'bakery') and rr.random() < 0.8:      # planters by the pilasters
            for u in (a + 0.3, b - 0.3):
                c = F.w(u, 0.55, 0); K.obj(lathe([(0.22, 0.0), (0.3, 0.6), (0.32, 0.65), (0.0, 0.65)], 12, c[0], c[1]), M['smooth'], (0.18, 0.18, 0.19))
                K.obj(lathe([(0.0, 0.6), (0.36, 0.75), (0.32, 1.2), (0.12, 1.45), (0.0, 1.5)], 8, c[0], c[1]), M['concrete'], (0.12, 0.3, 0.1))


def shutter(K, M, F, a, b, gf, rng):
    """Closed unit: roller shutter in its box, a few faded posters, a for-rent notice."""
    zt = min(gf - 1.15, 3.3)
    for u0, u1 in ((a, a + 0.42), (b - 0.42, b)): K.obj(F.box(u0, u1, 0.0, 0.22, 0.0, gf - 0.05), M['plaster'], (0.82, 0.8, 0.76), 'box', 1.6)
    K.obj(F.box(a, b, 0.0, 0.3, zt + 0.1, gf - 0.1), M['plaster'], (0.78, 0.76, 0.72), 'box', 1.6)
    K.obj(F.box(a + 0.42, b - 0.42, 0.0, 0.32, zt - 0.3, zt + 0.1), M['galv'], (0.6, 0.62, 0.64))
    K.obj(F.box(a + 0.42, b - 0.42, -0.05, 0.0, 0.0, zt - 0.3), M['corr'], (0.7, 0.72, 0.74), 'boxv', 0.35)
    for k in range(3):
        u = a + 1.2 + k * 1.1 + rng.uniform(-0.2, 0.2); K.obj(F.box(u - 0.35, u + 0.35, 0.0, 0.01, 1.2 + rng.uniform(0, 0.4), 2.1 + rng.uniform(0, 0.3)), M['smooth'], tuple(rng.uniform(0.4, 0.95, 3)))


def podium(K, M, F, Ln, gf, rng, lobby_u=0.0):
    """Retail ground floor for a glass tower side of length Ln: a lobby portal at lobby_u, shops either side."""
    mats(M); u = -Ln / 2
    K.obj(F.box(-Ln / 2 - 0.1, Ln / 2 + 0.1, 0.0, 0.5, gf, gf + 0.6), M['stone'], (0.84, 0.83, 0.8), 'box', 2.0, 0.02, 2)            # podium cornice
    while u < Ln / 2 - 3.0:
        w = min(rng.choice([6.0, 7.5, 9.0]), Ln / 2 - u)
        if lobby_u is not None and u <= lobby_u + 4.5 and u + w >= lobby_u - 4.5: u = lobby_u + 4.6; continue
        if w >= 4.0: storefront(K, M, F, u, u + w, gf, rng, door=True)
        u += w
    if lobby_u is not None:
        K.obj(F.box(lobby_u - 4.5, lobby_u + 4.5, 0.0, 0.5, 0.0, gf), M['stone'], (0.9, 0.89, 0.86), 'box', 2.0, 0.02, 2)
        K.obj(F.box(lobby_u - 3.8, lobby_u + 3.8, -0.4, -0.38, 0.1, gf - 0.3), M['shopglass'], (1, 1, 1))
        _cell_quad(K, M, F, lobby_u - 3.8, lobby_u + 3.8, -2.4, 0.0, gf - 0.2, 'shopin', 1, 2)
        for uu in np.linspace(lobby_u - 3.8, lobby_u + 3.8, 6): K.obj(F.fin(uu - 0.05, uu + 0.05, -0.4, -0.3, 0.1, gf - 0.3), M['galv'], (0.5, 0.52, 0.55), smooth=False)
        K.obj(F.box(lobby_u - 5.0, lobby_u + 5.0, 0.4, 4.6, gf - 0.5, gf - 0.25), M['galv'], (0.42, 0.44, 0.48), 'box', 2.0)
        K.obj(F.box(lobby_u - 4.8, lobby_u + 4.8, 0.6, 4.4, gf - 0.52, gf - 0.5), M['lens'], (1.0, 0.95, 0.85))
        c = F.w(lobby_u, 1.2, 0); K.obj(lathe([(1.3, 0.0), (1.3, 2.6), (0.0, 2.6)], 24, c[0], c[1], 0.1, close_bottom=False), M['winglass'], (1, 1, 1))
        K.obj(lathe([(1.38, 2.6), (1.38, 2.85), (0.0, 2.85)], 24, c[0], c[1], 0.1, close_bottom=False), M['galv'], (0.55, 0.57, 0.6))


# ------------------------------------------------------------------ sheet tiles: one bay or a row against a wall section, on a pavement
def _backdrop(K, M, W, gf, h=10.0, wall=(0.86, 0.82, 0.74), mat='plaster'):
    F = Frame((0, 0, 0), (0, 1, 0), (1, 0, 0))
    K.obj(F.box(-W / 2 - 0.5, W / 2 + 0.5, -2.2, 0.0, gf, gf + h), M[mat], wall, 'box', 2.4)
    for k in range(int(W / 2.6)):                                                                      # upper windows with shutters
        u = -W / 2 + 1.3 + k * 2.6
        for zz in (gf + 1.2, gf + 4.6):
            K.obj(F.box(u - 0.55, u + 0.55, 0.0, 0.02, zz, zz + 2.0), M['winglass'], (1, 1, 1)); K.obj(F.box(u - 0.7, u + 0.7, 0.0, 0.16, zz - 0.12, zz), M['stone'], (0.92, 0.9, 0.85))
            for sg in (-1, 1): K.obj(F.box(u + sg * 0.6 - 0.0 if sg > 0 else u - 1.15, u + 1.15 if sg > 0 else u - 0.6, 0.0, 0.05, zz, zz + 2.0), M['pwood'], (0.2, 0.36, 0.3), 'box', 1.0)
    K.obj(F.box(-W / 2 - 0.5, W / 2 + 0.5, -2.2, 6.0, -0.2, 0.0), M['setts'] if 'setts' in M else M['concrete'], (0.82, 0.8, 0.76), 'box', 1.4)
    K.obj(F.box(-W / 2 - 0.5, W / 2 + 0.5, 6.0, 6.3, -0.2, 0.02), M['concrete'], (0.75, 0.74, 0.7), 'box', 1.0)
    K.obj(F.box(-W / 2 - 0.5, W / 2 + 0.5, 6.3, 12.0, -0.36, -0.14), M['asphalt'] if 'asphalt' in M else M['concrete'], (0.5, 0.49, 0.48), 'box', 4.0)
    return F


def tile(shop, W=8.0, gf=4.6):
    def fn(K, M):
        rng = np.random.default_rng(shop); F = _backdrop(K, M, W, gf); storefront(K, M, F, -W / 2, W / 2, gf, rng, True, shop)
    return fn


def tile_row(K, M):
    rng = np.random.default_rng(21); W, gf = 26.0, 4.6; F = _backdrop(K, M, W, gf, wall=(0.92, 0.8, 0.62))
    u = -W / 2
    for shop, w in ((12, 7.0), (2, 5.5), (5, 7.5), (8, 6.0)): storefront(K, M, F, u, u + w, gf, rng, True, shop); u += w


def tile_podium(K, M):
    rng = np.random.default_rng(3); W, gf = 30.0, 5.6; F = Frame((0, 0, 0), (0, 1, 0), (1, 0, 0))
    K.obj(F.box(-W / 2 - 0.3, W / 2 + 0.3, -2.4, 0.0, gf + 0.6, gf + 14.0), M['winglass'], (1, 1, 1))
    for u in np.linspace(-W / 2, W / 2, 11): K.obj(F.fin(u - 0.08, u + 0.08, 0.0, 0.25, gf + 0.6, gf + 14.0), M['galv'], (0.6, 0.62, 0.66), smooth=False)
    for z in np.arange(gf + 0.6, gf + 14.0, 3.6): K.obj(F.box(-W / 2 - 0.3, W / 2 + 0.3, 0.0, 0.2, z, z + 0.3), M['galv'], (0.55, 0.57, 0.6))
    podium(K, M, F, W, gf, rng, 0.0)
    K.obj(F.box(-W / 2 - 0.5, W / 2 + 0.5, -2.2, 6.0, -0.2, 0.0), M['concrete2'], (0.8, 0.79, 0.76), 'box', 1.8)
    K.obj(F.box(-W / 2 - 0.5, W / 2 + 0.5, 6.0, 6.3, -0.2, 0.02), M['concrete'], (0.75, 0.74, 0.7))
    K.obj(F.box(-W / 2 - 0.5, W / 2 + 0.5, 6.3, 12.0, -0.36, -0.14), M['asphalt'] if 'asphalt' in M else M['concrete'], (0.5, 0.49, 0.48), 'box', 4.0)


def tile_shutter(K, M):
    rng = np.random.default_rng(9); F = _backdrop(K, M, 8.0, 4.6, wall=(0.8, 0.72, 0.62)); shutter(K, M, F, -4.0, 4.0, 4.6, rng)


ITEMS = dict(sh_cafe=(tile(0), 6.0), sh_boutique=(tile(1), 6.0), sh_pharmacy=(tile(2), 6.0), sh_trattoria=(tile(3), 6.0), sh_bakery=(tile(4), 6.0), sh_market=(tile(5), 6.0),
             sh_gelateria=(tile(7), 6.0), sh_books=(tile(8), 6.0), sh_pizzeria=(tile(12), 6.0), sh_row=(tile_row, 6.0), sh_podium=(tile_podium, 20.0), sh_shutter=(tile_shutter, 6.0))


def register(M=None):
    M = M if M is not None else P.mats()
    import isle_roads_hq as RQ; RQ.materials(M); mats(M)
    for k, (fn, h) in ITEMS.items(): P.PROPS[k] = (fn, {}); P.HEIGHT[k] = h

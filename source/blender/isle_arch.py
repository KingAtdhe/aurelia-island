"""Aurelia Island architecture: walls with real window openings (reveals, glass, frames, sills, shutters), tiled gable roofs,
curtain walls with modelled mullions and spandrels. Replaces the flat textured facades close up; the flat ones stay as the far detail level."""
import math, bpy
import numpy as np
import isle_lib as L
import isle_kit as KIT
from isle_lib import lin, box, cyl, fft_noise, make_image, new_mat

rng = np.random.default_rng(77)          # own stream, so the island layout (which uses the shared stream) does not move
HD_TILE = 200.0
K_Y = -2400.0
P = {}                                   # part name -> list of (V, F, C, U, key)
STAT = dict(windows=0, houses=0, midrise=0, towers=0)


def put(part, V, F, C, U=None, key=None):
    V = np.asarray(V, float); C = np.asarray(C, float)
    if C.ndim == 1: C = np.tile(C, (len(V), 1))
    P.setdefault(part, []).append((V, np.asarray(F, np.int64), C, np.zeros((len(V), 2)) if U is None else np.asarray(U, float), key))


def quads(part, Q, want, C, U=None, key=None):
    """Q: (n, 4, 3) corner loops. Faces are wound so their normal agrees with `want` ((3,) or (n, 3))."""
    Q = np.asarray(Q, float); n = len(Q)
    if not n: return
    nr = np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0]); flip = np.einsum('ij,ij->i', nr, np.broadcast_to(want, nr.shape)) < 0
    Q = np.where(flip[:, None, None], Q[:, ::-1], Q)
    if U is not None: U = np.where(flip[:, None, None], np.asarray(U, float)[:, ::-1], U).reshape(-1, 2)
    C = np.asarray(C, float)
    if C.ndim == 3: C = np.where(flip[:, None, None], C[:, ::-1], C).reshape(-1, 3)
    elif C.ndim == 2 and len(C) == n: C = np.repeat(C, 4, 0)
    q = np.arange(n) * 4
    put(part, Q.reshape(-1, 3), np.vstack([np.c_[q, q + 1, q + 2], np.c_[q, q + 2, q + 3]]), C, U, key)


def textures():
    T = {}
    pl = 0.90 + 0.10 * (fft_noise(512, 1.3, 81) - 0.5) + 0.05 * (fft_noise(512, 0.4, 82) - 0.5); v = (np.arange(512) / 512)[:, None]
    pl = pl - 0.05 * np.clip(fft_noise(512, 1.8, 83) - 0.6, 0, 1) * 2.5
    T['plaster'] = make_image('wall_plaster', np.repeat(np.clip(pl, 0, 1)[..., None], 3, 2)); T['plaster_n'] = L.nmap('wall_plaster_n', pl, 3.0)
    yy, xx = np.mgrid[0:512, 0:512]; row = yy // 32; xo = (xx + (row % 2) * 32) % 512; bx = xo // 64
    hsh = ((row * 7349 + bx * 9151) * 2654435761 % 1000) / 1000.0
    mort = ((yy % 32) < 3) | ((xo % 64) < 3)
    br = np.where(mort, 0.62, 0.74 + 0.26 * hsh) + 0.07 * (fft_noise(512, 0.7, 84) - 0.5)
    T['brick'] = make_image('wall_brick', np.repeat(np.clip(br, 0, 1)[..., None], 3, 2)); T['brick_n'] = L.nmap('wall_brick_n', np.where(mort, 0.0, 1.0) + 0.1 * fft_noise(512, 0.7, 85), 2.5)
    rw = 64; ry = (yy % rw) / rw; col_ = ((xx + (yy // rw % 2) * 32) % 64) / 64.0
    hgt = 0.55 * np.sin(np.pi * col_) ** 0.7 + 0.45 * ry                      # barrel tiles, each row lapping the one below
    hs2 = (((yy // rw) * 911 + ((xx + (yy // rw % 2) * 32) // 64) * 3571) * 2654435761 % 1000) / 1000.0
    rt = 0.55 + 0.33 * hgt + 0.16 * (hs2 - 0.5) + 0.06 * (fft_noise(512, 0.8, 86) - 0.5); rt[(yy % rw) < 4] -= 0.2
    T['roof'] = make_image('roof_tiles', np.repeat(np.clip(rt, 0, 1)[..., None], 3, 2)); T['roof_n'] = L.nmap('roof_tiles_n', hgt, 5.0)
    # window atlas, 4 x 4: what is behind the glass by day, and which panes are lit at night
    r = np.random.default_rng(5); n = 64; day = np.zeros((4 * n, 4 * n, 3)); nite = np.zeros((4 * n, 4 * n, 3)); y_, x_ = np.mgrid[0:n, 0:n] / n
    for k in range(16):
        base = np.array([0.09, 0.12, 0.16]) * r.uniform(0.7, 1.5); c = np.ones((n, n, 3)) * base; kind = k % 4
        c *= (0.75 + 0.5 * y_)[..., None]                                     # sky reflection gradient
        if kind == 1:
            m = (x_ < 0.2) | (x_ > 0.8); c[m] = np.array([0.55, 0.5, 0.42]) * r.uniform(0.6, 1.0)        # curtains
        elif kind == 2:
            m = (y_ > r.uniform(0.35, 0.7)); c[m] = ((0.7 + 0.3 * (np.sin(y_ * 60) > 0))[..., None] * np.array([0.5, 0.5, 0.48]))[m]   # blind half down
        lit = r.random() < 0.42; e = np.zeros((n, n, 3))
        if lit:
            warm = np.array([1.0, 0.74, 0.40]) if r.random() < 0.7 else np.array([0.72, 0.85, 1.0])
            e = warm * (0.55 + 0.45 * np.exp(-((x_ - 0.5) ** 2 + (y_ - 0.65) ** 2) * 5))[..., None] * r.uniform(0.6, 1.0)
            if kind == 1: e[(x_ < 0.2) | (x_ > 0.8)] *= 0.55
            if kind == 2: e *= (0.6 + 0.4 * (np.sin(y_ * 60) > 0))[..., None]
            e[(y_ < 0.3) & (np.abs(x_ - r.uniform(0.3, 0.7)) < 0.12)] *= 0.35                              # furniture silhouette
        i, j = k // 4, k % 4; day[i * n:(i + 1) * n, j * n:(j + 1) * n] = c; nite[i * n:(i + 1) * n, j * n:(j + 1) * n] = e
    T['win'] = make_image('window_atlas', day); T['win_e'] = make_image('window_atlas_emissive', nite)
    import isle_photo as PH; PH.images(T, ('plaster', 'roof'))
    return T


def materials(M, T=None):
    import bpy
    T = T or textures()
    M.plaster = new_mat('WallPlaster', 0.9, image=T['plaster'], vcol=True, normal=T['plaster_n'], nstrength=0.5)
    M.brick = new_mat('WallBrick', 0.88, image=T['brick'], vcol=True, normal=T['brick_n'], nstrength=0.8)
    M.rooft = new_mat('RoofTiles', 0.8, image=T['roof'], vcol=True, normal=T['roof_n'], nstrength=1.0)
    M.glass = new_mat('WindowGlass', 0.08, metal=0.0, image=T['win'])
    nt = M.glass.node_tree; b = nt.nodes['Principled BSDF']; et = nt.nodes.new('ShaderNodeTexImage'); et.image = T['win_e']
    nt.links.new(et.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 1.0
    try: b.inputs['Specular IOR Level'].default_value = 1.0
    except Exception: pass
    M.trim = new_mat('Trim', 0.6, vcol=True)
    rgb, hh = KIT.trim_sheet(); M.kit = new_mat('KitTrim', 0.8, image=make_image('kit_trim_sheet', rgb), vcol=True, normal=L.nmap('kit_trim_sheet_n', hh, 3.0), nstrength=1.0)
    g = np.zeros((64, 8, 4)); g[..., 3] = (0.62 * (1 - np.arange(64) / 63.0) ** 1.8)[:, None]; im = make_image('contact_shade', g)
    m = bpy.data.materials.new('ContactAO'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (0, 0, 0, 1); b.inputs['Roughness'].default_value = 1.0
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
    try: m.surface_render_method = 'BLENDED'
    except Exception: pass
    M.ao = m; M.sign = new_mat('ShopSigns', 0.45, image=make_image('shop_signs', sign_atlas()))
    return T


# ------------------------------------------------------------------ walls with openings
def wall(p0, p1, z0, fh, nfl, bw, win, wallc, mat, key, depth=0.26, shop=False, shutters=None, blank=(), sillc=None, framec=None, below=0.0, uvs=2.56, plinth=False, cornice=False, door=(), quoins=False, doorc=None):
    """Wall from p0 to p1 (outside is on the right of the direction of travel). win = (width, height, sill height)."""
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float); Lw = float(np.linalg.norm(p1 - p0))
    if Lw < 0.5: return
    t = (p1 - p0) / Lw; nrm = np.array([t[1], -t[0]]); n3 = np.array([nrm[0], nrm[1], 0.0]); t3 = np.array([t[0], t[1], 0.0]); up = np.array([0, 0, 1.0])
    nu = max(1, int(round(Lw / bw))); cw = Lw / nu; ww, wh, sh = win; ww = min(ww, cw - 0.7)
    sillc = wallc * 0.82 + 0.12 if sillc is None else sillc; framec = lin('#e8e6df') if framec is None else framec

    def W(s, z, d=0.0):                                                       # local (along, up, depth into the wall) -> world
        s = np.asarray(s, float); z = np.asarray(z, float); d = np.broadcast_to(np.asarray(d, float), s.shape)
        return np.stack([p0[0] + t[0] * s - nrm[0] * d, p0[1] + t[1] * s - nrm[1] * d, z], -1)

    def Q(s0, s1, za, zb, d=0.0):                                             # vertical rectangles facing out
        return np.stack([W(s0, za, d), W(s1, za, d), W(s1, zb, d), W(s0, zb, d)], 1)

    def UVq(s0, s1, za, zb): return np.stack([np.c_[s0, za], np.c_[s1, za], np.c_[s1, zb], np.c_[s0, zb]], 1) / uvs
    if below > 0: quads(mat, Q(np.array([0.0]), np.array([Lw]), np.array([z0 - below]), np.array([z0])), n3, wallc * 0.9, UVq(np.array([0.0]), np.array([Lw]), np.array([z0 - below]), np.array([z0])), key)
    I, J = np.meshgrid(np.arange(nu), np.arange(nfl)); I = I.ravel(); J = J.ravel()
    s0 = I * cw; s1 = s0 + cw; zc0 = z0 + J * fh; zc1 = zc0 + fh
    isblank = np.zeros(len(I), bool)
    for bi, bj in blank: isblank |= (I == (bi % nu)) & (J == bj)
    if ww < 0.6: isblank[:] = True
    isdoor = np.zeros(len(I), bool)
    for bi, bj in door: isdoor |= (I == (bi % nu)) & (J == bj)
    isdoor &= ~isblank
    if isblank.any(): m = isblank; quads(mat, Q(s0[m], s1[m], zc0[m], zc1[m]), n3, wallc, UVq(s0[m], s1[m], zc0[m], zc1[m]), key)
    m = ~isblank
    if not m.any(): return
    s0, s1, zc0, zc1, J = s0[m], s1[m], zc0[m], zc1[m], J[m]; n = len(s0); isdoor = isdoor[m]
    isshop = (J == 0) & shop & ~isdoor
    a0 = np.where(isshop, s0 + 0.35, s0 + (cw - ww) / 2); a1 = np.where(isshop, s1 - 0.35, s0 + (cw + ww) / 2)
    b0 = np.where(isshop, zc0 + 0.45, zc0 + sh); b1 = np.minimum(np.where(isshop, zc1 - 0.6, b0 + wh), zc1 - 0.22)
    mid_ = (s0 + s1) / 2; a0 = np.where(isdoor, mid_ - 0.52, a0); a1 = np.where(isdoor, mid_ + 0.52, a1); b0 = np.where(isdoor, zc0 + 0.03, b0); b1 = np.where(isdoor, zc0 + 2.12, b1)
    cols = np.where((isshop)[:, None], wallc * 0.78, wallc)
    ztop = z0 + nfl * fh
    def shade(za, zb):                                                        # baked contact shading: dirt at the ground, shadow under the cornice
        f = lambda zz: 1 - 0.30 * np.clip(1 - (zz - z0) / 1.1, 0, 1) - 0.16 * np.clip(1 - (ztop - zz) / 0.7, 0, 1)
        fa, fb = f(za), f(zb); return cols[:, None, :] * np.stack([fa, fa, fb, fb], 1)[:, :, None]
    for (x0, x1, y0, y1) in ((s0, s1, zc0, b0), (s0, s1, b1, zc1), (s0, a0, b0, b1), (a1, s1, b0, b1)):                     # wall round the opening
        quads(mat, Q(x0, x1, y0, y1), n3, shade(y0, y1), UVq(x0, x1, y0, y1), key)
    dp = np.where(isshop, depth * 1.6, depth); rc = cols * 0.72
    quads(mat, np.stack([W(a0, b0), W(a1, b0), W(a1, b0, dp), W(a0, b0, dp)], 1), up, rc, UVq(a0, a1, b0, b0 + dp), key)   # reveals
    quads(mat, np.stack([W(a0, b1), W(a1, b1), W(a1, b1, dp), W(a0, b1, dp)], 1), -up, rc, UVq(a0, a1, b1, b1 + dp), key)
    quads(mat, np.stack([W(a0, b0), W(a0, b1), W(a0, b1, dp), W(a0, b0, dp)], 1), t3, rc, UVq(a0, a0 + dp, b0, b1), key)
    quads(mat, np.stack([W(a1, b0), W(a1, b1), W(a1, b1, dp), W(a1, b0, dp)], 1), -t3, rc, UVq(a1, a1 + dp, b0, b1), key)
    cu = rng.integers(0, 4, n) / 4.0; cv = rng.integers(0, 4, n) / 4.0; e = 0.01                                           # glass
    quads('glass', Q(a0, a1, b0, b1, dp), n3, np.ones(3), np.stack([np.c_[cu + e, cv + e], np.c_[cu + 0.25 - e, cv + e], np.c_[cu + 0.25 - e, cv + 0.25 - e], np.c_[cu + e, cv + 0.25 - e]], 1), key)
    if isdoor.any():                                                           # panelled door leaf, a stone step and a lintel
        d_ = isdoor; nd = int(d_.sum()); dc = lin('#6a3f2a') if doorc is None else doorc; kp_ = 'kit' if key is None else 'kit_hd'
        quads(kp_, Q(a0[d_], a1[d_], b0[d_], b1[d_], dp[d_] * 0.5), n3, np.clip(dc * 1.6, 0, 1), KIT.strip_uv('plank', 1.04, nd), key)
        quads(kp_, Q(a0[d_] - 0.14, a1[d_] + 0.14, b1[d_], b1[d_] + 0.22, -0.05), n3, np.clip(wallc * 0.6 + 0.36, 0, 1), KIT.strip_uv('stone', 1.3, nd), key)
        quads(kp_, np.stack([W(a0[d_] - 0.2, b0[d_] + 0.12, -0.45), W(a1[d_] + 0.2, b0[d_] + 0.12, -0.45), W(a1[d_] + 0.2, b0[d_] + 0.12, 0.0), W(a0[d_] - 0.2, b0[d_] + 0.12, 0.0)], 1), up, lin('#b9b4a8'), KIT.strip_uv('stone', 1.4, nd), key)
        quads(kp_, Q(a0[d_] - 0.2, a1[d_] + 0.2, b0[d_] - 0.3, b0[d_] + 0.12, -0.45), n3, lin('#a39e92'), KIT.strip_uv('stone', 1.4, nd), key)
    fd = dp - 0.05; fw = 0.035                                                                                           # frame: border, mullion, transom
    mid = (a0 + a1) / 2; tz = b0 + (b1 - b0) * np.where(isshop, 0.8, 0.64); fcol = np.where(isshop[:, None], lin('#2a2d31'), framec)
    for (x0, x1, y0, y1) in (((mid - fw, mid + fw, b0, b1), (a0, a1, tz - fw, tz + fw), (a0, a0 + 2 * fw, b0, b1), (a1 - 2 * fw, a1, b0, b1), (a0, a1, b1 - 2 * fw, b1), (a0, a1, b0, b0 + 2 * fw)) if key is None else ((mid - fw * 1.4, mid + fw * 1.4, b0, b1), (a0, a1, tz - fw * 1.4, tz + fw * 1.4))):
        quads('trim', Q(x0, x1, y0, y1, fd), n3, fcol, None, key)
    ns = ~isshop & ~isdoor
    if ns.any():                                                                                                         # sills
        x0, x1, y1 = a0[ns] - 0.12, a1[ns] + 0.12, b0[ns]; y0 = y1 - 0.12; o = -0.11; m_ = int(ns.sum()); kc = np.clip(sillc * 1.15, 0, 1); kp = 'kit' if key is None else 'kit_hd'
        quads(kp, Q(x0, x1, y0, y1, o), n3, kc, KIT.strip_uv('stone', x1 - x0, m_), key)
        quads(kp, np.stack([W(x0, y1, o), W(x1, y1, o), W(x1, y1, 0.02), W(x0, y1, 0.02)], 1), up, kc, KIT.strip_uv('stone', x1 - x0, m_), key)
        lz = b1[ns]; quads(kp, Q(x0 + 0.02, x1 - 0.02, lz, lz + 0.2, -0.045), n3, kc, KIT.strip_uv('stone', x1 - x0, m_), key)
        quads(kp, np.stack([W(x0 + 0.02, lz, -0.045), W(x1 - 0.02, lz, -0.045), W(x1 - 0.02, lz, 0.0), W(x0 + 0.02, lz, 0.0)], 1), -up, kc * 0.6, KIT.strip_uv('stone', x1 - x0, m_), key)
        for xa, xb in ((a0[ns] - 0.1, a0[ns]), (a1[ns], a1[ns] + 0.1)):
            Qc = np.stack([W(xb, y1, -0.03), W(xb, lz, -0.03), W(xa, lz, -0.03), W(xa, y1, -0.03)], 1); quads(kp, Qc, n3, kc, KIT.strip_uv('frame', lz - y1, m_), key)
        if key is None: quads('trim', np.stack([W(x0, y0, o), W(x1, y0, o), W(x1, y0, 0.0), W(x0, y0, 0.0)], 1), -up, sillc * 0.7, None, key)
    if shutters is not None and cw > ww + 1.25 and ns.any():
        sw = min(0.52, ww / 2)
        for sg in (-1, 1):
            xa = (a0[ns] - 0.05 - sw) if sg < 0 else (a1[ns] + 0.05); xb = xa + sw; o = -0.055
            Qs_ = np.stack([W(xa, b0[ns], o), W(xa, b1[ns], o), W(xb, b1[ns], o), W(xb, b0[ns], o)], 1); quads('kit' if key is None else 'kit_hd', Qs_, n3, np.clip(shutters * 1.7, 0, 1), KIT.strip_uv('louvre', b1[ns] - b0[ns], int(ns.sum())), key)
            xe = xa if sg < 0 else xb
            quads('trim', np.stack([W(xe, b0[ns], o), W(xe, b1[ns], o), W(xe, b1[ns], 0.0), W(xe, b0[ns], 0.0)], 1), t3 * sg, shutters * 0.7, None, key)
            quads('trim', np.stack([W(xa, b1[ns], o), W(xb, b1[ns], o), W(xb, b1[ns], 0.0), W(xa, b1[ns], 0.0)], 1), up, shutters * 1.1, None, key)
    STAT['windows'] += n
    kp = 'kit' if key is None else 'kit_hd'; one = np.array([0.0]); LL = np.array([Lw]); stonec = np.clip(wallc * 0.6 + 0.36, 0, 1)

    def band(za, zb, out, strip, colr, top=True, bottom=False):                 # a moulding running the whole length of the wall
        quads(kp, Q(one, LL, np.array([za]), np.array([zb]), -out), n3, colr, KIT.strip_uv(strip, Lw, 1), key)
        if top: quads(kp, np.stack([W(one, np.array([zb]), -out), W(LL, np.array([zb]), -out), W(LL, np.array([zb]), 0.0), W(one, np.array([zb]), 0.0)], 1), up, colr, KIT.strip_uv('stone', Lw, 1), key)
        if bottom: quads(kp, np.stack([W(one, np.array([za]), -out), W(LL, np.array([za]), -out), W(LL, np.array([za]), 0.0), W(one, np.array([za]), 0.0)], 1), -up, colr * 0.55, KIT.strip_uv('stone', Lw, 1), key)
    if not shop and plinth and not door: band(z0, z0 + 0.8, 0.06, 'ashlar', stonec * 0.92)
    if quoins:                                                                # corner stones: the ashlar strip run up both ends of the wall
        for sa, sb in ((0.0, 0.42), (Lw - 0.42, Lw)):
            Qq = np.stack([W(np.array([sa]), np.array([z0]), -0.045), W(np.array([sa]), np.array([ztop]), -0.045), W(np.array([sb]), np.array([ztop]), -0.045), W(np.array([sb]), np.array([z0]), -0.045)], 1)
            quads(kp, Qq, n3, stonec, KIT.strip_uv('ashlar', ztop - z0, 1) * np.array([1.0, 1.0]), key)
    for j in range(1, nfl): band(z0 + j * fh - 0.1, z0 + j * fh + 0.1, 0.05, 'course', stonec, bottom=True)
    if shop: band(z0 + fh - 0.16, z0 + fh + 0.16, 0.1, 'course', stonec, bottom=True)
    if cornice: band(ztop - 0.5, ztop, 0.14, 'cornice', stonec, top=False, bottom=True); band(ztop, ztop + 0.16, 0.34, 'stone', stonec, bottom=True)


def rect(x, y, sx, sy, yaw=0.0):
    c, s = math.cos(yaw), math.sin(yaw)
    return [np.array([x + a * c - b * s, y + a * s + b * c]) for a, b in ((-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2))]


FASCIA = [lin(c) for c in ('#a3271f', '#1f4f8a', '#1f6b4a', '#c98a1c', '#4a2d6b', '#22262b', '#b8532a', '#0f6f7a')]
SHUT = [lin(c) for c in ('#2f5d50', '#345a80', '#6a3f2a', '#7a2f2a', '#4b5a34', '#3a4652')]


def house(C, x, y, z, sx, sy, sz, yaw, wallc, rfc, rh, flat=False):
    """Detached house: walls with openings on a plinth, gable roof with real eaves (or a parapet roof), chimney."""
    R = rect(x, y, sx, sy, yaw); z0 = z + 0.3; h = sz - 0.3; nfl = 2 if h > 4.6 else 1; fh = h / nfl
    sh = SHUT[rng.integers(len(SHUT))] if (not flat and rng.random() < 0.7) else None
    win = (1.05, min(1.35, fh - 1.35), 0.95) if not flat else (0.8, min(1.0, fh - 1.5), 1.2)
    for k in range(4):
        Lw = np.linalg.norm(R[(k + 1) % 4] - R[k]); nu = max(1, int(round(Lw / 3.1)))
        wall(R[k], R[(k + 1) % 4], z0, fh, nfl, 3.1, win, wallc, 'plaster', None, depth=0.2, shutters=sh, door=[(nu // 2, 0)] if k == 0 else [], below=0.0, plinth=True, quoins=not flat, doorc=SHUT[rng.integers(len(SHUT))] * 0.8)
    c, s = math.cos(yaw), math.sin(yaw)

    def Wd(a, b, zz): return np.stack([x + np.asarray(a) * c - np.asarray(b) * s, y + np.asarray(a) * s + np.asarray(b) * c, np.broadcast_to(zz, np.shape(a)) + 0.0], -1)
    zt = z + sz
    if flat:
        for k in range(4): wall(R[k], R[(k + 1) % 4], zt, 0.55, 1, 99, (0, 0, 0), wallc * 0.97, 'plaster', None)
        C.S.add(box(x, y, zt - 0.05, sx - 0.5, sy - 0.5, 0.2, yaw), rfc * 0.8)
        for k in range(4):                                                    # roof beams poking through the wall, as on adobe houses
            if k % 2 == 0:
                for q in np.linspace(-sx / 2 + 0.8, sx / 2 - 0.8, max(2, int(sx / 1.6))): p = Wd(q, (sy / 2 + 0.18) * (1 if k else -1), 0)[:2]; C.S.add(box(p[0], p[1], zt - 0.42, 0.16, 0.5, 0.16, yaw), lin('#5a4030'))
        STAT['houses'] += 1; contact(C, x, y, sx, sy, yaw, 1.5); return
    ov = 0.5; th = 0.15; hy = sy / 2; hx = sx / 2 + 0.4; k_ = rh / hy; ze = -ov * k_; ln = math.hypot(hy + ov, rh + ov * k_)
    nrm_l = np.array([0, -rh, hy]) / math.hypot(rh, hy)                        # local normal of the y<0 slope... sign fixed by `want` below
    for sg in (-1, 1):
        ye = sg * (hy + ov); A = np.array([-hx, hx, hx, -hx]); B = np.array([ye, ye, 0, 0]); Z = np.array([ze, ze, rh, rh])
        nl = np.array([0, sg * rh, hy]); nl = nl / np.linalg.norm(nl); nw = np.array([nl[0] * c - nl[1] * s, nl[0] * s + nl[1] * c, nl[2]])
        top = Wd(A, B, zt + Z + 0.0); top[:, 2] += th / nl[2] * 0.5; bot = top - nw * th
        quads('roof', top[None], nw, rfc, np.array([[(-hx, 0), (hx, 0), (hx, ln), (-hx, ln)]]) / 2.2, None)
        quads('trim', bot[None], -nw, rfc * 0.55 + 0.05, None, None)
        quads('trim', np.array([[top[0], top[1], bot[1], bot[0]]]), np.array([-s * sg, c * sg, 0]), rfc * 0.6, None, None)      # eave fascia
        for a, b, sgx in ((0, 3, -1), (1, 2, 1)): quads('trim', np.array([[top[a], top[b], bot[b], bot[a]]]), np.array([c * sgx, s * sgx, 0]), lin('#e8e6df'), None, None)   # barge boards
        g = Wd(np.array([-hx - 0.02, hx + 0.02]), np.array([ye, ye]), zt + ze - 0.02)                                              # gutter
        C.S.add(L.beam(g[0], g[1], 0.14, 0.11), lin('#5b6067'))
    rr = Wd(np.array([-hx, hx]), np.array([0, 0]), zt + rh + th * 0.6); C.S.add(L.beam(rr[0], rr[1], 0.34, 0.16), rfc * 0.72)       # ridge cap
    for sgx in (-1, 1):                                                       # gable walls
        tri = Wd(np.array([sgx * sx / 2] * 3), np.array([-hy, hy, 0.0]), zt + np.array([0, 0, rh]))
        F = [(0, 1, 2)] if sgx > 0 else [(0, 2, 1)]
        put('plaster', tri, F, wallc, np.array([(-hy, 0), (hy, 0), (0, rh)]) / 2.56)
        if rh > 1.9:                                                          # round attic vent
            vc = Wd(np.array([sgx * (sx / 2 + 0.03)]), np.array([0.0]), zt + rh * 0.42)[0]; C.S.add(L.beam(vc - (c * 0.02 * sgx, s * 0.02 * sgx, 0), vc + (c * 0.05 * sgx, s * 0.05 * sgx, 0), 0.5, 0.5), lin('#2a2f36'))
    if nfl == 2 and sx > 8.5:                                                 # balcony over the door: slab on brackets, iron rail with bars
        zb = z0 + fh - 0.12; pb = Wd(0.0, -hy - 0.55, 0); C.S.add(box(pb[0], pb[1], zb, 2.6, 1.1, 0.12, yaw), lin('#d9d4c8'))
        for a_ in (-1.05, 1.05): q = Wd(a_, -hy - 0.3, 0); C.S.add(box(q[0], q[1], zb - 0.32, 0.12, 0.6, 0.32, yaw), lin('#bdb8ac'))
        iron = lin('#23262a')
        for a_ in np.linspace(-1.25, 1.25, 9): q = Wd(a_, -hy - 1.06, 0); C.S.add(box(q[0], q[1], zb + 0.12, 0.035, 0.035, 0.95, yaw), iron)
        for b_ in (-hy - 0.3, -hy - 0.7):
            for a_ in (-1.25, 1.25): q = Wd(a_, b_, 0); C.S.add(box(q[0], q[1], zb + 0.12, 0.035, 0.035, 0.95, yaw), iron)
        q = Wd(0.0, -hy - 1.06, 0); C.S.add(box(q[0], q[1], zb + 1.05, 2.6, 0.06, 0.05, yaw), iron)
        for a_ in (-1.25, 1.25): q = Wd(a_, -hy - 0.55, 0); C.S.add(box(q[0], q[1], zb + 1.05, 0.06, 1.05, 0.05, yaw), iron)
        STAT['balconies'] = STAT.get('balconies', 0) + 1
    if rh > 2.1 and sx > 8:                                                   # dormer on the front slope: cheeks, little gable roof, glazed front
        yd = -hy * 0.52; zd = zt + rh * (1 - abs(yd) / hy) - 0.25; pd = Wd(-sx * 0.2, yd - 0.1, 0)
        C.S.add(box(pd[0], pd[1], zd, 1.25, 1.5, 1.05, yaw), wallc * 0.95); C.S.add(L.roof(pd[0], pd[1], zd + 1.05, 1.25, 1.5, 0.5, yaw + math.pi / 2, 0.14), rfc * 0.8)
        g0 = Wd(np.array([-sx * 0.2 - 0.42, -sx * 0.2 + 0.42, -sx * 0.2 + 0.42, -sx * 0.2 - 0.42]), np.full(4, yd - 0.86), zd + np.array([0.2, 0.2, 0.92, 0.92]))
        quads('glass', g0[None], np.array([s, -c, 0.0]), np.ones(3), np.array([[(0.26, 0.26), (0.49, 0.26), (0.49, 0.49), (0.26, 0.49)]]), None)
        STAT['dormers'] = STAT.get('dormers', 0) + 1
    cx_, cy_ = sx * 0.22, hy * 0.35; zc = zt + rh * (1 - cy_ / hy); p = Wd(cx_, cy_, 0)                                          # chimney with cap and pots
    brick = lin('#8a5a44'); C.S.add(box(p[0], p[1], zc - 0.5, 0.75, 0.6, 1.9, yaw), brick); C.S.add(box(p[0], p[1], zc + 1.4, 0.95, 0.8, 0.12, yaw), lin('#b9b2a6'))
    for o in (-0.16, 0.16): q = Wd(cx_ + o, cy_, 0); C.S.add(cyl(q[0], q[1], zc + 1.52, 0.1, 0.085, 0.32, 6), lin('#a8553a'))
    STAT['houses'] += 1; contact(C, x, y, sx, sy, yaw, 1.5)


def contact(C, x, y, sx, sy, yaw, reach=1.8):
    """Soft dark band on the ground round a footprint (baked contact shading)."""
    c, s = math.cos(yaw), math.sin(yaw); hx, hy = sx / 2, sy / 2
    def Wp(a, b): px, py = x + a * c - b * s, y + a * s + b * c; return np.array([px, py, C.hgt(px, py) + 0.07])
    cs = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]; out = [(-hx - reach, -hy - reach), (hx + reach, -hy - reach), (hx + reach, hy + reach), (-hx - reach, hy + reach)]
    for k in range(4):
        a, b = cs[k], cs[(k + 1) % 4]; oa, ob = out[k], out[(k + 1) % 4]
        quads('ao', np.array([[Wp(*a), Wp(*b), Wp(*ob), Wp(*oa)]]), np.array([0, 0, 1.0]), np.ones(3), np.array([[(0, 0.02), (1, 0.02), (1, 0.98), (0, 0.98)]]), None)


def block(C, x, y, z, sx, sy, h, yaw, col, fh=3.9, bw=5.0, shop=False, mat='plaster', win=(2.6, 1.8, 0.95), roofc=None):
    """Flat-roofed utility building assembled from the kit: four walls with openings, cornice, roof slab, contact shade."""
    R_ = rect(x, y, sx, sy, yaw); nfl = max(1, int(round(h / fh))); fh = h / nfl
    C.S.add(box(x, y, z - 2.0, sx - 0.5, sy - 0.5, h + 1.9, yaw), lin('#2a2d31'))
    for k in range(4): wall(R_[k], R_[(k + 1) % 4], z, fh, nfl, bw, win, col, mat, None, depth=0.28, shop=shop, plinth=True, cornice=True, below=1.5)
    C.S.add(box(x, y, z + h, sx + 0.3, sy + 0.3, 0.3, yaw), lin('#4a4f57') if roofc is None else roofc); contact(C, x, y, sx, sy, yaw, 2.0); STAT['blocks'] = STAT.get('blocks', 0) + 1


def tile_key(x, y): return (int(math.floor(x / HD_TILE)), int(math.floor(y / HD_TILE)))


def emit_model(K, x, y, z, yaw, name):
    """Place a modelled part set (built facing +X at the origin) at (x, y, z) turned to the map's yaw; returns its triangle count."""
    import isle_props as KP
    groups = []; a_ = yaw - math.pi / 2; c_, s_ = math.cos(a_), math.sin(a_)
    for Pq, T, N, U, Cq, mt in K.arrays():
        Pw = np.c_[x + Pq[:, 0] * c_ - Pq[:, 1] * s_, y + Pq[:, 0] * s_ + Pq[:, 1] * c_, z + Pq[:, 2]]; Nw = np.c_[N[:, 0] * c_ - N[:, 1] * s_, N[:, 0] * s_ + N[:, 1] * c_, N[:, 2]]
        groups.append((Pw, T, Nw, U, Cq, mt))
    ob, nt = KP.make_prop(name, groups); ob.parent = L.ROOT; return nt


def midrise(C, x, y, sx, sy, h, yaw, z, wallc):
    """Mid-rise block: near version with real openings (keyed by 200 m tile) and the flat textured far version."""
    key = tile_key(x, y)
    hero = None                                                                # hero designs (art sheet 01) take plots big enough for them
    import isle_hero as HR
    fits = [k for k, (w_, d_, h_) in HR.DIMS.items() if w_ <= sx + 0.5 and d_ <= sy + 0.5 and (k != 'C' or h > 26) and (k != 'B' or h > 18)]
    if fits and rng.random() < 0.45:
        hero = fits[int(rng.integers(len(fits)))]; w_, d_, h_ = HR.DIMS[hero]; sx, sy, h = w_, d_, h_ - 2.5
    R = rect(x, y, sx, sy, yaw)
    for k in range(4):                                                        # far version: one textured quad per wall
        p0, p1 = R[k], R[(k + 1) % 4]; ln = np.linalg.norm(p1 - p0); nu = max(1, round(ln / 4.2)); nv = max(1, round((h + 2.5) / 3.6))
        quads('flat', np.array([[(p0[0], p0[1], z - 2.5), (p1[0], p1[1], z - 2.5), (p1[0], p1[1], z + h), (p0[0], p0[1], z + h)]]), np.array([p1[1] - p0[1], p0[0] - p1[0], 0]), wallc,
              np.array([[(0, 0), (nu, 0), (nu, nv), (0, nv)]], float), key)
    u = rng.random(); style = 'modern' if (h > 24 and u < 0.18) else ('artdeco' if (h > 18 and 0.18 <= u < 0.32) else ('loft' if 0.32 <= u < 0.45 else ('brick' if 0.45 <= u < 0.66 else 'plaster')))
    import isle_props as KP, isle_city as CI                                 # near version: the modelled city block (isle_city)
    if hero:
        K = KP.Part(); M_ = HR.hero_materials(KP.mats()); w_, d_, _ = HR.DIMS[hero]
        {'A': HR.building_A, 'B': HR.building_B, 'C': HR.building_C, 'D': HR.building_D}[hero](K, M_, -w_ / 2, int(rng.integers(3)))
        K2 = HR.Rotated(K, d_)                                                 # built facing -Y at the origin; turned to face +X like the city blocks
        nt = emit_model(K2, x, y, z, yaw, 'BuildingsHDModel__t%d_%d_%d' % (key[0], key[1], STAT['midrise'])); STAT['hero_' + hero] = STAT.get('hero_' + hero, 0) + 1
    else:
        K = KP.Part(); CI.building(K, KP.mats(), sx, sy, h, style, rng); nt = emit_model(K, x, y, z, yaw, 'BuildingsHDModel__t%d_%d_%d' % (key[0], key[1], STAT['midrise']))
    STAT['model_blocks'] = STAT.get('model_blocks', 0) + 1; STAT['model_block_tris'] = STAT.get('model_block_tris', 0) + nt
    contact(C, x, y, sx, sy, yaw, 2.4)
    STAT['midrise'] += 1


def curtain(C, pts, z, h, col, top=1.0, bay=3.6, floor=3.9, inset=0.32):
    """Glass curtain wall: the glass sits back behind modelled mullions (every bay) and spandrel bands (every floor). Returns the top outline."""
    pts = np.asarray(pts, float); c = pts.mean(0); n = len(pts); tp = c + (pts - c) * top
    shrink = lambda q: c + (q - c) * (1 - inset / np.maximum(np.linalg.norm(q - c, axis=1), 1e-3))[:, None]
    gi, gt = shrink(pts), shrink(tp)
    per = np.concatenate([[0], np.cumsum(np.linalg.norm(np.roll(pts, -1, 0) - pts, axis=1))]); tot = max(1, round(per[-1] / bay)); nv = max(1, round(h / floor))
    metal = lin('#c2c8ce') * rng.uniform(0.55, 1.0); dark = metal * 0.55
    for k in range(n):
        a, b, ta, tb = gi[k], gi[(k + 1) % n], gt[k], gt[(k + 1) % n]; u0, u1 = per[k] / per[-1] * tot, per[k + 1] / per[-1] * tot
        Vq = np.array([(a[0], a[1], z), (b[0], b[1], z), (tb[0], tb[1], z + h), (ta[0], ta[1], z + h)])
        C.FB.add((Vq, np.array([(0, 1, 2), (0, 2, 3)])), col, solid=False, uv=np.array([(u0, 0), (u1, 0), (u1, nv), (u0, nv)]))
        A, B, TA, TB = pts[k], pts[(k + 1) % n], tp[k], tp[(k + 1) % n]; ed = B - A; ln = np.linalg.norm(ed); t = ed / ln; nr = np.array([t[1], -t[0]]); n3 = np.array([nr[0], nr[1], 0]); t3 = np.array([t[0], t[1], 0])
        nb = max(1, int(round(u1 - u0))); f = np.arange(nb + 1) / nb                                       # mullions: front and two cheeks
        lo = A + (B - A) * f[:, None]; hi = TA + (TB - TA) * f[:, None]; w = 0.07
        def strip(off_t, off_n0, off_n1, want, colr):
            q0 = lo + t * off_t; q1 = hi + t * off_t
            if off_n0 == off_n1:
                Qd = np.stack([np.c_[q0 - t * w - nr * off_n0, np.full(nb + 1, z)], np.c_[q0 + t * w - nr * off_n0, np.full(nb + 1, z)], np.c_[q1 + t * w - nr * off_n0, np.full(nb + 1, z + h)], np.c_[q1 - t * w - nr * off_n0, np.full(nb + 1, z + h)]], 1)
            else:
                Qd = np.stack([np.c_[q0 - nr * off_n0, np.full(nb + 1, z)], np.c_[q0 - nr * off_n1, np.full(nb + 1, z)], np.c_[q1 - nr * off_n1, np.full(nb + 1, z + h)], np.c_[q1 - nr * off_n0, np.full(nb + 1, z + h)]], 1)
            quads('kit', Qd, want, np.clip(colr * 1.2, 0, 1), KIT.strip_uv('metal', h, nb + 1))
        strip(0, -0.06, -0.06, n3, metal); strip(-w, -0.06, inset, -t3, dark); strip(w, -0.06, inset, t3, dark)
        g = (np.arange(nv + 1) / nv); zz = z + h * g; sb = 0.55                                               # spandrel bands
        P0 = A + (TA - A) * g[:, None]; P1 = B + (TB - B) * g[:, None]; zb = np.clip(zz - sb * 0.3, z, z + h); zt = np.clip(zz + sb * 0.7, z, z + h)
        def band(z0_, z1_, d0, d1, want, colr):
            Qd = np.stack([np.c_[P0 - nr * d0, z0_], np.c_[P1 - nr * d0, z0_], np.c_[P1 - nr * d1, z1_], np.c_[P0 - nr * d1, z1_]], 1); quads('kit', Qd, want, np.clip(colr * 1.2, 0, 1), KIT.strip_uv('metal', ln, nv + 1))
        band(zb, zt, 0.0, 0.0, n3, metal * 0.92); band(zt, zt, 0.0, inset, np.array([0, 0, 1.0]), metal); band(zb, zb, 0.0, inset, np.array([0, 0, -1.0]), dark)
    STAT['towers'] += 1
    return tp


def emit(C):
    """Create the mesh objects. Parts with a key are split per 200 m tile so the game can swap near and far versions."""
    M = C.M; spec = dict(plaster=('Houses', M.plaster, True), roof=('Roofs', M.rooft, True), glass=('Glazing', M.glass, True), trim=('ArchTrim', M.trim, False), kit=('KitTrim', M.kit, True), sign=('BuildingsHD_Signs', M.sign, True), kit_hd=('BuildingsHD_Kit', M.kit, True), ao=('ContactAO', M.ao, True), foam=('ShoreFoam', getattr(M, 'foam', M.ao), True), shallow=('Shallows', getattr(M, 'shallow', M.ao), True),
                         plaster_hd=('BuildingsHD_Plaster', M.plaster, True), brick_hd=('BuildingsHD_Brick', M.brick, True), flat=('BuildingsLOD', M.fa, True))
    for part, items in P.items():
        name, mat, uv = spec[part]; groups = {}
        for it in items: groups.setdefault(it[4], []).append(it)
        for key, its in groups.items():
            off = 0; Vs = []; Fs = []; Cs = []; Us = []
            for V, F, Cc, U, _ in its: Vs.append(V); Fs.append(F + off); Cs.append(Cc); Us.append(U); off += len(V)
            V = np.vstack(Vs); F = np.vstack(Fs); Cc = np.vstack(Cs); U = np.vstack(Us)
            if name == 'BuildingsLOD': U = U * np.array([0.25, 0.5])                                  # the far facade texture holds 4 bays x 2 floors
            if key is None: L.make_chunked(name, V, F, Cc, U if uv else None, mat, False, tile=300 if name in ('Houses', 'KitTrim', 'ArchTrim') else None)
            else:
                nm = {'glass': 'BuildingsHD_Glazing', 'trim': 'BuildingsHD_Trim', 'kit': 'BuildingsHD_Kit'}.get(part, name)
                L.make_obj('%s__t%d_%d' % (nm, key[0], key[1]), V, F, Cc, U if uv else None, mat, False)
    library(C); L.STATS['architecture'] = dict(STAT)


def library(C):
    """The kit as stand-alone pieces (objects KIT_<piece>_<part>), laid out in a row off the south coast for export."""
    M = C.M; mats = dict(plaster=M.plaster, brick_hd=M.brick, plaster_hd=M.plaster, glass=M.glass, trim=M.trim, kit=M.kit, kit_hd=M.kit); w0 = STAT['windows']
    cream = lin('#e7d9c0'); pieces = [
        ('House_Window_Bay', dict(fh=2.9, nfl=1, bw=3.1, win=(1.05, 1.35, 0.95), mat='plaster', shutters=SHUT[0], plinth=True), 3.1),
        ('House_Plain_Bay', dict(fh=2.9, nfl=1, bw=3.1, win=(1.05, 1.35, 0.95), mat='plaster', blank=[(0, 0)], plinth=True), 3.1),
        ('House_Two_Storey_Bay', dict(fh=2.8, nfl=2, bw=3.1, win=(1.05, 1.35, 0.95), mat='plaster', plinth=True), 3.1),
        ('Block_Window_Bay_Wide', dict(fh=3.6, nfl=1, bw=5.2, win=(3.2, 1.8, 0.95), mat='plaster', depth=0.3), 5.2),
        ('Block_Window_Bay_Narrow', dict(fh=3.6, nfl=1, bw=3.7, win=(1.7, 1.95, 0.85), mat='brick_hd', depth=0.3), 3.7),
        ('Block_Shopfront_Bay', dict(fh=3.6, nfl=1, bw=5.2, win=(3.2, 1.8, 0.95), mat='plaster', depth=0.3, shop=True), 5.2),
        ('Block_Top_Floor_With_Cornice', dict(fh=3.6, nfl=1, bw=5.2, win=(3.2, 1.8, 0.95), mat='plaster', depth=0.3, cornice=True), 5.2),
        ('Block_Three_Floor_Stack', dict(fh=3.6, nfl=3, bw=5.2, win=(3.2, 1.8, 0.95), mat='plaster', depth=0.3, shop=True, cornice=True), 5.2)]
    saved = {k: list(v) for k, v in P.items()}; x = -40.0; n = 0
    for name, kw, wd in pieces:
        P.clear(); mat = kw.pop('mat'); wall((x, K_Y), (x + wd, K_Y), 0.0, kw.pop('fh'), kw.pop('nfl'), kw.pop('bw'), kw.pop('win'), cream if 'brick' not in mat else lin('#a8644a'), mat, None, **kw)
        for part, items in P.items():
            off = 0; Vs = []; Fs = []; Cs = []; Us = []
            for V, F, Cc, U, _ in items: Vs.append(V); Fs.append(F + off); Cs.append(Cc); Us.append(U); off += len(V)
            o = L.make_obj('KIT_%s_%s' % (name, part), np.vstack(Vs), np.vstack(Fs), np.vstack(Cs), np.vstack(Us), mats[part], False); o.hide_render = True; L.STATS.pop('KIT_%s_%s' % (name, part), None); n += 1
        x += wd + 2.0
    P.clear(); P.update(saved); STAT['windows'] = w0; STAT['kit_pieces'] = len(pieces); STAT['kit_objects'] = n


SIGN_NAMES = ['CAFÉ LUNA', 'BAKERY', 'PHARMACY', 'BOOKS', 'FLOWERS', 'PIZZERIA', 'GELATO', 'SHOES', 'OPTICIAN', 'MARKET', 'BAR NOVA', 'DELI', 'SPORTS', 'HAIR STUDIO', 'TAILOR', 'WINE']


def sign_atlas():
    """4 x 4 atlas of shop names, dark lettering on a pale panel (cells 256 x 64 px)."""
    from PIL import Image, ImageDraw, ImageFont
    W_, H_ = 1024, 256; im = Image.new('RGB', (W_, H_), (238, 233, 220)); d = ImageDraw.Draw(im)
    fonts = ['/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf']
    inks = [(28, 30, 34), (122, 28, 22), (22, 52, 92), (24, 70, 48)]
    for k, nm in enumerate(SIGN_NAMES):
        cx, cy = (k % 4) * 256, (k // 4) * 64; f = ImageFont.truetype(fonts[k % 2], 40); sz = 40
        while d.textlength(nm, font=f) > 228 and sz > 16: sz -= 2; f = ImageFont.truetype(fonts[k % 2], sz)
        tw = d.textlength(nm, font=f); d.text((cx + 128 - tw / 2, cy + 32), nm, fill=inks[k % 4], font=f, anchor='lm')
        d.rectangle([cx + 3, cy + 3, cx + 252, cy + 60], outline=inks[k % 4], width=2)
    return np.asarray(im, float)[::-1] / 255.0


def sign_uv(n):
    k = rng.integers(0, 16, n); u0 = (k % 4) / 4 + 0.004; v0 = 1 - (k // 4 + 1) / 4 + 0.006; u1 = u0 + 0.25 - 0.008; v1 = v0 + 0.25 - 0.012
    return np.stack([np.c_[u0, v0], np.c_[u1, v0], np.c_[u1, v1], np.c_[u0, v1]], 1)

"""Art sheet 04 foliage atlas: 4 x 4 cells of painted twigs, sprays and fronds (alpha cut-out), and bark textures.
Pure numpy / PIL so it can be previewed outside Blender. Cells are drawn at 4x and filtered down."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CELL = 512; SS = 3                       # cell size in the atlas, supersampling
S = CELL * SS
NAMES = ['plane', 'oak', 'birch', 'olive',
         'spruce', 'pinetuft', 'cypress', 'pinna',
         'box', 'oleander', 'fern', 'grass',
         'flowers', 'ivy', 'laurel', 'maple_red']


def _rgb(c, g=1.0):
    return tuple(int(np.clip(v * g, 0, 255)) for v in c)


def leaf_poly(kind, base, ang, L, W, r):
    """Outline of one leaf: base point, pointing at angle ang (radians, image space), length L, half-width W."""
    t = np.linspace(0, 1, 28)
    if kind == 'oak':
        w = W * np.sin(np.pi * t) ** 0.7 * (0.68 + 0.32 * np.cos(t * 2 * np.pi * 3.5 + 0.6))
    elif kind == 'lance':
        w = W * np.sin(np.pi * t ** 0.9) ** 1.1
    elif kind == 'birch':
        w = W * np.sin(np.pi * t ** 0.8) ** 0.75 * (1 + 0.08 * np.sign(np.sin(t * 60)))
    elif kind == 'ivy':
        w = W * (np.sin(np.pi * t) ** 0.6) * (1 + 0.35 * np.cos(t * 2 * np.pi * 1.5))
    else:
        w = W * np.sin(np.pi * t ** 0.85) ** 0.8
    ax = np.array([math.cos(ang), math.sin(ang)]); nr = np.array([-ax[1], ax[0]])
    pts_l = base + ax * (t * L)[:, None] + nr * w[:, None]; pts_r = base + ax * (t * L)[:, None] - nr * w[:, None]
    return [tuple(p) for p in np.vstack([pts_l, pts_r[::-1]])], base + ax * L


def palmate(d, base, ang, L, col, r, lobes=5, spread=0.55):
    for k in range(lobes):
        a = ang + (k - (lobes - 1) / 2) * spread; ln = L * (1 - 0.18 * abs(k - (lobes - 1) / 2))
        poly, tip = leaf_poly('plain', base, a, ln, ln * 0.3, r); d.polygon(poly, fill=col)
    for k in range(lobes):                                                           # veins
        a = ang + (k - (lobes - 1) / 2) * spread; ln = L * (1 - 0.18 * abs(k - (lobes - 1) / 2)) * 0.85
        d.line([tuple(base), tuple(base + ln * np.array([math.cos(a), math.sin(a)]))], fill=_rgb(col, 0.78), width=max(1, SS))


def twig(d, r, kind, col, n=11, lscale=1.0, flowers=None, stem=(70, 52, 36), sides=2):
    """A spray: main twig rising from the bottom centre with `sides` side twigs, alternate leaves; back leaves drawn darker first."""
    leaves = []; segs = []

    def shoot(p, ang, length, nl, w0):
        pts = [np.asarray(p, float)]
        for i in range(10):
            ang += r.uniform(-0.1, 0.1); pts.append(pts[-1] + np.array([math.cos(ang), math.sin(ang)]) * length / 10)
        for i in range(10): segs.append((pts[i], pts[i + 1], max(SS, int(w0 * (1 - i / 11)))))
        for i in range(nl):
            f = 0.12 + 0.86 * i / max(1, nl - 1); idx = f * 10; j = min(int(idx), 9); q = pts[j] + (pts[j + 1] - pts[j]) * (idx - j)
            side = 1 if i % 2 else -1; sa = ang + side * r.uniform(0.55, 1.1)
            if i == nl - 1: sa = ang
            L = S * (0.17 + 0.08 * math.sin(math.pi * f)) * lscale * r.uniform(0.85, 1.12)
            leaves.append((r.random() < 0.4, q, sa, L))
        return pts
    a0 = -math.pi / 2 + r.uniform(-0.1, 0.1)
    main = shoot((S * 0.5, S * 0.985), a0, S * 0.72, n, SS * 6)
    for k in range(sides):
        f = 0.28 + 0.3 * k; q = main[int(f * 10)]; sg = 1 if k % 2 == 0 else -1
        shoot(q, a0 + sg * r.uniform(0.55, 0.8), S * 0.42 * (1 - 0.25 * k), max(3, int(n * 0.55)), SS * 4)
    for p0, p1, w in segs: d.line([tuple(p0), tuple(p1)], fill=stem, width=w)
    for back, q, sa, L in sorted(leaves, key=lambda x: not x[0]):
        g = r.uniform(0.82, 1.12) * (0.7 if back else 1.0); c = _rgb(col, g)
        pet = q + np.array([math.cos(sa), math.sin(sa)]) * L * 0.1; d.line([tuple(q), tuple(pet)], fill=stem, width=2 * SS)
        if kind == 'palmate': palmate(d, pet, sa, L * 0.75, c, r)
        else:
            fs = r.uniform(0.55, 1.0)                                               # foreshortening: some leaves seen edge-on
            poly, tip = leaf_poly(kind, pet, sa, L, L * {'oak': 0.3, 'lance': 0.1, 'birch': 0.33, 'ivy': 0.42}.get(kind, 0.28) * fs, r)
            d.polygon(poly, fill=c); d.line([tuple(pet), tuple(tip)], fill=_rgb(col, g * 0.72), width=max(1, SS))
            d.line(poly[:len(poly) // 2], fill=_rgb(col, g * 1.2), width=max(1, SS // 2))   # lit edge on one side
    if flowers is not None:
        for _ in range(10):
            q = segs[int(r.integers(len(segs) // 3, len(segs)))][1] + r.normal(0, S * 0.06, 2)
            for k in range(5):
                a = k * 2 * math.pi / 5 + r.uniform(0, 1); p = q + np.array([math.cos(a), math.sin(a)]) * S * 0.022
                d.ellipse([p[0] - S * 0.022, p[1] - S * 0.022, p[0] + S * 0.022, p[1] + S * 0.022], fill=_rgb(flowers, r.uniform(0.85, 1.1)))
            d.ellipse([q[0] - S * 0.008, q[1] - S * 0.008, q[0] + S * 0.008, q[1] + S * 0.008], fill=(240, 220, 120))


def needles_branch(d, r, p0, p1, ln, dens, col, wd, lighten=0.0):
    p0 = np.array(p0, float); p1 = np.array(p1, float); ax = p1 - p0; L_ = np.linalg.norm(ax); ax /= L_; nr = np.array([-ax[1], ax[0]])
    d.line([tuple(p0), tuple(p1)], fill=(72, 54, 38), width=int(wd * 1.6))
    for s in np.arange(0, L_, dens):
        for sg in (-1, 1):
            q = p0 + ax * s; e = q + (ax * 0.55 + nr * sg * r.uniform(0.5, 1.0)) * ln * r.uniform(0.75, 1.1) * (1 - 0.35 * s / L_)
            g = r.uniform(0.75, 1.2) * (1 + lighten * s / L_); d.line([tuple(q), tuple(e)], fill=_rgb(col, g), width=wd)


def spruce_spray(d, r, col):
    """Dense spruce shoot: a main axis with many side shoots, each with its own branchlets, needles overlapping into a mass."""
    base = np.array([S * 0.5, S * 0.99]); tip = np.array([S * 0.5, S * 0.02])
    for t in np.linspace(0.04, 0.92, 22):
        q = base + (tip - base) * t; env = (1 - t) ** 0.5 * 0.46
        for sg in (-1, 1):
            e = q + np.array([sg * S * env * r.uniform(0.85, 1.05), -S * env * 0.45]); needles_branch(d, r, q, e, S * 0.05, S * 0.006, col, SS * 2, 0.35)
            for u in (0.35, 0.65):
                qq = q + (e - q) * u; ee = qq + np.array([sg * S * env * 0.35, -S * env * 0.45]); needles_branch(d, r, qq, ee, S * 0.04, S * 0.006, col, SS * 2, 0.3)
    needles_branch(d, r, base, tip, S * 0.05, S * 0.006, col, SS * 2, 0.35)


def box_mass(d, r, col):
    """Clipped boxwood: a mass of tiny overlapping leaves filling the cell, darker toward the middle."""
    for k in range(2600):
        rr = S * 0.5 * math.sqrt(r.random()); a = r.uniform(0, 2 * math.pi); q = np.array([S * 0.5 + rr * math.cos(a), S * 0.5 + rr * math.sin(a)])
        L = S * r.uniform(0.03, 0.05); g = r.uniform(0.7, 1.2) * (0.75 + 0.45 * rr / (S * 0.5))
        poly, _ = leaf_poly('plain', q, r.uniform(0, 2 * math.pi), L, L * 0.35, r); d.polygon(poly, fill=_rgb(col, g))


def pine_tuft(d, r, col):
    for k in range(9):                                                            # bundles of long needles fanning up
        b = np.array([S * (0.5 + r.uniform(-0.18, 0.18)), S * (0.85 - r.uniform(0, 0.25))]); d.line([(S * 0.5, S * 0.98), tuple(b)], fill=(90, 62, 40), width=SS * 4)
        for j in range(70):
            a = -math.pi / 2 + r.normal(0, 0.75); L = S * r.uniform(0.18, 0.32); e = b + np.array([math.cos(a), math.sin(a)]) * L
            d.line([tuple(b), tuple(e)], fill=_rgb(col, r.uniform(0.7, 1.2)), width=SS)


def cypress_spray(d, r, col):
    """Flattened scale-leaf sprays, fan-branched, densely packed (Italian cypress)."""
    def frond(p, a, L, depth):
        e = p + np.array([math.cos(a), math.sin(a)]) * L; n = max(3, int(L / (S * 0.012)))
        for k in range(n):
            q = p + (e - p) * (k + 0.5) / n; s = S * 0.011 * (1.5 - k / n) * (1 + 0.6 * depth)
            d.ellipse([q[0] - s, q[1] - s * 1.6, q[0] + s, q[1] + s * 1.6], fill=_rgb(col, r.uniform(0.72, 1.18)))
        if depth:
            for k in range(1, 7):
                q = p + (e - p) * k / 7
                for sg in (-1, 1): frond(q, a + sg * r.uniform(0.45, 0.75), L * 0.42 * (1 - k / 8), depth - 1)
    for k in range(3): frond(np.array([S * (0.5 + (k - 1) * 0.12), S * 0.99]), -math.pi / 2 + (k - 1) * 0.25, S * 0.88 * (1 - 0.12 * abs(k - 1)), 2)


def pinna(d, r, col):
    """Half a palm frond: rachis along the left edge, leaflets hanging to the right."""
    x0 = S * 0.06
    d.line([(x0, S * 0.99), (x0 + S * 0.02, S * 0.01)], fill=(150, 140, 80), width=SS * 6)
    for y in np.linspace(S * 0.96, S * 0.04, 34):
        t = 1 - y / S; L = S * 0.88 * (0.55 + 0.45 * math.sin(math.pi * min(1, t * 1.1))); a = r.uniform(0.05, 0.3)
        e = np.array([x0 + L * math.cos(a), y + L * math.sin(a) * 0.8]); m = (np.array([x0, y]) + e) / 2 + np.array([0, -S * 0.02])
        w = S * 0.013; g = r.uniform(0.8, 1.15)
        d.polygon([(x0, y - w), tuple(m + [0, -w]), tuple(e), tuple(m + [0, w]), (x0, y + w)], fill=_rgb(col, g))
        d.line([(x0, y), tuple(m), tuple(e)], fill=_rgb(col, g * 1.25), width=max(1, SS // 2))


def fern(d, r, col):
    for k in range(5):
        a = -math.pi / 2 + (k - 2) * 0.32; p = np.array([S * 0.5, S * 0.98]); L = S * 0.92 * (1 - 0.1 * abs(k - 2)); n = 26
        prev = p
        for j in range(n):
            t = (j + 1) / n; aa = a + 0.5 * t * (1 if k >= 2 else -1) * 0.6; q = p + np.array([math.cos(aa), math.sin(aa)]) * L * t
            d.line([tuple(prev), tuple(q)], fill=(80, 100, 40), width=SS * 2); prev = q
            ln = S * 0.09 * math.sin(math.pi * min(1, t * 1.05)) + S * 0.01
            for sg in (-1, 1):
                b = aa + sg * 1.25; poly, _ = leaf_poly('lance', q, b, ln, ln * 0.22, r); d.polygon(poly, fill=_rgb(col, r.uniform(0.8, 1.15)))


def grass_clump(d, r, col, flowers=None):
    for k in range(140):
        x = S * (0.5 + r.normal(0, 0.13)); h = S * r.uniform(0.45, 0.97); bend = r.normal(0, 0.18) * S
        pts = [(x + bend * (t ** 2), S * 0.995 - h * t) for t in np.linspace(0, 1, 8)]
        g = r.uniform(0.65, 1.2) * (0.8 + 0.3 * (h / S)); c = _rgb(col, g) if r.random() > 0.15 else _rgb((150, 140, 80), g)
        for i in range(7): d.line([pts[i], pts[i + 1]], fill=c, width=int(SS * 3.2 * (1 - i / 8) + 1))
        if flowers is not None and r.random() < 0.3:
            fx, fy = pts[-1]; rr = S * r.uniform(0.012, 0.022); fc = flowers[int(r.integers(len(flowers)))]
            for a in np.linspace(0, 2 * math.pi, 6)[:-1]: d.ellipse([fx + math.cos(a) * rr - rr, fy + math.sin(a) * rr - rr, fx + math.cos(a) * rr + rr, fy + math.sin(a) * rr + rr], fill=_rgb(fc, r.uniform(0.85, 1.1)))
            d.ellipse([fx - rr * 0.6, fy - rr * 0.6, fx + rr * 0.6, fy + rr * 0.6], fill=(235, 200, 70))


def draw_cell(name, seed):
    r = np.random.default_rng(seed); im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if name == 'plane': twig(d, r, 'palmate', (88, 128, 52), n=9, lscale=1.25)
    elif name == 'oak': twig(d, r, 'oak', (70, 104, 40), n=13)
    elif name == 'birch': twig(d, r, 'birch', (122, 160, 60), n=17, lscale=0.62, stem=(60, 40, 30))
    elif name == 'olive': twig(d, r, 'lance', (118, 132, 96), n=21, lscale=0.8, stem=(110, 100, 80))
    elif name == 'spruce': spruce_spray(d, r, (44, 82, 52))
    elif name == 'pinetuft': pine_tuft(d, r, (74, 112, 58))
    elif name == 'cypress': cypress_spray(d, r, (50, 84, 44))
    elif name == 'pinna': pinna(d, r, (96, 128, 56))
    elif name == 'box': box_mass(d, r, (58, 98, 40))
    elif name == 'oleander': twig(d, r, 'lance', (62, 100, 50), n=13, lscale=1.1, flowers=(232, 110, 150))
    elif name == 'fern': fern(d, r, (82, 128, 44))
    elif name == 'grass': grass_clump(d, r, (92, 132, 50))
    elif name == 'flowers': grass_clump(d, r, (84, 124, 48), flowers=[(225, 60, 50), (245, 240, 230), (150, 95, 205), (250, 205, 60)])
    elif name == 'ivy': twig(d, r, 'ivy', (46, 84, 36), n=11, lscale=0.85)
    elif name == 'laurel': twig(d, r, 'plain', (58, 96, 44), n=15, lscale=0.9)
    elif name == 'maple_red': twig(d, r, 'palmate', (160, 60, 34), n=9, lscale=1.15)
    im = im.resize((CELL, CELL), Image.LANCZOS)
    a = np.asarray(im, float) / 255.0
    yy = np.linspace(1.08, 0.86, CELL)[:, None, None]; blot = 0.9 + 0.2 * _noise(CELL, 1.3, seed)[..., None]
    a[..., :3] = np.clip(a[..., :3] * yy * blot, 0, 1)
    m = a[..., 3] > 0.35                                                            # bleed colour under the cut-out so mips stay clean
    if m.any():
        blur = Image.fromarray((a[..., :3] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)); bl = np.asarray(blur, float) / 255.0
        a[~m, :3] = np.where(bl[~m].sum(1, keepdims=True) > 0.05, bl[~m], a[m, :3].mean(0))
    return a


def atlas():
    """Returns float RGBA (rows top to bottom), 4 x 4 cells of CELL px, in NAMES order (row 0 at the top)."""
    out = np.zeros((CELL * 4, CELL * 4, 4))
    for i, n in enumerate(NAMES):
        y, x = divmod(i, 4); out[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL] = draw_cell(n, 100 + i)
    return out


def cell_uv(name):
    """UV rect (u0, v0, u1, v1) of a cell, v up as in Blender (image row 0 at the top)."""
    i = NAMES.index(name); y, x = divmod(i, 4); e = 2.0 / (CELL * 4)
    return (x / 4 + e, 1 - (y + 1) / 4 + e, (x + 1) / 4 - e, 1 - y / 4 - e)


# ------------------------------------------------------------------ bark
def _noise(n, beta, seed):
    r = np.random.default_rng(seed).normal(size=(n, n)); fx = np.fft.fftfreq(n)[:, None]; fy = np.fft.fftfreq(n)[None, :]
    f = np.hypot(fx, fy); f[0, 0] = 1; a = np.fft.ifft2(np.fft.fft2(r) / f ** beta).real; a -= a.min(); return a / a.max()


def bark(kind, n=512):
    """(colour RGB, height) tileable bark, rows top to bottom; u runs round the trunk, v up it."""
    v, u = np.mgrid[0:n, 0:n] / n
    if kind == 'rough':                                                             # oak / pine: deep vertical furrows
        w = _noise(n, 1.6, 1); ridge = np.abs(np.sin(np.pi * (7 * u + 1.6 * w))) ** 0.45; fine = _noise(n, 0.8, 2)
        h = np.clip(0.3 + 0.6 * ridge + 0.2 * (fine - 0.5) - (np.abs(_noise(n, 1.9, 3) - 0.5) < 0.015) * 0.3, 0, 1)
        c = np.array([0.30, 0.24, 0.19]) * (0.45 + 0.75 * h[..., None]) * (0.9 + 0.2 * _noise(n, 1.2, 4)[..., None])
        c = c * (1 - 0.25 * (_noise(n, 1.4, 5) > 0.62)[..., None] * np.array([0.3, 0.0, 0.35]))            # lichen tint in places
    elif kind == 'plane':                                                           # flaking camouflage: cream, olive, grey-brown patches
        p1 = _noise(n, 2.1, 11); p2 = _noise(n, 2.1, 12)
        c = np.where((p1 > 0.55)[..., None], [0.80, 0.78, 0.62], np.where((p2 > 0.5)[..., None], [0.55, 0.55, 0.40], [0.44, 0.40, 0.33]))
        h = 0.5 + 0.25 * (p1 > 0.55) + 0.1 * (_noise(n, 0.8, 13) - 0.5); c = c * (0.88 + 0.2 * _noise(n, 0.9, 14)[..., None])
    elif kind == 'birch':                                                           # white with dark horizontal lenticels and black scars
        nn = _noise(n, 1.0, 21); lent = (np.abs(np.sin(np.pi * (v * 46 + 2 * _noise(n, 1.5, 22)))) > 0.96) & (_noise(n, 1.3, 23) > 0.5)
        scar = _noise(n, 2.0, 24) > 0.8
        c = np.ones((n, n, 3)) * np.array([0.92, 0.9, 0.86]) * (0.85 + 0.15 * nn[..., None]); c[lent] = [0.25, 0.22, 0.2]; c[scar] = [0.1, 0.09, 0.09]
        h = 0.6 + 0.2 * nn - 0.4 * lent - 0.3 * scar
    elif kind == 'palm':                                                            # stacked leaf-base scars
        ring = (v * 18 + 0.15 * np.sin(2 * np.pi * u * 3)) % 1; h = np.clip(np.where(ring < 0.7, ring / 0.7, (1 - ring) / 0.3), 0, 1) ** 0.7
        dia = (np.abs(((u * 6 + v * 9) % 1) - 0.5) < 0.04) * 0.3
        c = np.array([0.45, 0.38, 0.28]) * (0.5 + 0.6 * h[..., None]) * (0.9 + 0.2 * _noise(n, 1.0, 31)[..., None]); h = h - dia
    else:                                                                           # olive: twisted grey, smooth with knots
        w = _noise(n, 1.8, 41); h = np.abs(np.sin(np.pi * (3 * u + 2.5 * v + 2.2 * w))) ** 0.8 * 0.6 + 0.3 * _noise(n, 1.0, 42)
        c = np.array([0.50, 0.48, 0.42]) * (0.6 + 0.5 * h[..., None])
    return np.clip(c, 0, 1), np.clip(h, 0, 1)


if __name__ == '__main__':
    a = atlas(); Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save('/tmp/atlas_hq.png')
    bg = Image.new('RGBA', (CELL * 4, CELL * 4), (205, 210, 200, 255)); bg.alpha_composite(Image.open('/tmp/atlas_hq.png')); bg.convert('RGB').resize((1024, 1024)).save('/tmp/atlas_prev.jpg')
    tiles = [Image.fromarray((bark(k)[0] * 255).astype(np.uint8)) for k in ('rough', 'plane', 'birch', 'palm', 'olive')]
    st = Image.new('RGB', (512 * 5, 512)); [st.paste(t, (i * 512, 0)) for i, t in enumerate(tiles)]; st.resize((1280, 256)).save('/tmp/bark_prev.jpg')

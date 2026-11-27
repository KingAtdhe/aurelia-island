"""Concept 16: city blocks with depth. Four building types for the glass-tower core and the streets round it, built from
boxes (each box = one cuboid, per material) so the game versions can be merged per material like the HD city.
Every type has real relief: window reveals, mullions and fins, spandrels, cornices, balconies, a roof crown.
build(kind, seed) -> { material name: [ (centre xyz, size xyz), ... ] }, footprint (w, d), height."""
import numpy as np

def _add(B, mat, c, s): B.setdefault(mat, []).append((tuple(map(float, c)), tuple(map(float, s))))

def curtain_face(B, x0, x1, y, z0, z1, floor_h, bay, outward, fin_d=0.35, spandrel=True, fins='Alu', glass='Glass', sp='Spandrel'):
    """A curtain-wall face along x at depth y (outward +1 / -1): glass set back, a fin at every bay, a spandrel band at every floor."""
    w = x1 - x0; n = max(1, int(round(w / bay))); bw = w / n; floors = int(round((z1 - z0) / floor_h))
    _add(B, glass, ((x0 + x1) / 2, y - outward * 0.12, (z0 + z1) / 2), (w, 0.05, z1 - z0))
    for k in range(n + 1):
        _add(B, fins, (x0 + k * bw, y + outward * fin_d / 2, (z0 + z1) / 2), (0.09, fin_d, z1 - z0))
    for f in range(floors + 1):
        z = z0 + f * floor_h
        if spandrel and f < floors: _add(B, sp, ((x0 + x1) / 2, y - outward * 0.06, z + 0.45), (w, 0.08, 0.9))
        _add(B, fins, ((x0 + x1) / 2, y + outward * 0.06, z), (w, 0.14, 0.07))

def punched_face(B, x0, x1, y, z0, z1, floor_h, bay, outward, win_w=1.5, win_h=2.0, reveal=0.32, wall='Stone', frame='Frame', glass='GlassDark', sill='Stone'):
    """Masonry wall with punched windows set back in deep reveals: full-height piers between the window columns,
    a wall band between the floors, a projecting sill course under each row of windows, the glazing behind."""
    w = x1 - x0; n = max(1, int(round(w / bay))); bw = w / n; floors = int(round((z1 - z0) / floor_h))
    ym = y - outward * reveal / 2
    _add(B, glass, ((x0 + x1) / 2, y - outward * (reveal + 0.04), (z0 + z1) / 2), (w, 0.04, z1 - z0))          # glazing behind
    pw = bw - win_w
    for k in range(n + 1):          # piers, the full height of the face
        cx = x0 + k * bw; ww = pw if 0 < k < n else pw / 2
        cx = cx if 0 < k < n else (cx + ww / 2 if k == 0 else cx - ww / 2)
        _add(B, wall, (cx, ym, (z0 + z1) / 2), (ww, reveal, z1 - z0))
    zs = [z0 + f * floor_h + (floor_h - win_h) * 0.55 for f in range(floors)]          # window bottoms
    bands = [(z0, zs[0])] + [(zs[f] + win_h, zs[f + 1]) for f in range(floors - 1)] + [(zs[-1] + win_h, z1)]
    for a, b in bands:          # wall between one row of windows and the next
        if b - a > 0.02: _add(B, wall, ((x0 + x1) / 2, ym, (a + b) / 2), (w, reveal, b - a))
    for zb in zs:          # sill course
        _add(B, sill, ((x0 + x1) / 2, y + outward * 0.05, zb - 0.05), (w + 0.1, 0.18, 0.1))
    if frame:          # one slim mullion in each window
        for k in range(n): _add(B, frame, (x0 + (k + 0.5) * bw, y - outward * (reveal - 0.03), (z0 + z1) / 2), (0.05, 0.05, z1 - z0))

def box_faces(B, w, d, z0, z1, face, **kw):
    """Run a face function round all four sides of a w x d block (x faces use the same function rotated)."""
    out = {}
    face(out, -w / 2, w / 2, -d / 2, z0, z1, outward=-1, **kw); face(out, -w / 2, w / 2, d / 2, z0, z1, outward=1, **kw)
    side = {}; face(side, -d / 2, d / 2, w / 2, z0, z1, outward=1, **kw); face(side, -d / 2, d / 2, -w / 2, z0, z1, outward=-1, **kw)
    for m, L in side.items():
        for c, s in L: out.setdefault(m, []).append(((c[1], c[0], c[2]), (s[1], s[0], s[2])))
    for m, L in out.items(): B.setdefault(m, []).extend(L)

def roof_plant(B, w, d, z, rng, screen=True):
    """Roof: parapet, plant room, AC units, a water tank, louvred screen."""
    for sx, sy, cx, cy in ((w, 0.3, 0, d / 2), (w, 0.3, 0, -d / 2), (0.3, d, w / 2, 0), (0.3, d, -w / 2, 0)):
        _add(B, 'Coping', (cx, cy, z + 0.55), (sx, sy, 1.1))
    pw, pd = w * 0.45, d * 0.4
    _add(B, 'Plant', (0, 0, z + 2.0), (pw, pd, 4.0))
    if screen:
        for k in range(int(pw / 0.5) + 1): _add(B, 'Louvre', (-pw / 2 + k * 0.5, pd / 2 + 0.3, z + 2.3), (0.06, 0.25, 4.6))
    for k in range(int(rng.integers(4, 9))):
        _add(B, 'Plant', (rng.uniform(-1, 1) * max(0.1, w / 2 - 2), rng.uniform(-1, 1) * max(0.1, d / 2 - 2), z + 0.6), (1.4, 1.0, 1.2))
    _add(B, 'Tank', (w * 0.3, -d * 0.25, z + 1.4), (2.4, 2.4, 2.8))

def office_glass(seed=1, w=30.0, d=24.0, floors=24):
    """A: glass office tower: fin-ribbed curtain wall, a two-storey lobby, two setbacks, a lit crown with a plant screen."""
    rng = np.random.default_rng(seed); B = {}; fh = 3.6
    _add(B, 'Stone', (0, 0, 3.5), (w, d, 7.0)); box_faces(B, w - 0.2, d - 0.2, 0.3, 6.8, curtain_face, floor_h=6.5, bay=3.0, fin_d=0.12, spandrel=False, glass='GlassLobby')
    _add(B, 'Canopy', (0, -d / 2 - 2.0, 6.0), (w * 0.5, 4.0, 0.35))
    z = 7.0; ww, dd = w, d
    for part, nf in ((0, floors - 8), (1, 5), (2, 3)):
        _add(B, 'Core', (0, 0, z + nf * fh / 2), (ww - 1.2, dd - 1.2, nf * fh))
        box_faces(B, ww, dd, z, z + nf * fh, curtain_face, floor_h=fh, bay=3.0, fin_d=0.24)          # game: wider bays, slimmer fins (more glass)
        z += nf * fh; _add(B, 'Coping', (0, 0, z + 0.25), (ww + 0.3, dd + 0.3, 0.5)); ww = max(10.0, ww - 4.0); dd = max(10.0, dd - 3.0)
    _add(B, 'CrownLight', (0, 0, z + 1.0), (ww + 3.0, dd + 2.5, 0.25))
    roof_plant(B, ww + 3.5, dd + 2.5, z, rng)
    return B, (w, d), z + 5.0

def office_stone(seed=2, w=26.0, d=20.0, floors=11):
    """B: stone-clad office (1930s): rusticated arcade base, punched windows in deep reveals, pilasters, a heavy cornice."""
    rng = np.random.default_rng(seed); B = {}; fh = 3.8
    _add(B, 'Core', (0, 0, 2.5), (w - 1.0, d - 1.0, 5.0)); _add(B, 'GlassLobby', (0, 0, 2.6), (w - 1.4, d - 1.4, 4.8))
    for k in range(9):          # arcade piers
        x = -w / 2 + k * w / 8
        for yy in (-d / 2, d / 2): _add(B, 'StoneDark', (x, yy, 2.6), (1.1, 1.0, 5.2))
    for k in range(7):
        y = -d / 2 + k * d / 6
        for xx in (-w / 2, w / 2): _add(B, 'StoneDark', (xx, y, 2.6), (1.0, 1.1, 5.2))
    _add(B, 'StoneDark', (0, 0, 5.6), (w + 0.4, d + 0.4, 0.8))
    z0 = 6.0; z1 = z0 + floors * fh
    box_faces(B, w, d, z0, z1, punched_face, floor_h=fh, bay=3.2, win_w=1.7, win_h=2.3, reveal=0.38)
    for k in range(5):          # pilasters
        x = -w / 2 + 1.6 + k * (w - 3.2) / 4
        _add(B, 'Stone', (x, -d / 2 - 0.15, (z0 + z1) / 2), (0.9, 0.35, z1 - z0))
    _add(B, 'StoneDark', (0, 0, z1 + 0.5), (w + 1.6, d + 1.6, 1.0)); _add(B, 'Stone', (0, 0, z1 + 1.2), (w + 0.6, d + 0.6, 0.5))
    roof_plant(B, w, d, z1 + 1.4, rng, screen=False)
    return B, (w, d), z1 + 4.0

def residential(seed=3, w=24.0, d=16.0, floors=9):
    """C: residential mid-rise: rendered wall with timber bands, balconies with glass rails, AC units, a roof terrace pergola."""
    rng = np.random.default_rng(seed); B = {}; fh = 3.1
    _add(B, 'Core', (0, 0, 2.5), (w, d, 5.0)); _add(B, 'GlassLobby', (0, -d / 2 - 0.05, 2.4), (w - 2, 0.1, 4.0))
    z0 = 5.0; z1 = z0 + floors * fh
    box_faces(B, w, d, z0, z1, punched_face, floor_h=fh, bay=3.0, win_w=1.9, win_h=2.2, reveal=0.22, wall='Render', frame='FrameDark', sill='Render')
    for f in range(floors):
        z = z0 + f * fh
        _add(B, 'Timber', (0, -d / 2 + 0.02, z + 0.15), (w + 0.1, 0.1, 0.3))
        nb = max(2, int(w / 6.0))
        for k in range(nb):
            x = -w / 2 + w / nb * (k + 0.5); bw = min(4.2, w / nb - 1.6)
            _add(B, 'Slab', (x, -d / 2 - 0.85, z + 0.1), (bw, 1.7, 0.2))
            _add(B, 'GlassRail', (x, -d / 2 - 1.68, z + 0.65), (bw, 0.04, 0.95))
            _add(B, 'FrameDark', (x, -d / 2 - 1.68, z + 1.13), (bw, 0.06, 0.05))
            if rng.random() < 0.45: _add(B, 'Plant', (x + bw * 0.35, -d / 2 - 0.5, z + 0.5), (0.8, 0.3, 0.6))          # AC unit
            if rng.random() < 0.35: _add(B, 'Foliage', (x - bw * 0.3, -d / 2 - 1.2, z + 0.55), (0.6, 0.6, 0.7))       # potted plant
    _add(B, 'Coping', (0, 0, z1 + 0.3), (w + 0.4, d + 0.4, 0.6))
    for k in range(7): _add(B, 'Timber', (-w / 2 + 3 + k * 1.8, -d / 4, z1 + 3.0), (0.18, d * 0.45, 0.22))         # pergola
    for x in (-w / 2 + 3, -w / 2 + 3 + 6 * 1.8):
        for y in (-d / 2 + 1, 0): _add(B, 'Timber', (x, y, z1 + 1.5), (0.2, 0.2, 3.0))
    _add(B, 'Plant', (w * 0.25, d * 0.2, z1 + 1.5), (4, 3, 3))
    return B, (w, d), z1 + 3.5

def mixed_tower(seed=4, w=22.0, d=22.0, floors=30, podium=None):
    """D: mixed-use: a five-storey podium with shopfront canopies, a slender banded tower, a sloped glass crown."""
    rng = np.random.default_rng(seed); B = {}; fh = 3.4
    pw, pd = podium if podium else (w + 14, d + 10)
    _add(B, 'Core', (0, 0, 9), (pw - 1, pd - 1, 18)); box_faces(B, pw, pd, 0, 5, curtain_face, floor_h=5, bay=4.0, fin_d=0.1, spandrel=False, glass='GlassLobby')
    box_faces(B, pw, pd, 5, 18, punched_face, floor_h=3.25, bay=2.6, win_w=1.9, win_h=2.2, reveal=0.25, wall='Panel', frame='Frame', sill='Panel')
    for k in range(4): _add(B, 'Canopy', (-pw / 2 + 4 + k * (pw - 8) / 3, -pd / 2 - 1.2, 4.2), (6, 2.4, 0.2))
    _add(B, 'Coping', (0, 0, 18.3), (pw + 0.3, pd + 0.3, 0.6))
    z0 = 18.6; z1 = z0 + floors * fh
    _add(B, 'Core', (0, 0, (z0 + z1) / 2), (w - 1, d - 1, z1 - z0))
    box_faces(B, w, d, z0, z1, curtain_face, floor_h=fh, bay=2.4, fin_d=0.16)
    for f in range(0, floors, 2): _add(B, 'Band', (0, 0, z0 + f * fh + 0.2), (w + 0.6, d + 0.6, 0.35))       # white bands every other floor
    for k in range(6):          # stepped glass crown
        s = 1.0 - k * 0.13; _add(B, 'GlassCrown', (0, 0, z1 + 1.0 + k * 1.6), (w * s, d * s, 1.6))
        _add(B, 'CrownLight', (0, 0, z1 + 0.25 + k * 1.6 + 1.6), (w * s + 0.2, d * s + 0.2, 0.12))
    _add(B, 'Alu', (0, 0, z1 + 14), (0.4, 0.4, 8))          # mast
    return B, (pw, pd), z1 + 18

KINDS = { 'office_glass': office_glass, 'office_stone': office_stone, 'residential': residential, 'mixed_tower': mixed_tower }


def fit(kind, w, d, h, seed=1):
    """A building of this kind on a plot w x d (m) standing about h m tall (the height of the tower it replaces)."""
    if kind == 'office_glass': return office_glass(seed, w, d, max(10, int(round((h - 12.0) / 3.6))))
    if kind == 'office_stone': return office_stone(seed, w, d, max(6, int(round((h - 10.0) / 3.8))))
    if kind == 'residential': return residential(seed, w, d, max(6, int(round((h - 8.5) / 3.1))))
    tw, td = max(14.0, w * 0.62), max(14.0, d * 0.62)
    return mixed_tower(seed, tw, td, max(10, int(round((h - 37.0) / 3.4))), podium=(w, d))

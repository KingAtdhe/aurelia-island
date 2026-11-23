"""Zones painted on the Mira body: every border is a curve (zero isoline of a signed function of position) the mesh is cut along.
Coordinates are sheet coordinates: s from the nose, y left, z up. Functions are negative inside their zone."""
import numpy as np
from matplotlib.path import Path
from mira_sdf import crs, sstep, interp, BELT, FS, RS, R

def poly_sd(pts, a, b):
    """Signed distance from (a, b) points to a closed polygon pts (negative inside)."""
    P = np.asarray(pts, float); Q = np.c_[a, b]; A = P; B = np.roll(P, -1, 0)
    d = np.full(len(Q), np.inf)
    for i in range(0, len(A), 64):                                 # chunks keep memory small
        a0 = A[i:i + 64][None]; ab = (B[i:i + 64] - A[i:i + 64])[None]; ap = Q[:, None] - a0
        t = np.clip((ap * ab).sum(2) / np.maximum((ab * ab).sum(2), 1e-12), 0, 1)
        d = np.minimum(d, np.sqrt(((ap - ab * t[..., None]) ** 2).sum(2)).min(1))
    inside = Path(P).contains_points(Q); return np.where(inside, -d, d)
def line_d(pts, a, b):
    P = np.asarray(pts, float); Q = np.c_[a, b]; A = P[:-1]; ab = P[1:] - P[:-1]; ap = Q[:, None] - A[None]
    t = np.clip((ap * ab[None]).sum(2) / np.maximum((ab * ab).sum(1), 1e-12)[None], 0, 1)
    return np.sqrt(((ap - ab[None] * t[..., None]) ** 2).sum(2)).min(1)
def closed(top, bot, n=10): return np.vstack([crs(top, n), crs(bot, n)])
def mask(g, ok): return np.where(ok, g, np.maximum(g, 0.05))           # outside the mask the point is never inside

SQ = 1 / np.sqrt(2)
# --- glass and pillars (side view s, z)
DLO = closed([(1.07, 1.005), (1.42, 1.215), (1.80, 1.385), (2.6, 1.418), (3.32, 1.400), (3.55, 1.33), (3.74, 1.19)], [(3.74, 1.19), (3.52, 1.115), (2.4, 1.075), (1.07, 1.005)])
CPIL = [(3.20, 1.43), (3.36, 1.43), (3.60, 1.32), (3.80, 1.19), (3.62, 1.13), (3.26, 1.10)]
BPIL = [(2.30, 1.45), (2.41, 1.45), (2.425, 1.05), (2.315, 1.05)]
SAIL = [(1.05, 1.0), (1.40, 1.205), (1.44, 1.17), (1.32, 1.02)]
WS = closed([(0.985, -0.001), (0.99, 0.50), (1.03, 0.66), (1.10, 0.705)], [(1.10, 0.705), (1.70, 0.57), (1.785, 0.50), (1.80, -0.001)])   # windscreen, plan (s, y), half
RG = closed([(0.0, 1.07), (0.60, 1.085), (0.655, 1.11)], [(0.655, 1.11), (0.57, 1.30), (0.49, 1.365), (0.0, 1.38)])                     # rear glass, rear view (|y|, z)
# --- lamps, drawn in a diagonal view across each corner: u = (y + s) / sqrt2 at the front, (y + 4.25 - s) / sqrt2 at the rear
HL = closed([(0.24, 0.708), (0.45, 0.712), (0.65, 0.728), (0.85, 0.762), (1.05, 0.818)], [(1.05, 0.818), (0.97, 0.786), (0.80, 0.708), (0.62, 0.650), (0.40, 0.628), (0.24, 0.630)])
HL_DRL = [(0.26, 0.697), (0.45, 0.701), (0.65, 0.716), (0.85, 0.748), (1.02, 0.800)]
TL = closed([(0.29, 0.990), (0.45, 0.996), (0.61, 1.0), (0.75, 0.996), (0.86, 0.986)], [(0.86, 0.986), (0.84, 0.958), (0.72, 0.930), (0.60, 0.905), (0.45, 0.896), (0.29, 0.894)])
TL_BAR = [(0.31, 0.955), (0.50, 0.960), (0.70, 0.962), (0.83, 0.968)]
GRILLE = closed([(-0.56, 0.575), (0.0, 0.590), (0.56, 0.575)], [(0.50, 0.345), (0.0, 0.335), (-0.50, 0.345)])   # front view (y, z)
INTAKE = [(0.62, 0.50), (0.84, 0.53), (0.86, 0.37), (0.66, 0.36)]

def sym_y(y): return np.abs(y)

def zone_fns(nose_s=0.0):
    """Ordered list of (name, fn(s, y, z) -> g, recess depth). Later zones win where they overlap."""
    Z = []
    def side(poly, s, y, z, ymin=0.5): return mask(poly_sd(poly, s, z), sym_y(y) > ymin)
    Z.append(('Clad', lambda s, y, z: z - (0.335 + 0.125 * sstep(4.08, 4.20, s) + 0.035 * sstep(0.30, 0.10, s)), 0.0))
    Z.append(('Liner', lambda s, y, z: np.minimum(np.sqrt((s - FS) ** 2 + (z - R) ** 2), np.sqrt((s - RS) ** 2 + (z - R) ** 2)) - 0.383, 0.0))
    Z.append(('Glass', lambda s, y, z: np.minimum(np.minimum(side(DLO, s, y, z, 0.55), mask(poly_sd(WS, s, sym_y(y)), (z > 0.95) & (s < 1.9))),
                                                   mask(poly_sd(RG, sym_y(y), z), s > 3.85)), 0.007))
    Z.append(('GlassBlack', lambda s, y, z: np.minimum(np.minimum(side(CPIL, s, y, z, 0.55), side(BPIL, s, y, z, 0.55)), side(SAIL, s, y, z, 0.55)), 0.007))
    uf = lambda s, y: (sym_y(y) + s) * SQ
    ur = lambda s, y: (sym_y(y) + 4.25 - s) * SQ
    Z.append(('Lamp', lambda s, y, z: mask(poly_sd(HL, uf(s, y), z), s < 0.8), 0.005))
    Z.append(('LED', lambda s, y, z: mask(line_d(HL_DRL, uf(s, y), z) - 0.0065, s < 0.8), 0.005))
    Z.append(('Tail', lambda s, y, z: mask(poly_sd(TL, ur(s, y), z), s > 3.7), 0.005))
    Z.append(('TailBand', lambda s, y, z: mask(np.maximum(np.abs(z - 0.94) - 0.046, sym_y(y) - 0.43), s > 4.12), 0.005))
    Z.append(('TailLED', lambda s, y, z: mask(line_d(TL_BAR, ur(s, y), z) - 0.006, s > 3.7), 0.005))
    Z.append(('Reverse', lambda s, y, z: mask(np.maximum(np.abs(z - 0.915) - 0.009, np.abs(ur(s, y) - 0.50) - 0.05), s > 3.7), 0.005))
    Z.append(('Grille', lambda s, y, z: mask(poly_sd(GRILLE, y, z), s < 0.25), 0.028))
    Z.append(('Intake', lambda s, y, z: mask(poly_sd(INTAKE, sym_y(y), z), s < 0.35), 0.015))
    Z.append(('Reflector', lambda s, y, z: mask(np.maximum(np.abs(z - 0.385) - 0.016, np.abs(sym_y(y) - 0.78) - 0.06), s > 4.15), 0.0))
    global GAPS
    GAPS = gaps = [  # (projection, polyline, mask)
        ('sz', [(1.215, 1.02), (1.235, 0.75), (1.235, 0.45), (1.25, 0.32)], lambda s, y, z: sym_y(y) > 0.6),
        ('sz', [(2.355, 1.08), (2.37, 0.70), (2.375, 0.32)], lambda s, y, z: sym_y(y) > 0.6),
        ('sz', [(3.41, 1.12), (3.36, 0.92), (3.30, 0.80)] + [(RS + 0.44 * np.cos(a), R + 0.44 * np.sin(a)) for a in np.radians(np.linspace(118, 178, 9))], lambda s, y, z: sym_y(y) > 0.6),
        ('sz', [(0.36, 0.665), (0.39, 0.60), (0.415, 0.52), (0.43, 0.44)], lambda s, y, z: sym_y(y) > 0.55),
        ('sz', [(4.23, 0.862), (4.02, 0.855), (3.92, 0.76), (3.875, 0.62), (3.86, 0.56)], lambda s, y, z: sym_y(y) > 0.55),
        ('sy', [(0.995, 0.715), (0.70, 0.768), (0.45, 0.785), (0.33, 0.775)], lambda s, y, z: z > 0.70),
        ('yz', [(-0.30, 0.716), (0.0, 0.719), (0.30, 0.716)], lambda s, y, z: s < 0.2),
        ('yz', [(-0.62, 0.862), (0.0, 0.862), (0.62, 0.862)], lambda s, y, z: s > 4.1),
    ]
    def gapfn(s, y, z):
        g = np.full(len(s), 1.0)
        for proj, pl, mk in gaps:
            a, b = {'sz': (s, z), 'sy': (s, sym_y(y)), 'yz': (y, z)}[proj]
            g = np.minimum(g, mask(line_d(pl, a, b) - 0.0026, mk(s, y, z)))
        return g
    return Z

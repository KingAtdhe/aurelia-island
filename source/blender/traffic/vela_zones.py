"""Zones on the Vela body: every border is the zero isoline of a signed function of sheet position (s from the nose, y left, z up)."""
import numpy as np
from mira_zones import poly_sd, line_d, closed, mask, sym_y
from vela_sdf import crs, sstep, FS, RS, R, L

SQ = 1 / np.sqrt(2)
DLO = closed([(1.42, 0.985), (1.75, 1.17), (2.03, 1.335), (2.55, 1.385), (3.02, 1.372), (3.33, 1.285), (3.62, 1.10)], [(3.62, 1.10), (3.30, 1.075), (2.4, 1.040), (1.42, 0.985)])
BPIL = [(2.36, 1.46), (2.46, 1.46), (2.47, 1.02), (2.37, 1.02)]
QDIV = [(3.10, 1.42), (3.18, 1.42), (3.165, 1.06), (3.10, 1.06)]
WS = closed([(1.375, -0.001), (1.38, 0.50), (1.42, 0.66), (1.50, 0.725)], [(1.50, 0.725), (1.92, 0.615), (2.00, 0.53), (2.02, -0.001)])
RG = closed([(0.0, 1.095), (0.60, 1.105), (0.665, 1.125)], [(0.665, 1.125), (0.565, 1.30), (0.47, 1.365), (0.0, 1.38)])
HL = closed([(0.36, 0.786), (0.60, 0.792), (0.80, 0.795), (0.98, 0.802), (1.13, 0.815)], [(1.13, 0.815), (1.05, 0.792), (0.90, 0.758), (0.70, 0.738), (0.50, 0.732), (0.36, 0.737)])
HL_DRL = [(0.38, 0.777), (0.60, 0.783), (0.80, 0.786), (0.98, 0.793), (1.11, 0.807)]
GRILLE = closed([(-0.50, 0.718), (0.0, 0.727), (0.50, 0.718)], [(0.45, 0.582), (0.0, 0.577), (-0.45, 0.582)])
LOWER = closed([(-0.62, 0.50), (0.0, 0.51), (0.62, 0.50)], [(0.58, 0.295), (0.0, 0.285), (-0.58, 0.295)])
INTAKE = [(0.70, 0.56), (0.84, 0.58), (0.86, 0.335), (0.74, 0.325)]
DRL2 = [(0.80, 0.55), (0.83, 0.555), (0.845, 0.36), (0.815, 0.355)]
TL = closed([(0.42, 0.996), (0.60, 0.998), (0.76, 1.000), (0.88, 1.000)], [(0.88, 1.000), (0.86, 0.965), (0.75, 0.935), (0.60, 0.888), (0.42, 0.882)])
TL_BARS = [[(0.45, 0.968), (0.62, 0.970), (0.76, 0.975), (0.86, 0.985)], [(0.45, 0.935), (0.62, 0.938), (0.74, 0.952)], [(0.45, 0.905), (0.60, 0.906)]]

def zone_fns():
    Z = []
    def side(poly, s, y, z, ymin=0.63): return mask(poly_sd(poly, s, z), sym_y(y) > ymin)
    uf = lambda s, y: (sym_y(y) + s) * SQ
    ur = lambda s, y: (sym_y(y) + L - s) * SQ
    Z.append(('Clad', lambda s, y, z: z - (0.315 + 0.085 * sstep(4.40, 4.58, s) + 0.045 * sstep(0.42, 0.14, s)), 0.0))
    Z.append(('Liner', lambda s, y, z: np.minimum(np.sqrt((s - FS) ** 2 + (z - R) ** 2), np.sqrt((s - RS) ** 2 + (z - R) ** 2)) - 0.400, 0.0))
    Z.append(('Chrome', lambda s, y, z: side(DLO, s, y, z) - 0.016, 0.0))
    Z.append(('Glass', lambda s, y, z: np.minimum(np.minimum(side(DLO, s, y, z), mask(poly_sd(WS, s, sym_y(y)), (z > 0.95) & (s < 2.1))),
                                                   mask(poly_sd(RG, sym_y(y), z), (s > 3.25) & (s < 3.86))), 0.007))
    Z.append(('GlassBlack', lambda s, y, z: np.minimum(side(BPIL, s, y, z), side(QDIV, s, y, z)), 0.007))
    Z.append(('Lamp', lambda s, y, z: mask(poly_sd(HL, uf(s, y), z), s < 0.8), 0.005))
    Z.append(('Grille', lambda s, y, z: mask(poly_sd(GRILLE, y, z), s < 0.35), 0.028))
    Z.append(('Intake', lambda s, y, z: np.minimum(mask(poly_sd(LOWER, y, z), s < 0.35), mask(poly_sd(INTAKE, sym_y(y), z), s < 0.45)), 0.02))
    Z.append(('Tail', lambda s, y, z: np.minimum(mask(poly_sd(TL, ur(s, y), z), s > 4.2), mask(np.maximum(np.abs(z - 0.967) - 0.031, sym_y(y) - 0.62), s > 4.55)), 0.005))
    Z.append(('Pipe', lambda s, y, z: mask(np.maximum(np.abs(z - 0.40) - 0.024, np.abs(sym_y(y) - 0.52) - 0.10), s > 4.45), 0.03))
    return Z

# recess groups for build_body: (zone names, depth, wall material)
GROUPS = [(('Lamp',), 0.006, 'Lamp'), (('Tail',), 0.006, 'Tail'), (('Grille',), 0.03, 'Grille'), (('Intake',), 0.02, 'Intake'), (('Pipe',), 0.03, 'Intake')]

# shut lines: (projection, polyline, mask, side) ; side for 'yz' = +1 seen from the front, -1 from the rear
ARC = lambda a0, a1, r: [(RS + r * np.cos(a), R + r * np.sin(a)) for a in np.radians(np.linspace(a0, a1, 9))]
GAPS = [
    ('sz', [(1.375, 0.985), (1.39, 0.70), (1.40, 0.42), (1.42, 0.31)], lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(2.42, 1.035), (2.43, 0.70), (2.44, 0.31)], lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(3.45, 1.08), (3.42, 0.88), (3.36, 0.76)] + ARC(125, 176, 0.46), lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(1.42, 0.31), (2.4, 0.315), (3.30, 0.32)], lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(0.30, 0.79), (0.44, 0.70), (0.52, 0.55), (0.54, 0.42)], lambda s, y, z: sym_y(y) > 0.55, 0),
    ('sz', [(4.695, 0.84), (4.40, 0.83), (4.24, 0.72), (4.21, 0.52)], lambda s, y, z: sym_y(y) > 0.55, 0),
    ('sy', [(1.345, 0.70), (1.0, 0.79), (0.62, 0.835), (0.42, 0.82), (0.34, 0.60), (0.31, 0.30), (0.30, 0.0)], lambda s, y, z: z > 0.70, 0),
    ('sy', [(3.86, 0.0), (3.86, 0.78), (4.30, 0.80), (4.58, 0.76)], lambda s, y, z: z > 0.98, 0),
    ('yz', [(-0.62, 0.81), (0.62, 0.81)], lambda s, y, z: s > 4.5, -1),
    ('yz', [(0.62, 1.01), (0.63, 0.81)], lambda s, y, z: s > 4.5, -1),
    ('yz', [(-0.62, 1.01), (-0.63, 0.81)], lambda s, y, z: s > 4.5, -1),
]
FUEL = (3.96, 4.10, 0.905, 1.000)

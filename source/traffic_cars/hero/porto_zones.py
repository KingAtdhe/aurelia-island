"""Zones on the Porto body (approved sheet 04): every border is the zero isoline of a signed function of (s, y, z)."""
import numpy as np
from mira_zones import poly_sd, line_d, closed, mask, sym_y
from porto_sdf import crs, sstep, FS, RS, R, L

DLO = closed([(0.99, 1.30), (1.15, 1.58), (1.37, 1.92), (1.55, 2.035), (1.80, 2.065)], [(1.835, 2.05), (1.84, 1.60), (1.84, 1.30)])
WS = closed([(0.86, -0.001), (0.86, 0.86), (0.92, 0.905)], [(0.92, 0.905), (1.46, 0.86), (1.50, 0.82), (1.52, -0.001)])
RW = [(0.08, 1.40), (0.76, 1.40), (0.76, 1.92), (0.08, 1.92)]
GRILLE = [(-0.50, 1.02), (0.50, 1.02), (0.48, 0.74), (-0.48, 0.74)]
HLF = closed([(0.52, 1.06), (0.78, 1.08), (0.965, 1.05)], [(0.97, 0.88), (0.78, 0.86), (0.56, 0.88)])
HLS = [(0.03, 1.03), (0.44, 1.105), (0.52, 1.09), (0.46, 0.90), (0.03, 0.87)]
LOWER = [(-0.55, 0.47), (0.55, 0.47), (0.52, 0.38), (-0.52, 0.38)]

def zone_fns():
    Z = []
    def side(poly, s, y, z, ymin=0.80): return mask(poly_sd(poly, s, z), sym_y(y) > ymin)
    arch = lambda s, z: np.minimum(np.sqrt((s - FS) ** 2 + (z - R) ** 2), np.sqrt((s - RS) ** 2 + (z - R) ** 2))
    strip = lambda s, y, z: mask(np.abs(z - 0.70) - 0.042, (sym_y(y) > 0.9) & (((s > FS + 0.42) & (s < RS - 0.42)) | ((s > RS + 0.42) & (s < 5.0))))
    Z.append(('Clad', lambda s, y, z: np.minimum(np.minimum(mask(z - 0.63, s < 0.42), mask(z - 0.58, s > 4.62)), np.minimum(strip(s, y, z), z - 0.395)), 0.0))
    Z.append(('Liner', lambda s, y, z: arch(s, z) - 0.42, 0.0))
    Z.append(('Glass', lambda s, y, z: np.minimum(np.minimum(side(DLO, s, y, z), mask(poly_sd(WS, s, sym_y(y)), (z > 1.20) & (s < 1.8))),
                                                   mask(poly_sd(RW, sym_y(y), z), s > 4.98)), 0.007))
    Z.append(('Lamp', lambda s, y, z: np.minimum(mask(poly_sd(HLF, sym_y(y), z), s < 0.55), side(HLS, s, y, z, 0.80)), 0.006))
    Z.append(('Grille', lambda s, y, z: mask(poly_sd(GRILLE, y, z), s < 0.40), 0.025))
    Z.append(('Intake', lambda s, y, z: mask(poly_sd(LOWER, y, z), s < 0.40), 0.02))
    Z.append(('Tail', lambda s, y, z: mask(np.maximum(np.abs(z - 0.95) - 0.33, 0.925 - sym_y(y)), s > 4.98), 0.004))
    return Z

GROUPS = [(('Lamp',), 0.008, 'Lamp'), (('Tail',), 0.004, 'Tail'), (('Grille',), 0.025, 'Grille'), (('Intake',), 0.02, 'Intake')]
GAPS = [
    ('sz', [(0.92, 1.20), (0.95, 0.95), (0.99, 0.83)] + [(FS + 0.50 * np.cos(a), R + 0.50 * np.sin(a)) for a in np.radians(np.linspace(62, 14, 6))], lambda s, y, z: sym_y(y) > 0.8, 0),
    ('sz', [(1.88, 2.08), (1.89, 1.30), (1.90, 0.42)], lambda s, y, z: sym_y(y) > 0.8, 0),
    ('sz', [(1.96, 2.04), (1.97, 1.30), (1.97, 0.42)], lambda s, y, z: sym_y(y) > 0.8, 0),
    ('sz', [(3.24, 2.04), (3.25, 1.30), (3.25, 0.80), (3.20, 0.75)], lambda s, y, z: sym_y(y) > 0.8, 0),
    ('sz', [(1.96, 2.04), (3.24, 2.04)], lambda s, y, z: sym_y(y) > 0.8, 0),
    ('sy', [(0.84, 0.90), (0.45, 0.93), (0.16, 0.92), (0.10, 0.0)], lambda s, y, z: z > 0.95, 0),
    ('yz', [(0.0, 2.08), (0.0, 0.60)], lambda s, y, z: s > 4.98, -1),
    ('yz', [(0.88, 2.08), (0.88, 0.60)], lambda s, y, z: s > 4.98, -1),
    ('yz', [(-0.88, 2.08), (-0.88, 0.60)], lambda s, y, z: s > 4.98, -1),
    ('yz', [(-0.88, 2.08), (0.88, 2.08)], lambda s, y, z: s > 4.98, -1),
]
FUEL = (1.98, 2.13, 0.87, 0.98)

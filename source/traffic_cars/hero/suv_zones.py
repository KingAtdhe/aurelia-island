"""Zones on the SUV body (traced from the reference): every border is the zero isoline of a signed function of (s, y, z)."""
import numpy as np
from mira_zones import poly_sd, line_d, closed, mask, sym_y
from suv_sdf import crs, sstep, FS, RS, R, L

DLO = closed([(1.30, 1.405), (1.45, 1.580), (1.62, 1.745), (1.76, 1.812), (2.0, 1.818), (4.0, 1.818), (4.14, 1.795), (4.17, 1.70)],
             [(4.17, 1.70), (4.17, 1.405), (2.6, 1.403), (1.30, 1.405)])
BPIL = [(2.48, 1.84), (2.60, 1.84), (2.60, 1.38), (2.48, 1.38)]
QDIV = [(3.28, 1.84), (3.46, 1.84), (3.46, 1.38), (3.28, 1.38)]
WS = closed([(1.20, -0.001), (1.20, 0.76), (1.25, 0.81)], [(1.25, 0.81), (1.70, 0.70), (1.75, 0.66), (1.76, -0.001)])
RG = closed([(0.0, 1.43), (0.70, 1.43), (0.73, 1.46)], [(0.73, 1.46), (0.68, 1.77), (0.64, 1.80), (0.0, 1.80)])
GRILLE = closed([(-0.42, 1.185), (0.42, 1.185), (0.45, 1.165)], [(0.45, 1.165), (0.45, 1.015), (0.42, 0.995), (-0.42, 0.995), (-0.45, 1.015), (-0.45, 1.165), (-0.42, 1.185)])
HLF = closed([(0.48, 1.18), (0.84, 1.18), (0.90, 1.15)], [(0.90, 1.15), (0.88, 1.01), (0.48, 1.01)])
LOWER = closed([(-0.70, 0.665), (0.70, 0.665)], [(0.70, 0.585), (-0.70, 0.585)])
TLR = closed([(0.70, 1.33), (0.94, 1.33)], [(0.94, 1.02), (0.70, 1.02)])

def zone_fns():
    Z = []
    def side(poly, s, y, z, ymin=0.70): return mask(poly_sd(poly, s, z), sym_y(y) > ymin)
    arch = lambda s, z: np.minimum(np.sqrt((s - FS) ** 2 + (z - R) ** 2), np.sqrt((s - RS) ** 2 + (z - R) ** 2))
    Z.append(('Clad', lambda s, y, z: np.minimum(z - (0.56 + 0.17 * sstep(0.48, 0.30, s) + 0.08 * sstep(4.40, 4.58, s)), arch(s, z) - 0.545), 0.0))
    Z.append(('Liner', lambda s, y, z: arch(s, z) - 0.455, 0.0))
    Z.append(('Trim', lambda s, y, z: side(DLO, s, y, z) - 0.020, 0.0))
    Z.append(('Glass', lambda s, y, z: np.minimum(np.minimum(side(DLO, s, y, z), mask(poly_sd(WS, s, sym_y(y)), (z > 1.38) & (s < 1.9))),
                                                   mask(poly_sd(RG, sym_y(y), z), s > 4.25)), 0.007))
    Z.append(('GlassBlack', lambda s, y, z: np.minimum(side(BPIL, s, y, z), side(QDIV, s, y, z)), 0.007))
    Z.append(('Lamp', lambda s, y, z: mask(poly_sd(HLF, sym_y(y), z), s < 0.35), 0.005))
    Z.append(('Grille', lambda s, y, z: mask(poly_sd(GRILLE, y, z), s < 0.30), 0.02))
    Z.append(('Intake', lambda s, y, z: mask(poly_sd(LOWER, y, z), s < 0.35), 0.02))
    Z.append(('Tail', lambda s, y, z: mask(poly_sd(TLR, sym_y(y), z), s > 4.45), 0.005))
    return Z

GROUPS = [(('Lamp',), 0.006, 'Lamp'), (('Tail',), 0.006, 'Tail'), (('Grille',), 0.02, 'Grille'), (('Intake',), 0.02, 'Intake')]
GAPS = [
    ('sz', [(1.29, 1.40), (1.30, 1.00), (1.31, 0.57)], lambda s, y, z: sym_y(y) > 0.7, 0),
    ('sz', [(2.55, 1.40), (2.56, 1.00), (2.57, 0.57)], lambda s, y, z: sym_y(y) > 0.7, 0),
    ('sz', [(3.40, 1.40), (3.41, 1.00), (3.42, 0.60)], lambda s, y, z: sym_y(y) > 0.7, 0),
    ('sy', [(1.16, 0.84), (0.6, 0.88), (0.25, 0.88), (0.13, 0.84), (0.10, 0.0)], lambda s, y, z: z > 1.15, 0),
    ('yz', [(-0.67, 0.68), (0.67, 0.68)], lambda s, y, z: s > 4.4, -1),
    ('yz', [(0.67, 1.82), (0.67, 0.68)], lambda s, y, z: s > 4.4, -1),
    ('yz', [(-0.67, 1.82), (-0.67, 0.68)], lambda s, y, z: s > 4.4, -1),
]
FUEL = (3.98, 4.11, 1.12, 1.24)

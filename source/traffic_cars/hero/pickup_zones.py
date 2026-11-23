"""Zones on the Pickup body (traced from the reference): every border is the zero isoline of a signed function of (s, y, z)."""
import numpy as np
from mira_zones import poly_sd, line_d, closed, mask, sym_y
from pickup_sdf import crs, sstep, FS, RS, R, L

DLO = np.array([(1.38, 1.36), (1.55, 1.50), (1.80, 1.67), (2.00, 1.75), (2.20, 1.775), (3.38, 1.78), (3.45, 1.745), (3.47, 1.36)])
BPIL = np.array([(2.56, 1.80), (2.67, 1.80), (2.67, 1.34), (2.56, 1.34)])
WS = closed([(1.30, -0.001), (1.30, 0.74), (1.35, 0.80)], [(1.35, 0.80), (2.05, 0.70), (2.10, 0.66), (2.11, -0.001)])
RGC = np.array([(0.0, 1.47), (0.64, 1.47), (0.66, 1.49), (0.64, 1.76), (0.0, 1.76)])
GRILLE = np.array([(-0.58, 0.80), (0.58, 0.80), (0.60, 0.82), (0.60, 1.13), (0.58, 1.15), (-0.58, 1.15), (-0.60, 1.13), (-0.60, 0.82)])
HLF = np.array([(0.61, 0.90), (0.94, 0.90), (0.94, 1.15), (0.61, 1.15)])
LOWER = np.array([(-0.50, 0.53), (0.50, 0.53), (0.50, 0.61), (-0.50, 0.61)])

def zone_fns():
    Z = []
    def side(poly, s, y, z, ymin=0.70): return mask(poly_sd(poly, s, z), sym_y(y) > ymin)
    arch = lambda s, z: np.minimum(np.sqrt((s - FS) ** 2 + (z - R) ** 2), np.sqrt((s - RS) ** 2 + (z - R) ** 2))
    bedin = lambda s, y, z: np.maximum(np.maximum(np.abs(s - 4.525) - 0.765, np.abs(y) - 0.915), z - 1.395)
    Z.append(('Clad', lambda s, y, z: np.minimum(np.minimum(z - 0.56, arch(s, z) - 0.585), np.minimum(mask(z - 0.78, s < 0.42), mask(z - 0.85, s > 5.33))), 0.0))
    Z.append(('Liner', lambda s, y, z: np.minimum(arch(s, z) - 0.48, bedin(s, y, z)), 0.0))
    Z.append(('Trim', lambda s, y, z: side(DLO, s, y, z) - 0.020, 0.0))
    Z.append(('Glass', lambda s, y, z: np.minimum(np.minimum(side(DLO, s, y, z), mask(poly_sd(WS, s, sym_y(y)), (z > 1.34) & (s < 2.2))),
                                                   mask(poly_sd(RGC, sym_y(y), z), (s > 3.55) & (s < 3.75) & (z > 1.43))), 0.007))
    Z.append(('GlassBlack', lambda s, y, z: side(BPIL, s, y, z), 0.007))
    Z.append(('Lamp', lambda s, y, z: mask(poly_sd(HLF, sym_y(y), z), s < 0.30), 0.006))
    Z.append(('Grille', lambda s, y, z: mask(poly_sd(GRILLE, y, z), s < 0.30), 0.025))
    Z.append(('Intake', lambda s, y, z: mask(poly_sd(LOWER, y, z), s < 0.45), 0.02))
    Z.append(('Tail', lambda s, y, z: mask(np.maximum(np.abs(z - 1.04) - 0.18, 0.835 - sym_y(y)), s > 5.20), 0.004))
    return Z

GROUPS = [(('Lamp',), 0.006, 'Lamp'), (('Tail',), 0.004, 'Tail'), (('Grille',), 0.025, 'Grille'), (('Intake',), 0.02, 'Intake')]
GAPS = [
    ('sz', [(1.30, 1.36), (1.31, 1.00), (1.34, 0.57)], lambda s, y, z: sym_y(y) > 0.8, 0),
    ('sz', [(2.61, 1.36), (2.61, 1.00), (2.61, 0.57)], lambda s, y, z: sym_y(y) > 0.8, 0),
    ('sz', [(3.55, 1.36), (3.55, 1.00), (3.55, 0.57)], lambda s, y, z: sym_y(y) > 0.8, 0),
    ('sz', [(3.71, 1.41), (3.71, 1.00), (3.71, 0.57)], lambda s, y, z: sym_y(y) > 0.8, 0),
    ('sy', [(1.27, 0.86), (0.6, 0.90), (0.20, 0.90), (0.12, 0.0)], lambda s, y, z: z > 1.10, 0),
    ('yz', [(-0.82, 1.41), (0.82, 1.41)], lambda s, y, z: s > 5.2, -1),
    ('yz', [(-0.82, 0.86), (0.82, 0.86)], lambda s, y, z: s > 5.2, -1),
    ('yz', [(0.82, 1.41), (0.82, 0.86)], lambda s, y, z: s > 5.2, -1),
    ('yz', [(-0.82, 1.41), (-0.82, 0.86)], lambda s, y, z: s > 5.2, -1),
]
FUEL = (3.78, 3.90, 1.13, 1.24)

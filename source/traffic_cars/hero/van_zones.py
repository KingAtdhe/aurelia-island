"""Zones on the Van body (traced from the reference): every border is the zero isoline of a signed function of (s, y, z)."""
import numpy as np
from mira_zones import poly_sd, line_d, closed, mask, sym_y
from van_sdf import crs, sstep, FS, RS, R, L

DLO = np.array([(1.08, 1.64), (1.50, 2.22), (1.57, 2.30), (2.08, 2.30), (2.10, 2.27), (2.10, 1.66), (2.07, 1.645)])
QTR = np.array([(0.86, 1.645), (1.14, 1.43), (1.30, 1.43), (1.06, 1.625)])
WS = closed([(0.80, -0.001), (0.80, 0.84), (0.86, 0.885)], [(0.86, 0.885), (1.40, 0.80), (1.44, 0.76), (1.45, -0.001)])
RW = np.array([(0.13, 1.62), (0.79, 1.62), (0.79, 2.30), (0.13, 2.30)])
GRILLE = np.array([(-0.53, 0.965), (0.53, 0.965), (0.53, 1.20), (-0.53, 1.20)])
HLF = np.array([(0.57, 0.975), (0.90, 0.975), (0.90, 1.195), (0.57, 1.195)])
LOWER = np.array([(-0.42, 0.47), (0.42, 0.47), (0.42, 0.55), (-0.42, 0.55)])

def zone_fns():
    Z = []
    def side(poly, s, y, z, ymin=0.78): return mask(poly_sd(poly, s, z), sym_y(y) > ymin)
    arch = lambda s, z: np.minimum(np.sqrt((s - FS) ** 2 + (z - R) ** 2), np.sqrt((s - RS) ** 2 + (z - R) ** 2))
    Z.append(('Clad', lambda s, y, z: np.minimum(mask(z - 0.865, s < 0.36), mask(z - 0.81, s > 4.62)), 0.0))
    Z.append(('Liner', lambda s, y, z: arch(s, z) - 0.465, 0.0))
    Z.append(('Trim', lambda s, y, z: side(DLO, s, y, z) - 0.018, 0.0))
    Z.append(('Glass', lambda s, y, z: np.minimum(np.minimum(side(DLO, s, y, z), mask(poly_sd(WS, s, sym_y(y)), (z > 1.60) & (s < 1.6))),
                                                   mask(poly_sd(RW, sym_y(y), z) - 0.0, s > 4.6)), 0.007))
    Z.append(('GlassBlack', lambda s, y, z: side(QTR, s, y, z), 0.007))
    Z.append(('Lamp', lambda s, y, z: mask(poly_sd(HLF, sym_y(y), z) + 0.0, s < 0.40), 0.008))
    Z.append(('Grille', lambda s, y, z: mask(poly_sd(GRILLE, y, z), s < 0.30), 0.025))
    Z.append(('Intake', lambda s, y, z: mask(poly_sd(LOWER, y, z), s < 0.30), 0.02))
    Z.append(('Tail', lambda s, y, z: mask(np.maximum(np.abs(z - 1.165) - 0.21, 0.885 - sym_y(y)), s > 4.55), 0.004))
    return Z

GROUPS = [(('Lamp',), 0.008, 'Lamp'), (('Tail',), 0.004, 'Tail'), (('Grille',), 0.025, 'Grille'), (('Intake',), 0.02, 'Intake')]
GAPS = [
    ('sz', [(1.02, 1.43), (1.03, 1.00), (1.02, 0.86)] + [(FS + 0.49 * np.cos(a), R + 0.49 * np.sin(a)) for a in np.radians(np.linspace(60, 20, 5))], lambda s, y, z: sym_y(y) > 0.8, 0),
    ('sz', [(2.21, 2.47), (2.21, 1.40), (2.21, 0.46)], lambda s, y, z: sym_y(y) > 0.8, 0),
    ('sz', [(2.33, 2.47), (2.33, 1.40), (2.33, 0.46)], lambda s, y, z: sym_y(y) > 0.8, 0),
    ('sz', [(4.38, 2.47), (4.38, 1.40), (4.38, 0.86)], lambda s, y, z: sym_y(y) > 0.8, 0),
    ('sy', [(0.78, 0.90), (0.40, 0.93), (0.16, 0.92), (0.10, 0.0)], lambda s, y, z: z > 1.30, 0),
    ('yz', [(0.0, 2.47), (0.0, 0.83)], lambda s, y, z: s > 4.6, -1),
    ('yz', [(0.86, 2.47), (0.86, 0.83)], lambda s, y, z: s > 4.6, -1),
    ('yz', [(-0.86, 2.47), (-0.86, 0.83)], lambda s, y, z: s > 4.6, -1),
    ('yz', [(-0.86, 2.47), (0.86, 2.47)], lambda s, y, z: s > 4.6, -1),
]
FUEL = (4.05, 4.17, 1.00, 1.11)

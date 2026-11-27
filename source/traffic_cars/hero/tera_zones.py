"""Zones on the Tera body (approved sheet 03): every border is the zero isoline of a signed function of (s, y, z)."""
import numpy as np
from mira_zones import poly_sd, line_d, closed, mask, sym_y
from tera_sdf import crs, sstep, FS, RS, R, L

DLO = closed([(1.36, 1.165), (1.62, 1.385), (1.98, 1.565), (2.6, 1.600), (3.5, 1.598), (3.98, 1.578), (4.15, 1.50), (4.21, 1.255)],
             [(4.21, 1.255), (3.5, 1.225), (2.4, 1.195), (1.36, 1.165)])
BPIL = [(2.42, 1.64), (2.53, 1.64), (2.54, 1.17), (2.43, 1.17)]
CPIL = [(3.40, 1.64), (3.47, 1.64), (3.47, 1.20), (3.40, 1.20)]
DPIL = [(3.86, 1.64), (4.34, 1.64), (4.34, 1.20), (3.97, 1.21), (3.92, 1.40)]
WS = closed([(1.30, -0.001), (1.31, 0.55), (1.36, 0.69), (1.44, 0.745)], [(1.44, 0.745), (1.86, 0.655), (1.93, 0.58), (1.95, -0.001)])
RG = closed([(0.0, 1.275), (0.64, 1.29), (0.68, 1.31)], [(0.68, 1.31), (0.62, 1.52), (0.55, 1.565), (0.0, 1.575)])
GRILLE = closed([(-0.50, 0.885), (0.50, 0.885)], [(0.43, 0.585), (-0.43, 0.585)])
HLB = closed([(0.53, 0.893), (0.70, 0.902), (0.90, 0.878)], [(0.905, 0.852), (0.70, 0.866), (0.55, 0.862)])        # slim DRL blade
HLM = [(0.61, 0.765), (0.87, 0.765), (0.87, 0.635), (0.61, 0.635)]                                                # main lamp low in the bumper
LOWER = closed([(-0.50, 0.51), (0.50, 0.51)], [(0.46, 0.415), (-0.46, 0.415)])
SKID = closed([(-0.44, 0.395), (0.44, 0.395)], [(0.40, 0.315), (-0.40, 0.315)])
TLR = [(0.50, 1.215), (0.90, 1.205), (0.93, 1.05), (0.80, 1.05), (0.78, 1.14), (0.50, 1.15)]
TLS = [(4.475, 1.245), (4.18, 1.255), (4.15, 1.19), (4.48, 1.10)]

def zone_fns():
    Z = []
    def side(poly, s, y, z, ymin=0.60): return mask(poly_sd(poly, s, z), sym_y(y) > ymin)
    arch = lambda s, z: np.minimum(np.sqrt((s - FS) ** 2 + (z - R) ** 2), np.sqrt((s - RS) ** 2 + (z - R) ** 2))
    Z.append(('Clad', lambda s, y, z: np.minimum(z - (0.44 + 0.13 * sstep(0.48, 0.12, s) + 0.12 * sstep(4.12, 4.38, s)), arch(s, z) - 0.505), 0.0))
    Z.append(('Liner', lambda s, y, z: arch(s, z) - 0.43, 0.0))
    Z.append(('Glass', lambda s, y, z: np.minimum(np.minimum(side(DLO, s, y, z), mask(poly_sd(WS, s, sym_y(y)), (z > 1.10) & (s < 2.05))),
                                                   mask(poly_sd(RG, sym_y(y), z), s > 4.20)), 0.007))
    Z.append(('GlassBlack', lambda s, y, z: np.minimum(np.minimum(side(BPIL, s, y, z), side(CPIL, s, y, z)), side(DPIL, s, y, z, 0.55)), 0.007))
    Z.append(('Lamp', lambda s, y, z: mask(np.minimum(poly_sd(HLB, sym_y(y), z), poly_sd(HLM, sym_y(y), z)), s < 0.55), 0.005))
    Z.append(('Grille', lambda s, y, z: mask(poly_sd(GRILLE, y, z), s < 0.40), 0.02))
    Z.append(('Intake', lambda s, y, z: mask(poly_sd(LOWER, y, z), s < 0.40), 0.02))
    Z.append(('Skid', lambda s, y, z: np.minimum(mask(poly_sd(SKID, y, z), s < 0.40), mask(poly_sd(SKID, y, z + 0.01), s > 4.10)), 0.0))
    Z.append(('Tail', lambda s, y, z: np.minimum(mask(poly_sd(TLR, sym_y(y), z), s > 4.20), side(TLS, s, y, z, 0.55)), 0.005))
    Z.append(('TailBand', lambda s, y, z: mask(np.maximum(np.abs(z - 1.165) - 0.016, sym_y(y) - 0.50), s > 4.30), 0.0))
    return Z

GROUPS = [(('Lamp',), 0.006, 'Lamp'), (('Tail',), 0.006, 'Tail'), (('Grille',), 0.022, 'Grille'), (('Intake',), 0.02, 'Intake')]
ARC = lambda a0, a1, r: [(RS + r * np.cos(a), R + r * np.sin(a)) for a in np.radians(np.linspace(a0, a1, 9))]
GAPS = [
    ('sz', [(1.30, 1.155), (1.32, 0.95), (1.33, 0.70), (1.35, 0.46)], lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(2.47, 1.19), (2.48, 0.80), (2.49, 0.46)], lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sz', [(3.44, 1.215), (3.43, 0.98), (3.36, 0.88)] + ARC(110, 150, 0.53), lambda s, y, z: sym_y(y) > 0.6, 0),
    ('sy', [(1.25, 0.70), (0.9, 0.80), (0.5, 0.845), (0.24, 0.83), (0.12, 0.62), (0.08, 0.0)], lambda s, y, z: z > 0.88, 0),
    ('yz', [(0.72, 1.56), (0.74, 0.70), (0.60, 0.645), (-0.60, 0.645), (-0.74, 0.70), (-0.72, 1.56)], lambda s, y, z: s > 4.2, -1),
]
FUEL = (3.82, 3.97, 0.95, 1.06)
